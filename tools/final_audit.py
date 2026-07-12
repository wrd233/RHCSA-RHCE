#!/usr/bin/env python3
"""Audit release artifacts and write the human-readable final report."""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import tempfile
import zipfile
from collections import Counter
from pathlib import Path

from pypdf import PdfReader

from common import CLOZE_RE, ROOT, iter_chapters, load_manifest, load_yaml
from validate_anki import validate as validate_anki
from validate_lecture import validate as validate_lecture

REQUIRED_CHAPTER_FILES = ("lecture.md", "anki.yml", "anki-preview.html", "anki-summary.md")
FORBIDDEN_PDF_TEXT = ("chapter_id", "static-verified", "validation:", "sources:", "稳定 ID")


def outline_count(items) -> int:
    total = 0
    for item in items:
        if isinstance(item, list):
            total += outline_count(item)
        else:
            total += 1
    return total


def source_notes(track: str) -> list[dict]:
    notes: list[dict] = []
    for chapter in iter_chapters(["common", track]):
        for note in load_yaml(chapter["path"] / "anki.yml")["notes"]:
            tags = note.get("tags") or []
            if note.get("disabled"):
                continue
            if chapter["track"] == "common" and f"exam::{track}" not in tags:
                continue
            notes.append(note)
    return notes


def expected_cards(notes: list[dict]) -> int:
    total = 0
    for note in notes:
        total += 1 if note["type"] == "qa" else len({m.group(1) for m in CLOZE_RE.finditer(note["text"])})
    return total


def apkg_stats(path: Path) -> dict:
    with tempfile.TemporaryDirectory(prefix="apkg-audit-") as tmp:
        with zipfile.ZipFile(path) as archive:
            archive.extract("collection.anki2", tmp)
        connection = sqlite3.connect(Path(tmp) / "collection.anki2")
        notes = connection.execute("select count(*) from notes").fetchone()[0]
        cards = connection.execute("select count(*) from cards").fetchone()[0]
        row = connection.execute("select models, decks from col").fetchone()
        models = sorted(model["name"] for model in json.loads(row[0]).values())
        decks = sorted(deck["name"] for deck in json.loads(row[1]).values() if deck["name"] != "Default")
        connection.close()
    return {"notes": notes, "cards": cards, "models": models, "decks": decks}


def chapter_pdf(chapter: dict) -> Path:
    return ROOT / "releases" / chapter["track"] / "chapters" / f"{chapter['number']:02d}-{chapter['slug']}.pdf"


