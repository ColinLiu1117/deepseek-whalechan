# Comedy engine

## Understand the source before adapting it

Record `input.source_analysis` before exploring premises:

- `source_event`: what actually happens and who speaks;
- `comic_target`: who or what the joke is about;
- `tone`: the source's emotional register, including bitterness or affection;
- `language_notes`: meaningful differences between supplied language versions and between the source and the lettering language, or explicitly state that none were supplied/found;
- `user_constraints`: the user's actual creative corrections, locked interpretations and visual requirements for the comic, or `[]`. Process instructions such as "plan only", "no images yet" or "give five proposals" are not constraints; the single generation confirmation governs them, and they must never reach a generation prompt;
- `native_direction`: `{direction, reason}` — the comedy direction the source itself already uses (see below), or `direction: null` when the source is not funny on its own. The reason cites what in the source makes it funny that way, or why it carries no joke of its own.

Separate evidence from interpretation. Do not claim certainty about an ambiguous pun. Read all supplied language versions; a literal translation can lose a social meaning or change who is being mocked. Preserve explicit user corrections unless they conflict with what can safely be depicted; report conflicts instead of silently substituting another joke.

Identify the native direction from how the source actually lands, not from what is easiest to draw. A screenshot that is funny because "this is exactly me" is `recognition` even if a twist could be invented for it. A plain request or statement with no joke of its own ("you may eat what's in my fridge") is `null`; do not assign it a direction just to have one.

## Five directions

Each premise has exactly one primary `direction`. The direction decides which fields carry the laugh. Only `reversal` uses expectation and reversal.

| Direction | Where the laugh comes from | Carrier fields |
|---|---|---|
| `reversal` 反转 | An expectation is broken or reread: strategic literalism, misreading, ambiguity, selective denial | `expectation`, `reversal` |
| `exposure` 暴露/降格 | A front is punctured: outer performance versus inner truth, a blunt put-down, status deflation, self-exposure | `surface`, `truth`, `exposure` (how the truth becomes visible) |
| `escalation` 升级/荒诞 | A small premise is followed rigorously to an extreme | `steps`: three or more escalating beats |
| `recognition` 共鸣/观察 | "That's exactly it" — an accurate, familiar truth, sometimes bittersweet | `situation`, `recognition` (the moment the viewer feels seen) |
| `character` 角色梗 | Whale-chan's established traits are the joke (rice as compute, standby slacking, tsundere denial) | `trait`, `trigger` (what in the source event sets the trait off) |

These describe where the laugh lives, not a menu to rotate through. Several directions can coexist in one comic; record the one that actually carries the punchline and mention the others in `mechanism`.

**Character gags.** Traits may flavor any direction. Prefer a pure character gag only when it competes well against source-specific alternatives; there is no reserved slot or maximum count. Compare how clearly its trigger comes from the source. Removing the trait mentally helps expose a generic sticker whose source has disappeared.

## Relate candidates to the native direction

Use the native direction as evidence about what makes the source funny, not an admission rule. Prefer preserving it when that produces the stronger joke; no candidate is guaranteed a place because it is native. Mark `is_native` truthfully, and mark none native when the source has no native direction. Do not relabel a converted joke to make the pool look balanced.

Review concentration in one direction and repeated character gags as comparative weaknesses where they reduce variety. Explain justified concentration in the review. Do not enforce direction quotas or change a label to silence a warning.

## Rhythm is an optional layer, used sparingly

Rhythm is a delivery technique layered on a direction, never a direction itself: `triple` (rule of three / deliberate repetition), `pause` (a beat of silence), `callback` (a later panel returns to an earlier element), `deadpan` (flat delivery of something absurd). Callbacks stay within one comic.

Default to no rhythm (`rhythm: null`). Most jokes do not need one. Declare it only when removing it would clearly weaken the punchline — for example, a source whose joke *is* the identical reply repeated. The `reason` must say why; "adds rhythm" or "funnier" is not a reason. Review every declared rhythm before freezing and delete those that do not pass this test. When more than half of a set's images declare rhythm, `validate-assignment` raises `rhythm_majority`; confirm each one in `warning_dispositions` or remove the unnecessary ones.

