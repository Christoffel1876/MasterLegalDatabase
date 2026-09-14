---
title: Completed preservation of two reacquired Weld County PDFs
date: "2026-09-11"
status: completed_archived_pending_pipeline
legal_currentness: not_verified
scope: two_source_byte_custody_and_source_review_only
---

Exactly two official Weld PDF originals were archived at `2026-09-11T20:02:02.187060Z`. The raw manifest increased from 38 to 40 records and the manual intake ledger from 39 to 41. Every prior JSONL byte remains an exact prefix. The two source files were written once, all three changed metadata files have exact preimage snapshots, and reconciliation replay required no changes. This is reacquisition of previously recorded sources; historical digest matches alone did not establish locally retained originals.

The ordinance is a selected county zoning amendment instrument, with April 6, 2026 adoption, April 10 publication and April 15 effectiveness **as stated in the source only**. Eleven date records retain the January/February proceedings and the separate 2000 historical recital. Typed names, the printed vote tally and a seal do not certify handwritten execution. This is not the complete consolidated Chapter 23.

The EHS document is a source-stated 2026 environmental-health fee schedule across eleven service groups. All 137 rows preserve 136 printed fee cells and one blank File Review fee cell. The blank is not zero. Native-only page 2/3 headers, a clipped coordinator label, a wrapped Additional Metals label, original spelling and the Board-approved contract exception remain explicit in the unchanged source review. No visible adoption or exact effective date was established.

Actual HTTP completion remains `2026-09-11T19:49:18.706875Z` for the ordinance and `2026-09-11T19:49:19.040662Z` for EHS, separately bound from repository receipt time. Atlas used ordinary direct curl requests with verified TLS. The schema value `manual_official_download` describes curated intake and does not claim a human browser download or an official transfer. Two initial DNS failures were not publisher HTTP denials. This was an Atlas acquisition, not dispatch or completion of Sherlock 010.

`intake-receipt.json` and `source-provenance.final.jsonl` bind the final canonical records, exact source bytes, HTTP custody and complete frozen reviews. `FINAL_VALIDATION.json` is the additive closure inventory. The original `README.md`, `PREPARATION.json`, preview records and preparation validator remain unchanged historical preparation evidence; their old pending wording and 38/39 baseline do not describe the completed transaction. Use this file and the final records for current intake status. The preparation validator deliberately no longer matches the changed live baseline.

Run the portable verifier from any copy of this entire directory with Python, Pydantic 2, jsonschema and PyMuPDF 1.28.2:

```sh
PYTHONDONTWRITEBYTECODE=1 python validate_intake.py
```

To also verify current canonical bytes and all three preimage snapshots:

```sh
PYTHONDONTWRITEBYTECODE=1 python validate_intake.py --repo-root /path/to/MasterLegalDatabase
```

The live check intentionally requires the recorded exact 40/41 state; a later intake needs its own new receipt. The portable check needs no original absolute handoff paths, network or repository outside this folder. It replays all 16,651 native bytes across eight pages, the ordinance's date/source observations and the EHS row, fee and group associations. Source reviews preserve all 71 original audit files unchanged. No source currentness, comprehensive coverage, execution certification or fee recalculation is asserted.

Root's full corpus validation at `2026-09-11T20:03:20Z` exited 1 with the same two inherited LFS-related JSON parse errors: `_CONTROL_PLANE/LOCAL_REVIEW_SUMMARY.json` and `08_County_Authorities/_index.jsonl`. The exact log is frozen in `evidence/verification/corpus-after-weld-directed.log`. Root reported no new corpus issue. This intake's dedicated checks pass independently; the corpus-wide result is not represented as a pass. The preexisting ledger-only executive-order original remains missing and unchanged. No broader regeneration or LFS retry was performed.

The three metadata replacements are individually atomic and snapshotted, not a single cross-file filesystem transaction. No registry, local coverage ledger, semantic queue, RuleUnit, Git or bot action belongs to this preservation operation.
