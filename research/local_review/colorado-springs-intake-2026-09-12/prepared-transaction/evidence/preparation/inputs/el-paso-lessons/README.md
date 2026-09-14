---
title: Reviewed El Paso received-PDF transaction, awaiting execution
date: "2026-09-12"
status: prepared_not_applied
real_repository_apply_performed: false
legal_currentness: not_verified
answer_safe: false
---

# Scope and current state

This is an executable **13-source preservation transaction awaiting root execution**. No real raw archive, manifest, ledger or report was changed during implementation or tests. The approved preparation is preserved byte-for-byte under `evidence/preparation/`. Its 144-file tree, source decisions, 15 exact PDFs, twenty-page title/role review, upstream cap/custody failures and source-date qualifications remain historical evidence, unchanged.

Only the approved county and Board of Health set can enter the CLI path. The school-district fee sheet and Colorado Geological Survey guide remain excluded. English/Spanish health-board texts stay separate. LDC Chapters 1, 2 and 5 keep the inherited-URL/no-fresh-anchor limitation. Ordinance 26-01 is stormwater; the unsafe-building artifact contains Resolution 17-321 and Ordinance 18-03. These roles are bound through the accepted provenance SHA and retained custody notes, not inferred from filenames at execution.

The expected starting raw manifest and ledger are **46 / 47**. Successful application would produce **59 / 60** while retaining the same ledger-only historical record and its missing-original disclosure. These after-counts are conditional until the real execution receipt exists. All new records use `received_review_package` and `archived_pending_pipeline`; no original HTTP acquisition, legal currentness, translation equivalence, semantic extraction or answer safety is promoted.

# Reviewed input pins

- Preparation: `08fc11d7de1f23128b2f1dae63c8ed0960517a9ecdbd1e1a0ef8f4852c05d0fa`
- Preparation manifest: `8291e4abed17a31eb11eb85c3482ae8386e8763dffaabbeb69bb07b87096caac`
- Existing manual-intake implementation: `5442b78cf16fb3b24f28a72f1c95753a444d39aaf8a906858e3fdcc9f439e0bd`
- Historical comparison commit remains `0a3ba27aaf5358141efb5af2c33c3a6b9043d099`.

Current HEAD is deliberately not equated with that historical comparison. Evidence-only descendant commits do not invalidate this transaction if its exact affected-file preimages and other pinned ownership/policy/code inputs remain identical. No Git command is used by the transaction.

# Commands

Use the existing interpreter with Pydantic 2, PyMuPDF 1.28.2, jsonschema and BeautifulSoup. `-I -B` isolates Python environment variables/user-site imports and disables bytecode writes. The script loads only the exact reviewed manual-intake module and pins the complete preparation before executing its read-only verifier.

**Dry run, read-only; also the default if no mode flag is given:**

```sh
/private/tmp/geode-status-venv/bin/python -I -B "/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-12/el-paso-intake-transaction/transaction.py" --root "/Users/mcoors/Documents/Project Geode/MasterLegalDatabase" --dry-run
```

**Apply, for root to execute after reviewing this implementation:**

```sh
/private/tmp/geode-status-venv/bin/python -I -B "/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-12/el-paso-intake-transaction/transaction.py" --root "/Users/mcoors/Documents/Project Geode/MasterLegalDatabase" --apply
```

**Verify completed application, read-only:**

```sh
/private/tmp/geode-status-venv/bin/python -I -B "/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-12/el-paso-intake-transaction/transaction.py" --root "/Users/mcoors/Documents/Project Geode/MasterLegalDatabase" --verify
```

The apply command has **not** been executed against the real repository. A missing completion receipt causes `--verify` to fail. A baseline or reviewed input change causes the command to stop for a new reviewed transaction; it does not invent updated pins or timestamps.

# Transaction and restart behavior

