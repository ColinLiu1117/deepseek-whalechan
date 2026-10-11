"""Pure drawing prompts, informed planning and historical recovery contracts."""
import argparse
import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import test_manage_run as fixtures

m = fixtures.manage
spec = importlib.util.spec_from_file_location("visual_builder", fixtures.SKILL_ROOT / "scripts/build-prompt.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class PromptContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "assignment.json"
        self.value = fixtures.assignment()

    def normalize(self, value=None):
        value = self.value if value is None else value
        self.path.write_text(json.dumps(fixtures.confirm_fixture_plan(value)))
        return m.validate_assignment(self.path)

    def test_visual_plan_precedes_confirmation_and_survives_initialization(self):
        value = self.value
        value["images"][0]["action_plan"][0]["action"] = "  She places the comma on the desk.  "
        value["images"][0]["references"][0]["instruction"] = "  Use only the lettering.  "
        fixtures.confirm_fixture_plan(value)
        before = m.selection_summary(value)["summary_sha256"]
        self.path.write_text(json.dumps(value))
        result = m.cmd_init(argparse.Namespace(assignment=str(self.path),
                           root=str(Path(self.tmp.name) / "runs"), effective_parallelism=1))
        run, frozen, manifest = m.load_run(result["run_dir"])
        self.assertEqual(frozen["schema_version"], 16)
        self.assertEqual(m.selection_summary(frozen)["summary_sha256"], before)
        self.assertEqual(manifest["review_workflow_version"], 1)
        self.assertTrue(all(i["qa_contract_version"] == 11 for i in frozen["images"]))
        self.assertTrue(builder.build_prompt(frozen, frozen["images"][0]))

    def test_visual_edits_invalidate_approval(self):
        changes = [lambda i: i["action_plan"][0].update(action="The door remains visibly closed."),
                   lambda i: i["expression_plan"][0].update(visual_description="She closes her eyes in sleep."),
                   lambda i: i["dialogue_plan"][0].update(placement="below her hand"),
                   lambda i: i.update(lettering_description="Thin red lettering.")]
        for change in changes:
            value = copy.deepcopy(self.value)
            change(value["images"][0])
            with self.subTest(change=change), self.assertRaisesRegex(m.RunError, "stale"):
                m.validate_approval(value)

    def test_missing_visuals_and_broken_dialogue_fail_before_confirmation(self):
        changes = [lambda v: v.pop("images"),
                   lambda v: v["images"][0]["action_plan"].clear(),
                   lambda v: v["images"][0]["expression_plan"][0].pop("visual_description"),
                   lambda v: v["images"][0]["dialogue_plan"][0].pop("placement"),
                   lambda v: v["images"][0]["dialogue_plan"][0].update(speaker="missing_person")]
        for change in changes:
            value = copy.deepcopy(self.value)
            change(value)
            with self.subTest(change=change), self.assertRaises(m.RunError):
                m.selection_summary(value)

    def test_metadata_does_not_change_drawing_prompt(self):
        frozen = self.normalize()
        expected = builder.build_prompt(frozen, frozen["images"][0])
        frozen["input"]["source_analysis"]["language_notes"] = "INTERNAL_TRANSLATION_REASON"
        frozen["images"][0]["text_style_reason"] = "INTERNAL_TEMPLATE_REASON"
        frozen["images"][0]["composition"]["reason"] = "INTERNAL_COMPOSITION_REASON"
        frozen["images"][0]["why_funny"] = "INTERNAL_JOKE_EXPLANATION"
        fixtures.confirm_fixture_plan(frozen)
        self.assertEqual(builder.build_prompt(frozen, frozen["images"][0]), expected)

    def test_all_panels_keep_actions_expressions_and_exact_text_once(self):
        value = self.normalize()
        for image in value["images"]:
            prompt = builder.build_prompt(value, image)
            for line in image["core_text"]:
                self.assertEqual(prompt.count(line), 1)
            for action in image["action_plan"]:
                self.assertIn(action["action"], prompt)
            for expression in image["expression_plan"]:
                self.assertIn(expression["visual_description"], prompt)
            for hidden in (image["text_style"], "acceptance_range", "CONFIRMED COMIC PLAN", "QA 11"):
                self.assertNotIn(hidden, prompt)
            self.assertIn(image["action_plan"][0]["action"], m.plan_markdown(value))

    def test_intentional_repeated_dialogue_and_technical_words_are_preserved(self):
        image = self.value["images"][1]
        image["core_text"] = ["QA worker 已完成。", "QA worker 已完成。"]
        self.value["proposal"]["options"][1]["key_lines"] = list(image["core_text"])
        value = self.normalize()
        prompt = builder.build_prompt(value, value["images"][1])
        self.assertEqual(prompt.count("QA worker 已完成。"), 2)

    def test_custom_visual_settings_and_label_survive(self):
        image = self.value["images"][0]
        image.update(style={"mode": "custom", "description": "Blue watercolor on rough paper"},
                     costume={"mode": "custom", "description": "a yellow raincoat"},
                     proportion={"mode": "custom", "target_head_ratio": 3.3})
        image["dialogue_plan"][0].update(delivery="label", prop="the red door", placement="at eye level")
        value = self.normalize()
        prompt = builder.build_prompt(value, value["images"][0])
        for detail in ("Blue watercolor on rough paper", "a yellow raincoat", "3.3 heads tall", "Writing on the red door"):
            self.assertIn(detail, prompt)
        self.assertNotIn("maid outfit", prompt)
        self.assertNotIn("acceptance_range", prompt)

    def test_optional_framing_and_authored_background_are_preserved(self):
        self.value["images"][0].pop("composition")
        self.value["images"][0]["background"] = {
            "mode": "custom", "origin": "tier", "description": "A tilted kitchen with green tiles"}
        value = self.normalize()
        prompt = builder.build_prompt(value, value["images"][0])
        self.assertIn("A tilted kitchen with green tiles", prompt)
        self.assertNotIn("Framing:", prompt)
        self.assertTrue(m.design_summary([value])["creative_review_required"])

    def test_device_caption_and_sound_effect_keep_their_carriers(self):
        for delivery, speaker, expected in [
            ("speech", "device", "Speech balloon from the in-scene device"),
            ("caption", "whalechan", "in whalechan's voice"),
            ("sfx", "narrator", "Drawn sound effect without a balloon"),
        ]:
            value = copy.deepcopy(self.value)
            image = value["images"][0]
            image["core_text"][0] = "砰"
            value["proposal"]["options"][0]["key_lines"] = list(image["core_text"])
            image["dialogue_plan"][0].update(delivery=delivery, speaker=speaker)
            normalized = self.normalize(value)
            with self.subTest(delivery=delivery):
                self.assertIn(expected, builder.build_prompt(normalized, normalized["images"][0]))

    def test_v15_prompt_and_confirmation_match_pre_change_baseline(self):
        value = self.normalize()
        value["schema_version"] = 15
        fixtures.confirm_fixture_plan(value)
        self.assertEqual(value["confirmation"]["summary_sha256"],
                         "c45057dfa1ac92d27e1db55e54f83fd51eb79eca77791d10e3d386ffcbbfcd7b")
        expected = ["9ff81735f5bf746f56f13ca5561ea6668767650f77ec85838db578e69cf3c969",
                    "a41aeb4e073f6d50406716e25e9f2f64c7065b8b6700e4430cf592ae69b5bfbc",
                    "1b853e33817df1e3be9f268c90faddcfafcbfe62124279a2899e77df776a159b",
                    "4671ac931144fe7a3e0cd00eb98e0479ec762e8fb86c75bffcd5379ddd0ea65d",
                    "bc6f48ed5c24e5518cd18d73c46312d26c58092f956745b5f670c364b6405e8f"]
        self.assertEqual([hashlib.sha256(builder.build_prompt(value, i).encode()).hexdigest()
                          for i in value["images"]], expected)

    def test_reference_bytes_bind_confirmation_and_external_copy_is_stable(self):
        image = self.value["images"][0]
        source = Path(image["references"][0]["path"])
        external = Path(self.tmp.name) / "user-style.webp"
        external.write_bytes(source.read_bytes())
        image["references"].append({"id": "user-style", "path": str(external), "roles": ["style"],
                                    "instruction": "Use the blue watercolor texture."})
        image["style"] = {"mode": "custom", "description": "Blue watercolor"}
        self.path.write_text(json.dumps(fixtures.confirm_fixture_plan(self.value)))
        result = m.cmd_init(argparse.Namespace(assignment=str(self.path),
                           root=str(Path(self.tmp.name) / "runs"), effective_parallelism=1))
        _, frozen, _ = m.load_run(result["run_dir"])
        self.assertEqual(m.selection_summary(frozen)["summary_sha256"],
                         self.value["confirmation"]["summary_sha256"])
        external.write_bytes(b"different reference bytes")
        with self.assertRaisesRegex(m.RunError, "stale"):
            m.validate_approval(self.value)

    def test_frozen_v15_keeps_review_workflow_and_prompt_recovery(self):
        self.path.write_text(json.dumps(self.value))
        result = m.cmd_init(argparse.Namespace(assignment=str(self.path),
                           root=str(Path(self.tmp.name) / "runs"), effective_parallelism=1))
        run = Path(result["run_dir"])
        frozen = m.read_json(run / "assignment.json")
        frozen["schema_version"] = 15
        fixtures.confirm_fixture_plan(frozen)  # Synthetic historical fixture only.
        m.write_json(run / "assignment.json", frozen)
        manifest = m.read_json(run / "manifest.json")
        manifest["assignment_sha256"] = m.sha256(run / "assignment.json")
        m.write_json(run / "manifest.json", manifest)
        self.assertEqual(m.review_workflow().load(argparse.Namespace(run_dir=str(run)))[1]["schema_version"], 15)
        self.assertIn("CONFIRMED COMIC PLAN", builder.build_prompt(frozen, frozen["images"][0]))


if __name__ == "__main__":
    unittest.main()
