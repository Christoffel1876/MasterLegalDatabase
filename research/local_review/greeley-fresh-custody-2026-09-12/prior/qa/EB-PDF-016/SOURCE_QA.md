---
title: "EB016: three-page Greeley impact fee memorandum source QA"
date: "2026-09-11"
source_id: "greeley-development-impact-fee-memo-sd008-07"
assignment_id: "EB-PDF-016"
status: "three_page_candidate_aware_source_qa_complete_pending_parent_integration"
review_mode: "candidate_aware_not_blind"
external_review_consulted: false
legal_currentness: "not_verified"
---

All three complete source images and seven targeted crops were inspected against the unchanged native candidate. The visible memo wording and printed table figures match the native text. No text edits or arithmetic corrections were applied. This is candidate-aware Atlas QA: the reviewer prepared the packet and had seen its source images, candidate and intake provenance. No external EB016 review was consulted.

The [typed review](SOURCE_QA.json) preserves every one of the 7,191 original native UTF-8 bytes in three original page files and 12 exhaustive chunks. The entire 7,530-byte page-marked candidate is copied unchanged. Three table regions contain 30 fee rows: Police 7, Fire 7, Park 4, Trails 4, Storm Drainage 1 and Transportation 7. Including captions, headers and blank separators, the explicit grid has 45 rows and 191 cells. Each non-whitespace native table byte belongs to exactly one cell; each fee row references its group header. Empty cells stay empty.

The material reading-order qualifications are:

- The page 1 EAF column labels are interleaved in native order. The reviewed grid binds each word to its visible column, keeps the final EAF weight cell blank, and preserves every printed percentage.
- Page 3 emits its first six Transportation labels followed by the 2025 column, the change column and the 2026 column. The reviewed grid restores the visible row associations while preserving the untouched original order. Its year/change headings are carried explicitly from page 2; they are not repeated on page 3.
- Residential size conditions span the first two columns and refer to heated living space. No unprinted per-dwelling unit was added. Commercial units retain page 2's `1,000 Sq. Ft of Building` and page 3's `1,000 Square Feet of Building` separately.
- Native `-A` before the page 1 title is not visible in the full image or header crop. It remains in the native record as an explicitly non-visible artifact. The logo words and the native U+F0B7 bullet encoding are separately disclosed. No printed page labels or footnotes were observed on these three pages.

Date and legal-scope statements remain source claims. The memorandum is dated November 1, 2025; it refers to a 2023 adoption of methodology and Code Chapter 4.64.055(b), describes the 2024-versus-2023 data comparison for fee year 2026, and states a March 1, 2026 effective date with approximately 120 days of public notification. The cited code and adoption instrument were not independently opened. The separate Water and Sewer paragraph says its PIFs will be adopted “in December”; it gives no explicit December year or water/sewer rates in this document and does not prove later adoption.

The general zero-decimal rounding description and “decrease an average of -2.07%” wording are preserved. The Storm Drainage row separately prints $0.315, -2.22% and $0.308 per impervious square foot. Neither those figures nor the other source percentages were recomputed, standardized or repaired. Present applicability, amendment completeness and current fee status remain unverified.

The local package contains exact copies of this PDF, candidate, full images, native evidence and the batch manifest, plus the untouched native page files and inspection crops. The canonical retained PDF was byte-equal when checked. This review performed no HTTP requests; it does not promote reported acquisition time into a newly witnessed event. The copied batch manifest refers to other queue documents, but this bounded review verifies only EB016 payloads. Earlier draft schema/data are retained under `_draft-snapshots/initial-schema` and are not the final review.

Run the portable verifier with the prepared Python environment:

```sh
PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-register-ci-venv/bin/python build_review.py --verify
```

The verifier checks strict Pydantic plus the exported JSON schema, 19 unique referenced files, all three source/candidate/evidence bindings, exact native extraction replay, all exhaustive spans and seven exact crop rerenders. Nine deliberate corruptions were rejected, including wrong values, missing rows, missing units, broken group/header references, changed image hashes, byte gaps and altered candidate offsets. The full-page images are the exact frozen 300 dpi Poppler renders; no source, packet, queue, repository, ledger or bot output was modified.
