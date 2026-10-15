# Provider routing

## Batch tool selection

Preflight in priority order: Codex ImageGen, OpenAI Images API, Nano Banana, Seedream. Lock the first compatible configured provider/transport/model in execution.tool. Use batch-prepare and batch-proposal from batch-commands.md; no probe image and no first-image barrier. Builtin availability comes from actual runtime tool evidence, not a shell guess. Preflight checks configuration/capability, not live quota or service health.

Visual failure retries stay on that tool. Any service error pauses new generation; do not retry automatically or switch. Preserve uncertain calls until reconciled, collect already in-flight results, and resume the same tool only after a user request. Safety rejection cannot be treated as a service retry.

## Codex ImageGen

Codex comes first whenever it is installed and logged in, whichever agent runs the Skill. Both paths record provider `codex`:

- **Inside Codex:** call the built-in `image_gen` tool, one call per provider-produced image. Load local references when required. Never shell out to `codex exec` from inside Codex.
- **In any other agent:** use `scripts/generate-codex.py` (below). Codex only renders the image; the calling agent keeps prompting, QA, recording, retries and delivery.

Codex ImageGen exposes no pixel-size parameter, so use it for automatic output and validate the returned native dimensions against the frozen ratio. A square result such as `1254x1254` is valid even though `1024x1024` is recommended. For explicit resolution, preflight records `capability` and considers OpenAI before locking; a capability error after locking pauses the batch. Copy every returned project-bound image into the run before QA and recording.

### Codex CLI adapter

```bash
python3 scripts/generate-codex.py --check
python3 scripts/generate-codex.py --request request.json --output candidate.png [--dry-run]
```

- `--check` confirms `codex` is on `PATH` and `codex login status` reports a login. During preflight, a failed check records `unavailable` or `authentication` and considers the next provider. A failed check after locking pauses the batch; frozen ordered routing uses the recovery reference.
- The request uses the external adapter contract below; generate it with `build-prompt.py --write-request` (add `--from-prompt` for retries, `--edit-target` for edits). The adapter runs `codex exec --json -s read-only` in a temporary directory, attaches the references in order with `-i`, and asks Codex to call ImageGen once with the prompt verbatim. Each reference's roles and instruction are listed by image number, so write instructions that make each role clear.
- It reads the Codex session record (`$CODEX_HOME/sessions/.../rollout-*-<thread>.jsonl`) to find the saved image, compare the prompt ImageGen actually received with the requested prompt, and count the references the tool used. It copies the image to `--output` without overwriting, and leaves the original under `$CODEX_HOME/generated_images/`.
- It writes `<output>.codex.json` (thread id, Codex version, `prompt_verbatim`, reference counts, output hash, `usable`). Pass it to `image-task ingest --provider-audit <output>.codex.json`. `usable: false` means the prompt was rewritten or references were dropped: the image still consumes a slot and cannot pass. `usable: null` means the session record could not verify either; the candidate may pass, but the record marks it unverified and `finalize` lists it under `unverified_provider_audits`.
- Edits, such as correcting lettering on a complete candidate, are ordinary requests: `build-prompt.py --from-prompt <prompt> --edit-target <layout.png>` puts the edit target first ("edit target; keep everything except the lettering unchanged"), then the typography reference. Observed edits re-render the whole canvas while preserving its structure, so review the full image again.
- Categories: missing CLI → `unavailable`; no login → `authentication`; timeout → `timeout`; usage or rate limits → `quota` / `rate_limit`; an ImageGen safety failure → `safety_rejection`; no image → `service`.
- CLI latency and context consumption depend on the active runtime and request; measure them from the current session. The session-record format is not a public Codex contract; if it is missing, the adapter falls back to the thread's image directory and reports `prompt_verbatim: null`.

## External adapter contract

Each adapter accepts `--request <json> --output <png>` and supports `--dry-run`:

```json
{
  "prompt": "complete effective prompt",
  "references": [
    {
      "id": "canonical-identity",
      "path": "path/to/reference.png",
      "roles": ["identity"],
      "instruction": "inherit identity only",
      "sha256": "64 lowercase hexadecimal characters"
    }
  ],
  "output": {
    "format": "png",
    "aspect_ratio": "1:1",
    "resolution": {"mode": "auto", "recommended": "1024x1024"}
  },
  "quality": "medium"
}
```

For current assignments, the prompt contains only the authored drawing descriptions in `prompt-design.md`; output configuration and reference metadata stay in the request. A retry prompt describes the visual correction, never QA codes, reviewer reports or budgets.

`build-prompt.py --write-request` writes this request from the frozen assignment; prefer it over hand-written JSON. `quality` is optional and only affects OpenAI; the other adapters accept and ignore it, so the same request format works with any tool selected during preflight. The nested `output` object is required and must specify format, aspect ratio and resolution. Use 1–5 bundled or frozen user references. Resolve relative paths from the request JSON. Adapters preserve the requested output, reference roles, and hashes in audit output while reporting the effective provider size or tier. Never silently approximate an explicit resolution or drop a required role because of a provider limit; report `capability`; resolve capabilities before locking the tool; a later capability error pauses the batch. A live adapter writes one PNG and never overwrites an existing path.

### OpenAI

`python3 scripts/generate-openai.py --request request.json --output candidate.png [--dry-run]`

- credential: `OPENAI_API_KEY`
- model override: `OPENAI_IMAGE_MODEL`; default `gpt-image-2`
- base override: `OPENAI_BASE_URL`
- automatic mode chooses a ratio-appropriate size with a nominal 1024-pixel short edge; an explicit size must satisfy `gpt-image-2` constraints: both edges multiples of 16, maximum edge 3840, ratio at most 3:1, and total pixels from 655,360 through 8,294,400

### Nano Banana

`python3 scripts/generate-nanobanana.py --request request.json --output candidate.png [--dry-run]`

- credential: `GEMINI_API_KEY` or `GOOGLE_API_KEY`
- model override: `NANO_BANANA_IMAGE_MODEL`
- base override: `GEMINI_BASE_URL`
- supports automatic `1:1` and `9:16` output using the provider's `512`/`1K`/`2K`/`4K` tiers; rejects explicit pixel resolution because the API does not guarantee exact dimensions

### Seedream

`python3 scripts/generate-seedream.py --request request.json --output candidate.png [--dry-run]`

- credential: `ARK_API_KEY`
- model override: `SEEDREAM_IMAGE_MODEL`
- base override: `SEEDREAM_BASE_URL`
- the verified adapter supports automatic `1:1` and `9:16`; it uses `1024x1024` and `1024x1792` respectively, and accepts explicit output only when it equals a verified native size

Record credentials neither in stdout nor in the run. Provider errors without images consume no candidate slot; any viewable returned image consumes one.

## v20 worker execution

Use independent role limits and image-task commands from `agent-orchestration.md`. Default generation capacity is 3 for Codex and 5 for general providers, reduced by known provider limits and runtime slots. Defaults are not a claim about backend capacity. Do not reduce unknown capacity to one automatically.

One generation worker owns an image through automatic checks, single-image QA and permitted retries. It writes only its image journal. Record no-image errors with image-task error; returned images consume budget even if automatic/audit checks fail. Use the version-specific tool policy above; v20 forbids changing the selected tool. The coordinator only dispatches tasks and reports status; it does not inspect images or write detailed QA. Collection/delivery workers perform serial manifest reconciliation.

Delegate a separate ready image to each generation worker. Never use concurrent calls inside one agent as evidence of provider concurrency. On explicit capacity/rate-limit failures, report the evidence and reduce new dispatch; do not interrupt successful in-flight image calls solely to rebalance roles.
