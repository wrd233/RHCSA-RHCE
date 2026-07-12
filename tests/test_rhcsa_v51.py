from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]
CHAPTERS = yaml.safe_load((ROOT / "config/chapters.yml").read_text(encoding="utf-8"))["rhcsa"]["chapters"]


def chapter_files(name: str) -> list[Path]:
    return [ROOT / item["path"] / name for item in CHAPTERS]


def test_all_33_packages_present():
    assert len(CHAPTERS) == 33
    assert all(path.is_file() for path in chapter_files("lecture.md") + chapter_files("anki.yml") + chapter_files("manifest.yml"))


def test_manifest_schema_all_chapters_and_no_self_hash():
    schema = json.loads((ROOT / "schemas/chapter-package-v5.1.schema.json").read_text())
    for path in chapter_files("manifest.yml"):
        value = yaml.safe_load(path.read_text())
        jsonschema.validate(value, schema)
        assert all(entry["path"] != "manifest.yml" for entry in value["files"].values())
        for entry in value["files"].values():
            assert re.fullmatch(r"[0-9a-f]{64}", entry["sha256"])


def test_anki_schema_ids_sources_cloze_and_chapter_tags():
    schema = json.loads((ROOT / "schemas/anki-chapter.schema.json").read_text())
    ids = []
    for chapter, path in zip(CHAPTERS, chapter_files("anki.yml")):
        value = yaml.safe_load(path.read_text())
        jsonschema.validate(value, schema)
        for note in value["notes"]:
            ids.append(note["id"])
            assert note["source"]
            assert f"chapter::{chapter['slug']}" in note["tags"]
            assert f"priority::{note['priority']}" in note["tags"]
            if note["type"] == "cloze":
                assert re.search(r"\{\{c\d+::.+?\}\}", note["text"])
    assert not [key for key, count in Counter(ids).items() if count > 1]
    assert "RHCSA-NETWORK-C01-QA-001" not in ids


def test_section_ids_unique_globally():
    ids = []
    pattern = re.compile(r'(?:id="((?:RHCSA)-[A-Za-z0-9_-]+)"|<!--\s*topic:\s*((?:RHCSA)-[A-Za-z0-9_-]+)\s*-->)')
    for path in chapter_files("lecture.md"):
        ids.extend(left or right for left, right in pattern.findall(path.read_text()))
    assert len(ids) >= 500
    assert not [key for key, count in Counter(ids).items() if count > 1]


def test_no_forbidden_archive_files():
    tracked = [Path(line) for line in __import__("subprocess").check_output(["git", "ls-files"], cwd=ROOT, text=True).splitlines()]
    assert not [path for path in tracked if "__MACOSX" in path.parts or path.name.startswith("._")]
