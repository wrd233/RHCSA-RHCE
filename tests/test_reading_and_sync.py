from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from build_apkg import QA_MODEL, CLOZE_MODEL
from common import lecture_markdown_to_html
import sync_anki

ROOT=Path(__file__).resolve().parents[1]
def test_reading_contract_and_no_page_counter():
    css=(ROOT/"styles/lecture-reading.css").read_text()
    base=(ROOT/"styles/lecture-base.css").read_text()
    assert "concept-block" in css and "concept-term" in css
    assert "grid-template-columns" not in css
    assert "counter(page)" not in css+base
    assert "break-before: page" in base
def test_semantic_concept_and_operation_markup():
    html=lecture_markdown_to_html("**[概念]** 词是单位。用于形成参数。\n\n**[操作语义]** `type` 查看名称。")
    assert 'class="concept-term"' in html and 'class="concept-understanding"' in html
    assert 'class="operation-block"' in html
def test_formal_anki_templates_keep_but_hide_source():
    for model in (QA_MODEL,CLOZE_MODEL):
        assert any(f["name"]=="Source" for f in model.fields)
        assert "{{Source}}" not in model.templates[0]["afmt"]
    assert all("{{Source}}" not in t["Back"] for m in sync_anki.MODELS.values() for t in m["templates"])
def test_disabled_sync_is_non_mutating(monkeypatch):
    calls=[]
    monkeypatch.setattr(sync_anki,"invoke",lambda action,**kw: calls.append(action) or ([1] if action=="findNotes" else None))
    assert sync_anki.sync_note({"id":"X","type":"qa","disabled":True},"D","E")=="disabled-skipped"
    assert calls==["findNotes"]
