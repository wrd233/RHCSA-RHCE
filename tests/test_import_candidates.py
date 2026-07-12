from __future__ import annotations

import hashlib
import sys
import zipfile
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.import_candidates import run


def candidate_zip(tmp_path: Path) -> Path:
    chapter = tmp_path / "candidate"
    chapter.mkdir()
    lecture = b"---\nstatus: candidate_complete\n---\n# Test\n"
    anki = yaml.safe_dump({"notes": []}).encode()
    (chapter / "lecture.md").write_bytes(lecture)
    (chapter / "anki.yml").write_bytes(anki)
    (chapter / ".DS_Store").write_text("noise")
    manifest = {
        "chapter": {"id": "RHCSA-01", "exam": "RHCSA", "number": 1, "slug": "test", "title": "Test"},
        "package": {"version": "1.0"},
        "files": {
            "lecture": {"path": "lecture.md", "sha256": hashlib.sha256(lecture).hexdigest()},
            "anki": {"path": "anki.yml", "sha256": hashlib.sha256(anki).hexdigest()},
        },
        "validation": {"live_test": "not_performed"},
    }
    (chapter / "manifest.yml").write_text(yaml.safe_dump(manifest))
    archive = tmp_path / "candidate.zip"
    with zipfile.ZipFile(archive, "w") as handle:
        for path in chapter.iterdir():
            handle.write(path, f"candidate/{path.name}")
    return archive


def test_dry_run_audits_without_writing_content(tmp_path: Path):
    archive = candidate_zip(tmp_path)
    root = tmp_path / "repo"
    result = run(archive, root=root)
    assert result["summary"] == {"found": 1, "accepted": 1, "rejected": 0, "notes": 0, "active": 0, "disabled": 0, "lecture_characters": 42, "pdf_pages": 0}
    assert not (root / "content").exists()


def test_apply_requires_confirmation_and_filters_macos_metadata(tmp_path: Path):
    archive = candidate_zip(tmp_path)
    root = tmp_path / "repo"
    try:
        run(archive, root=root, apply=True)
    except ValueError as exc:
        assert "--yes" in str(exc)
    else:
        raise AssertionError("apply without --yes must fail")
    run(archive, root=root, apply=True, yes=True)
    assert (root / "content/rhcsa/chapters/test/lecture.md").is_file()
    assert not list((root / ".build").rglob(".DS_Store"))


def test_hash_mismatch_is_rejected(tmp_path: Path):
    archive = candidate_zip(tmp_path)
    rewritten = tmp_path / "tampered.zip"
    with zipfile.ZipFile(archive) as source, zipfile.ZipFile(rewritten, "w") as target:
        for info in source.infolist():
            target.writestr(info, b"tampered" if info.filename == "candidate/lecture.md" else source.read(info))
    result = run(rewritten, root=tmp_path / "repo")
    assert result["summary"]["rejected"] == 1
    assert "hash mismatch" in " ".join(result["packages"][0]["errors"])


def test_manifest_self_hash_is_excluded(tmp_path: Path):
    archive = candidate_zip(tmp_path)
    rewritten = tmp_path / "self-hash.zip"
    with zipfile.ZipFile(archive) as source, zipfile.ZipFile(rewritten, "w") as target:
        for info in source.infolist():
            if info.filename != "candidate/manifest.yml":
                target.writestr(info, source.read(info))
                continue
            manifest = yaml.safe_load(source.read(info))
            manifest["files"]["manifest"] = {"path": "manifest.yml", "sha256": "0" * 64}
            target.writestr(info, yaml.safe_dump(manifest))
    result = run(rewritten, root=tmp_path / "repo")
    assert result["summary"]["accepted"] == 1
