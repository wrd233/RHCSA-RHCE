from __future__ import annotations

import hashlib
import re
import subprocess
import sys
from pathlib import Path

import yaml
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from common import iter_chapters, lecture_markdown_to_html

REFERENCE_SHA = "94613171491c8dc864850fc194d26c8d5a1e3803dab7b76078ffcd955b84f770"


def sources() -> str:
    text_suffixes = {".py", ".md", ".yml", ".yaml", ".json", ".css", ".html", ".toml", ".txt", ".csv"}
    paths = [p for p in ROOT.rglob("*") if p.is_file() and p.suffix in text_suffixes and ".git" not in p.parts and not any(x in p.parts for x in ("build", "tmp", "incoming", ".venv", "__pycache__"))]
    return "\n".join(p.read_text(encoding="utf-8", errors="ignore") for p in paths)


def test_no_wrong_reference_filename():
    forbidden = "Shell解析引用展开与命令组合-" + "大字号阅读版样章.pdf"
    assert forbidden not in sources()


def test_no_user_downloads_absolute_path():
    forbidden = "/Users/" + "example/Downloads/"
    assert forbidden.replace("example", "[^/]+") not in sources()
    assert not re.search(r"/Users/[^/]+/" + "Downloads/", sources())


def test_no_mechanical_concept_splitter():
    text = (ROOT / "tools/common.py").read_text()
    old_definition = "concept-" + "definition"
    old_understanding = "concept-" + "understanding"
    assert "re.split" not in text and old_definition not in text and old_understanding not in text


def test_no_renderer_injected_definition_understanding():
    rendered = lecture_markdown_to_html('<div class="concept-block"><span class="concept-label">概念</span><p><strong>对象</strong>作者原文。</p></div>')
    assert "定义：" not in rendered and "理解：" not in rendered


def test_no_plain_operation_quickref_fallback():
    rendered = lecture_markdown_to_html("**[操作语义]** `type` 查询。")
    assert "operation-quickref" not in rendered


def test_concept_preserves_authored_text():
    authored = "作者写好的完整解释，不拆句也不补写。"
    rendered = lecture_markdown_to_html(f'<div class="concept-block"><span class="concept-label">概念</span><p><strong>术语</strong>{authored}</p></div>')
    assert authored in rendered and 'class="concept-term"' in rendered


def test_operation_quickref_has_synopsis_and_vertical_options():
    html = lecture_markdown_to_html((ROOT / "content/rhcsa/chapters/shell-parsing-expansion/lecture.md").read_text())
    assert "operation-quickref" in html and "quickref-synopsis" in html and "option-list" in html
    assert html.index("<dt") < html.index("<dd")


def test_renderer_does_not_invent_parameters():
    source = '<div class="quick-reference"><div class="command-card">**SYNOPSIS**\n\n```bash\ntype name\n```\n\n作者说明。</div></div>'
    rendered = lecture_markdown_to_html(source)
    assert "-a" not in rendered and "type name" in rendered


def test_renderer_preserves_code_and_section_ids():
    for chapter in iter_chapters(["rhcsa"]):
        source = (chapter["path"] / "lecture.md").read_text()
        ids = re.findall(r'id="(RHCSA-[^"]+)"', source)
        rendered = lecture_markdown_to_html(source)
        assert all(f'id="{value}"' in rendered for value in ids)


def test_five_pilots_pass_visual_contract():
    for number in (1, 3, 12, 25, 32):
        path = next((ROOT / "releases/rhcsa-v5.1/chapters").glob(f"{number:02d}-*.pdf"))
        reader = PdfReader(path)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        assert "SYNOPSIS" in text and all((page.extract_text() or "").strip() for page in reader.pages)


def test_all_33_chapter_pdfs_and_no_blank_pages():
    paths = sorted((ROOT / "releases/rhcsa-v5.1/chapters").glob("*.pdf"))
    assert len(paths) == 33
    for path in paths:
        reader = PdfReader(path)
        assert all((page.extract_text() or "").strip() for page in reader.pages)


def test_no_visible_raw_html_or_headers_footers_page_numbers():
    for path in (ROOT / "releases/rhcsa-v5.1/chapters").glob("*.pdf"):
        texts = [page.extract_text() or "" for page in PdfReader(path).pages]
        assert not any(re.search(r"<(?:div|section)\b|class=\"", text) for text in texts)
        assert not any(re.fullmatch(r"\s*Page\s+\d+\s*", line) for text in texts for line in text.splitlines())


def test_fonts_are_subset():
    reader = PdfReader(next((ROOT / "releases/rhcsa-v5.1/chapters").glob("01-*.pdf")))
    names = []
    for page in reader.pages:
        fonts = (page.get("/Resources") or {}).get("/Font") or {}
        names += [str(ref.get_object().get("/BaseFont", "")) for ref in fonts.values()]
    assert any(re.search(r"/[A-Z]{6}\+", name) for name in names)


def test_task_solution_page_breaks():
    css = (ROOT / "styles/lecture-base.css").read_text()
    assert ".classic-task, .reference-solution { break-before: page; }" in css
    for chapter in iter_chapters(["rhcsa"]):
        rendered = lecture_markdown_to_html((chapter["path"] / "lecture.md").read_text())
        assert "classic-task" in rendered and "reference-solution" in rendered


def test_book_is_merge_and_page_count_equals_components():
    chapters = sorted((ROOT / "releases/rhcsa-v5.1/chapters").glob("*.pdf"))
    book = PdfReader(ROOT / "releases/rhcsa-v5.1/RHCSA-RHEL9-v5.1.pdf")
    total = sum(len(PdfReader(path).pages) for path in chapters)
    assert len(book.pages) == total + 3


def test_book_pages_match_single_pdfs():
    book = PdfReader(ROOT / "releases/rhcsa-v5.1/RHCSA-RHEL9-v5.1.pdf")
    offset = 3
    for path in sorted((ROOT / "releases/rhcsa-v5.1/chapters").glob("*.pdf")):
        single = PdfReader(path)
        for index, page in enumerate(single.pages):
            assert page.get_contents().get_data() == book.pages[offset + index].get_contents().get_data()
        offset += len(single.pages)


def test_finalizer_does_not_modify_canonical_and_preserves_disabled():
    paths = sorted((ROOT / "content/rhcsa/chapters").glob("*/anki.yml"))
    before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    subprocess.run(["uv", "run", "python", "tools/finalize_v51.py", "--skip-tests"], cwd=ROOT, check=True)
    assert before == {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def test_root_has_no_consumed_inputs():
    assert not list(ROOT.glob("RHCSA-*.zip"))
