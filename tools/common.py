from __future__ import annotations

import hashlib
import html
import os
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
CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    r"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    r"C:\\Program Files\\Chromium\\Application\\chrome.exe",
]


def find_chrome() -> Path | None:
    for key in ("CHROME_BIN", "CHROMIUM_BIN"):
        if os.environ.get(key) and Path(os.environ[key]).is_file():
            return Path(os.environ[key])
    for name in ("google-chrome", "chromium", "chromium-browser", "chrome"):
        found = shutil.which(name)
        if found:
            return Path(found)
    return next((Path(value) for value in CHROME_CANDIDATES if Path(value).is_file()), None)


def load_yaml(path: Path):
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_manifest() -> dict:
    return load_yaml(ROOT / "config" / "chapters.yml")


def iter_chapters(tracks: Iterable[str] = ("common", "rhcsa", "rhce")):
    manifest = load_manifest()
    for track in tracks:
        for fallback_number, entry in enumerate(manifest[track]["chapters"], 1):
            if entry.get("status") == "pending" or not entry.get("enabled", True):
                continue
            item = dict(entry)
            configured_path = entry.get("path")
            if configured_path:
                chapter_path = ROOT / configured_path
            else:
                base = ROOT / "content" / track
                if track != "common":
                    base = base / "chapters"
                chapter_path = base / entry["slug"]
            item.update(
                track=track,
                number=entry.get("number", fallback_number),
                path=chapter_path,
            )
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
    rendered = markdown.markdown(
        body,
        extensions=["extra", "md_in_html", "sane_lists", "toc"],
        output_format="html5",
    )
    # Canonical Markdown remains the source; deterministic semantic wrappers
    # expose its authored labels to reading CSS without inventing content.
    def concept(match: re.Match) -> str:
        term = match.group(1).strip()
        content = f'{term}是{match.group(2).strip()}。'
        sentences = re.split(r'(?<=。)', content, maxsplit=1)
        definition = sentences[0]
        understanding = sentences[1].strip() if len(sentences) > 1 else ""
        extra = f'<div class="concept-understanding"><strong>理解：</strong>{understanding}</div>' if understanding else ""
        return ('<div class="concept-block"><div class="concept-heading">'
                '<span class="semantic-badge">概念</span>'
                f'<strong class="concept-term">{term}</strong></div>'
                f'<div class="concept-definition"><strong>定义：</strong>{definition}</div>{extra}</div>')
    rendered = re.sub(
        r'<p><strong>\[概念\]</strong>\s*(.*?)(?:是|指|属于)(.*?)(?:。</p>)',
        concept,
        rendered, flags=re.S)
    rendered = re.sub(
        r'<p><strong>\[操作语义\]</strong>\s*(.*?)</p>',
        r'<div class="operation-block"><div class="operation-heading"><span class="semantic-badge">操作语义</span></div><div class="operation-semantics">\1</div></div>',
        rendered, flags=re.S)
    rendered = re.sub(r'<h2>\[(知识|操作|诊断)专题\]\s*', r'<h2><span class="semantic-badge">\1专题</span> ', rendered)
    rendered = re.sub(r'<h3>([①-⑳])\s*\[(知识点|操作|诊断点)\]\s*', r'<h3><span class="point-index">\1</span><span class="semantic-badge subtle">\2</span> ', rendered)
    rendered = rendered.replace('<p><strong>[Cheatsheet]</strong></p>', '<div class="cheatsheet-label">Cheatsheet</div>')
    return rendered


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
    chrome = find_chrome()
    if not chrome:
        raise RuntimeError("Chrome/Chromium not found; set CHROME_BIN or CHROMIUM_BIN")
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    if pdf_path.exists():
        pdf_path.unlink()
    profile = Path(tempfile.mkdtemp(prefix="chrome-pdf-", dir=ROOT / "build"))
    command = [
        str(chrome),
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
        try:
            _, stderr = process.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
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
