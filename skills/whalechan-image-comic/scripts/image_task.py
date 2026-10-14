"""Exclusive per-image journals for v17–v19; shared manifests are serial projections."""
from __future__ import annotations
import copy
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace


class ImageTasks:
    def __init__(self, manager):
        self.m = manager
        self.locked = manager.extension_module("agent_orchestration").locked

    def require(self, condition, message):
        if not condition:
            raise self.m.RunError(message)

    def path(self, run, image):
        return run / "tasks" / image / "state.json"

    def load(self, args):
        run, assignment, manifest = self.m.load_run(args.run_dir)
        self.require(assignment["schema_version"] in {17, 18, 19}, "Image tasks require v17/v18/v19")
        self.require(manifest["status"] == "in_progress", "Run is closed")
        self.m.state_for(manifest, args.image)
        return run, assignment, manifest

    def write(self, path, data):
        data["revision"] += 1
        data["updated_at"] = self.m.now()
        self.m.write_json(path, data)

    def proxy(self, run, assignment, manifest, data, path, image):
        local = copy.deepcopy(manifest)
        local["images"][image] = data["state"]
        local["events"] = data["events"]
        def save(_run, value):
            data["state"] = value["images"][image]
            data["events"] = value["events"]
            self.write(path, data)
        proxy = SimpleNamespace(**vars(self.m))
        proxy.task_local = True
        proxy.load_run = lambda _: (run, assignment, local)
        proxy.save_manifest = save
        # A crash may leave the identical archived bytes before the journal write.
        def copy_same(source, destination):
            if destination.exists():
                self.require(self.m.sha256(source) == self.m.sha256(destination), "Recovery file differs")
            else:
                self.m.copy_once(source, destination)
        proxy.copy_once = copy_same
        workflow = self.m.extension_module("review_workflow").ReviewWorkflow(proxy)
        return workflow, local

    def run(self, args):
        if args.action in {"start", "ingest", "submit"}:
            return self.m.extension_module("batch_workflow").BatchWorkflow(self.m).image(args)
        run, assignment, manifest = self.load(args)
        path = self.path(run, args.image)
        # Claim/recovery synchronize with collection operations; generation only locks its image.
        with ExitStack() as stack:
            policy = self.m.extension_module("provider_policy")
            if assignment["schema_version"] in {18, 19} and args.action in {"claim", "begin", "error", "uncertain"}:
                batch_path = policy.batch_path(self.m, manifest, assignment)
                stack.enter_context(self.locked(batch_path.with_suffix(".lock")))
                policy.guard(self.m, manifest, assignment, allow_paused=args.action in {"error", "uncertain"})
            if args.action in {"claim", "recover"}:
                stack.enter_context(self.locked(run / ".manifest.lock"))
            stack.enter_context(self.locked(path.with_suffix(".lock")))
            run, assignment, manifest = self.load(args)
            data = self.m.read_json(path) if path.exists() else {
                "assignment_sha256": manifest["assignment_sha256"], "image": args.image,
                "state": copy.deepcopy(manifest["images"][args.image]), "owner": None, "task_id": None,
                "revision": 0, "flight": None, "events": [], "base_round": len(manifest["collection"]["reviews"])}
            self.require(data["assignment_sha256"] == manifest["assignment_sha256"], "Task assignment changed")
            if args.action == "status":
                return data
            if args.action == "claim":
                self.require(data["owner"] is None, "Image already has an owner")
                round_number = len(manifest["collection"]["reviews"])
                if round_number != data["base_round"]:
                    self.require(manifest.get("task_revisions", {}).get(args.image) == data["revision"],
                                 "Merge the previous image task before collection repair")
                    data["state"] = copy.deepcopy(manifest["images"][args.image])
                    data["base_round"] = round_number
                self.require(data["state"]["status"] == "pending" and not data["flight"], "Image is not ready")
                self.m.text(args.owner, "owner"); self.m.text(args.task_id, "task_id")
                data.update(owner=args.owner, task_id=args.task_id)
            elif args.action == "recover":
                self.require(args.evidence and args.owner and args.task_id, "Reconcile old worker and provide recovery evidence")
                self.require(data["owner"] is not None, "There is no owner to recover")
                data.update(owner=args.owner, task_id=args.task_id)
                data["events"].append({"event": "owner_recovered", "at": self.m.now(), "evidence": args.evidence})
                # Uncertain calls stay in flight. Recovery never clears a consumed slot.
            else:
                self.require(data["owner"] == args.owner and data["task_id"] == args.task_id and data["owner"],
                             "Only the current owner/task can mutate this image")
                state = data["state"]
                workflow, local = self.proxy(run, assignment, manifest, data, path, args.image)
                if args.action == "begin":
                    self.require(state["status"] == "pending" and not data["flight"], "Image has an unresolved call or is not pending")
                    self.require(len(state["attempts"]) < 3, "Candidate budget exhausted")
                    self.m.provider_allowed(state, args.provider, assignment)
                    if assignment["schema_version"] in {18, 19}:
                        policy.guard(self.m, manifest, assignment, args.provider, args.model)
                    if state["provider_errors"] and assignment["schema_version"] not in {18, 19}:
                        self.require(state["provider_errors"][-1]["provider"] != args.provider,
                                     "After a no-image failure, advance provider; do not retry indefinitely")
                    self.require(args.model, "Model is required")
                    data["flight"] = {"provider": args.provider, "model": args.model,
                                      "started_at": self.m.now(), "attempt": len(state["attempts"]) + 1}
                    data["events"].append({"event": "generation_started", "image": args.image, "at": self.m.now()})
                elif args.action == "prepare":
                    self.require(args.candidate and Path(args.candidate).is_file(), "Locate the returned image before preparation; call stays in flight")
                    flight = data["flight"]
                    if assignment["schema_version"] in {18, 19}:
                        expected_transport = assignment["execution"]["tool"]["transport"] if args.provider == "codex" else None
                        self.require(args.transport == expected_transport, "Locked transport mismatch")
                    self.require(flight and flight["provider"] == args.provider and flight["model"] == args.model,
                                 "Prepare requires the matching in-flight call")
                    if len(state["attempts"]) >= flight["attempt"]:
                        record = state["attempts"][-1]
                        self.require(self.m.sha256(Path(args.candidate)) == record["candidate_sha256"], "Recovery candidate differs")
                        if record["verdict"] == "PENDING" and not record.get("automatic_qa"):
                            state["attempts"].pop()
                            state["status"] = "pending"
                            data["events"][:] = [e for e in data["events"] if not (
                                e.get("event") == "image_returned" and e.get("attempt") == record["attempt_id"])]
                            workflow.prepare(args)
                    else:
                        workflow.prepare(args)
                    data["flight"] = None
                elif args.action == "review-start":
                    self.require(not data["flight"], "Resolve preparation before QA")
                    previous = next((i for i in range(len(data["events"]) - 1, -1, -1)
                                     if data["events"][i]["event"] == "image_returned"), -1)
                    already = any(e["event"] == "single_review_started" for e in data["events"][previous + 1:])
                    if assignment["schema_version"] not in {18, 19} or not already:
                        workflow.mark(SimpleNamespace(run_dir=str(run), image=args.image, event="single_review_started"))
                elif args.action == "review":
                    self.require(not data["flight"], "Resolve preparation before QA")
                    workflow.record_candidate(args, run, assignment, local)
                elif args.action in {"error", "uncertain"}:
                    self.require(data["flight"] and args.evidence, "A no-image error requires call and reconciliation evidence")
                    self.require(args.category in self.m.ADVANCE_ERRORS | {"safety_rejection"}, "Unsupported provider error")
                    flight = data["flight"]
                    self.require(flight["provider"] == args.provider and flight["model"] == args.model, "Error provider/model mismatch")
                    if assignment["schema_version"] in {18, 19}:
                        batch_path, batch = policy.guard(self.m, manifest, assignment, args.provider, args.model, True)
                        reason = self.m.text(args.evidence, "evidence")
                        pause = {"image": args.image, "reason": reason, "category": args.category}
                        if batch.get("pause", {}).get("category") == "safety_rejection":
                            pause = batch["pause"]
                        batch.update(status="paused", pause=pause)
                        batch["events"].append({"event": "service_paused", "at": self.m.now(), "image": args.image})
                        self.m.write_json(batch_path, batch)
                        if args.action == "uncertain":
                            data["events"].append({"event": "call_unresolved", "at": self.m.now(), "evidence": reason})
                            self.write(path, data)
                            return {"status": "paused", "next_action": "reconcile-flight", "journal": str(path)}
                    state["provider_errors"].append({"provider": args.provider, "model": args.model,
                        "category": args.category, "details": self.m.text(args.evidence, "evidence"),
                        "created_at": self.m.now(), "consumes_candidate_budget": False})
                    if args.category == "safety_rejection":
                        state["status"] = "safety_blocked"
                    elif args.provider == self.m.PROVIDERS[-1] and assignment["schema_version"] not in {18, 19}:
                        state["status"] = "technical_blocked"
                    data["flight"] = None
                elif args.action == "block":
                    self.require(not data["flight"], "Reconcile the in-flight call before blocking")
                    workflow.block(SimpleNamespace(run_dir=str(run), image=args.image, reason=args.evidence))
                elif args.action == "finish":
                    self.require(not data["flight"] and state["status"] in {
                        "awaiting_collection", "technical_blocked", "exhausted", "safety_blocked"},
                        "Resolve all calls and reviews before finishing")
                    data.update(owner=None, task_id=None)
                else:
                    raise self.m.RunError("Unknown image task action")
            self.write(path, data)
            return {"image": args.image, "status": data["state"]["status"], "owner": data["owner"],
                    "revision": data["revision"], "remaining": 3 - len(data["state"]["attempts"]),
                    "flight": data["flight"], "journal": str(path)}

    def validate(self, assignment, data, image):
        self.require(not data["owner"] and not data["flight"], "Image task is still owned or in flight")
        state = data["state"]
        self.require(len(state["attempts"]) <= 3, "Budget exceeded")
        self.require(state["status"] in {"awaiting_collection", "exhausted", "technical_blocked", "safety_blocked"},
                     "Image has not reached a terminal single-image decision")
        if state["status"] == "awaiting_collection":
            self.require(state["attempts"] and state["attempts"][-1]["verdict"] == "PASS", "No passing candidate")
        if state["status"] == "exhausted":
            self.require(len(state["attempts"]) == 3 and state["attempts"][-1]["verdict"] == "FAIL", "Invalid exhaustion")
        spec = next(i for i in assignment["images"] if i["id"] == image)
        for n, record in enumerate(state["attempts"], 1):
            self.require(record["attempt_id"] == f"attempt-{n:02d}", "Attempt sequence changed")
            self.require(self.m.sha256(Path(record["candidate"])) == record["candidate_sha256"], "Candidate changed")
            if record.get("visual_qa"):
                self.require(self.m.sha256(Path(record["visual_qa"])) == record["visual_sha256"], "QA record changed")
                self.m.validate_compact_qa(self.m.read_json(Path(record["visual_qa"])), record["candidate_sha256"], spec)
                self.m.validate_automatic(Path(record["automatic_qa"]), record["candidate_sha256"], spec["output"])
            else:
                self.require(state["status"] == "technical_blocked" and record.get("technical_error"),
                             "Unreviewed candidate cannot pass")

    def merge_locked(self, run, assignment, manifest):
        revisions = manifest.setdefault("task_revisions", {})
        hashes = manifest.setdefault("task_hashes", {})
        for image in manifest["images"]:
            path = self.path(run, image)
            if not path.exists():
                continue
            data = self.m.read_json(path)
            self.require(data["assignment_sha256"] == manifest["assignment_sha256"], "Task belongs to another assignment")
            self.validate(assignment, data, image)
            previous = revisions.get(image, -1)
            self.require(data["revision"] >= previous, "Task journal rolled back")
            digest = self.m.contract_hash(data)
            if data["revision"] == previous:
                self.require(hashes.get(image) == digest, "Merged task changed without a revision")
                continue
            old_attempts = manifest["images"][image]["attempts"]
            self.require(data["state"]["attempts"][:len(old_attempts)] == old_attempts, "Previously merged attempts changed")
            manifest["images"][image] = copy.deepcopy(data["state"])
            revisions[image] = data["revision"]
            hashes[image] = digest
            # Replace this image's local event projection, retaining collection events.
            manifest["events"] = [e for e in manifest["events"] if e.get("task_image") != image]
            manifest["events"].extend({**e, "task_image": image} for e in data["events"])
        self.m.save_manifest(run, manifest)

    def shared(self, args, operation=None):
        run = Path(args.run_dir).resolve()
        with self.locked(run / ".manifest.lock"), ExitStack() as stack:
            run, assignment, manifest = self.m.load_run(str(run))
            self.require(assignment["schema_version"] in {17, 18, 19}, "Task merge requires v17/v18/v19")
            for image in sorted(manifest["images"]):
                stack.enter_context(self.locked(self.path(run, image).with_suffix(".lock")))
            self.merge_locked(run, assignment, manifest)
            return operation(args) if operation else {"merged": True, "task_revisions": manifest["task_revisions"]}

    def register(self, commands):
        command = commands.add_parser("image-task", help="Exclusive v17 image execution without coordinator QA handoffs")
        command.add_argument("action", choices=("claim", "recover", "status", "begin", "prepare", "review-start", "review", "error", "uncertain", "block", "finish", "start", "ingest", "submit"))
        for name in ("run-dir", "image"):
            command.add_argument("--" + name, required=True)
        for name in ("owner", "task-id", "provider", "model", "candidate", "prompt-file", "automatic-json",
                     "visual-json", "provider-audit", "transport", "category", "evidence", "retry-prompt"):
            command.add_argument("--" + name)
        command.set_defaults(handler=self.run)
        merge = commands.add_parser("merge-tasks", help="Serially merge completed image journals")
        merge.add_argument("--run-dir", required=True)
        merge.set_defaults(handler=self.shared)
