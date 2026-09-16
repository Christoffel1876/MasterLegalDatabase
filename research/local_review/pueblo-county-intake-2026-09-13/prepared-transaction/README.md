---
status: PREPARED_NOT_APPLIED
source_id: pueblo-county-planning-fees-sh-ext-002
legal_currentness: not_verified
canonical_mutations: 0
---
# Pueblo County fee PDF — one-source preservation proposal

This prepares exactly one received two-page PDF, 75,214 bytes, SHA256 `1c9fda2c8bacb414468947664d6edb6640845081fcb1a5366dccf0c58720a084`. Root has accepted its limited source-fidelity review. No canonical intake has been applied by this packet.

The proposed identity is `pueblo-county-planning-fees-sh-ext-002`, authority `CO-COUNTY-PUEBLO`, layer `08_County_Authorities`. City of Pueblo remains a separate source. Acquisition is `received_review_package`; `official_source_url` is null. The exact reported county URL, public headers, serial reservation/result times, error response and browser-DOM referral remain separately preserved. The reported reservation/result interval is not relabeled as a witnessed HTTP start/end or a root download. Actual repository receipt time remains null until an approved application creates its intent.

The selected incoming file is `inputs/independent-review/received/original.pdf`, so the final `original_filename` is truthfully `original.pdf`. The exact original delivery filename `SHEXT002-A001.pdf` is separately preserved in the unchanged custody audit. This is a selected copy of the same hash, not a claimed publisher filename. Only one PDF is proposed: the denied catalog body, duplicate `.bin` bytes, DOM, rasters and extracted text are not separate canonical originals.

Root acceptance `ec064067521ee2d4c350f049b4ce03bfa2acc31cb378a1008e2f53a6efe07289` covers two full pages and 88 physical rows (69 labeled fee rows), including continuations and global/group marker context. It establishes neither adoption nor current law. Filename “Adopted 5.8.25,” PDF metadata and Last-Modified remain different claims. The commissioner catalog was reported HTTP 403 and the adopting instrument remains unresolved.

The unchanged independent custody audit is fully copied under `inputs/custody-audit/`; its own manifest is `78e4618dae861428702f4f7810702b16afa1fb8f72e7f43942e3d074a0104168`. Its recorded complete pinned/current legacy scans cover 48,390 metadata rows each and have no exact/decoded URL, digest or proposed-ID match. The full legacy streams were deliberately omitted by that audit; do not claim they are included here. The proposed transaction pins the current stream’s exact 33,903,546 bytes/SHA before writing. This is a dated metadata comparison, not proof of global novelty, absent unrecorded originals or a legal change. No historical original bytes were compared.

## Exact append and recovery boundary

`PREPARATION.json` pins raw-manifest 63 rows and ledger 64 rows, report, legacy coverage ledger, intake policy, blocked queue and all transitive local runtime files. The comparison commit is historical evidence; a later evidence-only commit is permitted when every affected-file/code pin remains exact. Expected final counts are 64 raw / 65 ledger, with the inherited missing ledger-only executive-order original unchanged.

`transaction.py` is a small fixed-source wrapper around the existing `reconcile_manual_source_intake` API. The generic archive request API does not admit `received_review_package` and reserializes historical raw JSONL, so it is not used. This wrapper validates the final typed record and root approval before any canonical write, creates the source once, appends one deterministic raw suffix without reserializing the old prefix, and appends only the same frozen ledger suffix and writes the exact typed report frozen in its immutable intent; generic reconciliation is invoked only read-only. A complete replay verifies byte identity without adding records.

The actual application creates one immutable intent with actual UTC receipt time and final archive path. It preserves every exact preimage under `execution/preimages/`; the exact raw, ledger and report preimages are also preserved under repository _SNAPSHOTS/<intake_id>/ before the first canonical write. Source and intent creation use atomic write-once publication; the raw update requires exact preimage bytes. An exclusive execution lock prevents two instances of this same packet from choosing different intents. Exact current-state checks reject unrelated concurrent changes; this is not a general lock on every possible repository writer.

Stop on failure and retain the original intent, source and partial prefixes. Recovery is forward replay of this same reviewed packet, not deletion of a source, truncation of JSONL, fabricated reconstruction or creation of a fresh timestamp. If the raw prefix has appended but ledger/report have not completed, the fixed-source writer repairs only that recognized state. A bad hash, foreign file, changed policy/code/legacy prefix or unexpected report state must be investigated before replay. The tested interruptions are process-boundary failures; directory entries are not fsynced, and power-loss/filesystem durability is not certified. Leftover temporary files after an actual abrupt process death require review; do not delete evidence blindly.

## Review and execution commands

Use the original prepared script with an explicit repository root. Do not execute a relocated historical copy against its embedded default root. No apply command has been executed here.

```sh
cd '/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-12/extended-run/pueblo-county-fees-intake-revision'
PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-status-venv/bin/python -B verify_preparation.py --manifest-sha256 FINAL_DIGEST --repository '/Users/mcoors/Documents/Project Geode/MasterLegalDatabase'
PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-status-venv/bin/python -B transaction.py --root '/Users/mcoors/Documents/Project Geode/MasterLegalDatabase' --dry-run
```

Only after root’s review of this exact prepared transaction:

```sh
PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-status-venv/bin/python -B transaction.py --root '/Users/mcoors/Documents/Project Geode/MasterLegalDatabase' --apply
PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-status-venv/bin/python -B transaction.py --root '/Users/mcoors/Documents/Project Geode/MasterLegalDatabase' --verify
```

The portable verifier checks closed custody and schemas without running historical scripts or HTTP. Its optional `--repository` performs only the current dry-run or completion verification. Test fixtures use synthetic prior records and clocks and temporary corpus roots; they are not actual intake receipts. Earlier pre-acceptance preparation and test invocation/focused logs remain in `preparation-history/` as historical evidence. They must not be mistaken for the final proposal. Current validation results and schema hashes are recorded in `VALIDATION.json`.

No raw source, ledger, report, registry, coverage, queue, lookup or monitoring state was changed by preparation. There is no new current-law capability.

## Fixed-source revision disposition

The original proposal was held because a foreign raw record arriving before generic reconciliation could be added to the ledger/report. Its original bytes and blocking independent reproduction remain historical evidence. This revision never calls generic reconciliation in write mode. It freezes the expected report before mutation and checks exact state again after each raw/ledger/report boundary. Foreign additions reject and remain unpromoted.44 combined temporary-fixture cases passed, including13 independent cases, five interruption boundaries and report tampering. This does not certify global atomicity against arbitrary noncooperating writers. No original source text, legal status or reported acquisition time was changed.
