#!/usr/bin/env python3
"""Summarize the scripts the user typed in recent local agent sessions; read-only.

Scans Claude Code (~/.claude/projects) and Codex CLI (~/.codex/sessions) records
from the last day, keeps only messages the user typed, and counts them by script.
The agent makes the final language decision; this is evidence, not a verdict.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import unicodedata

KANA = re.compile(r"[぀-ヿ]")
HANGUL = re.compile(r"[가-힯]")
HAN = re.compile(r"[一-鿿]")
CYRILLIC = re.compile(r"[Ѐ-ӿ]")
LATIN = re.compile(r"[A-Za-zÀ-ɏ]")
# Drop paths, URLs and code so a Chinese request quoting a file path still reads as Chinese.
NOISE = re.compile(r"```.*?```|`[^`]*`|https?://\S+|(?:~|\.{0,2})?/[\w.@~/-]+|\$[\w-]+", re.S)
SIMPLIFIED = set("这个们说时会对还没为过发后来见问题国学开关门长东车马书图张让应该给实现简写语")
TRADITIONAL = set("這個們說時會對還沒為過發後來見問題國學開關門長東車馬書圖張讓應該給實現簡寫語")
INJECTED = ("<", "# AGENTS.md instructions", "Caveat:", "[Request interrupted by user")


def parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return stamp if stamp.tzinfo else stamp.replace(tzinfo=timezone.utc)


def typed(text: str) -> str | None:
    text = text.strip()
    if not text or text.startswith(INJECTED):
        return None
    return text


def claude_messages(root: Path, since: datetime):
    for path in root.glob("*/*.jsonl"):
        if datetime.fromtimestamp(path.stat().st_mtime, timezone.utc) < since:
            continue
        with path.open(encoding="utf-8", errors="replace") as handle:
            for line in handle:
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if record.get("type") != "user" or record.get("isMeta") or record.get("isSidechain"):
                    continue
                stamp = parse_time(record.get("timestamp"))
                content = (record.get("message") or {}).get("content")
                parts = [content] if isinstance(content, str) else [
                    item.get("text", "") for item in content or [] if isinstance(item, dict) and item.get("type") == "text"]
                for part in parts:
                    if stamp and stamp >= since and (text := typed(part)):
                        yield "claude-code", str(path), stamp, text



def codex_messages(root: Path, since: datetime):
    for path in root.glob("*/*/*/rollout-*.jsonl"):
        if datetime.fromtimestamp(path.stat().st_mtime, timezone.utc) < since:
            continue
        interactive = True
        with path.open(encoding="utf-8", errors="replace") as handle:
            for line in handle:
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                payload = record.get("payload") or {}
                if record.get("type") == "session_meta":
                    # `codex exec` sessions carry prompts written by tools such as generate-codex.py.
                    source = payload.get("source")
                    interactive = source != "exec" and not isinstance(source, dict)
                if not interactive or record.get("type") != "response_item" or payload.get("role") != "user":
                    continue
                stamp = parse_time(record.get("timestamp"))
                for item in payload.get("content") or []:
                    if stamp and stamp >= since and item.get("type") == "input_text" and (text := typed(item.get("text", ""))):
                        yield "codex", str(path), stamp, text



def classify(text: str) -> str | None:
    clean = NOISE.sub(" ", text)
    clean = "\n".join(line for line in clean.splitlines() if not line.lstrip().startswith(">"))
    if len(clean.strip()) < 3 or clean.strip().lower() in {"okay", "yes", "sure", "thanks", "continue"}:
        return None
    if KANA.search(clean):
        return "ja"
    if HANGUL.search(clean):
        return "ko"
    han = HAN.findall(clean)
    if len(han) >= 2:
        simplified = sum(char in SIMPLIFIED for char in han)
        traditional = sum(char in TRADITIONAL for char in han)
        return "zh-Hant" if traditional > simplified else "zh-Hans"
    if len(CYRILLIC.findall(clean)) >= 3:
        return "cyrillic"
    if len(LATIN.findall(clean)) >= 3:
        return "latin"
    if sum(unicodedata.category(char).startswith("L") for char in clean) >= 3:
        return "other"
    return None


def detect(hours: float, home: Path, samples: int) -> dict:
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    seen, rows = set(), []
    stores = {"claude-code": home / ".claude" / "projects", "codex": home / ".codex" / "sessions"}
    readers = {"claude-code": claude_messages, "codex": codex_messages}
    for agent, root in stores.items():
        if not root.is_dir():
            continue
        for source, session, stamp, text in readers[agent](root, since):
            # Deduplicate repeated transport records, not later messages with the same wording.
            key = (session, stamp, hashlib.sha256(text.encode("utf-8")).hexdigest())
            if key in seen:
                continue
            seen.add(key)
            if (script := classify(text)):
                rows.append({"agent": source, "session": session, "time": stamp, "script": script, "text": text})
    counts = Counter(row["script"] for row in rows)
    agents = Counter(row["agent"] for row in rows)
    leading = counts.most_common(1)[0][0] if counts else None
    rows.sort(key=lambda row: row["time"], reverse=True)
    sessions = {}
    for row in rows:
        session = sessions.setdefault(row["session"], {"session": row["session"], "agent": row["agent"],
            "last_user_message": row["time"].isoformat(), "by_script": {}, "latest": []})
        script = row["script"]
        session["by_script"][script] = session["by_script"].get(script, 0) + 1
        if len(session["latest"]) < samples:
            session["latest"].append({"script": script, "excerpt": row["text"][:240]})
    if sessions:
        leading = max(next(iter(sessions.values()))["by_script"], key=next(iter(sessions.values()))["by_script"].get)
    return {
        "sessions": list(sessions.values()),
        "window_hours": hours,
        "stores": {agent: root.is_dir() for agent, root in stores.items()},
        "messages": len(rows),
        "by_agent": dict(agents),
        "by_script": dict(counts.most_common()),
        "leading": leading,
        "suggested_tag": {"latin": None, "cyrillic": None, "other": None}.get(leading, leading),
        "latest": [{"agent": row["agent"], "time": row["time"].isoformat(), "script": row["script"],
                    "excerpt": row["text"][:80]} for row in rows[:samples]],
        "note": "Latin or Cyrillic script does not identify the language; read the excerpts. "
                "Use current-session expression first; otherwise inspect the newest meaningful session, not global counts. Quoted source material may still require agent exclusion.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hours", type=float, default=24)
    parser.add_argument("--samples", type=int, default=5)
    parser.add_argument("--home", default=os.path.expanduser("~"), help=argparse.SUPPRESS)
    args = parser.parse_args()
    print(json.dumps(detect(args.hours, Path(args.home), args.samples), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
