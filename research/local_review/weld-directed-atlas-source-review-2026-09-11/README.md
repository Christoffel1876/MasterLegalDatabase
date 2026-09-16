---
title: "Weld directed source reviews - portable Atlas evidence"
prepared_at: "2026-09-11T20:01:32.223610+00:00"
status: "source_reviews_complete_pending_separate_intake"
legal_currentness: "not_verified"
source_and_native_changed: false
---

# Two preserved source reviews

This package combines the completed Atlas source checks of Weld Ordinance 2026-01 and the 2026 Environmental Health Services fee schedule. All **71 frozen audit files** are copied unchanged: 45 ordinance files and 26 EHS files. Together they preserve **eight source pages and 16,651 native UTF-8 bytes**. No source or native text is rewritten; no new visual review or external reviewer assignment occurred during packaging.

Read the [ordinance source review](frozen/ordinance/SOURCE_QA.md) with its [typed findings](frozen/ordinance/SOURCE_QA.json), and the [EHS source review](frozen/ehs/SOURCE_QA.md) with its [typed fee rows and notes](frozen/ehs/SOURCE_QA.json). The complete PDFs, original native page bytes, page images, diagnostic crops, schemas and verification records accompany the findings.

## Source identity and pending intake

| Audit source ID, preserved unchanged | Pending intake source ID | Scope |
|---|---|---|
| `weld-ordinance26-01` | `weld-ordinance-26-01-atlas-directed` | Five-page ordinance; 9,284 native bytes |
| `weld-ehs-fees-2026-atlas-directed` | `weld-ehs-fees-2026-atlas-directed` | Three-page EHS fee schedule; 7,367 native bytes |

Both sources identify Weld County. [package-record.json](package-record.json) records the explicit ID mapping and additive review status. It does not edit the old audit ID or claim canonical intake has occurred. Original-source intake, its raw/manual/control records and subsequent legal reconciliation are separate work.

## Ordinance role and limits

The source presents Ordinance 2026-01 as adopted **April 6, 2026**, with four printed Aye votes and one Nay, and states **Effective: April 15, 2026**. Publication, first/second reading, rescheduled final reading and continuation dates keep separate roles. The printed approval/attestation names and county seal are preserved; no handwritten signature was observed, and execution is not independently authenticated.

These five pages contain selected Chapter 23 zoning amendments with explicit no-change/renumber instructions. They are not the complete consolidated chapter. Preserve the definition's separation of peak electrical load from backup generation capacity, the **65 dB(C)** limit and property-boundary context, the noise-plan **may be required** wording, and distinct I-1 special-review versus I-2/I-3 site-plan-review routes. The source typo **I. though T. - No change.** remains unchanged. Municode supplementation instructions do not prove supplementation happened.

The source check contains 18 page-bound observations, 11 separately labeled date records, all five complete page checks, three additional full-page renders and eleven crops. It identifies source-stated adoption and effectiveness; legal currentness and later amendments remain unverified.

## EHS fee role and limits

The schedule identifies Weld County Department of Public Health and Environment and the year **2026**. No adoption/effective date or adopting resolution is shown in these three pages. The year is not converted into a legal date.

The source check preserves **137 rows in 11 service groups**, **136 printed fee cells**, **one visibly blank fee cell**, and all **313 native lines**. All three full pages and five crops were checked in that frozen audit. Row/fee geometry and nearest preceding group were verified. Blank, zero, hourly, market-rate, capped and contract-dependent amounts remain distinct.

Keep the clipped coordinator condition incomplete, preserve source spellings, and do not invent an exactly-25-person tier between `<25` and `>25`. File Review Fees has a blank amount, not zero. The methamphetamine permit's four-hour inclusion and excess-time note stay together; the three-times-fee rule stays in its bacteriological group. Wrapped Additional Metals is one label with one fee. The final contract-approved-by-the-Board exception remains attached to the stated analysis rates. No contract or replacement amount was reviewed.

## Immutable history and portability

The copied audits retain their original absolute paths, times, historical statuses, access-result claims and assembly scripts. Those paths are custody text, not dependencies of the portable entry point. Do not rerun historical builders in write mode. The ordinance `_SNAPSHOTS/initial-review-draft/` is historical; the active top-level `SOURCE_QA.json` and Markdown contain the final checked wording.

The exact source SHA256 values are:

- Ordinance PDF: `2ba9073aa06420e41a5dce98fade56278df96729630f5d61d3ab1c910e839eb0` (125,953 bytes).
- EHS PDF: `852801c5ad0056c7b0dde6300e66e86f2e4235ce0efc16471d5210d74aa17ed3` (174,911 bytes).

Both came from the separately preserved Atlas directed access check. This packaging task performed no retrieval. The successful response history, prior DNS failures and historical-digest qualifications remain in the frozen access evidence; source parsing, year labels and HTTP success do not establish current law.

## Offline validation

Use Python 3.11+, Pydantic 2, jsonschema and PyMuPDF 1.28.2:

```sh
PYTHONDONTWRITEBYTECODE=1 python /absolute/path/to/weld-directed-atlas-source-review-2026-09-11/validate_package.py
```

The portable wrapper checks strict status and inventory schemas, every file identity, both original frozen inventories and the unchanged ID mapping. It then invokes the ordinance's existing read-only validator without historical-path checks and the EHS builder's existing **`--verify`** mode. No original paths, network, Git, canonical intake, source edits or legal-currentness promotion are involved. An optional `--package /absolute/path/to/package` locates a copied bundle.
