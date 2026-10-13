"""Offline v19 fixtures: invented content and reviews, never production approval."""
import copy
from types import SimpleNamespace as NS
import hashlib
import math
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import test_manage_run as fixtures
import test_batch_workflow as batch_fixtures
m = fixtures.manage
selection = m.extension_module("selection_contract")


def draft(n=5, source="source-a"):
    base = fixtures.assignment()
    value = copy.deepcopy(base)
    for key in ("duels", "tie_breaks", "confirmation"):
        value.pop(key, None)
    value.update(schema_version=19, target_images=n, source_id=source, run_name=source,
                 author_agent_ids=["author"], concept_task_id="concepts-" + source)
    value["execution"].update(planning_mode=selection.METHOD)
    value["execution"]["role_limits"]["selection"] = 2
    value["creative_pool"] = []
    value["images"], value["proposal"]["options"] = [], []
    for i in range(2 * n):
        candidate = copy.deepcopy(base["creative_pool"][i % 5])
        candidate.update(id=f"idea_{i+1:02d}", premise=f"premise {i+1}", scene=f"scene {i+1}",
                         punchline=f"punchline {i+1}", key_lines=[f"任务 {i+1}", f"独有结果 {i+1}"])
        value["creative_pool"].append(candidate)
        if i < n:
            option = copy.deepcopy(base["proposal"]["options"][i % 5])
            option.update(idea_id=candidate["id"], premise=candidate["premise"], scene=candidate["scene"],
                          twist=candidate["punchline"], key_lines=candidate["key_lines"])
            value["proposal"]["options"].append(option)
            image = copy.deepcopy(base["images"][i % 5])
            image.update(name=f"comic_{i+1}", idea_id=candidate["id"], source_rank=i+1,
                         premise=candidate["premise"], core_text=candidate["key_lines"])
            value["images"].append(image)
    value["pool_sha256"] = selection.pool(m, value, verify_hash=False)
    value["selection_reason"] = "Synthetic overall priority and set variety."
    value["selection_review"] = {
        "review_method": selection.METHOD, "reviewer_agent_id": "reviewer",
        "selection_task_id": "selection-" + source, "selection_reason": value["selection_reason"],
        **{k: value[k] for k in ("source_id", "target_images", "pool_sha256")},
        "ranking": [{"idea_id": c["id"], "reason": f"Synthetic priority {i+1}"}
                    for i, c in enumerate(value["creative_pool"])]}
    value["ranked_ideas"] = [c["id"] for c in value["creative_pool"][:n]]
    return value


