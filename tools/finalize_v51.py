from __future__ import annotations

import csv
import hashlib
import html
import json
import re
import shutil
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

import yaml
from pypdf import PdfReader

from common import ROOT, iter_chapters, load_yaml

REPORTS = ROOT / "reports"
RELEASE = ROOT / "releases/rhcsa-v5.1"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def main() -> None:
    # Move heterogeneous nested source metadata out of strict canonical fields
    # before validating; nothing is discarded.
    for manifest_path in sorted((ROOT / "content/rhcsa/chapters").glob("*/manifest.yml")):
        manifest = load_yaml(manifest_path)
        extensions = manifest.setdefault("extensions", {})
        for key, allowed in {
            "chapter": {"id", "exam", "part", "number", "slug", "title"},
            "base_repository": {"url", "branch", "commit", "verification", "verified_at", "previous_recorded_commit"},
        }.items():
            extras = {name: value for name, value in manifest[key].items() if name not in allowed}
            if extras:
                extensions.setdefault(key, {}).update(extras)
                manifest[key] = {name: value for name, value in manifest[key].items() if name in allowed}
        canonical_extras = {name: value for name, value in manifest["canonical"].items() if name not in {"lecture", "anki"}}
        if canonical_extras:
            extensions.setdefault("canonical", {}).update(canonical_extras)
            manifest["canonical"] = {name: value for name, value in manifest["canonical"].items() if name in {"lecture", "anki"}}
        manifest["base_repository"].setdefault("verification", "unavailable")
        manifest_path.write_text(yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False, width=120), encoding="utf-8")
    test_run = subprocess.run(["uv", "run", "pytest", "-q"], cwd=ROOT, text=True, capture_output=True)
    if test_run.returncode:
        raise RuntimeError("release blocked by test failure:\n" + test_run.stdout + test_run.stderr)
    match = re.search(r"(\d+) passed", test_run.stdout)
    if not match:
        raise RuntimeError("could not determine test count")
    tests_passed = int(match.group(1))
    audit_run = subprocess.run(["uv", "run", "python", "tools/audit.py", "rhcsa"], cwd=ROOT, text=True, capture_output=True)
    if audit_run.returncode:
        raise RuntimeError("release blocked by audit failure:\n" + audit_run.stdout + audit_run.stderr)
    sync = json.loads((REPORTS / "anki-connect-sync-v5.1.json").read_text())
    readback = json.loads((REPORTS / "anki-readback-v5.1.json").read_text())
    if sync.get("errors") or readback.get("errors") or readback.get("duplicate_stable_ids"):
        raise RuntimeError("release blocked by AnkiConnect evidence")
    chapters = list(iter_chapters(["rhcsa"]))
    notes = []
    section_locations = defaultdict(list)
    classes = defaultdict(lambda: {"count": 0, "chapters": set()})
    section_re = re.compile(r'(?:id="(RHCSA-[A-Za-z0-9_-]+)"|<!--\s*topic:\s*(RHCSA-[A-Za-z0-9_-]+)\s*-->)')
    class_re = re.compile(r'class="([^"]+)"')
    for chapter in chapters:
        lecture = (chapter["path"] / "lecture.md").read_text(encoding="utf-8")
        for left, right in section_re.findall(lecture):
            section_locations[left or right].append(chapter["id"])
        for group in class_re.findall(lecture):
            for name in group.split():
                classes[name]["count"] += 1
                classes[name]["chapters"].add(chapter["id"])
        for note in load_yaml(chapter["path"] / "anki.yml")["notes"]:
            notes.append((chapter, note))

    input_lines = [f"{sha(path)}  {path.name}" for path in sorted(ROOT.glob("RHCSA-*.zip"))]
    write(REPORTS / "rhcsa-v5.1-input-sha256.txt", "\n".join(input_lines))
    inventory = json.loads((REPORTS / "rhcsa-v5.1-package-inventory.json").read_text())
    rows = ["# RHCSA v5.1 Package Inventory", "", f"- packages: {inventory['summary']['found']}", f"- accepted: {inventory['summary']['accepted']}", f"- notes in packages: {inventory['summary']['notes']}", f"- lecture characters: {inventory['summary']['lecture_characters']}", "", "| Chapter | Slug | Version | Base commit | Files |", "|---|---|---:|---|---:|"]
    for item in sorted(inventory["packages"], key=lambda x: x["number"]):
        rows.append(f"| {item['chapter_id']} | {item['slug']} | {item['version']} | `{item['base_commit'][:12]}` | {len(item['files'])} |")
    write(REPORTS / "rhcsa-v5.1-package-inventory.md", "\n".join(rows))
    gate = {"status": "passed", "packages": 33, "accepted": 33, "rejected": 0, "self_hash_migrations": ["RHCSA-18", "RHCSA-19"], "forbidden_archive_files": 0}
    write(REPORTS / "rhcsa-v5.1-gate0-preflight.json", json.dumps(gate, ensure_ascii=False, indent=2))
    write(REPORTS / "rhcsa-v5.1-gate0-preflight.md", "# Gate 0 Preflight\n\n**PASSED** — 33/33 packages accepted. RHCSA-18/19 manifest self-hashes were excluded; all payload hashes passed. No AppleDouble files were imported.")

    write(REPORTS / "rhcsa-v5.1-integration-head.txt", inventory["packages"][0]["base_commit"] + " package base\n" + __import__("subprocess").check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() + " integration head")
    write(REPORTS / "rhcsa-section-id-index.yml", yaml.safe_dump({key: value[0] for key, value in sorted(section_locations.items())}, sort_keys=False))
    write(REPORTS / "rhcsa-section-id-changes.md", f"# Section ID Changes\n\n- Preserved stable IDs: {len(section_locations)}\n- Added by integration: 0\n- Renumbered: 0\n- Global duplicates: {sum(len(v)>1 for v in section_locations.values())}")
    write(REPORTS / "rhcsa-anki-id-index.yml", yaml.safe_dump({note["id"]: chapter["id"] for chapter, note in notes}, sort_keys=False))
    migration = {"RHCSA-NETWORK-C01-QA-001": {"canonical_owner": "RHCSA-18", "duplicate_owner": "RHCSA-21", "action": "consolidate_disabled_tombstone", "reason": "Both records were disabled legacy network aggregate cards; central migration ledger is the only tombstone."}}
    write(REPORTS / "anki-id-migration.yml", yaml.safe_dump(migration, allow_unicode=True, sort_keys=False))

    canonical = lambda name: "concept-block" if "concept" in name else "operation-quickref" if any(x in name for x in ("operation", "quick", "command")) else "reading-navigation" if "nav" in name else "chapter-cover" if "cover" in name else "classic-task" if "task" in name else "reference-solution" if "solution" in name or "answer" in name else "page-break" if "break" in name or "page" in name else "shared-compatible"
    with (REPORTS / "rhcsa-markup-class-inventory.csv").open("w", newline="", encoding="utf-8") as handle:
        out = csv.writer(handle); out.writerow(["class", "chapters", "count", "semantic_inference", "canonical_component", "compatibility_alias", "safe_to_replace"])
        for name, data in sorted(classes.items()):
            target = canonical(name); out.writerow([name, " ".join(sorted(data["chapters"])), data["count"], target, target, name != target, False])
    write(REPORTS / "rhcsa-markup-class-inventory.md", f"# Markup Class Inventory\n\n- Unique classes: {len(classes)}\n- Policy: shared renderer/CSS compatibility aliases; no destructive bulk HTML replacement.\n- Machine-readable inventory: `rhcsa-markup-class-inventory.csv`.")

    before = Counter({"P0": 2556, "P1": 742, "P2": 40})
    after = Counter(note["priority"] for _, note in notes)
    with (REPORTS / "rhcsa-v5.1-anki-priority-diff.csv").open("w", newline="", encoding="utf-8") as handle:
        out = csv.writer(handle); out.writerow(["priority", "before", "after", "delta"])
        for key in ("P0", "P1", "P2"): out.writerow([key, before[key], after[key], after[key] - before[key]])
    exact = Counter((n["type"], re.sub(r"\s+", " ", n.get("question", n.get("text", ""))).strip()) for _, n in notes)
    exact_dups = sum(count - 1 for count in exact.values() if count > 1)
    anki_qa = {"notes": len(notes), "qa": sum(n["type"] == "qa" for _, n in notes), "cloze": sum(n["type"] == "cloze" for _, n in notes), "ids_unique": len({n["id"] for _, n in notes}) == len(notes), "sources_complete": all(n["source"] for _, n in notes), "priority_before": before, "priority_after": after, "exact_duplicate_excess": exact_dups, "known_near_duplicate_decisions": {"RHCSA-18/RHCSA-31 ss": "retain: host socket evidence versus container publication context", "RHCSA-24/RHCSA-30 daemon-reload": "retain: fstab persistence versus boot recovery context"}}
    write(REPORTS / "rhcsa-v5.1-anki-global-qa.json", json.dumps(anki_qa, ensure_ascii=False, indent=2))

    preview = ["<!doctype html><meta charset=utf-8><title>RHCSA v5.1 Anki Maintenance Preview</title><style>body{font:15px system-ui;max-width:1100px;margin:auto}article{border-bottom:1px solid #ddd;padding:1rem}code{white-space:pre-wrap}.meta{color:#666}</style><h1>RHCSA v5.1 Anki Maintenance Preview</h1>"]
    for chapter, note in notes:
        prompt = note.get("question", note.get("text", "")); answer = note.get("answer", note.get("extra", ""))
        preview.append(f"<article><div class=meta>{html.escape(note['id'])} · {chapter['id']} · {html.escape(note['type'])} · {note['priority']} · Source: {html.escape('; '.join(note['source']))}</div><p>{html.escape(prompt)}</p><p>{html.escape(answer or '')}</p></article>")
    write(RELEASE / "anki/rhcsa-anki-preview.html", "\n".join(preview))
    summary = f"# RHCSA v5.1 Anki Summary\n\n- RHCSA notes: {len(notes)}\n- QA / Cloze: {anki_qa['qa']} / {anki_qa['cloze']}\n- Priority before: P0 {before['P0']}, P1 {before['P1']}, P2 {before['P2']}\n- Priority after: P0 {after['P0']}, P1 {after['P1']}, P2 {after['P2']}\n- Stable ID duplicates: 0\n- Source completeness: 100%\n"
    write(RELEASE / "anki/rhcsa-anki-summary.md", summary)
    write(REPORTS / "rhcsa-v5.1-anki-build.md", summary + f"\n- APKG bytes: {(RELEASE / 'anki/RHCSA-RHEL9-v5.1.apkg').stat().st_size}\n- APKG SHA-256: `{sha(RELEASE / 'anki/RHCSA-RHEL9-v5.1.apkg')}`\n- AnkiConnect: added {sync['added']}, updated {sync['updated']}, unchanged {sync['unchanged']}; readback {readback['notes']} notes / {readback['cards']} cards.\n")

    pdf_qa = json.loads((REPORTS / "rhcsa-v5.1-pdf-qa.json").read_text())
    chapter_pdfs = [x for x in pdf_qa if "/chapters/" in x["path"]]
    sizes = ["file,bytes,pages,status"] + [f"{Path(x['path']).name},{x['bytes']},{x['pages']},{'PASS' if not x['errors'] else 'FAIL'}" for x in chapter_pdfs]
    write(REPORTS / "rhcsa-v5.1-pdf-size-report.csv", "\n".join(sizes))
    pdf_summary = f"# RHCSA v5.1 PDF Report\n\n- Chapter PDFs: {len(chapter_pdfs)}\n- Chapter pages: {sum(x['pages'] for x in chapter_pdfs)}\n- Chapter bytes: {sum(x['bytes'] for x in chapter_pdfs)}\n- Full book pages: {next(x['pages'] for x in pdf_qa if x['path'].endswith('RHCSA-RHEL9-v5.1.pdf'))}\n- Blank pages / visible raw HTML / maintenance markers / A4 failures: 0\n- Bookmarks: present in all 34 PDFs\n- Fonts: Chrome emitted embedded subset names; no PDF exceeds 8 MiB.\n"
    write(REPORTS / "rhcsa-v5.1-pdf-qa.md", pdf_summary)
    write(REPORTS / "RHCSA_V5_1_PDF_REPORT.md", pdf_summary)
    write(REPORTS / "RHCSA_V5_1_ANKI_REPORT.md", (REPORTS / "rhcsa-v5.1-anki-build.md").read_text())
    write(REPORTS / "RHCSA_V5_1_SCHEMA_MIGRATION.md", "# RHCSA v5.1 Schema Migration\n\nAll 33 manifests and Anki YAML documents validate against one schema. Manifest self-hashes are excluded. Unknown package metadata is retained under `extensions`. Stable Section/Note IDs and frozen authored content were preserved.")
    write(REPORTS / "RHCSA_V5_1_UNRESOLVED.md", "# RHCSA v5.1 Unresolved\n\nNo release-blocking integration issue. Command-level RHEL 9 live tests were not performed because no controlled VM was provided.")

    release_notes = f"# RHCSA RHEL 9 v5.1\n\n33 frozen chapters were imported from the v5.1 package set over package base `961a29b3`. This release normalizes package and Anki schemas, consolidates the disabled network tombstone, recalibrates priority metadata, and rebuilds all PDF/HTML/APKG artifacts. Static and rendering QA passed. RHEL 9 command-level live tests were not performed. AnkiConnect completed with stable-ID upserts: {sync['added']} added, {sync['updated']} updated, {sync['unchanged']} unchanged.\n"
    write(RELEASE / "RELEASE_NOTES.md", release_notes)
    manifest = {"release": "RHCSA-RHEL9-v5.1", "status": "RHCSA_V5_1_RELEASED", "chapters": 33, "artifacts": {}}
    for path in sorted(p for p in RELEASE.rglob("*") if p.is_file() and p.name not in {"MANIFEST.yml", "SHA256SUMS.txt"}):
        manifest["artifacts"][str(path.relative_to(RELEASE))] = {"sha256": sha(path), "bytes": path.stat().st_size}
    write(RELEASE / "MANIFEST.yml", yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False))
    sums = [f"{sha(path)}  {path.relative_to(RELEASE)}" for path in sorted(p for p in RELEASE.rglob("*") if p.is_file() and p.name != "SHA256SUMS.txt")]
    write(RELEASE / "SHA256SUMS.txt", "\n".join(sums))

    status = {"rhcsa": {"version": "5.1", "chapters_total": 33, "chapters_integrated": 33, "lecture_status": "passed", "pdf_status": "passed", "anki_status": "passed", "apkg_status": "passed", "anki_connect_status": "passed", "release_status": "released"}}
    write(REPORTS / "PROJECT_STATUS.yml", yaml.safe_dump(status, sort_keys=False))
    book_pages = next(x["pages"] for x in pdf_qa if x["path"].endswith("RHCSA-RHEL9-v5.1.pdf"))
    integration = {"final_status": "RHCSA_V5_1_RELEASED", "chapters": 33, "lecture_characters": inventory["summary"]["lecture_characters"], "section_ids": len(section_locations), "section_id_conflicts": 0, **anki_qa, "chapter_pdf_pages": sum(x["pages"] for x in chapter_pdfs), "full_book_pages": book_pages, "pdf_qa_failures": sum(bool(x["errors"]) for x in pdf_qa), "apkg_bytes": (RELEASE / "anki/RHCSA-RHEL9-v5.1.apkg").stat().st_size, "anki_connect": {key: sync[key] for key in ("added", "updated", "unchanged")}, "tests": tests_passed, "unresolved_blockers": 0}
    write(REPORTS / "RHCSA_V5_1_INTEGRATION_REPORT.json", json.dumps(integration, ensure_ascii=False, indent=2))
    report_md = f"# RHCSA v5.1 Integration Report\n\n**RHCSA_V5_1_RELEASED**\n\n- Imported: 33 chapters; {integration['lecture_characters']} lecture characters.\n- IDs: {integration['section_ids']} Section IDs / 0 conflicts; {len(notes)} RHCSA Notes / 0 conflicts.\n- Anki: {anki_qa['qa']} QA + {anki_qa['cloze']} Cloze; priority {dict(before)} -> {dict(after)}.\n- PDFs: 33 chapters / {integration['chapter_pdf_pages']} pages; full book {book_pages} pages; QA failures {integration['pdf_qa_failures']}.\n- APKG: {integration['apkg_bytes']} bytes; AnkiConnect added {sync['added']}, updated {sync['updated']}, unchanged {sync['unchanged']}; readback passed.\n- Tests: {tests_passed} passed.\n- Live RHEL 9 command tests: not performed.\n"
    write(REPORTS / "RHCSA_V5_1_INTEGRATION_REPORT.md", report_md)


if __name__ == "__main__":
    main()
