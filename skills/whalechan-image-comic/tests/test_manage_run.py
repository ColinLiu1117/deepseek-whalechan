from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = SKILL_ROOT / "scripts" / "manage-run.py"
SPEC = importlib.util.spec_from_file_location("comic_manage_run", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Cannot load {MODULE_PATH}")
manage = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(manage)


TEXT_STYLE = "06_top-bottom-punchline"


def text_style_reference(style: str = TEXT_STYLE) -> dict:
    return {
        "id": "text-style",
        "path": str(SKILL_ROOT / f"assets/text-style-templates/{style}/reference.webp"),
        "roles": ["typography"],
        "instruction": "Apply typography treatment only",
    }


# One passing idea per comedy direction, so the fixture exercises every carrier.
DIRECTION_FIXTURES = [
    ("reversal", {"expectation": "Fix the punctuation", "reversal": "She builds a factory instead"}),
    ("exposure", {"surface": "Calm expert pose", "truth": "She never found the comma", "exposure": "The factory log shows zero commas"}),
    ("escalation", {"steps": ["She checks one line", "She audits the chapter", "She builds a comma factory"]}),
    ("recognition", {"situation": "Proofreading late at night", "recognition": "The missing comma was in the title all along"}),
    ("character", {"trait": "rice as compute currency", "trigger": "The comma hunt drains her compute"}),
]


def visual_fixture() -> dict:
    pool = []
    for number in range(1, 11):
        direction, carrier = DIRECTION_FIXTURES[(number - 1) % len(DIRECTION_FIXTURES)]
        item = {
            "id": f"idea_{number:02d}",
            "premise": f"premise {number}",
            "direction": direction,
            **copy.deepcopy(carrier),
            "punchline": f"punchline {number}",
            "personality": ["serious", "malicious"],
            "fact_anchor": "missing comma",
            "scene": f"scene {number}",
            "mechanism": f"mechanism {number}",
        }
        pool.append(item)
    layouts = [(1, "single"), (2, "top-bottom"), (4, "2x2"), (1, "single"), (2, "left-right")]
    ranks = [(n, 1) for n in range(1, 6)]
    images = []
    for index in range(5):
        panels, layout = layouts[index]
        rank, execution = ranks[index]
        style = TEXT_STYLE if index % 2 == 0 else "03_blue-banner"
        images.append(
            {
                "name": f"comic_{index + 1}",
                "source_rank": rank,
                "idea_id": f"idea_{rank:02d}",
                "execution": execution,
                "execution_note": f"Distinct consequence {index + 1}",
                "composition": {
                    "shot": "wide action view", "staging": f"factory position {index + 1}",
                    "text_placement": "above the action", "reason": "Keeps the punctuation visible",
                },
                "proportion_check": "measured",
                "fact_anchor": "missing comma",
                "premise": f"premise {rank}",
                "punchline": f"knife {index + 1}",
                "why_funny": "huge effort produces punctuation",
                "personality": ["serious", "malicious"],
                "panel_count": panels,
                "expression_plan": [
                    {
                        "panel": panel,
                        "preset": "procedural" if panel == 1 else "smug",
                        "performance": "grounded" if panel == 1 else "heightened",
                    }
                    for panel in range(1, panels + 1)
                ],
                "action_plan": [
                    {
                        "panel": panel,
                        "action": f"perform requested action in panel {panel}",
                    }
                    for panel in range(1, panels + 1)
                ],
                "layout": layout,
                "core_text": ["全厂推理完毕", "缺了个逗号。"],
                "text_style": style,
                "text_style_reason": "Separate the setup from the oversized factory-service boast.",
                "references": [text_style_reference(style)],
                "dialogue_plan": [
                    {"text_index": line, "panel": min(line + 1, panels),
                     "speaker": "whalechan", "delivery": "speech"}
                    for line in range(2)
                ],
                "cast_plan": [],
            }
        )
    value = {
        "schema_version": 19,
        "run_name": "comma-factory",
        "input": {
            "type": "text", "content": "input", "language": "zh-CN", "fact_anchor": "missing comma", "participants": [],
            "source_analysis": {
                "source_event": "A comma is missing", "comic_target": "Disproportionate effort",
                "tone": "playful", "language_notes": "Simplified Chinese", "user_constraints": [],
                "native_direction": {"direction": "reversal", "reason": "The source turns a tiny fix into a factory."},
            },
        },
        "selection_reason": "These premises expose the disproportionate response.",
        "creative_pool": pool,
        "ranked_ideas": ["idea_01", "idea_02", "idea_03"],
        "images": images,
        "budget": {"per_image_candidates": 3},
    }
    value["proposal"] = {
        "revision": 1, "fact_anchor": "missing comma",
        "native_direction": copy.deepcopy(value["input"]["source_analysis"]["native_direction"]),
        "options": [
            {"title": f"Proposal {choice}", "idea_id": idea["id"],
             "premise": idea["premise"], "scene": idea["scene"], "twist": f"twist {idea['id']}",
             "direction": idea["direction"], "is_native": idea["direction"] == "reversal",
             "staging": "Wide shot with the comma visible", "key_lines": ["缺了个逗号。"]}
            for choice, idea in zip("ABCDE", pool[:5])
        ],
    }
    return value


def confirm_fixture_plan(value: dict) -> dict:
    """Synthetic single approval for tests only; never user authorization."""
    for option, image in zip(value["proposal"]["options"], value["images"]):
        next(c for c in value["creative_pool"] if c["id"] == option["idea_id"])["key_lines"] = list(option["key_lines"])
        if "proportion" in image:
            option["proportion"] = copy.deepcopy(image["proportion"])
    value["pool_sha256"] = manage.extension_module("selection_contract").pool(manage, value, verify_hash=False)
    value["selection_review"].update({k:value[k] for k in ("source_id","target_images","pool_sha256","selection_reason")})
    value["confirmation"] = {"status": "confirmed", "user_reply": "Synthetic plan confirmation",
                             "summary_sha256": manage.selection_summary(value)["summary_sha256"]}
    return value


def assignment() -> dict:
    value = visual_fixture()
    pool = value["creative_pool"]
    for index, idea in enumerate(pool, 1):
        idea["key_lines"] = [f"任务 {index} 已完成", f"独有结果 {index}。"]
    value["ranked_ideas"] = [idea["id"] for idea in pool[:5]]
    proposal = value["proposal"]
    tiers = ["A", "B", "C", "A", "A"]
    for index, (option, image, idea, tier) in enumerate(zip(proposal["options"], value["images"], pool, tiers), 1):
        option.update(key_lines=list(idea["key_lines"]), panel_count=image["panel_count"], twist=idea["punchline"],
                      selection_reason=f"Rank {index}: a distinct visible consequence.", exaggeration=tier)
        image.update(source_rank=index, idea_id=idea["id"], premise=idea["premise"], execution=1,
                     core_text=list(idea["key_lines"]), exaggeration=tier,
                     effects_plan=[] if tier == "C" else [{"axis": "effect_lines", "effect": "speed lines behind the factory"}])
        image["lettering_description"] = "Bold dark lettering in clear white balloons."
        for line in image["dialogue_plan"]:
            line["placement"] = "above the speaker, with a tail toward their mouth"
        for entry in image["expression_plan"]:
            entry["tier"] = tier
            entry["visual_description"] = "She gazes steadily at the work with a quiet, closed mouth."
    value["execution"] = manage.role_execution({"batch_id": "synthetic-batch", "tool": {"provider": "codex", "transport": "builtin", "model": "unknown", "on_error": "pause"}})
    value["worker_plan"] = {"coordinator": "main", "allocation": "dynamic"}
    value.update(target_images=5, source_id="source-a", author_agent_ids=["author"], concept_task_id="concepts-source-a",
                 exaggeration_policy={"mode":"target-ratio","ratio":{"A":3,"B":1,"C":1}})
    for option, image in zip(value["proposal"]["options"], value["images"]):
        option["proportion"] = {"mode":"preset","preset":"semi-chibi"}
    value["selection_review"] = {"review_method":"independent-priority-ranking", "reviewer_agent_id":"reviewer",
        "selection_task_id":"selection-source-a", "ranking":[{"idea_id":c["id"],"reason":"Synthetic priority"} for c in pool],
        "selection_reason":value["selection_reason"]}
    return confirm_fixture_plan(value)


class RunStateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.magick = shutil.which("magick")
        if self.magick is None:
            self.skipTest("ImageMagick is required")
        self.initialize()

    def initialize(self, choices=None):
        root = Path(self.temporary.name)
        assignment_path = root / "assignment.json"
        value = assignment()
        assignment_path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
        result = manage.cmd_init(argparse.Namespace(
            assignment=str(assignment_path), root=str(root / "runs"), effective_parallelism=None,
        ))
        self.run_dir = Path(result["run_dir"])
        frozen = manage.read_json(self.run_dir / "assignment.json")
        batch = manage.read_json(self.run_dir / "batch.json")
        batch["status"] = "ready"  # Synthetic local preflight evidence for offline protocol tests.
        manage.write_json(self.run_dir / "batch.json", batch)
        from types import SimpleNamespace
        proxy = SimpleNamespace(**vars(manage)); proxy.task_local = True
        self.workflow = manage.extension_module("review_workflow").ReviewWorkflow(proxy)
        self.image_spec = frozen["images"][0]
        self.image = self.image_spec["id"]
        return frozen

    def files(self, number: int, verdict: str = "FAIL") -> argparse.Namespace:
        root = self.run_dir / f"test-input-{number}"
        root.mkdir()
        candidate = root / "candidate.png"
        subprocess.run([self.magick, "-size", "1024x1024", "xc:#aabbcc", "-colorspace", "sRGB", "-type", "TrueColor", str(candidate)], check=True)
        prompt = root / "prompt.txt"
        prompt.write_text("test prompt", encoding="utf-8")
        candidate_hash = hashlib.sha256(candidate.read_bytes()).hexdigest()
        overlay = root / "measurement.png"
        shutil.copy2(candidate, overlay)
        automatic = root / "automatic.json"
        automatic.write_text(
            json.dumps(
                {
                    "schema_version": 2,
                    "overall": "PASS",
                    "candidate_sha256": candidate_hash,
                    "expected_output": self.image_spec["output"],
                    "metrics": {
                        "format": "PNG",
                        "width": 1024,
                        "height": 1024,
                        "colorspace": "sRGB",
                        "channels": "srgb",
                    },
                    "gates": {
                        "F1": {"verdict": "PASS"},
                        "F2": {"verdict": "PASS"},
                    },
                }
            ),
            encoding="utf-8",
        )
        visual = root / "visual.json"
        gates = {key: "PASS" for key in manage.CONFIGURABLE_GATES}
        defects = []
        targeted = None
        evidence = {"form_evidence": {
                "candidate_sha256": candidate_hash,
                "measurement_method": "pose-neutralized-skeleton",
                "target_source": "preset",
                "target_sha256": self.image_spec["proportion_sha256"],
                "mean_head_ratio": 2.8,
                "acceptance_range": [2.695, 2.995],
                "head_axis": {"top": [100, 0], "chin": [100, 100]},
                "body_segments": [
                    {"name": "chin_to_pelvis", "start": [100, 100], "end": [100, 160]},
                    {"name": "pelvis_to_knee", "start": [100, 160], "end": [100, 220]},
                    {"name": "knee_to_sole", "start": [100, 220], "end": [100, 280]},
                ],
                "calculated_head_ratio": 2.8,
                "measurement_overlay": str(overlay),
                "measurement_overlay_sha256": hashlib.sha256(overlay.read_bytes()).hexdigest(),
            }}
        if verdict == "FAIL":
            gates["J1"] = "FAIL"
            defects = ["The punchline is flat"]
            targeted = "Replace the punchline"
        visual.write_text(json.dumps({"review_status":"reviewed", "reviewer":"synthetic-test",
            "method":"direct-image-inspection", "candidate_sha256":candidate_hash,
            "checked":sorted(manage.CONFIGURABLE_GATES), "panels":[{"panel":i,"observed_scene":"Synthetic scene"}
                for i in range(1,self.image_spec["panel_count"]+1)], "text_transcription":self.image_spec["core_text"],
            "verdict":verdict,"core_defects":[] if verdict=="PASS" else [{"check":"J1","detail":"Synthetic defect"}],
            "minor_issues":[],"targeted_retry":targeted,"form_evidence":evidence["form_evidence"]}))
        return argparse.Namespace(run_dir=str(self.run_dir), image=self.image, provider="codex", model="test", candidate=str(candidate), prompt_file=str(prompt), automatic_json=str(automatic), visual_json=str(visual), transport="builtin")


    def test_frozen_assignment_and_existing_prompt_are_protected(self):
        command = [sys.executable, "-B", str(SKILL_ROOT / "scripts/build-prompt.py"),
                   "--run-dir", str(self.run_dir), "--image", self.image]
        first = subprocess.run(command, capture_output=True, text=True, check=True)
        prompt = Path(json.loads(first.stdout)["prompt_file"])
        original = prompt.read_bytes()
        repeated = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(repeated.returncode, 2)
        self.assertEqual(prompt.read_bytes(), original)
        frozen_path = self.run_dir / "assignment.json"
        frozen = manage.read_json(frozen_path)
        frozen["images"][0]["core_text"] = ["Changed after confirmation"]
        manage.write_json(frozen_path, frozen)
        with self.assertRaisesRegex(manage.RunError, "Frozen assignment SHA-256"):
            manage.load_run(str(self.run_dir))


if __name__ == "__main__":
    unittest.main()
