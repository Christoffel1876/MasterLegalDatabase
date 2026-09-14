---
title: "EB014 external reconciliation - portable additive research evidence"
prepared_at: "2026-09-11T19:47:57.724221+00:00"
status: "external_report_reconciled_with_qualifications"
legal_currentness: "not_verified"
source_and_candidate_changed: false
---

# EB014 reconciliation

This sibling preserves the completed Atlas reconciliation of Ebenezer's EB014 report. All **85 frozen audit files** are copied unchanged under `frozen/`: the four external reports and receipts, seven-page PDF and all seven page images, unchanged candidate and native evidence, custody, source annotations and links, eleven directly inspected crops, typed decisions, schemas and validation records. The earlier source package and original handoffs remain unchanged.

Read [Atlas's complete disposition](frozen/ATLAS_RECONCILIATION.md) with the [29 typed decisions](frozen/RECONCILIATION.json). The scope is **21 findings, three errata and five unresolved themes**: eight accepted, eleven qualified and ten source observations. These are report dispositions, not 29 extraction errors. **No substantive native word or number correction was found.** Legal currentness and operative effect remain unverified.

## Qualifications that travel with the evidence

- The cover's extracted footer and contents page's extracted banner/footer are not visible in the checked renders. Those strings nevertheless reproduce from the source PDF. Preserve their native bytes and distinguish them from visible text; do not call them fabricated or silently delete them.
- The mixed title quote shapes, narrow no-break spaces, inline `- 4 -`, repeated Conflict, missing conjunction and lowercase `it` are preserved source/native features. They are not instructions to normalize or repair the text.
- The City logo graphic extends left of and underneath its wordmark. The image words are preserved separately from native text. Exact logo contours, all font styles and Unicode identity from pixels are not certified.
- Three embedded page-2 URI destinations are recorded as PDF annotation metadata. None was opened. A printed label is not the same evidence as its full embedded destination, and neither establishes present availability.
- Purpose items A-L continue as M-N with the following qualification, explicit-reference exception, cited sections and contextual limits. The ongoing-use paragraph on physical page 7 continues section 1.2.4 before section 1.2.5. The copied source package retains all five existing context associations.
- The retained PDF contains Article 1 only. References to other articles, authority and adoption by reference are source wording, not independent verification of the adopting instrument, amendment chain or applicable law. No visible edition/adoption/effective date is established here.

## Immutable history and current additive status

[package-record.json](package-record.json) records the completed reconciliation status. Earlier `external_review_pending` fields inside the copied source package and received reports are historical statements. They have not been rewritten. The frozen comparison is bound to commit `95155c235bc64756c6ed1cdf9014cd920fe30fcc` and the handoff manifest SHA256 `449bff25ace84f7dffa817f3088b8d10aa40d8e44224c46ecfd220e81fe2d8c2`.

The external reviewer explicitly said `original.pdf` was absent from its local working directory and bound its hash from the assignment. Atlas independently hashed the actual **340,287-byte PDF**. The unchanged candidate is **14,370 bytes**, including packaging; **13,579 native page bytes** remain intact. All fourteen distinct advertised asset hashes match the local saved sources. This does not authenticate acquisition or independently certify the external reviewer's blind order, timing or tool actions.

Historical absolute paths in receipts, Markdown commands and assembly scripts remain unchanged for custody. **They are not dependencies of portable validation.** No files are omitted. Assembly scripts in `frozen/` are historical inputs; do not rerun them. Use the entry point below, which checks the top-level hash inventory before invoking the unchanged frozen validator in its default local-copy-only mode. The optional historical `--check-originals` mode is intentionally not used.

## Offline validation

Use Python 3.11+, Pydantic 2, jsonschema and PyMuPDF 1.28.2:

```sh
PYTHONDONTWRITEBYTECODE=1 python /absolute/path/to/ebenezer-014-reconciliation-2026-09-11/validate_package.py
```

An explicit `--package /absolute/path/to/package` is supported. The validator performs no network, Git or data writes. It checks the complete portable inventory, unchanged frozen inventory, all four reports, exact claim lines and 29 dispositions, source/page/candidate identities, native re-extractions and complete partitions, source observations, link metadata, font support and crop reproduction. It runs the copied earlier source-package validator as part of that check. It does not claim current law, operative effect or unseen historical reviewer actions.
