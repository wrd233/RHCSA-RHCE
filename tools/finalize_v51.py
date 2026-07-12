#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import yaml

from build_apkg import build as build_apkg
from common import ROOT
from reading_release_qa import RELEASE, sha, write


def canonical_files() -> list[Path]:
    return sorted((ROOT / "content/rhcsa/chapters").glob("*/lecture.md")) + sorted((ROOT / "content/rhcsa/chapters").glob("*/anki.yml"))


def fingerprints() -> dict[str, str]:
    return {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in canonical_files()}


def run(command: list[str]) -> str:
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError("command failed: " + " ".join(command) + "\n" + result.stdout + result.stderr)
    return result.stdout + result.stderr


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate read-only canonical data and finalize RHCSA v5.1 release evidence.")
    parser.add_argument("--skip-tests", action="store_true")
    args = parser.parse_args()
    before = fingerprints()
    outputs = {}
    if not args.skip_tests:
        outputs["pytest"] = run(["uv", "run", "pytest", "-q"])
    outputs["lecture"] = run(["uv", "run", "python", "tools/validate_lecture.py"])
    outputs["anki"] = run(["uv", "run", "python", "tools/validate_anki.py"])
    outputs["audit"] = run(["uv", "run", "python", "tools/audit.py", "rhcsa"])
    built_apkg = build_apkg("rhcsa")
    formal_apkg = RELEASE / "anki/RHCSA-RHEL9-v5.1.apkg"
    formal_apkg.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(built_apkg, formal_apkg)
    run(["uv", "run", "python", "tools/reading_release_qa.py"])
    after = fingerprints()
    if before != after:
        raise RuntimeError("finalizer modified canonical lecture or Anki files")
    artifacts = {}
    for path in sorted(p for p in RELEASE.rglob("*") if p.is_file() and p.name not in {"MANIFEST.yml", "SHA256SUMS.txt"}):
        artifacts[str(path.relative_to(RELEASE))] = {"sha256": sha(path), "bytes": path.stat().st_size}
    manifest = {
        "release": "RHCSA-RHEL9-v5.1", "status": "RHCSA_V5_1_READING_RELEASED",
        "chapters": 33, "canonical_read_only": True, "anki_canonical": "UNCHANGED",
        "ankiconnect_apply": "NOT_REQUIRED", "artifacts": artifacts,
    }
    write(RELEASE / "MANIFEST.yml", yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False))
    paths = sorted(p for p in RELEASE.rglob("*") if p.is_file() and p.name != "SHA256SUMS.txt")
    write(RELEASE / "SHA256SUMS.txt", "\n".join(f"{sha(path)}  {path.relative_to(RELEASE)}" for path in paths))
    notes = """# RHCSA RHEL 9 v5.1 Reading Release

The formal book is merged from 33 accepted single-chapter PDFs. The renderer consumes explicit concept and operation-quickref markup, preserves authored text, and emits no running header, footer or page number. Canonical Anki YAML was unchanged; the APKG was rebuilt offline and no AnkiConnect apply was performed.
"""
    write(RELEASE / "RELEASE_NOTES.md", notes)
    evidence = {"canonical_before": before, "canonical_after": after, "canonical_unchanged": before == after, "commands": outputs}
    write(ROOT / "reports/finalizer-readonly-evidence.json", json.dumps(evidence, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
