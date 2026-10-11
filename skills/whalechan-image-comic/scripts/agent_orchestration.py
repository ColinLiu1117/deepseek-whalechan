"""Role limits and persistent task dispatch; this module never starts agents."""
from __future__ import annotations
import copy
import fcntl
from contextlib import contextmanager
from pathlib import Path

ROLES = ("planning", "generation", "collection", "delivery")
DEFAULT_LIMITS = {"planning": 5, "generation": 5, "codex_generation": 3, "collection": 2, "delivery": 1}


@contextmanager
def locked(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def execution(value=None):
    if value is not None and not isinstance(value, dict):
        raise ValueError("execution must be an object")
    value = copy.deepcopy(value or {})
    allowed = {"batch_id", "role_limits", "batch_limit", "scheduling", "commit_strategy"}
    if set(value) - allowed:
        raise ValueError("Role execution contains unsupported fields")
    limits = value.get("role_limits", DEFAULT_LIMITS)
    if not isinstance(limits, dict) or set(limits) != set(DEFAULT_LIMITS) or any(type(n) is not int or not 1 <= n <= 10 for n in limits.values()):
        raise ValueError("role_limits must name all five positive limits, at most 10")
    total = value.get("batch_limit", 10)
    if type(total) is not int or not 1 <= total <= 10:
        raise ValueError("batch_limit must be between 1 and 10")
    batch = value.get("batch_id")
    if not isinstance(batch, str) or not batch.strip():
        raise ValueError("execution.batch_id is required")
    for key, expected in (("scheduling", "source-first-generation-priority"),
                          ("commit_strategy", "worker-serial-merge")):
        if value.get(key, expected) != expected:
            raise ValueError(f"{key} must be {expected}")
        value[key] = expected
    return {**value, "batch_id": batch.strip(), "role_limits": limits, "batch_limit": total}


def capacity(limit, scope="subagents", external=0):
    if type(limit) is not int or type(external) is not int or min(limit, external) < 0:
        raise ValueError("Capacity and external occupancy must be nonnegative integers")
    if scope not in {"subagents", "all-agents"}:
        raise ValueError("Unknown capacity scope")
    return max(0, limit - (scope == "all-agents") - external)


def targets(policy, slots, ready, provider="codex", provider_limit=None):
    """Allocate targets, not preemptions. Idle residents may be reused."""
    limits = execution(policy)["role_limits"]
    total = min(slots, policy.get("batch_limit", 10))
    if type(total) is not int or total < 0:
        raise ValueError("Invalid available capacity")
    gen = limits["codex_generation"] if provider == "codex" else limits["generation"]
    if provider_limit is not None:
        if type(provider_limit) is not int or provider_limit < 1:
            raise ValueError("provider_limit must be positive")
        gen = min(gen, provider_limit)
    demand = {r: min(max(0, ready.get(r, 0)), gen if r == "generation" else limits[r]) for r in ROLES}
    result = dict.fromkeys(ROLES, 0)
    # A finished source gets a reviewer without reserving an idle reviewer.
    if demand["collection"]:
        result["collection"] = min(1, total)
    result["generation"] = min(demand["generation"], total - sum(result.values()))
    result["collection"] += min(demand["collection"] - result["collection"], total - sum(result.values()))
    for role in ("planning", "delivery"):
        result[role] = min(demand[role], total - sum(result.values()))
    return result


class Orchestration:
    def __init__(self, manager):
        self.m = manager

    def ready(self, task, policy):
        if task["role"] == "planning":
            return True
        inputs = task["inputs"]
        paths = inputs.get("run_dirs", []) if task["role"] == "delivery" else [inputs.get("run_dir")]
        if not paths:
            raise self.m.RunError("Execution tasks require frozen run paths")
        runs = [self.m.load_run(path) for path in paths if path]
        if len(runs) != len(paths):
            raise self.m.RunError("Missing frozen run path")
        for run, assignment, manifest in runs:
            if assignment["schema_version"] != 17 or assignment["execution"] != policy:
                raise self.m.RunError("Task run must share the approved v17 batch execution")
            if task["role"] in {"collection", "delivery"} and task.get("recovery_evidence"):
                return True  # Resume the existing sheet/receipt, never repeat its visual judgment.
            if task["role"] == "generation":
                image = inputs.get("image")
                state = self.m.state_for(manifest, image)
                path = run / "tasks" / image / "state.json"
                if path.exists():
                    local = self.m.read_json(path)
                    if local["owner"] or local["flight"]:
                        return bool(task.get("recovery_evidence") and local["owner"] == task["owner"]
                                    and local["task_id"] == task["id"])
                    if task.get("recovery_evidence") and local["state"]["status"] in {
                            "awaiting_collection", "technical_blocked", "exhausted", "safety_blocked"}:
                        return True  # Completion receipt was lost; do not generate again.
                    if local["base_round"] == len(manifest["collection"]["reviews"]):
                        state = local["state"]
                return manifest["status"] == "in_progress" and state["status"] == "pending"
            for image, state in manifest["images"].items():
                path = run / "tasks" / image / "state.json"
                if path.exists():
                    local = self.m.read_json(path)
                    if local["owner"] or local["flight"]:
                        return False
                    if local["base_round"] == len(manifest["collection"]["reviews"]):
                        state = local["state"]
                if state["status"] not in {"awaiting_collection", "collection_accepted", "passed",
                                           "technical_blocked", "exhausted", "collection_failed", "safety_blocked"}:
                    return False
            group = manifest["collection"]["status"]
            if task["role"] == "collection" and group not in {"pending", "repairing"}:
                return False
            if task["role"] == "delivery" and group != "complete":
                return False
        return True


    def run(self, args):
        path = Path(args.batch).resolve()
        with locked(path.with_suffix(".lock")):
            if args.action == "init":
                if path.exists():
                    raise self.m.RunError("Batch already exists")
                policy = execution(self.m.read_json(Path(args.policy)))
                state = {"execution": policy, "sources": args.source, "tasks": {}, "workers": {}, "events": []}
                if not args.source or len(set(args.source)) != len(args.source):
                    raise self.m.RunError("Provide unique ordered sources")
            else:
                state = self.m.read_json(path)
                execution(state["execution"])
            result = {}
            tasks = state["tasks"]
            if args.action == "enqueue":
                item = self.m.read_json(Path(args.task_json))
                required = {"id", "role", "source", "inputs", "depends_on"}
                if set(item) != required or item["role"] not in ROLES or item["source"] not in state["sources"]:
                    raise self.m.RunError("Task requires id/role/source/inputs/depends_on")
                self.m.text(item["id"], "task.id")
                if not isinstance(item["inputs"], dict) or not isinstance(item["depends_on"], list):
                    raise self.m.RunError("Task inputs/dependencies have invalid types")
                if item["id"] in tasks or any(d not in tasks for d in item["depends_on"]):
                    raise self.m.RunError("Duplicate task or unknown dependency")
                tasks[item["id"]] = {**item, "status": "pending", "owner": None, "queued_at": self.m.now()}
            elif args.action in {"next", "claim"}:
                slots = min(capacity(args.slots, args.scope, args.external), state["execution"]["batch_limit"])
                ready = [t for t in tasks.values() if t["status"] == "pending" and
                         all(tasks[d]["status"] == "complete" for d in t["depends_on"]) and
                         self.ready(t, state["execution"])]
                active = [t for t in tasks.values() if t["status"] == "running"]
                def work_key(task):
                    inputs = task["inputs"]
                    if task["role"] in {"generation", "collection"}:
                        return (task["role"], str(Path(inputs["run_dir"]).resolve()), inputs.get("image"))
                    return (task["role"], task["source"])
                occupied = {work_key(t) for t in active}
                ready = [t for t in ready if work_key(t) not in occupied]
                counts = {r: sum(t["role"] == r for t in active) for r in ROLES}
                demand = {r: counts[r] + sum(t["role"] == r for t in ready) for r in ROLES}
                allocation = targets(state["execution"], slots, demand, args.provider, args.provider_limit)
                ordered = sorted(ready, key=lambda t: (state["sources"].index(t["source"]), t["queued_at"], t["id"]))
                choice = next((t for t in ordered if counts[t["role"]] < allocation[t["role"]]
                               and (not args.task or t["id"] == args.task)), None)
                if len(active) >= slots:
                    choice = None
                result = {"targets": allocation, "active": counts, "available_slots": slots,
                          "next_task": copy.deepcopy(choice)}
                if args.action == "claim":
                    if not choice:
                        raise self.m.RunError("No task can be dispatched at current capacity")
                    owner = self.m.text(args.worker, "worker")
                    if choice["owner"] is not None and choice["owner"] != owner:
                        raise self.m.RunError("Recovered task is assigned to another worker")
                    if any(t["owner"] == owner for t in active):
                        raise self.m.RunError("Worker already owns a running task")
                    residents = state["workers"]
                    if owner not in residents and len(residents) >= slots:
                        raise self.m.RunError("Idle agents still occupy slots; reuse or confirm release")
                    choice.update(status="running", owner=owner, started_at=self.m.now())
                    residents[owner] = choice["id"]
                    result["next_task"] = copy.deepcopy(choice)
            elif args.action == "finish":
                task = tasks.get(args.task)
                if not task or task["status"] != "running" or task["owner"] != args.worker:
                    raise self.m.RunError("Only the running task owner can finish")
                output = Path(args.result).resolve()
                record = self.m.read_json(output)
                if record.get("task_id") != task["id"] or record.get("status") not in {"complete", "blocked"}:
                    raise self.m.RunError("Result must bind task_id and complete/blocked status")
                task.update(status=record["status"], result=str(output), result_sha256=self.m.sha256(output),
                            finished_at=self.m.now())
                state["workers"][args.worker] = None
            elif args.action == "release":
                if args.worker not in state["workers"] or state["workers"][args.worker] is not None:
                    raise self.m.RunError("Only an idle resident may be released")
                if not args.evidence:
                    raise self.m.RunError("Actual runtime release evidence is required")
                del state["workers"][args.worker]
            elif args.action == "recover":
                task = tasks.get(args.task)
                if not task or task["status"] != "running" or not args.evidence:
                    raise self.m.RunError("Recovery requires a running task and reconciled runtime evidence")
                # The image-task owner must also be reconciled before another image call.
                state["workers"][task["owner"]] = None
                task.update(status="pending", owner=args.worker, recovery_evidence=args.evidence)
            if args.action != "next":
                state["events"].append({"at": self.m.now(), "event": args.action,
                                        "task": result.get("next_task", {}).get("id") if result.get("next_task") else getattr(args, "task", None),
                                        "worker": getattr(args, "worker", None)})
                self.m.write_json(path, state)
            return {**result, "batch": str(path), "execution": state["execution"]}

    def register(self, commands):
        plan = commands.add_parser("plan-roles", help="Role limits and available targets; does not launch agents")
        plan.add_argument("--batch-id", required=True)
        plan.add_argument("--slots", type=int, required=True)
        plan.add_argument("--scope", choices=("subagents", "all-agents"), default="subagents")
        plan.add_argument("--external", type=int, default=0)
        plan.add_argument("--provider", choices=self.m.PROVIDERS, default="codex")
        plan.add_argument("--provider-limit", type=int)
        for role in ROLES:
            plan.add_argument("--" + role, type=int, default=0, help="Ready task count")
        def show(args):
            policy = execution({"batch_id": args.batch_id})
            slots = capacity(args.slots, args.scope, args.external)
            return {"execution": policy, "available_slots": slots, "targets": targets(
                policy, slots, {r: getattr(args, r) for r in ROLES}, args.provider, args.provider_limit)}
        plan.set_defaults(handler=show)
        batch = commands.add_parser("agent-batch", help="Maintain one batch queue; runtime delegation remains explicit")
        batch.add_argument("action", choices=("init", "enqueue", "next", "claim", "finish", "release", "recover"))
        batch.add_argument("--batch", required=True)
        batch.add_argument("--policy")
        batch.add_argument("--source", action="append")
        batch.add_argument("--task-json")
        batch.add_argument("--task")
        batch.add_argument("--worker")
        batch.add_argument("--result")
        batch.add_argument("--evidence")
        batch.add_argument("--slots", type=int, default=0)
        batch.add_argument("--scope", choices=("subagents", "all-agents"), default="subagents")
        batch.add_argument("--external", type=int, default=0)
        batch.add_argument("--provider", choices=self.m.PROVIDERS, default="codex")
        batch.add_argument("--provider-limit", type=int)
        batch.set_defaults(handler=self.run)
