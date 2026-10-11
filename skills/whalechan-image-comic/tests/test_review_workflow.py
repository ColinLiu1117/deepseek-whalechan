"""Synthetic lifecycle tests; blank fixtures are never real visual acceptance evidence."""
import argparse
import copy
import subprocess
import unittest
from pathlib import Path

import test_manage_run as fixtures

m = fixtures.manage


class ReviewWorkflowTests(unittest.TestCase):
    current_review_workflow = True
    setUp = fixtures.RunStateTests.setUp
    initialize = fixtures.RunStateTests.initialize
    files = fixtures.RunStateTests.files

    def candidate(self, number, verdict="PASS", color="#aabbcc"):
        args = self.files(number, verdict)
        subprocess.run([self.magick, "-size", "1024x1024", f"xc:{color}", "-colorspace", "sRGB",
                        "-type", "TrueColor", args.candidate], check=True)
        old = m.read_json(Path(args.visual_json))
        digest = m.sha256(Path(args.candidate))
        form = old["evidence"]["form_evidence"]
        form["candidate_sha256"] = digest
        value = {"review_status": "reviewed", "reviewer": "synthetic-test",
                 "method": "direct-image-inspection", "checked": sorted(m.CONFIGURABLE_GATES),
                 "panels": old["observation"]["panels"], "text_transcription": self.image_spec["core_text"],
                 "verdict": verdict, "core_defects": [] if verdict == "PASS" else [
                     {"check": "J1", "detail": "Synthetic missing visual payoff"}],
                 "minor_issues": [], "targeted_retry": None if verdict == "PASS" else "Restore the approved action",
                 "form_evidence": form}
        m.write_json(Path(args.visual_json), value)
        return args

    def prepare(self, args):
        return m.review_workflow().prepare(args)

    def record(self, args):
        self.prepare(args)
        return m.record_image(args, False)

    def block_others(self):
        frozen = m.read_json(self.run_dir / "assignment.json")
        for spec in frozen["images"]:
            if spec["id"] != self.image:
                m.review_workflow().block(argparse.Namespace(run_dir=str(self.run_dir), image=spec["id"], reason="Synthetic technical block"))
    def collection(self, fail=False):
        w = m.review_workflow()
        index = w.build_sheet(argparse.Namespace(run_dir=str(self.run_dir)))
        review = {"review_status": "reviewed", "reviewer": "synthetic-set-test",
                  "sheet_sha256": index["sheet_sha256"], "observation": "Synthetic set comparison",
                  "checked": ["distinctness", "consistency", "overall"],
                  "verdict": "FAIL" if fail else "PASS", "minor_issues": [],
                  "core_defects": [{"check": "consistency", "images": [self.image],
                                    "detail": "Synthetic identity mismatch across the set",
                                    "targeted_retry": "Match the approved identity"}] if fail else []}
        path = self.run_dir / f"review-{index['round']}.json"
        m.write_json(path, review)
        return w.record_collection(argparse.Namespace(run_dir=str(self.run_dir), review_json=str(path)))

    def test_single_review_minor_tolerance_and_collection_before_promotion(self):
        args = self.candidate(1)
        qa = m.read_json(Path(args.visual_json))
        qa["minor_issues"] = [{"check": "V1", "detail": "Tiny mouth curvature; same calm emotion"}]
        m.write_json(Path(args.visual_json), qa)
        self.assertEqual(self.record(args)["verdict"], "PASS")
        with self.assertRaisesRegex(m.RunError, "already be reviewed"):
            m.record_image(args, False)
        with self.assertRaisesRegex(m.RunError, "collection"):
            m.cmd_promote(argparse.Namespace(run_dir=str(self.run_dir), image=self.image))
        self.block_others()
        self.assertEqual(self.collection()["status"], "complete")
        result = m.cmd_promote(argparse.Namespace(run_dir=str(self.run_dir), image=self.image))
        self.assertTrue(Path(result["final"]).is_file())
        self.assertEqual(m.cmd_finalize(argparse.Namespace(run_dir=str(self.run_dir), allow_partial=True))["passed"], 1)

    def test_only_one_collection_repair_and_shared_three_candidate_budget(self):
        self.record(self.candidate(1, "FAIL"))
        self.record(self.candidate(2))
        self.block_others()
        self.assertEqual(self.collection(True)["repair_images"], [self.image])
        self.record(self.candidate(3, color="red"))
        self.assertEqual(self.collection(True)["status"], "complete")
        state = m.load_run(str(self.run_dir))[2]["images"][self.image]
        self.assertEqual((state["status"], len(state["attempts"])), ("collection_failed", 3))
        with self.assertRaises(m.RunError):
            self.prepare(self.candidate(4))
        with self.assertRaises(m.RunError):
            self.collection()
        self.assertEqual(m.cmd_finalize(argparse.Namespace(run_dir=str(self.run_dir), allow_partial=True))["passed"], 0)
    def test_technical_failure_counts_image_and_never_regenerates(self):
        args = self.candidate(1)
        subprocess.run([self.magick, "-size", "300x500", "xc:red", args.candidate], check=True)
        result = self.prepare(args)
        self.assertEqual(result["status"], "technical_blocked")
        self.assertIsNone(result["attempt"]["visual_qa"])
        with self.assertRaisesRegex(m.RunError, "not ready"):
            self.prepare(self.candidate(2))
        self.block_others()
        self.assertIn("skipped", m.review_workflow().build_sheet(argparse.Namespace(run_dir=str(self.run_dir))))
        result = m.cmd_finalize(argparse.Namespace(run_dir=str(self.run_dir), allow_partial=True))
        self.assertEqual(result["status"], "partial")

    def test_invalid_review_does_not_consume_another_image_or_invent_pass(self):
        args = self.candidate(1)
        self.prepare(args)
        qa = m.read_json(Path(args.visual_json)); original = copy.deepcopy(qa)
        for field, value in [("review_status", "pending"), ("checked", ["J1"]),
                             ("text_transcription", ["incorrect"]), ("candidate_sha256", "0" * 64),
                             ("core_defects", [{"check": "J1", "detail": "Missing punchline"}])]:
            bad = copy.deepcopy(original); bad[field] = value
            m.write_json(Path(args.visual_json), bad)
            with self.subTest(field=field), self.assertRaises(m.RunError):
                m.record_image(args, False)
        state = m.load_run(str(self.run_dir))[2]["images"][self.image]
        self.assertEqual((len(state["attempts"]), state["status"]), (1, "awaiting_review"))
        m.write_json(Path(args.visual_json), original)
        self.assertEqual(m.record_image(args, False)["verdict"], "PASS")

    def test_set_repair_cannot_reopen_exhausted_task(self):
        self.record(self.candidate(1, "FAIL"))
        self.record(self.candidate(2, "FAIL"))
        self.record(self.candidate(3))
        self.block_others()
        result = self.collection(True)
        self.assertEqual((result["status"], result["repair_images"]), ("complete", []))
        with self.assertRaises(m.RunError):
            m.cmd_promote(argparse.Namespace(run_dir=str(self.run_dir), image=self.image))

    def test_sheet_hash_and_original_images_are_bound(self):
        args = self.candidate(1)
        digest = m.sha256(Path(args.candidate))
        self.record(args); self.block_others()
        index = m.review_workflow().build_sheet(argparse.Namespace(run_dir=str(self.run_dir)))
        self.assertEqual(len(index["items"]), 5)
        self.assertEqual(sum(i["candidate"] is None for i in index["items"]), 4)
        self.assertEqual(m.sha256(Path(args.candidate)), digest)
        result = subprocess.check_output([self.magick, "identify", "-format", "%wx%h", index["sheet"]], text=True)
        self.assertEqual(result, "1864x1320")
        Path(index["sheet"]).write_bytes(b"changed")
        with self.assertRaisesRegex(m.RunError, "sheet changed"):
            m.review_workflow().record_collection(argparse.Namespace(run_dir=str(self.run_dir), review_json="unused"))

    def test_all_five_pass_export_preserves_set_review_and_minor_issues(self):
        from test_gallery import gallery, payload
        frozen = m.read_json(self.run_dir / "assignment.json")
        for n, image in enumerate(frozen["images"], 1):
            self.image_spec, self.image = image, image["id"]
            args = self.candidate(n)
            qa = m.read_json(Path(args.visual_json))
            qa["minor_issues"] = [{"check": "V1", "detail": "Synthetic minor issue"}]
            m.write_json(Path(args.visual_json), qa)
            self.record(args)
        self.collection()
        for image in frozen["images"]:
            m.cmd_promote(argparse.Namespace(run_dir=str(self.run_dir), image=image["id"]))
        m.cmd_finalize(argparse.Namespace(run_dir=str(self.run_dir), allow_partial=False))
        group = payload(gallery.export_gallery([self.run_dir])["gallery"])["groups"][0]
        self.assertEqual((group["passed"], group["calls"]), (5, 5))
        self.assertEqual(len(group["collection_reviews"]), 1)
        self.assertEqual(group["warnings"], [])
        self.assertTrue(group["proposals"][0]["images"][0]["attempts"][0]["minor_issues"])
        self.assertTrue(group["stage_events"])

    def test_new_prompt_and_confirmation_describe_tolerant_single_review(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("new_builder", fixtures.SKILL_ROOT / "scripts/build-prompt.py")
        builder = importlib.util.module_from_spec(spec); spec.loader.exec_module(builder)
        frozen = m.read_json(self.run_dir / "assignment.json")
        prompt = builder.build_prompt(frozen, frozen["images"][0])
        self.assertIn(frozen["images"][0]["expression_plan"][0]["visual_description"], prompt)
        self.assertNotIn("do not impose mathematically straight mouths", prompt)
        self.assertNotIn("Manpu allowance:", prompt)
        plan = m.plan_markdown(frozen)
        self.assertIn("技术检查失败不触发生图", plan)
        legacy = copy.deepcopy(frozen); legacy["schema_version"] = 14
        self.assertNotEqual(m.selection_summary(frozen)["summary_sha256"], m.selection_summary(legacy)["summary_sha256"])

    def test_missing_file_blocks_without_another_generation(self):
        args = self.candidate(1); Path(args.candidate).unlink()
        self.assertEqual(self.prepare(args)["status"], "technical_blocked")
        with self.assertRaisesRegex(m.RunError, "not ready"):
            self.prepare(self.candidate(2))

    def test_sheet_places_all_five_images_in_their_numbered_cells(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("sheet_test", fixtures.SKILL_ROOT / "scripts/build-review-sheet.py")
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        colors = ["FF0000", "00FF00", "0000FF", "FFFF00", "FF00FF"]
        items = []
        for n, color in enumerate(colors):
            path = self.run_dir / f"color-{n}.png"
            subprocess.run([self.magick, "-size", "400x200", f"xc:#{color}", str(path)], check=True)
            items.append({"candidate": str(path), "sha256": m.sha256(path)})
        output = self.run_dir / "five-slots.png"
        module.compose(items, output)
        for n, color in enumerate(colors):
            x, y = 16 + n % 3 * 616 + 300, 16 + n // 3 * 652 + 36 + 300
            pixel = subprocess.check_output([self.magick, str(output), "-format", f"%[hex:p{{{x},{y}}}]", "info:"], text=True)
            self.assertEqual(pixel[:6], color)
        # Wide originals must be letterboxed, not cover-cropped or stretched.
        pixel = subprocess.check_output([self.magick, str(output), "-format", "%[hex:p{316,60}]", "info:"], text=True)
        self.assertEqual(pixel[:6], "FFFFFF")

    def test_undecodable_return_stays_counted_and_exports_as_technical_failure(self):
        from test_gallery import gallery, payload
        args = self.candidate(1); Path(args.candidate).write_bytes(b"not a PNG")
        result = self.prepare(args)
        self.assertEqual(result["status"], "technical_blocked")
        self.block_others()
        m.review_workflow().build_sheet(argparse.Namespace(run_dir=str(self.run_dir)))
        m.cmd_finalize(argparse.Namespace(run_dir=str(self.run_dir), allow_partial=True))
        group = payload(gallery.export_gallery([self.run_dir])["gallery"])["groups"][0]
        self.assertEqual((group["passed"], group["calls"]), (0, 1))
        attempt = group["proposals"][0]["images"][0]["attempts"][0]
        self.assertTrue(attempt["defects"])
        self.assertIsNone(attempt["picture"]["src"])


if __name__ == "__main__":
    unittest.main()
