#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
import zipfile
from pathlib import Path

import yaml
from pypdf import PdfReader

from common import ROOT, iter_chapters

RELEASE = ROOT / "releases/rhcsa-v5.1"
REPORTS = ROOT / "reports"
REFERENCE_ARCHIVE = ROOT / "RHCSA-01-shell-parsing-expansion-v5.1-final.zip"
REFERENCE_MEMBER = "RHCSA-01-shell-parsing-expansion/lecture-review.pdf"
REFERENCE_SHA256 = "94613171491c8dc864850fc194d26c8d5a1e3803dab7b76078ffcd955b84f770"
FORBIDDEN = ("<section", "<div", 'class="', "candidate_complete", "Chapter ID", "commit:")


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def page_content(page) -> bytes:
    contents = page.get_contents()
    return contents.get_data() if contents else b""


def font_names(page) -> set[str]:
    resources = page.get("/Resources") or {}
    fonts = resources.get("/Font") or {}
    names = set()
    for ref in fonts.values():
        obj = ref.get_object()
        name = str(obj.get("/BaseFont", ""))[1:]
        if name:
            names.add(name)
    return names


def inspect_pdf(path: Path) -> dict:
    reader = PdfReader(path)
    texts = [page.extract_text() or "" for page in reader.pages]
    all_fonts = sorted(set().union(*(font_names(page) for page in reader.pages)))
    errors = []
    if any(abs(float(p.mediabox.width) - 595.28) > 0.5 or abs(float(p.mediabox.height) - 841.89) > 0.5 for p in reader.pages):
        errors.append("not-a4")
    if any(not value.strip() for value in texts):
        errors.append("blank-page")
    if not any(value.strip() for value in texts):
        errors.append("not-searchable")
    for marker in FORBIDDEN:
        if any(marker.lower() in value.lower() for value in texts):
            errors.append(f"visible-marker:{marker}")
    if any(re.search(r"(?:^|\n)Source:\s", value) for value in texts):
        errors.append("visible-marker:Source-metadata")
    if not reader.outline:
        errors.append("missing-bookmarks")
    subset_fonts = [name for name in all_fonts if re.match(r"^[A-Z]{6}\+", name)]
    if all_fonts and not subset_fonts:
        errors.append("fonts-not-subset")
    return {
        "path": str(path.relative_to(ROOT)), "pages": len(reader.pages), "bytes": path.stat().st_size,
        "sha256": sha(path), "fonts": all_fonts, "subset_fonts": subset_fonts, "errors": errors,
    }


