---
title: Manual intake custody reconciliation
date: 2026-09-11
status: reconciled_pending_pipeline
legal_currentness: not_verified
audit_sha256: 632fdd9d931088aad71db81c8e4ce0fdab5d85a602835a210b1852b0e29cc772
---

# Manual intake custody reconciliation

Appended the 11 verified Larimer archive records missing from the control ledger. The prior two ledger records and their custody wording remain unchanged. The resulting ledger has **13 custody records**, with **12 local originals hash/size verified**. The existing EO-2019-007 record is ledger-only and its raw PDF is missing locally.

All 13 records remain `archived_pending_pipeline`. The 11 Larimer records remain `received_review_package`; reconciliation does not turn receipt from a review package into an official-source download. The 12-record raw manifest and every original were left byte-identical.

## Commands

The default is a read-only preview:

```bash
python -m geode.pipeline.manual_source_intake --root . --reconcile --json
python -m geode.pipeline.manual_source_intake --root . --reconcile --apply --json
```

The preview proposed 11 additions. Apply appended 11 once. A repeated apply returned `no_change`, preserved ledger/report bytes and created no additional snapshots.

## Validation

51 focused tests passed, with 96% coverage of `geode.pipeline.manual_source_intake`. Tests cover identity/path/digest/custody conflicts, malformed metadata, missing or changed originals, symlinks, dry-run behavior, stale input detection, exact custody preservation, repeated calls and recovery after an interrupted report write.

Existing ledger/report bytes were snapshotted at:

- `_SNAPSHOTS/snapshot_2026-09-11T182350799528Z/_CONTROL_PLANE/MANUAL_SOURCE_INTAKE_LEDGER.jsonl` — SHA-256 `b78ce6d847f1e8bd49bdf1bd3d8dd22b75e3674b22b502dcdc5e30d27cdafe50`.
- `_SNAPSHOTS/snapshot_2026-09-11T182350803605Z/_CONTROL_PLANE/MANUAL_SOURCE_INTAKE_REPORT.json` — SHA-256 `4e4a44f96ec0468accd008d3992bc788da8607b67137fe4d8b1a00b4cb914399`.

The detailed JSON records input/output hashes, all 12 verified source paths, protected controls, commands and results.

## Limits

- The control ledger has 13 custody records but only 12 local originals verified. Historical EO-2019-007 is ledger-only and its raw file is unavailable; it was retained unchanged rather than removed or certified.
- All 13 statuses remain archived_pending_pipeline. Eleven Larimer records retain received_review_package; their received_at is repository intake time and upstream acquisition remains supplied claims.
- Hash/size verification establishes local byte identity, not original delivery, legal currentness, transcription accuracy, coverage completeness, or a pipeline rebuild.
- Reconciliation writes the ledger and report as separately atomic, snapshotted operations. An interruption between them can leave a stale report; an idempotent rerun repairs it without duplicating ledger records. No raw/source manifest, blocked-download queue, ownership registry or coverage ledger is written.
