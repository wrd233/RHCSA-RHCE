# PDF Redesign and Anki Sync Report

## Final status

`CLOSED_VERIFIED`

## PDF

Reference: `/Users/wangrundong/Downloads/RHCSA-01-Shell解析引用展开与命令组合-大字号阅读版样章.pdf` (34 pages, A4). The formal implementation uses A4, 20 mm margins, 10.2 pt body at 1.64 line height, 8.5 pt code, and 8.5 pt tables. It intentionally removes all visible headers, footers, page numbers, build/commit/status IDs and Source metadata.

Implemented `lecture-base.css`, `lecture-reading.css`, and `lecture-reading.html`; added a default `reading` profile, cross-platform Chrome discovery, 9-part builds, doctor, PDF QA, semantic concept/operation transforms, clickable chapter TOC and PDF outlines. Concepts are full-width single-column blocks; terms use `.concept-term`; authored first sentence is Definition and authored remainder is Understanding. No technical explanation is generated. Operations use semantic blocks; source-authored parameter structures remain authoritative.

Pilots RHCSA-01, 12, 25 and 32 passed rendered contact-sheet review. Full output: 33 technical chapters, 1 common chapter, 9 parts, and one 540-page full book. The 43 RHCSA PDFs contain 2,121 pages total; full book size is 17,638,189 bytes. Structural QA: 0 failures; all are A4, unencrypted, searchable, bookmarked and free of injected maintenance markers. Thirty-three seven-page contact sheets were generated under the ignored review directory. SHA256 sums are in the ignored distribution directory.

Known limitation: concepts with only one authored sentence have no fabricated Understanding paragraph; validation reports such authoring gaps rather than inventing content. Existing lecture validation emits non-blocking warnings for operation topics lacking an explicit verification marker, with 0 errors.

## Anki

Endpoint `http://127.0.0.1:8765`, API version 6. Canonical repository validation: 3,360 active Notes across all common/RHCSA sources; RHCSA exam filtering matches the APKG at 3,353 Notes and 3,700 Cards. APKG SQLite audit found 0 duplicate GUIDs.

Preflight found no existing `RedHat-QA`, `RedHat-Cloze`, or project Notes. Backup snapshot: `/Users/wangrundong/work/redhat/backups/anki/RHCSA-before-sync-20260712-182053.notes.json`. Dry-run made no AnkiConnect calls. Apply created compatible models/decks and added 3,353 Notes in batches: added 3,353; updated 0; unchanged 0; stale 0; disabled 0; failed 0. Since all project Notes were new, no prior review progress existed to preserve; future updates use `updateNoteFields`, never delete/recreate.

Readback: 3,353 Notes / 3,700 Cards; QA 3,083, Cloze 270; 34 chapter tags; 0 duplicate stable IDs; correct fields including Source; formal templates hide Source. Twenty Notes were read back across 10 chapters, including QA and Cloze content, fields and tags. Errors: 0.

## Engineering

- `pytest`: passed (16 tests)
- lecture validation: 34 files, 0 errors
- Anki validation: 34 files, 3,360 Notes, 0 errors
- repository audit: 0 errors
- New long-term tools: doctor, PDF QA, safe scoped/batched Anki sync, Anki readback
- Documentation: README, lecture spec, PDF reading spec, build/release guide, AnkiConnect guide
- Generated PDFs/APKG/contact sheets/backups remain ignored and are not committed
- Remote push: no
