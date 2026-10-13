# Offline preview gallery

For v17/v18 a delivery sub-agent merges completed image journals, promotes/finalizes and exports HTML. Main returns the resulting links. File/link/count checks do not authorize generation or another visual review.

After generation and QA, finalize the run and export its gallery before delivery. This uses Python 3 and the existing ImageMagick `magick` dependency, with no image API calls or frontend build step.

```bash
python3 scripts/export-gallery.py --run-dir <completed-run> --language <zh|en>
python3 scripts/export-gallery.py --run-dir <source-a-run> --run-dir <source-b-run> \
  --language <zh|en> --output artifacts/whalechan-image-comic/<batch-name>/gallery
```

A single run defaults to `<run>/gallery/index.html`. A batch requires `--output`. Existing outputs are preserved by selecting `gallery-02`, `gallery-03`, etc. The command prints the actual HTML path and missing-record warnings as JSON. Link that path in the final delivery. `--language` sets the page's initial language (`zh` for a Chinese session, `en` otherwise; default `zh`) and the language of the printed warnings. The masthead button switches the page between Chinese and English and remembers the viewer's choice in that browser. Records stay structured; user text, prompts and proposal content are shown as recorded, never translated. Copy or zip the entire gallery directory when sharing; the HTML needs its adjacent `assets/` folder.

## Organization and interaction

One independent source group or creative theme is one run and one tab. Consecutive screenshots share that run's `input.content` list and proposal set. Preserve the user-specified grouping and order; do not split consecutive screenshots into separate runs just for display. For a batch, export all finalized runs in the requested tab order in one call. A single gallery contains only one skill's runs.

Source/theme tabs wrap into three columns on desktop and two columns at widths up to 700px. Labels wrap in full rather than truncating or requiring horizontal scrolling.

Show original requests, source images and separately labelled visual references above one comic-image grid per source. Add source-local filters: Passed finals (default), Attempts, and All, with counts of available pictures. Passed finals shows one formally delivered full comic per task, using the recorded final even when its source attempt is ambiguous or missing; a PASS component or unselected PASS candidate is not a final. Attempts shows records not uniquely identified as the delivered final, including failed candidates, components, and ambiguous matching records. All retains the complete chronological sequence below. Do not create proposal headings or separate proposal image grids. Grid and list use the same filtered collection. Show stable proposal titles on cards and keep scene descriptions, prompts and QA in each image's collapsed details, and retain selected and unselected summaries under one collapsed records section. Include unselected summaries from the frozen `creative_pool` when proposal options contain only the selected five.

Passed finals follows the approved proposal/image order. In All and Attempts, order comic images by their recorded timestamps, normalizing timezones. Preserve original task/attempt order for equal timestamps; put absent or invalid timestamps last in that same stable order. Retain a separate card for each image-bearing record, even when multiple records have identical bytes. Mark the uniquely matched PASS record as the final and avoid a second card for its final-file copy. If multiple records match, label the candidates as matching the final with ambiguous provenance; do not choose a prompt arbitrarily. In All, show a standalone final only when no available eligible attempt picture matches it, and expose missing provenance explicitly. Passed finals always shows one available final per delivered task; when several attempt records match it, retain those separate records in Attempts and All without choosing one as its source.

Open any comic card in a lightbox with keyboard navigation restricted to the current filtered collection, native-size viewing, details and focus restoration. Keep each source's filter and idea scope during tab, language and layout changes within the browsing session. Final cards offer an action to show all versions of that idea, with a return to all ideas. Use stable proposal titles and attempt identifiers rather than renumbering cards after filtering. Empty finals stay empty and offer an explicit action to view attempts. Final counts reflect deliverable pictures, not the number of PASS records; ambiguous matching records remain individually available in history without inventing prompt ownership. Keep original-input and visual-reference navigation in their own collections. The shared character-gallery branch retains proposal grouping; mirror shared exporters/templates while limiting the flat layout to comic exports.

## Evidence and counts

Finals are matched to recorded candidates by hash, never by assuming the last attempt won. Actual prompts are collapsed and copyable; every candidate keeps its own prompt, provider/model, QA results and recorded defects. Browser clipboard restrictions fall back to selected text for manual copying.

A generation count is the number of image-producing attempts, including failed candidates and comic components. Local composition and promotion add no calls. The flat grid can therefore contain more pictures than generation calls when local composites are included. Errors that returned no image remain text records and never create image cards. Composite comics expose their source components and prompts, not an invented single prompt. A partial run exposes failed versions through Attempts and All with failure badges and preserves gaps in its records; failed candidates never acquire final badges.

The exporter reads supported records without modifying or migrating them: character assignment v5–6 / manifest v3, or comic assignment v11 and v13–16 / manifest v1 in the comic skill. It checks the assignment hash and available recorded image hashes, but does not perform or replace visual QA. Missing optional historical files appear as missing, never fabricated. Unsupported schemas, changed hashes and open runs fail export. Setup-blocked runs remain open and resumable under the existing workflow; do not finalize them just to obtain a gallery.

Character screenshot inputs must name existing files, absolute or relative to the assignment file. New runs archive them as `source/original-01.*`, etc. Text requests remain text. Historical source files are used only when their recorded paths still resolve. Source interpretations are labelled separately from user wording.

Image files are copied byte for byte and deduplicated by content hash. HTML embeds its script, styles and data; all image paths are relative, and no network access or `fetch()` is needed. Prompt/source text is rendered as text. Gallery folders remain portable after being moved. In-repository gallery templates/exporters are mirrored in both skills so either skill can be installed alone; keep mirrored files identical when editing them.

## QA 11 records

For v15/v16/v17/v18, display accepted minor issues and core defects with each attempt. A single-image PASS awaiting or failing collection is not a delivered final. Include collection contact sheets, set-level decisions, task outcomes and stage events in collapsed details; these sheets do not count as provider calls or comic candidates. Technical blockers may have no visual QA, because technical rejection does not require LLM inspection or regeneration. Preserve all returned-image call counts.

For v18 use batch-deliver for promotion, finalization, aggregate export, index, file/hash/count verification and the task receipt. It reuses matching interrupted outputs. Keep service-paused runs open. HEIC/HEIF source images retain an original asset plus a local PNG display copy; candidates/finals are never converted by this compatibility path. Verify hashes of all embedded gallery-data asset references, not only static src/href attributes.
