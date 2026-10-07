# Exaggeration tiers

Exaggeration is how hard a joke is performed, not where its laugh lives. Any comedy direction can be played at any tier, so choose the tier for the execution after the five ideas are selected. `references/exaggeration-tiers.json` is the authority for each tier's ten-axis palette, landing markers, allowed performance levels, sound-effect limits and default background; `build-prompt.py` and QA read it directly.

| Tier | Register | In one line |
|---|---|---|
| `A` | manga impact | Detailed scene, bold camera, effect lines, manga_burst face, stylized lettering, a world that reacts |
| `B` | comic outburst | Desk-slamming accusation, a situation running out of hand, comic collapse |
| `C` | restrained deadpan | Gentle, dry or bittersweet; the line, a glance or negative space carries it |

The same idea can play at all three. "You may eat what's in my fridge": at `C` she stands calmly in the doorway hugging the fridge with a small "收到。"; at `B` the user slams the desk and points while she charges out pushing it; at `A` a low-angle kitchen shot shows her lifting the fridge one-handed against a backlit impact flash, a drawn "咚——！" and the user knocked to their knees with white dot eyes.

## Tier the landing panel

`exaggeration` names the tier of the landing panel, where the punchline hits. It defaults to the last panel; set `landing_panel` when the landing comes earlier. Every `expression_plan` entry carries its own `tier`, and setup panels never exceed the landing tier. A calm setup followed by an explosion is often the joke itself, so do not run four panels at full `A` by default.

Each panel's expression `performance` must be allowed by its tier: `C` reaches `heightened`, `B` adds `punchline_peak`, `A` adds `manga_burst`.

## Choose a tier from the execution

Pick the tier that performs this idea best, not by rank, image number or panel count. Mismatching the tier and the event is a legitimate technique:

- **Mock epic:** play a trivial event at `A` (choosing lunch staged as a final battle).
- **Deadpan disaster:** play a catastrophe at `C` (the server burns while she sips tea).

For a bittersweet or tender source, prefer mock epic or a `contrast` for its `A` image, and record why that idea can carry the impact without trampling the tone.

## Cover all three tiers

By default (`exaggeration_policy: {"mode": "narrative"}`) the five images of each run include at least one `A`, one `B` and one `C`. Two images remain free. Only a real user instruction such as "全部 C 档" permits `{"mode": "user-override", "user_instruction": "..."}`. Coverage binds the plan; when an image fails its budget, finalize reports the missing tier instead of reassigning another image.

## Lower one axis on purpose

A landing panel may declare `contrast`: `{"panel", "axes", "lowered_to", "reason"}`. The named axes are performed at the lower tier while the rest stay at the declared tier, as in an `A` scene where her face stays flat (`A（脸→C）`). The image still counts as its declared tier. Markers whose axes are all lowered are waived; the lowered axes are checked against the lower tier's palette. The reason must say why the flat axis is funnier, not merely that it is different.

## Declare the landing effects

`effects_plan` lists the landing panel's key effects, each with its axis, drawn from the tier's palette. Small effects inside the palette need no declaration; anything outside the palette fails QA. This keeps `C` from being quietly decorated and keeps declared `A` effects from going missing.

## Background follows the tier

When the user resolves no background, use the tier's default and record `background.origin: "tier"`: `A` a detailed text-free location, `B` an effect background, `C` pure white. A user-resolved background (`origin: "user"`) always wins and waives the `A-background` marker.

Detailed `A` scenes invite pseudo-text. Turn signs, screens, book spines and labels blank or away from the viewer; any writing that matters belongs in `core_text`.

## Deformation and identity

`manga_burst` is fully open: blank or dot eyes, giant mouths, tear rivers, sudden chibi shifts, a soul leaving the body, petrified cracks, or a face-only gekiga rendering. In a deformed panel, judge identity by the anchors instead of the face: keep at least three of hair, fin ears, ahoge, tail and maid outfit clearly visible. Deformed panels use visible-only proportion review. A gekiga face stays on the face; if the heavy rendering spreads to the body, background or the whole canvas, that is a style shift and fails.

## Lettering

Drawn sound effects are text: put each one in `core_text` and attribute it in `dialogue_plan` with `speaker: narrator` and `delivery: sfx`, drawn into the scene without a balloon. `A` allows two sound effects of at most four characters, `B` one, `C` none. The text-style template still controls letterforms; `text-style-routing.md` lists which templates usually suit each tier, without enforcing it.

## Repair a missed tier

When QA finds the landing panel below its tier or outside its palette, keep the joke and the frozen plan and retry once naming only the missing markers or the violating axis. Do not change the tier to match a weak render; that is a plan revision and needs a new confirmation.
