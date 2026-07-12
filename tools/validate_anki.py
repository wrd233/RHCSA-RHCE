#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

import yaml

from common import CLOZE_RE, iter_chapters, rel


def validate(path: Path) -> tuple[list[str], list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"YAML parse error: {exc}"], [], []
    if not isinstance(data, dict):
        return ["root must be a mapping"], [], []
    for field in ("chapter_id", "deck", "notes"):
        if not data.get(field):
            errors.append(f"missing root field: {field}")
    ids: list[str] = []
    signatures: Counter[tuple[str, str]] = Counter()
    for index, note in enumerate(data.get("notes") or [], 1):
        label = note.get("id") or f"note #{index}"
        note_id = note.get("id")
        if not note_id:
            errors.append(f"{label}: missing id")
        else:
            ids.append(note_id)
        kind = note.get("type")
        if kind not in {"qa", "cloze"}:
            errors.append(f"{label}: invalid type {kind!r}")
        if kind == "qa" and (not note.get("question") or not note.get("answer")):
            errors.append(f"{label}: QA requires question and answer")
        if kind == "cloze":
            text = note.get("text") or ""
            matches = list(CLOZE_RE.finditer(text))
            if not matches:
                errors.append(f"{label}: invalid or missing cloze")
            numbers = {m.group(1) for m in matches}
            if len(numbers) > 2:
                errors.append(f"{label}: more than two cloze numbers")
        tags = note.get("tags") or []
        for prefix in ("exam::", "chapter::", "card::"):
            if not any(str(tag).startswith(prefix) for tag in tags):
                errors.append(f"{label}: missing {prefix} tag")
        if not note.get("source"):
            errors.append(f"{label}: missing source")
        key_text = note.get("question") if kind == "qa" else note.get("text")
        signatures[(kind or "", re.sub(r"\s+", " ", key_text or "").strip())] += 1
        if len(note.get("answer") or "") > 900:
            warnings.append(f"{label}: answer may be too long")
    duplicates = [item for item, count in Counter(ids).items() if count > 1]
    if duplicates:
        errors.append(f"duplicate IDs: {', '.join(duplicates)}")
    for (_, text), count in signatures.items():
        if text and count > 1:
            errors.append(f"duplicate extraction target ({count}x): {text[:80]}")
    return errors, warnings, ids


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*", type=Path)
    args = parser.parse_args()
    paths = args.paths or [c["path"] / "anki.yml" for c in iter_chapters() if (c["path"] / "anki.yml").exists()]
    failures = 0
    global_ids: list[str] = []
    for path in paths:
        errors, warnings, ids = validate(path)
        global_ids.extend(ids)
        for item in warnings:
            print(f"WARN {rel(path)}: {item}")
        for item in errors:
            print(f"ERROR {rel(path)}: {item}")
        failures += len(errors)
    duplicates = [item for item, count in Counter(global_ids).items() if count > 1]
    if duplicates:
        print(f"ERROR global duplicate IDs: {', '.join(duplicates)}")
        failures += 1
    print(f"Anki validation: {len(paths)} file(s), {len(global_ids)} note(s), {failures} error(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

