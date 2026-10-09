# Final plan and one user confirmation

Complete creative planning before the single generation gate: freeze ten candidates, compare every pair, select five, then plan one image per selected idea. The table reports the result; the user confirms or revises the whole plan.

## Display the complete plan

Show one eight-column Markdown table per source, with five rows:

| 序号 | 创意 | 方向 | 格数 | 档位 | 场景／分镜 | 关键台词 | 入选理由 |
|---|---|---|---|---|---|---|---|
| 1 | 具体创意 | 方向及笑点如何落地 | 1 | A | 画面事件、镜头、互动 | 准备上图的关键文字 | 对决中体现的具体优势 |
| 2 | … | … | 2 | C | … | … | … |
| 3 | … | … | 4 | B | … | … | … |
| 4 | … | … | 2 | A（脸→C） | … | … | … |
| 5 | … | … | 1 | C | … | … | … |

> 格数分布：1 格 ×2 · 2 格 ×2 · 4 格 ×1 ✓ ｜ 档位分布：A ×2 · B ×1 · C ×2 ✓

Numbers identify rows, not mechanisms, layouts or tiers. Name the actual comedy direction; optionally mark a native-direction idea with “（原）” and explain the marker. Write a declared contrast as the tier followed by the lowered axes, such as “A（脸→C）”. The helper computes the distribution line and marks each coverage policy as satisfied or user-overridden. Do not impose native/character quotas. Keep cells concise, escape pipes and use `<br>` for line breaks.

Below the table, show:

- Five ideas, one image each, five total images per source; for multiple sources include each source's count and the grand total.
- Worker-to-image assignments, concrete sub-agent count, requested and effective concurrency, and the coordinator's planning, QA, recording and delivery duties. With zero sub-agents, state that the main agent executes all five images serially and explain the limiting reason; a one-sub-agent plan also runs sequentially.
- A maximum of three image-producing calls per image, fifteen per source, and the provider route.
- Any explicit user overrides, including a nondefault panel-count or exaggeration policy.

Then ask once:

> **确认按以上创意、张数和分工开始生成吗？** 每个创意生成一张；确认后执行生成、验收和交付。

Wait for an actual affirmative reply to this plan. Silence, a recommendation, an automatically selected UI answer or a planning-only request is not permission to generate. Honor authorization already given for this exact displayed scope; do not invent an additional gate.

Before displaying the plan, inspect runtime/provider capacity and use `plan-execution` from `provider-routing.md`. Default to automatic sub-agents; cap one five-image run at five workers and the shared batch pool at ten. Respect explicit serial requests. Save the concrete `execution` and matching `worker_plan` in the draft. Display actual observed capacity rather than promising the ceiling; workers reuse the queue without increasing image counts or candidate budgets.

## Record the decision

Use schema v14 and the helper commands in `run-schema.md`. Save drafts under `artifacts/whalechan-image-comic/<run-name>-planning/` unless the user specifies another location. Preserve revisions as separate files. Complete image plans and the worker allocation before rendering the plan; drafts do not require visual QA.

Render the plan with either read-only helper:

```bash
python3 scripts/manage-run.py render-proposal --draft <draft.json>
python3 scripts/manage-run.py summarize-selection --draft <draft.json>
```

`summarize-selection` is an alias of `render-proposal`; both return the complete table, counts, budget, worker allocation, question and `summary_sha256`. Display the Markdown directly, not inside a code block. After the real reply, save `confirmation` with `status: confirmed`, the actual `user_reply` and the returned `summary_sha256`, binding the count, worker allocation and normalized execution settings. Use `worker_plan`, `panel_policy` and `exaggeration_policy` as specified in `run-schema.md`; full `images` records may be completed after confirmation while preserving the displayed scenes, key lines and panel counts. Hashes are audit metadata, not user-facing text. Helpers render and validate records; they cannot approve on the user's behalf.

Changes to the creative content, quantity or planned allocation require an updated displayed plan and confirmation of that version; the disclosed runtime capacity reductions below do not revise the approved plan. Apply the user's corrections without silently replacing other ideas. A revised core idea changes the frozen candidate pool: preserve the prior version and redo the affected comparisons once for that explicit revision, rather than automatically generating another pool. For multiple sources show one combined execution summary and bind the same reply to each current source plan. Qualify each worker assignment by source and idea. Share one global worker capacity across the batch; do not multiply concurrency by the number of sources. Per-source worker plans describe which workers participate, while the coordinator schedules their jobs within the displayed global limit. Never reuse an old reply for an altered scope.

After confirmation, validate and freeze the assignment, then execute without another routine approval. If runtime capacity falls, disclose the reduction and any necessary queue reassignment; record the lower actual count without editing the frozen plan or its hash. Actual workers must not exceed the confirmed count. Increasing approved capacity requires a revised plan and confirmation. Create and dispatch workers using the runtime's delegation tools; unavailable delegation falls back to serial main-agent execution. Workers write to unique staging paths; only the coordinator records and promotes candidates. Keep retries serial within each image's independent budget.

Frozen v11 and v13 runs keep their original contracts and recovery paths; see `run-schema.md`. Do not rewrite their decisions or fabricate a v14 confirmation for them. Create new runs with v14.
