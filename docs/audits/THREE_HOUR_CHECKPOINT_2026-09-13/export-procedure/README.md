---
title: Prepared staged-index export verification
status: PREPARED_NOT_EXECUTED
owner: Plato
scope: Existing staged bytes and offline readiness only
---

Root must supply the final reviewed SCAN and schema hashes after CI installation, tests, and staging. This preparation has performed no staging, repository export, source HTTP, LFS download, maintained-file mutation, or full-suite repeat. Twenty-three small tests use in-memory Git responses and temporary synthetic files only. Earlier 18- and 20-case results and the predecessor before the stronger basename exclusion are retained.

The procedure first verifies the exact final SCAN and its schema, checks the Git HEAD, captures every stage-zero index entry, and compares every selected file's actual Git blob SHA-256/size with the final scan. Every staged modification must be in that scan. It rejects unresolved entries, symlinks/submodules, duplicate or case-aliased paths, missing selected files, and either excluded basename (`models 2.py` or `PROJECT_STATUS_2026-09-09.md`) anywhere in the index, manifests, or exported tree, including nested historical evidence. A pinned copy of an excluded user file is still excluded.

Only after those checks does it export the entire captured index to a new `/private/tmp/geode-staged-*` directory. It reads object bytes with `git cat-file --batch`; no checkout or clean/smudge/process filter is invoked. `GIT_LFS_SKIP_SMUDGE=1` is also set. Existing LFS pointer blobs remain pointers. Missing objects, mismatched pointers, and other failures are recorded, never hydrated or silently skipped. The original working tree is not the export source.

The export is checked against every captured index blob and mode. Each wrapper selected by the final scan is schema-validated and checked for exact closed membership and hashes, supporting both wrapper-relative and repository-relative paths. Then exactly these two checks run from the exported tree:

```sh
/private/tmp/geode-status-venv/bin/python -B -m geode.pipeline.manual_review_inventory --root EXPORT --check
/private/tmp/geode-status-venv/bin/python -B scripts/manual_source_watch_ci.py --root EXPORT --run-name staged-offline --event local_readiness
```

The CI call has no `--execute`. Its returned and retained summary must agree, report `ready`, four verified readiness pairs, no execution/verification exits or source observations, unchanged baseline, no publication/activation, and legal currentness `not_verified`. Its files are allowed only under the new export's `.geode_runtime/manual_source_watch_ci/staged-offline/`. All original exported bytes/modes and closed wrappers are rechecked afterward. The source index listing and HEAD must remain exact before and after. No network sandbox availability or Linux/GitHub execution is inferred from these local commands.

Root-reviewed dispatch template (do not run before root supplies final pins and authorizes this export):

```sh
PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-status-venv/bin/python -B \
  '/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-13/plato-staged-export-procedure/verify_staged_export.py' \
  --repository '/Users/mcoors/Documents/Project Geode/MasterLegalDatabase' \
  --scan '/ABSOLUTE/FINAL/SCAN.json' \
  --scan-sha256 FINAL_SCAN_SHA256 \
  --schema-sha256 FINAL_SCAN_SCHEMA_SHA256 \
  --python /private/tmp/geode-status-venv/bin/python \
  --output /private/tmp/geode-staged-ROOT_SELECTED_UNIQUE_NAME \
  --execute-reviewed-export
```

The execution requires an unused output directory, at most 25,000 regular index entries, 500 MB per blob, and 4 GB cumulative per pass. Each batch reader has a 240-second kill timer. It retains actual command arguments, UTC start/finish, exit codes, stderr, and stdout logs or stream digests. `EXPORTED_INDEX.json` binds every exported path, Git object ID, mode, SHA-256 and size; `RECEIPT.json` records actual checks or failure and pins the copied procedure/model files. Schemas validate records before writing. A failed run preserves its logs and partial export; use a new name only after root reviews the cause. No retry, source repair or staging operation is embedded.

The 23 fixtures test ordinary scope; unmerged, symlink, duplicate and case-alias refusal; both user basenames in original/uppercase/nested/runtime locations; unreviewed or missing index paths; unsafe path syntax; exact consumed blob matching; and truncated-stream failure retention. They do not claim an actual current-index export succeeded. The complete-index cap is expected to cover the reported approximately 12,550 prior tracked files plus this session's additions; actual bounds are checked at execution.

Run preparation verification, without any export:

```sh
PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-status-venv/bin/python -B '/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-13/plato-staged-export-procedure/verify_preparation.py'
```
