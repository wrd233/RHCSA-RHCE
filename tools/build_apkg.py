#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

import genanki

from common import ROOT, iter_chapters, load_manifest, load_yaml, safe_markdown_to_html, stable_int

CARD_CSS = """
.card { font-family: -apple-system, BlinkMacSystemFont, 'Hiragino Sans GB', sans-serif; font-size: 20px; line-height: 1.55; color: #172033; background: #fff; text-align: left; padding: 24px; }
code { font-family: Menlo, 'Hiragino Sans GB', sans-serif; background: #eef2f6; border-radius: 3px; padding: .08em .25em; }
pre { font-size: 16px; background: #f4f6f8; border-left: 3px solid #315b87; padding: 12px; white-space: pre-wrap; }
.extra { color: #475569; border-top: 1px solid #cbd5e1; margin-top: 16px; padding-top: 12px; font-size: .88em; }
.nightMode .card { color: #e5e7eb; background: #111827; }
.nightMode code, .nightMode pre { background: #1f2937; }
"""

QA_MODEL = genanki.Model(
    stable_int("RedHat-QA-v1"),
    "RedHat-QA",
    fields=[{"name": "ID"}, {"name": "Question"}, {"name": "Answer"}, {"name": "Extra"}],
    templates=[{
        "name": "RedHat-QA",
        "qfmt": "{{Question}}",
        "afmt": "{{Answer}}<div class=\"extra\">{{Extra}}</div>",
    }],
    css=CARD_CSS,
)

CLOZE_MODEL = genanki.Model(
    stable_int("RedHat-Cloze-v1"),
    "RedHat-Cloze",
    fields=[{"name": "ID"}, {"name": "Text"}, {"name": "Extra"}],
    templates=[{
        "name": "RedHat-Cloze",
        "qfmt": "{{cloze:Text}}",
        "afmt": "{{cloze:Text}}<div class=\"extra\">{{Extra}}</div>",
    }],
    css=CARD_CSS,
    model_type=genanki.Model.CLOZE,
)


def build(track: str) -> Path:
    if track not in {"rhcsa", "rhce"}:
        raise ValueError(track)
    manifest = load_manifest()
    deck_name = manifest[track]["deck"]
    deck = genanki.Deck(stable_int(deck_name), deck_name)
    note_count = 0
    card_count = 0
    for chapter in iter_chapters(["common", track]):
        data = load_yaml(chapter["path"] / "anki.yml")
        for item in data["notes"]:
            if item.get("disabled"):
                continue
            tags = list(item.get("tags") or [])
            if chapter["track"] == "common" and f"exam::{track}" not in tags:
                continue
            if item["type"] == "qa":
                fields = [
                    item["id"],
                    safe_markdown_to_html(item["question"]),
                    safe_markdown_to_html(item["answer"]),
                    safe_markdown_to_html(item.get("extra")),
                ]
                model = QA_MODEL
                card_count += 1
            else:
                fields = [item["id"], safe_markdown_to_html(item["text"]), safe_markdown_to_html(item.get("extra"))]
                model = CLOZE_MODEL
                card_count += len(set(re.findall(r"\{\{c(\d+)::", item["text"])))
            note = genanki.Note(model=model, fields=fields, tags=tags, guid=genanki.guid_for(item["id"]))
            deck.add_note(note)
            note_count += 1
    output = ROOT / "build" / "anki" / f"RHEL9-{track.upper()}.apkg"
    output.parent.mkdir(parents=True, exist_ok=True)
    genanki.Package(deck).write_to_file(output)
    release = ROOT / "releases" / track / output.name
    release.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(output, release)
    print(f"built {release.relative_to(ROOT)}: {note_count} notes, {card_count} cards")
    return release


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("track", choices=["rhcsa", "rhce"])
    args = parser.parse_args()
    missing = [c["id"] for c in iter_chapters([args.track]) if not (c["path"] / "anki.yml").exists()]
    if missing:
        print("missing Anki YAML: " + ", ".join(missing), file=sys.stderr)
        return 1
    build(args.track)
    return 0


if __name__ == "__main__":
    sys.exit(main())
