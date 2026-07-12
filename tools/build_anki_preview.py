#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from common import ROOT, cloze_back, cloze_front, iter_chapters, load_yaml, rel, safe_markdown_to_html

ENV = Environment(
    loader=FileSystemLoader(ROOT / "templates"),
    autoescape=select_autoescape(["html"]),
)


def card_count(note: dict) -> int:
    if note.get("type") == "qa":
        return 1
    return len(set(re.findall(r"\{\{c(\d+)::", note.get("text") or "")))


def build(chapter: dict) -> tuple[Path, Path]:
    source = chapter["path"] / "anki.yml"
    data = load_yaml(source)
    notes = [n for n in data["notes"] if not n.get("disabled")]
    rendered_notes = []
    for note in notes:
        if note["type"] == "qa":
            front = safe_markdown_to_html(note["question"])
            back = safe_markdown_to_html(note["answer"])
        else:
            front = safe_markdown_to_html(cloze_front(note["text"]))
            back = safe_markdown_to_html(cloze_back(note["text"]))
        extra = safe_markdown_to_html(note.get("extra"))
        if extra:
            back += f'<div class="extra">{extra}</div>'
        rendered_notes.append({"front": front, "back": back})
    css_uri = (ROOT / "styles" / "anki.css").resolve().as_uri()
    html = ENV.get_template("anki/preview.html").render(
        title=chapter["title"], notes=rendered_notes, css_uri=css_uri
    )
    preview = chapter["path"] / "anki-preview.html"
    preview.write_text(html, encoding="utf-8")
    types = Counter(n["type"] for n in notes)
    cards = sum(card_count(n) for n in notes)
    extra_count = sum("coverage::extra" in (n.get("tags") or []) for n in notes)
    priorities = Counter(tag for n in notes for tag in n.get("tags", []) if tag.startswith("priority::"))
    summary = chapter["path"] / "anki-summary.md"
    summary.write_text(
        "\n".join([
            f'# {chapter["title"]} Anki 覆盖摘要',
            "",
            f'- Chapter ID：`{data["chapter_id"]}`',
            f'- 有效 Note：{len(notes)}',
            f'- 生成 Card：{cards}',
            f'- QA / Cloze：{types["qa"]} / {types["cloze"]}',
            f'- 讲义外补充卡：{extra_count}',
            f'- P0 / P1：{priorities["priority::P0"]} / {priorities["priority::P1"]}',
            "- Schema、稳定 ID、Cloze 与必需标签：由 `tools/validate_anki.py` 校验。",
            "- 覆盖结论：知识关系、操作命令、关键参数、验证边界、诊断下一步与经典任务均需有主动提取表达。",
            "",
        ]),
        encoding="utf-8",
    )
    print(f"built {rel(preview)} and {rel(summary)}")
    return preview, summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--chapter")
    parser.add_argument("--track", choices=["common", "rhcsa", "rhce"])
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()
    chapters = list(iter_chapters([args.track] if args.track else ("common", "rhcsa", "rhce")))
    if args.chapter:
        chapters = [c for c in chapters if c["slug"] == args.chapter]
    elif not args.all:
        parser.error("choose --chapter or --all")
    missing = [c for c in chapters if not (c["path"] / "anki.yml").exists()]
    if missing:
        print("missing Anki YAML: " + ", ".join(c["id"] for c in missing), file=sys.stderr)
        return 1
    for chapter in chapters:
        build(chapter)
    return 0


if __name__ == "__main__":
    sys.exit(main())

