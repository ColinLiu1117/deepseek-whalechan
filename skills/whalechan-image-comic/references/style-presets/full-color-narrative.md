# 精致全彩叙事漫画 / Full-color narrative

Preset ID: `full-color-narrative`. Opt-in aliases: 精致全彩叙事漫画、全彩韩漫风. For this Whale-chan workflow, interpret these aliases as the rendering treatment below, not a change of character or a promise to reproduce every convention of Korean comics. The canonical style remains the default when this preset is not selected.

## Apply through the existing v20 fields

This is a planning preset, not a new schema mode or CLI switch. For every selected image, expand its rendering description into `style.mode: custom` and `style.description` before confirmation. Do not add an unsupported `style.preset` field or rely on the preset name alone in a drawing prompt. Preserve the resolved task language; translate the description when needed.

Chinese field fragment (merge into a complete image plan):

```json
{
  "style": {
    "mode": "custom",
    "description": "精致全彩叙事漫画：清晰细致、轻重有变化的深蓝轮廓线，柔和色彩渐变结合形体明确的赛璐璐阴影；头发以清楚的发束和克制高光表现层次，眼睛通透但保持原有蓝色身份；肤色和衣料有柔和受光，避免塑料般过亮。画面主次清楚，人物表情与关键道具优先；有场景时使用统一环境光和适度背景虚化，有效果背景或纯白背景时保留同样的人物上色品质。日常表情细腻，笑点处按已选夸张等级变形。保持鲸鱼娘原有圆脸、发色、鲸鳍耳、呆毛、鲸尾、服装及冻结的头身比例；配角维持低细节靛蓝抽象人物。"
  }
}
```

Keep `costume`, `proportion`, `background`, `output`, exaggeration, typography and panel count independently resolved. In particular, selecting this preset alone does not authorize a uniform, a longer body, a portrait aspect ratio, detailed supporting characters, or a different background policy. Missing costume remains canonical and missing proportion remains semi-chibi (2.8 heads). Retain explicit user choices instead of resetting them to defaults.

## Identity and reference authority

Use the existing canonical identity anchor, retaining its `identity`, canonical `costume`, and preset `proportion` roles as applicable, but remove its `style` role for this custom style. Preserve broad round face, blue-gradient eyes, deep-ocean-blue hair with cyan curled ends, paired whale-fin ears, forward-curving ahoge and coherent whale tail. Do not copy the style example's uniform, body geometry, orange-haired companion, crying personality, account names, watermark, dialogue, or plot.

This preset is self-contained and needs no clipboard images. When the user supplies visual style examples in a future run, use them as `style` only; add `composition` only when that layout is requested and supported. Freeze supplied references with the normal run process. Keep the canonical identity reference first, the chosen bundled typography reference as the sole typography authority, and the existing five-reference limit. Never load a style example as a supporting-character identity reference.

## Camera and story treatment

Translate these choices into `action_plan[].action`, `composition.shot`, `composition.staging`, expression descriptions and dialogue placements; do not leave them only in the preset label.

- Alternate an establishing medium shot, a meaningful prop close-up and a character reaction when each adds new information. Select shots by story need rather than mechanically cycling them.
- A phone screen or document close-up can carry the fact anchor. Put all essential visible words in `core_text`; leave incidental book spines and background signs blank.
- Preserve detailed everyday expressions alongside tier-appropriate comic deformation. A polished finish must not suppress the punchline or turn every scene into crying, blushing or passive cuteness.
- Use clear balloon tails, readable text and enough space around faces. Retain the selected typography template; this preset does not override its authority.
- When a scene background is already selected, keep its lighting and spatial cues coherent. Under existing tier defaults, B still uses an effect background and C still uses pure white. A user request for continuous scenic backgrounds resolves `background` separately with `origin: user`; do not infer that request from style selection alone.

## Supported layouts and limits

This first preset uses the current engine: one panel (`single`), two (`top-bottom` or `left-right`), or four (`2x2`). The existing panel/tier distribution policy stays in force. Vary camera scale inside supported panels to create visual rhythm.

The sample's wide-wide-split four-panel page, six-panel page, slanted inset, overlapping panels and multi-page continuity are not implemented by this preset. Do not encode these as `2x2`, bypass validation, or promise them in the confirmation plan. They require a separate layout-engine change. Do not import a sample's aspect ratio implicitly.

## Review against the resolved plan

Use the existing QA pass, without an extra review round. Check that the custom finish is visible (fine linework, controlled gradients, readable hair masses and coherent lighting where applicable), while identity, costume, body geometry, cast ownership and exact text remain intact. Abstract partners may receive simple lighting but no detailed hair, costume or replacement mascot. Normal identity anchors stay authoritative even when the rendering is richer. Existing tier-specific deformation exceptions remain unchanged.

Do not fail this preset for departing from canonical bold outlines or restrained cel shading: those are the rendering choices it intentionally replaces. Do fail material identity drift, unreadable text, loss of the planned joke or unsupported layouts under the existing rules. Actual visual quality must be verified on a generated sample; configuration validation alone is not visual proof.
