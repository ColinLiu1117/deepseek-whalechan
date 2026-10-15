"""Reusable current batch and image operations. Provider calls and visual judgments stay with workers."""
from __future__ import annotations
import json
import re
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace as NS


class BatchWorkflow:
    def __init__(self, manager):
        self.m = manager
        self.roles = manager.extension_module("agent_orchestration")
        self.policy = manager.extension_module("provider_policy")
        self.locked = self.roles.locked

    def require(self, ok, message):
        if not ok:
            raise self.m.RunError(message)

    def event(self, batch, name, **fields):
        batch["events"].append({"event": name, "at": self.m.now(), **fields})

    def state(self, path):
        value = self.m.read_json(Path(path))
        self.require(value.get("schema_version") in self.m.SUPPORTED_ASSIGNMENT_VERSIONS, "Batch schema_version must be 19")
        self.policy.validate(value["execution"].get("tool"))
        return value

    def attach(self, args, run, assignment, manifest):
        path = Path(getattr(args, "batch", None) or run / "batch.json").resolve()
        with self.locked(path.with_suffix(".lock")):
            if path.exists():
                batch = self.state(path)
                self.require(batch["execution"] == assignment["execution"], "Batch execution mismatch")
            else:
                batch = {"schema_version": assignment["schema_version"], "execution": assignment["execution"], "sources": [assignment["run_name"]],
                         "tasks": {}, "workers": {}, "events": [], "runs": {},
                         "status": "preflight_required"}
                if assignment["schema_version"] == 20:
                    batch.update(self.m.language_policy().contract(assignment))
                batch["runs"][assignment["run_name"]] = str(run)
                self.m.write_json(path, batch)
        manifest["batch_file"] = str(path)

    def prepare(self, args):
        path = Path(args.batch).resolve()
        spec = self.m.read_json(Path(args.spec))
        version = spec.get("schema_version", self.m.ASSIGNMENT_SCHEMA_VERSION)
        self.require(type(version) is int and version in self.m.SUPPORTED_ASSIGNMENT_VERSIONS, "Batch version must be 19")
        with self.locked(path.with_suffix(".lock")):
            self.require(not path.exists(), "Batch exists; use status/resume")
            sources = spec.get("sources", [])
            self.require(bool(sources), "Provide ordered sources")
            inventory = []
            for source in sources:
                ident = source.get("id", "")
                self.require(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", ident), "Source id must be kebab-case")
                files = []
                for filename in source.get("paths", []):
                    file = Path(filename).resolve()
                    self.require(file.is_file(), "Source file missing")
                    files.append({"path": str(file), "sha256": self.m.sha256(file), "type": file.suffix.lower()})
                self.require(files or isinstance(source.get("text"), str) and source["text"].strip(),
                             "Each source needs paths or text")
                item = {"id": ident, "files": files, "text": source.get("text")}
                item["target_images"] = self.m.extension_module("selection_contract").count(source.get("target_images", 5))
                item["exaggeration_policy"] = self.m.normalize_tier_policy(
                    source.get("exaggeration_policy", self.m.DEFAULT_TIER_POLICY))
                inventory.append(item)
            self.require(len({s["id"] for s in inventory}) == len(inventory), "Duplicate source id")
            preflight = self.policy.preflight(self.m, spec.get("availability", {}), spec.get("requests", []))
            if preflight["status"] != "ready":
                self.m.write_json(path.with_name(path.stem + "-preflight.json"), preflight)
                return preflight
            execution = self.roles.execution({**spec["execution"], "tool": preflight["tool"],
                "planning_mode": self.roles.PRIORITY_MODE})
            language = spec.get("language")
            if version == 20:
                self.m.language_policy().contract(spec)
            else:
                self.require(language in {"zh", "en"}, "Legacy communication language must be zh or en")
            batch = {"schema_version": version, "execution": execution, "sources": [s["id"] for s in inventory],
                     "inventory": inventory, "language": language, "preflight": preflight,
                     "status": "planning", "tasks": {}, "workers": {}, "events": [], "runs": {},
                     "language_evidence": spec.get("language_evidence") or (spec.get("language_resolution") if spec.get("language_resolution", {}).get("source") != "recent-session" and spec.get("language_resolution") else self.m.extension_module("detect-language").detect(24, Path.home(), 5))}
            if version == 20:
                batch.update(self.m.language_policy().contract(spec))
            for source in inventory:
                self.enqueue(batch, "concepts-" + source["id"], "planning", source["id"],
                    {"stage": "concepts", "source": source,
                     "output": str(path.parent / (source["id"] + "-pool.json"))}, [])
            self.event(batch, "batch_prepared")
            self.m.write_json(path, batch)
            return {"status": "planning", "batch": str(path), "execution": execution,
                    "next_action": "dispatch-planning", "tasks": list(batch["tasks"])}

    def enqueue(self, batch, ident, role, source, inputs, dependencies):
        self.require(re.fullmatch(r"[A-Za-z0-9_-]+", ident), "Unsafe task id")
        spec = {"id": ident, "role": role, "source": source, "inputs": inputs, "depends_on": dependencies}
        if ident in batch["tasks"]:
            self.require(all(batch["tasks"][ident][k] == v for k, v in spec.items()), "Task definition changed")
            return
        self.require(all(d in batch["tasks"] for d in dependencies), "Unknown dependency")
        batch["tasks"][ident] = {**spec, "status": "pending", "owner": None, "queued_at": self.m.now()}

    def proposal(self, args):
        path = Path(args.batch).resolve()
        batch = self.state(path)
        self.require(batch["status"] == "planning", "Proposal requires planning state")
        self.require(len(args.draft or []) == len(batch["sources"]), "One draft per ordered source")
        drafts = []
        run_names = set()
        requests = []
        builder = self.m.extension_module("build-prompt")
        for source, filename in zip(batch["sources"], args.draft):
            filename = Path(filename).resolve()
            task = batch["tasks"].get("detail-" + source, {})
            self.require(task.get("status") == "complete", "Complete independent selection and detail tasks first")
            receipt = self.m.read_json(Path(task["result"]))
            self.require(self.m.sha256(Path(task["result"])) == task["result_sha256"], "Detail receipt changed")
            self.require(str(filename) == receipt["output"] and self.m.sha256(filename) == receipt["output_sha256"],
                         "Draft must be the completed detail output")
            draft = self.m.validate_assignment(filename, require_approval=False)
            self.require(draft["execution"] == batch["execution"], "Draft must share batch policy")
            self.require(draft["run_name"] not in run_names, "Each source needs a unique run_name")
            run_names.add(draft["run_name"])
            for image in draft["images"]:
                request = builder.build_request(image, self.m.visual_prompt().render(draft, image), None, "")
                output = path.parent / "requests" / source / (image["id"] + ".json")
                self.m.write_json(output, request)
                requests.append(str(output))
            normalized = path.parent / (source + "-normalized.json")
            self.m.write_json(normalized, draft)
            origin = next(x for x in batch["inventory"] if x["id"] == source)
            self.require(draft["schema_version"] == batch["schema_version"] and draft["source_id"] == source and
                         draft["target_images"] == origin["target_images"], "Draft source/count differs")
            if batch["schema_version"] == 20:
                self.require(all(draft.get(k) == batch.get(k) for k in ("language", "language_overrides", "language_resolution")), "Draft language differs from the batch")
            self.require(draft.get("exaggeration_policy") == origin.get("exaggeration_policy"),
                         "Draft must preserve the source tier policy")
            if origin["files"]:
                planned = draft["input"]["content"]
                planned = planned if isinstance(planned, list) else [planned]
                self.require([str(Path(x).resolve()) for x in planned] == [x["path"] for x in origin["files"]], "Draft source paths differ")
                self.require(all(self.m.sha256(Path(x["path"])) == x["sha256"] for x in origin["files"]), "Source bytes changed")
            else:
                self.require(draft["input"]["content"] == origin["text"], "Draft source text differs")
            drafts.append({"source": source, "path": str(normalized), "sha256": self.m.sha256(normalized),
                           "summary_sha256": self.m.selection_summary(draft)["summary_sha256"]})
        review = self.m.read_json(Path(args.review_json))
        self.require(review.get("review_status") == "reviewed" and bool(review.get("observation")),
                     "Author the cross-source review before proposal")
        self.require(review.get("sources") == batch["sources"], "Cross-source review must cover ordered sources")
        matrix = self.m.design_summary([self.m.read_json(Path(d["path"])) for d in drafts])
        preflight = self.policy.preflight(self.m, batch["preflight"]["evidence"], requests,
                                          expected=batch["execution"]["tool"])
        self.require(preflight["status"] == "ready", "Locked tool cannot meet all plans; batch is not ready")
        proposal = {"drafts": drafts, "cross_review": review, "matrix": matrix,
                    "execution": batch["execution"], "requests": requests}
        proposal["summary_sha256"] = self.m.contract_hash(proposal)
        target = path.parent / "proposal.json"
        self.m.write_json(target, proposal)
        rendered = path.parent / "proposal.md"
        words = None
        if batch["schema_version"] == 20:
            first = self.m.read_json(Path(drafts[0]["path"]))
            lp = self.m.language_policy()
            words = lp.locale(first, lp.effective(first, "communication"), "plan")
        question = words["question"] if words else self.m.PLAN_TEXT[batch["language"]]["question"]
        tables = [self.m.plan_markdown(self.m.read_json(Path(d["path"])), language=batch["language"]).replace(question, "")
                  for d in drafts]
        count = sum(self.m.target_images(self.m.read_json(Path(d["path"]))) for d in drafts)
        total = (f"总计：{count}张；最多{count * 3}次出图。各来源共用上述角色上限。" if batch["language"] == "zh"
                 else f"Total: {count} images; maximum {count * 3} calls. Role limits are shared across sources.")
        if words:
            total = words["totals"].format(n=count, calls=count * 3)
        rendered.write_text("\n\n".join(tables) + "\n\n" + total + "\n\n" + question + "\n")
        with self.locked(path.with_suffix(".lock")):
            batch = self.state(path)
            batch.update(proposal=str(target), proposal_sha256=self.m.sha256(target), preflight=preflight)
            self.event(batch, "proposal_rendered")
            self.m.write_json(path, batch)
        return {"status": "awaiting_confirmation", "proposal": str(target), "rendered": str(rendered),
                "summary_sha256": proposal["summary_sha256"], "next_action": "one-user-confirmation"}

    def start(self, args):
        path = Path(args.batch).resolve()
        # A separate operation lock serializes multi-file initialization; each run is checkpointed.
        with self.locked(path.with_name(path.stem + ".workflow.lock")):
            batch = self.state(path)
            self.require(batch["status"] in {"planning", "initializing", "ready"}, "Batch cannot initialize")
            proposal_path = Path(batch["proposal"])
            self.require(self.m.sha256(proposal_path) == batch["proposal_sha256"], "Proposal changed")
            proposal = self.m.read_json(proposal_path)
            confirmation = self.m.read_json(Path(args.confirmation))
            self.m.text(confirmation.get("user_reply"), "actual user reply")
            self.require(confirmation.get("summary_sha256") == proposal["summary_sha256"],
                         "User confirmation must bind the displayed batch")
            if batch.get("confirmation"):
                self.require(batch["confirmation"] == confirmation, "Confirmation changed")
            if batch["status"] == "ready":
                return {"status": "ready", "runs": batch["runs"], "next_action": "dispatch-generation"}
            for source in batch.get("inventory", []):
                self.require(all(self.m.sha256(Path(f["path"])) == f["sha256"] for f in source["files"]), "Source bytes changed after proposal")
            batch.update(status="initializing", confirmation=confirmation)
            self.m.write_json(path, batch)
            for entry in proposal["drafts"]:
                draft_path = Path(entry["path"])
                self.require(self.m.sha256(draft_path) == entry["sha256"], "Displayed draft changed")
                draft = self.m.read_json(draft_path)
                draft["confirmation"] = {"status": "confirmed", "user_reply": confirmation["user_reply"],
                                         "summary_sha256": entry["summary_sha256"]}
                approved = path.parent / (entry["source"] + "-assignment.json")
                self.m.write_json(approved, draft)
                if entry["source"] not in batch["runs"]:
                    result = self.m.cmd_init(NS(assignment=str(approved), root=args.root,
                        effective_parallelism=min(len(draft["images"]), args.slots or 1, draft["execution"]["role_limits"]["codex_generation" if draft["execution"]["tool"]["provider"] == "codex" else "generation"]),
                        effective_subagents=min(len(draft["images"]), args.slots, draft["execution"]["role_limits"]["codex_generation" if draft["execution"]["tool"]["provider"] == "codex" else "generation"]), batch=str(path)))
                    batch["runs"][entry["source"]] = result["run_dir"]
                    self.m.write_json(path, batch)
                run = batch["runs"][entry["source"]]
                frozen = self.m.load_run(run)[1]
                deps = []
                for image in frozen["images"]:
                    ident = entry["source"] + "-gen-" + image["id"]
                    self.enqueue(batch, ident, "generation", entry["source"],
                                 {"run_dir": run, "image": image["id"]}, [])
                    deps.append(ident)
                self.enqueue(batch, entry["source"] + "-collection-0", "collection", entry["source"],
                             {"run_dir": run}, deps)
            batch["status"] = "ready"
            self.event(batch, "batch_started")
            self.m.write_json(path, batch)
            return {"status": "ready", "runs": batch["runs"], "next_action": "dispatch-generation"}

    def owned(self, path, task_id, owner, role, run=None):
        task = self.state(path)["tasks"].get(task_id)
        self.require(task and task["owner"] == owner and task["role"] == role and
                     task["status"] in {"running", "complete"}, "Task owner/role/status mismatch")
        if run is not None:
            self.require(Path(task["inputs"]["run_dir"]).resolve() == run, "Task run mismatch")
        return task

    def receipt(self, batch_path, task_id, owner, result):
        if not task_id:
            return result
        with self.locked(batch_path.with_suffix(".lock")):
            batch = self.state(batch_path)
            task = batch["tasks"].get(task_id)
            self.require(task and task["owner"] == owner, "Only task owner can submit receipt")
            if task["status"] == "complete":
                receipt = Path(task["result"])
                self.require(self.m.sha256(receipt) == task["result_sha256"], "Receipt changed")
                return {**result, "receipt": str(receipt)}
            self.require(task["status"] == "running", "Task is not running")
            output = batch_path.parent / "receipts" / (task_id + ".json")
            self.m.write_json(output, {**result, "task_id": task_id, "status": "complete"})
            task.update(status="complete", finished_at=self.m.now(), result=str(output),
                        result_sha256=self.m.sha256(output))
            batch["workers"][owner] = None
            self.event(batch, "finish", task=task_id, worker=owner)
            self.m.write_json(batch_path, batch)
            return {**result, "receipt": str(output)}

    def packet(self, args):
        batch = self.state(args.batch)
        task = batch["tasks"][args.task]
        role = task["role"]
        refs = {"planning": ["prompt-design", "proposal-selection", "comedy-engine", "run-schema"],
                "generation": ["provider-routing", "review-workflow"],
                "selection": ["proposal-selection"],
                "collection": ["review-workflow"], "delivery": ["gallery"]}[role]
        stage = task["inputs"].get("stage")
        if stage:
            refs = {"concepts": ["comedy-engine", "proposal-selection"],
                    "selection": ["proposal-selection"], "detail": ["prompt-design", "run-schema"]}[stage]
        return {"language_contract": {k: batch[k] for k in self.m.language_policy().FIELDS if k in batch},
                "schema_version": batch["schema_version"], "task": task, "batch": str(Path(args.batch).resolve()), "tool": batch["execution"]["tool"],
                "skill": str(self.m.SKILL_ROOT), "references": [str(self.m.SKILL_ROOT / "references" / (r + ".md")) for r in refs + ["language-policy"]],
                "next_action": "execute-" + (stage or role),
                **({"submission_template": {"input": None, "creative_pool": []},
                    "candidate_count": 2 * task["inputs"]["source"]["target_images"]} if stage == "concepts" else {}),
                **({"submission_template": {"ranking": [], "selection_reason": None}} if stage == "selection" else {})}

    def image(self, args):
        run, assignment, manifest = self.m.load_run(args.run_dir)

        batch_path = self.policy.batch_path(self.m, manifest, assignment)
        tool = assignment["execution"]["tool"]
        task = self.owned(batch_path, args.task_id, args.owner, "generation", run)
        self.require(task["inputs"]["image"] == args.image, "Task image mismatch")
        api = self.m.image_tasks()
        journal = api.path(run, args.image)
        def act(action, **fields):
            values = dict(vars(args))
            values.update(action=action, provider=tool["provider"],
                          model=tool["model"], transport=tool["transport"] if tool["provider"] == "codex" else None)
            values.update(fields)
            return api.run(NS(**values))
        def stamp(event):
            with self.locked(journal.with_suffix(".lock")):
                data = self.m.read_json(journal)
                self.require(data["owner"] == args.owner and data["task_id"] == args.task_id, "Image owner mismatch")
                data["events"].append({"event": event, "image": args.image, "at": self.m.now()})
                api.write(journal, data)
        if args.action == "start":
            data = self.m.read_json(journal) if journal.exists() else None
            if data and data["flight"]:
                return {"status": "in_flight", "next_action": "reconcile-flight", "journal": str(journal)}
            if not data or data["owner"] is None:
                act("claim")
            else:
                self.require(data["owner"] == args.owner and data["task_id"] == args.task_id, "Image owner mismatch")
            data = self.m.read_json(journal)
            self.require(data["state"]["status"] == "pending", "Image not pending; inspect status")
            stamp("request_preparation_started")
            spec = next(i for i in assignment["images"] if i["id"] == args.image)
            number = len(data["state"]["attempts"]) + 1
            self.require(number <= 3, "Candidate budget exhausted")
            if number > 1:
                self.require(getattr(args, "retry_prompt", None), "A targeted drawing-only retry prompt is required")
                prompt = Path(args.retry_prompt).read_text()
            else:
                prompt = self.m.visual_prompt().render(assignment, spec)
            self.require(prompt.strip(), "Empty prompt")
            folder = run / "staging" / args.image
            prompt_path = folder / f"prompt-{number:02d}.txt"
            if prompt_path.exists():
                self.require(prompt_path.read_text() == prompt, "Saved attempt prompt differs")
            else:
                prompt_path.write_text(prompt)
            request = self.m.extension_module("build-prompt").build_request(spec, prompt, None, "")
            request_path = folder / f"prompt-{number:02d}.request.json"
            self.m.write_json(request_path, request)
            act("begin")
            return {"status": "in_flight", "next_action": "call-locked-tool-once", "tool": tool,
                    "request_file": str(request_path), "prompt_file": str(prompt_path),
                    "output": str(folder / f"returned-{number:02d}.png"), "remaining": 3 - number}
        data = self.m.read_json(journal)
        if args.action == "ingest":
            number = data["flight"]["attempt"] if data["flight"] else len(data["state"]["attempts"])
            prompt_path = run / "staging" / args.image / f"prompt-{number:02d}.txt"
            if data["flight"]:
                stamp("ingest_started")
                act("prepare", prompt_file=str(prompt_path))
            else:
                self.require((data["owner"] == args.owner and data["task_id"] == args.task_id) or
                             (data["owner"] is None and data["state"]["status"] == "technical_blocked"), "Image owner mismatch")
                self.require(data["state"]["attempts"] and self.m.sha256(Path(args.candidate)) ==
                             data["state"]["attempts"][-1]["candidate_sha256"], "Returned bytes differ")
            data = self.m.read_json(journal)
            record = data["state"]["attempts"][-1]
            template = {"review_status": None, "checked": [], "panels": [], "text_transcription": [],
                        "verdict": None, "core_defects": [], "minor_issues": [],
                        "targeted_retry": None, "form_evidence": {}}
            spec = next(i for i in assignment["images"] if i["id"] == args.image)
            result = {"status": data["state"]["status"], "candidate": record["candidate"],
                      "journal": str(journal), "qa_input_template": template,
                      "required_checks": sorted(self.m.CONFIGURABLE_GATES), "image_spec": spec,
                      "next_action": "review-start-and-inspect-once"}
            if data["state"]["status"] == "technical_blocked":
                if data["owner"]:
                    act("finish")
                result["next_action"] = "terminal-technical-block"
                return self.receipt(batch_path, args.task_id, args.owner, result)
            return result
        record = data["state"]["attempts"][-1]
        if record["verdict"] == "PENDING":
            review = self.m.read_json(Path(args.visual_json))
            review.setdefault("reviewer", args.owner)
            review.setdefault("method", "direct-image-inspection")
            review_path = run / "staging" / args.image / (record["attempt_id"] + "-review.json")
            self.m.write_json(review_path, review)
            act("review", candidate=record["candidate"], prompt_file=record["prompt"], visual_json=str(review_path))
            data = self.m.read_json(journal)
        else:
            existing = self.m.read_json(Path(record["visual_qa"]))
            submitted = self.m.read_json(Path(args.visual_json))
            self.require(all(existing.get(k) == v for k, v in submitted.items()), "Already recorded different review")
        result = {"status": data["state"]["status"], "journal": str(journal),
                  "remaining": 3 - len(data["state"]["attempts"])}
        if result["status"] == "pending":
            result.update(next_action="targeted-retry-same-tool",
                          targeted_retry=self.m.read_json(Path(data["state"]["attempts"][-1]["visual_qa"]))["targeted_retry"])
            return result
        if data["owner"]:
            act("finish")
        result["next_action"] = "task-complete"
        return self.receipt(batch_path, args.task_id, args.owner, result)

    def collection(self, args):
        run, assignment, manifest = self.m.load_run(args.run_dir)

        batch_path = self.policy.batch_path(self.m, manifest, assignment)
        self.owned(batch_path, args.task_id, args.owner, "collection", run)
        group = manifest["collection"]
        if args.action == "prepare":
            if group["status"] == "awaiting_review":
                stored = group["sheets"][-1]
                self.require(self.m.sha256(Path(stored["index"])) == stored["index_sha256"], "Sheet index changed")
                index = self.m.read_json(Path(stored["index"]))
                self.require(self.m.sha256(Path(index["sheet"])) == index["sheet_sha256"], "Sheet changed")
            elif group["status"] == "complete":
                result = self.receipt(batch_path, args.task_id, args.owner,
                                      {"status": "complete", "next_action": "collection-already-complete"})
                self.queue_delivery(batch_path)
                return result
            else:
                index = self.m.image_tasks().shared(NS(run_dir=str(run)), self.m.review_workflow().build_sheet)
            if "skipped" in index:
                result = self.receipt(batch_path, args.task_id, args.owner,
                                      {"status": "complete", "next_action": "no-eligible-candidates"})
                self.queue_delivery(batch_path)
                return result
            return {"status": "awaiting_review", "sheet": index["sheet"], "index": index,
                    "next_action": "inspect-sheet-once",
                    "review_template": {"review_status": None, "checked": [], "observation": "",
                                        "verdict": None, "core_defects": [], "minor_issues": []}}
        if group["status"] == "awaiting_review":
            review = self.m.read_json(Path(args.review_json))
            index = self.m.read_json(Path(group["sheets"][-1]["index"]))
            review.setdefault("sheet_sha256", index["sheet_sha256"])
            review.setdefault("reviewer", args.owner)
            target = run / "collection" / f"submission-{len(group['reviews'])}.json"
            self.m.write_json(target, review)
            self.m.image_tasks().shared(NS(run_dir=str(run), review_json=str(target)),
                                       self.m.review_workflow().record_collection)
        else:
            self.require(group["reviews"], "No collection judgment to recover")
            saved = self.m.read_json(Path(group["reviews"][-1]["path"]))
            incoming = self.m.read_json(Path(args.review_json))
            self.require(all(saved.get(k) == v for k, v in incoming.items()), "Collection review differs")
        group = self.m.load_run(str(run))[2]["collection"]
        self.receipt(batch_path, args.task_id, args.owner, {"collection_status": group["status"]})
        with self.locked(batch_path.with_suffix(".lock")):
            batch = self.state(batch_path)
            source = next(k for k, v in batch["runs"].items() if Path(v) == run)
            if group["status"] == "repairing":
                deps = []
                states = self.m.load_run(str(run))[2]["images"]
                for image in group["repair_targets"]:
                    if states[image]["status"] != "pending":
                        continue
                    ident = source + "-repair-" + image
                    self.enqueue(batch, ident, "generation", source, {"run_dir": str(run), "image": image}, [args.task_id])
                    deps.append(ident)
                self.enqueue(batch, source + "-collection-1", "collection", source, {"run_dir": str(run)}, deps)
            self.m.write_json(batch_path, batch)
        self.queue_delivery(batch_path)
        return {"status": group["status"], "repair_images": group.get("repair_targets", []),
                "next_action": "dispatch-repairs" if group["status"] == "repairing" else "collection-complete"}

    def queue_delivery(self, path):
        with self.locked(path.with_suffix(".lock")):
            batch = self.state(path)
            collections = [t for t in batch["tasks"].values() if t["role"] == "collection"]
            if not collections or any(t["status"] != "complete" for t in collections):
                return
            runs = list(batch["runs"].values())
            if any(self.m.load_run(run)[2]["collection"]["status"] != "complete" for run in runs):
                return
            self.enqueue(batch, "delivery-all", "delivery", batch["sources"][0],
                         {"run_dirs": runs}, [t["id"] for t in collections])
            self.m.write_json(path, batch)

    def status(self, args):
        path = Path(args.batch).resolve()
        batch = self.state(path)
        images = []
        for source, filename in batch.get("runs", {}).items():
            run, assignment, manifest = self.m.load_run(filename)
            for image, projected in manifest["images"].items():
                journal = self.m.image_tasks().path(run, image)
                data = self.m.read_json(journal) if journal.exists() else {}
                state = data.get("state", projected)
                if journal.exists() and manifest.get("task_revisions", {}).get(image) == data.get("revision"):
                    state = projected
                phase = state["status"]
                action = {"pending": "start-or-targeted-retry", "awaiting_review": "submit-existing-observations",
                          "awaiting_collection": "finish-receipt-then-collection", "collection_accepted": "deliver",
                          "passed": "none"}.get(phase, "finish-terminal-receipt")
                if data.get("flight"):
                    action = "reconcile-flight"
                if batch["status"] in {"paused", "preflight_required"} and phase == "pending":
                    action = "wait-for-user-resume"
                images.append({"source": source, "image": image, "status": phase,
                               "remaining": 3 - len(state["attempts"]), "next_action": action,
                               "owner": data.get("owner"), "flight": data.get("flight")})
        return {"status": batch["status"], "tool": batch["execution"]["tool"], "images": images,
                "tasks": {k: {"status": t["status"], "owner": t["owner"]} for k, t in batch["tasks"].items()}}

    def resume(self, args):
        path = Path(args.batch).resolve()
        self.m.text(args.user_reply, "Actual user resume reply")
        evidence = self.m.read_json(Path(args.evidence))
        with self.locked(path.with_suffix(".lock")):
            batch = self.state(path)
            self.require(batch["status"] in {"paused", "preflight_required"}, "Batch is not paused")
            self.require(batch.get("pause", {}).get("category") != "safety_rejection",
                         "Safety rejection cannot be resumed as a service retry")
            preflight = self.policy.preflight(self.m, evidence, expected=batch["execution"]["tool"])
            if preflight["status"] != "ready":
                return {**preflight, "next_action": "restore-locked-tool"}
            batch.update(status="ready", preflight=preflight)
            self.event(batch, "user_resumed", user_reply=args.user_reply)
            self.m.write_json(path, batch)
        return self.status(args)

    def deliver(self, args):
        path = Path(args.batch).resolve()
        with self.locked(path.with_name(path.stem + ".workflow.lock")):
            batch = self.state(path)
            self.require(batch["status"] != "paused", "Restore paused batch before delivery")
            self.owned(path, args.task_id, args.owner, "delivery")
            runs = list(batch["runs"].values())
            self.require(bool(runs), "No runs to deliver")
            outcomes, final_paths, tier_distributions = [], [], []
            for filename in runs:
                run, assignment, manifest = self.m.load_run(filename)
                if manifest["status"] == "in_progress":
                    self.m.image_tasks().shared(NS(run_dir=str(run)))
                    manifest = self.m.load_run(filename)[2]
                    self.require(manifest["collection"]["status"] == "complete", "Collection unresolved")
                    for image, state in manifest["images"].items():
                        if state["status"] == "collection_accepted":
                            self.m.image_tasks().shared(NS(run_dir=str(run), image=image), self.m.cmd_promote)
                    self.m.image_tasks().shared(NS(run_dir=str(run), allow_partial=True), self.m.cmd_finalize)
                    manifest = self.m.load_run(filename)[2]
                for image, state in manifest["images"].items():
                    record = {"run": str(run), "image": image, "status": state["status"],
                              "attempts": len(state["attempts"]), "final": state["final_path"],
                              "final_sha256": state["final_sha256"]}
                    if state["status"] == "passed":
                        final = Path(state["final_path"])
                        self.require(final.is_file() and self.m.sha256(final) == state["final_sha256"],
                                     "Final file/hash mismatch")
                        final_paths.append(str(final))
                    outcomes.append(record)
                if assignment.get("exaggeration_policy", {}).get("mode") == "target-ratio":
                    planned = {t: sum(i["exaggeration"] == t for i in assignment["images"]) for t in "ABC"}
                    delivered = {t: sum(i["exaggeration"] == t and manifest["images"][i["id"]]["status"] == "passed"
                                        for i in assignment["images"]) for t in "ABC"}
                    tier_distributions.append({"run": assignment["run_name"], "target_ratio": {"A": 3, "B": 1, "C": 1},
                        "planned": planned, "delivered": delivered,
                        "missing": {t: planned[t] - delivered[t] for t in "ABC"}})
            output = Path(args.output or path.parent / "gallery").resolve()
            binding_path = path.parent / "delivery-inputs.json"
            binding = {"output": str(output), "outcomes": outcomes,
                       "assignments": {run: self.m.sha256(Path(run) / "assignment.json") for run in runs}}
            locales = self.m.read_json(Path(args.locales)) if getattr(args, "locales", None) else None
            if locales is not None:
                binding["locales_sha256"] = self.m.contract_hash(locales)
            if binding_path.exists():
                self.require(self.m.read_json(binding_path) == binding, "Delivery inputs/output changed")
            else:
                self.require(not output.exists(), "Use a fresh dedicated gallery directory")
                self.m.write_json(binding_path, binding)
            receipt_file = path.parent / "delivery.json"
            if receipt_file.exists():
                delivery = self.m.read_json(receipt_file)
                self.require(delivery["outcomes"] == outcomes, "Delivery state changed")
            else:
                # Exporter writes into a fresh directory; recover an interrupted receipt from index.html.
                if (output / "index.html").is_file():
                    gallery = str(output / "index.html")
                else:
                    exported = self.m.extension_module("export-gallery").export_gallery(runs, output,
                        None if batch["schema_version"] == 20 else batch.get("language", "zh"), locales)
                    gallery = exported["gallery"]
                delivery = {"gallery": gallery, "outcomes": outcomes, "passed": len(final_paths),
                            "expected": len(outcomes)}
            gallery = Path(delivery["gallery"])
            data = json.loads(re.search(r'<script id="gallery-data" type="application/json">(.*?)</script>',
                                        gallery.read_text(), re.S).group(1))
            self.require(len(data["groups"]) == len(runs), "Gallery source count mismatch")
            for filename, group in zip(runs, data["groups"]):
                _, frozen, manifest = self.m.load_run(filename)
                expected = {key: value["status"] for key, value in manifest["images"].items()}
                self.require(group["title"] == frozen.get("run_title", frozen["run_name"]) and group.get("task_outcomes") == expected,
                             "Gallery belongs to different run outcomes")
                self.require(group["passed"] == sum(v == "passed" for v in expected.values()), "Gallery count mismatch")
            assets = set()
            def collect(value):
                if isinstance(value, str) and value.startswith("assets/"):
                    assets.add(value)
                elif isinstance(value, dict):
                    for item in value.values():
                        collect(item)
                elif isinstance(value, list):
                    for item in value:
                        collect(item)
            collect(data)
            for asset in assets:
                file = gallery.parent / asset
                self.require(file.is_file() and self.m.sha256(file) == file.stem, "Gallery asset missing or changed")
            delivery.update(assets_checked=len(assets), gallery_sha256=self.m.sha256(gallery))
            index = path.parent / "delivery-index.md"
            index.write_text(f"# Comics: {len(final_paths)}/{len(outcomes)}\n\n" + "\n".join(
                f"- [{r['image']}]({r['final']})" if r["final"] else
                f"- {r['run']} / {r['image']}: {r['status']}" for r in outcomes))
            if tier_distributions:
                delivery["tier_distributions"] = tier_distributions
                with index.open("a") as handle:
                    handle.write("\n\n" + ("## 档位配比（A:B:C）" if batch.get("language", "zh") == "zh" else "## Tier distribution (A:B:C)") + "\n\n")
                    for row in tier_distributions:
                        counts = {k: ":".join(str(row[k][t]) for t in "ABC") for k in ("planned", "delivered", "missing")}
                        handle.write((f"- {row['run']}：目标 3:1:1；计划 {counts['planned']}；交付 {counts['delivered']}；缺项 {counts['missing']}。\n" if batch.get("language", "zh") == "zh" else
                            f"- {row['run']}: target 3:1:1; planned {counts['planned']}; delivered {counts['delivered']}; missing {counts['missing']}.\n"))
            if batch["schema_version"] == 20:
                lp = self.m.language_policy()
                first = self.m.read_json(Path(runs[0]) / "assignment.json")
                words = lp.locale(first, lp.effective(first, "communication"), "plan")
                titles = {}
                for run in runs:
                    saved = self.m.read_json(Path(run) / "assignment.json")
                    titles[saved["run_name"]] = saved["run_title"]
                    for image in saved["images"]:
                        titles[(str(Path(run)), image["id"])] = image["title"]
                lines = ["# " + batch["run_title"], ""]
                for row in outcomes:
                    title = titles.get((row["run"], row["image"]), row["image"])
                    lines.append(f"- [{title}]({row['final']})" if row["final"] else f"- {title}: {words['not_produced']}")
                lines += ["", words["delivery_tiers"]]
                for row in tier_distributions:
                    counts = {k: ":".join(str(row[k][t]) for t in "ABC") for k in ("planned", "delivered", "missing")}
                    lines.append(words["delivery_row"].format(run=titles.get(row["run"], row["run"]), **counts))
                index.write_text("\n".join(lines) + "\n")
            delivery["index"] = str(index)
            self.m.write_json(receipt_file, delivery)
            result = self.receipt(path, args.task_id, args.owner,
                                  {"delivery": str(receipt_file), "gallery": str(gallery)})
            with self.locked(path.with_suffix(".lock")):
                batch = self.state(path)
                batch["status"] = "complete"
                if not any(e["event"] == "delivered" for e in batch["events"]):
                    self.event(batch, "delivered")
                self.m.write_json(path, batch)
            return {**result, "passed": len(final_paths), "expected": len(outcomes),
                    **({"tier_distributions": tier_distributions} if tier_distributions else {})}

    def timing(self, args):
        batch = self.state(args.batch)
        def ts(value):
            return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
        def merge(values):
            result = []
            for a, b in sorted(values):
                if b <= a:
                    continue
                if result and a <= result[-1][1]:
                    result[-1][1] = max(b, result[-1][1])
                else:
                    result.append([a, b])
            return result
        sleeps = self.m.read_json(Path(args.sleep_json))["intervals"] if args.sleep_json else []
        sleeps = merge([(ts(a), ts(b)) for a, b in sleeps])
        def elapsed(a, b):
            return b - a - sum(max(0, min(b, d) - max(a, c)) for c, d in sleeps)
        spans = {}
        for role in self.roles.roles(batch["execution"]):
            spans[role] = [(ts(t["started_at"]), ts(t["finished_at"])) for t in batch["tasks"].values()
                           if t["role"] == role and t.get("started_at") and t.get("finished_at")]
        for task in batch["tasks"].values():
            stage = task["inputs"].get("stage") or (
                "cross-review" if task["inputs"].get("kind") == "cross-review" else None)
            if stage and task.get("started_at"):
                spans.setdefault(stage + "-queue", []).append((ts(task["queued_at"]), ts(task["started_at"])))
                if task.get("finished_at") and stage != task["role"]:
                    spans.setdefault(stage, []).append((ts(task["started_at"]), ts(task["finished_at"])))
        for filename in batch.get("runs", {}).values():
            run, _, manifest = self.m.load_run(filename)
            for image in manifest["images"]:
                journal = self.m.image_tasks().path(run, image)
                if not journal.exists():
                    continue
                starts = {}
                for e in self.m.read_json(journal)["events"]:
                    event, at = e["event"], ts(e["at"])
                    if event in {"request_preparation_started", "generation_started", "ingest_started",
                                 "image_returned", "automatic_check_completed", "single_review_started"}:
                        starts[event] = at
                    for begin, end, label in [
                        ("request_preparation_started", "generation_started", "request-preparation"),
                        ("generation_started", "ingest_started", "generation-to-ingest"),
                        ("ingest_started", "image_returned", "archive"),
                        ("image_returned", "automatic_check_completed", "automatic-check"),
                        ("automatic_check_completed", "single_review_started", "review-setup"),
                        ("single_review_started", "single_review_recorded", "single-review-and-record")]:
                        if event == end and begin in starts:
                            spans.setdefault(label, []).append((starts.pop(begin), at))
        for task in batch["tasks"].values():
            if not task.get("started_at") or not task.get("finished_at"):
                continue
            a, b = ts(task["started_at"]), ts(task["finished_at"])
            if task["role"] == "collection":
                manifest = self.m.load_run(task["inputs"]["run_dir"])[2]
                events = [e for e in manifest["events"] if a <= ts(e["at"]) <= b]
                sheet = next((ts(e["at"]) for e in events if e["event"] == "sheet_created"), None)
                review = next((ts(e["at"]) for e in events if e["event"] == "collection_review_recorded"), None)
                if sheet is not None and review is not None:
                    for name, x, y in [("collection-prepare", a, sheet),
                                       ("collection-review-and-record", sheet, review),
                                       ("collection-receipt", review, b)]:
                        spans.setdefault(name, []).append((x, y))
            elif task["role"] == "generation":
                run = Path(task["inputs"]["run_dir"])
                journal = self.m.image_tasks().path(run, task["inputs"]["image"])
                if journal.exists():
                    reviews = [ts(e["at"]) for e in self.m.read_json(journal)["events"]
                               if e["event"] == "single_review_recorded" and a <= ts(e["at"]) <= b]
                    if reviews:
                        spans.setdefault("post-review-receipt", []).append((max(reviews), b))
        metrics = {name: {"count": len(values), "worker_seconds": sum(elapsed(a, b) for a, b in values),
                         "union_seconds": sum(elapsed(a, b) for a, b in merge(values))}
                   for name, values in spans.items()}
        events = batch["events"]
        return {"sleep_excluded": bool(args.sleep_json), "stages": metrics,
                "elapsed_seconds": elapsed(ts(events[0]["at"]), ts(events[-1]["at"])) if events else 0,
                "limitations": "Generation-to-ingest includes dispatch/archive; not provider GPU time. Stage unions overlap."}

    def register(self, commands):
        p = commands.add_parser("planning-task")
        p.add_argument("action", choices=("concepts-submit", "selection-submit", "detail-submit"))
        for name in ("batch", "task-id", "owner", "input-json"):
            p.add_argument("--" + name, required=True)
        p.set_defaults(handler=self.m.extension_module("selection_contract").PlanningTasks(self).submit)
        handlers = {"batch-prepare": self.prepare, "batch-proposal": self.proposal, "batch-start": self.start,
                    "batch-status": self.status, "batch-resume": self.resume, "batch-deliver": self.deliver,
                    "task-packet": self.packet, "timing-summary": self.timing}
        for name, handler in handlers.items():
            p = commands.add_parser(name)
            p.add_argument("--batch", required=True)
            if name == "batch-prepare":
                p.add_argument("--spec", required=True)
            elif name == "batch-proposal":
                p.add_argument("--draft", action="append", required=True)
                p.add_argument("--review-json", required=True)
            elif name == "batch-start":
                p.add_argument("--confirmation", required=True)
                p.add_argument("--root", default="artifacts/whalechan-image-comic")
                p.add_argument("--slots", type=int, default=1)
            elif name == "batch-resume":
                p.add_argument("--user-reply", required=True)
                p.add_argument("--evidence", required=True)
            elif name == "batch-deliver":
                p.add_argument("--locales")
                p.add_argument("--output")
                p.add_argument("--task-id", required=True)
                p.add_argument("--owner", required=True)
            elif name == "task-packet":
                p.add_argument("--task", required=True)
            elif name == "timing-summary":
                p.add_argument("--sleep-json")
            p.set_defaults(handler=handler)
        p = commands.add_parser("collection-task")
        p.add_argument("action", choices=("prepare", "submit"))
        for name in ("run-dir", "task-id", "owner"):
            p.add_argument("--" + name, required=True)
        p.add_argument("--review-json")
        p.set_defaults(handler=self.collection)
