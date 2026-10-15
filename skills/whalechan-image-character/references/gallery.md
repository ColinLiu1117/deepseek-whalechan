# Offline preview gallery

After generation and QA, finalize the run and export its gallery before delivery. This uses Python 3 and the existing ImageMagick `magick` dependency, with no image API calls or frontend build step.

```bash
python3 scripts/export-gallery.py --run-dir <completed-run> --language <BCP-47>
python3 scripts/export-gallery.py --run-dir <source-a-run> --run-dir <source-b-run> \
  --language <BCP-47> --output artifacts/whalechan-image-character/<batch-name>/gallery
```

A single run defaults to `<run>/gallery/index.html`. A batch requires `--output`. Existing outputs are preserved by selecting `gallery-02`, `gallery-03`, etc. The command prints the actual HTML path and missing-record warnings as JSON. Link that path in the final delivery. The saved interface language sets the initial page language; `--language` explicitly overrides it. Offer Simplified Chinese, English and the task languages. Remember a manual selection per gallery, never globally. Supply extra complete UI dictionaries with `--locales`; see `language-policy.md`. Records stay structured; user text, prompts and proposal content are shown as recorded, never translated. Copy or zip the entire gallery directory when sharing; the HTML needs its adjacent `assets/` folder.

## Organization and interaction

One independent source group or creative theme is one run and one tab. Consecutive screenshots share that run's `input.content` list and proposal set. Preserve the user-specified grouping and order; do not split consecutive screenshots into separate runs just for display. For a batch, export all finalized runs in the requested tab order in one call. A single gallery contains only one skill's runs.

Source/theme groups appear in a sticky sidebar index. Each entry shows a thumbnail of the group's input image (or its first final), its number, the full title and pass/call counts; titles wrap rather than truncate. `[` and `]` switch groups from anywhere on the page, arrow keys move within the index, and previous/next buttons close each group. At widths up to 900px the index becomes a horizontally scrolling row above the content. A single-group gallery hides the index.

The warm ivory page shows original requests, source images and separately labelled visual references, then all proposals. Selected proposals group all their final images together. Unselected proposals retain collapsed summaries. Grid is the default; list view retains the same groups. Original images, references, finals and attempts open in the same full-screen viewer (zoom, pan, thumbnail strip, details panel, input-image comparison for generated pictures) with keyboard navigation and focus restoration. Navigation stays within the current source collection, proposal's finals or image's attempts.

## Evidence and counts

Finals are matched to recorded candidates by hash, never by assuming the last attempt won. Actual prompts are collapsed and copyable; every candidate keeps its own prompt, provider/model, QA results and recorded defects. Browser clipboard restrictions fall back to selected text for manual copying.

A generation count is the number of image-producing attempts, including failed candidates. Promotion adds no calls. Errors that returned no image are counted separately. A partial run shows gaps; failed candidates never become final artwork in the gallery.

The exporter reads supported records without modifying or migrating them: character assignment v7 / manifest v3, or comic assignment v19 / manifest v1 in the comic skill. It checks the assignment hash and available recorded image hashes, but does not perform or replace visual QA. Missing files appear as missing, never fabricated. Unsupported schemas, changed hashes and open runs fail export. Setup-blocked runs remain open and resumable under the existing workflow; do not finalize them just to obtain a gallery.

Character screenshot inputs must name existing files, absolute or relative to the assignment file. New runs archive them as `source/original-01.*`, etc. Text requests remain text. Source interpretations are labelled separately from user wording.

Image files are copied byte for byte and deduplicated by content hash. HTML embeds its script, styles and data; all image paths are relative, and no network access or `fetch()` is needed. Prompt/source text is rendered as text. Gallery folders remain portable after being moved. In-repository gallery templates/exporters are mirrored in both skills so either skill can be installed alone; keep mirrored files identical when editing them.
