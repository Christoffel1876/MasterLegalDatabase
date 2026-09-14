---
title: Selective integration of the 2026 CRS passage lookup
prepared: 2026-09-12
status: selectively_integrated_pending_root_full_suite
legal_currentness: not_verified
---

# Integration scope

This audit binds the new `scripts/crs_source_lookup.py`, its focused tests and
`docs/CRS_SOURCE_LOOKUP.md`. The command reuses the existing, unchanged repository
source package at
`research/local_review/crs-2026-title1-source-review-2026-09-12/`.
There is no duplicate production source copy and no change to the 2025 metadata
prototype, raw archive, catalog, index or ledger.

The production lookup differs from the accepted handoff prototype only by adding
the repository-relative source location and using it as the CLI default. This
allows execution outside the checkout. The tests use the repository import and
source path, plus six integration regressions covering that default and five
actual outside-checkout CLI invocations. The exact diffs are retained here.

`prototype-subset/` contains eight unchanged historical preparation artifacts.
Its copied `MANIFEST.json` describes the **full** frozen handoff and is retained
as evidence, not as a claim that the entire handoff is present in this subset.
`VERIFICATION.json` lists every omitted prototype path. The source bytes are
already preserved in the separately verified repository source packet; they are
not duplicated in this audit. The complete original handoff remains untouched.

The three saved matched examples preserve six whole source paragraphs and all
19 selected native regions, including section 102(1)'s page 4-to-5 continuation
and section 103's page 6 notes. Two refusal examples contain no source passages.
The source acquisition timestamps, review timestamp, printed edition and
historical date statements remain separate. Legal currentness and the prior
2025 original-source custody gap are not resolved by this integration.

`VERIFICATION.json` is a strict typed receipt for the measured focused test run,
its branch-inclusive coverage, all five real CLI calls from an unrelated
temporary directory, exact code/source bindings and the prototype subset.
`RESULT.schema.json` exports the response contract. The schema does not replace
the Pydantic association checks or the pinned original semantic verifier.

Run the read-only audit and source-response replay from the repository root:

```sh
python docs/audits/FOUR_HOUR_RUN_2026-09-12/CRS_LOOKUP/verify_integration.py --root .
```

The verifier checks the audit's closed inventory and all referenced implementation
and source files, then replays the three source selections and two refusals. It
does not rerun pytest, contact a source, modify a file or claim full-suite success.
The parent task owns the subsequent repository-wide test and commit decisions.
