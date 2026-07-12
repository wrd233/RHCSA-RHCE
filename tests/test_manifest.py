from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def manifest():
    return yaml.safe_load((ROOT / "config" / "chapters.yml").read_text(encoding="utf-8"))


def test_v2_chapter_counts_and_required_fields():
    data = manifest()
    assert len(data["rhcsa"]["chapters"]) == 33
    assert len(data["rhce"]["chapters"]) == 25
    required = {"exam", "part", "number", "slug", "title", "path", "status"}
    for track in ("common", "rhcsa", "rhce"):
        for chapter in data[track]["chapters"]:
            assert required <= chapter.keys()


def test_slugs_numbers_and_paths_are_unique_and_ordered():
    for track, section in manifest().items():
        if "chapters" not in section:
            continue
        chapters = section["chapters"]
        assert len({c["slug"] for c in chapters}) == len(chapters)
        assert len({c["path"] for c in chapters}) == len(chapters)
        numbers = [c["number"] for c in chapters]
        assert numbers == sorted(numbers)
        for chapter in chapters:
            assert chapter["status"] in {"pending", "integrated", "validated", "released"}
            if chapter["status"] != "pending":
                assert (ROOT / chapter["path"] / "lecture.md").is_file()
                assert (ROOT / chapter["path"] / "anki.yml").is_file()


def test_old_wide_slugs_are_not_active():
    old = {"shell-help", "files-text-archive", "users-permissions", "processes-services-logs", "architecture-inventory", "yaml-playbook-modules", "loops-conditionals-handlers"}
    active = {c["slug"] for track in ("rhcsa", "rhce") for c in manifest()[track]["chapters"]}
    assert not old & active
