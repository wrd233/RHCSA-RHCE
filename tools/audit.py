from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path

import yaml

from common import ROOT, iter_chapters, load_manifest
from validate_anki import validate as validate_anki
from validate_lecture import ID_RE, validate as validate_lecture


FORBIDDEN_SUFFIXES = {".pdf", ".zip", ".apkg", ".pyc"}
FORBIDDEN_PARTS = {"build", "dist", "releases", "tmp", "__pycache__", "__MACOSX", "examples", "archive"}


def repository_errors() -> list[str]:
    import subprocess
    tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")
    errors = []
    for name in filter(None, tracked):
        path = Path(name)
        if path.suffix.lower() in FORBIDDEN_SUFFIXES or FORBIDDEN_PARTS & set(path.parts):
            errors.append(f"forbidden tracked path: {name}")
        full = ROOT / path
        if full.is_file() and full.stat().st_size > 20 * 1024 * 1024:
            errors.append(f"tracked file exceeds 20 MiB: {name}")
    return errors


def content_errors(track: str) -> list[str]:
    errors: list[str] = []
    ids: dict[str, list[str]] = defaultdict(list)
    sections: dict[str, list[str]] = defaultdict(list)
    for chapter in iter_chapters([track]):
        lecture = chapter["path"] / "lecture.md"
        anki = chapter["path"] / "anki.yml"
        lecture_errors, _ = validate_lecture(lecture)
        anki_errors, _, note_ids = validate_anki(anki)
        errors.extend(f"{chapter['id']} lecture: {item}" for item in lecture_errors)
        errors.extend(f"{chapter['id']} Anki: {item}" for item in anki_errors)
        for note_id in note_ids:
            ids[note_id].append(chapter["slug"])
        for left, right in ID_RE.findall(lecture.read_text(encoding="utf-8")):
            sections[left or right].append(chapter["slug"])
        data = yaml.safe_load(anki.read_text(encoding="utf-8")) or {}
        for note in data.get("notes") or []:
            actual = [tag for tag in note.get("tags", []) if str(tag).startswith("chapter::")]
            if actual != [f"chapter::{chapter['slug']}"]:
                errors.append(f"{note.get('id')}: chapter tag mismatch in {chapter['slug']}")
            if not isinstance(note.get("source"), list) or not all(isinstance(x, str) and x.strip() for x in note.get("source", [])):
                errors.append(f"{note.get('id')}: Source must be a non-empty string list")
    errors.extend(f"global duplicate Note ID {note_id}: {slugs}" for note_id, slugs in ids.items() if len(slugs) > 1)
    errors.extend(f"global duplicate Section ID {section_id}: {slugs}" for section_id, slugs in sections.items() if len(slugs) > 1)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("track", choices=["rhcsa", "rhce"], default="rhcsa", nargs="?")
    args = parser.parse_args()
    errors = repository_errors() + content_errors(args.track)
    print(f"V2 audit: {len(errors)} error(s)")
    for error in errors:
        print(f"ERROR {error}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
