"""Offline v18 protocol tests. Synthetic pixels/observations are not real visual approvals."""
import argparse
import copy
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import test_manage_run as fixtures
import test_review_workflow as qa_fixtures

m = fixtures.manage


class BatchWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.batch = self.root / "batch.json"
        self.workflow = m.extension_module("batch_workflow").BatchWorkflow(m)
        self.native = {"builtin": {"available": True, "evidence": "Synthetic runtime tool-list fixture"}}
        self.magick = __import__("shutil").which("magick")
        if not self.magick:
            self.skipTest("ImageMagick required")
        spec = {"schema_version": 18, "sources": [{"id": "source-a", "text": "input"}],
                "execution": {"batch_id": "test-v18"}, "language": "zh",
                "availability": self.native, "language_evidence": {"source": "synthetic user fixture"}}
        self.spec = self.save("spec.json", spec)
        self.cli("batch-prepare", "--spec", self.spec)

    def save(self, name, value):
        path = self.root / name
        m.write_json(path, value)
        return str(path)

    def cli(self, command, *args):
        tokens = [command, "--batch", str(self.batch), *map(str, args)]
        return m.invoke(m.parser().parse_args(tokens))

    def initialize(self):
        draft = fixtures.assignment()
        draft["execution"] = self.workflow.state(self.batch)["execution"]
        draft.pop("confirmation")
        draft_path = self.save("draft.json", draft)
        review = self.save("cross.json", {"review_status": "reviewed", "sources": ["source-a"],
                                         "observation": "Synthetic authored source comparison"})
        proposal = self.cli("batch-proposal", "--draft", draft_path, "--review-json", review)
        confirm = self.save("confirmation.json", {"user_reply": "Synthetic authorization, not a real user",
                            "summary_sha256": proposal["summary_sha256"]})
        result = self.cli("batch-start", "--confirmation", confirm, "--root", self.root / "runs", "--slots", 3)
        self.run_dir = Path(result["runs"]["source-a"])
        self.frozen = m.load_run(str(self.run_dir))[1]
        self.image_spec = self.frozen["images"][0]
        self.image = self.image_spec["id"]
        self.task = "source-a-gen-" + self.image
        self.claim(self.task)
        return confirm

    def claim(self, task, owner="worker"):
        return self.cli("agent-batch", "claim", "--task", task, "--worker", owner, "--slots", 3)

    def act(self, action, **kwargs):
        tokens = ["image-task", action, "--run-dir", str(self.run_dir), "--image", self.image,
                  "--owner", "worker", "--task-id", self.task]
        for key, value in kwargs.items():
            tokens += ["--" + key.replace("_", "-"), str(value)]
        return m.invoke(m.parser().parse_args(tokens))

    files = fixtures.RunStateTests.files
    candidate = qa_fixtures.ReviewWorkflowTests.candidate

    def render_review(self, number=1, verdict="PASS", retry=None):
        start = self.act("start", **({"retry_prompt": retry} if retry else {}))
        self.assertEqual(start["next_action"], "call-locked-tool-once")
        image = self.candidate(number, verdict)
        self.act("ingest", candidate=image.candidate)
        self.act("review-start")
        result = self.act("submit", visual_json=image.visual_json)
        return result, image

    def test_provider_preflight_is_local_and_selects_available_tool(self):
        policy = m.extension_module("provider_policy")
        with patch.dict(os.environ, {"OPENAI_API_KEY": "secret-test-only"}, clear=True):
            result = policy.preflight(m, {"builtin": {"available": False, "evidence": "not present"}})
            self.assertEqual(result["tool"]["provider"], "openai")
            self.assertNotIn("secret-test-only", json.dumps(result))
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(policy.preflight(m, {})["status"], "blocked")

    def test_confirmation_and_tool_are_bound_and_start_is_repeatable(self):
        confirm = self.initialize()
        before = list((self.root / "runs").iterdir())
        result = self.cli("batch-start", "--confirmation", confirm, "--root", self.root / "runs", "--slots", 3)
        self.assertEqual(list((self.root / "runs").iterdir()), before)
        value = copy.deepcopy(self.frozen)
        value["execution"]["tool"]["provider"] = "openai"
        value["execution"]["tool"]["transport"] = "api"
        with self.assertRaisesRegex(m.RunError, "stale"):
            m.validate_approval(value)
        self.assertEqual(result["status"], "ready")

    def test_combined_image_and_receipt_recovery(self):
        self.initialize()
        result, candidate = self.render_review()
        self.assertEqual(result["status"], "awaiting_collection")
        before = m.read_json(self.run_dir / "tasks" / self.image / "state.json")
        again = self.act("submit", visual_json=candidate.visual_json)
        after = m.read_json(self.run_dir / "tasks" / self.image / "state.json")
        self.assertEqual(before, after)
        self.assertEqual(result["receipt"], again["receipt"])
        self.assertEqual(self.workflow.state(self.batch)["tasks"][self.task]["status"], "complete")

    def test_failed_visual_stays_on_same_tool_and_budget(self):
        self.initialize()
        result, _ = self.render_review(1, "FAIL")
        self.assertEqual(result["next_action"], "targeted-retry-same-tool")
        prompt = self.root / "retry.txt"
        prompt.write_text("Restore the approved action. Exact same text and cast.")
        result, _ = self.render_review(2, "PASS", str(prompt))
        self.assertEqual(result["remaining"], 1)
        journal = m.read_json(self.run_dir / "tasks" / self.image / "state.json")
        self.assertEqual([a["provider"] for a in journal["state"]["attempts"]], ["codex", "codex"])

    def test_service_error_pauses_new_calls_and_resume_preserves_tool(self):
        self.initialize()
        self.act("start")
        self.act("error", provider="codex", model="unknown", category="quota", evidence="Synthetic proven no image")
        self.assertEqual(self.cli("batch-status")["status"], "paused")
        with self.assertRaisesRegex((ValueError, m.RunError), "paused"):
            self.act("start")
        with self.assertRaisesRegex(m.RunError, "No task"):
            self.claim("source-a-gen-" + self.frozen["images"][1]["id"], "worker-2")
        evidence = self.save("availability.json", self.native)
        self.cli("batch-resume", "--evidence", evidence, "--user-reply", "Synthetic resume authorization")
        self.assertEqual(self.act("start")["tool"]["provider"], "codex")
        journal = m.read_json(self.run_dir / "tasks" / self.image / "state.json")
        self.assertEqual(len(journal["state"]["attempts"]), 0)
        self.assertEqual(journal["flight"]["attempt"], 1)

    def test_uncertain_error_never_reissues_and_can_ingest_during_pause(self):
        self.initialize()
        self.act("start")
        self.act("uncertain", provider="codex", model="unknown", category="timeout", evidence="Unknown result")
        self.assertEqual(self.act("start")["next_action"], "reconcile-flight")
        image = self.candidate(1)
        self.act("ingest", candidate=image.candidate)
        self.assertEqual(self.cli("batch-status")["status"], "paused")
        self.act("review-start")
        self.act("submit", visual_json=image.visual_json)
        journal = m.read_json(self.run_dir / "tasks" / self.image / "state.json")
        self.assertEqual(len(journal["state"]["attempts"]), 1)

    def test_invalid_visual_report_does_not_invent_pass(self):
        self.initialize()
        self.act("start")
        image = self.candidate(1)
        output = self.act("ingest", candidate=image.candidate)
        self.assertIsNone(output["qa_input_template"]["verdict"])
        bad = m.read_json(Path(image.visual_json))
        bad["checked"] = []
        bad_path = self.save("bad-review.json", bad)
        with self.assertRaisesRegex(m.RunError, "14 visual checks"):
            self.act("submit", visual_json=bad_path)
        journal = m.read_json(self.run_dir / "tasks" / self.image / "state.json")
        self.assertEqual(journal["state"]["status"], "awaiting_review")
        self.assertEqual(len(journal["state"]["attempts"]), 1)

    def test_complete_collection_delivery_and_timing(self):
        self.initialize()
        self.render_review()
        for index, spec in enumerate(self.frozen["images"][1:], 2):
            self.image_spec, self.image = spec, spec["id"]
            self.task = "source-a-gen-" + self.image
            self.claim(self.task)
            self.render_review(index)
        task = "source-a-collection-0"
        self.claim(task)
        def collection(action, *rest):
            return m.invoke(m.parser().parse_args(["collection-task", action, "--run-dir", str(self.run_dir),
                            "--task-id", task, "--owner", "worker", *rest]))
        sheet = collection("prepare")
        self.assertEqual(collection("prepare")["sheet"], sheet["sheet"])
        review = self.save("set.json", {"review_status": "reviewed", "checked": ["distinctness", "consistency", "overall"],
                         "observation": "Synthetic set only", "verdict": "PASS", "core_defects": [], "minor_issues": []})
        collection("submit", "--review-json", review)
        self.claim("delivery-all")
        result = self.cli("batch-deliver", "--owner", "worker", "--task-id", "delivery-all")
        self.assertEqual((result["passed"], result["expected"]), (5, 5))
        again = self.cli("batch-deliver", "--owner", "worker", "--task-id", "delivery-all")
        self.assertEqual(result, again)
        timing = self.cli("timing-summary")
        self.assertEqual(timing["stages"]["single-review-and-record"]["count"], 5)
        self.assertFalse(timing["sleep_excluded"])


    def test_tool_capability_preflight_and_locked_provider_rejection(self):
        self.initialize()
        request = self.act("start")["request_file"]
        data = m.read_json(Path(request))
        data["output"]["resolution"] = {"mode": "explicit", "width": 1024, "height": 1024}
        explicit = self.save("explicit.json", data)
        with patch.dict(os.environ, {"OPENAI_API_KEY": "synthetic-secret", "PATH": os.environ["PATH"]}, clear=True):
            checked = self.workflow.policy.preflight(m, self.native, [explicit])
        self.assertEqual(checked["tool"]["provider"], "openai")
        with self.assertRaisesRegex((ValueError, m.RunError), "locked|mismatch"):
            self.act("error", provider="openai", model="unknown", category="service", evidence="No image")
        journal = m.read_json(self.run_dir / "tasks" / self.image / "state.json")
        self.assertIsNotNone(journal["flight"])

    def test_receipt_failure_recovers_without_another_review(self):
        self.initialize()
        self.act("start")
        candidate = self.candidate(1)
        self.act("ingest", candidate=candidate.candidate)
        self.act("review-start")
        original = m.write_json
        def interrupted(path, data):
            if Path(path).parent.name == "receipts":
                raise OSError("synthetic receipt interruption")
            return original(path, data)
        with patch.object(m, "write_json", side_effect=interrupted):
            with self.assertRaisesRegex(OSError, "receipt interruption"):
                self.act("submit", visual_json=candidate.visual_json)
        before = m.read_json(self.run_dir / "tasks" / self.image / "state.json")
        self.assertIsNone(before["owner"])
        result = self.act("submit", visual_json=candidate.visual_json)
        after = m.read_json(self.run_dir / "tasks" / self.image / "state.json")
        self.assertEqual(before, after)
        self.assertTrue(Path(result["receipt"]).is_file())

    def test_interrupted_initialization_reuses_same_directory(self):
        # Build a real bound proposal, then interrupt initialization after frozen assignment output.
        draft = fixtures.assignment()
        draft["execution"] = self.workflow.state(self.batch)["execution"]
        draft.pop("confirmation")
        proposal = self.cli("batch-proposal", "--draft", self.save("draft.json", draft),
            "--review-json", self.save("cross.json", {"review_status": "reviewed",
               "sources": ["source-a"], "observation": "Synthetic comparison"}))
        confirmation = self.save("confirmation.json", {"user_reply": "Synthetic authorization",
                                                     "summary_sha256": proposal["summary_sha256"]})
        original = m.write_json
        def interrupted(path, data):
            if Path(path).name == "manifest.json":
                raise OSError("synthetic init interruption")
            return original(path, data)
        with patch.object(m, "write_json", side_effect=interrupted):
            with self.assertRaisesRegex(OSError, "init interruption"):
                self.cli("batch-start", "--confirmation", confirmation, "--root", self.root / "runs")
        result = self.cli("batch-start", "--confirmation", confirmation, "--root", self.root / "runs")
        self.assertEqual(len(list((self.root / "runs").iterdir())), 1)
        self.assertEqual(m.load_run(result["runs"]["source-a"])[1]["schema_version"], 18)

    def test_all_technical_blocks_skip_collection_and_deliver_partial(self):
        self.initialize()
        for index, spec in enumerate(self.frozen["images"], 1):
            self.image_spec, self.image = spec, spec["id"]
            self.task = "source-a-gen-" + self.image
            if index > 1:
                self.claim(self.task)
            self.act("start")
            candidate = self.candidate(index)
            subprocess.run([self.magick, "-size", "100x200", "xc:red", candidate.candidate], check=True)
            self.assertEqual(self.act("ingest", candidate=candidate.candidate)["status"], "technical_blocked")
        task = "source-a-collection-0"
        self.claim(task)
        result = m.invoke(m.parser().parse_args(["collection-task", "prepare", "--run-dir", str(self.run_dir),
                     "--task-id", task, "--owner", "worker"]))
        self.assertEqual(result["next_action"], "no-eligible-candidates")
        self.claim("delivery-all")
        result = self.cli("batch-deliver", "--owner", "worker", "--task-id", "delivery-all")
        self.assertEqual(result["passed"], 0)

    def test_second_image_already_in_flight_is_preserved_after_pause(self):
        self.initialize()
        first_image, first_task = self.image, self.task
        self.act("start")
        self.image = self.frozen["images"][1]["id"]
        self.task = "source-a-gen-" + self.image
        self.claim(self.task, "worker-2")
        def second(action, *extra):
            return m.invoke(m.parser().parse_args(["image-task", action, "--run-dir", str(self.run_dir),
               "--image", self.image, "--task-id", self.task, "--owner", "worker-2", *extra]))
        second("start")
        second("error", "--provider", "codex", "--model", "unknown", "--category", "service", "--evidence", "No image")
        self.image, self.task = first_image, first_task
        candidate = self.candidate(1)
        self.act("ingest", candidate=candidate.candidate)
        self.act("review-start")
        self.act("submit", visual_json=candidate.visual_json)
        self.assertEqual(self.cli("batch-status")["status"], "paused")


    def test_collection_repair_shared_budget_and_interrupted_sheet(self):
        self.initialize()
        self.render_review()
        for index, spec in enumerate(self.frozen["images"][1:], 2):
            self.image_spec, self.image = spec, spec["id"]
            self.task = "source-a-gen-" + self.image
            self.claim(self.task)
            self.render_review(index)
        selected = self.frozen["images"][0]
        self.image_spec, self.image = selected, selected["id"]
        task = "source-a-collection-0"
        self.claim(task)
        def collection(action, *rest):
            return m.invoke(m.parser().parse_args(["collection-task", action, "--run-dir", str(self.run_dir),
                 "--task-id", task, "--owner", "worker", *rest]))
        original = m.write_json
        def interrupted(path, data):
            if Path(path).name == "manifest.json" and data.get("collection", {}).get("status") == "awaiting_review":
                raise OSError("synthetic sheet checkpoint interruption")
            return original(path, data)
        with patch.object(m, "write_json", side_effect=interrupted):
            with self.assertRaisesRegex(OSError, "sheet checkpoint"):
                collection("prepare")
        sheet = collection("prepare")
        sheet_hash = m.sha256(Path(sheet["sheet"]))
        self.assertEqual(m.sha256(Path(collection("prepare")["sheet"])), sheet_hash)
        fail = {"review_status": "reviewed", "checked": ["distinctness", "consistency", "overall"],
                "observation": "Synthetic set mismatch", "verdict": "FAIL", "minor_issues": [],
                "core_defects": [{"check": "consistency", "images": [self.image],
                                 "detail": "Synthetic mismatch", "targeted_retry": "Restore identity"}]}
        review = self.save("set-fail.json", fail)
        self.assertEqual(collection("submit", "--review-json", review)["status"], "repairing")
        self.task = "source-a-repair-" + self.image
        self.claim(self.task)
        retry = self.root / "repair-prompt.txt"
        retry.write_text("Restore the planned identity and exact visible text.")
        self.render_review(6, "FAIL", str(retry))
        self.render_review(7, "PASS", str(retry))
        task = "source-a-collection-1"
        self.claim(task)
        collection("prepare")
        result = collection("submit", "--review-json", review)
        self.assertEqual(result["status"], "complete")
        manifest = m.load_run(str(self.run_dir))[2]
        self.assertEqual(manifest["images"][self.image]["status"], "collection_failed")
        self.assertEqual(len(manifest["images"][self.image]["attempts"]), 3)
        self.assertEqual(len(manifest["collection"]["reviews"]), 2)
        self.assertNotIn("source-a-collection-2", self.workflow.state(self.batch)["tasks"])

    def test_v17_confirmation_hash_is_unchanged_from_previous_commit(self):
        value = fixtures.assignment()
        value["schema_version"] = 17
        value["execution"].pop("tool")
        value.pop("confirmation")
        self.assertEqual(m.selection_summary(value)["summary_sha256"],
                         "6e80780de94b70e816d80c9f319ab152ada92974cf94547958cee81645d5b7ae")

    def test_two_sources_share_one_confirmation_and_one_tool(self):
        # Reuse prepare with a new batch; no independent per-source pools.
        self.batch = self.root / "two-batch.json"
        spec = m.read_json(Path(self.spec))
        spec["sources"].append({"id": "source-b", "text": "input"})
        self.cli("batch-prepare", "--spec", self.save("two-spec.json", spec))
        drafts = []
        for source in ("a", "b"):
            value = fixtures.assignment()
            value["run_name"] = "source-" + source
            value["execution"] = self.workflow.state(self.batch)["execution"]
            value.pop("confirmation")
            drafts += ["--draft", self.save(source + ".json", value)]
        review = self.save("two-cross.json", {"review_status": "reviewed", "sources": ["source-a", "source-b"],
                              "observation": "Synthetic acknowledged structural similarity"})
        result = self.cli("batch-proposal", *drafts, "--review-json", review)
        confirm = self.save("two-confirm.json", {"user_reply": "Synthetic one confirmation",
                                              "summary_sha256": result["summary_sha256"]})
        result = self.cli("batch-start", "--confirmation", confirm, "--root", self.root / "two-runs", "--slots", 5)
        self.assertEqual((self.root / "proposal.md").read_text().count(m.PLAN_TEXT["zh"]["question"]), 1)
        self.assertEqual(len(result["runs"]), 2)
        executions = [m.load_run(run)[1]["execution"] for run in result["runs"].values()]
        self.assertEqual(executions[0], executions[1])
        self.assertEqual(sum(t["role"] == "generation" for t in self.workflow.state(self.batch)["tasks"].values()), 10)


    def test_api_tool_uses_combined_image_flow_without_codex_transport(self):
        self.batch = self.root / "api-batch.json"
        spec = m.read_json(Path(self.spec))
        spec["availability"] = {"builtin": {"available": False, "evidence": "Synthetic absent tool"}}
        with patch.dict(os.environ, {"OPENAI_API_KEY": "synthetic-secret", "PATH": os.environ["PATH"]}, clear=True):
            self.cli("batch-prepare", "--spec", self.save("api-spec.json", spec))
            self.initialize()
            result, _ = self.render_review()
        self.assertEqual(result["status"], "awaiting_collection")
        attempt = m.read_json(self.run_dir / "tasks" / self.image / "state.json")["state"]["attempts"][0]
        self.assertEqual(attempt["provider"], "openai")
        self.assertIsNone(attempt["transport"])

    def test_heic_source_display_conversion_preserves_original(self):
        gallery = m.extension_module("export-gallery")
        source = self.root / "source.heic"
        subprocess.run([self.magick, "-size", "64x64", "xc:blue", str(source)],
                       check=True, capture_output=True)
        sha = m.sha256(source)
        reader = gallery.RunReader.__new__(gallery.RunReader)
        reader.assets = self.root / "assets"
        reader.assets.mkdir()
        reader.warnings = []
        result = reader.picture(source, "synthetic source", sha, "source")
        self.assertTrue(result["src"].endswith(".png"))
        self.assertEqual(m.sha256(source), sha)
        self.assertEqual(m.sha256(self.root / result["original_src"]), sha)

    def test_concurrent_pause_and_begin_cannot_start_after_pause(self):
        import sys
        from concurrent.futures import ThreadPoolExecutor
        self.initialize()
        self.act("start")
        second = self.frozen["images"][1]["id"]
        second_task = "source-a-gen-" + second
        self.claim(second_task, "worker-2")
        base = [sys.executable, str(fixtures.MODULE_PATH), "image-task"]
        error = base + ["error", "--run-dir", str(self.run_dir), "--image", self.image,
                       "--owner", "worker", "--task-id", self.task, "--provider", "codex",
                       "--model", "unknown", "--category", "service", "--evidence", "Synthetic proven no image"]
        begin = base + ["start", "--run-dir", str(self.run_dir), "--image", second,
                       "--owner", "worker-2", "--task-id", second_task]
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(subprocess.run, cmd, capture_output=True, text=True) for cmd in (error, begin)]
            results = [f.result() for f in futures]
        self.assertEqual(results[0].returncode, 0, results[0].stderr)
        self.assertIn(results[1].returncode, (0, 2))
        batch = self.workflow.state(self.batch)
        self.assertEqual(batch["status"], "paused")
        pause = next(e["at"] for e in batch["events"] if e["event"] == "service_paused")
        journal = self.run_dir / "tasks" / second / "state.json"
        if journal.exists():
            for event in m.read_json(journal)["events"]:
                if event["event"] == "generation_started":
                    self.assertLessEqual(event["at"], pause)
