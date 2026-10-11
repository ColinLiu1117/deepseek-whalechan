---
name: whalechan-image-comic
description: Create five DeepSeek Whale-chan comics from text, screenshots, images, chat logs, or reasoning traces. Compare ten ideas in 45 pairwise duels, select five, then obtain one confirmation of the plan, total and worker allocation. Use for funny 1/2/4-panel Whale-chan adaptations with exact dialogue, consistent identity, configurable visuals, provider fallbacks, one candidate review and one collection review with at most one repair round. Generate one image per selected idea, covering 1/2/4-panel layouts and A/B/C exaggeration tiers (manga impact, comic outburst, restrained deadpan) across the set.
---

# Whale-chan Image Comic

Turn one recognizable fact into ten candidates, select five by complete pairwise comparison, and generate one comic per selected idea after confirmation. Preserve the source's actual comic target and tone, considering its native comedy direction during comparison. Jokes come in five directions — reversal, exposure, escalation, recognition and character — each carried by its own fields; do not force every source into an expectation-and-reversal shape. Candidate ids and image numbers are identifiers, never creative instructions.

Workflow: analyze → freeze ten ideas → 45 pairwise duels → select five → plan five images and worker allocation → **one user confirmation of table, totals and allocation** → validate and freeze → generate, review and deliver. Complete planning before this gate; planning alone never authorizes image calls.

## Load the guidance

Read these before every run:

- `references/prompt-design.md` for drawing-only visual plans authored before confirmation.
- `references/proposal-selection.md` for the information-only eight-column table with its panel and tier distribution, the single user confirmation and its record.
- `references/comedy-engine.md` for source analysis, the five comedy directions, native-direction preferences, the optional rhythm layer, selection, and where exaggeration tiers fit.
- `references/character-personality.md` for Whale-chan, form, outfit, and abstract-supporting-character locks.
- `references/form-profiles.md` for the five recommended presets, custom-ratio rules, measurement, and panel adaptation.
- `references/panel-grammar.md` for 1/2/4-panel structure and retry limits.
- `references/expression-presets.json` for per-panel visible facial acting and performance levels.
- `references/exaggeration-tiers.md` and `references/exaggeration-tiers.json` to give each image an A/B/C exaggeration tier, its landing markers and its effect palette.
- `references/text-style-routing.md` to select one primary text treatment per image and review variety across the set.
- `references/asset-index.md` to select bundled references, `references/form-authority.json` for form targets, and `references/asset-catalog.json` for paths and hashes.
- `references/provider-routing.md` before any provider call.
- `references/review-workflow.md` for new-run single-image QA, tolerances, contact sheets, collection repair and timing.
- `references/qa-rubric.md` only for frozen QA 9/10 recovery or measured proportion evidence.
- `references/gallery.md` before exporting the completed task's preview gallery.

## Choose the language

Infer the session language from what the user typed in this session and in local agent sessions from the last 24 hours, whichever agent runs this Skill; do not take it from the agent's defaults, system locale or the source material. Run `python3 scripts/detect-language.py` for the history: it reads Claude Code and Codex CLI records, skips injected and tool-written text, and reports message counts by script with recent excerpts. When this session and the history disagree, this session wins; read the excerpts before deciding a Latin-script language. When no history is available, use this session alone. An explicit user instruction ("reply in English", "台词用日语") overrides the inferred language for the scope it names: communication, visible text, or both.

- **Communication:** write every user-facing message, plan table, confirmation question and final report in the communication language. `render-proposal` and `summarize-selection` take `--language zh|en`; use `zh` for Chinese, `en` for English, and translate the `en` rendering for any other language, keeping every row, column, count, tier, worker assignment and exact visible text unchanged. Export the gallery with `--language zh` for a Chinese session and `--language en` otherwise; the page can switch between Chinese and English. Confirmation hashes cover the structured record, not the Markdown.
- **Visible text:** write `core_text` in the session language unless the user names another. Adapt a source in a different language rather than copying it, and record the difference in `language_notes`. Keep model names, error tokens and technical terms in their original form when that is funnier. Freeze the result as a BCP-47 tag in `input.language`.
- **Internal:** provider prompts stay in English with exact visible text inserted verbatim; run and image names stay English identifiers.

## Apply defaults and user overrides

