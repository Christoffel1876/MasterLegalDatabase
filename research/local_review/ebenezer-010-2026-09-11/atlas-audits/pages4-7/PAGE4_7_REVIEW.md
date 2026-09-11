---
title: "EB-PDF-010: independent source review, pages 4–7"
date: "2026-09-11"
source_id: "larimer-development-review-fees-sd004-07"
review_status: "rendered_regions_checked_pending_integration"
legal_currentness: "not_verified"
external_reports_consulted: []
source_sha256: "752dec4468ad92f5895a7af53ad0451b21517fb390212dc76b5f358f15fec64b"
candidate_sha256: "10e1a99cc47fdf2bbd3e42b5a17577efc975b4c36c94dc3f8f7090a195c55f04"
findings_sha256: "54cf3fd6ee9736b40efe0d78a0215e40935e5b07a45783ab8a4e0c5c096daf87"
---

# EB-PDF-010 — pages 4–7

The four complete packet images were inspected before the native page slices. This bounded check records **50 fee-value rows across 16 regions**. The checked amounts match the visible labels; the material defects are displaced headings, conditions and tier associations in the native reading order. No numeric correction or legal-currentness conclusion is made.

## Findings

| Page | Source association to preserve | Native-text limitation |
|---|---|---|
| 4 | General Fund exemption under **Location and Extent Review — $1,971.23** | Exemption moved after the final **Temporary Permit — $880.58** row. |
| 4 | **Engineering Fees** governs the construction, flood-board, vacation and final miscellaneous groups | Heading moved to page tail. Certificate amendments and commercial/industrial Urban/Rural indentation also needs explicit parent labels. |
| 5 | BFPD and PFA each have their own **may be subject to an additional Scope Fee — TBD** | Both qualification paragraphs moved below LCSO rows. Wrapped application lists remain single priced rows. |
| 6 | **$125 Initial Submittal and Resubmittal** carries the all-projects/all-resubmittals statement | Qualification moved after Special Review. |
| 6 | **Special Review — Hourly Rate, TBD by CGS** with its non-school/no-new-lots paragraph | Hourly/TBD line moved to page tail. Preserve the general no-additional-fee-to-$1500 range, complexity qualifier and cannot-be-prepaid wording. |
| 7 | Tier 1 **$200 / $100 / $25**; Tier 2 **$600 / $200 / $100**; Tier 3 **$1,100 / $500 / $250** | The three tier labels are detached from the fee blocks. Each sequence is Standard / Non-Profit–Community / Natural Resources. Full Road Closure is a separate **$500** row. |
| 7 | Three separate four-bullet tier groups, under **at least one** of the listed characteristics | Left-column tier/attendance labels displaced from the bullets. The Natural Resources asterisk condition must remain attached to the applicable fee rows. |
| 7 | The Tier 3 transportation bullet visibly lacks a closing parenthesis after “transit” | Native text preserves the source omission. Annotate it; do not silently repair it. |

## Boundaries and evidence

- Physical pages **4, 5, 6 and 7** were inspected in full; the typed records identify the particular fee/condition regions checked. Pages 1–3 were not reviewed in this subtask.
- No external reviewer report was read or compared, and nothing was sent to Ebenezer. Targeted crops were inspected after the native comparison.
- The packet source PDF and matching repository raw PDF have the same SHA-256 and **86,261 bytes / 7 pages**. The candidate, four images and four native receipts match their manifest hashes. PyMuPDF **1.28.2**, `sort=False`, `flags=195` reproduces pages 4–7 exactly, including the candidate byte slices.
- Footer crops confirm the supplied pages 5 and 7 each visibly contain **Larimer County Development Review Fee Schedule** and **Page 5 / Page 7**. They are not native-text inventions.
- Exact file hashes, page offsets, rendered-region rows, qualifications, ten findings, five diagnostic crop bindings and limits are in [source-review.json](source-review.json), validated against [source-review.schema.json](source-review.schema.json).
- No packet, native text, external report or repository corpus was edited. Source URL/acquisition claims, operative dates, amendment completeness and legal applicability remain unverified.

The source-only review is ready for Atlas integration; it does not certify all-page transcription accuracy or promote any legal claim.
