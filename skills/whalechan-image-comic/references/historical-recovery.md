# Frozen comic run recovery

Load this reference when continuing an existing run. New work follows v19 in [run-schema.md](run-schema.md) and [batch-commands.md](batch-commands.md).

## Version map

| Assignment | Selection / consent | Prompt / QA | Execution |
|---|---|---|---|
| v11 | User selection and two gates; original per-choice counts | Original builder / QA9 | Original execution and coordinator records |
| v13 | Ten candidates, 45 duels, five winners, one gate | Original builder / QA9 | Fixed worker allocation |
| v14 | Same tournament and gate; A/B/C tiers | Original builder / QA10 | Fixed worker allocation |
| v15 | Same tournament and gate | Original builder / QA11 | Single candidate review and collection lifecycle |
| v16 | Same tournament; full visual plan bound before consent | Drawing-only builder / QA11 | Original candidate commands |
| v17 | Same tournament and visual contract | Drawing-only builder / QA11 | Four role caps, image journals, dynamic owners |
| v18 | Same tournament and visual contract | Drawing-only builder / QA11 | Fixed batch commands and locked tool |
| Earlier v19 | Independent 2N-to-N ranking | Drawing-only builder / QA11 | Five role caps; original recorded tier policy |

Recovery uses the frozen assignment, approval projection, references and remaining budget. Each version keeps its original confirmation hash. Missing tier policies retain narrative coverage; old v19 inventories without a tier policy retain their original behavior. New inventories explicitly bind the target ratio.

For v11/v13/v14 visual records use [qa-rubric.md](qa-rubric.md). For QA11 use [review-workflow.md](review-workflow.md). All versions use [form-evidence.md](form-evidence.md) for measured or visible-only proportion evidence.

## Historical tournament v13–v18

The following section applies only to frozen tournament contracts; new v19 records use [independent selection](run-schema.md#independent-priority-selection).

Freeze one pool of ten candidates before comparing them. Record exactly 45 unordered pairs, each once; no self-pairs or unknown IDs:

```json
{
  "duels": [
    {"a": "idea_01", "b": "idea_02", "winner": "idea_01", "reason": "The moving refrigerator shows the permission error before any explanation is needed."},
    {"a": "idea_01", "b": "idea_03", "winner": null, "reason": "Both give equally immediate visual consequences, with different emotional payoffs."}
  ],
  "tie_breaks": [
    {"ideas": ["idea_03", "idea_06"], "reason": "With equal total and head-to-head points, the access joke adds a clearer contrast to the already selected ownership joke."}
  ]
}
```

This fragment shows record shapes, not a complete tournament. A winner must be one of the pair or `null` for a draw. Each idea plays nine matches. Award 2 points for a win, 1 to each drawn idea and 0 for a loss. Compare source fidelity, laugh strength, visual contribution, concise dialogue and character specificity; explain actual content rather than assigning unsupported absolute quality scores.

Run `rank-ideas --draft <file>` to compute standings and `ranked_ideas` from `creative_pool`, `duels` and `tie_breaks` before completing the proposal. The script computes `tournament_results`; do not author a second score table. Sort by total points, then points from matches within the entire equal-total group. For every subgroup still tied, supply one `tie_breaks` record with the exact tied IDs in final order and a concrete comparative reason. If no ties remain, use `[]`. Do not use ID or input position to decide the order. `ranked_ideas` must equal the first five of this computed ranking. Keep all ten candidates and all comparisons, including losses; never extend the pool because relative winners seem weak.

## Panel-component recovery — v11/v13/v14 only

If the whole-canvas candidate fails cross-panel coherence and exactly two provider slots remain, generate the two panels separately and compose locally. Record both components. Do not use this rescue after a second provider image has already consumed a slot.

Because every task has only three image-producing calls, never rescue a failed four-panel image by generating four new panels. Retry the complete canvas. Local four-panel composition is permitted only from already-existing inputs that consume no new provider calls.

Use `scripts/compose-panels.py` only for existing panel images. Pass the frozen `--resolution-mode`, `--aspect-ratio`, and explicit `--width`/`--height` when applicable. In automatic mode it derives the canvas width from the first existing panel and computes the frozen ratio. It normalizes each panel with cover cropping, places white gutters, and outputs an exact canvas without stretching the completed montage. It does not add text.

## Lettering recovery — v11/v13/v14 only

For a text-only failure with two slots left, spend one on a text-free but composition-matched base with empty bubbles/headline areas, and the last editing that base with exact core text and the same template reference. With one slot left, edit the failed candidate directly, changing only the lettering. Recheck every character; plausible pseudo-text is a failure.

## Ordered provider routing — v11–v17

Use the original order: Codex ImageGen, OpenAI Images API, Nano Banana, Seedream; never move backward. Advance only after a visual failure, unavailable required capability, or recorded availability/authentication/quota/rate-limit/timeout/service error. Never use fallback to bypass a safety rejection.

## Candidate commands — v15/v16

Build the initial request using `build-prompt.py --run-dir <run> --image <id> --write-request`. Use its exact prompt and ordered role-scoped references; follow `provider-routing.md`. Before an authorized image call, record `manage-run.py mark-stage --run-dir <run> --image <id> --event generation_started`.

Preserve every returned image immediately in unique staging. The coordinator runs one command to archive it, count the consumed slot, copy the prompt, hash and validate the image:

```bash
python3 scripts/manage-run.py prepare-candidate --run-dir <run> --image <id> \
  --candidate <returned.png> --prompt-file <prompt.txt> \
  --provider codex --model gpt-image --transport builtin
```

CLI Codex uses `--transport cli --provider-audit <audit.json>`. Other providers omit transport. Never call an image API inside this preparation command. A technical failure keeps the returned bytes and consumed slot, marks `technical_blocked`, and authorizes no new image. Missing files or record errors are reported, not converted into visual defects. Use `block-image --run-dir <run> --image <id> --reason <details>` to terminate an unresolved technical blocker. Mechanical record corrections may reuse the same image; do not repeat visual inspection or manufacture a PASS.

When preparation returns `awaiting_review`, the designated reviewer opens the archived candidate, records `mark-stage --event single_review_started`, and writes one compact report using the [shared QA11 report shape](review-workflow.md#candidate).

Record without another visual review:

```bash
python3 scripts/manage-run.py record-candidate --run-dir <run> --image <id> \
  --candidate <archived.png> --prompt-file <prompt.txt> \
  --automatic-json <automatic.json> --visual-json <review.json> \
  --provider codex --model gpt-image --transport builtin
```

The prepared receipt is authoritative for provider metadata and automatic QA. A FAIL with core defects returns to `pending` only while fewer than three images have been produced. A PASS becomes `awaiting_collection`. Never promote it yet. The coordinator builds a targeted retry from the frozen idea and the recorded defects; do not replace its core premise. Prompt or QA JSON formatting errors alone never authorize a new image.

## Frozen v15/v16 recovery

Retain their coordinator-serial prepare-candidate/record-candidate lifecycle and previously approved worker allocation. Review every candidate once, without coordinator visual rereview, then one per-source contact sheet and at most one repair round. Do not apply v17 local image journals or role policies to frozen histories. v11/v13/v14 keep their original recovery contracts.
