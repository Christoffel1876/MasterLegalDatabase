---
title: EB013 Fort Collins wildfire draft — Atlas source review
prepared_at: 2026-09-11T19:17:05.296996+00:00
document_status: visibly_draft
extraction_review_status: atlas_eight_page_source_review_complete
external_review_status: pending_receipt_and_reconciliation
legal_currentness: not_verified
---

# Result and boundaries

This portable package combines the two independent Atlas source audits for all eight physical pages. It preserves the original PDF, unchanged native candidate, eight full-page images, eight native receipts, complete source-audit inputs and frozen intake custody. The typed review contains 72 source observations, 126 separate annotations and all 18,881 original native UTF-8 bytes. No word or number correction was identified by either scoped source review.

The document is visibly a discussion draft. The source's proposed enacting language, title year and redline markup do not establish adoption, current effect or applicability. Ebenezer's external EB013 review is **pending receipt and reconciliation**; no external report was consulted or incorporated here.

[candidate.txt](candidate.txt) is the exact original byte sequence, including struck wording, placeholders, footers and page markers. [reviewed-draft.json](reviewed-draft.json) retains the native pages and separate byte-bound annotations. It contains no clean enacted ordinance. Display-order IDs move the conceptual footer position without rewriting source characters.

# Preserve these distinctions

- The draft retains `ORDINANCE NO. XXX, 2025`, two consecutive C recitals and the unusual citation wording `8 Code of Regulations Colorado 1507-39(3)`. The July 1, 2025 recital and June 1, 2025 publication wording describe distinct source assertions; neither is resolved here.
- Three green-filled notice-date blanks on page 2 remain unfilled. The two notice intervals, eight and fifteen days, stay distinct. Exact native underscores remain, without claiming a physical underline-glyph count.
- Jurisdiction replacement, variance/modification pairs, the historic-preservation deletion and the complete old Section 103 block have distinct strike/highlight annotations. The repeated unstruck Section 103 heading is retained and connects to its page 5 replacement body. The `]the` adjacency is not silently changed.
- Permit-exemption and Chapter 401 scope-exception lists retain their separate introductions, conditions and numbering. The April 1, 2026 comparisons, inequality words, area/distance thresholds, historic-designation conditions and literal `Chapter X` are preserved. No missing date condition is added to another list item.
- Deleted materials, planting and tree paragraphs remain as struck source text. The old C101.3.7 fee-authority wording remains anomalous source text; the highlighted replacement continues across pages 7–8 through § 1-15(f) and the separate-offense sentence.
- Page 8's full draft header is present. Reading dates, signature lines and effective-date field remain blank, with printed 2025. Madelene Shehan is a printed label, not an authenticated signature.

# Custody and portability

Every working evidence path is relative to this folder. Immutable original audits and custody records retain their historical path strings; the manifest maps those inputs to copied local bytes. The packet's frozen 31-row raw manifest, physical line 17, source-provenance line 5 and original intake receipt agree on the 169,449-byte PDF. Actual repository receipt remains September 11, 2026 at 18:29:00.820696 UTC. Original acquisition time is unknown; source URL, HTTP status and referral remain qualified supplied claims.

The full historical custody records also describe other documents. Their upstream originals and 193 MB archive are not part of this eight-page review. The original packet manifest names EB014 as well; EB014 is not reviewed here. Source/candidate bytes and active repository records remain unchanged.

# Offline validation

From any directory, using Python with Pydantic 2, jsonschema and PyMuPDF:

```sh
PYTHONDONTWRITEBYTECODE=1 python /absolute/path/to/ebenezer-013-2026-09-11/validate_package.py
```

Alternatively pass `--package /absolute/path/to/ebenezer-013-2026-09-11`. The validator requires no handoff directory, repository imports, network, credentials or writes. It verifies the complete file inventory, source and page hashes, all eight native re-extractions, candidate slices, exhaustive byte partitions, annotation bounds, unchanged independent findings and retained custody. This is evidence validation, not legal-currentness certification.