1. Verify all immutable input files and the exact current preimages; stream old JSONL records through their schema. Check explicit source/owner joins, source hashes, ID/digest collisions and every existing manual original through the current read-only reconciliation function. Reject symlinks and nonordinary files before reading or writing.
2. Take an exclusive nonblocking transaction lock. Recheck under the lock. On the first authorized apply, capture actual UTC receipt time, generate all 13 final typed records, and validate their exact suffix, intended report, raw destinations and preimages **before any repository write**.
3. Atomically create `execution/INTENT.json` and `execution/records.jsonl` within this handoff. The intent contains the actual application time, fixed record IDs, source digests, expected before/after hashes and snapshot paths. Later attempts must regenerate exactly the same records from that intent; they do not take a new receipt time.
4. Preserve all three exact preimages under `_SNAPSHOTS/el-paso-sd011-<UTC stamp>/preimages/`. Copy each source into an independent temporary inode, flush it, then atomically link it into a new raw destination without replacing any existing destination. No canonical original shares its inode with the received handoff source.
5. Verify every new raw file before publishing the manifest suffix. Replace the raw manifest atomically only when its bytes still equal the pinned preimage. The result must be exactly `before + suffix`; historical JSONL is not parsed and reserialized for writing.
6. Ask the existing reconciliation function for a **read-only** prediction. Require precisely these 13 additions and the planned report content. Append the same exact suffix to the old ledger bytes, then write the typed reconciled report. The generic raw append helper is never called, and the official-only request API is not misused to label a received package as an independently observed official download.
7. Require a no-additions/no-report-change reconciliation replay, check all destination/snapshot hashes and both exact-prefix equations, then create `execution/RECEIPT.json`. It explicitly says full corpus validation was not run by this transaction. Root must run the normal corpus validation and preserve its actual results separately after apply.

Restart accepts only these exact manifest/ledger/report states: before/before/before; after/before/before; after/after/before; or after/after/after. Any foreign bytes, unsupported order, changed intent, unexpected duplicate, corrupted original or bad snapshot stops the run. Repeating `--apply` with a completed receipt verifies the same result without creating another record or changing the receipt time. Later unrelated appends are not automatically absorbed; this immediate transaction verifier intentionally expects its exact final state.

File data is flushed with `fsync`, but directory entries are not fsynced. **The tests cover process interruption and deterministic replay, not a proven power-loss or filesystem durability guarantee.** Unique temporary staging files may remain after an abrupt process death; they are scratch files under the recorded snapshot staging directory, not promoted originals. Existing wrong bytes at an intended raw destination are never overwritten or silently repaired.

The lock coordinates this transaction's own invocations. It is not a global lock respected by every other repository tool. Exact preimage checks immediately before replacement make unrelated changes fail closed; avoid parallel manual-intake writers during the root's short apply operation.

# Validation and distributable boundary

`VALIDATION.json` binds the final implementation/tests, exact real baseline before/after, read-only dry-run output, fixture test output and coverage. Tests use generated small PDFs and synthetic 46/47-row fixture repositories under this handoff's `_test_runs*` directories. They never invoke apply against the actual repository or alter real source bytes. Fault injection covers six process-interruption boundaries plus malformed inputs, ownership, collisions, path types, locking and receipt/state tampering.

`FINAL_MANIFEST.json` inventories distributable code, schemas, validation evidence and the unchanged approved preparation. Runtime fixture directories, coverage database files and the future `execution/` directory are explicitly outside that frozen inventory. Execution artifacts have their own typed intent/receipt and exact hashes. The old preparation's private header exclusions still apply; no raw cookie-bearing headers or discovery archives were added.

Validate the frozen package itself without importing or applying the transaction:

```sh
/private/tmp/geode-status-venv/bin/python -I -B "/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-12/el-paso-intake-transaction/validate_package.py"
```

The frozen package check verifies its historical `prepared_not_applied` evidence. It does not inspect later execution state or supersede `transaction.py --verify`. Fixture-only coverage and combined fixture-plus-read-only-CLI coverage are retained separately; no coverage is claimed from applying against the real repository.
