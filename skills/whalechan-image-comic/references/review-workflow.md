# Review workflow — assignments v15/v16/v17/v18 / QA 11

Contents: [Ownership](#ownership) · [Criteria](#criteria) · [Candidate](#candidate) · [Collection](#collection) · [Failure](#failure) · [Timing](#timing)

## Ownership

For v18 use image-task start/ingest/review-start/submit and collection-task prepare/submit from batch-commands.md. Keep all fourteen actual checks and required form evidence. Scripts fill mechanical metadata only; never default checked declarations or PASS. Service errors pause the locked tool; visual failures alone allow same-tool retries.

For v17 use the role/task commands in `agent-orchestration.md`: the same generation worker performs the single-image lifecycle, collection workers make and review sheets, and delivery workers promote/finalize/export. The coordinator handles no content or visual work. The direct prepare-candidate/record-candidate examples below are the frozen v15/v16 path; v17 calls the same validators through image-task prepare/review.

Review each returned candidate once, at its original resolution, by one designated reviewer. For frozen v15/v16 a worker may render and review, or the coordinator may be the sole reviewer; never repeat the same candidate's visual review at handoff. The coordinator checks files and records through scripts, not by opening the picture again. Keep manifest mutations serial: coordinator-owned for frozen v15/v16, designated collection/delivery-worker-owned for v17. Only the two visual decisions below authorize image-producing retries.

1. Single-image QA: inspect all fourteen categories in one pass and report all observed core defects.
2. Collection QA: inspect one contact sheet per source's five tasks. If it fails, allow one repair round and one focused collection recheck. Do not add another final visual sweep, cross-source image review, or delivery-time visual review.

Local edits produce new candidates and consume slots. Inspect their whole canvas once. Never infer unchanged pixels from the edit instruction. New runs use complete canvases; panel-component rescue remains a frozen-run recovery feature.

## Criteria

For v16/v17/v18, inspect against the authored panel actions, `visual_description`, exact dialogue and explicit user locks. Preset names and unused effect menus are planning aids, not additional pixel requirements. Nonessential details left open during planning remain open during QA.

Keep J1 joke, K1 source anchor, I1 identity, C1 cast/performance, P1 panels, T1 lettering/ownership, A1 anatomy, V1 visual/expression, S1 style, O1 costume, B1 background, X1 action, E1 tier and H1 proportion. `checked` explicitly attests that the reviewer inspected each category; scripts cannot inspect pixels or prove this assertion.

Treat unreadable or wrong text, missing identity, incorrect speakers, broken narrative order, missing key actions, changed emotion/joke, gross anatomy or material cropping as core defects. Explicit user-locked requirements remain hard requirements.

Accept small mouth/brow variations preserving the intended emotion, unobtrusive sweat/tear/line count differences, and minor edge proximity preserving identity and readability. Record these as `minor_issues`; they do not trigger regeneration. For E1 judge the overall performance, planned contrast and narrative impact. The quantitative manpu palettes and exact face cues in the bundled JSON are creative guidance for QA 11, not automatic rejection thresholds. Preserve exact semantic text, including labels and sound effects.

For measured compositions retain candidate-bound H1 landmark measurement and overlay inspection within the same review. Visible-only shots record a reason and visible cues, never an invented numeric ratio.

## Candidate

The command examples in this section apply to frozen v15/v16. For v17 use image-task begin/prepare/review-start/review/finish from agent-orchestration.md; the same compact report and QA rules apply.

Build the initial request using `build-prompt.py --run-dir <run> --image <id> --write-request`. Use its exact prompt and ordered role-scoped references; follow `provider-routing.md`. Before an authorized image call, record `manage-run.py mark-stage --run-dir <run> --image <id> --event generation_started`.

Preserve every returned image immediately in unique staging. The coordinator runs one command to archive it, count the consumed slot, copy the prompt, hash and validate the image:

```bash
python3 scripts/manage-run.py prepare-candidate --run-dir <run> --image <id> \
  --candidate <returned.png> --prompt-file <prompt.txt> \
  --provider codex --model gpt-image --transport builtin
```

CLI Codex uses `--transport cli --provider-audit <audit.json>`. Other providers omit transport. Never call an image API inside this preparation command. A technical failure keeps the returned bytes and consumed slot, marks `technical_blocked`, and authorizes no new image. Missing files or record errors are reported, not converted into visual defects. Use `block-image --run-dir <run> --image <id> --reason <details>` to terminate an unresolved technical blocker. Mechanical record corrections may reuse the same image; do not repeat visual inspection or manufacture a PASS.

When preparation returns `awaiting_review`, the designated reviewer opens the archived candidate, records `mark-stage --event single_review_started`, and writes one compact report:

```json
{
  "review_status": "reviewed",
  "reviewer": "actual-reviewer-id",
  "method": "direct-image-inspection",
  "checked": ["J1", "K1", "I1", "C1", "P1", "T1", "A1", "V1", "S1", "O1", "B1", "X1", "E1", "H1"],
  "panels": [{"panel": 1, "observed_scene": "Actual visible scene, not copied from the plan"}],
  "text_transcription": ["Actual visible text"],
  "verdict": "PASS",
  "core_defects": [],
  "minor_issues": [{"check": "V1", "detail": "Slight mouth curvature; the intended calm emotion is intact"}],
  "targeted_retry": null,
  "form_evidence": {"mode": "visible-only", "reason": "Planned torso close-up", "observed_cues": ["Large head and short torso"]}
}
```

This example shows structure, not default acceptance. Use one ordered observation per actual panel. A core defect is `{check, detail}`; FAIL requires at least one and a specific `targeted_retry`. A PASS requires exact transcription and no core defects. Measured PASS uses the existing measurement evidence fields from `qa-rubric.md`. Candidate SHA-256 may be omitted; the manager supplies it, or verifies it when provided.

Record without another visual review:

```bash
python3 scripts/manage-run.py record-candidate --run-dir <run> --image <id> \
  --candidate <archived.png> --prompt-file <prompt.txt> \
  --automatic-json <automatic.json> --visual-json <review.json> \
  --provider codex --model gpt-image --transport builtin
```

The prepared receipt is authoritative for provider metadata and automatic QA. A FAIL with core defects returns to `pending` only while fewer than three images have been produced. A PASS becomes `awaiting_collection`. Never promote it yet. The coordinator builds a targeted retry from the frozen idea and the recorded defects; do not replace its core premise. Prompt or QA JSON formatting errors alone never authorize a new image.

## Collection

When all five tasks are awaiting collection or terminal, run:

```bash
python3 scripts/build-review-sheet.py --run-dir <run>
```

The script makes a 3×2 contact sheet with five numbered slots, using complete images fitted into cells without cropping. Missing tasks stay gray in their original slots; the sixth cell is unused. `index.json` maps positions to image IDs, premises, exact lines, attempt IDs and hashes. The original candidates remain unchanged. Sheet creation is local and consumes no image budget. If no candidates remain, the script records a skipped collection and no visual call is needed.

Send the sheet and index together for one set review. Inspect only distinctness of ideas/payoffs, identity/style consistency and overall readability/tone. Do not recheck tiny mouths, sweat counts, exact glyphs or other already reviewed single-image details. Small-scale uncertainty is not a core failure.

```json
{
  "review_status": "reviewed",
  "reviewer": "actual-set-reviewer-id",
  "sheet_sha256": "hash from index.json",
  "checked": ["distinctness", "consistency", "overall"],
  "observation": "What the actual sheet shows as a set",
  "verdict": "FAIL",
  "core_defects": [{"check": "distinctness", "images": ["02_image_id"], "detail": "Name the duplicated payoff and comparison image", "targeted_retry": "Correct the execution within its frozen idea"}],
  "minor_issues": []
}
```

`images` names only tasks to repair, not every image mentioned for comparison. Record with `manage-run.py record-collection-review --run-dir <run> --review-json <json>`.

On first collection failure, only named images with unused slots reopen. Repair them within their frozen plans; each new candidate gets one single-image review. Single-image failures can use the remaining shared budget inside this one repair round. Then build the updated five-slot sheet and submit one focused collection recheck. Keep unchanged candidates as visual context. A recheck cannot name new repair targets or start another collection round. Failed targets become `collection_failed`; exhausted or technically blocked tasks remain missing. If no repair is possible, close the collection without another visual call.

When the collection is complete, run `promote` for each `collection_accepted` task. The manager revalidates data and hashes without another LLM image inspection. Then `finalize`, using `--allow-partial` for terminal shortfalls, and export the gallery. Do not fill gaps with rejected pictures or restore an earlier set-rejected candidate as a final.

## Failure

- Only a recorded single-image or collection core defect authorizes image-producing retries.
- All returned images count, including invalid PNGs and provider audit failures. At most three calls per image; no transfer or reset on collection repair.
- Automatic metadata, file/hash, schema, audit, promotion, finalization and gallery failures never trigger regeneration. Report or mechanically repair the existing files/records without a new visual judgment.
- Do not bypass a provider safety rejection. Stop dispatch; preserve returned images and mark affected tasks blocked.
- If the premise itself must change, stop the affected task and report the plan conflict. Do not hide a new creative pool or renewed budget in a collection repair.

## Timing

`manifest.events` records generation/review starts, receipt saving, automatic-check completion, single-review recording, sheet creation, collection-review recording, promotion and finalization. The receipt timestamp is when `prepare-candidate` receives the saved output, not backend GPU completion time. Pair it with provider/session timestamps when separating transport delay. Record starts through `mark-stage`; never backfill invented timestamps. Scripts enforce stored decisions, not the truthfulness or real-world count of LLM image inspections.

Frozen assignments v11/v13/v14 keep their original QA 9/10 and recovery behavior. Frozen v15 retains its original prompt contract and this QA 11 workflow. New assignments use v18 and QA 11; never migrate approval histories or old PASS results merely to change policy.
