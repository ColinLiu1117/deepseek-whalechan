# Final plan and one user confirmation

Complete creative planning before the single generation gate: freeze ten candidates, compare every pair, select five, then plan one image per selected idea. The table reports the result; the user confirms or revises the whole plan.

## Display the complete plan

Show one eight-column Markdown table per source, with five rows. The headers, distribution line and question below are the `--language zh` rendering; `--language en` renders them in English, and other communication languages translate the `en` rendering (see SKILL.md). Write the cells in the communication language and keep the exact visible text unchanged:

| 序号 | 创意 | 方向 | 格数 | 档位 | 场景／分镜 | 关键台词 | 入选理由 |
|---|---|---|---|---|---|---|---|
| 1 | 具体创意 | 方向及笑点如何落地 | 1 | A-日漫冲击 | 画面事件、镜头、互动 | 准备上图的关键文字 | 对决中体现的具体优势 |
| 2 | … | … | 2 | C-克制冷幽默 | … | … | … |
| 3 | … | … | 4 | B-漫画爆发 | … | … | … |
| 4 | … | … | 2 | A-日漫冲击（脸→C） | … | … | … |
| 5 | … | … | 1 | C-克制冷幽默 | … | … | … |

> 格数分布：1 格 ×2 · 2 格 ×2 · 4 格 ×1 ✓ ｜ 档位分布：A-日漫冲击 ×2 · B-漫画爆发 ×1 · C-克制冷幽默 ×2 ✓

> 本次目标头身比：2.8 头身（半 Q 版，semi-chibi），适用于全部 5 张。

Numbers identify rows, not mechanisms, layouts or tiers. Name the actual comedy direction; optionally mark a native-direction idea with “（原）” and explain the marker. Use the fixed labels `A-日漫冲击`, `B-漫画爆发`, `C-克制冷幽默` in both the tier column and distribution line (`A-Manga impact`, `B-Comic outburst`, `C-Restrained deadpan` in English). Write a declared contrast after the descriptive label, such as “A-日漫冲击（脸→C）”. The helper computes the distribution line and marks each coverage policy as satisfied or user-overridden. Do not impose native/character quotas. Keep cells concise, escape pipes and use `<br>` for line breaks.

Show the target head-to-body ratio immediately below the distribution line and before image totals, never as another table column. Record `proportion` in every new `proposal.options` entry before rendering, including the default `{"mode": "preset", "preset": "semi-chibi"}`. Resolve targets from the preset catalog or the explicit custom ratio. When all five match, show one shared target; otherwise group table row numbers by target, for example “第 1、3、5 张为 2.8 头身（半 Q 版，semi-chibi）；第 2、4 张为 2.5 头身（Q 版，chibi）”. Custom ratios read “3.0 头身（自定义）”. These are planned targets, not measurements of generated images. Historical plans without this field retain their original confirmation contract and are marked as not having recorded a planning target.

Below the table, show:

- Five ideas, one image each, five total images per source; for multiple sources include each source's count and the grand total.
- Independent role caps (planning 5, generation 5 / Codex 3, collection 2, delivery 1), actual observed runtime slots, shared batch limit, dynamic assignment and main-agent orchestration-only duties. Disclose serial main-agent fallback only when delegation is unavailable or explicitly requested.
- A maximum of three image-producing calls per image, fifteen per source, and the provider route.
- Any explicit user overrides, including a nondefault panel-count or exaggeration policy.

Then ask once:

> **确认按以上创意、张数和 sub-agent 分配开始生成吗？** 每个创意生成一张；确认后执行生成、验收和交付。

Wait for an actual affirmative reply to this plan. Silence, a recommendation, an automatically selected UI answer or a planning-only request is not permission to generate. Honor authorization already given for this exact displayed scope; do not invent an additional gate.

Before displaying the plan, inspect runtime capacity and use plan-roles from agent-orchestration.md. Save one shared batch execution policy and dynamic worker_plan. Planning workers author the content; main displays their rendered plan plus current capacity. Role caps are not guaranteed available slots.

## Record the decision

Use schema v17 and the helper commands in `run-schema.md`. Save drafts under `artifacts/whalechan-image-comic/<run-name>-planning/` unless the user specifies another location. Preserve revisions as separate files. Complete image plans and the worker allocation before rendering the plan; drafts do not require visual QA.

Render the plan with either read-only helper:

```bash
python3 scripts/manage-run.py render-proposal --draft <draft.json> --language <zh|en>
python3 scripts/manage-run.py summarize-selection --draft <draft.json> --language <zh|en>
```

`summarize-selection` is an alias of `render-proposal`; both return the complete table, counts, budget, worker allocation, question and `summary_sha256`. Display the Markdown directly, not inside a code block. After the real reply, save `confirmation` with `status: confirmed`, the actual `user_reply` and the returned `summary_sha256`, binding the count, worker allocation and normalized execution settings. Use `worker_plan`, `panel_policy` and `exaggeration_policy` as specified in `run-schema.md`; full v17 `images` records must exist before this display. The scene/staging cells come from their panel actions and expression descriptions; the confirmation also binds the visual projection used by the prompt builder. See `prompt-design.md`. Hashes are audit metadata, not user-facing text. Helpers render and validate records; they cannot approve on the user's behalf.

Changes to creative content, quantity or approved role/batch limits require updated consent. Normal role switching and capacity changes within those limits do not. Preserve previous versions for substantive revisions. For multiple sources show one combined execution summary and bind the same actual reply to each current source plan; never multiply quotas by source count. Runtime actor identities belong in the dispatch log, not the approval hash.

Disclose the QA 11 policy in the execution summary: one candidate inspection, minor-issue tolerance, one collection contact-sheet review and at most one repair round within the same three-call budget.

After confirmation, assign validation/freezing to a planning worker. Main dispatches actual sub-agents through runtime tools. Generation workers own isolated image journals and permitted retries; collection/delivery workers reconcile and mutate shared manifests serially. Follow agent-orchestration.md for capacity reductions, resident reuse, ownership and recovery.

Frozen v11/v13/v14/v15/v16 keep their original contracts. Never fabricate a v17 confirmation or migrate approvals. Create new runs with v17.
