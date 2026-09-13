---
title: Prepared English El Paso EHS source lookup addition
status: prepared_not_installed
source_id: el-paso-boh-ehs-fees-sd011
legal_currentness: not_verified
---

This handoff proposes one source-only lookup adapter and one inventory review join. No production file, original PDF, review evidence, canonical intake, scheduler or normal query backend was changed. The source has 65 service/fee rows in seven groups, 37 context records and 8,060 unchanged native bytes across five English pages.

`proposed/` contains complete proposed files; `PROPOSED.patch` expresses the same changes against the exact production preimages recorded in `BASELINE.json`. Installation is a separate root action after independent review. Reject a stale baseline rather than overwriting later work. The proposal adds the exact accepted English schema as `checked_tables` and appends one review join (21 to 22), preserving all prior authority mappings and review entries. The immutable source review lacks inline source/authority IDs; its exact source SHA, copied canonical row and accepted custody identify this explicit join. The lookup also checks the live canonical row and original PDF; a catalog name alone is insufficient.

The adapter pins the acceptance receipt and the closed 42-file source QA package, runs its pinned verifier in an isolated Python subprocess, checks the package again, then streams the current raw manifest to require exactly one byte-identical selected row. It verifies the actual canonical PDF. Output retains source, candidate, review, acceptance, native-page and image identities; exact native spans; group continuation; table cells and rectangles; and all source context. Verification has no network path.

All 37 contexts accompany each successful response, including no matching fee and context-only results. A context/caption match does not invent a fee row. Source quirks remain: two years in R031, explicit 2024 in R032, two stacked event fees in R057/R058, the full-menu omission of “for”, R056's statutory reference, the carried OWTS heading, the new-permit asterisk, and the unmatched closing quotation in definition 7. The Section 2 civil-penalty exception, $100 per day limit, per-visit note and no-fee investigations remain explicit. No arithmetic or applicability conclusion is made.

Printed approval October 25, 2023 and effective January 1, 2024 remain source assertions. Repository receipt on September 12, 2026 is separate from the original supplier's unverified HTTP acquisition claim. Current-law requests are refused before evidence loading; every other response remains `answer_safe=false` and `legal_currentness=not_verified`. The separate Spanish document was neither opened nor compared and is unsupported.

Run the draft from anywhere with an explicit repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-status-venv/bin/python -B \
  '/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-12/el-paso-ehs-lookup-integration/proposed/research_source_lookup.py' \
  --root '/Users/mcoors/Documents/Project Geode/MasterLegalDatabase' \
  --source-id el-paso-boh-ehs-fees-sd011 --query 'OWTS New Permit' --format json
```

Use `--list-rows` for the entire 65-row schedule. `--query 'complaint investigations'` returns the relevant context with no fee row. `--mode current-law` returns the existing refusal exit code 2. Evidence failure returns 1. Source reporting returns 0 and does not imply legal verification.

Validation commands:

```sh
PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-status-venv/bin/python -I -B \
  '/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-12/el-paso-ehs-lookup-integration/verify_preparation.py'

cd '/Users/mcoors/Documents/Project Geode'
PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-status-venv/bin/python -B -m pytest \
  handoffs/run-2026-09-12/el-paso-ehs-lookup-integration/test_ehs_lookup.py \
  -q -p no:cacheprovider
```

The handoff's custody verification is portable. Behavioral tests intentionally depend on the already accepted repository evidence and local Python dependencies. The 12 saved legacy fixtures contain the complete JSON and Markdown outputs of the six previously supported sources; the focused cases compare these byte for byte. The original test log is retained, including one subsequently fixed fixture class-identity error; final results are separate. Root must run the full suite after installation and separately regenerate the inventory from the validated proposed join plan. Neither action is claimed here.

The complete prepared inventory companions are under `proposed/inventory/`; their exact predecessor is retained under `_SNAPSHOTS/BEFORE_EL_PASO_EHS_2026-09-13`. They contain the same 61 source records, with 22 explicit review links and 39 unknown review statuses. `proposed/test_manual_review_inventory.py` updates the three affected historical comparisons and adds a full 61-source preservation test for this one join. Its helper removes only the exact SHA-checked EHS review when comparing earlier snapshots; it preserves every other field.

`verify_proposed_inventory_cases.py` runs the four affected cases against actual repository evidence, redirecting only the exact plan and new snapshot paths in memory. It does not install files or write repository output. Root must install all prepared inventory companions and their predecessor snapshot together, then run the unmodified test file from its normal production location. `INVENTORY_TEST_RESULTS.log` records the bounded prepared-state test, separate from a future full suite.

Installation-ready lookup tests are `proposed/test_el_paso_ehs_native_lookup.py`, targeting `tests/test_el_paso_ehs_native_lookup.py`. Copy `proposed/test-fixtures/el_paso_ehs_native_lookup/` to `tests/fixtures/el_paso_ehs_native_lookup/`. The installed test imports the maintained `scripts.research_source_lookup` module and derives ROOT from its normal tests path; it has no handoff path dependency. It contains the 51 lookup cases from the handoff test; the separate inventory preservation test belongs in `proposed/test_manual_review_inventory.py`. Copy that file to `tests/test_manual_review_inventory.py`. Copy the proposed inventory outputs and predecessor snapshot under `research/local_review/manual-source-review-inventory-2026-09-11/`, together with the proposed join plan. Full production-suite execution remains a root integration step.

Final focused adapter result: 52 cases passed, including the handoff-only inventory join check. New EHS-block branch-inclusive coverage is 96.03% (224/230 statements and 66/72 branches); this is the explicit new adapter block, not the entire preexisting multi-source module. Four updated inventory integration cases passed against the prepared path substitutions. An independent reviewer confirmed the Section 2 correction, related amount/citation boundaries and unchanged earlier-source implementation. Frozen historical logs retain earlier failures and superseded test iterations.
