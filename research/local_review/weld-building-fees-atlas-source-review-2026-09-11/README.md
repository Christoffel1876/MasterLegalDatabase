---
title: "Weld building fees — portable Atlas source review"
packaged_at: "2026-09-11T19:57:11.623396+00:00"
status: "internal_source_qa_complete"
review_mode: "atlas_candidate_aware_not_blind"
external_assignment: null
legal_currentness: "not_verified"
---

This package preserves all **49 files** of the frozen Atlas review exactly under `frozen/`. The five-page source, unchanged candidate, native text, page images, crops, review, schemas, custody and existing validator remain intact. Start with [the source review](frozen/SOURCE_REVIEW.md); its typed record is [SOURCE_REVIEW.json](frozen/SOURCE_REVIEW.json).

The completed source QA covers 107 fee/value/referral rows, including 252 valuation-matrix cells. All 14,311 native UTF-8 bytes are preserved. These are transcription counts, not counts of legal requirements. This is candidate-aware Atlas review, with no external EB assignment. Packaging does not constitute another source review.

The face **JANUARY 2026** and literal **Revised 012/25** retain their distinct date roles. Visible source anomalies remain unchanged. No arithmetic, signature identity, legal interpretation, adopted-status or currentness certification is supplied.

Acquisition remains `received_review_package`, with successful requested version/final URL and original HTTP acquisition time unconfirmed. The supplied `/v/3/` URL is reconstructed context only. `official_source_url` remains null. Repository receipt time is separate, and the source remains `archived_pending_pipeline`.

[package-status.json](package-status.json) records these boundaries. Its historical handoff path is informational; validation does not open that location or the live repository. Other sources referenced by whole copied custody records are outside this single-source package.

## Offline verification

Use Python 3.11+ with Pydantic 2, jsonschema and PyMuPDF **1.28.2**:

```sh
PYTHONDONTWRITEBYTECODE=1 python /path/to/weld-building-fees-atlas-source-review-2026-09-11/validate_package.py
```

`--root /path/to/copied-package` is optional. The wrapper verifies the typed packaging status and complete file inventory, then invokes the unchanged `frozen/validate_review.py`. It adds no source-semantic logic or new synthetic tests. The retained validator still performs its original extraction/image/crop/association and tamper checks. Verification is read-only and offline; successful hashes and reproduction do not certify human judgment or legal effect.

Pin the SHA-256 of `evidence-manifest.json` outside the package. Its inventory covers every file except itself. Run with bytecode disabled so the verifier does not create files inside the inventory.