class SelectionTests(unittest.TestCase):
    def test_n_and_frozen_priority_contract(self):
        for n in (1, 2, 3, 5, 6, 10, 51):
            with self.subTest(n=n):
                value = draft(n)
                summary = m.plan_summary(value)
                self.assertEqual((summary["image_count"], summary["maximum_total"]), (n, 3*n))
                self.assertEqual(len(summary["standings"]), 2*n)
        for n in (0, -1, True, 1.5, "5", None):
            with self.subTest(n=n), self.assertRaises(ValueError):
                selection.count(n)

    def test_invalid_ranking_and_frozen_text(self):
        changes = [
            lambda v: v.update(duels=[]),
            lambda v: v["selection_review"].update(reviewer_agent_id="author"),
            lambda v: v["selection_review"]["ranking"].pop(),
            lambda v: v["selection_review"]["ranking"][1].update(idea_id="idea_01"),
            lambda v: v["selection_review"]["ranking"][0].update(idea_id="idea_99"),
            lambda v: v["creative_pool"][0].update(scene="tampered"),
            lambda v: v["images"].reverse(),
            lambda v: v["images"][0].update(core_text=["changed", "text"]),
            lambda v: v["proposal"]["options"][0].update(key_lines=["changed"]),
        ]
        for change in changes:
            value = draft()
            change(value)
            with self.assertRaises((ValueError, m.RunError)):
                m.plan_summary(value)

    def test_v18_normalized_golden_hash_and_prompts(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "draft.json"
            m.write_json(path, fixtures.assignment())
            value = m.validate_assignment(path)
            self.assertEqual(m.selection_summary(value)["summary_sha256"],
                             "9e0854857be82a34f8a2f87fcbab0657eac67e2078800e6fc286cae28c659f83")
            expected = ["24e816489a3b1e09f275d631c1b0767cb244dd101e0729cd1e25f9717831b5b3",
                        "18a91c74bb365154d6d8bd1797448d019c1f282871e6149dded83be299d30478",
                        "23fa02e4a160f284b9d98c55464ad0295f7c1c633bbe5f6a43b73eae89e894cb",
                        "2138aafca0f709d0d3fb2ac5769721dfa80cecbfe1723f07a4554f71d19bd19a",
                        "adf94df4ee6dc8e00c65e9209d0748d7cb66144861500516fd798dadab0b697b"]
            self.assertEqual([hashlib.sha256(m.visual_prompt().render(value, i).encode()).hexdigest()
                              for i in value["images"]], expected)

    def test_dynamic_sheet_slots_and_multi_digit_labels(self):
        module = m.extension_module("build-review-sheet")
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "source.png"
            subprocess.run(["magick", "-size", "80x40", "xc:red", str(source)], check=True)
            original = source.read_bytes()
            for n in (1, 2, 3, 5, 6, 10):
                output = root / f"sheet-{n}.png"
                items = [{"candidate": str(source) if i == 0 else None,
                          "sha256": hashlib.sha256(original).hexdigest() if i == 0 else None}
                         for i in range(n)]
                module.compose(items, output, dynamic=True)
                cols = math.ceil(math.sqrt(n))
                rows = math.ceil(n/cols)
                result = subprocess.check_output(["magick", "identify", "-format", "%wx%h", str(output)]).decode()
                self.assertEqual(result, f"{cols*600+(cols+1)*16}x{rows*636+(rows+1)*16}")
                if n == 10:
                    # Second digit of slot 10's '10' label has its own black pixels.
                    x, y = 16 + 616 + 20, 16 + 2*652
                    pixel = subprocess.check_output(["magick", str(output), "-format",
                                                     f"%[pixel:p{{{x},{y}}}]", "info:"]).decode()
                    self.assertIn("17,24,39", pixel)
            legacy = root / "legacy.png"
            module.compose([{"candidate": str(source) if i == 0 else None,
                             "sha256": hashlib.sha256(original).hexdigest() if i == 0 else None}
                            for i in range(5)], legacy)
            self.assertEqual(subprocess.check_output(["magick", "compare", "-metric", "AE",
                str(legacy), str(root / "sheet-5.png"), "null:"], stderr=subprocess.STDOUT).decode(), "0")
            self.assertEqual(source.read_bytes(), original)


class PlanningTests(unittest.TestCase):
    save = batch_fixtures.BatchWorkflowTests.save
    cli = batch_fixtures.BatchWorkflowTests.cli
    claim = batch_fixtures.BatchWorkflowTests.claim

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.batch = self.root / "batch.json"
        self.workflow = m.extension_module("batch_workflow").BatchWorkflow(m)

    def prepare(self, counts=(5,)):
        spec = {"sources": [{"id": f"source-{chr(97+i)}", "text": "input", "target_images": n}
                            for i, n in enumerate(counts)], "language": "zh",
                "execution": {"batch_id": "synthetic-v19"},
                "availability": {"builtin": {"available": True, "evidence": "synthetic tools"}},
                "language_evidence": {"source": "synthetic"}}
        return self.cli("batch-prepare", "--spec", self.save("spec.json", spec))

    def submit(self, stage, owner, value, source="source-a"):
        return self.cli("planning-task", stage + "-submit", "--task-id", stage + "-" + source,
                        "--owner", owner, "--input-json", self.save(stage + "-input.json", value))

    def concepts(self, n=5, source="source-a", owner="author"):
        value = draft(n, source)
        self.claim("concepts-" + source, owner)
        self.submit("concepts", owner, {k: value[k] for k in ("input", "creative_pool")}, source)
        return value

    def select(self, value, owner="reviewer"):
        source = value["source_id"]
        self.claim("selection-" + source, owner)
        result = self.submit("selection", owner, {k: value["selection_review"][k] for k in
                                               ("ranking", "selection_reason")}, source)
        return m.read_json(Path(result["output"]))

    def finish_plan(self, n=5, source="source-a"):
        value = self.concepts(n, source)
        value.update(self.select(value))
        self.claim("detail-" + source, "author")
        return self.submit("detail", "author", value, source)

    def test_pipeline_mixed_n_and_confirmation(self):
        self.prepare((1, 3, 6))
        paths = [self.finish_plan(n, f"source-{chr(97+i)}")["output"] for i, n in enumerate((1, 3, 6))]
        batch = self.workflow.state(self.batch)
        self.assertFalse(batch["runs"])
        self.assertEqual(len(batch["tasks"]), 9)
        review = self.save("cross.json", {"review_status": "reviewed", "sources": batch["sources"],
                                        "observation": "Synthetic cross-source observation."})
        args = [a for p in paths for a in ("--draft", p)]
        proposal = self.cli("batch-proposal", *args, "--review-json", review)
        self.assertIn("总计：10张；最多30次", Path(proposal["rendered"]).read_text())
        confirm = self.save("confirmation.json", {"user_reply": "Synthetic approval",
                                                "summary_sha256": proposal["summary_sha256"]})
        result = self.cli("batch-start", "--confirmation", confirm, "--root", self.root / "runs", "--slots", 3)
        self.assertEqual([len(m.load_run(r)[1]["images"]) for r in result["runs"].values()], [1, 3, 6])
        timing = self.cli("timing-summary")["stages"]
        for stage in ("concepts", "selection", "detail", "selection-queue"):
            self.assertEqual(timing[stage]["count"], 3)

    def test_no_bypass_or_self_review_and_cross_source_dispatch(self):
        self.prepare((2, 2))
        a = self.concepts(2)
        with self.assertRaises(m.RunError):
            self.claim("selection-source-a", "author")
        self.concepts(2, "source-b", "reviewer")
        result = self.cli("agent-batch", "next", "--worker", "reviewer", "--slots", 3)
        self.assertEqual(result["next_task"]["id"], "selection-source-a")
        with self.assertRaises(m.RunError):
            self.claim("selection-source-a", "main")
        with self.assertRaises(m.RunError):
            self.cli("batch-proposal", "--draft", self.save("arbitrary.json", a),
                     "--draft", self.save("another.json", a), "--review-json", self.save("cross.json", {}))
        self.claim("selection-source-a", "reviewer")
        with self.assertRaises(m.RunError):
            self.cli("agent-batch", "finish", "--task", "selection-source-a", "--worker", "reviewer",
                     "--result", self.save("fake.json", {"status": "complete", "task_id": "selection-source-a"}))

    def test_selection_receipt_crash_preserves_reviewer_and_rank(self):
        self.prepare((1,))
        value = self.concepts(1)
        self.claim("selection-source-a", "reviewer")
        original = m.write_json
        def fail_state(path, data):
            if Path(path).resolve() == self.batch.resolve():
                raise OSError("synthetic crash before task checkpoint")
            return original(path, data)
        submitted = {k: value["selection_review"][k] for k in ("ranking", "selection_reason")}
        input_path = self.save("selection-crash.json", submitted)
        with patch.object(m, "write_json", side_effect=fail_state), self.assertRaises(OSError):
            selection.PlanningTasks(self.workflow).submit(NS(batch=str(self.batch), action="selection-submit",
                task_id="selection-source-a", owner="reviewer", input_json=input_path))
        saved = (self.root / "source-a-selection.json").read_bytes()
        self.cli("agent-batch", "recover", "--task", "selection-source-a", "--worker", "replacement",
                 "--evidence", "Synthetic terminated reviewer; existing frozen output")
        self.claim("selection-source-a", "replacement")
        self.submit("selection", "replacement", submitted)
        self.assertEqual(saved, (self.root / "source-a-selection.json").read_bytes())
        self.assertEqual(self.workflow.state(self.batch)["tasks"]["detail-source-a"]["preferred_owner"], "author")
        with self.assertRaises(m.RunError):
            self.claim("detail-source-a", "replacement")

    def test_recovered_concept_contributors_all_excluded(self):
        self.prepare((1,))
        self.claim("concepts-source-a", "author")
        self.cli("agent-batch", "recover", "--task", "concepts-source-a", "--worker", "coauthor",
                 "--evidence", "Synthetic author terminated after contributing")
        self.claim("concepts-source-a", "coauthor")
        value = draft(1)
        self.submit("concepts", "coauthor", {k: value[k] for k in ("input", "creative_pool")})
        for owner in ("author", "coauthor"):
            with self.assertRaises(m.RunError):
                self.claim("selection-source-a", owner)

    def test_three_slot_targets_and_single_slot_identity(self):
        roles = m.extension_module("agent_orchestration")
        policy = roles.execution({"batch_id": "test", "planning_mode": selection.METHOD})
        self.assertEqual(roles.targets(policy, 3, {"planning": 5, "selection": 2})["planning"], 2)
        self.assertEqual(roles.targets(policy, 3, {"planning": 5, "selection": 2})["selection"], 1)
        self.prepare((1,))
        self.concepts(1)
        result = self.cli("agent-batch", "next", "--worker", "author", "--slots", 1)
        self.assertIsNone(result["next_task"])
        with self.assertRaises(m.RunError):
            self.cli("agent-batch", "claim", "--worker", "reviewer", "--slots", 1)
        self.cli("agent-batch", "release", "--worker", "author", "--evidence", "Synthetic runtime termination")
        self.cli("agent-batch", "claim", "--worker", "reviewer", "--slots", 1)

    files = batch_fixtures.BatchWorkflowTests.files
    candidate = batch_fixtures.BatchWorkflowTests.candidate
    act = batch_fixtures.BatchWorkflowTests.act
    render_review = batch_fixtures.BatchWorkflowTests.render_review

    def test_n2_complete_partial_empty_delivery_and_gallery(self):
        self.magick = __import__("shutil").which("magick")
        if not self.magick:
            self.skipTest("ImageMagick required")
        for passed in (2, 1, 0):
            with self.subTest(passed=passed):
                self.batch = self.root / f"batch-{passed}" / "batch.json"
                self.prepare((2,))
                output = self.finish_plan(2)["output"]
                cross = self.save("cross.json", {"review_status": "reviewed", "sources": ["source-a"],
                                               "observation": "Synthetic cross-source review"})
                proposal = self.cli("batch-proposal", "--draft", output, "--review-json", cross)
                confirmation = self.save("confirm.json", {"user_reply": "Synthetic approval",
                    "summary_sha256": proposal["summary_sha256"]})
                result = self.cli("batch-start", "--confirmation", confirmation,
                                  "--root", self.root / f"runs-{passed}", "--slots", 3)
                self.run_dir = Path(result["runs"]["source-a"])
                frozen = m.load_run(str(self.run_dir))[1]
                for i, spec in enumerate(frozen["images"]):
                    self.image_spec, self.image = spec, spec["id"]
                    self.task = "source-a-gen-" + self.image
                    self.claim(self.task)
                    if i < passed:
                        self.render_review(i+1)
                    else:
                        self.act("start")
                        bad = self.root / "bad.png"
                        bad.write_bytes(b"synthetic corrupt provider image")
                        result = self.act("ingest", candidate=bad)
                        self.assertEqual(result["status"], "technical_blocked")
                task = "source-a-collection-0"
                self.claim(task)
                args = ["--run-dir", str(self.run_dir), "--task-id", task, "--owner", "worker"]
                prepared = m.invoke(m.parser().parse_args(["collection-task", "prepare", *args]))
                if passed:
                    index = m.read_json(self.run_dir / "collection/review-00/index.json")
                    self.assertEqual(len(index["items"]), 2)
                    self.assertEqual(sum(bool(i["candidate"]) for i in index["items"]), passed)
                    again = m.invoke(m.parser().parse_args(["collection-task", "prepare", *args]))
                    self.assertEqual(again["sheet"], prepared["sheet"])
                    review = self.save("set.json", {"review_status": "reviewed",
                        "checked": ["distinctness", "consistency", "overall"],
                        "observation": "Synthetic set comparison", "verdict": "PASS",
                        "core_defects": [], "minor_issues": []})
                    m.invoke(m.parser().parse_args(["collection-task", "submit", *args, "--review-json", review]))
                self.claim("delivery-all")
                result = self.cli("batch-deliver", "--task-id", "delivery-all", "--owner", "worker")
                self.assertEqual((result["passed"], result["expected"]), (passed, 2))
                html = Path(result["gallery"]).read_text()
                import json
                data = json.loads(html.split('<script id="gallery-data" type="application/json">')[1].split("</script>")[0])
                group = data["groups"][0]
                self.assertEqual((group["planned"], group["passed"]), (2, passed))
                self.assertEqual(len(group["proposals"]), 4)
                self.assertEqual(len(group["selection_review"]["ranking"]), 4)
