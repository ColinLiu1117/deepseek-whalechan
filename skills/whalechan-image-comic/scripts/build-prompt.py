#!/usr/bin/env python3
"""Build a generation prompt, ordered references and the adapter request from a frozen assignment."""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("comic_manage_run", Path(__file__).with_name("manage-run.py"))
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Cannot load run manager")
manage = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(manage)


def build_prompt(assignment: dict, image: dict) -> str:
    manage.planning_draft(assignment, "Prompt assignment")
    manage.validate_approval(assignment)
    if image.get("qa_contract_version") != manage.QA_CONTRACT_VERSION:
        raise manage.RunError(f"Image qa_contract_version must be {manage.QA_CONTRACT_VERSION}")
    if image not in assignment["images"]:
        raise manage.RunError("Image must belong to the confirmed assignment")
    return manage.visual_prompt().render(assignment, image)


def adapter_reference(reference: dict) -> dict:
    return {key: reference.get(key) for key in ("id", "path", "roles", "instruction", "sha256")}


def build_request(image: dict, prompt: str, edit_target: Path | None, edit_instruction: str) -> dict:
    """Assemble the external adapter request from the frozen image, so references and output never drift."""
    references = [adapter_reference(item) for item in image["references"]]
    if edit_target is not None:
        if not edit_target.is_file():
            raise manage.RunError(f"Edit target does not exist: {edit_target}")
        typography = [item for item in references if item["roles"] == ["typography"]]
        references = [{
            "id": "edit-target", "path": str(edit_target), "roles": ["composition"],
            "instruction": edit_instruction, "sha256": manage.sha256(edit_target),
        }] + typography
    return {"prompt": prompt, "references": references, "output": image["output"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--image", required=True)
    parser.add_argument("--output", help="Defaults to the image's staging/prompt-01.txt; never overwritten")
    parser.add_argument("--from-prompt", help="Reuse a saved retry or repair prompt instead of building the initial one")
    parser.add_argument("--write-request", action="store_true",
                        help="Also write the adapter request JSON beside the prompt (<prompt>.request.json)")
    parser.add_argument("--edit-target", help="Edit request: this image first, then the frozen typography reference")
    parser.add_argument("--edit-instruction", default="edit target; keep everything except the lettering unchanged")
    args = parser.parse_args()
    try:
        run, assignment, _manifest = manage.load_run(args.run_dir)
        image = next((item for item in assignment["images"] if item["id"] == args.image), None)
        if image is None:
            raise manage.RunError(f"Unknown image id: {args.image}")
        if args.from_prompt:
            if args.output:
                raise manage.RunError("--output only applies when building the initial prompt")
            destination = Path(args.from_prompt).resolve()
            prompt = destination.read_text(encoding="utf-8")
            if not prompt.strip():
                raise manage.RunError("Prompt file is empty")
        else:
            prompt = build_prompt(assignment, image)
            destination = Path(args.output).resolve() if args.output else run / "staging" / args.image / "prompt-01.txt"
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("x", encoding="utf-8") as handle:
                handle.write(prompt)
        result = {"prompt_file": str(destination), "references": [item["path"] for item in image["references"]]}
        if args.write_request or args.edit_target:
            edit_target = Path(args.edit_target).resolve() if args.edit_target else None
            request = build_request(image, prompt, edit_target, args.edit_instruction)
            request_path = destination.with_name(destination.stem + ".request.json")
            with request_path.open("x", encoding="utf-8") as handle:
                json.dump(request, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
            result.update(request_file=str(request_path), references=[item["path"] for item in request["references"]])
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (manage.RunError, OSError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
