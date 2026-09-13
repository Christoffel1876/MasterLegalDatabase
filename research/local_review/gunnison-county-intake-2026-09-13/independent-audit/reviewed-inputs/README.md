---
title: Prepared three-source Gunnison custody transaction
status: PREPARED_NOT_APPLIED
prepared_date: 2026-09-13
legal_currentness: not_verified
---

This handoff prepares preservation of exactly three already retained Gunnison County
PDFs. It has not applied canonical changes. Root must review this closed preparation and
its independent test results before explicitly applying it. No network request, host
allowlist change, historical transaction execution or new source review occurs here.

| Proposed source ID | Retained basename | Pages | Bytes |
| --- | --- | ---: | ---: |
| `gunnison-building-fees-resolution-2025-24-sh-ext-003` | `SHEXT003-A026.pdf` | 3 | 126,763 |
| `gunnison-building-code-resolution-2023-22-sh-ext-003` | `SHEXT003-A027.pdf` | 16 | 682,037 |
| `gunnison-iwuic-resolution-2022-33-sh-ext-003` | `SHEXT003-A028.pdf` | 4 | 114,843 |

All records use `CO-COUNTY-GUNNISON` and `08_County_Authorities`. The proposed record
method is `received_review_package`, its `official_source_url` is null, and its status
is `archived_pending_pipeline`. The supplied official URLs, exact parent anchors,
HTTP 200 results and historical reservation/completion times remain separate reported
provenance. Original acquisition was not independently witnessed. The original equivalent
tool commands for actions 26–28 were not retained. The earlier audit reviewed only the
first page of each document for role context; this package does not claim complete
23-page transcription, fee-table validation, currentness or legal effect.

`PREPARATION.json` binds the three exact source identities, metadata, small custody subset,
current prefixes and runtime hashes. No actual intake timestamp is present. On an eventual
apply, one actual UTC receipt time is frozen in `execution/INTENT.json`; all three records
and the exact expected report are bound to it. `original_filename` is the actual incoming
basename, not a descriptive name invented from the publisher title.

The exact 64-record raw manifest and 65-record ledger prefixes are preserved unchanged.
One deterministic three-record suffix is appended atomically to each, yielding 67 raw
records and 68 ledger records. The report is derived only from those captured ledger
records plus the selected three. The inherited missing executive-order original remains
ledger-only; the result must not be described as 68 available originals. No generic
append or mutating reconciliation API is called. The existing request CLI's acquisition
enum is not widened; the maintained durable record and path validators are reused.

Before canonical writes, the preflight validates all proposed records, all selected source
hashes/page counts, historical raw identities, current guards, missing-history report,
source ID/digest collisions, actual incoming basenames, and every destination. The full
48,390-row legacy file remains an exact hash/size guard; it is not duplicated in this small
transaction. The complete supporting audit is separately frozen at `../popper-sh003/`.
Only the explicitly pinned relevant subset is copied here. `reference-only/` contains
three unchanged files from the accepted fixed-scope Pueblo County revision for comparison;
they are not run and do not authorize a Pueblo or Gunnison intake.

The transaction uses a nonblocking advisory lock in this preparation's execution folder.
It accepts only its immutable intent, a prefix of the three exact original-file writes,
and monotone raw → ledger → report states. Each canonical write is preceded by a fresh
preflight and exact-byte comparison. Unrelated arrivals are refused without promotion
into the ledger or report. A second apply reuses the same intent/time and returns the
same receipt. Recognized interruptions resume without reserializing old rows. An unknown
execution file, wrong source, foreign suffix, changed guard, altered report, path alias or
symlink is rejected. Unexpected abandoned temporary files require inspection; they are
not silently deleted as recovery evidence.

The lock coordinates invocations of this same preparation. This does not promise a global
lock against arbitrary noncooperating writers or eliminate the filesystem race between
the last comparison and rename. Root should keep unrelated canonical writers paused
through this bounded transaction. A failure may leave its own already verified source
files or recognized prefix state; it must not be relabeled as a completed intake.

Before mutation, exact old raw/ledger/report bytes are preserved both under
`execution/preimages/` and `_SNAPSHOTS/GUNNISON-<actual receipt timestamp>/`. Current guards
are also retained in execution preimages. Raw PDF writes are immutable: an existing
conflicting destination is rejected. The final typed receipt binds all source paths,
source digests, intent time and complete canonical state. A subsequent explicit `--verify`
checks this state and the preserved snapshots; it performs no apply.

Run the portable closed-preparation verifier first from any working directory:

```sh
/private/tmp/geode-status-venv/bin/python -B '/absolute/path/popper-gunnison-intake-preparation/validate_preparation.py'
```

Run the actual repository preflight, still read-only:

```sh
/private/tmp/geode-status-venv/bin/python -B '/absolute/path/popper-gunnison-intake-preparation/transaction.py' --dry-run --root '/Users/mcoors/Documents/Project Geode/MasterLegalDatabase'
```

Only after root reviews and authorizes this exact frozen package, the corresponding
commands are:

```sh
/private/tmp/geode-status-venv/bin/python -B '/absolute/path/popper-gunnison-intake-preparation/transaction.py' --apply --root '/Users/mcoors/Documents/Project Geode/MasterLegalDatabase'
/private/tmp/geode-status-venv/bin/python -B '/absolute/path/popper-gunnison-intake-preparation/transaction.py' --verify --root '/Users/mcoors/Documents/Project Geode/MasterLegalDatabase'
```

The transaction pins the maintained schema/runtime files in the original repository
before importing them. It is not a stand-alone runtime installer. The portable verifier
does not require the original repository or execute the copied transaction. It checks
future execution filenames if present but does not certify a completed execution; the
explicit transaction `--verify` does that against canonical state.

Focused tests use temporary repositories and the exact three received PDF candidates.
No test applies to the actual repository. `VALIDATION.json` records the final commands,
counts and coverage; no source currentness or independent model diversity is claimed.
