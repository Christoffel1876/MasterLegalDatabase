---
title: "EB013 source QA: physical pages 1–4"
reviewed_at: "2026-09-11T19:10:24.427427Z"
source_id: "fort-collins-wildfire-code-sd005-05"
assignment_id: "EB-PDF-013"
status: "pages_1_4_candidate_aware_source_qa_complete_pending_parent_integration"
review_mode: "candidate_aware_not_blind"
external_review_consulted: false
legal_currentness: "not_verified"
---

# EB013 source QA: physical pages 1–4

No word or number correction was identified in these four pages. All 10,704 original native UTF-8 bytes are retained unchanged in the typed review and four `page-NNNN.original-native.txt` files. The original PDF, packet, candidate and canonical records were not changed. This review is candidate-aware: the reviewer prepared the packet, previously saw its source images and now compared the candidate against four complete images and nine focused source crops. No external EB013 report was consulted.

`SOURCE_QA.json` contains 33 observations and 36 exact byte-bound evidence spans. Each page binds the original PDF hash, full-page PNG hash, native-evidence hash, full candidate offsets and preserved native bytes. Header, footer and body chunks exhaustively partition every page byte. Their separate display-order references place the footer last without rewriting the original text.

## Findings requiring preservation

- **Draft status and numbering:** All four pages show both draft-warning lines. Page 1 retains `ORDINANCE NO. XXX, 2025` and two consecutive recitals labeled `C.`. Do not fill the ordinance identifier or renumber the second C.
- **Source citation and date wording:** Page 1 prints `8 Code of Regulations Colorado 1507-39(3)` in that unusual order. The July 1, 2025 adoption recital and page 2 June 1, 2025 publication wording describe different asserted events; neither has been independently verified here. Preserve the exact citations, dates and nine-month wording.
- **Notice blanks:** Page 2 has three green-filled underlined blank date areas followed by 2025. The candidate's underscores preserve native characters; neither the dates nor exact rendered underline-glyph counts are supplied. Article II, Section 7 and both notice intervals—at least eight (8) days and at least fifteen (15) days—match.
- **Page 3 redline marks:** `[NAME OF JURISDICTION]` is struck through and immediately followed by yellow-highlighted `the City of Fort Collins`; the native `]the` adjacency is retained. Both instances of `variance` are struck and both following instances of `modification` are yellow-highlighted. The complete 102.9.1 exemption paragraph is struck through after an unstruck deletion instruction. Plain text alone does not convey these distinctions.
- **Exception scope:** The full three-designation historic-structure exception, including its negative wording, remains unchanged. The 102.10 introductory caveat and exemption item 1 on page 3 connect to items 2–10 on page 4.
- **Page 4 numerical conditions:** Preserve 500 square feet, the separate 25-percent and twenty-five-percent clauses, the three April 1, 2026 comparison phrases, the 120-square-foot cap, greater-than-or-equal-to 10 feet, more than 50 feet, more than 8 feet, and the thirty-five-acre/one-residential-structure/non-abutment condition. The date-comparison clauses for items 2–4 are yellow-highlighted; item 5 lacks that dated phrase.
- **Section 103 marks and hierarchy:** The outer amendment number 5 resumes after exemption item 10. The first standalone Section 103 heading and all old 103.1–103.3 text, including `[INSERT NAME OF DEPARTMENT]`, are struck. The second standalone heading at the bottom is unstruck and yellow-highlighted. It must not be deduplicated. Its subsequent replacement body falls outside this four-page review.
- **Other layout:** Yellow outlines surround the page 2 Article IX body and the bodies of pages 3–4. Native extraction places each printed footer before the body; actual visual reading order is header, body, footer. These physical annotations and ordering observations are separate from source wording and legal effect.

## Verification and limits

Strict Pydantic and exported JSON Schema validation passed. The verifier checked 24 file identities, four native re-extractions, complete candidate-page offsets, all native chunk partitions, all observation byte spans and their SHA256 values. A separate direct check confirmed original/candidate identity against the frozen packet manifest and exact equality between the packet PDF and canonical raw PDF. The source has eight physical pages; this task reviewed only pages 1–4.

Source SHA256: `00e7446d7deac3499b86c4b8f15a5d802cc0c14dc2621409845ec13525cb01d2`.

Candidate SHA256: `9fc7fe62d1d678407db0d228a6e5ddc2397765a1d2f6d5ab4430a7cac3922ea7`.

Typed review SHA256: `6b08592e9a3d8c2149b4d0c12401516802931ff10d2ee273f96fd9748686841e`.

No consolidated or operative text was produced. Exact visible Unicode codepoints, a complete font-style inventory and every individual underline glyph are not certified. The source is visibly a draft; its filename, enacting language, additions, strikes and dates establish no adopted or current legal effect. No network requests, external report consultation or legal applicability assessment occurred. Existing packet custody paths remain necessary; this review is not a standalone bundle of all upstream evidence.

Revalidate without changing outputs:

```sh
PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-register-ci-venv/bin/python \
  handoffs/atlas-reviews/fort-collins-wildfire-code-sd005-05/pre-review-2026-09-11/pages1-4/build_review.py --verify
```
