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


def wrap_html(title: str, body: str, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    css_uri = (ROOT / "styles" / "lecture.css").resolve().as_uri()
    rendered = ENV.get_template("lecture.html").render(title=title, body=body, css_uri=css_uri)
    output.write_text(rendered, encoding="utf-8")


def chapter_html(chapter: dict) -> str:
    source = chapter["path"] / "lecture.md"
    return lecture_markdown_to_html(source.read_text(encoding="utf-8"))


def build_chapter(chapter: dict) -> Path:
    out_dir = ROOT / "build" / "chapters" / chapter["track"] / chapter["slug"]
    html_path = out_dir / "lecture.html"
    pdf_path = out_dir / "lecture.pdf"
    wrap_html(chapter["title"], chapter_html(chapter), html_path)
    chrome_pdf(html_path, pdf_path)
    release = ROOT / "dist" / chapter["track"] / "chapters" / f'{chapter["number"]:02d}-{chapter["slug"]}.pdf'
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


def build_book(track: str, incomplete: bool = False) -> Path:
    manifest = load_manifest()
    common = list(iter_chapters(["common"]))
    chapters = common + list(iter_chapters([track]))
    title = f'RHEL 9 {track.upper()} 讲义'
    filename = book_filename(track, incomplete)
    out_dir = ROOT / "build" / "books" / track
    html_path = out_dir / f"{track}.html"
    pdf_path = out_dir / filename
    wrap_html(title, book_body(title, chapters), html_path)
    chrome_pdf(html_path, pdf_path)
    release = ROOT / "dist" / track / filename
    release.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(pdf_path, release)
    print(f"built {rel(release)} ({len(PdfReader(release).pages)} pages)")
    return release


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
