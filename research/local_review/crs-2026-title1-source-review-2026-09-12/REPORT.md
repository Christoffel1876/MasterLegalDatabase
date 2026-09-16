---
title: Distinct 2026 CRS Title 1 PDF — first three sections, source-only review
status: scoped_source_qa_pending_atlas_acceptance
source_id: crs-2026-title1-official-pdf
prepared_on: 2026-09-12
selected_sections: [CRS-1-1-101, CRS-1-1-102, CRS-1-1-103]
legal_currentness: not_verified
answer_safe: false
prior_2025_original_custody: unresolved
---

# Acquisition and exact boundary

The explicitly linked **2026 Title 1 PDF** was acquired successfully as a distinct
new representation. The source is `events/E001/body.bin`, exactly 3,967,221 bytes,
SHA256 `1c6b021e612929ca8024bebf1022ba45f57aa99712d080c404da8f7f7e90cd1d`.
Its PDF page tree contains **1,008 physical pages**. That is a structural count,
not a claim of reviewing the complete title.

One deliberate GET to `https://olls.info/crs/crs2026-title-01.pdf` returned HTTP 200
with ordinary TLS verification, `application/pdf`, no redirect, no retry and no
cookie/authentication headers. Actual local UTC request bracket:
`2026-09-12T22:13:16.539063+00:00` to `2026-09-12T22:13:17.603959+00:00`.
The source passed PDF magic/EOF checks and opens without repair or encryption.
It is not a browser print, OCR derivative or reconstructed document.

The request was based on the preserved official OLLS 2026 download page, whose
Title 1 row explicitly links this PDF. `REFERRAL_PROOF.json` binds that exact HTML,
its earlier HTTP receipt, and copied prior-gap evidence. Its publication statement
describes changes from the 2026 Second Regular Session. No new request for that
already frozen page was made. No HTML/DOCX title representation was acquired.

The response-header derivative is byte-identical here because there were zero
cookie/auth header lines. The receipt nevertheless labels its general derivative
contract explicitly and records the observed original header hash. No cookie value
or credential is included. No forms, official contacts or accounts were used.

# Direct review scope and native order

**Six complete pages, physical 1–6**, were viewed at 144 dpi using Poppler. The
review was candidate-aware: the native text and inherited three-record metadata
were already available. It is not an independent blind transcription claim.

Uncorrected PyMuPDF 1.28.2 extraction (`flags=195`, `sort=False`) for those six
pages is preserved as six UTF-8 files totaling **11,298 bytes**. The source QA
classifies all those bytes into **31 nonoverlapping regions**, including footers,
contents/context and an explicitly out-of-scope tail. Region text is byte-exact;
no spelling, punctuation, whitespace or OCR correction was applied.

Native text from page 7 was briefly read to locate the selection boundary before
the review was scoped. No page 7 visual review or later-page inspection is claimed.
The PDF's remaining pages are retained original custody, not reviewed coverage.

| Physical page | Inspected content and boundaries |
| --- | --- |
| 1 | Title 1/Elections, title-level editor note and cross references, beginning of article contents. The 2026 edition appears in the footer. |
| 2 | Continued article contents and category headings; context only. |
| 3 | Article 1/Part 1 contents in two columns. Entries such as 1-1-101 here are catalog occurrences, not the substantive section start. |
| 4 | Upper two-column contents, then a distinct substantive Part 1 heading; all of 1-1-101 and the beginning of 1-1-102(1). |
| 5 | Continuation of 1-1-102(1), all of (2), its source/editor/cross-reference notes; all three 1-1-103 paragraphs and its source note. |
| 6 | 1-1-103 editor note and complete two-column case annotation. Section 1-1-104 begins afterward and is explicitly outside the selected review. |

The three-line footer is emitted **first** in each native page but appears last
visually. It is separated from statutory paragraphs in the QA. Contents columns
read left then right, and the page 6 case annotation likewise continues from the
left column to the right; alternating rows would scramble its sentence.

# First three section selections

