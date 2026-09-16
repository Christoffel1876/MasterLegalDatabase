---
title: Proposed Colorado Springs fire-fee source intake
status: PREPARED_NOT_APPLIED
legal_currentness: not_verified
---

# Two originals ready for intake review

The proposal preserves two directly acquired City of Colorado Springs PDFs under **10_Municipal_Authorities**, authority **CO-MUNICIPAL-COLORADO_SPRINGS**. No canonical original, raw manifest, ledger, registry or coverage record has been changed.

| Source | Proposed record ID | Pages | Bytes | Scope |
|---|---|---:|---:|---|
| SD014-01 | `colorado-springs-code-services-fees-2015-atlas-directed` | 7 | 162,682 | Visible 2015 Code Services schedule; full numeric table QA is incomplete. |
| SD014-02 | `colorado-springs-construction-fees-atlas-directed` | 7 | 258,393 | Construction Services schedule; accepted seven-page source QA covers all 128 fee rows and complete context. |

The original SHA256 values are respectively `555570a62a5a557a824d1bcf3ecd2e60d57e48d19ea401f06a2e5b7ccb177e56` and `e35de501a011fe55f03140bf91aef54226997d896fec0b6308a2eac9bd40909a`. Both are absent from the current canonical raw archive, manual manifest and ledger. Both proposed IDs are unused in the checked current records and registries. Exact URL/hash/ID searches of five named metadata files found no matches; this is not a fuzzy historical-version claim.

## Custody and scope

Atlas retained complete HTTP 200 bodies without redirects from the exact official URLs on 12 September 2026. The Code Services request ran **23:10:46.169682Z–23:10:46.652367Z**; Construction Services ran **23:10:46.676197Z–23:10:47.380038Z**. Public headers, original event receipts and parent HTML are copied unchanged. Each parent iframe's `data-src` matches its PDF viewer `file` argument after exactly one percent-decoding and matches the actual requested PDF URL. The descriptive copy filenames are derived from the exact PDF URL basenames; the original downloader stored `body.bin`, and no server-supplied filename is claimed. These are directly observed Atlas acquisitions, so the existing `manual_official_download` method is appropriate. They are not Sherlock received-package claims.

The visible 2015 title is not proof of an enactment or effective date. Hidden native “2015 Proposed changes” strings and white-on-white numbers are qualified in the retained source-scope review. No draft or adopted status is inferred from those strings. The modern PDF prints **Effective 07/01/2026**, with legal effect and adopting instrument still unverified. No supersession finding links these particular editions.

The City fire department is the issuer. PPRBD's collection of construction-plan-check fees and the conditional deduction at CSFD approval remain source context, not a reassignment to a district. Source review does not certify current law, make fees answer-safe or decide applicability.

## Proposed records, not final receipt times

`proposed-records.jsonl` contains strict append templates with **null intake_id, archive_path and received_at**, and `proposed_not_applied` status. `requests.jsonl` contains two validated existing `ManualSourceIntakeRequest` records. `dry-run-previews.jsonl` contains actual API dry-run outputs, validated as `ManualSourceIntakeRecord` and against reconciliation host/layer/path rules. Their timestamp is the preparation time only. Their deliberate `dry_run_pending_archive` status must never enter the canonical manifest.

Execution must take one actual UTC repository intake time, freeze it in an intent, and derive new IDs, paths and `archived_pending_pipeline` records. Do not substitute source dates or HTTP acquisition times for that receipt time. `source-provenance.jsonl` preserves these separate date roles and their limitations.

The current baseline has **59 verified originals / 60 ledger records**. The existing missing EO remains ledger-only history. Adding the two new PDFs would yield **61 verified originals / 62 ledger records**, not 62 available originals. Current reconciliation reports no missing additions or report drift. Both exact source URLs pass the existing strict host validator; no allowlist change is required.

## Required transaction preflight

1. Approve the exact two source IDs and frozen preparation. Serialize the short apply against other intake writers. Recheck all pinned baseline/code/policy/queue hashes, source bytes, seven-page counts, URLs and custody before any mutation.
2. Re-run global raw-byte/LFS-pointer dedupe and ID/path conflicts. The generic intake helper rejects only a duplicate digest under the same record ID; that is not a complete dedupe check.
3. Re-run current reconciliation and final row validation, including the strict host validator, municipal layer, canonical archive parent and timezone-aware receipt. The recent El Paso interruption demonstrated why parsing a permissive record model alone is insufficient.
4. Freeze an actual-time intent and exact source-record suffix. Snapshot the byte-exact raw-manifest, ledger and report preimages. Stage independent original copies, refusing existing destinations and symlinks; verify both originals before publishing any suffix.
5. Use a separately reviewed transaction that preserves **before + exact suffix** and safely resumes its own interrupted states. Do not call the generic apply helper: it reserializes prior raw-manifest rows and does not coordinate all writes as a resumable transaction. No apply tool or new transaction implementation is included here.
6. After originals, append the exact suffix to the raw manifest and ledger, then write the typed reconciled report. Verify historical prefixes, both source hashes, snapshots, expected counts and unchanged missing EO history. Reconciliation must again show no additions/report changes. Preserve a final execution receipt and actual repository-validation result.

`PREPARATION.json` holds the full machine-readable preflight. All official source bytes and old records remain unchanged. Full QA dependencies are retained in their separate frozen review packages; this preparation copies their exact metadata and acceptance evidence, not another full QA package.

## Read-only validation

Portable package check:

```sh
PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-status-venv/bin/python -I -B "/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-12/colorado-springs-intake-preparation/validate_preparation.py"
```

Add `--repo "/Users/mcoors/Documents/Project Geode/MasterLegalDatabase"` for fresh baseline, actual schema/host/path dry-run, reconciliation and global raw dedupe checks. This remains read-only. A later legitimate intake or metadata/code change invalidates this pinned preflight and requires a reviewed refresh; do not bypass the refusal. No network request or canonical write is performed.