- Generate exactly ten candidates and select five by all 45 pairwise duels. Produce one final PNG per selected idea, five total per source. Default to automatic provider-native `1:1` output with `1024×1024` as a recommendation, not a required pixel size.
- Accept an explicit aspect ratio, an explicit pixel resolution, or both. Infer the ratio from an explicit resolution when omitted; reject conflicting values. Automatic mode validates the ratio, while explicit mode validates exact width and height.
- Freeze the ten-candidate pool before comparisons. Record actual judgments and all results; never prewrite winners.
- Make candidate scenes, actions and payoffs distinct. Preserve each selected core idea and user-locked wording in its one image. Shared source lines do not justify identical final replies or consequences.
- Cover 1, 2 and 4 panels across the five images, allocating them by narrative need rather than index. Record an explicit user override; never add empty panels to meet the default.
- Cover exaggeration tiers A, B and C across the five images, choosing each from the execution rather than rank, index or panel count. Record an explicit user override. Tiers bind the plan; a tier lost to an exhausted budget is reported, never reassigned.
- Select typography, framing, cast staging and text placement independently for each joke. Repetition is allowed when justified by the source; random rotation is not creative diversity. A consistent character identity does not require consistent layouts.
- For dialogue-driven material, default to bodily present abstract indigo partners. Record a narrative reason for an offscreen, avatar-only, or omitted role; preserve who speaks and who reacts.
- Default to `semi-chibi`, the canonical clean rounded cel-shaded style, the canonical navy-and-white maid outfit, and the tier's default background when the user resolves none: a detailed text-free scene for `A`, an effect background for `B`, pure white `#FFFFFF` for `C`.
- Write visible comic text in the language resolved under [Choose the language](#choose-the-language), not automatically in the source's language.
- Treat the five bundled forms as recommended presets. Accept any finite measurable custom head ratio greater than `1.0`; custom ratios have no bundled proportion reference.
- Allow any physically depictable action and any user-resolved background, art style, or outfit, subject to provider safety and technical limits. A custom field changes only that field.
- Default to automatic sub-agent execution. Before the single confirmation, resolve and display the actual worker count from ready images, observed runtime slots (excluding the main agent), provider capacity and user limits. Use at most five workers for one five-image run and a shared ceiling of ten across a batch. Honor explicit serial execution; use the main agent when sub-agents are unavailable. See `references/provider-routing.md`.
- Start planning immediately. Show the final five-row table, image total, worker allocation and budget together, then obtain one real confirmation. Never infer approval from silence or a preselected answer. A planning-only request never authorizes image calls.
- Give each task an independent maximum of three image-producing calls. Never transfer unused calls.

## Understand the source and select five ideas

1. Record `input.source_analysis`: source event, comic target, tone, language differences, user corrections and native direction with evidence (`null` when the source has no joke). Separate observed facts from interpretation. Extract the fact anchor and participants; use `input.participants: []` only for solo material. Preserve speaker roles without copying real faces. For screenshot/image sources, retain the file path in `input.content` and the transcription in `source_event`.
2. Author exactly ten distinct candidates, each with direction/carrier fields, scene, key dialogue, visual payoff, mechanism and personality. Native direction and source-grounded character gags are comparative preferences, not quotas. Freeze the pool; weak ideas still compete, and the pool is never extended or regenerated.
3. Compare all 45 unique pairs using `comedy-engine.md`. Record winner or draw and a concrete reason. Award 2/1/0 points for win/draw/loss; break ties by head-to-head points, then authored reasons and distinctness. Select the top five and preserve the full record. Ids and order never decide winners.
4. Plan exactly one image per selected idea. Check that the answers, final beats and visual consequences differ; merely changing nouns, fonts or poses does not establish five ideas.

## Complete the plan, confirm once, then freeze

Prepare these decisions before the user confirmation:

1. Set `ranked_ideas` to the five winners and explain the ranking in `selection_reason`. Link one image to each `idea_id` and describe its unique payoff in `execution_note`. Cover 1/2/4 panels across the set unless explicitly overridden by the user. Choose worker assignments and effective concurrency from actual capacity. Record each option's `proportion` before confirmation, defaulting to `{"mode": "preset", "preset": "semi-chibi"}`; completed image proportions must match.
2. Settle scenes, key lines, panel counts, staging and worker assignments before confirmation. Resolve fields from explicit user instructions, declared reference roles, source semantics, then defaults. For v16, finish all five visual image records before displaying the confirmation plan. Write actions as visible moments, add natural expression descriptions and text positions, and resolve semantic conflicts in this same planning pass; see `prompt-design.md`. Freeze the completed composition, exact text and speaker/cast plans, output, style, costume, background, typography, actions, expressions and proportions before initialization. Assign image numbers last. Intentional close-ups use `visible-only`; measurable full-body shots use `measured`.
3. Use a canonical identity reference first and the selected bundled text-style reference as the sole `typography` reference. Declare each reference's roles: `identity`, `style`, `pose_action`, `composition`, `costume`, `background`, `typography`, or `proportion`. Load the abstract-user pose sheet only when a supporting character appears. Use at most five effective references; never silently drop required typography.
4. Review each execution against its selected idea and user constraints, then check typography, speaker ownership and cast staging against the source. Reject random template rotation, generic reasons and offscreen choices made just to simplify drawing. Refine expression without replacing the frozen candidate. Decide each image's exaggeration tier, landing panel, per-panel tiers, landing `effects_plan` and any `contrast`. Decide its optional `rhythm`; leave it `null` unless the punchline clearly needs it. Write the schema v16 draft and render the complete information table, image total, worker allocation and budget as specified in `proposal-selection.md`. After the single real confirmation, save its bound record in `assignment.json`, then validate and initialize; initialization writes `creative-record.md`:

   ```bash
   python3 scripts/manage-run.py validate-assignment --assignment <assignment.json>
   python3 scripts/manage-run.py init --assignment <assignment.json> \
     --effective-parallelism <current-capacity> --effective-subagents <actual-worker-count>
   ```

For multiple inputs, compare source-specific mechanisms, narrative beats and staging before displaying the consolidated plan: run `python3 scripts/manage-run.py validate-batch --draft <first-draft.json> --draft <second-draft.json>` with every planning draft, which flags repeated panel, tier and panel-by-tier recipes from the planned options. Once assignments are confirmed, run `validate-batch --assignment <first.json> --assignment <second.json>` with every assignment before the first generation call. Review its case-by-position matrix and warnings, not just aggregate counts. Compare mechanisms, narrative beats, shots, cast positions and text placement across cases and across positions; changing order must not hide a repeated skeleton. Ask whether another case's dialogue could replace this one's without changing the drawing. Save a `batch-review.md` beside the assignments naming the compared cases, warning dispositions, source-specific reasons for retained similarities, and revisions. Do not generate until this review is actually performed. Structural validity is not creative approval; no warnings is not approval either. For final images use only the per-source contact-sheet collection review in `review-workflow.md`; do not add a cross-source visual sweep. See `references/batch-review.md`.

In the confirmation table and distribution line, use fixed descriptive labels: `A-日漫冲击`, `B-漫画爆发`, `C-克制冷幽默` (English: `A-Manga impact`, `B-Comic outburst`, `C-Restrained deadpan`). Keep contrast suffixes, such as `A-日漫冲击（脸→C）`. Immediately below the distribution line, show the current target head-to-body ratio, shared across all five images or grouped by table row numbers when different. Label custom ratios explicitly. Keep this outside the eight-column table and distinguish planned targets from measurements of finished images.

Use schema v16 in `references/run-schema.md` for new runs. Preserve frozen v11, v13, v14 and v15 runs (v13 keeps QA 9; v14 keeps QA 10; v15 keeps its QA 11 and original prompt builder) under their original recovery contracts; never rewrite their approval history. The initialized run belongs under `artifacts/whalechan-image-comic/<run-name>/` unless the user gives another destination. External references are frozen into the run with hashes.

## Generate and review

Follow `references/review-workflow.md` for assignments v15/v16 / QA 11. New v16 prompts contain only shared visual settings and per-panel drawings; the script assembles the frozen fields without another LLM rewrite. Build the frozen prompt with `build-prompt.py --write-request`, call the authorized provider once, preserve its output, then have the coordinator run `prepare-candidate`. This archives the image, counts its slot, hashes and checks it in one command. Technical failures block the candidate and never authorize another image.

Have one designated reviewer inspect the whole candidate once. Record concise actual observations, exact text, core defects and tolerated minor issues. Do not have the main agent repeat a worker's visual inspection at handoff. Only core single-image defects authorize a retry within the three-call budget. A passed candidate waits for collection review.

After the five tasks resolve, build one numbered contact sheet per source with `build-review-sheet.py`. Review distinctness, consistency and overall performance once. Only named failed images may enter one collection repair round, sharing their original three-call budgets. Inspect each new candidate once, then do at most one focused collection recheck on the updated sheet. Recheck failure means a shortfall, never another collection round. Promote only collection-accepted candidates.

Keep safety halts, source fidelity, exact semantic text and explicit user locks strict. Allow minor facial/decoration variations that preserve emotion, identity, tier and readability. Do not let exact mouth curvature or sweat counts alone cause a retry unless the user explicitly locked them.

For frozen v11/v13/v14 runs, retain their original candidate recording, promotion, component rescue and QA contracts; see `qa-rubric.md`. Never rewrite old approvals or records.

## Route providers strictly

Use this order and never move backward:

1. Codex ImageGen / GPT Image (built-in tool inside Codex, `generate-codex.py` elsewhere)
2. OpenAI Images API
3. Nano Banana
4. Seedream

Use the adapters described in `references/provider-routing.md`. Move forward only after the current provider returned a visual-QA-failed candidate eligible for retry, lacks the required capability before producing an image, or recorded an availability/authentication/quota/service failure. Provider errors do not authorize skipping an untouched intermediate provider.

## Coordinate parallel work safely

Display source-qualified worker-to-image assignments, the actual planned sub-agent count and any capacity limits before confirmation. After confirmation, validation, initialization and the required batch review, create the confirmed workers using the runtime's delegation tool, reduced only for current capacity. Writing a parallelism field alone does not start workers. Follow dispatch and collection in `references/provider-routing.md`; reuse a shared pool across sources, capped at ten globally and five per run. Disclose capacity reductions and any resulting queue reassignment without rewriting frozen approval; increasing approved capacity or otherwise revising the plan requires confirmation. With zero sub-agents the main agent executes all five images serially. Workers use unique staging paths and never record, promote or finalize. The coordinator runs script checks and serial record operations without repeating visual QA; only collection-accepted candidates are promoted. Never dispatch two candidates for one image at once; retries and fallback remain serial within that image.

## Finalize honestly

Complete or skip the empty collection review, promote accepted images, and finalize after all open tasks are resolved:

```bash
python3 scripts/manage-run.py finalize --run-dir <run>
```

Finalize against the confirmed task total. If fewer tasks pass because budgets are exhausted, collection recheck failed or technical blockers remain, use `--allow-partial`, deliver only passed comics grouped by proposal, and report the missing tasks per proposal. Never fill the set with a failed image.

If every provider failed only for setup reasons (`unavailable`, `authentication` or `quota`) while tasks still have unused slots, leave the run open instead: a finalized run cannot accept more images. Report what to configure (install and log in to Codex CLI, or set a provider key) so the same run can resume within its confirmed scope. Use `--allow-partial` in that case only when the user asks to close the run.

Keep every image-producing candidate, prompt, QA record, asset hash, duel, error log, and final path. Report final paths, provider/model, attempt count, any shortfall, and the actual typography/cast distribution. Separate pre-generation design review from post-generation visual QA; neither substitutes for the other.

Inspect the actual candidate and record candidate-bound observations before comparing with the plan. An unreviewed draft is `review_status: pending`, not PASS, and cannot be recorded as an accepted candidate or promoted. The manager checks evidence structure, not whether the reviewer truly looked or whether a joke is funny. The coordinator must not reopen the image for a routine second visual review. Never copy planned text into a purported transcription or fabricate landmarks to satisfy a ratio. Report `H1: NA` only for a planned `visible-only` shot, with visible-proportion observations and the limitation explicitly recorded.

## Preview gallery

Before final delivery, export the finalized run with `python3 scripts/export-gallery.py --run-dir <run> --language <zh|en>` and link the returned `gallery` HTML path. For multiple sources, keep each independent source group in its own run, with consecutive screenshots together in `input.content`; after all runs finalize, export one gallery using repeated `--run-dir` and an explicit `--output`. Default each source to Passed finals, with Attempts and All filters and visible picture counts. Keep all available attempt images, including failures and composites, in the chronological All view without proposal sections. Final cards link to that idea’s generation history; lightbox navigation follows the active filter. Preserve filter state across source, language and layout switches, and keep ambiguous or missing final provenance explicit. Mark the matching PASS as the final rather than duplicating its image; retain distinct generation records even when their bytes match. Keep proposal summaries, prompts and QA in collapsed details. Local composites show their component prompts and consume no extra generation call. Open runs awaiting setup recovery are exported only after completion. Export errors do not require regeneration. See `references/gallery.md`.

## Hard stops

- Do not generate, call a paid image API, or initialize a formal run before the single confirmation of the current five-image plan, totals and worker allocation and successful assignment validation. Rendering a plan does not grant approval.
- Do not exceed three image-producing calls for any task.
- Do not transfer budget between tasks.
- Do not accept a comic that is merely cute, accurate, or polished but not funny.
- For QA 11 reject material loss of tier, identity, emotional intent or readability; treat minor decorative variations as warnings. Preserve explicit user locks. Frozen QA 10 keeps its original marker and count rules.
- Do not relabel a converted joke as the source's native direction, or change a direction label just to silence a warning.
- Do not accept missing, additional, unreadable, misspelled, incorrectly ordered, or wrong-language core text.
- Do not accept a required physical partner replaced by an avatar, an offscreen balloon, or Whale-chan speaking their lines. Record visible lettering treatment, speaker connectors, and cast representation as QA evidence.
- Do not treat the automatic-mode recommendation as an exact-size gate. Do not accept a wrong aspect ratio in automatic mode or any pixel mismatch in explicit mode.
- Do not judge a custom style or outfit against the canonical default it replaced. Do not accept an unrecognizable fact anchor, permanent identity drift, proportion drift, broken anatomy/contact, accidental crop, confused reading order, or detailed supporting characters.
- Do not depend on files outside this Skill except user-supplied references that the run manager freezes and hashes. Do not depend on external scripts or fonts.
