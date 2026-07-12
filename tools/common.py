from __future__ import annotations

import hashlib
import html
import re
import shutil
import subprocess
import tempfile
import time
import unicodedata
from pathlib import Path
from typing import Iterable

import bleach
import markdown
import yaml
from pypdf import PdfReader, PdfWriter

ROOT = Path(__file__).resolve().parents[1]
CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")


def load_yaml(path: Path):
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_manifest() -> dict:
    return load_yaml(ROOT / "config" / "chapters.yml")


def iter_chapters(tracks: Iterable[str] = ("common", "rhcsa", "rhce")):
    manifest = load_manifest()
    for track in tracks:
        base = ROOT / "content" / track
        if track != "common":
            base = base / "chapters"
        for number, entry in enumerate(manifest[track]["chapters"], 1):
            item = dict(entry)
            item.update(track=track, number=number, path=base / entry["slug"])
            yield item


def strip_front_matter(text: str) -> tuple[dict, str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ValueError("front matter is not closed")
    meta = yaml.safe_load(text[4:end]) or {}
    return meta, text[end + 5 :]


def lecture_markdown_to_html(text: str) -> str:
    _, body = strip_front_matter(text)
    body = re.sub(r"<section(?![^>]*\bmarkdown=)", '<section markdown="1"', body)
    return markdown.markdown(
        body,
        extensions=["extra", "md_in_html", "sane_lists", "toc"],
        output_format="html5",
    )


ALLOWED_TAGS = {
    "p", "br", "strong", "em", "code", "pre", "ul", "ol", "li",
    "blockquote", "span", "div",
}


def safe_markdown_to_html(value: str | None) -> str:
    rendered = markdown.markdown(value or "", extensions=["fenced_code", "sane_lists"])
    return bleach.clean(rendered, tags=ALLOWED_TAGS, attributes={}, strip=True)


CLOZE_RE = re.compile(r"\{\{c(\d+)::(.*?)(?:::(.*?))?\}\}")


def cloze_front(text: str) -> str:
    return CLOZE_RE.sub(lambda match: f"[{html.escape(match.group(3) or '…')}]", text)


def cloze_back(text: str) -> str:
    return CLOZE_RE.sub(lambda match: match.group(2), text)


def stable_int(value: str) -> int:
    return int(hashlib.sha1(value.encode()).hexdigest()[:12], 16)


def chrome_pdf(html_path: Path, pdf_path: Path) -> None:
    if not CHROME.exists():
        raise RuntimeError(f"Chrome not found: {CHROME}")
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    if pdf_path.exists():
        pdf_path.unlink()
    profile = Path(tempfile.mkdtemp(prefix="chrome-pdf-", dir=ROOT / "build"))
    command = [
        str(CHROME),
        "--headless=new",
        "--disable-gpu",
        "--disable-background-networking",
        "--disable-component-update",
        "--disable-sync",
        "--no-first-run",
        "--no-default-browser-check",
        "--no-pdf-header-footer",
        "--run-all-compositor-stages-before-draw",
        f"--user-data-dir={profile}",
        f"--print-to-pdf={pdf_path.resolve()}",
        html_path.resolve().as_uri(),
    ]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    last_size = -1
    stable = 0
    try:
        for _ in range(120):
            if process.poll() is not None:
                break
            size = pdf_path.stat().st_size if pdf_path.exists() else 0
            if size > 0 and size == last_size:
                stable += 1
                if stable >= 4:
                    break
            else:
                stable = 0
                last_size = size
            time.sleep(0.25)
        if process.poll() is None:
            process.terminate()
        _, stderr = process.communicate(timeout=10)
    except Exception:
        process.kill()
        process.wait()
        raise
    finally:
        shutil.rmtree(profile, ignore_errors=True)
    if not pdf_path.exists() or pdf_path.stat().st_size == 0:
        raise RuntimeError(f"Chrome PDF failed: {stderr}")
    add_pdf_bookmarks(html_path, pdf_path)


def _plain(value: str) -> str:
    value = re.sub(r"<[^>]+>", "", value)
    value = html.unescape(value)
    value = unicodedata.normalize("NFKC", value)
    return re.sub(r"\s+", "", value)


def add_pdf_bookmarks(html_path: Path, pdf_path: Path) -> None:
    html_text = html_path.read_text(encoding="utf-8")
    headings = [(int(level), _plain(title), re.sub(r"<[^>]+>", "", html.unescape(title)).strip())
                for level, title in re.findall(r"<h([12])[^>]*>(.*?)</h\1>", html_text, re.S)]
    reader = PdfReader(pdf_path)
    page_text = [_plain(page.extract_text() or "") for page in reader.pages]
    located: list[tuple[int, str, int]] = []
    cursor = 0
    for level, needle, display in headings:
        found = None
        for index in range(cursor, len(page_text)):
            if needle and needle in page_text[index]:
                found = index
                break
        if found is None:
            for index, text_value in enumerate(page_text):
                if needle and needle in text_value:
                    found = index
                    break
        if found is not None:
            located.append((level, display, found))
            cursor = found
    writer = PdfWriter()
    writer.clone_document_from_reader(reader)
    parent = None
    for level, display, page_index in located:
        if level == 1:
            parent = writer.add_outline_item(display, page_index)
        else:
            writer.add_outline_item(display, page_index, parent=parent)
    temp = pdf_path.with_suffix(".bookmarked.pdf")
    with temp.open("wb") as handle:
        writer.write(handle)
    temp.replace(pdf_path)


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT.resolve()))
