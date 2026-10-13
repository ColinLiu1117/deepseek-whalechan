# Fixed batch commands — v18

Contents: [Boundary](#boundary) · [Prepare](#prepare) · [Plan](#plan) · [Start](#start) · [Image](#image) · [Collection](#collection) · [Delivery](#delivery) · [Recovery](#recovery) · [Timing](#timing)

## Boundary

Use these commands rather than authoring temporary bookkeeping/recovery/gallery/receipt scripts during normal production. Report unsupported cases instead of bypassing validators. Commands do not generate images, launch agents, inspect pixels or invent approval.

Main dispatches and communicates. Planning workers own prepare/proposal/start; generation workers own image commands and the actual tool call; collection workers own collection commands; delivery workers own export/verification. Main can read status/task packets. Reuse role guidance in existing workers; reload when context was lost.

Use v18 for new assignments. Preserve frozen v11–v17 confirmation and recovery contracts. QA stays 11; drawing-only prompts and budgets are unchanged. Command success is not visual approval. Paths and runtime outputs belong under the batch artifact directory.

## Prepare

Author spec.json from actual inputs and the observed tool list:

~~~json
{
  "sources": [
    {"id": "source-a", "paths": ["/absolute/source-a.png"]},
    {"id": "source-b", "text": "Actual supplied text"}
  ],
  "execution": {"batch_id": "batch-01"},
  "language": "zh",
  "availability": {
    "builtin": {
      "available": true,
      "evidence": "Actual tool name observed in this runtime",
      "model": null
    }
  }
}
~~~

Author source grouping; consecutive images of one source share its paths list. Resolve language from the user's session. The command gathers recent language-history evidence once; provide language_evidence when already gathered or explicitly set by the user. A planning worker compares that evidence with the current session.

Outside Codex, availability.codex_cli=true requests a local CLI login check. Inside Codex, supply builtin tool-list evidence; never launch nested Codex. Optional requests lists existing request JSONs for early capability validation. External preflight checks credentials without printing values.

~~~bash
python3 scripts/manage-run.py batch-prepare --batch <batch.json> --spec <spec.json>
~~~

This creates source inventory, planning tasks and common execution policy. It produces no test image. It selects the first configured compatible tool in the existing priority order and locks provider/transport/configured model. An unexposed native model is unknown. Actual service/quota remain unverified. No compatible tool returns blocked without production.

## Plan

Claim/dispatch planning tasks via agent-batch. One worker authors each source's ten candidates, all 45 real comparisons and five visual plans. Use the returned common execution object in every draft and a unique run_name per source.

Reuse rank-ideas, render-proposal, validate-batch and existing schemas. Scripts check comparison completeness/ranking; the worker authors winners, reasons and content.

After the existing cross-source review, its worker submits:

~~~json
{
  "review_status": "reviewed",
  "sources": ["source-a", "source-b"],
  "observation": "Actual comparison of mechanisms, beats and staging, including warning dispositions."
}
~~~

~~~bash
python3 scripts/manage-run.py batch-proposal --batch <batch.json> \
  --draft <source-a-draft.json> --draft <source-b-draft.json> \
  --review-json <cross-source-review.json>
~~~

Draft order must match sources. This checks source binding, normalizes/validates schemas and rankings, builds requests, checks the locked tool against every request, and writes proposal.md/proposal.json. Planning completion is recorded from those bound outputs.

Inspect structural warnings and explain dispositions in the cross-source review before showing the plan. A warning-free matrix is not creative approval. Main relays the tables, total, budget, role caps, observed capacity and tool through the existing single user confirmation.

## Start

Save the actual reply and returned batch summary hash:

~~~json
{"user_reply": "Actual user response", "summary_sha256": "returned summary hash"}
~~~

~~~bash
python3 scripts/manage-run.py batch-start --batch <batch.json> \
  --confirmation <confirmation.json> --root <runs-root> --slots 3
~~~

Never infer approval from templates, silence or defaults. Start validates/freezes each assignment and initializes generation/collection dependencies. Matching interrupted initialization resumes without creating duplicate runs. Slots are actual available subagent slots; zero is for disclosed no-delegation/explicit serial execution, not temporary occupancy.

~~~bash
python3 scripts/manage-run.py agent-batch claim --batch <batch.json> --slots 3 --worker <actual-id>
python3 scripts/manage-run.py task-packet --batch <batch.json> --task <returned-task-id>
~~~

Actually spawn/follow up the assigned agent. Scripts do not launch agents. Independent role caps, actual total capacity and idle resident occupancy apply; see agent-orchestration.md.

## Image

One generation worker owns the image and permitted retries.

~~~bash
python3 scripts/manage-run.py image-task start --run-dir <run> --image <image> \
  --owner <actual-id> --task-id <task>
~~~

Use the exact returned request, references and output path to call the locked tool once. Runtime state is outside the drawing prompt.

~~~bash
python3 scripts/manage-run.py image-task ingest --run-dir <run> --image <image> \
  --owner <actual-id> --task-id <task> --candidate <returned.png>
python3 scripts/manage-run.py image-task review-start --run-dir <run> --image <image> \
  --owner <actual-id> --task-id <task>
~~~

Ingest archives/counts the image before automatic checks and returns review materials plus an unfilled template. Add provider-audit for Codex CLI. Technical failures terminate the image without regeneration; returned bytes consume budget. Record review-start when actually beginning inspection, not at ingest.

Inspect once. Fill actual checked declarations for all 14 categories, per-panel observations, exact transcription, verdict, core defects, necessary minor issues, targeted retry and form evidence. Blank fields are not evidence. Scripts never fill checked, observations, PASS or landmarks.

~~~bash
python3 scripts/manage-run.py image-task submit --run-dir <run> --image <image> \
  --owner <actual-id> --task-id <task> --visual-json <observations.json>
~~~

Submit supplies mechanical reviewer identity/method and candidate metadata, validates, records and finishes terminal image/queue receipts. A core FAIL with budget returns targeted-retry-same-tool; author a drawing-only correction and call start with --retry-prompt <file>. Keep frozen premise/text/cast and the three-call budget.

If a receipt was interrupted, resubmit identical observations. A different review cannot overwrite it. An in-flight response instructs reconcile-flight: locate original bytes/status; re-running start never reissues an uncertain call.

## Collection

After all five tasks resolve, claim the collection task:

~~~bash
python3 scripts/manage-run.py collection-task prepare --run-dir <run> \
  --task-id <task> --owner <actual-id>
~~~

It merges journals and creates/reuses the sheet/index. Empty sources skip visual review. Inspect only distinctness, consistency and overall performance once; use the returned template, without repeating single-image details.

~~~bash
python3 scripts/manage-run.py collection-task submit --run-dir <run> \
  --task-id <task> --owner <actual-id> --review-json <observations.json>
~~~

Submit writes the judgment/receipt and enqueues only eligible named repairs plus the one focused recheck. Repairs share original budgets. Delivery depends on every terminal collection task, including repairs. No additional visual sweep.

## Delivery

Claim the automatically enqueued delivery-all task:

~~~bash
python3 scripts/manage-run.py batch-deliver --batch <batch.json> \
  --task-id delivery-all --owner <actual-id> --output <gallery-directory>
~~~

It promotes accepted candidates, finalizes complete/partial resolved sources, exports the aggregate gallery/index, checks final and embedded-asset hashes/counts, and writes the receipt. HEIC/HEIF sources retain originals with local PNG display copies; comics are unchanged.

Keep service-blocked work open. Delivery cannot close viable pending work as a shortfall. Use a dedicated output directory. Interrupted delivery reuses matching output and finishes missing metadata. Main receives links and counts.

## Recovery

Service errors pause new generation; never retry or switch automatically. Collect already in-flight outputs and finish local bookkeeping. A timeout does not prove no image:

~~~bash
python3 scripts/manage-run.py image-task uncertain --run-dir <run> --image <image> \
  --owner <actual-id> --task-id <task> --provider <locked-provider> \
  --model <recorded-model> --category timeout --evidence <actual-status>
~~~

Preserve the flight until reconciled. For a proven no-image failure use image-task error with factual evidence; it clears only that proven empty flight, consumes no candidate slot and pauses the batch. Safety rejection cannot resume as an ordinary service retry.

~~~bash
python3 scripts/manage-run.py batch-status --batch <batch.json>
python3 scripts/manage-run.py batch-resume --batch <batch.json> \
  --user-reply <actual-resume-request> --evidence <availability.json>
~~~

Resume rechecks the same tool and retains budgets/unknown flights. If an old worker stopped, use agent-batch recover and image-task recover with actual evidence before a replacement. Wait timeout alone never proves a worker stopped.

Direct init without batch creates a standalone preflight-required batch; generation is blocked until real preflight/resume. Prefer batch-start.

## Timing

~~~bash
python3 scripts/manage-run.py timing-summary --batch <batch.json> --sleep-json <sleep.json>
~~~

Optional sleep input: {"intervals":[["ISO start with timezone","ISO end with timezone"]]}. Without it sleep_excluded is false. Do not infer sleep from long gaps.

Separate role/task duration, request preparation, generation-to-ingest, archive, automatic checks, review setup and visual review/recording. Stage unions overlap; worker time is not user waiting. Generation-to-ingest includes tool/transport/agent latency, not GPU time. Pair session tool timestamps with events for precise provider waiting.
