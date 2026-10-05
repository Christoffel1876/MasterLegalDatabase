---
title: Statewide source collection and pilot closeout
as_of: 2026-09-23T19:23:28.943734+00:00
status: ready_for_draft_review
legal_currentness: not_verified
---

# Statewide source collection and pilot closeout

This document preserves the initial collection checkpoint. A subsequent verified
build at 20:14 UTC completed DORA native extraction, raising the local searchable
CCR total to 850 PDFs / 24,933 pages. See the [DORA build and search guide](CCR_DORA_NATIVE_SEARCH_2026-09-23.md)
for the later result, exact plans and unchanged limitations. The earlier figures
below describe the initial checkpoint, not the later search coverage.

Project Geode is moving from individual pilot documents to complete source-family
batches. Source acquisition can expand while legal-text review and currentness
reconciliation remain separate, visible work. None of the figures below is a
percentage of all Colorado law.

## What this run establishes

The official SOS numerical catalog lists 25 department IDs. Completed collections
cover 23 of those IDs, including a separately retained refresh of department 12.
The other 22 collections contain 850 rule-series records. These are SOS source
series, not 850 individual obligations or independently certified current rules.
Every completed collection preserves its catalog, agency pages, rule history pages
and source-designated current/future documents. Historical links do not mean the
entire historical document archive was downloaded.

All 22 new departments (850 records) have been added to this checkout as
2,817 verified source and inventory files, totaling 562,064,030 bytes.
The existing department-12 inventory and daily update lane remain separate.
The [collection guide](CCR_STATEWIDE_SOURCE_COLLECTION.md) explains explicit scope,
source identities, validation and source-only status.

The [native text bridge](CCR_SOURCE_TEXT.md) supports exact source-citation and
literal phrase lookup with original hashes and physical page references. At this
checkpoint, 637 new rule PDFs / 18,521 physical pages have machine-extracted text
in local reproducible packages. Word originals remain preserved but unsupported
by this bridge. Native PDF text can flatten redlines and reading order; these
packages are unreviewed and cannot produce current-law or applicability answers.
DORA's additional 213 PDFs / 6,412 pages remain pending native-package creation:
the estimated 7,119 payload files exceed the unchanged 4,000-file package cap.
A bounded document-selection/sharding step is next; these pages are excluded
from the searchable 637-PDF total above.

All 46 published CRS titles (1–44, 25.5 and 26.5), plus the Constitution, have
fresh PDF and HTML copies in internal research staging. The 47 PDFs contain
46,882 physical pages, with byte-verified native text and source-page search.
The HTML structural pass preserves candidate heading and annotation markers;
it does not yet establish complete section boundaries or annotation exclusion.
The project's recorded external-publication restriction remains in force for
these CRS artifacts; the full compilations are not part of this Git change.

County acquisition also continued. Sherlock returned source leads for Alamosa,
Archuleta, Baca and Bent, including seven PDFs / 43 pages (five are exact legacy
byte matches); Popper retained Eagle catalogs and ten Elbert PDFs / 135 pages.
These counties remain partial. Returned files, legacy-byte matches, failed requests
and category gaps are separately inventoried. A discovery checklist entry is not
an acquired, extracted or reviewed document.

## Finite pilot engineering closeout

The engineering pilot has demonstrated these capabilities:

- Immutable originals, typed inventories and source identity/hash checks.
- Cited lookup for native PDFs, scanned local documents and a CRS passage.
- Explicit refusal when the requested current-law answer exceeds reviewed evidence.
- Change, no-change, corrupt-input and incomplete-discovery regression handling.
- Review-candidate packaging with exact source replay and no automatic merge.

Close the engineering pilot after this implementation and the scoped data proposal
pass final review and CI. Broad collection is already underway and does not wait
for every historical ambiguity to be resolved. This does **not** close the original
two-county/two-municipality/two-district category-completeness commitment or the
operational acceptance checks. Those remain explicit rollout work.

## Next batches and owners

| Work | Deliverable and stopping condition | Owner |
|---|---|---|
| Remaining CCR departments | Resolve source-format and size/structure blockers; validate each whole traversal before adding it | Atlas / Popper |
| CRS structure | One shared connector for the retained official HTML; retain section/annotation boundaries and test against the PDFs | Plato |
| County and municipal discovery | Work the pinned batches of eight authorities; preserve bytes and mark missing categories | Sherlock |
| Extraction review | Review prioritized tables, redlines and scanned text; direct-image adjudication of material disagreements | Ebenezer / Atlas |
| Coverage accounting | Recount installed evidence, extraction, review and refresh health independently | Ptolemy |
| Daily updates | Extend beyond department 12 in bounded reviewed groups, then demonstrate successful scheduled runs | Atlas |

The local queue covers 64 county identities and 272 registered municipal
identities. Sheridan Lake is a separate registry/ledger reconciliation item;
these are queue counts, not a newly certified official municipal denominator.
Special-district coverage still lacks a complete reconciled denominator.
State bills, session laws, Register notices, executive orders, AG opinions and
COPRRR reports each retain separate collection and currentness queues.

## Open operating limits

Daily statewide monitoring is not deployed. The existing CCR schedule still
selects department 12. The Register's missing-ID failure and the county collector's
Clear Creek 403 remain unresolved. Manual-source watch readiness is distinct from
an executing always-on monitor. Archive restore verification, missed-run detection
and seven successful scheduled runs remain acceptance checks.

At this checkpoint, department 16 exceeded the unchanged 150 MB department limit,
and department 21 returned an HTML error for a Word document. Their failed attempts
remain preserved and contribute no partial successful inventory. Department 18
completed a fresh attempt after a tested correction for its hyphenated agency
label; the earlier failure remains preserved.

Fresh executive-order and COPRRR catalog requests returned HTTP 403; the AG
opinions catalog returned an empty HTTP 202 challenge. These are access failures,
not empty legal collections. Five newly observed collection gaps are recorded in
`_CONTROL_PLANE/BLOCKED_DOWNLOAD_QUEUE.json`, with dated evidence under
`docs/audits/STATEWIDE_COLLECTION_2026-09-23/` and the previous queue preserved.

## Verify this source checkpoint

Use the repository dependencies (including Beautiful Soup), then verify the dated
index against this Git revision:

```bash
python -B scripts/verify_ccr_source_coverage.py --root . \
  --index-sha256 2a8e6f11287c7f46ead392b7497a93be9788a201e3971dcd7d8965f513bfa94d
```

The index and its schema live in `_CONTROL_PLANE/`. It replays new source snapshots
against original hashes and source metadata, while checking department 12 only as
existing metadata. Later changes to the referenced living inventories will cause
this dated index to fail verification; retain this Git revision for exact replay
and create a new dated coverage checkpoint after future updates. A passing replay
establishes retained-source consistency, not visual or legal accuracy.

## Release verification

The final local release suite passed 3,354 tests with no failures, errors or skips.
The public source-file inventory and materialization receipt are retained under
`docs/audits/STATEWIDE_COLLECTION_2026-09-23/`. They bind all 2,817 added source
and inventory files by SHA-256 and byte count. GitHub CI and owner review remain
separate requirements before merge.
