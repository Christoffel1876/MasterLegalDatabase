---
title: Coverage inventory and current CCR pilot
date: 2026-09-09
---
# Coverage inventory and current CCR pilot

This package makes missing coverage visible and checks one complete department
in the Secretary of State's CCR catalog. It produces source evidence for review;
it does not certify statewide currency or replace the inherited CCR legal text.

## Coverage dashboard

Run from the repository with the dependencies in `requirements-ci.txt`:

```bash
python -m geode.pipeline.coverage_dashboard --root . --output-dir .geode_runtime/coverage
```

The output contains `coverage-dashboard.md` for reading and
`coverage-dashboard.json` for machines. It recounts indexes, metadata, source
registries, and local download attempts. It separates authority identities,
preserved-source declarations, substantive records, and extracted units. Original
file availability, unresolved Git LFS pointers, schema failures, and category
gaps remain visible. Historical retries are collapsed by source ID and requested
URL when counting distinct requests.

This is an offline inventory. A recent download date cannot establish live
currency, and a listed source or government cannot establish complete legal
coverage. The report checks referenced evidence availability, not every byte in
the historic raw-file manifest. The
[September baseline](audits/COVERAGE_BASELINE_2026-09-09.md) was generated before
the pending Register and CCR data proposals were merged.

## Current CCR scope

The automated pilot traverses department 12, the Department of Local Affairs,
through the [official numerical catalog](https://www.sos.state.co.us/CCR/NumericalDeptList.do).
It reads every listed agency and rule page in that department and preserves the
source-designated current and future documents, including available PDF and Word
versions. Historical version links remain in the inventory; their full document
history is outside this pilot's download scope.

The verification records distinguish `source_current`, `source_repealed`,
`future_effective`, and `ambiguous`. Explicit repeal labels take precedence over
the website's generic “Current version” table heading. Effective dates, adopted
dates, publication dates, the website's publication cutoff, and retrieval times
remain separate. `source_current` records what the publisher labels current; it
does not resolve legal applicability. Every record requires review.

Outputs are restricted to:

- `02_Regulations_CCR/_verification/current/department-12.jsonl`
- `02_Regulations_CCR/_verification/current/department-12-state.json`
- `_RAW_ARCHIVE/ccr/current/` with content-addressed original files
- `_SNAPSHOTS/ccr_current/` with prior verification inventories and states

These verification files are separate from the canonical CCR index and text.
Downstream legal answers must not treat this evidence proposal as a reviewed
update to that text. Resolving differences and rebuilding canonical text,
metadata, crosswalks, and retrieval indexes is a subsequent reviewed step.

## Daily operation

Once merged into `main`, `.github/workflows/ccr-current.yml` checks department 12
daily at 12:47 UTC (06:47 MDT / 05:47 MST) and supports manual dispatch. GitHub
may delay scheduled runs. Its scope is independent of the Colorado Register
notice pilot, which runs at 12:23 UTC.

The collection job has read-only repository access. It resumes the pending data
branch, incorporates current main, runs offline regression checks, collects the
sources, validates the transaction, and generates a coverage report. It packages
a Git bundle containing only permitted data paths. The separate publisher job
downloads that bundle and its validation report, rechecks both, and uses a
non-force push to maintain one PR on `codex/ccr-current-update`.

No workflow approves or merges data PRs. A reviewer checks the original sources,
classification evidence, effective dates, unresolved items, and proposed changes.
Code approval and source-data approval are separate decisions.

Every run retains a report, including failed and no-change checks, for 90 days.
Candidate bundles are retained for 14 days; publication evidence for 90 days.
No-change checks retain their new check timestamp in the run artifact while
leaving the prior content inventory unchanged. Only the specifically recognized
passive Cloudflare wrapper is excluded from HTML comparison; originals remain
immutable. Documents are compared by their original bytes.

A run stops before promoting derived data on incomplete discovery, disappearing
previously listed agencies/rules, unexpected page structures, failed downloads,
corrupt prior evidence, or a backwards publication cutoff. It also stops at the
pilot limits: 300 distinct source URLs, 150 MB total, and 15 MB per source. A failed
run cannot make the source current. Raw evidence already written during a
failed filesystem transaction may remain for investigation.

## Local verification

Use a separate output root when evaluating live collection:

```bash
python -m geode.pipeline.ccr_current --root .geode_runtime/ccr-trial --department-id 12 --report-dir .geode_runtime/ccr-report
python -m pytest tests/test_ccr_current.py tests/test_publish_ccr_current.py tests/test_coverage_dashboard.py -q
```

Inspect `report.json`, `changes.json`, and `summary.md` in the report directory.
The inventory and original evidence are under the trial root. Do not interpret
successful schema validation as independent validation of every legal statement.

## Remaining work

The [county recovery audit](audits/COUNTY_RECOVERY_2026-09-09.md) distinguishes
unrecoverable latest objects from historical metadata recovered through Git.
No original backup was available from the owner. Recollection starts from
documented official county catalogs; recovered old metadata remains historical.

Follow the [approved coverage roadmap](audits/UPDATE_ROADMAP_2026-09-09.md) for
the remaining CCR departments, CRS and session-law reconciliation, and the
two-county/two-municipality/two-district collection pilot. Reconcile official
jurisdiction lists and category denominators before claiming complete coverage.
Archive restore verification, missed-run monitoring, and seven successful
scheduled runs remain operating acceptance checks.
