# Cross-case creative review

For v17 assign this existing comparison to a planning sub-agent after source drafts are ready; main only relays its results. It does not add a new review gate. Final collections are handled by collection sub-agents.

Run this design comparison before the first image call in a multi-source batch. For v15/v16/v17 final images, use only the per-source contact-sheet review in `review-workflow.md`, not another cross-source visual review. Frozen contracts retain their original final comparison. Keep the review beside the batch assignments; do not rewrite frozen history.

## Compare sources, not slots

Start with each source's actual turn, comic target, tone, language differences and user corrections. Compare the selected N ideas within each source and across sources in a case-by-position matrix. Each source contributes its own N images, one per idea; check both the unique creative payoff and the 1/2/4-panel and A/B/C tier coverage (or the recorded user overrides). For N>=3 both coverage rules apply; N=1/2 is exempt. Applying the coverage rules mechanically can invite a fixed recipe, such as every source pairing a one-panel A with a four-panel B; `validate-batch` flags the same panel or tier sequence by position (`repeated_panel_sequence`, `repeated_tier_sequence`) and the same panel-by-tier pairing in any order (`repeated_panel_tier_sequence`); each repeat needs a source-specific reason or a revision. Run it with `--draft` on the planning drafts before displaying the plan, and with `--assignment` on the confirmed assignments before generating. Inspect mechanism, setup/reveal timing, panel count/layout, exaggeration tier, shot, character staging, text placement and lettering. Also compare across positions: shuffling images can disguise the same recipe.

`validate-batch` provides structural signals, not semantic verdicts; a near-copy that differs in one cell still needs your eye. Same-position layouts/templates, identical panel sequences and repeated staging deserve inspection. A repeated visual identity is expected. Neither repeated structure nor every image passing structural checks is automatically wrong; the question is whether each decision follows its source. Different template counts are not proof of different jokes.

Review each source's tier policy in this same pass. New five-image sets use 3A/1B/1C; other N aim close to 60%/20%/20% with content-based integer allocation. Inspect the displayed deviations and whether the selected actions/expressions actually support the assigned tiers. A repeated aggregate 3:1:1 count is expected under this policy; ordinal or panel-tier pairings still need source-specific reasoning. Preserve frozen historical policies.

Inspect repeated key lines, complete dialogue sequences and final punchlines as well as layout warnings. Cite the affected images. Shared source wording can be necessary, but identical replies and consequences require a concrete explanation or an in-idea revision. A generic claim that the ideas share a source is insufficient. Text similarity is a review signal, not an automatic elimination threshold or permission to generate another pool.

Use two counterfactual checks:

- **Dialogue substitution:** could another case's dialogue replace this one without materially changing the picture? If yes, explain what makes the scene source-specific or redesign it.
- **Ordinal removal:** hide image numbers. Can you still justify each shot, panel count, tier and text treatment from the selected premise? Changing order should only change identifiers, not creative choices.

## Review record

Write `batch-review.md` with:

1. Cases and versions reviewed, with paths to assignments or candidate images.
2. Specific repeated combinations, including those not caught by the script.
3. For each concern, affected cases/images and either a source-grounded reason to retain it or the actual revision made.
4. Any uncertainty requiring source clarification; do not silently assume an ambiguous joke.
5. Conclusion: ready for generation, revise plans, or final images still need review.

Perform this agent review before displaying the complete plan for the single user confirmation. For v15 review the final per-source contact sheets through the collection lifecycle, without another routine user approval. After confirmation, changes to the core idea or execution allocation require an updated displayed plan and confirmation of that revision. Do not satisfy a warning by random font rotation, forced camera variety, or merely reordering images. If repetition is legitimate, retain it and record why.

## Honest limits

Scripts cannot establish humor or independent visual inspection from prose fields. Record what was actually inspected and leave pending work pending. Compare final images with their sources as well as with each other; a perfectly rendered wrong interpretation still fails.

For v18/v19 the planning worker submits the actual cross-source observation and warning dispositions to batch-proposal in the ordered source list. The command verifies/computes structural data but never substitutes for creative comparison. Use collection-task for the existing final per-source review; do not add another cross-source visual pass.

For mixed N, compare all available rows; a shorter source has no missing-position defect. Review each source against its own confirmed count.