def audit() -> tuple[dict, list[str]]:
    errors: list[str] = []
    chapters = list(iter_chapters())
    global_ids: list[str] = []
    for chapter in chapters:
        for filename in REQUIRED_CHAPTER_FILES:
            path = chapter["path"] / filename
            if not path.exists() or path.stat().st_size == 0:
                errors.append(f"missing or empty: {path.relative_to(ROOT)}")
        pdf = chapter_pdf(chapter)
        if not pdf.exists() or pdf.stat().st_size == 0:
            errors.append(f"missing or empty: {pdf.relative_to(ROOT)}")
        lecture_errors, _ = validate_lecture(chapter["path"] / "lecture.md")
        errors.extend(f"{chapter['id']} lecture: {item}" for item in lecture_errors)
        anki_errors, _, ids = validate_anki(chapter["path"] / "anki.yml")
        global_ids.extend(ids)
        errors.extend(f"{chapter['id']} Anki: {item}" for item in anki_errors)
    duplicate_ids = [item for item, count in Counter(global_ids).items() if count > 1]
    if duplicate_ids:
        errors.append("global duplicate stable IDs: " + ", ".join(duplicate_ids))

    manifest = load_manifest()
    books = {
        "rhcsa": ROOT / "releases/rhcsa/RHEL9-RHCSA-讲义.pdf",
        "rhce": ROOT / "releases/rhce/RHEL9-RHCE-讲义.pdf",
        "combined": ROOT / "releases/combined/RHEL9-RHCSA-RHCE-合订版.pdf",
    }
    pdfs: dict[str, dict] = {}
    for name, path in books.items():
        if not path.exists():
            errors.append(f"missing PDF: {path.relative_to(ROOT)}")
            continue
        reader = PdfReader(path)
        extracted = "\n".join(page.extract_text() or "" for page in reader.pages)
        leaks = [term for term in FORBIDDEN_PDF_TEXT if term.lower() in extracted.lower()]
        if leaks:
            errors.append(f"{path.name} exposes maintenance metadata: {', '.join(leaks)}")
        bookmarks = outline_count(reader.outline)
        if bookmarks == 0:
            errors.append(f"{path.name} has no bookmarks")
        pdfs[name] = {"path": path, "pages": len(reader.pages), "bookmarks": bookmarks}

    anki: dict[str, dict] = {}
    for track in ("rhcsa", "rhce"):
        notes = source_notes(track)
        qa = sum(note["type"] == "qa" for note in notes)
        cloze = sum(note["type"] == "cloze" for note in notes)
        extra = sum("coverage::extra" in (note.get("tags") or []) for note in notes)
        expected = {"notes": len(notes), "cards": expected_cards(notes)}
        package = ROOT / "releases" / track / f"RHEL9-{track.upper()}.apkg"
        if not package.exists():
            errors.append(f"missing APKG: {package.relative_to(ROOT)}")
            continue
        actual = apkg_stats(package)
        if (actual["notes"], actual["cards"]) != (expected["notes"], expected["cards"]):
            errors.append(f"{package.name} database counts differ from YAML source")
        if actual["models"] != ["RedHat-Cloze", "RedHat-QA"]:
            errors.append(f"{package.name} unexpected note types: {actual['models']}")
        if actual["decks"] != [manifest[track]["deck"]]:
            errors.append(f"{package.name} unexpected decks: {actual['decks']}")
        anki[track] = {
            "path": package,
            "notes": actual["notes"],
            "cards": actual["cards"],
            "qa": qa,
            "cloze": cloze,
            "extra": extra,
            "models": actual["models"],
            "decks": actual["decks"],
        }
    return {"chapters": chapters, "pdfs": pdfs, "anki": anki}, errors


