---
title: Two-source manual inventory integration preparation
status: preliminary_pending_actual_intake
legal_currentness: not_verified
---

This handoff prepares metadata-only inventory joins for the accepted Douglas County environmental-health schedule and City of Pueblo planning-fee schedule. It does not install production changes, append intake records, expose a lookup adapter or claim current law.

The exact prior inventory, join plan, module, tests and intake streams are retained in `preimages/`. The installation snapshot is prepared under `proposed/inventory/_SNAPSHOTS/BEFORE_FINAL_TWO_2026-09-13/`. The prior state contains 61 original sources, 22 explicit review mappings and 39 sources without mapped reviews. After both separately authorized intakes actually complete, the proposed state will contain 63 originals, 24 review mappings and the same 39 unmapped sources. Until that actual receipt is available, those latter counts are a plan, not a completed inventory.

`PRELIMINARY.json` is strictly schema-validated and intentionally has null intake IDs/times. It binds both immutable reviews, exported schemas, root acceptance receipts, source hashes, historical review aliases and proposed canonical identities:

- `douglas-ehs-fees-atlas-directed`: `CO-COUNTY-DOUGLAS`, county layer 08. The county-issued source separately labels fee-setting authority under county and state captions. Those captions do not turn its issuer into a state department. The review preserves 44 rows on one physical page, seven contexts, two blank penalty fee cells and the printed county/state date distinctions.
- `pueblo-planning-fees-atlas-directed`: `CO-MUNICIPAL-PUEBLO`, municipality layer 10. This is the City of Pueblo, separate from Pueblo County. The review preserves four physical pages, 44 physical application rows, 43 nested entries and 4,923 native bytes. The printed `2-13-26` remains a source date without a verified legal-effect label.

Only the two exact reviewed schema hashes are added to the proposed inventory module's allowlist. Authority, original hash, actual repository receipt and verified HTTP acquisition will be bound to the final retained intake provenance. All existing authority, custody and review joins must remain unchanged; only the manual-manifest reference and two new entries in each join list will change.

The old reviews' pending-intake and not-enrolled statements remain unchanged historical evidence. The new inventory record will identify actual later receipt separately. No currentness, monitoring, applicability, translation or fee arithmetic conclusion is implied. Original blank fees remain null, never zero.

`proposed/test_manual_review_inventory.py` includes the historical count/prefix adjustments and seven new preservation/refusal cases. Final inventory companions, exact transaction bindings and test results will be added only after actual intake receipt validation. Root alone controls any canonical apply and production installation.
