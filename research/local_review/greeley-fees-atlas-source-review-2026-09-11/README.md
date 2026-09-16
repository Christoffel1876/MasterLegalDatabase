---
title: Greeley fee sources — portable Atlas source-review package
date: "2026-09-11"
status: atlas_source_reviews_packaged_pending_external_review
legal_currentness: not_verified
external_report_intake: false
---

# Scope

This package preserves three candidate-aware Atlas source audits and their exact input evidence. It covers six physical pages and all 11,743 native text bytes. External review remains pending and has not been incorporated. This is source fidelity research, not a set of operative fees, a current-law answer, or a coverage promotion.

| Assignment | Retained source | Pages | Native bytes | Source-review scope |
|---|---|---:|---:|---|
| EB-PDF-015 | Greeley building permit fee schedule | 1 | 3,236 | Eight valuation rows, nine other-fee items, both footnotes, sales tax and temporary electrical sections |
| EB-PDF-016 | Greeley development impact fee memorandum | 3 | 7,191 | EAF grid, thirty fee rows and all memo paragraphs; row/column and unit associations |
| EB-PDF-017 | Greeley proposed Water/Sewer PIF notice and schedule | 2 | 1,316 | Conditional notice, separate seven-row and one-row tables, image-only logo/footer findings |

The source audits are unchanged in `source-audits/EB-PDF-015`, `source-audits/EB-PDF-016` and `source-audits/EB-PDF-017`. Their JSON records retain complete native bytes or exhaustive spans, source/candidate hashes, reviewed reading order, table associations and scope qualifications. Their human-readable audits remain adjacent. EB016's earlier draft schema/data are preserved in its original `_draft-snapshots` subdirectory as historical evidence; the top-level `SOURCE_QA.json` is the final audit referenced by the package.

# Dates and conditional statements

- The building source has a 2024 title and `Effective -2024` table heading, plus an unlabeled `8/18/2026` footer. The footer is not silently reclassified as an adoption or effective date. Hourly-cost footnotes, distinct minimum durations, fee additions and sales-tax conditions remain bound to their source passages.
- The impact source is a memorandum dated November 1, 2025. Its statements about a 2023 methodology, fee year 2026, March 1, 2026 effective date and approximate notification interval remain separate. Its future Water/Sewer adoption statement is not certified as completed. All printed percentages, units and amounts remain unchanged, including the general zero-decimal wording and the Storm Drainage row's three-decimal amounts.
- The utility source is a notice dated November 20, 2020. It anticipates Board review on December 16, 2020 and expressly conditions March 1, 2021 on adoption. The two tables remain separate, including the right table's blank first header. Dollar signs were not added to cells where they are absent. Weld County contractors are recipients, not proof of a Weld County fee enactment.

All three audits are candidate-aware source checks, not blind external transcriptions. Native text that loses layout, source-image wording absent from native extraction and printed source anomalies are disclosed separately. No fees were computed or corrected.

# Portable evidence and verification

`packet/` is an exact copy of the frozen EB015–017 packet, including the three originals, six complete 300 dpi images, untouched native candidates and extraction evidence, exported schemas, saved Greeley referral HTML, derived response headers, intake receipt, provenance and the immutable 38-record raw manifest snapshot. The historical packet status and dispatch instructions are preserved as evidence only; this package does not dispatch work or change a queue.

`PACKAGE.json` inventories every payload by hash, size, path and copy provenance, identifies each final audit and includes explicit mappings from relevant historical original paths to frozen local copies. Those mappings do not change the original audit or manifest. Original acquisition times remain qualified upstream claims; this packaging step performed no network acquisition. The exact retained PDFs were copied from already archived evidence.

Run the read-only wrapper from any directory with Python 3.11+, Pydantic 2, jsonschema and PyMuPDF 1.28.2:

```sh
python /path/to/greeley-fees-atlas-source-review-2026-09-11/validate_package.py
```

Use `--rerender` with Poppler `pdftoppm` 26.05.0 to additionally reproduce all six full-page PNGs exactly. The wrapper disables bytecode writes. It validates the closed payload inventory, exported schemas, source/candidate/page hashes and offsets, complete native replay, fee/footnote associations and table geometry. It invokes only the read-only parts of the copied source verifiers and resolves their historical inputs from this package. Do not run archived `build_review.py` construction commands.

Some preserved audit prose or provenance records still name original absolute paths, and the packet's full-header identities intentionally refer to header bytes not included here; the included header files are the previously derived copies with Set-Cookie lines omitted. Those historical/context references are not runtime dependencies of this wrapper. The raw-manifest snapshot also contains unrelated intake records; this package verifies the three selected source lines and makes no completeness claim about those unrelated records or the original upstream environment.

No repository control plane, raw archive, coverage ledger, source packet, handoff audit or external report was changed. Legal currentness, adoption verification and amendment completeness remain unverified.
