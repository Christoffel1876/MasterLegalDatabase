---
title: EB013 external reconciliation — portable additive research evidence
prepared_at: 2026-09-11T19:41:46.760194+00:00
status: external_report_reconciled_with_qualifications
source_document_status: visibly_draft
legal_currentness: not_verified
source_and_candidate_changed: false
---

# Result and scope

This portable sibling preserves the completed Atlas reconciliation of Ebenezer's EB013 report. It includes all four unchanged external reports/receipts, every disposition and its source evidence, the complete frozen source-review package, source/candidate/page/native/custody bytes, diagnostic crops and limited native font metadata. The existing committed source package and original handoffs remain unchanged.

The reconciliation contains **23 external findings, four errata and three Atlas supplements**: eight accepted, thirteen qualified, four rejected and five source observations. These are dispositions of report claims, not thirty independent extraction errors. **No native word or number correction is required.** The original candidate remains unchanged and the document remains visibly draft, with operative effect and legal currentness unverified.

Read [Atlas's complete disposition](frozen/ATLAS_RECONCILIATION.md) with [exact typed decisions](frozen/RECONCILIATION.json). The [external PASS2 report](frozen/received/PASS2_REVIEW.md) and [frozen PASS1](frozen/received/PASS1_frozen.md) are retained without editing; the disposition governs the qualifications to their claims.

# Qualifications that must travel with the evidence

- **E03 is rejected:** `Ignition-resistant plantings` and `Immediate Zone` are roman in the struck Exception. The preceding `noncombustible` is italic. Preserve the entire Exception's strike independently from font style.
- **E04 is rejected:** the full `habitable space` phrase is italic in item 8. Do not make `space` roman. Nearby item 9's `habitable` is roman; font style does not transfer between adjacent items.
- Green-filled, underlined blank date fields do not prove redaction or removed month/day characters. Finding 023's redaction framing is rejected and overlaps finding 001. No hidden date is inferred or supplied.
- The candidate retains the draft banner and explicit deletion/replacement instructions. Missing graphic strikes or highlights are representation limits, not evidence that the plain text is operative law or that old and replacement provisions apply concurrently.
- Blank execution fields, proposed enacting wording, draft dates and highlighted replacements do not establish adoption, currentness or applicability. Exact Unicode, physical underscore counts and exhaustive font styling are not certified.
- The external counts of ten critical, seven minor, four information and two unresolved findings are preserved as reported arithmetic. They do not establish nineteen independent accepted errors. Several findings overlap or aggregate multiple passages.
- Atlas's eight-page reconciliation was candidate-aware. External blind-order, timing, model and caption-access claims remain self-reported. No external diagnostic crop files accompanied the four-file report delivery.

# Portability and immutable history

[package-record.json](package-record.json) gives the new additive status and accounts for every frozen handoff input. The copied prior source package remains under `frozen/comparison/committed-package/`; its old external-review-pending label is a historical statement, not the current status of this later reconciliation. It contains all eight original page images, the 169,449-byte PDF, the unchanged candidate and all 18,881 native page bytes with 72 observations and 126 annotations.

The four external files are bound by `frozen/CUSTODY_RECEIPT.json`. The 75 comparison inputs and fifteen distinct asset-hash claims are bound by `frozen/COMPARISON_RECEIPT.json`. The original handoff inventory SHA256 is **7f77104042b259162bee7981ad3d3091aefc088865a3b74dbde0310ad38e7da4**. Historical absolute paths and Git-match fields are preserved as historical receipt text; portable validation uses copied local bytes instead.

The source package is copied once as a complete independently verifiable unit. Four historical assembly/nonportable validation scripts are omitted, with their exact size/hash identities in the input dispositions. No source, external report, typed finding, custody receipt or source-review file is omitted. Retained helper scripts are historical evidence; use the portable entry point below.

# Offline validation

Use Python with Pydantic 2, jsonschema and PyMuPDF:

```sh
PYTHONDONTWRITEBYTECODE=1 python /absolute/path/to/ebenezer-013-reconciliation-2026-09-11/validate_package.py
```

An explicit `--package /absolute/path/to/package` is supported. The validator performs no network, Git or file writes and needs no original handoff paths. It checks the actual inventory, original frozen manifest, strict reconciliation schemas, four report identities, all comparison and claimed hashes, exact report lines, decision/page/annotation bindings, all eight native page re-extractions and the unchanged source package. It also replays bounded native font spans and diagnostic crop pixels. It does not authenticate source acquisition, external blind review, legal effect or excluded script bytes.
