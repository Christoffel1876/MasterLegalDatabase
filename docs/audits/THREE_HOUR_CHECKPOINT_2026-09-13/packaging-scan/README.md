---
title: Final bounded packaging scan after CI installation
reviewer: Plato
status: SCAN_COMPLETE_NOT_STAGED_BY_PLATO
---

This adaptation preserves the accepted scanner as `REVIEWED_SCANNER.py` and writes only beneath this new handoff folder. The actual scan passed once: **21 wrappers, 3,052 files, 199,789,316 bytes, 119 ignored/untracked payloads, and exactly six original PDFs**. The recorded command, real UTC interval and exit zero are in `RUN.json`; stdout/stderr are retained. No staging, commit, export, source request, or canonical change was performed by this scan.

The 19 inventory hashes from the accepted earlier scan remain exact. The two additions are the root-accepted scanner audit and the final manual-watch CI installation. `APPROVALS.json` binds the complete 21-name inventory allowlist, the root scanner decision, and the supplied CI installation/schema identities. Missing, additional or changed wrappers refuse. The CI installed-file pins are schema-validated and carried through final asset verification. Both excluded user basenames are refused at every path depth, regardless of case.

The adaptation otherwise retains the accepted expected-identity propagation, six explicitly selected raw originals and exact historical prefix, pinned inventory snapshots, final inventory execution/preimage receipts, and failure on unbound inventory additions. It does not restamp later changes. Review/receipt histories remain historical; byte inclusion is not endorsement of every old assertion.

Root's exact staging inputs are the `paths.nul` and `force-add.nul` under `runs/final-ci-installed/`. The companion `SCAN.json` and schema are the sole intended inputs to the separately prepared staged-export procedure. Root owns staging and its approval. That later verification must compare actual index blobs to these exact pins before exporting; this successful working-file scan is not a claim that later staged bytes already match.

Scan SHA-256: `3ba29be62065db3af9d13e3786a56720ab54fcc3bb4fc9ba07d02443052526b7`.
Schema SHA-256: `ad1b8d46440d5166dfa0d07a92ab0cc38c649b115debf9b44d3ab975765f61e5`.

Read-only portable receipt verification:

```sh
PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-status-venv/bin/python -B '/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-13/plato-final-packaging-scan/verify_final_scan.py'
```

The scan itself depends on the fixed repository and reviewed metadata and must not be rerun into this closed folder. Any subsequent changed bytes or additional wrapper require an explicit new reviewed scan. No full test suite was repeated here; root's final suite is separate.
