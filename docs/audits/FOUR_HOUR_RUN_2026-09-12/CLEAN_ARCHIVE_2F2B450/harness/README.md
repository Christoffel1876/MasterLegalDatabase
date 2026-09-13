---
status: prepared_not_executed
purpose: offline_clean_git_archive_smoke_check
public_activity: none_requested
legal_currentness: not_verified
---
# Clean archive smoke check

This is a prepared harness, not a successful release-test receipt. Root must supply an
already extracted Git archive at a different absolute path, an explicit Python environment,
a commit label and a **new external output directory**. The harness neither calls Git nor
creates the archive, so the commit label remains the operator's assertion.

Example, after reviewing the harness and creating the archive:

```sh
/private/tmp/geode-status-venv/bin/python -B \
  '/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-12/clean-archive-smoke/smoke_check.py' \
  --archive-root /private/tmp/geode-clean-archive-COMMIT \
  --output /private/tmp/geode-clean-smoke-COMMIT-isolated \
  --python /private/tmp/geode-status-venv/bin/python \
  --commit-label COMMIT
```

The default requires `/usr/bin/sandbox-exec` when available on PATH. Its temporary profile
applies only to each test subprocess and its descendants: network is denied, reads/writes
of the original Project Geode workspace are denied, and writes to the archive are denied.
It changes no machine security setting. Archive, output scratch and installed runtime reads
remain available; unrelated `/private/tmp` is deliberately not blocked globally. Python,
Pydantic, jsonschema, PyMuPDF 1.28.2, Beautiful Soup and other installed project dependencies
remain external runtime requirements. No installation is performed.

All commands run with the new output directory as their working directory and a minimal
environment. Scripts are opened by absolute archive path; module lookup puts the archive
first. Child validators may use isolated Python and temporary output scratch. No command
contains `--execute`, `--write`, a watcher run name, scheduler activation or public URL to
fetch. The watch command is **readiness only**. Total elapsed budget is 600 seconds by
default, at most 180 seconds per subprocess; timed-out process groups are terminated.

The 14 checks cover:

- All seven native sources, using their documented `--list-rows --format json`: Grand
  Junction 57 rows, Greeley building 19 entries, Weld EHS 137 rows, Greeley impact 30 rows,
  proposed Greeley PIF 8 rows, Colorado Springs construction 128 rows and El Paso EHS 65 rows.
- Source-specific context: Greeley minimum/footnote, Weld blank fee and page context,
  proposed PIF adoption condition, Springs implementation/context, and the English EHS
  year-specific amounts, statutory-reference fee, included reinspection and exceptions.
- The scanned El Paso `Erosion` query: four exact source rows/fees, global footnote 1,
  three General Notes, the clipped source tail and empty native text.
- CRS-1-1-102, including its physical-page 4-to-5 continuation, both paragraphs and three
  ancillary notes. This invokes the documented default packet location within the archive.
- Manual inventory `--check`, with expected 61 sources / 22 review links / 39 unmapped;
  readiness with 61 hash-available originals, two selected sources and 59 unselected.
- Explicit current-law refusal for native, scanned and CRS interfaces.

Every active structured native/scanned evidence path must be an ordinary file under the
archive root. Historical absolute paths quoted inside custody text are not treated as
active references or rewritten. This proves the tested interface's path bindings and, when
the OS profile actually runs, absence of original-workspace access by its child processes.
It does **not** claim that all unrelated temporary paths were inaccessible.

If isolation cannot run, retain that failed/blocked output. There is no automatic fallback.
Root may separately rerun with `--isolation none` and a **different output directory** to
obtain structural/CLI evidence. Such a receipt is explicitly unisolated, cannot establish
filesystem/network isolation, and still invokes only the listed offline APIs. Never turn
an isolation failure into a claimed successful isolated test.

`RUN_RECEIPT.schema.json` is the strict Pydantic-generated schema for a future run. Actual
execution writes `RUN_RECEIPT.json`, every command's stdout/stderr and their hashes, timing,
errors, checked evidence paths and the temporary sandbox profile into the external output
directory. No run receipt exists in this preparation package. The preparation preimage
retains an earlier unexecuted draft; use only the top-level harness.

No full repository tests, archive commands, source acquisition, canonical mutations or
release checks were executed while preparing this harness. Source counts are snapshot
expectations, not complete jurisdictional coverage or current-law claims.
