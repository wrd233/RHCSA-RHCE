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
from bs4 import BeautifulSoup
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
    # Normalize only the repository's explicit fenced-component syntax.
    fenced = []
    fence_depth = 0
    for line in body.splitlines():
        opening = re.fullmatch(r"\s*:{3,}\s*\{([^}]+)\}\s*", line)
        if opening:
            attrs = opening.group(1)
            classes = re.findall(r"\.([A-Za-z0-9_-]+)", attrs)
            identity = re.search(r"#([A-Za-z0-9_-]+)", attrs)
            extras = re.findall(r'([A-Za-z0-9_-]+)="([^"]*)"', attrs)
            attr_text = (f' id="{identity.group(1)}"' if identity else "")
            attr_text += (f' class="{" ".join(classes)}"' if classes else "")
            attr_text += "".join(f' {key}="{value}"' for key, value in extras)
            fenced.append(f'<div markdown="1"{attr_text}>')
            fence_depth += 1
        elif fence_depth and re.fullmatch(r"\s*:{3,}\s*", line):
            fenced.append("</div>")
            fence_depth -= 1
        else:
            fenced.append(line)
    body = "\n".join(fenced)
    body = body.replace(' markdown="block"', ' data-explicit-html="1"')
    body = re.sub(r"<section(?![^>]*\bmarkdown=)", '<section markdown="1"', body)
    entry_classes = (
        "command-card|command-entry|quick-command|quickref-item|quickref-card|"
        "cmd-group|cmd-entry|op-entry|semantic-item|op-spec"
    )
    body = re.sub(
        rf'<div(?![^>]*(?:\bmarkdown=|data-explicit-html=))(?=[^>]*class="[^"]*(?:{entry_classes})\b)',
        '<div markdown="1"', body,
    )
    quickref_classes = (
        "quick-reference|quickref-zone|quickref-section|quickref|ops-quick|"
        "operation-quick|operation-atlas|semantic-zone|quick-zone"
    )
    body = re.sub(
        rf'<div(?![^>]*\bmarkdown=)(?=[^>]*class="[^"]*(?:{quickref_classes})\b)',
        '<div markdown="1"', body,
    )
    rendered = markdown.markdown(
        body,
        extensions=["extra", "md_in_html", "sane_lists", "toc"],
        output_format="html5",
    )
    # The renderer may normalize only explicit authored markup. It must never
    # infer semantic structure from prose, split sentences, or invent options.
    aliases = {
        "cover-page": "chapter-cover", "cover": "chapter-cover",
        "navigation-page": "reading-navigation", "reading-nav": "reading-navigation",
        "nav-page": "reading-navigation", "navigation": "reading-navigation",
        "concept-card": "concept-block", "concept-box": "concept-block",
        "quick-reference": "operation-quickref", "semantic-quick-reference": "operation-quickref",
        "semantic-quick": "operation-quickref", "quickref-zone": "operation-quickref",
        "quickref-section": "operation-quickref", "quickref": "operation-quickref",
        "quick-reference": "operation-quickref", "ops-quick": "operation-quickref",
        "operation-quick": "operation-quickref", "operation-atlas": "operation-quickref",
        "semantic-zone": "operation-quickref", "quick-zone": "operation-quickref",
        "semantic-command": "quickref-command", "command-group": "quickref-command",
        "command-card": "quickref-command", "command-entry": "quickref-command",
        "quick-command": "quickref-command", "quickref-item": "quickref-command",
        "quickref-card": "quickref-command", "cmd-group": "quickref-command",
        "cmd-entry": "quickref-command", "op-entry": "quickref-command",
        "semantic-item": "quickref-command", "op-spec": "quickref-command",
        "task": "classic-task", "task-page": "classic-task",
        "answer": "reference-solution", "solution-page": "reference-solution",
        "reference-answer": "reference-solution", "summary": "chapter-closing",
        "closing": "chapter-closing", "closure": "chapter-closing",
        "pagebreak": "page-break", "force-new-page": "page-break",
    }

    def add_aliases(match: re.Match) -> str:
        tokens = match.group(1).split()
        for token in list(tokens):
            alias = aliases.get(token)
            if alias and alias not in tokens:
                tokens.append(alias)
        return f'class="{" ".join(tokens)}"'

    rendered = re.sub(r'class="([^"]+)"', add_aliases, rendered)
    # Structural normalization below is anchored to explicit component classes,
    # not words in the author's prose.
    rendered = re.sub(
        r'(<(?:div|section) class="[^"]*\bconcept-block\b[^"]*"[^>]*>)\s*'
        r'<span class="[^"]*(?:concept-label|concept-badge|concept-pill|concept-tag|concept-chip)[^"]*">概念</span>\s*'
        r'<p><strong>(.*?)</strong>(.*?)</p>',
        r'\1<div class="concept-heading"><span class="semantic-badge">概念</span>'
        r'<strong class="concept-term">\2</strong></div><div class="concept-explanation">\3</div>',
        rendered, flags=re.S,
    )
    rendered = re.sub(
        r'<div class="([^"]*(?:synopsis-label|synopsis-title|syn-label)[^"]*)">\s*SYNOPSIS\s*</div>\s*(<pre>.*?</pre>)',
        r'<div class="quickref-synopsis"><span>SYNOPSIS</span>\2</div>',
        rendered, flags=re.S,
    )
    rendered = re.sub(
        r'<p><strong>SYNOPSIS</strong></p>\s*(<pre>.*?</pre>)',
        r'<div class="quickref-synopsis"><span>SYNOPSIS</span>\1</div>',
        rendered, flags=re.S,
    )
    rendered = rendered.replace("<dl>", '<dl class="option-list">')
    rendered = re.sub(r'<h2>\[(知识|操作|诊断)专题\]\s*', r'<h2><span class="semantic-badge">\1专题</span> ', rendered)
    rendered = re.sub(r'<h3>([①-⑳])\s*\[(知识点|操作|诊断点)\]\s*', r'<h3><span class="point-index">\1</span><span class="semantic-badge subtle">\2</span> ', rendered)
    rendered = rendered.replace('<p><strong>[Cheatsheet]</strong></p>', '<div class="cheatsheet-label">Cheatsheet</div>')
    soup = BeautifulSoup(rendered, "html.parser")
    # Repair explicit nested HTML that Python-Markdown escaped while processing
    # an authored markdown-in-HTML component. Only markup-shaped code blocks are
    # eligible; ordinary command examples remain untouched.
    for code in list(soup.select("pre > code")):
        value = html.unescape(code.get_text())
        if re.search(r"<(?:div|pre|p|dl|h[1-4])(?:\s|>)", value) and re.search(r"</(?:div|pre|p|dl|h[1-4])>", value):
            fragment = BeautifulSoup(value, "html.parser")
            pre = code.parent
            for child in list(fragment.contents):
                pre.insert_before(child.extract())
            pre.decompose()
    for node in list(soup.find_all(string=lambda value: value and re.search(r"<(?:h[1-4]|div|pre|p|dl)(?:\s|>)", value))):
        value = html.unescape(str(node))
        if not re.search(r"</(?:h[1-4]|div|pre|p|dl)>", value):
            continue
        fragment = BeautifulSoup(value, "html.parser")
        for child in list(fragment.contents):
            node.insert_before(child.extract())
        node.extract()
    for tag in soup.find_all(class_=True):
        tokens = tag.get("class", [])
        for token in list(tokens):
            alias = aliases.get(token)
            if alias and alias not in tokens:
                tokens.append(alias)
        tag["class"] = tokens
    kind_aliases = {
        "knowledge-topic": "knowledge-topic", "operation-topic": "operation-topic",
        "diagnosis-topic": "diagnosis-topic", "classic-task": "classic-task",
        "reference-answer": "reference-solution", "reference-solution": "reference-solution",
        "answer-topic": "reference-solution", "chapter-summary": "chapter-closing",
        "closing": "chapter-closing",
    }
    for tag in soup.find_all(attrs={"data-kind": True}):
        alias = kind_aliases.get(tag.get("data-kind"))
        if alias:
            tag["class"] = list(dict.fromkeys([*tag.get("class", []), alias]))
    for heading in soup.find_all(["h1", "h2", "h3"]):
        label = heading.get_text(" ", strip=True)
        alias = "classic-task" if label.startswith("[经典任务]") else "reference-solution" if label.startswith(("[参考解答]", "[参考答案]")) else None
        if alias:
            heading["class"] = list(dict.fromkeys([*heading.get("class", []), alias]))
    for tag in list(soup.find_all(["p", "div", "span"])):
        if re.match(r"^Source\s*:", tag.get_text(" ", strip=True), re.I):
            tag.decompose()
    concept_markers = {"concept-label", "concept-badge", "concept-pill", "concept-tag", "concept-chip"}
    for marker in soup.find_all(["span", "div"]):
        classes = set(marker.get("class", []))
        if marker.get_text(strip=True) != "概念" or not classes.intersection(concept_markers):
            continue
        container = marker.parent
        if container.name not in {"p", "div", "section"}:
            continue
        container["class"] = list(dict.fromkeys([*container.get("class", []), "concept-block"]))
        term = container.find("strong") or marker.find_next("strong")
        if term:
            term["class"] = list(dict.fromkeys([*term.get("class", []), "concept-term"]))
            explanation = term.parent
            explanation["class"] = list(dict.fromkeys([*explanation.get("class", []), "concept-explanation"]))
        marker["class"] = list(dict.fromkeys([*marker.get("class", []), "semantic-badge"]))
    for container in soup.find_all(["div", "section"], class_=lambda value: value and "concept" in " ".join(value if isinstance(value, list) else [value]).split()):
        marker = container.find(["span", "div"], string=lambda value: value and value.strip() == "概念")
        term = container.find("strong")
        if marker and term:
            container["class"] = list(dict.fromkeys([*container.get("class", []), "concept-block"]))
            term["class"] = list(dict.fromkeys([*term.get("class", []), "concept-term"]))
            term.parent["class"] = list(dict.fromkeys([*term.parent.get("class", []), "concept-explanation"]))
    for container in soup.find_all(class_="concept-block"):
        term = container.find("strong")
        if term:
            term["class"] = list(dict.fromkeys([*term.get("class", []), "concept-term"]))
            term.parent["class"] = list(dict.fromkeys([*term.parent.get("class", []), "concept-explanation"]))
    synopsis_nodes = list(soup.find_all(string=lambda value: value and value.strip() == "SYNOPSIS"))
    for node in synopsis_nodes:
        marker = node.parent
        existing = marker.find_parent(class_="quickref-synopsis")
        command = ((existing.find_parent("div") if existing else None)
                   or marker.find_parent(class_="quickref-command") or marker.find_parent("div"))
        if not command:
            continue
        command["class"] = list(dict.fromkeys([*command.get("class", []), "quickref-command"]))
        pre = marker.find_next("pre")
        if pre and not existing:
            wrapper = soup.new_tag("div")
            wrapper["class"] = ["quickref-synopsis"]
            marker.insert_before(wrapper)
            wrapper.append(marker.extract())
            wrapper.append(pre.extract())
        dl = command.find("dl")
        if dl:
            dl["class"] = list(dict.fromkeys([*dl.get("class", []), "option-list"]))
    for node in soup.find_all(["dl", "div"]):
        classes = set(node.get("class", []))
        if node.name == "dl" or classes.intersection({"param-list", "params", "forms", "definition-list"}):
            node["class"] = list(dict.fromkeys([*node.get("class", []), "option-list"]))
    # Some frozen chapters use sibling command cards without an outer wrapper.
    # Group only explicit, consecutive quickref-command siblings.
    for parent in soup.find_all(["div", "section", "body"]):
        children = [child for child in parent.children if getattr(child, "name", None)]
        run = []
        for child in children + [None]:
            if child is not None and "quickref-command" in child.get("class", []):
                run.append(child)
                continue
            if run:
                wrapper = soup.new_tag("section")
                wrapper["class"] = ["operation-quickref"]
                run[0].insert_before(wrapper)
                for item in run:
                    wrapper.append(item.extract())
                run = []
    return str(soup)


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
