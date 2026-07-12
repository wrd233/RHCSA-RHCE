from pathlib import Path
import sys

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from tools.audit import repository_errors
from tools.build import release_ready
from tools.build_apkg import package_filename
from tools.build_lecture import book_filename


ROOT = Path(__file__).resolve().parents[1]


def test_formal_release_requires_every_chapter_validated():
    manifest = yaml.safe_load((ROOT / "config/chapters.yml").read_text())
    assert release_ready("rhce", manifest) is False
    for chapter in manifest["rhcsa"]["chapters"]:
        chapter["status"] = "validated"
    assert release_ready("rhcsa", manifest) is True
    manifest["rhcsa"]["chapters"][0]["status"] = "pending"
    assert release_ready("rhcsa", manifest) is False


def test_repository_has_no_tracked_generated_or_large_files():
    assert repository_errors() == []


def test_migrations_reference_known_ids_and_chapters():
    manifest = yaml.safe_load((ROOT / "config/chapters.yml").read_text())
    migrations = yaml.safe_load((ROOT / "config/anki-migrations.yml").read_text())
    chapters = {chapter["slug"] for chapter in manifest["rhcsa"]["chapters"]}
    active_ids = set()
    for chapter in manifest["rhcsa"]["chapters"]:
        path = ROOT / chapter["path"] / "anki.yml"
        active_ids.update(note["id"] for note in yaml.safe_load(path.read_text())["notes"])
    assert all(item["chapter"] in chapters for item in migrations["canonical_ids"].values())
    assert all(note_id in active_ids for note_id in migrations["canonical_ids"])


def test_incomplete_artifacts_cannot_use_formal_names():
    assert book_filename("rhce", True) == "RHEL9-RHCE-V2-INCOMPLETE-PREVIEW.pdf"
    assert package_filename("rhce", True) == "RHEL9-RHCE-V2-INCOMPLETE-PREVIEW.apkg"
    assert "INCOMPLETE-PREVIEW" not in book_filename("rhcsa", False)
