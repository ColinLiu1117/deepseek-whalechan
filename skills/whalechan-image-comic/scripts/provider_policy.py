"""Non-generating preflight and the immutable batch tool policy."""
from __future__ import annotations
import os
from pathlib import Path

ORDER = ("codex", "openai", "nano-banana", "seedream")


def validate(value):
    if not isinstance(value, dict) or set(value) != {"provider", "transport", "model", "on_error"}:
        raise ValueError("tool requires provider/transport/model/on_error")
    if value["provider"] not in ORDER or value["on_error"] != "pause":
        raise ValueError("Tool must use a supported provider and on_error=pause")
    if value["transport"] not in ({"builtin", "cli"} if value["provider"] == "codex" else {"api"}):
        raise ValueError("Unsupported provider transport")
    if not isinstance(value["model"], str) or not value["model"].strip():
        raise ValueError("Record configured model, or unknown when not exposed")
    return value


def preflight(manager, evidence, requests=(), expected=None):
    native = evidence.get("builtin", {})
    if native and (type(native.get("available")) is not bool or not native.get("evidence")):
        raise ValueError("builtin requires actual tool-list evidence and boolean available")
    checks = []
    for provider in ORDER:
        if expected and provider != expected["provider"]:
            continue
        transport, model, reason, available = "api", "unknown", "configuration missing", False
        if provider == "codex":
            transport = expected["transport"] if expected else ("cli" if evidence.get("codex_cli") else "builtin")
            if transport == "builtin":
                available = native.get("available") is True
                model = native.get("model") or "unknown"
                reason = "runtime tool evidence" if available else "builtin tool not observed"
            else:
                try:
                    manager.extension_module("generate-codex").check_codex()
                    available, reason = True, "CLI login check"
                except Exception as exc:
                    reason = "CLI check failed: " + type(exc).__name__
        else:
            keys, model_key, default = {
                "openai": (["OPENAI_API_KEY"], "OPENAI_IMAGE_MODEL", "gpt-image-2"),
                "nano-banana": (["GEMINI_API_KEY", "GOOGLE_API_KEY"], "NANO_BANANA_IMAGE_MODEL", "gemini-3.1-flash-image"),
                "seedream": (["ARK_API_KEY"], "SEEDREAM_IMAGE_MODEL", "doubao-seedream-5-0-lite-260128"),
            }[provider]
            available = any(bool(os.environ.get(key)) for key in keys)
            model = os.environ.get(model_key) or default
            if provider == "nano-banana":
                model = model.removeprefix("models/")
            reason = "credential present; quota unverified" if available else "credential missing"
        tool = dict(provider=provider, transport=transport, model=model, on_error="pause")
        if available:
            try:
                for request in requests:
                    data = manager.read_json(Path(request))
                    adapter = manager.extension_module("generate-" + ("nanobanana" if provider == "nano-banana" else provider))
                    spec = adapter.load_request(Path(request))
                    if hasattr(adapter, "effective_size"):
                        adapter.effective_size(spec["output"])
                    if hasattr(adapter, "provider_settings"):
                        adapter.provider_settings(spec["output"])
                    if not 1 <= len(data.get("references", [])) <= 5:
                        raise ValueError("Require one to five effective references")
            except (ValueError, RuntimeError, OSError, KeyError) as exc:
                available, reason = False, "capability check failed: " + str(exc)
        if expected and tool != expected:
            available, reason = False, "Locked transport/model changed; restore original configuration"
        checks.append({"tool": tool, "available": available, "reason": reason})
        if available:
            return {"status": "ready", "tool": validate(tool), "checked_at": manager.now(),
                    "checks": checks, "evidence": evidence,
                    "limitation": "No image call; quota and service health unverified"}
    return {"status": "blocked", "tool": expected, "checked_at": manager.now(), "checks": checks,
            "evidence": evidence, "limitation": "No compatible configured provider found"}


def batch_path(manager, manifest, assignment):
    path = Path(manifest["batch_file"]).resolve()
    batch = manager.read_json(path)
    if batch.get("schema_version") not in manager.SUPPORTED_ASSIGNMENT_VERSIONS or batch["schema_version"] != assignment["schema_version"]:
        raise ValueError("Batch schema_version must match the current assignment schema")
    if batch["execution"] != assignment["execution"]:
        raise ValueError("Run and batch execution policy differ")
    return path


def guard(manager, manifest, assignment, provider=None, model=None, allow_paused=False):
    path = batch_path(manager, manifest, assignment)
    batch = manager.read_json(path)
    tool = validate(assignment["execution"].get("tool"))
    if provider is not None and provider != tool["provider"]:
        raise ValueError("Batch tool is locked; provider switching is forbidden")
    if model is not None and tool["model"] != "unknown" and model != tool["model"]:
        raise ValueError("Batch model is locked")
    if not allow_paused and batch.get("status") in {"paused", "preflight_required", "planning", "initializing"}:
        raise ValueError("Batch paused; explicit user resume required")
    return path, batch