The review preserves **six substantive paragraphs in seven native fragments**:
one unnumbered paragraph for 101, two paragraphs for 102, and three for 103.
It also preserves each heading and source note, all three editor notes, the 102
cross-reference block, and the complete 103 annotation heading/body.

- **1-1-101:** heading, unnumbered body, historical source note and editor note
  are all on physical 4. Quotation marks and the semicolon in the short-title
  paragraph are preserved; the ancillary notes remain separate from the body.
- **1-1-102:** paragraph (1) crosses physical 4 to 5. The top two lines of page 5
  continue that paragraph; they are not a new paragraph. Paragraph (2) follows.
  The cross-reference block associates general election, primary election and
  congressional vacancy election with the printed `(17)`, `(32)` and `(5)`
  references in that order. Referenced provisions were not opened or resolved.
- **1-1-103:** all three numbered paragraphs are on physical 5. The source note
  follows, and the editor note plus annotation continue on physical 6 before 104.
  The annotation's bold first sentence ends at “candidate petitions.” The remaining
  normal-weight text and *Griswold v. Ferrigno Warren* citation are case commentary,
  not an additional statutory paragraph or an independently checked case holding.

No fee/data table, numbered footnote, strikeout, handwritten amendment, signature
or filled form field was observed within these selected substantive regions.
Contents listings and the two-column annotation retain their actual roles. The
visible font/style observations do not certify Unicode encodings; exact codepoints
are preserved from native bytes. No statutory applicability or meaning is inferred.

# Cross-edition comparison, not original recovery

`SOURCE_QA.json` retains each exact inherited body/history string, its metadata-line
hash, every new source fragment, literal line diffs and a declared word/punctuation
token comparison. Literal strings differ in wrapping, whitespace and paragraph-label
spacing; history-note layout also differs. The mechanical token comparison reports
no word/punctuation edit operations for these three **body and history strings only**.
That narrow algorithmic result is not section/edition equivalence, legal currentness,
or authentication of the missing SGML/zip.

The new PDF also contains ancillary material absent from the selected inherited
`full_text` and `history_note` fields: editor notes for the three sections, the 102
cross references and the 103 annotation. That may reflect omissions in the earlier
derivation. It is **not evidence that those passages were added in 2026**. The old
original bytes are missing, so that question remains unresolved. No old record was
corrected or overwritten.

The source's printed 2026 edition and publisher catalog statement are kept separate
from its PDF creation/modification metadata (August 18, 2026), actual September 12
acquisition time, and historical source-note dates. No 2026 legal effective date is
assigned. The complete title and later amendments have not been reconciled.

# Artifacts and offline verification

- `SOURCE_QA.json` and `.schema.json`: strict source/section/page/region/comparison records.
- `native/page-0001.txt` through `page-0006.txt`: uncorrected complete native pages.
- `pages/page-0001.png` through `page-0006.png`: complete Poppler page renders.
- `SELECTED_PASSAGES.md`: readable view of the exact selected regions and roles.
- `events/E001.json`, body, metadata and header derivative: actual acquisition custody.
- `reference/`: exact copied referral and prior-gap evidence; historical references
  inside those frozen records remain original context and are not silently rewritten.
- `FINAL_MANIFEST.json` and schema: complete file/hash inventory, excluding itself
  and its schema only.

Use the existing environment with Pydantic 2, PyMuPDF 1.28.2 and BeautifulSoup:

```bash
env -u PYTHONOPTIMIZE PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-status-venv/bin/python -B \
  '/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-12/crs-2026-title1-source-review/build_review.py' --verify
```

The read-only verifier checks strict schemas, all inventory hashes, the official
referral and source digest/receipt, PDF structure, six native re-extractions,
complete region partitions/offsets, ordered paragraphs and recomputed comparisons.
It performs no network request, legal interpretation or catalog promotion.

This packet is ready for Atlas's direct review. It is not canonical intake or a
normal-backend answer source. The prior 2025 custody gap remains unchanged.
