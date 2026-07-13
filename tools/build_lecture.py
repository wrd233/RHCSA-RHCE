#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from pypdf import PdfReader, PdfWriter
from pypdf.annotations import Link

from common import ROOT, chrome_pdf, iter_chapters, lecture_markdown_to_html, load_manifest, rel

ENV = Environment(
    loader=FileSystemLoader(ROOT / "templates"),
    autoescape=select_autoescape(["html"]),
)


def wrap_html(title: str, body: str, output: Path, profile: str = "reading") -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    if profile != "reading":
        raise ValueError("only the formal reading profile is supported")
    css_name = "lecture-reading.css"
    template = "lecture-reading.html"
    css_uri = (ROOT / "styles" / css_name).resolve().as_uri()
    rendered = ENV.get_template(template).render(title=title, body=body, css_uri=css_uri)
    output.write_text(rendered, encoding="utf-8")


def chapter_html(chapter: dict) -> str:
    source = chapter["path"] / "lecture.md"
    return lecture_markdown_to_html(source.read_text(encoding="utf-8"))


def display_title(chapter: dict) -> str:
    if chapter["track"] == "rhcsa":
        clean = re.sub(r'^RHCSA-\d+\s*', '', chapter["title"])
        return f'第 {chapter["number"]:02d} 章　{clean}'
    return chapter["title"]


def build_chapter(chapter: dict, profile: str = "reading") -> Path:
    out_dir = ROOT / "build" / "chapters" / profile / chapter["track"] / chapter["slug"]
    html_path = out_dir / "lecture.html"
    pdf_path = out_dir / "lecture.pdf"
    body = re.sub(r'<h1>.*?</h1>', f'<h1>{display_title(chapter)}</h1>', chapter_html(chapter), count=1)
    wrap_html(display_title(chapter), body, html_path, profile)
    chrome_pdf(html_path, pdf_path)
    release = (ROOT / "releases" / "rhcsa-v5.1" / "chapters" / f'{chapter["number"]:02d}-{chapter["slug"]}.pdf'
               if chapter["track"] == "rhcsa" and profile == "reading"
               else ROOT / "dist" / chapter["track"] / profile / "chapters" / f'{chapter["number"]:02d}-{chapter["slug"]}.pdf')
    release.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(pdf_path, release)
    print(f"built {rel(release)} ({len(PdfReader(release).pages)} pages)")
    return release


def book_body(title: str, chapters: list[dict]) -> str:
    toc = "".join(f'<li><a href="#chapter-{c["id"].lower()}">{c["title"]}</a></li>' for c in chapters)
    parts = [
        f'<section class="book-title"><h1>{title}</h1><p>RHEL 9 实操考试备考讲义</p></section>',
        f'<nav class="toc"><h1>目录</h1><ol>{toc}</ol></nav>',
    ]
    for chapter in chapters:
        body = chapter_html(chapter)
        body = re.sub(r"<h1([^>]*)>", f'<h1 id="chapter-{chapter["id"].lower()}"\\1>', body, count=1)
        parts.append(body)
    return "\n".join(parts)


def book_filename(track: str, incomplete: bool) -> str:
    return f'RHEL9-{track.upper()}-V2-INCOMPLETE-PREVIEW.pdf' if incomplete else f'RHEL9-{track.upper()}-讲义.pdf'


def build_book(track: str, incomplete: bool = False, profile: str = "reading") -> Path:
    chapters = list(iter_chapters([track]))
    title = f'RHEL 9 {track.upper()} 讲义'
    filename = "RHEL9-RHCSA-讲义-大字号阅读版.pdf" if track == "rhcsa" and profile == "reading" and not incomplete else book_filename(track, incomplete)
    if track == "rhcsa" and profile == "reading" and not incomplete:
        return build_reading_book_from_chapters(chapters)
    out_dir = ROOT / "build" / "books" / profile / track
    html_path = out_dir / f"{track}.html"
    pdf_path = out_dir / filename
    wrap_html(title, book_body(title, chapters), html_path, profile)
    chrome_pdf(html_path, pdf_path)
    release = ROOT / "dist" / track / profile / filename
    release.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(pdf_path, release)
    print(f"built {rel(release)} ({len(PdfReader(release).pages)} pages)")
    return release


