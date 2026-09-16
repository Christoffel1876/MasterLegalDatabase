---
title: Next source-only lookup — Weld environmental-health fees
prepared_at: 2026-09-11T21:45:14.343573+00:00
status: implementation_proposal_only
legal_currentness: not_verified
answer_safe: false
---

The reviewed Weld schedule is a suitable next addition to the existing two-source lookup. No new acquisition or source QA is needed to propose it. The bounded change would add one typed adapter and its regression tests to `scripts/research_source_lookup.py` and `tests/test_research_source_lookup.py`. It must not modify the frozen review, normal retrieval backend, catalog, ledger or legal status. There is no evidence-based reason to switch to another source for this step.

The exact source ID is **`weld-ehs-fees-2026-atlas-directed`**, owned by **`CO-COUNTY-WELD`**. Its role is a county environmental-health services fee schedule, covering eleven service groups; its URL under an `owts` directory does not make the whole schedule OWTS-only. The official recorded requested/final URL is [Weld's preserved 2026 schedule](https://www.weld.gov/files/sharedassets/public/v/1/departments/health-and-environment/documents/environmental-health/owts/2026-ehs-fee-schedule_final.pdf). This assessment made no request to that URL.

Package root: `research/local_review/weld-directed-atlas-source-review-2026-09-11/`.
The following exact identities were read locally:

| Relative artifact | SHA-256 |
| --- | --- |
| `frozen/ehs/original.pdf` — 174,911 bytes, three pages | `852801c5ad0056c7b0dde6300e66e86f2e4235ce0efc16471d5210d74aa17ed3` |
| `frozen/ehs/SOURCE_QA.json` | `468658770c7f755c00dc844a2a62d1ce8c6afd458ba760a20fedfef2480ee97e` |
| `frozen/ehs/SOURCE_QA.schema.json` | `d634dc0aa26fbea08cfa7b41bf46ada615dd8dcdc08e98207d5a8da3cfd0b545` |
| `frozen/ehs/build_review.py` | `a9411fb842d9cd1d1c7064601c01120121986e03827ee96f7cb1234ed1fe8f65` |
| `frozen/ehs/FINAL_MANIFEST.json` | `30bf267e562f2d6864a1131dd04eed1818098e86f30cbb675f530bc28ffabdc0` |
| `frozen/ehs/ACCESS_RESULT.json` | `540626b8a68e3ddc1b039e7ade2339a310e91ee8d3ae7a887dd72e2f025aeb15` |
| `package-record.json` | `cdb534f7012b5e38d65f7b34cffe69d2cc3c3484cdfbbc0ee6039d883f2238c5` |
| `evidence-manifest.json` | `7928dbd366f95db4eddcfece663d6372265e4e1cc09f72b9cf6349220f1e78b0` |
| `validate_package.py` | `a300ac9a4a4987c081638ecb99087b28dc8c699e54171c7833b8f6909fd9d94c` |
| `package-record.schema.json` | `2f86c1b305aebd2b686a27e81dececca586a70e6d60af93228eef8db72326318` |
| `evidence-manifest.schema.json` | `96890bd6a6bfc3577cad5784a81c737b6dffac6da328d6e3b5d99afee1824d88` |
| `frozen/ehs/FINAL_MANIFEST.schema.json` | `91c0cf6eb8c42d57a8789f2a7f66de13c43a1a7e7f5fcf31870af3d09bab69d7` |

1. **Add one explicit source branch with a dedicated result model.** Keep the existing exact-source allowlist; add only this EHS ID and reject its sibling ordinance ID. Reuse the current safe path, phrase matching, Markdown escaping, refusal and before/after hashing patterns. EHS needs `label_spans[]`, optional `fee_span`/fee text, `fee_cell_status`, row `note_spans[]`, and separate page context. It cannot safely reuse the Grand Junction row model's mandatory `fee: str`. Preserve exact native strings and half-open UTF-8 spans; do not parse amounts into computed numbers. Return at most 137 rows, county ownership, PDF/review/source provenance, all twelve review qualifications and `answer_safe=false`, `legal_currentness=not_verified`. Extend the existing `--source-id … --query …` / `--list-rows` interface; these are proposed future commands, currently unsupported for this ID.

2. **Verify the frozen evidence before extracting rows.** Pin the identities above plus the two outer schemas and the frozen inventory schema. Check the closed package inventory and every referenced asset before any subprocess, then run only the pinned EHS `build_review.py --verify` in an isolated `python -I -B` subprocess with a timeout, and recheck hashes afterward. Parse its logging-prefixed JSON deliberately and require passed status, three pages, 137 rows, eleven groups, 7,367 native bytes, 313 lines, 136 printed fee cells and one blank. Use the recorded PyMuPDF 1.28.2 extraction environment. The existing verifier uses Python `assert`; do not run it with `-O`, and test that inherited `PYTHONOPTIMIZE` cannot disable checks. Unlike the outer wrapper's ordinary `-B` children, a direct EHS `-I -B` call avoids executing the unrelated ordinance verifier and avoids untrusted module-path/environment imports. Keep the package's read-only verifier unchanged. A validator timeout, missing PDF/native file, changed schema or source ID, unlisted file, symlink or any binding failure must fail closed. This is an implementation prerequisite, not a missing-source blocker.

3. **Carry the complete row and context relationships.** The existing JSON has 137 rows with group/label/fee links and an exhaustive native partition. Group counts are Body Art 7; Child Care 8; Food Protection 32; Institution 4; Miscellaneous 12; OWTS 20; Methamphetamine 2; Bacteriological Assessment 5; Chemical Assessment 41; Miscellaneous Laboratory 3; Oil and Gas Laboratory 3. Their sum is 137. Source-group IDs and exact labels are authoritative; do not merge similarly named services or amounts. The label of `EHS-R131` spans `P3-L085` and `P3-L086`; both belong to one Additional Metals row. `EHS-R084` carries row note `P2-L073`. Page-3 market-rate note `P3-L088`/`P3-L089` and contract exception `P3-L111` are not row notes in the frozen schema: return them as separately labeled page context, including for relevant page-3 row matches, rather than silently dropping them or inventing applicability. A note-only query must not imply the note is absent merely because no fee row matched. Preserve `header_visible`: page 1 true, pages 2/3 false, although native headers are present on all three pages. Do not describe hidden native header text as visibly repeated headings.

4. **Keep the three clocks and legal dates distinct.** `ACCESS_RESULT.json`, event `ATLAS-WELD-04`, records successful verified-TLS HTTP completion at **2026-09-11T19:49:19.040662Z**, matching the PDF SHA, with no redirects. Review time is **2026-09-11T19:55:05.808484Z**. If the adapter reports repository custody, use the separate frozen `research/local_review/weld-directed-intake-2026-09-11/intake-receipt.json` (SHA `13e1de8f33a6af1cd36a70d74c9b4275e07c2bcc0a832e53c100e55e3a0dcdaa`): its matching source row records **2026-09-11T20:02:02.187060Z**, and archive status remains `archived_pending_pipeline`. The intake was an Atlas-initiated ordinary curl download followed by curation, not a human-browser handoff. Do not read the frozen preparation's simulated preview time or substitute whole-transaction completion time. Pin the receipt and referenced final record if used, rather than the mutable current raw manifest. The combined source-review package's earlier pending-intake label remains immutable history. The printed year is only `source_year_assertion: "2026"`; adoption/effective dates remain null, with no adopting resolution or later-amendment chain verified. HTTP success and byte preservation do not resolve current law.

5. **Require focused regressions for every material exception.** Exhaustively compare all 137 output associations with the frozen JSON and original native slices, then check the following cases before release. Preserve existing Grand Junction and Greeley outputs, refusal behavior and read-only execution from another working directory. Run corruptions for wrong source/page/group, swapped same-price cells, altered text/offsets, missing conditions, blank/zero coercion, dropped page notes and wrong authority/date assertions. Check bounded output, safe Markdown, no matching row versus absence, unsupported sibling IDs, verifier failure/timeout, optimization environment and unchanged package bytes. Do not add legal answers, totals or a broader fee-source search.

| Regression target | Required behavior |
| --- | --- |
| `EHS-R062` File Review Fees | `fee=null`, `visibly_blank`; retain Appendix 5-D / Chapter 5 reference. Never show zero. |
| `EHS-R016`, `EHS-R028` | Preserve printed `$0.00` and their school/nonprofit/mobile conditions and CRS citation, distinct from the blank row. |
| `EHS-R033` coordinator | Preserve clipped `if applicab` and `$100.00/hour`; do not finish the word or condition. Keep `Temproary` on R032. |
| R003; R036/R038/R039 | Keep `$100` application plus hourly language; preserve separate `$895/$775/$620` caps. No calculation. |
| R045/R046/R047 | Keep `<25` and `>25` with their separate prices. No invented exactly-25 tier. |
| R050/R051 | Preserve different reciprocal licensing/permitting labels and `$100` versus `$50`. |
| R060/R061 | Preserve the lead-investigation one-hour minimum and fax `$5.00+` / additional-page condition. |
| R084/R085 and `P2-L073` | `$400.00` covers up to four hours; excess-time note remains with R084; `$100.00/hour` remains a separate row. |
| R086 | `3 x Stated Fee` remains under bacteriological assessment, not a multiplier for all groups. |
| R080/R081/R082/R089/R090 | Distinguish with/without water sample `$248/$200`, OWTS `$48`, and bacteriological `$52.50/$54.50`. |
| R105/R107/R132 | Preserve `Market Rate`, not zero, an estimate or a fabricated amount. |
| R131 and page-3 notes | Preserve both wrapped label spans and one `$23.00` fee; keep unlisted-service market-rate and Board-approved-contract exceptions separate. |
| R007/R123 | Preserve Body Art `$13.00` versus Chemical Assessment `$14.00` spore tests. |

This plan inspected already frozen records, source identities and code; it did not perform new visual QA, re-extract PDFs, rerun source verifiers, execute a lookup implementation, access public sources or modify production evidence. No current-law blocker was resolved or represented as resolved.
