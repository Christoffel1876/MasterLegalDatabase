---
title: Local text and fee recovery audit
prepared: 2026-09-10
baseline_commit: 290d4c2f876efccc289ff53294657fb5464eda64
legal_currentness: not_verified
legal_review: pending
---

# Local text and fee recovery audit

This batch recovers the two pilot municipal publications, OCR for the selected
local scans, broader fee schedules, and source-backed amendment/fee findings.
The original statewide coverage ledger remains the denominator. No category is
certified complete or current, and no recovered text is promoted to canonical
legal obligations.

## What was preserved

| Evidence | Result |
|---|---|
| Golden published code | 1,202 physical PDF pages; Supplement 20 through April 28, 2026 |
| Georgetown published code | 1,384 ordered publisher chunks; Supplement 15 through April 23, 2024 |
| Georgetown linked images | All 12, including one logo and 11 substantive plates |
| Native municipal text | 2,586 source-bound records, verified by full regeneration |
| OCR | 364 page records from 26 PDFs; 394 receipt/manifest/page JSON files |
| OCR limitations | No engine failures; one visually blank page; 266 low-confidence pages |
| Additional fee sources | 10 complete PDFs and two official catalogs |
| Sampled fee study | 27 cited findings and 11 open amendment/conflict chains |
| Visual passage checks | 30 amendment excerpts plus 11 fee excerpts |

The ledger grows from 106 to 120 source captures. It retains 340 authority entries
and 4,080 investigation items: 45 have legal documents preserved, nine have only
supporting evidence, and 4,026 have no assigned evidence. These counts describe
collection, not active-government completeness or legal applicability. Both
legally current and legally reviewed category counts remain zero.

The export manifest separately owns its supporting proof and images. This batch
adds 33 immutable source files and two explicitly derived proof summaries,
30,206,429 bytes in total. The largest new file is Golden's 20,047,945-byte PDF.
Existing originals are reused unchanged. Source requests were bounded: 29
operations for municipal exports and 25 for fee research, including web discovery.

## Accuracy findings that change the next work

- Golden's comprehensive fee publication and separately linked building-fee
  sheet disagree on the minimum time for an inspection without a specific fee:
  two hours versus half an hour. Their adopting instruments remain necessary.
- Georgetown's general fee schedule lists a flat truck-haul amount while a later
  ordinance describes fees based on trips and road impacts. The fee study also
  preserves duplicate labels, an omitted usage unit and differing waiver routes.
- Clear Creek R-24-92 identifies the missing R-22-60 planning-fee resolution and
  expressly supersedes its short-term-rental fees. It does not establish that
  all planning fees were replaced.
- Visual checks corrected OCR errors in handwritten dates, including Georgetown
  Ordinance 4's posting date and Clear Creek Ordinance 4-A's second-publication
  year. Raw OCR remains unchanged and its unreviewed status is retained.
- West Metro's adoption contains further municipality/county approval conditions.
  Its district adoption date alone does not prove effectiveness for a property.
- Georgetown Ordinances 3 and 4 touch overlapping Chapter 15.20 provisions. The
  published 2024 consolidated code and later signed enactments require a careful
  amendment sequence before a current text can be assembled.

## Reproducibility and review limits

The two immutable OCR selections retain the SHA-256 of the ledger as it existed
when each selection was made. Those exact ledgers are archived at:

- `_SNAPSHOTS/snapshot_2026-09-10T195232193125Z/_CONTROL_PLANE/LOCAL_COVERAGE_LEDGER.json`
- `_SNAPSHOTS/snapshot_2026-09-10T195906947018Z/_CONTROL_PLANE/LOCAL_COVERAGE_LEDGER.json`

The current ledger can grow without silently extending an older OCR selection.
Validation checks every selected source, physical page, ordered manifest entry,
receipt hash, text hash and summary. Checked excerpts must also belong to their
validated collection. Every unchecked passage remains machine-generated text.

The original signed publisher download response and unrelated vendor JavaScript
bundle remain in ignored runtime storage. Their exact original hashes are retained
in explicitly derived durable summaries, with non-recomputation disclosed. The
actual municipal code and image bytes are preserved as originals. No temporary
signed token, browser credential or local machine path is needed in the published
evidence package.

See [Local text recovery](../LOCAL_TEXT_RECOVERY.md) for edition cutoffs, the known
blank-page status and validation commands. The fee study's citations and open
chains provide the next bounded research queue. The optional
[Grok source review brief](../GROK_SOURCE_REVIEW_BRIEF.md) can support an independent
audit without repository write access.

## Validation results

- Full repository test suite: **1,438 passed**.
- Focused local-evidence workflow: **448 passed**, using the frozen CI dependencies.
- New modules: OCR and fee review **100%** branch-aware coverage; municipal export
  **99%** and checked-excerpt review **97%**. The extended ledger validator is **99%**.
- Actual ledger originals, municipal proof, all 2,586 saved native records, both
  OCR collections, 41 checked excerpts and 27 fee findings passed offline validation.
- Both exact selection-ledger snapshots match their recorded hashes and validate.
- All staged source blobs were compared with the preserved bytes; existing raw
  sources were unchanged. No new file exceeds 50 MB.

The six missing legacy LFS objects remain unrecovered. Whole-corpus validation
still reports the inherited county-index and review-summary checks; the latter
depends on the missing review queue, while the summary JSON itself parses.
The daily county manifest remains four catalogs and 30 selected documents.
Hosted collection failures and deferred always-on Mac installation are unchanged.
Local research usability is not external reliance readiness; human/legal review
remains pending, and this corpus is not legal advice.