def build_reading_book_from_chapters(chapters: list[dict]) -> Path:
    """Merge accepted chapter PDFs; never reflow the 33 Markdown documents."""
    release_root = ROOT / "releases/rhcsa-v5.1"
    chapter_paths = [release_root / "chapters" / f'{c["number"]:02d}-{c["slug"]}.pdf' for c in chapters]
    missing = [path for path in chapter_paths if not path.is_file()]
    if missing:
        raise FileNotFoundError("build chapter PDFs before the book: " + ", ".join(map(str, missing)))
    page_counts = [len(PdfReader(path).pages) for path in chapter_paths]
    toc = "".join(
        f'<li><strong>{c["id"]}</strong>　{c["title"]}　<span>{pages} 页</span></li>'
        for c, pages in zip(chapters, page_counts)
    )
    front_body = (
        '<section class="book-title"><h1>RHCSA RHEL 9 v5.1</h1>'
        '<p>大字号正式阅读版</p><p>由 33 个已验收单章 PDF 原样合并</p></section>'
        f'<nav class="toc"><h1>目录与阅读导航</h1><ol>{toc}</ol></nav>'
    )
    out_dir = ROOT / "build/books/reading/rhcsa"
    front_html = out_dir / "front-matter.html"
    front_pdf = out_dir / "front-matter.pdf"
    wrap_html("RHCSA RHEL 9 v5.1", front_body, front_html, "reading")
    chrome_pdf(front_html, front_pdf)
    writer = PdfWriter()
    writer.append(str(front_pdf))
    front_pages = len(PdfReader(front_pdf).pages)
    offset = front_pages
    part_parents: dict[str, object] = {}
    chapter_offsets = []
    for chapter, path, pages in zip(chapters, chapter_paths, page_counts):
        chapter_offsets.append(offset)
        writer.append(str(path), import_outline=False)
        part = chapter.get("part", "RHCSA")
        if part not in part_parents:
            part_parents[part] = writer.add_outline_item(part, offset)
        chapter_parent = writer.add_outline_item(
            f'{chapter["id"]} {chapter["title"]}', offset, parent=part_parents[part]
        )
        source_reader = PdfReader(path)
        def copy_outline(items, parent):
            last_parent = parent
            for item in items:
                if isinstance(item, list):
                    copy_outline(item, last_parent)
                    continue
                if not hasattr(item, "title"):
                    continue
                try:
                    local_page = source_reader.get_destination_page_number(item)
                except Exception:
                    continue
                last_parent = writer.add_outline_item(str(item.title), offset + local_page, parent=parent)
        copy_outline(source_reader.outline, chapter_parent)
        offset += pages
    # The front-matter TOC spans two pages. Add PDF GoTo annotations over each
    # chapter row and named destinations for assistive/document tooling.
    per_page = (len(chapters) + max(front_pages - 1, 1) - 1) // max(front_pages - 1, 1)
    for index, (chapter, target) in enumerate(zip(chapters, chapter_offsets)):
        toc_page = 1 + index // per_page
        row = index % per_page
        y_top = 748 - row * 38
        writer.add_annotation(toc_page, Link(rect=(52, y_top - 24, 543, y_top + 8), target_page_index=target))
        writer.add_named_destination(chapter["id"], target)
    release = release_root / "RHCSA-RHEL9-v5.1.pdf"
    staging = out_dir / "RHCSA-RHEL9-v5.1.staging.pdf"
    staging.parent.mkdir(parents=True, exist_ok=True)
    with staging.open("wb") as handle:
        writer.write(handle)
    actual = len(PdfReader(staging).pages)
    expected = front_pages + sum(page_counts)
    if actual != expected:
        raise RuntimeError(f"book page equation failed: {actual} != {sum(page_counts)} + {front_pages}")
    release.parent.mkdir(parents=True, exist_ok=True)
    staging.replace(release)
    print(f"built {rel(release)} ({actual} pages = {sum(page_counts)} chapter + {front_pages} front matter)")
    return release


def build_parts(track: str, profile: str = "reading") -> list[Path]:
    chapters = list(iter_chapters([track]))
    grouped: dict[str, list[dict]] = {}
    for chapter in chapters:
        grouped.setdefault(chapter["part"], []).append(chapter)
    outputs = []
    for index, (part, members) in enumerate(grouped.items(), 1):
        title = f'RHEL 9 {track.upper()}　{part}'
        out_dir = ROOT / "build" / "parts" / profile / track
        html_path = out_dir / f"part-{index:02d}.html"
        pdf_path = out_dir / f"part-{index:02d}.pdf"
        wrap_html(title, book_body(title, members), html_path, profile)
        chrome_pdf(html_path, pdf_path)
        release = ROOT / "dist" / track / profile / "parts" / f"{index:02d}-{part.replace('　', '-')}.pdf"
        release.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(pdf_path, release)
        outputs.append(release)
        print(f"built {rel(release)} ({len(PdfReader(release).pages)} pages)")
    return outputs


def build_combined() -> Path:
    chapters = list(iter_chapters(["common", "rhcsa", "rhce"]))
    title = "RHEL 9 RHCSA / RHCE 合订讲义"
    filename = "RHEL9-RHCSA-RHCE-合订版.pdf"
    out_dir = ROOT / "build" / "books" / "combined"
    html_path = out_dir / "combined.html"
    pdf_path = out_dir / filename
    wrap_html(title, book_body(title, chapters), html_path)
    chrome_pdf(html_path, pdf_path)
    release = ROOT / "releases" / "combined" / filename
    release.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(pdf_path, release)
    print(f"built {rel(release)} ({len(PdfReader(release).pages)} pages)")
    return release


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--chapter", help="chapter slug")
    parser.add_argument("--track", choices=["common", "rhcsa", "rhce"])
    parser.add_argument("--book", choices=["rhcsa", "rhce", "combined"])
    parser.add_argument("--all-chapters", action="store_true")
    args = parser.parse_args()
    if args.book:
        build_combined() if args.book == "combined" else build_book(args.book)
        return 0
    chapters = list(iter_chapters([args.track] if args.track else ("common", "rhcsa", "rhce")))
    if args.chapter:
        chapters = [c for c in chapters if c["slug"] == args.chapter]
    elif not args.all_chapters:
        parser.error("choose --chapter, --all-chapters, or --book")
    missing = [c for c in chapters if not (c["path"] / "lecture.md").exists()]
    if missing:
        print("missing lectures: " + ", ".join(c["id"] for c in missing), file=sys.stderr)
        return 1
    for chapter in chapters:
        build_chapter(chapter)
    return 0


if __name__ == "__main__":
    sys.exit(main())
