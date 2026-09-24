---
title: Required post-intake inventory integration
status: pending-actual-apply-and-root-review
---

The fixed transaction includes the manual intake report:74 raw originals/75 ledger entries.
The derived local-review inventory must be separately refreshed to74 originals/38 linked
reviews/36 unmapped. No source-role review becomes a full inventory review automatically.

Root sequence:

1. Preserve/install this reviewed packet at the final research evidence path. Verify its closure.
2. Apply the new fixed transaction and run its `--verify` immediately while all captured guards
   remain unchanged. Preserve that actual receipt. No original, ledger or source clock is
   created by this preparation.
3. Snapshot the current inventory join-plan, module/tests if necessary, and all generated
   companions. Keep all71 authority joins and38 review joins exactly. Set the join-plan's
   `manual_manifest` hash/size to the actual appended74-row bytes.
4. Append exactly3 `AuthorityJoin` entries, each pointing to the installed PREPARATION JSON
   and its exact preparation SHA/size. Use JSON pointers shown below. `verified_http` stays
   null; no `ReviewJoin` or schema allowlist addition. Update prepared_at to integration time.
5. Run the existing maintained writer then checker, from the repository root:
   `python -B -m geode.pipeline.manual_review_inventory --root . --write`
   `python -B -m geode.pipeline.manual_review_inventory --root . --check`
6. Verify all previous71 source rows (except global input-manifest pin where embedded) and38
   review bindings retain their exact scoped content; only3 new rows are unreviewed. Update
   only current live-count tests; historical checkpoint assertions remain historical.

| Record | Authority | Provenance prefix |
|---|---|---|
|custer-right-to-ranch-farm-resolution-98-14-shstate03|CO-COUNTY-CUSTER|/provenance/0|
|delta-land-use-adoption-resolution-2021-r-001-shstate03|CO-COUNTY-DELTA|/provenance/1|
|delta-land-use-code-2024-label-shstate03|CO-COUNTY-DELTA|/provenance/2|

For each prefixP, `sha_pointer=P/source/sha256`, `source_id_pointer=P/source_id`,
`authority_pointer=P/authority_id`. Reported-acquisition pointers: `P/requested_url_reported`,
`P/final_url_reported`, `P/http_status_reported`, `P/reported_reserved_at`,
`P/reported_finished_at`, `P/verified_original_acquired_at`.
Role pointers: `P/physical_pages`, `P/originally_reported_pages`, `P/referral_kind`.
Qualification pointers: `P/limitations`, `P/legal_currentness`,
`P/original_transport_witnessed_by_this_preparer`, `P/private_header_contents_included`.
The final installed PREPARATION path must be the actual root-approved location, not guessed.

The custody transaction deliberately pins the old inventory/join-plan among its preapply
unrelated-state guards. After this separately authorized inventory integration, rerunning its
live preflight/verify will refuse the changed guard; preserve the successful pre-integration
execution receipt and use the inventory's own exact post-integration checks. Do not weaken
frozen transaction guards to make later evolved repository state appear identical.