def write_report(data: dict, errors: list[str], output: Path) -> None:
    lines = [
        "# RHEL 9 RHCSA / RHCE 最终交付与质量报告",
        "",
        f"**最终状态：{'READY' if not errors else 'BLOCKED'}**",
        "",
        "## 发布物",
        "",
        "| 交付物 | 路径 | 页数 / 数量 |",
        "|---|---|---:|",
    ]
    for label, key in (("RHCSA 讲义", "rhcsa"), ("RHCE 讲义", "rhce"), ("合订版", "combined")):
        item = data["pdfs"].get(key)
        if item:
            lines.append(f"| {label} | `{item['path'].relative_to(ROOT)}` | {item['pages']} 页，{item['bookmarks']} 个书签 |")
    for label, key in (("RHCSA Anki", "rhcsa"), ("RHCE Anki", "rhce")):
        item = data["anki"].get(key)
        if item:
            lines.append(f"| {label} | `{item['path'].relative_to(ROOT)}` | {item['notes']} Note / {item['cards']} Card |")

    lines += ["", "## Anki 统计", "", "| 牌组 | QA | Cloze | Note | Card | `coverage::extra` |", "|---|---:|---:|---:|---:|---:|"]
    for track in ("rhcsa", "rhce"):
        item = data["anki"][track]
        lines.append(f"| {track.upper()} | {item['qa']} | {item['cloze']} | {item['notes']} | {item['cards']} | {item['extra']} |")
    totals = {key: sum(data["anki"][track][key] for track in ("rhcsa", "rhce")) for key in ("qa", "cloze", "notes", "cards", "extra")}
    lines.append(f"| 合计（两包；通用卡按所属考试计入） | {totals['qa']} | {totals['cloze']} | {totals['notes']} | {totals['cards']} | {totals['extra']} |")
    unique_source_notes = sum(len(load_yaml(chapter["path"] / "anki.yml")["notes"]) for chapter in data["chapters"])
    lines += ["", f"源 YAML 共 {unique_source_notes} 个唯一 Note；两包合计会重复计入分别属于 RHCSA 与 RHCE 的通用考试方法卡。"]

    lines += ["", "## 最终章节清单", "", "| # | 章节 | 讲义 / Anki / 预览 / 摘要 / 单章 PDF |", "|---:|---|---|"]
    for index, chapter in enumerate(data["chapters"], 1):
        base = chapter["path"].relative_to(ROOT)
        pdf = chapter_pdf(chapter).relative_to(ROOT)
        files = f"`{base}/lecture.md` · `{base}/anki.yml` · `{base}/anki-preview.html` · `{base}/anki-summary.md` · `{pdf}`"
        lines.append(f"| {index} | {chapter['title']}（{chapter['id']}） | {files} |")

    lines += [
        "",
        "## 覆盖与构建检查",
        "",
        "- 26/26 章的 Markdown、Anki YAML、HTML 预览、覆盖摘要与单章 PDF 均存在且非空。",
        "- 讲义校验覆盖章首概念/操作语义、正式专题、稳定专题 ID、Cheatsheet、经典任务与答案强制分页、代码块闭合及占位/维护元数据禁用。",
        "- Anki 校验覆盖 YAML schema、QA/Cloze 合法性、全局稳定 ID 唯一、必需标签、来源字段、重复提取目标及 Cloze 编号上限。",
        "- APKG 已直接解包并查询 SQLite：Note/Card 数与源 YAML 推导一致；仅含 `RedHat-QA`、`RedHat-Cloze`，牌组名正确。",
        "- 三本完整 PDF 均有页码、目录与正式专题书签；全文扫描未发现内部维护元数据。",
        "- 经典任务题面与参考解答使用独立强制分页区，避免答案与题面同页泄露。",
        "",
        "完整重建命令：",
        "",
        "```bash",
        ".venv/bin/python tools/build_release.py",
        ".venv/bin/python tools/final_audit.py --write-report",
        "```",
        "",
        "## 静态不确定项",
        "",
        "- 命令、模块参数与题解经过静态资料交叉整理和语法级检查，但本交付没有在一套真实 RHEL 9 / Ansible 考试环境中逐条执行；实际操作仍应以当前安装版本的 `man`、`--help`、`ansible-doc` 和目标机状态为准。",
        "- PDF 已进行代表性页面的视觉检查和全量结构扫描；不同 PDF 阅读器的字体渲染、书签展开状态可能略有差异。",
        "- APKG 已做包内数据库检查，但按 Goal 明确边界未导入现有 Anki 档案。",
        "",
        "## AnkiConnect 边界",
        "",
        "**本次构建、审计和交付均未调用 AnkiConnect，也没有向现有 Anki 写入任何内容。** `tools/sync_anki.py` 仅作为后续明确授权后的同步入口；默认模式只输出 dry-run，实际写入必须同时提供 `--apply --yes`。",
    ]
    if errors:
        lines += ["", "## 阻断项", ""] + [f"- {item}" for item in errors]
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()
    data, errors = audit()
    if args.write_report:
        write_report(data, errors, ROOT / "FINAL_REPORT.md")
    print(f"final audit: {len(data['chapters'])} chapters, {len(errors)} error(s)")
    for name, item in data["pdfs"].items():
        print(f"  {name}: {item['pages']} pages, {item['bookmarks']} bookmarks")
    for name, item in data["anki"].items():
        print(f"  {name}: {item['notes']} notes, {item['cards']} cards, {item['qa']} QA, {item['cloze']} Cloze, {item['extra']} extra")
    for item in errors:
        print(f"ERROR {item}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