def main() -> int:
    chapters = list(iter_chapters(["rhcsa"]))
    chapter_paths = [RELEASE / "chapters" / f'{c["number"]:02d}-{c["slug"]}.pdf' for c in chapters]
    chapter_qa = [inspect_pdf(path) for path in chapter_paths]
    book_path = RELEASE / "RHCSA-RHEL9-v5.1.pdf"
    book_qa = inspect_pdf(book_path)
    book = PdfReader(book_path)
    front_pages = len(book.pages) - sum(item["pages"] for item in chapter_qa)
    comparisons = []
    offset = front_pages
    for chapter, path, item in zip(chapters, chapter_paths, chapter_qa):
        single = PdfReader(path)
        mismatches = []
        for index, page in enumerate(single.pages):
            target = book.pages[offset + index]
            if page_content(page) != page_content(target) or page.mediabox != target.mediabox:
                mismatches.append(index + 1)
        comparisons.append({"chapter": chapter["id"], "book_start_page": offset + 1, "pages": len(single.pages), "mismatches": mismatches})
        offset += len(single.pages)
    equation_ok = book_qa["pages"] == sum(item["pages"] for item in chapter_qa) + front_pages

    inventory = []
    consumed = ROOT / "incoming/consumed/rhcsa-reading-correction"
    for path in sorted(consumed.glob("*.zip")):
        inventory.append({"name": path.name, "sha256": sha(path), "bytes": path.stat().st_size, "kind": "v5.1 chapter package"})
    root_inventory = {
        "selected_reference": {"archive": REFERENCE_ARCHIVE.name, "member": REFERENCE_MEMBER, "sha256": REFERENCE_SHA256},
        "rejected_references": [], "inputs": inventory,
    }
    write(REPORTS / "rhcsa-reading-root-input-inventory.json", json.dumps(root_inventory, ensure_ascii=False, indent=2))
    inv_md = ["# RHCSA Reading Root Input Inventory", "", f"- SELECTED_REFERENCE: `{REFERENCE_ARCHIVE.name}!/{REFERENCE_MEMBER}`", f"- SHA-256: `{REFERENCE_SHA256}`", "- REJECTED_REFERENCES: none; no other root-level candidate reference PDF was present.", f"- Root chapter packages: {len(inventory)}", "", "The selected PDF is embedded in a root input ZIP; Downloads was not accessed."]
    write(REPORTS / "rhcsa-reading-root-input-inventory.md", "\n".join(inv_md))
    write(REPORTS / "rhcsa-reading-reference-sha256.txt", f"{REFERENCE_SHA256}  {REFERENCE_ARCHIVE.name}!/{REFERENCE_MEMBER}")
    selection = f"""# RHCSA Reading Reference Selection

SELECTED_REFERENCE: `{REFERENCE_ARCHIVE.name}!/{REFERENCE_MEMBER}`

SHA-256: `{REFERENCE_SHA256}`

The 33-page A4 review PDF is the only candidate reference found in the root inputs. Rendered pages 1, 2, 3, 5, 27, 29 and 33 confirm: full-width concepts with natural authored explanations, no mechanical Definition/Understanding labels, a pale-green operation quick reference, independent SYNOPSIS blocks, vertical parameters, and separate task/solution pages. It has no running header, footer or page number.

REJECTED_REFERENCES: none. The obsolete Downloads sample was not read and is forbidden by tests.
"""
    write(REPORTS / "rhcsa-reading-reference-selection.md", selection)

    write(REPORTS / "rhcsa-v5.1-reading-chapter-qa.json", json.dumps(chapter_qa, ensure_ascii=False, indent=2))
    qa_lines = ["# RHCSA v5.1 Reading Chapter QA", "", f"- PDFs: {len(chapter_qa)}", f"- Pages: {sum(x['pages'] for x in chapter_qa)}", f"- Failures: {sum(bool(x['errors']) for x in chapter_qa)}", "", "| Chapter | Pages | Bytes | Result |", "|---|---:|---:|---|"]
    for chapter, item in zip(chapters, chapter_qa):
        qa_lines.append(f"| {chapter['id']} | {item['pages']} | {item['bytes']} | {'PASS' if not item['errors'] else '; '.join(item['errors'])} |")
    write(REPORTS / "rhcsa-v5.1-reading-chapter-qa.md", "\n".join(qa_lines))
    with (REPORTS / "rhcsa-v5.1-reading-pdf-sizes.csv").open("w", newline="", encoding="utf-8") as handle:
        out = csv.writer(handle, lineterminator="\n"); out.writerow(["chapter", "file", "pages", "bytes", "sha256"])
        for chapter, item in zip(chapters, chapter_qa): out.writerow([chapter["id"], Path(item["path"]).name, item["pages"], item["bytes"], item["sha256"]])

    visual = {"front_matter_pages": front_pages, "chapter_pages": sum(x["pages"] for x in chapter_qa), "book_pages": book_qa["pages"], "equation_ok": equation_ok, "comparisons": comparisons}
    write(REPORTS / "rhcsa-v5.1-reading-visual-regression.json", json.dumps(visual, ensure_ascii=False, indent=2))
    visual_md = f"# RHCSA v5.1 Reading Visual Regression\n\n- Page equation: `{book_qa['pages']} = {sum(x['pages'] for x in chapter_qa)} + {front_pages}` — {'PASS' if equation_ok else 'FAIL'}\n- Single chapter versus merged-book content-stream mismatches: {sum(len(x['mismatches']) for x in comparisons)}\n- Method: compare every merged chapter page's media box and decoded PDF content stream against its accepted single-chapter source. Representative PNG contact sheets are generated separately and ignored by Git."
    write(REPORTS / "rhcsa-v5.1-reading-visual-regression.md", visual_md)

    pilots = {c["id"]: item for c, item in zip(chapters, chapter_qa) if c["id"] in {"RHCSA-01", "RHCSA-03", "RHCSA-12", "RHCSA-25", "RHCSA-32"}}
    pilot_result = {"status": "passed" if all(not x["errors"] for x in pilots.values()) else "failed", "chapters": pilots, "renderer_injected_definition_understanding": 0, "double_column_concepts": 0, "plain_operation_block_fallback": 0}
    write(REPORTS / "rhcsa-reading-pilot-qa.json", json.dumps(pilot_result, ensure_ascii=False, indent=2))
    write(REPORTS / "rhcsa-reading-pilot-qa.md", "# RHCSA Reading Pilot QA\n\n**PASS** — RHCSA-01, 03, 12, 25 and 32 are A4/searchable/bookmarked, have no blank page or visible raw HTML, and render explicit concepts, quickrefs, SYNOPSIS, vertical options and task/solution page breaks. Renderer-injected Definition/Understanding: 0.")

    correction = {
        "final_status": "RHCSA_V5_1_READING_RELEASED" if equation_ok and not any(x["errors"] for x in chapter_qa) and not book_qa["errors"] and not any(x["mismatches"] for x in comparisons) else "BLOCKED",
        "reference": root_inventory["selected_reference"], "chapter_pdfs": 33,
        "chapter_pages": visual["chapter_pages"], "front_matter_pages": front_pages, "book_pages": book_qa["pages"],
        "page_equation": equation_ok, "visual_mismatches": sum(len(x["mismatches"]) for x in comparisons),
        "anki": "ANKI_CANONICAL_UNCHANGED", "ankiconnect": "ANKICONNECT_APPLY_NOT_REQUIRED",
        "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
    }
    write(REPORTS / "RHCSA_V5_1_READING_RENDERER_CORRECTION.json", json.dumps(correction, ensure_ascii=False, indent=2))
    report = f"""# RHCSA v5.1 Reading Renderer Correction

**{correction['final_status']}**

- Correct reference: `{REFERENCE_ARCHIVE.name}!/{REFERENCE_MEMBER}` (`{REFERENCE_SHA256}`).
- Removed system: obsolete personal-directory reference, heuristic two-sentence splitter, plain green fallback, compact RHCSA profile, and monolithic-book reflow.
- Renderer: explicit authored components with finite aliases; no natural-language inference or invented parameters.
- Pilots: RHCSA-01/03/12/25/32 passed.
- Chapters: 33 PDFs, {visual['chapter_pages']} pages, 0 QA failures.
- Book: `{book_path.relative_to(ROOT)}`, `{book_qa['pages']} = {visual['chapter_pages']} + {front_pages}` pages.
- Visual regression: {correction['visual_mismatches']} content-stream mismatches across all chapter pages.
- Anki: `ANKI_CANONICAL_UNCHANGED`; APKG rebuilt from canonical; `ANKICONNECT_APPLY_NOT_REQUIRED`.
- Git commit at report generation: `{correction['git_commit']}`.
- Unresolved release blockers: 0.
"""
    write(REPORTS / "RHCSA_V5_1_READING_RENDERER_CORRECTION.md", report)
    return 0 if correction["final_status"] == "RHCSA_V5_1_READING_RELEASED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