## Generate one concise pool of 2N

For each source's target N (default 5), author exactly 2N concise distinct candidates before choosing winners or layouts. Give each a comparable description: premise, primary direction and its carrier fields, punchline/key dialogue, personality, fact anchor, scene, mechanism and visual payoff. Different situations, actions and consequences create different ideas; replacing a noun, pose or prop does not.

Freeze this pool. Candidates carry no PASS/FAIL label; PASS/FAIL belongs to image QA. Weak ideas still enter the comparisons, and the pool is never extended or regenerated. Refine wording without replacing the core idea; preserve the actual candidates and judgments instead of reverse-engineering losers from finished image plans.

Compare source fidelity, clarity, surprise, joke strength, visual contribution, timing, concise dialogue and recognizable character acting. Treat illustrated summaries, decorative reactions, unrelated metaphors, explanation-heavy dialogue and repetitive beats as weaknesses in that comparison, not separate creative rejection gates. Structural correctness, user constraints and image QA remain separate obligations.

Do not force every source into reversal or self-serving wordplay. Native recognition, escalation, blunt exposure and precise reactions can carry a stronger joke than generic food, laziness or technical spectacle.

## Independently rank once, then stage N selected ideas

A different real sub-agent reads the original source, constraints and frozen pool. Rank all 2N by comprehensive priority, weighing source fidelity, laugh strength, visual contribution, concise dialogue and set variety together. The first N form the selected set; candidate IDs and storage order never determine priority.

Write one short reason per candidate and one paragraph explaining the selected set, including justified similarities. Submit ranking and selection_reason via planning-task selection-submit; the script binds identities and pool hash and derives selected IDs. Do not use numeric scoring, pairwise duels, multiple judges, another de-duplication ranking, or replacement candidates. Structural errors can be corrected in the same record; they do not call for another semantic review.

Return the detail task to the original author. Make one image plan per selected idea, preserving its premise, key lines, scene and payoff. Compare replies and visual consequences within the selected set. Pose, font and background swaps alone do not establish different jokes. Only selected ideas need full panel/action/expression/typography fields.

Receive the source tier policy before creating/selecting ideas. New N=5 sets require 3 A, 1 B and 1 C; for other N the author allocates tiers by content close to 60%/20%/20%. For N>=3 retain independent panel counts 1/2/4 and tier coverage, unless explicitly overridden. N=1/2 relaxes coverage while aiming close to the ratio. Never add empty beats or map rank to panels or tiers. Review complete visual plans and their allocation across sources before the one confirmation in proposal-selection.md.

Frozen v13–v18 retain their original ten-candidate, 45-pair tournament and historical ranking/recovery. See the historical tournament section in run-schema.md; do not apply it to new runs.

## Perform each idea at a tier

Direction says where the laugh lives; exaggeration says how hard it is performed. After selecting N ideas, give each image a tier — `A` manga impact, `B` comic outburst, `C` restrained deadpan — and for N>=3 cover all three across the run unless the user overrides it. The tier belongs to the execution, so do not preassign it as a candidate score or follow rank or panel count. See `exaggeration-tiers.md`.

A quiet close-up may still be the strongest punchline, and a trivial event may deserve full impact. Never use vulnerable groups, private information, hate, discrimination, sexual humiliation or actual harm as a shortcut to a joke, at any tier. Random cruelty is not a punchline.

## Keep text disciplined

Prefer a compact final knife and short bubbles. Put the strongest word near the end when the language permits it. Preserve meaningful pauses and direct insults when they are the source's mechanism rather than euphemizing them into a different joke. Follow applicable safety limits.

The text should perform the joke, not explain it. Put every intended semantic string in `core_text` with speaker/delivery attribution; writing on an object uses `delivery: label` with its `prop`. A plan or carrier that relies on readable writing (a labelled folder, a poem scroll) must give that writing a `label` line, or describe the prop by shape and color instead; printed writing that belongs to no character uses `speaker: narrator`. Documents whose words do not matter need no label. Keep analytical explanations in the creative record. Review executions within and across the selected proposals and, for batches, use `batch-review.md` before generation.
