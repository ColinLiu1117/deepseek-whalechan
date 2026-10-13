"""v19 frozen 2N candidate pool and independent priority ranking."""
from __future__ import annotations
import re

METHOD = "independent-priority-ranking"
POOL_FIELDS = ("source_id", "target_images", "input", "creative_pool", "author_agent_ids", "concept_task_id")


def count(value):
    if type(value) is not int or value < 1:
        raise ValueError("target_images must be a positive integer")
    return value


def pool(manager, value, verify_hash=True):
    n = count(value.get("target_images"))
    manager.text(value.get("source_id"), "source_id")
    manager.text(value.get("concept_task_id"), "concept_task_id")
    authors = manager.string_list(value.get("author_agent_ids"), "author_agent_ids")
    if len(set(authors)) != len(authors) or any(a in {"main", "/root"} for a in authors):
        raise ValueError("Pool requires distinct actual sub-agent authors")
    source = value.get("input")
    if not isinstance(source, dict):
        raise ValueError("Candidate input is required")
    anchor = manager.text(source.get("fact_anchor"), "input.fact_anchor")
    manager.native_direction(source.get("source_analysis", {}).get("native_direction"), "native_direction")
    ideas = value.get("creative_pool")
    if not isinstance(ideas, list) or len(ideas) != 2 * n:
        raise ValueError("creative_pool must contain exactly 2N candidates")
    ids = []
    for idea in ideas:
        if not isinstance(idea, dict) or not re.fullmatch(r"idea_[0-9]{2,}", str(idea.get("id", ""))):
            raise ValueError("Each candidate requires a stable idea_NN id")
        ids.append(idea["id"])
        for key in ("premise", "scene", "punchline", "mechanism"):
            manager.text(idea.get(key), "candidate." + key)
        if idea.get("fact_anchor") != anchor:
            raise ValueError("Candidate fact anchor differs from source")
        if any(key in idea for key in ("gate", "gate_reason", "rejection_reason", "score")):
            raise ValueError("Candidates are ranked, not rejected or pre-scored by the author")
        manager.direction_carriers(idea, idea["id"])
        manager.string_list(idea.get("key_lines"), "candidate.key_lines")
        if len(manager.string_list(idea.get("personality"), "candidate.personality", 2)) != 2:
            raise ValueError("Candidate requires two personality traits")
    if len(set(ids)) != 2 * n:
        raise ValueError("Candidate ids must be unique")
    digest = manager.contract_hash({key: value[key] for key in POOL_FIELDS})
    if verify_hash and value.get("pool_sha256") != digest:
        raise ValueError("Frozen candidate pool changed")
    return digest


def ranking(manager, value):
    if any(key in value for key in ("duels", "tie_breaks", "tournament_results")):
        raise ValueError("v19 cannot mix priority selection with tournament records")
    pool(manager, value)
    if value.get("execution", {}).get("planning_mode") != METHOD:
        raise ValueError("v19 requires independent-priority-ranking execution")
    review = value.get("selection_review")
    if not isinstance(review, dict) or review.get("review_method") != METHOD:
        raise ValueError("Independent selection_review is required")
    for key in ("source_id", "target_images", "pool_sha256"):
        if review.get(key) != value[key]:
            raise ValueError("Selection review does not bind the candidate pool")
    reviewer = manager.text(review.get("reviewer_agent_id"), "reviewer_agent_id")
    if reviewer in value["author_agent_ids"] or reviewer in {"main", "/root"}:
        raise ValueError("Candidate authors/main cannot review this pool")
    manager.text(review.get("selection_task_id"), "selection_task_id")
    manager.text(review.get("selection_reason"), "selection_reason")
    if review.get("selection_reason") != value.get("selection_reason"):
        raise ValueError("Selection reason differs from recorded reviewer decision")
    items = review.get("ranking")
    ids = {idea["id"] for idea in value["creative_pool"]}
    if not isinstance(items, list) or len(items) != len(ids):
        raise ValueError("Ranking must contain all 2N candidates")
    seen = set()
    for item in items:
        if not isinstance(item, dict) or set(item) != {"idea_id", "reason"}:
            raise ValueError("Ranking rows require idea_id and a short reason")
        if item["idea_id"] not in ids or item["idea_id"] in seen:
            raise ValueError("Ranking contains duplicate or unknown ids")
        manager.text(item["reason"], "ranking.reason")
        seen.add(item["idea_id"])
    if value.get("ranked_ideas") != [item["idea_id"] for item in items[:count(value["target_images"])]]:
        raise ValueError("ranked_ideas must be the first N priority-ranked candidates")
    return items


