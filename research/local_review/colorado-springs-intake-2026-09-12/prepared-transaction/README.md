---
title: "Colorado Springs two-source intake transaction"
status: PREPARED_NOT_APPLIED
prepared_date: 2026-09-12
legal_currentness: not_verified
---

# Prepared two-source transaction

This package is ready for review. No canonical apply was performed while preparing it. It preserves the approved 66-file preparation exactly under `evidence/preparation/`; that preparation's manifest SHA-256 is `5b0e8cf0cd835d793c99ae1c32f50d287e9760ae854fa8fa69e911c1b6b21142`.

The two sources are City of Colorado Springs Fire Department documents, routed to `10_Municipal_Authorities` and `CO-MUNICIPAL-COLORADO_SPRINGS`:

| Source ID | Received document | Pages | Original bytes | SHA-256 |
|---|---|---:|---:|---|
| `colorado-springs-code-services-fees-2015-atlas-directed` | Code Services fee schedule with visible 2015 title | 7 | 162,682 | `555570a62a5a557a824d1bcf3ecd2e60d57e48d19ea401f06a2e5b7ccb177e56` |
| `colorado-springs-construction-fees-atlas-directed` | Construction Services fee schedule, printed “Effective 07/01/2026” | 7 | 258,393 | `e35de501a011fe55f03140bf91aef54226997d896fec0b6308a2eac9bd40909a` |

Both have retained direct Atlas HTTPS acquisition receipts, HTTP 200, complete response bodies, no redirects, and exact official parent-link evidence. Acquisition occurred on September 12 at 23:10:46–23:10:47 UTC. Their future repository `received_at` is a different event and is null until an actual apply starts. PPRBD's collection role does not change municipal ownership. The printed 2015 title and 07/01/2026 wording do not establish legal effective dates, adoption or currentness. The first source has structural/selected-context review, not complete numeric QA; the modern source has a separately accepted seven-page, 128-row source review. Intake changes neither scope.

## Exact changes and refusal gates

An apply creates two immutable raw copies, appends the exact same two validated JSONL lines to the original raw and ledger byte prefixes, and replaces only the intake report. The expected result is **61 verified original records / 62 ledger records**. The ledger-only historical `MSI-20260707T221329208329Z-EO-2019-007` remains missing; it is not a 62nd available original. Existing 59 raw and 60 ledger rows, including noncanonical whitespace, are not reserialized. This is custody preservation with `archived_pending_pipeline`, `legal_currentness=not_verified` and `answer_safe=false`; no source registry, coverage, retrieval catalog, queue or legal text is promoted.

Before any write, the transaction pins the approved preparation and all 14 transitive repository Python modules, validates the actual strict `ManualSourceIntakeRequest` and final reconciliation record rules, verifies source hashes, municipal layer, authority, official host, safe archive destinations, baseline/policy/queue hashes, global exact-byte/LFS duplicates, and actual reconciliation of the 59 existing originals. It refuses changed inputs, unrelated publication states, lexical escapes, symlink ancestors, nonordinary files, orphan state artifacts, existing conflicting IDs/digests and incompatible schema/policy changes. It does not expand host policy.

The first `--apply` freezes a single actual UTC receipt time in `execution/INTENT.json`. Every replay rederives and checks that same intent, record IDs and suffix. Raw destinations use `_RAW_ARCHIVE/manual_intake/10_Municipal_Authorities/<source-id>/<actual-UTC-second>_<safe-filename>.pdf`. Preimages of the three overwritten files are preserved exactly under `_SNAPSHOTS/colorado-springs-sd014-<actual-UTC-microsecond>/preimages/`. All originals are checked before either manifest exposes their records. The allowed states are old/old/old, appended raw/old ledger/old report, appended raw/appended ledger/old report, and all final. Other states require investigation rather than a reset or rollback.

The execution directory has a nonblocking process lock. Root must serialize this apply with other intake writers; this is not a repository-wide lock on arbitrary outside processes. File writes are flushed and fsynced and published atomically, with immediate preimage checks. Process interruption and replay are tested. Directory-entry fsync and abrupt-power-loss durability are not claimed. An interrupted process may leave unused ordinary staging files. Preserve them and the intent; rerun the same command. Never delete the intent to obtain a new timestamp.

## Commands

Use the reviewed Python environment. The first command checks the portable evidence only and does not import repository modules. The transaction can be run from outside the checkout; its reviewed repository imports are anchored to the Project Geode location, not the working directory. `--root` selects the data root, not an alternative implementation. A moved package requires a separately reviewed path adaptation before applying; the portable evidence validator remains independent of the repository.

```bash
PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-status-venv/bin/python -I -B "/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-12/colorado-springs-intake-transaction/validate_package.py"

PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-status-venv/bin/python -I -B "/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-12/colorado-springs-intake-transaction/transaction.py" --root "/Users/mcoors/Documents/Project Geode/MasterLegalDatabase" --dry-run
```

Only after root review, use the following apply and verification commands. Repeating `--apply` resumes or verifies the same completed transaction; it does not append duplicates. A bare invocation is a dry run. `--verify` refuses an unapplied transaction.

```bash
PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-status-venv/bin/python -I -B "/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-12/colorado-springs-intake-transaction/transaction.py" --root "/Users/mcoors/Documents/Project Geode/MasterLegalDatabase" --apply

PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-status-venv/bin/python -I -B "/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-12/colorado-springs-intake-transaction/transaction.py" --root "/Users/mcoors/Documents/Project Geode/MasterLegalDatabase" --verify
```

`execution/RECEIPT.json` exists only after completion and records the actual time, exact suffix, originals, preimages and no-op reconciliation. That mutable execution subtree is explicitly outside the frozen preparation inventory; the execution verifier validates its records and canonical outputs. No completed receipt is supplied in this prepared package.

## Validation and preserved implementation history

`VALIDATION.json` binds 56 focused tests, their exact outputs, branch-inclusive coverage above 90%, the actual two-record dry run, and unchanged hashes for all three canonical baseline files. The tests use isolated synthetic repositories, except a read-only test against the approved real two-source plan. They cover all publication interruption boundaries, first-source interruption, idempotence, strict final schema refusal before writes, ownership/host/layer/URL mismatch, changed runtime code, prefix/newline/report shape, source corruption, duplicate bytes/LFS pointers, symlinks/FIFOs, orphan state, conflicting intent/receipt, lock exclusion and atomic destination collisions. They do not run the full corpus validation or prove legal accuracy.

`evidence/el-paso-reference/` retains the earlier implementation solely as provenance, not executable guidance. The new transaction fixes that earlier permissive-record/strict-host preflight gap, uses the two approved municipal sources and direct acquisition method, and freezes actual receipt time only at apply. It does not import the earlier transaction or recovery script. The one-time build/refinement scripts and prior code bytes under `_SNAPSHOTS/` are historical preparation evidence, not run instructions. Final entry points are only `validate_package.py` and `transaction.py`.
