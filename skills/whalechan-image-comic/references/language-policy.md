# Task language

## Resolve once

Before planning, resolve `language` from an explicit user instruction, otherwise the user's meaningful expression in the current session, otherwise the most recent meaningful local session visible within 24 hours. Current-session evidence does not need to be on disk. If evidence is insufficient, ask. Never infer language from agent defaults, system locale, source material, or total historical message counts.

Run `python3 scripts/detect-language.py` once when historical evidence is needed. It returns sessions ordered by their last meaningful user message, script counts and excerpts. Inspect the recent stretch of user-authored expression; exclude code, quoted/source material, injected instructions, tool-written text and acknowledgments such as “OK”. Script detection is evidence, not a language verdict: Latin text is not automatically English. The collector cannot identify every unmarked quotation; the agent must resolve that ambiguity.

Use normalized BCP-47 tags: `zh-Hans`, `zh-Hant`, `en`, `ja`, etc. Preserve observable script differences; infer regional variants only from explicit instructions or sufficient evidence. The local validator checks tag structure and common Chinese aliases, not the complete IANA registry.

## Save and inherit

Save `language`, optional `language_overrides`, `language_resolution` and `run_title` before presenting a new plan. Example:

```json
{
  "language": "zh-Hans",
  "language_overrides": {"visible_text": "ja"},
  "language_resolution": {"source": "current-session", "reason": "User's recent original expression is Simplified Chinese; user explicitly requested Japanese dialogue."},
  "run_name": "rice-before-reason",
  "run_title": "推理之前先吃饭"
}
```

Allowed resolution sources: `explicit`, `current-session`, `recent-session`, `user-answer`. Store a concise factual reason, not full unrelated session transcripts. Every image has a localized `title`; retain English `run_name`, image `name`/`id`, filenames, field names and enum values internally.

Allowed override scopes: `communication`, `visible_text`, `interface`, `prompt`, `titles`. Resolve each as its explicit override or `language`. Record the actual scoped instruction in the resolution reason. Unscoped “use Japanese” changes the common default; “only dialogue in Japanese” changes visible text only. Retain exact user-locked wording, code, errors, model names and necessary proper nouns.

Pass this record to every worker; workers do not rerun detection. On resume use the saved record even if the current conversation uses another language. A deliberate language change follows the existing revision/confirmation rules for affected frozen content; do not rewrite prior attempts, original user material or historic approval hashes.

## Author and render

Write new communication, descriptions, prompts, QA prose and visible titles in their resolved scopes. Keep exact image text in its resolved language, not automatically the source's language. Comic `input.language` must match `visible_text`; character `text.languages` records the actual lettering languages. Normally include the resolved language and explicitly requested additional languages; when exact user-locked wording uses only another language, record that exact content in `language_resolution.preserved_text` and preserve its actual language tags. No-text character images remain text-free.

Author drawing fields directly in the resolved prompt language before confirmation. Keep reference instructions and retries in that language. Prompt templates localize fixed instructions; identifiers remain internal. Set supporting participants' `role` to a readable prompt-language description. If communication and prompt languages differ, supply comic proposal `display_staging` in the communication language, faithfully preserving the frozen drawing plan. Do not translate or rewrite the initial prompt at dispatch.

## Locale packs

`assets/locales/en.json` defines the complete translation keys and placeholders; `zh-Hans.json` supplies Simplified Chinese. Additional languages, including Traditional Chinese, are authored by the planning/delivery agent as needed, not by a browser service.

Store custom packs under `localizations.<BCP-47 tag>` in the task. Supply only the required sections: `plan` for comic plan messages, `gate` for character confirmation messages, `prompt` for comic prompt templates, and `gallery` for the UI. Every supplied section must contain all keys from the English section and preserve placeholders and template structure. Retain `name` (native language name) and `direction` (`ltr` or `rtl`) for gallery packs. Scripts validate completeness and placeholders, not translation quality; read the translations before use.

Prepare plan/prompt translations before confirmation; they participate in the frozen language contract. Delivery may add gallery-only packs in a separate JSON file passed through `export-gallery.py --locales <file>`; do not mutate the frozen assignment. For batch delivery supply that same file with `batch-deliver --locales <file>`.

## Offline gallery

Export without `--language` to use the saved interface language. Provide Simplified Chinese, English, and every distinct task/override language. The first opening uses the task's interface language; subsequent manual choices are remembered only for that gallery. Browser preferences from other galleries do not override it.

Switch only UI controls, labels, hints and statistics. Preserve recorded titles, source text, plans, prompts, QA and image lettering. The page embeds dictionaries and works offline. Missing translations must be supplied before export; exporting errors do not authorize image regeneration.

## Legacy runs

New character assignments use v7; new comic assignments/batches use v20. Existing v6/v19 records retain their original validation and prompt behavior. Do not fabricate language decisions or migrate their approvals. Legacy exports may retain existing titles/IDs and default to the old Chinese UI unless explicitly overridden.
