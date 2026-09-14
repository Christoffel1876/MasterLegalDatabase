---
title: El Paso intake host-policy failure and additive recovery preparation
date: "2026-09-12"
status: recovery_prepared_not_executed
legal_currentness: not_verified
answer_safe: false
---

# Observed failure

The root's authorized apply preserved thirteen exact originals and appended the raw manifest from 46 to 59 records. It stopped before changing the 47-row ledger or report because the existing reconciliation validator rejected `epc-assets.elpasoco.com`.

This exposed a missed implementation check: `ManualSourceIntakeRecord` and the transaction's `NewRecord` validate record structure but do not run the official-host predicate. The original initial preflight reconciled the old records only. Nine new asset-host URLs first reached the stricter validator after the raw append. The original fixture URLs did not exercise this difference. The failure is not evidence of corrupt source bytes.

The original frozen transaction, reports, source PDFs, append suffix and intent remain unchanged. The original actual repository receipt time is **2026-09-12T22:59:48.795762Z**. The recovery must retain that time and every intake ID.

# Exact evidence and repair scope

`DIAGNOSIS.json` binds all thirteen source IDs/URLs/hashes, the exact interrupted manifest/ledger/report copies, and nine previously rejected URLs to retained official anchors. Three official parent HTML bodies support the asset host: planning and development, clerk ordinances, and health-board regulations. The three inherited LDC URLs still have no fresh anchor; they already passed the existing host policy. Approval of the asset host does not repair inherited referral or acquisition gaps.

Root added **only** `epc-assets.elpasoco.com` to the existing host set. No wildcard, suffix rule, extra subdomain or unrelated host is accepted. The old constants bytes are retained from root's preimage snapshot; the later observed constants bytes are separately identified. The wrapper pins the reviewed new constants SHA, unchanged actual reconciliation code/validator, frozen original transaction SHA and exact original intent SHA.

`replay.py` is additive. Before it invokes the unchanged transaction, it calls the actual `_validate_reconciliation_record` on every final record, then the original full preflight. The original transaction already recognizes the exact after/before/before state. It verifies existing originals and the already-appended raw suffix, appends the same suffix to the old ledger, writes the intended report, and checks reconciliation. It cannot invent replacement receipt times or silently repair conflicting bytes.

No real replay was executed while preparing this package. Root owns review and execution. The original package's historical `prepared_not_applied` receipt is not rewritten to conceal the subsequently interrupted apply.

# Root commands

First validate only this frozen recovery evidence:

```sh
/private/tmp/geode-status-venv/bin/python -I -B "/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-12/el-paso-intake-recovery/validate_recovery.py"
```

Then root may inspect the actual interrupted state with the default read-only replay preflight:

```sh
/private/tmp/geode-status-venv/bin/python -I -B "/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-12/el-paso-intake-recovery/replay.py"
```

After approval, root alone executes the same command with `--apply`; completed state is checked with `--verify`. No other intake writer should run concurrently. The transaction lock is local to these invocations, not a repository-wide lock. Process interruption and deterministic replay are tested; power-loss/filesystem durability is not certified, and the original transaction does not fsync directory entries.

# Offline validation scope

Eight focused tests use all thirteen actual approved templates and their unchanged received PDF bytes with a synthetic 46/47-row old baseline. They reproduce the unauthorized real-host condition and require rejection before any write. They also exercise authorized after/before/before replay, exact prefixes and original timestamps, repeated no-op application, corrupted archived bytes, altered intent identity, changed hash pins, symlinks, directories and missing files. Fixture tests never apply against the actual repository.

The package inventory excludes only itself and isolated `_test_runs/` scratch files. Acquisition times, full-table review, translation equivalence and legal currentness remain unverified as previously qualified. This repair changes source-host acceptance and completes custody reconciliation only; it does not create legal rule units or promote coverage or answer safety.
