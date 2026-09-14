---
status: PRELIMINARY_NOT_STAGED
prepared_at: 2026-09-13T04:58:00Z
archive_execution: not_run
public_requests: 0
---
# Preliminary staging audit and clean-export smoke plan

This is a dated review proposal, not a final release list. Nothing was staged, committed, fetched,
or executed against a clean archive. The initial Git status was captured at HEAD
`2f2b450d8ecb3eff5258598d7be27189bc5e4cff` while root was completing the Pueblo County intake.
Its later record appears in the measured raw-file inventory, but the complete final intake and
EB023/024 packages must be added only after their owners freeze them.

`STAGING_AUDIT.json` binds 2,695 selected files (197,030,071 bytes) by exact path, SHA256 and size.
It records tracked status, ignore rule and LFS filter. The largest file is 33,903,546 bytes; no
selected file reaches 100 MB. This does not certify every repository file or future addition.

The two user-owned files are excluded explicitly:

- `docs/audits/PROJECT_STATUS_2026-09-09.md`
- `geode/schemas/models 2.py`

`candidate-pathspecs.nul` lists 2,601 ordinary candidate paths. The separate
`force-add-ignored-pathspecs.nul` lists 94 ignored files for explicit review, including three
canonical originals, 16 snapshots, PDFs inside portable evidence packages and required test logs.
The text companions are for inspection. Do not replace these exact lists with a broad forced add.
The selected originals are Douglas County EHS, City of Pueblo planning and Pueblo County planning;
their authorities remain separate. All three are ordinary PDF bytes with no Git LFS filter.

The scan found no actual secret values in the selected text-like files under its stated patterns.
Twelve Set-Cookie-shaped lines are explicit redaction markers. Three other hits are Python type
annotations; one credential-shaped hit is a legacy source-page filename substring. `REVIEW.json`
records the classifications without copying values. PDF/image contents were hashed, not searched
by OCR for private information, and this is not a universal credential detector.

## Final staging gate

Root should first finish and freeze the County intake package, EB023/024 dispositions, the final
inventory and final test receipt/log. At this scan the raw manifest and ledger were 64/65, while
inventory still described 63 sources, 24 with review links and 39 without. That intermediate
mismatch is explicit; the final inventory count must be supplied to the smoke command.

Re-capture Git status in a new dated audit, add any newly accepted paths, and compare every selected
file to its recorded hash before staging. Inspect ignored originals and all closed-manifest payloads
rather than relying on Git status alone. Confirm the final full-test log is tracked. Preserve this
preliminary snapshot unchanged. Older untracked snapshots omitted by the selection rule are listed
in the JSON for review; they were not swept into the candidate list.

The optional command below only detects changes to this historical selection. It cannot discover
new untracked files or replace the final release audit:

```sh
/private/tmp/geode-status-venv/bin/python -B verify_preparation.py --repository \
  '/Users/mcoors/Documents/Project Geode/MasterLegalDatabase'
```

## Prepared relocation checks

The new `smoke_check.py` retains the earlier seven-source harness, adds Douglas and City of Pueblo,
and tests all three additional named watch batches in readiness mode. The exact predecessor is
preserved as `previous-smoke_check.py`; `SMOKE_PREPARATION.json` records both hashes and changes.
No source code or maintained test was changed. Preparation compiled/imported the harness and
exported its strict receipt schema; it did not execute any of the following 19 checks:

- Nine native source selections with exact row/entry counts, jurisdiction and complete context.
- The scanned El Paso Erosion query with mandatory notes and unresolved clipping preserved.
- CRS 1-1-102 with its page 4–5 continuation and separately classified notes.
- The current manual inventory check and explicit supplied count comparison.
- Original Springs watch readiness plus county, western and Greeley batch readiness.
- Native, scanned and CRS current-law refusals.

All active structured native/scanned evidence paths must resolve to ordinary files under the clean
archive root. Source-only status, unverified currentness, null legal dates, Douglas blank cells and
Pueblo nested associations are checked. Watching and lookup are separate: no `--execute`, HTTP,
monitoring enrollment, schedule, fee calculation or current-law answer is requested.

After root creates and verifies the final commit, export it to a fresh absolute directory outside
Project Geode. Supply the final observed inventory counts explicitly; the harness has no stale
count defaults. Example placeholders must be replaced with reviewed values:

```sh
/private/tmp/geode-status-venv/bin/python -B smoke_check.py \
  --archive-root /private/tmp/CHOSEN_CLEAN_ARCHIVE \
  --output /private/tmp/NEW_SMOKE_OUTPUT \
  --python /private/tmp/geode-status-venv/bin/python \
  --commit-label EXACT_REVIEWED_COMMIT \
  --expected-sources FINAL_SOURCE_COUNT --expected-reviewed FINAL_REVIEW_LINK_COUNT \
  --isolation required --max-seconds 900
```

The temporary per-process sandbox denies network, original Project Geode reads/writes and archive
writes. It does not change machine settings or globally deny unrelated `/private/tmp` runtime
files. The child environment does not override HOME. If sandbox execution is unavailable, retain
that blocked result. A separately named `--isolation none` run, if root explicitly chooses it,
would prove structural relocation only and must not be described as isolated. There is no public
fallback. Python and declared dependencies remain external runtime requirements.

The harness reports its actual run only when invoked. This package certifies preparation and
recorded hashes, not a successful final archive, final staging decision or legal completeness.
