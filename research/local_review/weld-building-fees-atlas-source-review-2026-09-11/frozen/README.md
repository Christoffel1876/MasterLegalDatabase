---
title: "Portable Weld building-fee source review"
status: "internal_source_qa_complete"
review_mode: "atlas_candidate_aware_not_blind"
external_assignment: null
legal_currentness: "not_verified"
---

This is a bounded Atlas review of the five-page received Weld building-fee PDF. It is not an Ebenezer assignment, a publisher-authenticated download, an adopted/current fee certification, or a pipeline promotion. Prior custody notes and native text were available during review.

Start with [SOURCE_REVIEW.md](SOURCE_REVIEW.md). [SOURCE_REVIEW.json](SOURCE_REVIEW.json) contains exact native byte ranges and all fee/table/context associations. The original PDF, five full-page images, ten targeted crops, unchanged candidate and per-page native/layout evidence are included. All raw native characters are preserved, including source anomalies and whitespace. The native layout JSON contains machine extraction geometry; source-review statements are separate.

The immutable preparation record predates the direct image review. It binds the canonical source, copied raw-manifest line 35, native candidate and full-page images. Copied custody records retain received-review provenance and their original limitations. Historical paths inside those records are informational; the validator never opens them. The other sources referenced in those whole copied custody files are excluded from this single-source package and are not being revalidated.

Use Python 3 with Pydantic 2, jsonschema and PyMuPDF **1.28.2**. From any directory:

```sh
PYTHONDONTWRITEBYTECODE=1 python /path/to/pre-review-2026-09-11/validate_review.py
```

An explicit package root is also supported:

```sh
PYTHONDONTWRITEBYTECODE=1 python /path/to/pre-review-2026-09-11/validate_review.py --root /path/to/copied-package
```

The validator is read-only and offline. It rejects missing, extra, changed or symlinked files; validates typed JSON/schema records; replays native extraction, page images and crops; checks full native byte partitions, row/column bindings, matrix geometry and required parent/footnote associations; and checks the selected raw-intake/custody chain. Successful reproduction proves the retained derivation/byte bindings under the specified engine, not human accuracy or legal effect. No external paths, URLs or live repository state are required.

The inventory includes every regular package file except the inventory itself, whose hash must be pinned by the recipient. Run with bytecode disabled so verification does not create files inside the inventoried package. Document checks are scoped to this exact five-page SHA, not all Weld sources.
