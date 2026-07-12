from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_sync_requires_explicit_apply_and_yes():
    source = (ROOT / "tools" / "sync_anki.py").read_text(encoding="utf-8")
    assert '"--apply"' in source
    assert '"--yes"' in source
    assert "args.apply" in source and "args.yes" in source


def test_generated_and_cache_directories_are_ignored():
    ignored = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "build/" in ignored
    assert "tmp/" in ignored
    assert "__pycache__/" in ignored
