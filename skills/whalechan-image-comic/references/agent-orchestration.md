# Role-specific sub-agent orchestration — v17

Contents: [Limits](#limits) · [Ownership](#ownership) · [Planning](#planning) · [Queue](#queue) · [Image task](#image-task) · [Collection and delivery](#collection-and-delivery) · [Recovery](#recovery)

## Limits

Keep independent maximums: planning 5; generation 5 for general providers and 3 for Codex ImageGen; collection 2; delivery 1. Apply the existing batch-wide ceiling of 10 and any lower user/runtime/provider limit. These are role limits, not one shared pool of three and not reserved resident agents.

Observe whether the runtime limit includes the main agent. Subtract external occupied slots. Count idle resident sub-agents as occupied unless the runtime actually releases them. Reuse an idle agent through follow-up work before creating another. Never invent a release tool or spawn nested agent CLIs to bypass capacity.

Plan targets without creating workers:

```bash
python3 scripts/manage-run.py plan-roles --batch-id batch-01 \
  --slots 3 --scope subagents --provider codex --generation 50 --collection 2
```

This produces independent policy and current targets (2 generation + 1 collection). With five available slots, Codex can use 3 + 2; general providers use 5 + 1 with six slots and 5 + 2 with seven. With no collection demand, use all available generation slots up to its role cap. With one slot, finish the current image before the ready collection, then resume generation. Do not preempt an image call.

Use defaults when provider capacity is unknown; label them as policy, not measured service capacity. Apply an observed lower provider limit through --provider-limit and reduce dispatch after explicit capacity/rate-limit failures. A single agent's concurrent ImageGen submissions may be serialized; assign separate agents for actual concurrency.

If delegation is entirely unavailable, disclose serial main-agent fallback. Temporarily occupied slots are not unavailable delegation: queue work and reuse residents. Respect explicit user serial execution.

## Ownership

Main handles requirements, consent, queue state, capacity, dependency readiness, budgets/status summaries and final links. Delegate source analysis, prompt authorship, visual judgments, image/file processing, manifest reconciliation and HTML to sub-agents. Main checks task receipts mechanically; it never reopens images or rewrites content.

Assign one role at a time to each resident:
- planning: one source's ten candidates, 45 duels, five plans and complete drawing fields. Also use a planning task for the existing cross-source batch comparison and post-confirmation freezing.
- generation: one image through its entire single-image lifecycle, including the sole visual QA and permitted targeted retries.
- collection: merge completed image records, make the local contact sheet, inspect it once, and record the result. One task per source; at most two different sources concurrently.
- delivery: reconcile records, promote accepted images, finalize and export the aggregate HTML. Check counts/files/links without another visual inspection.

Reuse actors across roles. A completed generation worker may become a collection worker without increasing resident count. While generation remains ready, prefer its throughput: under three slots use 2 generation + 1 collection; use the second collection slot only when additional capacity or insufficient generation demand permits.

Every dispatch packet includes task ID, role, batch file/ID, source, frozen run/image where applicable, skill path, exact input/output paths, provider/model, remaining budget, role-specific references and completion conditions. Workers do not spawn agents or change confirmed content.

## Planning

Start planning sub-agents before generation consent; planning never calls an image API. Parallelize by original source, with one worker authoring its full five-image visual plan. Pass the same batch execution policy to every source. The main agent assembles worker-rendered plan fragments and communicates user corrections without doing semantic rewrites.

Assign the existing cross-source comparison to a planning worker after all drafts are available. Resolve its findings in the drafts before the single consent. Bind one actual user reply to all approved source plans. Delegate validation and initialization after consent. No production run or image call precedes consent.

Use v17 execution and dynamic worker_plan from run-schema.md. Bind approved role limits and batch strategy, not transient worker identities. Disclose current runtime capacity separately. Lower dispatch or recovery within approved role/batch limits does not alter the visual plan. Raising approved limits or materially changing content requires updated consent.

## Queue

Save the inner execution object from plan-roles as execution.json. Keep one batch JSON for all sources. Never give each source its own complete set of global quotas.

```bash
python3 scripts/manage-run.py agent-batch init --batch <batch.json> \
  --policy <execution.json> --source source-a --source source-b
python3 scripts/manage-run.py agent-batch enqueue --batch <batch.json> --task-json <task.json>
python3 scripts/manage-run.py agent-batch next --batch <batch.json> --slots 3
python3 scripts/manage-run.py agent-batch claim --batch <batch.json> --slots 3 --worker <actual-agent-id>
```

Task input:
```json
{"id":"a-image-1","role":"generation","source":"source-a",
 "inputs":{"run_dir":"/absolute/frozen/run","image":"actual-image-id"},
 "depends_on":["freeze-a"]}
```

For planning, inputs contains source paths/output draft paths; for collection use run_dir; for delivery use run_dirs. Dependencies must already exist. Enqueue initial generation tasks in source/image order, collection after the source's five generation task IDs, and delivery after all terminal collection tasks. For repair, enqueue new generation task IDs only for recorded repair_images, then one new collection task depending on those repairs. The delivery dependency must point to the final collection task; enqueue delivery only once all collection lifecycles resolve.

The helper picks ready tasks in source order, subject to role targets and active tasks. A source's already-running images do not block dispatch for later sources. Frozen execution tasks must match the batch policy and valid confirmation. A collection is ready only after every image is terminal at the single-image stage and no unresolved owner/call remains.

After claim, actually spawn or follow up the assigned runtime agent. On creation failure reconcile the claim with agent-batch recover and actual evidence; never pretend it started. The helper cannot call the delegation tool or verify the truth of runtime evidence.

Workers write a JSON receipt with task_id, status (complete or blocked), result paths and short outcome. Use complete for a fully resolved image that has a terminal shortfall; blocked means the task still needs reconciliation and must not unlock dependents.

```bash
python3 scripts/manage-run.py agent-batch finish --batch <batch.json> \
  --task <task-id> --worker <actual-agent-id> --result <receipt.json>
```

An idle actor stays in the resident registry and may receive another role. Use release only after actual runtime release, with --evidence. After confirming the previous worker stopped, use agent-batch recover --task <same-task> --worker <replacement> --evidence <facts>, then image-task recover with that same owner/task. Claim the recovered batch task explicitly with --task and --worker before resuming it. Keep any in-flight call unresolved until returned bytes or proven no-image evidence are reconciled. For a failed spawn before any image task exists, recover may omit --worker and return it to the ready queue. Never mark a live image safe merely because a wait timed out.

## Image task

The generation worker owns its image journal, not the shared manifest. v17 single-image commands require owner and task-id. Use the actual runtime identity; workers cannot share an image.

```bash
python3 scripts/manage-run.py image-task claim --run-dir <run> --image <image> --owner <worker> --task-id <task>
python3 scripts/build-prompt.py --run-dir <run> --image <image> --write-request
python3 scripts/manage-run.py image-task begin --run-dir <run> --image <image> \
  --owner <worker> --task-id <task> --provider codex --model <actual-model>
```

Call the authorized provider once, preserve the returned bytes, then:
```bash
python3 scripts/manage-run.py image-task prepare --run-dir <run> --image <image> \
  --owner <worker> --task-id <task> --candidate <returned.png> --prompt-file <prompt.txt> \
  --provider codex --model <actual-model> --transport builtin
```

Preparation archives and counts the returned image before automatic checks. When automatic checks pass, record image-task review-start with the same run/image/owner/task-id, then inspect the whole archived candidate once. Write the compact QA 11 report from review-workflow.md. Retain measured proportion evidence where required.

```bash
python3 scripts/manage-run.py image-task review --run-dir <run> --image <image> \
  --owner <worker> --task-id <task> --candidate <archived.png> --prompt-file <prompt.txt> \
  --provider codex --model <actual-model> --visual-json <review.json>
```

A core FAIL with remaining budget returns pending. Build a targeted drawing-only retry and repeat begin/call/prepare/review without waiting for main-agent judgment. Preserve frozen premise/text locks and provider order. PASS, exhaustion or technical/safety blockage ends the image task:
```bash
python3 scripts/manage-run.py image-task finish --run-dir <run> --image <image> --owner <worker> --task-id <task>
```

Return the journal path and complete receipt. Single-image journals are the authoritative attempt ledger. Same-image retries stay serial; all returned images consume the original maximum of three, including technical failures. Candidate/QA hashes bind evidence; malformed records permit mechanical repair, not another image or visual inspection.

For a proven no-image provider failure use image-task error with provider/model/category/evidence. Preserve uncertainty as an in-flight call. Advance providers through the existing order rather than retrying an unavailable provider indefinitely. A safety rejection stops new batch dispatch and is reported immediately. Setup-only failure may leave the run open for later authorized recovery; do not silently finalize it.

## Collection and delivery

The collection worker uses merge-tasks or the shared CLI operations, which lock the whole manifest read/modify/write and reconcile completed image journals. Local journals never write the manifest directly. No extra permanent bookkeeping agent is needed.

Use build-review-sheet.py and manage-run.py record-collection-review. These v17 entry points merge under the same run lock. Review only distinctness, consistency and overall performance. Technical merge/hash errors never authorize regeneration. Main dispatches recorded repair targets through generation tasks, carrying the original remaining budget.

After the one repair round, a collection worker rebuilds the sheet and performs at most one focused recheck. Do not add a final sweep. A recheck failure terminates affected images rather than spawning another round.

The delivery worker runs promote/finalize and export-gallery.py after collections complete. v17 shared CLI mutations merge idempotently; previously accepted collection states are not overwritten by re-reading an unchanged local journal. Keep missing tasks explicit and follow existing partial/open-run rules.

## Recovery

Use image-task status to inspect the journal without acquiring new ownership. Before image-task recover, verify the old worker stopped and reconcile output/staging/provider status; supply the new owner/task-id and factual --evidence. Recovery changes ownership but never clears an in-flight call or replenishes budget. The old owner cannot mutate the recovered task.

If an image journal already finished, recover only its missing completion receipt. For interrupted collection/delivery tasks, resume the existing sheet, recorded review or exported files; do not create another visual judgment merely to recover a receipt. If the image already returned, prepare/review the same bytes and existing observations. An interrupted archive may be replayed only with identical bytes. A proven no-image result is recorded with error; an unknown result remains unresolved. Never turn a timeout into assumed free budget.

Record queue events, actual actor IDs, local generation/review events and provider/session timestamps. Distinguish queue residence, setup, actual tool execution, QA, collection and delivery. Exclude sleep; report wall-clock and cumulative worker time separately. Scripts verify structure and transitions, not whether an LLM really inspected pixels or whether a runtime observation is truthful.
