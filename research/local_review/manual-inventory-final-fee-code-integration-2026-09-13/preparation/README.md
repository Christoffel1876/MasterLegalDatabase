---
status: prepared_tested_not_installed
reviewer: Plato
scope: final_two_review_joins_one_authority_join
legal_currentness: not_verified
answer_safe: false
---

This proposal updates the manual review inventory from **69 originals / 33 mapped reviews / 36 unmapped** to **70 / 35 / 35**. It adds exactly the accepted Gunnison sixteen-page building-code resolution review and the accepted Chaffee two-page planning-fee review. The single newly archived Chaffee fee original gains its exact County authority/custody mapping. No lookup, source text, archive, intake runtime, rule or current-law change is included.

All 69 previous authority joins and 33 review joins remain exact. All previous source rows remain exact except the formerly unknown Gunnison building-code review/status. The new fee row preserves its actual repository receipt at **2026-09-13T17:02:09.370066Z**, separately from observed HTTP completion at **16:44:33.133961Z** and printed date claims. Both issuers are counties; no municipal or service-provider identity is inferred.

The module diff contains only two exact schema allowlist entries. Proposed tests retain all historical preservation checks and add full-count, scope, condition, source-hash/authority/schema/alias refusal and rehashed-currentness refusal cases. Gunnison's empty native text, original OCR, 132 blocks, 27 design associations and three strikes remain qualified source evidence. Chaffee's 49 rows/10 categories, cross-page continuation, refund/rental/hourly/escrow notes and printed dates remain complete. The original QA's historical custody wording is retained, with the acceptance's one-fee-GET/earlier A003 HTTP 302 clarification carried in the review note.

`PREIMAGE_RECEIPT.json` preserves the seven installed 69/33 inventory/module/test predecessors. The fee intake had already made the raw manifest 70 records, so the prior inventory was expected to be temporarily stale; that condition was captured explicitly. `history/before-custody-clarification/` preserves the first successful draft and 142-test run. The final run passed 142 tests with 99.25373134328358% branch-inclusive module coverage and includes the explicit acquisition-qualification assertion. `STAGED_TEST_RUN.json`, `focused-tests.log` and `coverage.json` record the final actual execution in a removed private copy, without production writes.

`PREPARATION.json` binds each exact target, source review, schema, root acceptance, actual intake receipt and raw manifest. The companion schema is unchanged. Root must review and authorize installation separately; this folder does not assert an installation or maintained full-suite result.

```sh
PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-status-venv/bin/python -B verify_preparation.py
PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-status-venv/bin/python -B verify_preparation.py \
  --repository '/Users/mcoors/Documents/Project Geode/MasterLegalDatabase'
```

The first command checks the closed proposal and exact preservation offline. The second additionally replays the proposed inventory against current canonical evidence without installing it. Do not rerun write-once preparation or test-receipt builders over a frozen packet. No public requests or source review claims were added by this integration.
