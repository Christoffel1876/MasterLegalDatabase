---
title: Sherlock007 received-package PDF intake
date: 2026-09-11
received_at: 2026-09-11T19:01:59.855958+00:00
status: archived_pending_pipeline
legal_currentness: not_verified
semantic_or_coverage_promotion: false
---

# Intake result

Nine retained PDFs (345 pages) were checked against both original and frozen delivery bytes. Six exactly match existing canonical originals, including the 97-page building amendments and 33-page wildfire code. Only three new originals (200 pages; 31,000,893 bytes) were archived: the two-page equity reduction instrument, four-page staff recommendation memo, and 194-page February meeting packet.

The equity instrument prints `January 2, 20243`; this source anomaly is not silently corrected. Its signatures are not authenticated. The memo's recommendation and intended implementation date are separate evidence. The February packet contains staff recommendations and an unsigned extension draft, not a verified executed extension. Source-audit qualifications are carried into each provenance record; this intake adds no legal interpretation or currentness certification.

The receipt time above records local repository custody. Original acquisition time remains unknown. Browser 200 status, final URLs and approximate file-time claims are reconstructed supplied claims. No network request was made. The CivicClerk URL is not accepted by the existing official-source allowlist; the packet record keeps `official_source_url=null` and preserves its exact supplied URL/referral context separately. No allowlist or acquisition-method policy was changed.

# Identity and preservation

The complete `_RAW_ARCHIVE` size screen covered 535 ordinary files. Every matching-size file was SHA-256 checked (6 files); no symlinks were encountered. Different-size bytes cannot be duplicates. Missing Git LFS objects and historical digests alone are not treated as available originals. All 87 audited original/frozen custody pairs remain unchanged, and all nine PDFs open unrepaired and unencrypted. PDF parsing here checks structure, not complete textual accuracy.

The raw manifest grew from 31 to 34 records. The ledger grew from 32 to 35, with all existing bytes preserved as exact prefixes. The report distinguishes 34 verified originals from the unchanged missing ledger-only EO record. Three preimage snapshots and immutable before/after transaction copies preserve the append. Batch4's exact 31-row manifest copy was verified before append; no review packet was modified.

The official-only intake request API cannot represent `received_review_package` truthfully. Validated `ManualSourceIntakeRecord` objects and existing write-once/reconciliation helpers were used; no production module or policy was edited. All records remain `archived_pending_pipeline`.

# Verification

From the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python research/local_review/larimer-intake-sherlock007-2026-09-11/validate_intake.py
```

The standalone validator checks strict records, immutable transaction bytes, the existing source custody, all nine canonical PDF hashes and page counts. Reconciliation dry-run predicted three additions; apply completed; repeat dry-run returned no additions or report changes. No full-corpus rebuild, source extraction, review/coverage promotion, Git commit, push or bot message was performed.
