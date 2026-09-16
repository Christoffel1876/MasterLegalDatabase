---
title: Mesa County and Grand Junction — three-source archival intake
date: "2026-09-11"
status: completed_archived_pending_pipeline
legal_currentness: not_verified
---

Exactly three official PDF originals are preserved: the 219-page Mesa County land-development code edition, Grand Junction's 29-page Ordinance 5269 and its two-page fire-prevention service fee schedule. County ownership uses layer 08; city ownership uses layer 10. Shared county building administration and the separate Rural Fire Protection District do not merge legal authorities. No district instrument, complete municipal-code corpus or RuleUnit was created.

The Mesa original has the same digest as 41 historical download records across category aliases. This is recovery of those exact bytes, not a newly discovered edition or 41 independent documents. Its cover identifies a 2020 code with amendment dates through April 23, 2024. The retained catalog separately lists proposed 2026 revisions and future hearings. Those catalog labels do not establish subsequent adoption or current completeness. The two city PDFs have no digest match in the compared historical download manifest; that limited result does not prove new legal content or corpus-wide novelty.

Ordinance 5269 states adoption of the 2024 IFC with local amendments to municipal Chapter 15.44. Introduction, passage, two publications, certification and effectiveness are separately recorded source statements. Signatures and seal were observed in the discovery review; identity, execution and current applicability were not certified. The city fee schedule has no observed printed edition, adoption or effective date. Its alternative catalog fee endpoint, complete adoption chain and district applicability remain unresolved. Fees were not recalculated or promoted into rules.

The frozen discovery contains 13 events at 12 requested URLs: ten HTTP 200 responses, two redirects and one initial DNS failure. This intake made no new requests. Actual HTTP times remain in each event/source record; actual repository receipt time is separately assigned during the three-file preservation. Curated `manual_official_download` means an Atlas direct download, not a claim of human browser activity or official transfer.

The original discovery's complete 356-file identity inventory is retained. Of those, 350 files are copied exactly. Six HTTP header files are represented by separately named public derivatives removing only three Set-Cookie lines each. Original header hashes, sizes and local custody locations remain recorded; the local handoff originals are unchanged. The public package cannot reconstruct the intentionally omitted cookie values, and the original discovery verifier should not be run directly against this derived subset. Use this package's validator, which resolves that explicit custody distinction and checks all other frozen bytes, actual HTML referrals, events and all 250 native page extractions.

Discovery visually inspected eight pages: Mesa pages 1–3, Ordinance 5269 pages 1, 28 and 29, and both fee pages. Intake independently checked each document's first-page title and scope. The other 242 pages were not visually reviewed in discovery. Native evidence covers every page, but full substantive transcription, table associations, exceptions, cross-references and currentness remain pending. Structural page counts do not certify a complete code or faithful semantic extraction.

Before preservation, all 544 ordinary raw files were size-screened; none matched these three PDF sizes. Exact current raw-manifest and manual-ledger comparisons found no ID, URL or digest collision. Source IDs were checked against the local source registries and coverage ledger. The raw manifest and manual ledger increase from 40/41 to 43/44 with exact old byte prefixes preserved, and each of the three changed metadata files has its own exact preimage snapshot. Original PDFs are written once. Individual replacements are atomic; this is not a single cross-file filesystem transaction. A no-change reconciliation replay is required by the final receipt.

`PREPARATION.json` is the immutable before-append assessment. `INTAKE_RECEIPT.json`, `records.final.jsonl` and `sources.final.jsonl` identify the completed transaction. The full-corpus result is recorded separately in the final receipt and exact stdout/stderr files. The expected two inherited LFS-related parse errors in `_CONTROL_PLANE/LOCAL_REVIEW_SUMMARY.json` and `08_County_Authorities/_index.jsonl` are not a transaction-specific failure or a whole-corpus pass. No regeneration or LFS retry is included. The preexisting missing ledger-only executive-order original remains unchanged.

Portable verification requires Python, Pydantic 2, jsonschema and PyMuPDF 1.28.2:

```sh
PYTHONDONTWRITEBYTECODE=1 python validate_intake.py
```

To additionally check the exact live 43/44 canonical state and snapshots:

```sh
PYTHONDONTWRITEBYTECODE=1 python validate_intake.py --repo-root /path/to/MasterLegalDatabase
```

The portable check requires no original absolute handoff paths. A later intake may change the live baseline and needs its own new receipt. This bounded operation performs no source-currentness certification, coverage or semantic promotion, source-registry changes, Git action or bot dispatch.
