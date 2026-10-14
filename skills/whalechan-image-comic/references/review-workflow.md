# Review workflow — assignments v15/v16/v17/v18/v19 / QA 11

Contents: [Ownership](#ownership) · [Criteria](#criteria) · [Candidate](#candidate) · [Collection](#collection) · [Failure](#failure) · [Timing](#timing)

## Ownership

For v18/v19 use image-task start/ingest/review-start/submit and collection-task prepare/submit from batch-commands.md. Keep all fourteen actual checks and required form evidence. Scripts fill mechanical metadata only; never default checked declarations or PASS. Service errors pause the locked tool; visual failures alone allow same-tool retries.

For v17 use the role/task commands in `agent-orchestration.md`: the same generation worker performs the single-image lifecycle, collection workers make and review sheets, and delivery workers promote/finalize/export. The coordinator handles no content or visual work. The direct prepare-candidate/record-candidate examples in historical-recovery.md are the frozen v15/v16 path; v17 calls the same validators through image-task prepare/review.

Review each returned candidate once, at its original resolution, by one designated reviewer. For frozen v15/v16 a worker may render and review, or the coordinator may be the sole reviewer; never repeat the same candidate's visual review at handoff. The coordinator checks files and records through scripts, not by opening the picture again. Keep manifest mutations serial: coordinator-owned for frozen v15/v16, designated collection/delivery-worker-owned for v17. Only the two visual decisions below authorize image-producing retries.

1. Single-image QA: inspect all fourteen categories in one pass and report all observed core defects.
2. Collection QA: inspect one contact sheet per source's N tasks. If it fails, allow one repair round and one focused collection recheck. Do not add another final visual sweep, cross-source image review, or delivery-time visual review.

Local edits produce new candidates and consume slots. Inspect their whole canvas once. Never infer unchanged pixels from the edit instruction. New runs use complete canvases; panel-component rescue remains a frozen-run recovery feature.

## Criteria

For v16/v17/v18/v19, inspect against the authored panel actions, `visual_description`, exact dialogue and explicit user locks. Preset names and unused effect menus are planning aids, not additional pixel requirements. Nonessential details left open during planning remain open during QA.

Keep J1 joke, K1 source anchor, I1 identity, C1 cast/performance, P1 panels, T1 lettering/ownership, A1 anatomy, V1 visual/expression, S1 style, O1 costume, B1 background, X1 action, E1 tier and H1 proportion. `checked` explicitly attests that the reviewer inspected each category; scripts cannot inspect pixels or prove this assertion.

Treat unreadable or wrong text, missing identity, incorrect speakers, broken narrative order, missing key actions, changed emotion/joke, gross anatomy or material cropping as core defects. Explicit user-locked requirements remain hard requirements.

Accept small mouth/brow variations preserving the intended emotion, unobtrusive sweat/tear/line count differences, and minor edge proximity preserving identity and readability. Record these as `minor_issues`; they do not trigger regeneration. For E1 judge the overall performance, planned contrast and narrative impact. The quantitative manpu palettes and exact face cues in the bundled JSON are creative guidance for QA 11, not automatic rejection thresholds. Preserve exact semantic text, including labels and sound effects.

For measured compositions retain candidate-bound H1 landmark measurement and overlay inspection within the same review. Visible-only shots record a reason and visible cues, never an invented numeric ratio.

## Candidate

Frozen v15/v16 preparation and recording commands are in [historical-recovery.md](historical-recovery.md#candidate-commands--v15v16). For v17 use image-task begin/prepare/review-start/review/finish from agent-orchestration.md; the same compact report and QA rules apply.

For v19 and frozen v18, the generation worker uses image-task start, ingest, review-start and submit from [batch-commands.md](batch-commands.md#image). Ingest preserves and counts the returned bytes and performs automatic checks. Record review-start when opening the archived candidate, then fill the returned compact report:

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

This example shows structure, not default acceptance. Use one ordered observation per actual panel. A core defect is `{check, detail}`; FAIL requires at least one and a specific `targeted_retry`. A PASS requires exact transcription and no core defects. Measured PASS uses the shared measurement evidence fields from [form-evidence.md](form-evidence.md). Candidate SHA-256 may be omitted; the manager supplies it, or verifies it when provided.

Submit the compact report with image-task submit from [batch-commands.md](batch-commands.md#image). Its receipt records the verdict and eligible same-tool retry or collection transition. The original three-call budget applies.

## Collection

For v18/v19 use collection-task prepare/submit from [batch-commands.md](batch-commands.md#collection), which merges journals and creates/reuses the sheet. For the frozen direct-command path, when all N tasks are awaiting collection or terminal, run:

```bash
python3 scripts/build-review-sheet.py --run-dir <run>
```

For v19 the script uses ceil(sqrt(N)) columns and ceil(N/columns) rows, preserving all N numbered slots and multi-digit labels. N=5 remains 3×2; frozen five-image sheets retain their original grid. Complete images fit without cropping; missing tasks remain gray at their original positions. If a large sheet cannot be meaningfully reviewed at the tool's pixel limit, report that technical limit; do not silently reduce N or add review rounds. `index.json` maps positions to image IDs, premises, exact lines, attempt IDs and hashes. The original candidates remain unchanged. Sheet creation is local and consumes no image budget. If no candidates remain, the script records a skipped collection and no visual call is needed.

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

`images` names only tasks to repair, not every image mentioned for comparison. For v18/v19 record through collection-task submit. Frozen direct-command runs use `manage-run.py record-collection-review --run-dir <run> --review-json <json>`.

On first collection failure, only named images with unused slots reopen. Repair them within their frozen plans; each new candidate gets one single-image review. Single-image failures can use the remaining shared budget inside this one repair round. Then build the updated N-slot sheet and submit one focused collection recheck. Keep unchanged candidates as visual context. A recheck cannot name new repair targets or start another collection round. Failed targets become `collection_failed`; exhausted or technically blocked tasks remain missing. If no repair is possible, close the collection without another visual call.

For v18/v19 the delivery worker runs batch-deliver from [batch-commands.md](batch-commands.md#delivery). In frozen direct-command runs, when the collection is complete, run `promote` for each `collection_accepted` task. The manager revalidates data and hashes without another LLM image inspection. Then `finalize`, using `--allow-partial` for terminal shortfalls, and export the gallery. Do not fill gaps with rejected pictures or restore an earlier set-rejected candidate as a final.

## Failure

- Only a recorded single-image or collection core defect authorizes image-producing retries.
- All returned images count, including invalid PNGs and provider audit failures. At most three calls per image; no transfer or reset on collection repair.
- Automatic metadata, file/hash, schema, audit, promotion, finalization and gallery failures never trigger regeneration. Report or mechanically repair the existing files/records without a new visual judgment.
- Do not bypass a provider safety rejection. Stop dispatch; preserve returned images and mark affected tasks blocked.
- If the premise itself must change, stop the affected task and report the plan conflict. Do not hide a new creative pool or renewed budget in a collection repair.

## Timing

`manifest.events` records generation/review starts, receipt saving, automatic-check completion, single-review recording, sheet creation, collection-review recording, promotion and finalization. The receipt timestamp is when `prepare-candidate` receives the saved output, not backend GPU completion time. Pair it with provider/session timestamps when separating transport delay. Record current review starts through image-task review-start; frozen v15/v16 use `mark-stage`; never backfill invented timestamps. Scripts enforce stored decisions, not the truthfulness or real-world count of LLM image inspections.

Frozen assignments v11/v13/v14 keep their original QA 9/10 and recovery behavior. Frozen v15 retains its original prompt contract and this QA 11 workflow. New assignments use v19 and QA 11; never migrate approval histories or old PASS results merely to change policy.
