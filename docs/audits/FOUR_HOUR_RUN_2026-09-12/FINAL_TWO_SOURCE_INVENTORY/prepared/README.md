---
title: Douglas County and City of Pueblo inventory integration proposal
status: prepared_tested_not_installed
legal_currentness: not_verified
---

This closed handoff prepares metadata-only inventory joins after the two actual guarded intakes. Root recorded repository receipt at **2026-09-13 01:38:28.176844 UTC**, separately from the earlier official HTTP acquisitions. The proposal has **63 original sources, 24 explicit review mappings and 39 unmapped sources**. All prior 61 source rows, 61 authority joins and 22 review joins remain unchanged. No production file was installed by this preparation.

The two mappings remain distinct:

- `douglas-ehs-fees-atlas-directed`: Douglas County, layer 08. Its one-page county-issued schedule has 44 rows, seven contexts, separate county/state captions and two blank penalty-fee cells. The state caption does not create a second state-issued source. Blank fees are null, not zero; source dates and amounts remain as recorded.
- `pueblo-planning-fees-atlas-directed`: City of Pueblo, layer 10. Its four-page schedule has 44 physical application rows and 43 nested entries, including 28 fee bullets and 15 paired subcategories. The printed `2-13-26` is not certified as an adoption or effective date. Pueblo County is a different authority.

Only the two exact accepted schema hashes are added to the proposed module allowlist. Actual source hashes, custody, government identities, review aliases, scope and qualifications are carried into the inventory. Earlier pending-intake and monitoring statements remain unchanged historical evidence. No source text, fee calculation, lookup adapter, current-law claim, coverage promotion or monitor enrollment is added.

Installable files are `proposed/manual_review_inventory.py`, `proposed/test_manual_review_inventory.py`, `proposed/join-plan.json`, and the three companions in `proposed/inventory/`. The latter directory also contains the exact four-file `BEFORE_FINAL_TWO_2026-09-13` snapshot for the existing inventory package. Root alone controls installation. The inventory module adds exactly two allowlist entries; tests also repair a historical Springs negative-test selection so it explicitly selects its intended source instead of whichever source happens to be last.

The proposed test module passed **79 cases in 18.24 seconds**, with **99.25% branch-inclusive module coverage**. Tests cover old-source preservation, explicit county/city ownership, source and alias mismatches, unlisted schema refusal, blank fees and nested row scope. The first successful run measured coverage only after import; its incomplete measurement is retained under `historical/pre-import-coverage/`. The final measurement starts before model and allowlist import. No full-suite or installation result is claimed here.

`PRELIMINARY.json` and its earlier null intake fields remain frozen historical planning evidence. `FINAL.json`, `ACTUAL_BINDING_RESULT.json` and the unchanged actual receipt copies in `custody/` record the completed intake and tested proposal. The final manifest binds every payload. Both verification modes are read-only:

```sh
PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-status-venv/bin/python -B \
  '/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-12/final-two-source-inventory/verify_preparation.py'

PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-status-venv/bin/python -B \
  '/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-12/final-two-source-inventory/verify_preparation.py' \
  --root '/Users/mcoors/Documents/Project Geode/MasterLegalDatabase'
```

The first command verifies the portable closed bundle, schemas and preservation claims. The second additionally checks the exact recorded repository inputs, including the actual intake receipt, original PDFs, acquisition events and accepted reviews. A later append to a pinned full manifest requires a new inventory proposal; this handoff does not silently revise its baseline. Builders and test drivers are preserved for reproducibility and are not part of read-only verification.