class PlanningTasks:
    """Freeze content and complete its queue dependency in one locked submission."""
    def __init__(self, workflow):
        self.w, self.m = workflow, workflow.m

    def submit(self, args):
        from pathlib import Path
        w, m = self.w, self.m
        path = Path(args.batch).resolve()
        stage = args.action.removesuffix("-submit")
        role = "selection" if stage == "selection" else "planning"
        with w.locked(path.with_suffix(".lock")):
            batch = w.state(path)
            w.require(batch.get("schema_version") == 19, "Planning tasks require v19")
            task = batch["tasks"].get(args.task_id)
            w.require(task and task["role"] == role and task["inputs"].get("stage") == stage and
                      task["owner"] == args.owner and task["status"] in {"running", "complete"},
                      "Planning task owner/role/stage/status mismatch")
            w.require(args.owner not in {"main", "/root"}, "Main agent only orchestrates")
            source = next(s for s in batch["inventory"] if s["id"] == task["source"])
            output = Path(task["inputs"]["output"])
            supplied = m.read_json(Path(args.input_json))
            w.require(isinstance(supplied, dict), "Planning submission must be an object")
            if task["status"] == "complete":
                receipt = m.read_json(Path(task["result"]))
                w.require(m.sha256(Path(task["result"])) == task["result_sha256"] and
                          m.sha256(output) == receipt["output_sha256"], "Completed planning record changed")
                return {**receipt, "receipt": task["result"]}
            if stage == "concepts":
                w.require({"input", "creative_pool"} <= set(supplied), "Concepts require input and creative_pool")
                w.require(not any(k in supplied for k in
                    ("ranked_ideas", "selection_review", "duels", "tie_breaks", "proposal", "images")),
                    "Concepts contain concise candidates, not winners or detailed plans")
                value = {key: supplied[key] for key in ("input", "creative_pool")}
                value.update(source_id=source["id"], target_images=source["target_images"],
                    author_agent_ids=task.get("contributors", [args.owner]), concept_task_id=task["id"])
                if source["files"]:
                    content = value["input"].get("content")
                    content = content if isinstance(content, list) else [content]
                    w.require([str(Path(x).resolve()) for x in content] == [f["path"] for f in source["files"]],
                              "Candidate source paths differ")
                    w.require(all(m.sha256(Path(f["path"])) == f["sha256"] for f in source["files"]), "Source changed")
                else:
                    w.require(value["input"].get("content") == source["text"], "Candidate source text differs")
                # After a crash, a saved pool is immutable; recovery only repairs its receipt.
                if output.exists():
                    saved = m.read_json(output)
                    pool(m, saved)
                    w.require(all(saved[k] == value[k] for k in
                        ("input", "creative_pool", "source_id", "target_images", "concept_task_id")),
                        "Frozen candidate pool changed; do not generate replacements")
                    value = saved
                else:
                    value["pool_sha256"] = pool(m, value, verify_hash=False)
                next_id = "selection-" + source["id"]
                next_role = "selection"
                inputs = {"stage": "selection", "source": source, "pool_file": str(output),
                          "output": str(path.parent / (source["id"] + "-selection.json"))}
            elif stage == "selection":
                frozen = m.read_json(Path(task["inputs"]["pool_file"]))
                pool(m, frozen)
                w.require(args.owner not in frozen["author_agent_ids"], "Authors cannot select their own candidates")
                w.require(set(supplied) <= {"ranking", "selection_reason", "attention_points"},
                          "Submit ranking/reason only; identity and selected IDs are bound by the script")
                w.require(isinstance(supplied.get("ranking"), list) and
                          all(isinstance(row, dict) for row in supplied["ranking"]), "ranking must be an ordered list of objects")
                review = {**supplied, "review_method": METHOD, "reviewer_agent_id": args.owner,
                          "selection_task_id": task["id"],
                          **{k: frozen[k] for k in ("source_id", "target_images", "pool_sha256")}}
                value = {**frozen, "execution": batch["execution"], "selection_review": review,
                         "selection_reason": supplied.get("selection_reason"),
                         "ranked_ideas": [r.get("idea_id") for r in supplied.get("ranking", [])[:frozen["target_images"]]]}
                if output.exists():
                    saved = m.read_json(output)
                    ranking(m, saved)
                    w.require(saved["pool_sha256"] == frozen["pool_sha256"] and
                              all(saved["selection_review"].get(k) == supplied.get(k) for k in
                                  ("ranking", "selection_reason", "attention_points")),
                              "Frozen selection changed; recovery cannot rerank")
                    value = saved
                ranking(m, value)
                next_id, next_role = "detail-" + source["id"], "planning"
                inputs = {"stage": "detail", "source": source, "pool_file": task["inputs"]["pool_file"],
                          "selection_file": str(output),
                          "output": str(path.parent / (source["id"] + "-draft.json"))}
            else:
                frozen = m.read_json(Path(task["inputs"]["selection_file"]))
                ranking(m, frozen)
                w.require(all(supplied.get(k) == frozen[k] for k in
                    (*POOL_FIELDS, "pool_sha256", "execution", "selection_review", "ranked_ideas", "selection_reason")),
                    "Detailed plans must preserve frozen candidates and selection")
                w.require(supplied.get("schema_version") == 19, "Detail requires schema v19")
                if "exaggeration_policy" in source:
                    w.require(supplied.get("exaggeration_policy") == source["exaggeration_policy"],
                              "Detail must preserve the source tier policy from its task packet")
                value = m.validate_assignment(Path(args.input_json), require_approval=False)
                if output.exists():
                    w.require(m.read_json(output) == value, "Frozen detail changed")
                next_id = None
            m.write_json(output, value)
            receipt_path = path.parent / "receipts" / (task["id"] + ".json")
            receipt = {"task_id": task["id"], "stage": stage, "status": "complete",
                       "output": str(output), "output_sha256": m.sha256(output)}
            m.write_json(receipt_path, receipt)
            task.update(status="complete", finished_at=m.now(), result=str(receipt_path),
                        result_sha256=m.sha256(receipt_path))
            batch["workers"][args.owner] = None
            w.event(batch, "finish", task=task["id"], worker=args.owner, stage=stage)
            if next_id:
                w.enqueue(batch, next_id, next_role, source["id"], inputs, [task["id"]])
                if stage == "selection":
                    concept = batch["tasks"][value["concept_task_id"]]
                    batch["tasks"][next_id]["preferred_owner"] = concept["owner"]
            m.write_json(path, batch)
            return {**receipt, "receipt": str(receipt_path), "next_task": next_id}
