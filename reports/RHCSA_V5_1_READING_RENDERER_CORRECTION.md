# RHCSA v5.1 Reading Renderer Correction

**RHCSA_V5_1_READING_RELEASED**

- Correct reference: `RHCSA-01-shell-parsing-expansion-v5.1-final.zip!/RHCSA-01-shell-parsing-expansion/lecture-review.pdf` (`610162e211a9a9e61fcfb404b8ed80f0511117362fed04be6f1107fe7fd1fc29`).
- Removed system: obsolete personal-directory reference, heuristic two-sentence splitter, plain green fallback, compact RHCSA profile, and monolithic-book reflow.
- Renderer: explicit authored components with finite aliases; no natural-language inference or invented parameters.
- Pilots: RHCSA-01/03/12/25/32 passed.
- Chapters: 33 PDFs, 1090 pages, 0 QA failures.
- Book: `releases/rhcsa-v5.1/RHCSA-RHEL9-v5.1.pdf`, `1093 = 1090 + 3` pages.
- Visual regression: 0 content-stream mismatches across all chapter pages.
- PDF QA: A4/searchable/bookmarked; blank pages, visible raw HTML, maintenance markers and non-subset fonts are all 0. Component counts and per-chapter pages/bytes/hashes are in the adjacent JSON/CSV reports.
- Anki: `ANKI_CANONICAL_UNCHANGED`; APKG rebuilt from canonical (2220250 bytes, `cf4041662acb32fc9ffc6bd97eb333e25fb9a8e6cd884f34e5cc739f635e14da`); existing AnkiConnect readback has 3363 notes / 3711 cards and no duplicate stable IDs; dry-run only, `ANKICONNECT_APPLY_NOT_REQUIRED`.
- Tests: `40 passed`; lecture/Anki/audit gates have 0 errors.
- Git commit at report generation: `d489368d70ee19fda2bf3b77a685cc4e1c42774e`.
- Git diff removes tracked binary releases and obsolete compact/report files; generated binaries remain local-only and are published as GitHub Release assets.
- Unresolved release blockers: 0.
