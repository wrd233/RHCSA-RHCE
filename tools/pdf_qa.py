#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
from pypdf import PdfReader

FORBIDDEN = ("candidate_complete", "validation mode", "Chapter ID", "commit:", "slug:", "stable ID:")
def inspect(path: Path) -> dict:
    reader = PdfReader(path)
    texts = [(p.extract_text() or "") for p in reader.pages]
    sizes = {(round(float(p.mediabox.width),1), round(float(p.mediabox.height),1)) for p in reader.pages}
    errors=[]
    if reader.is_encrypted: errors.append("encrypted")
    if sizes != {(595.0, 841.9)}: errors.append(f"page-size-drift:{sizes}")
    if not any(t.strip() for t in texts): errors.append("no-searchable-text")
    if any(not t.strip() for t in texts): errors.append("blank-page")
    for marker in FORBIDDEN:
        if any(marker.lower() in t.lower() for t in texts): errors.append(f"visible-marker:{marker}")
    if not reader.outline: errors.append("missing-bookmarks")
    return {"path":str(path),"pages":len(reader.pages),"bytes":path.stat().st_size,"errors":errors}
def main() -> int:
    p=argparse.ArgumentParser(); p.add_argument("root",type=Path); p.add_argument("--json",type=Path); a=p.parse_args()
    results=[inspect(x) for x in sorted(a.root.rglob("*.pdf"))]
    if a.json: a.json.write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding="utf-8")
    failed=[r for r in results if r["errors"]]
    print(f"PDF QA: {len(results)} files, {sum(r['pages'] for r in results)} pages, {len(failed)} failed")
    for r in failed: print(r)
    return bool(failed)
if __name__ == "__main__": raise SystemExit(main())
