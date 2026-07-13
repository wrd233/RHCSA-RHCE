# RHCSA v5.1 Finalization Report

**RHCSA_V5_1_FINALIZATION_BLOCKED**

## Published v5.1

- Tag/commit: `v5.1` / `ed86710eb395729cd6673a8afcd8297dfdb0bec6`.
- Release: https://github.com/wrd233/RHCSA-RHCE/releases/tag/v5.1
- GitHub API verified a non-draft, non-prerelease Release with 38 assets: 33 chapter PDFs, one 1093-page book, one APKG, `MANIFEST.yml`, `SHA256SUMS.txt`, and `RELEASE_NOTES.md`.
- Server-provided SHA-256 digests match the published Manifest for the book, APKG, and all 33 chapter PDFs.

## Blocking findings

- The Release is missing the required Anki HTML preview and Anki summary assets; 40 assets were required, 38 are published.
- Manual PDF sampling of RHCSA-01 found an isolated cover-kicker page and an isolated chapter-opening label page. The cause is the global `h1` page break combined with unstyled explicit reading components.
- The local correction preserves canonical content and removes these blank/isolated pages. Its verified candidate contains 33 PDFs, 1043 chapter pages, and a 1046-page book (`1043 + 3`); it is not a published Release.
- A `v5.1.1` Release is required. The GitHub Release creation API returned HTTP 401 (`Requires authentication`), so no tag, Release, or published asset was changed.

## Quality evidence

- Candidate QA: 41 pytest tests passed; lecture and Anki validation reported 0 errors; RHCSA audit reported 0 errors; PDF QA reported 0 errors.
- Candidate AnkiConnect readback: 3363 notes, 3711 cards, no duplicate stable IDs, and formal templates hide `Source`. The RHCSA canonical subset remains 33 chapters; the readback includes the common chapter namespace.
- Canonical lecture Markdown and Anki YAML were not edited. No RHEL 9 command-level live test was performed.

## Main status

`main` remains at `961a29b3af4c07a828078a5de90c221a036546df`. No feature-branch push, main merge, PR, tag movement, or Release replacement was performed because Gate A/B failed.

## Retained evidence

Retained machine evidence includes `PROJECT_STATUS.yml`, Anki ID and section ID indexes, Anki global QA/readback, reading chapter and visual-regression reports, reference selection/hash evidence, and finalizer readonly evidence. The local candidate verification files are temporary and are not committed.
