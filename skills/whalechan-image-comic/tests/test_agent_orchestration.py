"""Synthetic current orchestration tests; no model or image API calls."""
import argparse
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import test_manage_run as fixtures
import test_review_workflow as review_fixtures

m = fixtures.manage
roles = m.extension_module("agent_orchestration")


class ImageTaskTests(unittest.TestCase):
    image_task_workflow = True
    setUp = fixtures.RunStateTests.setUp
    initialize = fixtures.RunStateTests.initialize
    files = fixtures.RunStateTests.files
    candidate = review_fixtures.ReviewWorkflowTests.candidate

    def act(self, action, candidate=None, **overrides):
        args = dict(run_dir=str(self.run_dir), image=self.image, owner="worker-1", task_id="job-1",
                    provider="codex", model="test-model", candidate=None, prompt_file=None,
                    automatic_json=None, visual_json=None, provider_audit=None, transport="builtin",
                    category=None, evidence=None, action=action)
        if candidate:
            args.update(vars(candidate))
        args.update(overrides)
        return m.image_tasks().run(argparse.Namespace(**args))

    def record(self, candidate):
        self.act("begin", candidate)
        self.act("prepare", candidate)
        return self.act("review", candidate)

    def shared(self, command, **kwargs):
        args = m.parser().parse_args([command, "--run-dir", str(self.run_dir)] +
                                    [s for k, v in kwargs.items() for s in ("--" + k.replace("_", "-"), str(v))])
        return m.invoke(args)

    def block_others(self):
        saved = self.image
        for image in m.load_run(str(self.run_dir))[1]["images"]:
            if image["id"] != saved:
                self.image = image["id"]
                self.act("claim")
                self.act("block", evidence="Synthetic technical block")
                self.act("finish")
        self.image = saved

    def collection(self, fail=False):
        index = self.shared("build-review-sheet")
        review = {"review_status": "reviewed", "reviewer": "synthetic-collection-worker",
                  "sheet_sha256": index["sheet_sha256"], "observation": "Synthetic observation",
                  "checked": ["distinctness", "consistency", "overall"], "verdict": "FAIL" if fail else "PASS",
                  "minor_issues": [], "core_defects": [{"check": "consistency", "images": [self.image],
                      "detail": "Synthetic mismatch", "targeted_retry": "Match frozen style"}] if fail else []}
        path = self.run_dir / f"set-{index['round']}.json"
        m.write_json(path, review)
        return self.shared("record-collection-review", review_json=path)

    def test_whole_image_retry_collection_repair_shared_budget_and_export(self):
        self.act("claim")
        self.record(self.candidate(1, "FAIL"))
        self.record(self.candidate(2))
        self.act("finish")
        self.block_others()
        self.assertEqual(len(m.load_run(str(self.run_dir))[2]["images"][self.image]["attempts"]), 0)
        self.assertEqual(self.collection(True)["repair_images"], [self.image])
        self.act("claim", task_id="repair-1")
        args = self.candidate(3)
        for action in ("begin", "prepare", "review", "finish"):
            self.act(action, args, task_id="repair-1")
        self.assertEqual(self.collection()["status"], "complete")
        self.shared("promote", image=self.image)
        result = m.invoke(
            m.parser().parse_args(["finalize", "--run-dir", str(self.run_dir), "--allow-partial"]))
        self.assertEqual(result["passed"], 1)
        from test_gallery import gallery, payload
        group = payload(gallery.export_gallery([self.run_dir])["gallery"])["groups"][0]
        self.assertEqual((group["calls"], group["passed"]), (3, 1))
        self.assertEqual(len(group["collection_reviews"]), 2)

    def test_technical_failure_counts_and_no_retry(self):
        self.act("claim")
        args = self.candidate(1)
        Path(args.candidate).write_bytes(b"invalid returned image")
        self.act("begin", args)
        result = self.act("prepare", args)
        self.assertEqual((result["status"], result["remaining"]), ("technical_blocked", 2))
        with self.assertRaises(m.RunError):
            self.act("begin", args)
        self.act("finish")
        self.block_others()
        self.assertIn("skipped", self.shared("build-review-sheet"))

    def test_uncertain_call_cannot_be_reissued_and_recovery_fences_old_owner(self):
        self.act("claim")
        args = self.candidate(1)
        self.act("begin", args)
        with self.assertRaises(m.RunError):
            self.act("begin", args)
        self.act("recover", owner="replacement", task_id="recovery", evidence="Old process ended; returned staging file found")
        with self.assertRaises(m.RunError):
            self.act("prepare", args)
        with self.assertRaises(m.RunError):
            self.act("begin", args, owner="replacement", task_id="recovery")
        for action in ("prepare", "review", "finish"):
            self.act(action, args, owner="replacement", task_id="recovery")
        self.assertEqual(self.act("status")["state"]["status"], "awaiting_collection")

    def test_concurrent_claims_and_merge_are_exclusive_and_idempotent(self):
        cmd = [sys.executable, str(fixtures.MODULE_PATH), "image-task", "claim",
               "--run-dir", str(self.run_dir), "--image", self.image, "--task-id", "job"]
        def claim(owner):
            return subprocess.run(cmd + ["--owner", owner], capture_output=True, text=True).returncode
        with ThreadPoolExecutor(2) as pool:
            statuses = list(pool.map(claim, ["one", "two"]))
        self.assertEqual(sorted(statuses), [0, 2])
        data = self.act("status")
        self.act("block", owner=data["owner"], task_id="job", evidence="Synthetic block")
        self.act("finish", owner=data["owner"], task_id="job")
        merge = [sys.executable, str(fixtures.MODULE_PATH), "merge-tasks", "--run-dir", str(self.run_dir)]
        with ThreadPoolExecutor(2) as pool:
            codes = list(pool.map(lambda _: subprocess.run(merge, capture_output=True).returncode, range(2)))
        self.assertEqual(codes, [0, 0])
        manifest = m.load_run(str(self.run_dir))[2]
        self.assertEqual(manifest["images"][self.image]["status"], "technical_blocked")

    def test_interrupted_preparation_reuses_returned_bytes_without_new_slot(self):
        self.act("claim")
        args = self.candidate(1)
        self.act("begin", args)
        self.act("prepare", args)
        path = self.run_dir / "tasks" / self.image / "state.json"
        journal = m.read_json(path)
        record = journal["state"]["attempts"][-1]
        record["automatic_qa"] = None
        journal["flight"] = {"provider": args.provider, "model": args.model, "attempt": 1}
        m.write_json(path, journal)
        self.assertEqual(self.act("prepare", args)["remaining"], 2)
        self.act("review", args)
        self.act("finish")

    def test_queue_requires_frozen_runs_and_waits_for_completed_image_journals(self):
        root = self.run_dir / "queue-test"
        root.mkdir()
        policy = m.load_run(str(self.run_dir))[1]["execution"]
        m.write_json(root / "policy.json", policy)
        batch = root / "batch.json"
        def call(action, **values):
            args = dict(batch=str(batch), action=action, policy=str(root / "policy.json"), source=["A"],
                        task_json=None, task=None, worker=None, result=None, evidence=None,
                        slots=3, scope="subagents", external=0, provider="codex", provider_limit=None)
            return roles.Orchestration(m).run(argparse.Namespace(**{**args, **values}))
        call("init")
        for key, role in [("draw", "generation"), ("duplicate-draw", "generation"), ("set", "collection")]:
            inputs = {"run_dir": str(self.run_dir)}
            if role == "generation":
                inputs["image"] = self.image
            m.write_json(root / (key + ".json"), {"id": key, "role": role, "source": "A",
                                                "inputs": inputs, "depends_on": []})
            call("enqueue", task_json=str(root / (key + ".json")))
        self.assertEqual(call("claim", worker="worker-1")["next_task"]["id"], "draw")
        self.assertIsNone(call("next")["next_task"])
        self.act("claim", task_id="draw")
        args = self.candidate(1)
        self.act("begin", args, task_id="draw")
        call("recover", task="draw", worker="replacement", evidence="Old worker stopped; output located")
        self.assertIsNone(call("next")["next_task"])
        self.act("recover", owner="replacement", task_id="draw", evidence="Old worker stopped; output located")
        self.assertEqual(call("claim", task="draw", worker="replacement")["next_task"]["id"], "draw")
        for action in ("prepare", "review-start", "review", "finish"):
            self.act(action, args, owner="replacement", task_id="draw")
        self.block_others()
        call("recover", task="draw", worker="replacement", evidence="Journal finished; receipt was lost")
        self.assertEqual(call("claim", task="draw", worker="replacement")["next_task"]["id"], "draw")
        receipt = root / "receipt.json"
        m.write_json(receipt, {"task_id": "draw", "status": "complete"})
        call("finish", worker="replacement", task="draw", result=str(receipt))
        self.assertEqual(call("next")["next_task"]["id"], "set")
        call("claim", task="set", worker="reviewer")
        self.shared("build-review-sheet")
        call("recover", task="set", worker="reviewer", evidence="Reviewer stopped after sheet creation")
        self.assertEqual(call("claim", task="set", worker="reviewer")["next_task"]["id"], "set")
        altered = m.read_json(batch)
        altered["execution"]["role_limits"]["planning"] = 4
        m.write_json(batch, altered)
        with self.assertRaisesRegex(m.RunError, "approved batch"):
            call("next")


    def test_direct_commands_cannot_mutate_owned_image(self):
        args = self.candidate(1)
        with self.assertRaisesRegex(m.RunError, "image-task"):
            m.review_workflow().prepare(args)


class QueueTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.batch = self.root / "batch.json"
        self.policy = roles.execution({"batch_id": "test-batch"})
        m.write_json(self.root / "policy.json", self.policy)
        self.call("init", policy=str(self.root / "policy.json"), source=["A", "B"])

    def call(self, action, **kwargs):
        defaults = dict(batch=str(self.batch), policy=None, source=None, task_json=None, task=None, worker=None,
                        result=None, evidence=None, slots=3, scope="subagents", external=0,
                        provider="codex", provider_limit=None, action=action)
        return roles.Orchestration(m).run(argparse.Namespace(**{**defaults, **kwargs}))

    def enqueue(self, key, source="A", depends=None):
        path = self.root / (key + ".json")
        m.write_json(path, {"id": key, "role": "planning", "source": source, "inputs": {},
                           "depends_on": depends or []})
        self.call("enqueue", task_json=str(path))

    def finish(self, key, worker):
        path = self.root / (key + "-result.json")
        m.write_json(path, {"task_id": key, "status": "complete"})
        self.call("finish", task=key, worker=worker, result=str(path))

    def test_source_order_dependencies_idle_slots_and_reuse(self):
        self.enqueue("B1", "B")
        self.enqueue("A1")
        self.enqueue("A2", depends=["A1"])
        self.assertEqual(self.call("claim", worker="one", slots=1)["next_task"]["id"], "A1")
        self.assertIsNone(self.call("next", slots=1)["next_task"])
        self.finish("A1", "one")
        with self.assertRaisesRegex(m.RunError, "Idle"):
            self.call("claim", worker="new", slots=1)
        self.assertEqual(self.call("claim", worker="one", slots=1)["next_task"]["id"], "A2")
        self.finish("A2", "one")
        self.assertEqual(self.call("next", slots=1)["next_task"]["id"], "B1")

    def test_role_limits_and_capacity_examples(self):
        ready = {"generation": 30, "collection": 10}
        for slots, provider, generation, collection in [(3, "codex", 2, 1), (5, "codex", 3, 2),
                                                        (6, "openai", 5, 1), (7, "openai", 5, 2)]:
            actual = roles.targets(self.policy, slots, ready, provider)
            self.assertEqual((actual["generation"], actual["collection"]), (generation, collection))
        self.assertEqual(roles.targets(self.policy, 10, ready, "codex", 1)["generation"], 1)
        with self.assertRaises(ValueError):
            roles.execution({**self.policy, "role_limits": {**roles.DEFAULT_LIMITS, "planning": 11}})
