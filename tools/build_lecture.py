#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from pypdf import PdfReader

from common import ROOT, chrome_pdf, iter_chapters, lecture_markdown_to_html, load_manifest, rel

ENV = Environment(
    loader=FileSystemLoader(ROOT / "templates"),
    autoescape=select_autoescape(["html"]),
)


def wrap_html(title: str, body: str, output: Path, profile: str = "reading") -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    css_name = "lecture-reading.css" if profile == "reading" else "lecture.css"
    template = "lecture-reading.html" if profile == "reading" else "lecture.html"
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
    release = ROOT / "dist" / chapter["track"] / profile / "chapters" / f'{chapter["number"]:02d}-{chapter["slug"]}.pdf'
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
    manifest = load_manifest()
    common = list(iter_chapters(["common"]))
    chapters = common + list(iter_chapters([track]))
    title = f'RHEL 9 {track.upper()} 讲义'
    filename = "RHEL9-RHCSA-讲义-大字号阅读版.pdf" if track == "rhcsa" and profile == "reading" and not incomplete else book_filename(track, incomplete)
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
