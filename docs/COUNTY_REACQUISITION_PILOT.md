---
title: Jefferson and Clear Creek source recovery pilot
date: 2026-09-10
---
# Jefferson and Clear Creek source recovery pilot

This pilot rebuilds original-source evidence for two counties. It preserves four
named official catalogs and 30 selected documents without replacing the missing
historical county index or treating downloaded documents as reviewed legal rules.
The explicit selection is in
`_CONTROL_PLANE/COUNTY_REACQUISITION_PILOT.json`.

**Operational status, September 10:** the first GitHub-hosted run failed when
Clear Creek returned HTTP 403. A fresh local run collected and validated all 34
sources. The daily schedule is enabled, but automated county collection is not
operational until this access problem is resolved. See the
[hosted-access audit](audits/COUNTY_HOSTED_ACCESS_2026-09-10.md).

## What is collected

| County / catalog | Selected documents | Scope |
| --- | ---: | --- |
| Jefferson / Zoning Resolution | 2 | Whole zoning resolution and wildfire resiliency code. |
| Jefferson / Land Use & Planning | 17 | Listed fees, permits, policies, and ordinances. |
| Clear Creek / Codes & Regulations | 7 | Directly linked animal, sewage, state-interest, road, snowmobile, subdivision, and zoning documents. |
| Clear Creek / County Ordinances | 4 | Ordinances 16–19, including explicit replacement labels on the publisher's catalog. |

The first discovery inventory identifies 88 directly linked documents in the four
catalogs' content areas. The selection does not silently discard the other 58:
48 separately published Jefferson zoning sections, a wildfire-interface map, and
nine other Clear Creek ordinances remain outside this first download batch.
Selecting the whole zoning PDF does not establish that every separately published
section is identical to it. Nested building-code and marijuana licensing/tax
pages, later amendments, incorporated model codes, geographic applicability, and
sources published elsewhere still need discovery and review.

The [dated acquisition audit](audits/COUNTY_REACQUISITION_2026-09-10.md) records
measured source sizes, hashes, PDF checks, exact historical matches, and gaps.
All 30 PDFs together contain 1,092 pages. No complete obligation count, legal
status, or county-wide currency is inferred from those pages.

## Collection and review

The collector requires one main content area and the expected heading in each
official catalog, verifies that each selected document remains linked there with
its source label, and records direct document links including unselected candidates.
It follows no recursive crawl. It accepts only
HTTPS on the two counties' configured hosts and checks redirects before following
them. Downloads use a descriptive Project Geode identity and verified TLS.

Limits are four catalogs, 30 PDFs, 100 MB of accepted source payloads, and 30 MB for
one response. The next request's response cap shrinks to the remaining payload
budget. Retry and redirect traffic is outside this accepted-payload accounting.
The single-source ceiling includes the measured 27.3 MB whole Jefferson zoning
PDF; the trial's complete archive is approximately 42.3 MB. All required sources
must succeed before derived records are promoted. A missing link, failed source,
corrupt prior original, invalid structure, or exceeded limit produces a failed
report and prevents publication. PDFs must have a complete end marker and parse
without repair or encryption; every page must load. A change to another document
format requires review instead of being accepted by a filename or header alone.

Every evidence record is validated and retains original URLs, catalog labels,
retrieval timestamps, file hashes, and source associations. Records explicitly
remain `source_preservation_only`, with `legal_status: unknown` and
`review_required: true`. Category labels organize review; they do not determine
legal applicability. A catalog's replacement label is preserved as evidence,
not converted automatically into a legal conclusion.

Originals are immutable under `_RAW_ARCHIVE/local/reacquisition/`. The two
verification files live under
`08_County_Authorities/_verification/reacquisition/`; prior versions are retained
under `_SNAPSHOTS/county_reacquisition/`. Byte-identical checks leave stored
retrieval times and content untouched while writing a new run report. HTML is
compared by its complete original bytes; a template change can therefore produce
an evidence update without a legal change.

## Daily operation

After the workflow is merged into main, `.github/workflows/county-reacquisition.yml`
runs daily at 13:17 UTC (07:17 MDT / 06:17 MST) and supports manual dispatch.
GitHub may delay scheduled starts. The fixed manifest defines this pilot's scope;
it does not automatically add every newly discovered document to downloads.
New or unselected links remain in the catalog inventory for review.
The stored manifest hash prevents silently changing an established pilot's scope.
Expanding the selected documents requires an explicit migration and review.

The collection job has read-only repository permission. A separate publisher
revalidates its Git bundle and same-run report, restricts changes to the county
verification files and hashed originals/snapshots, and maintains one PR on
`codex/county-reacquisition-update`. It uses non-force pushes and stops on branch
races. It never approves or merges data PRs.
Before publishing, it verifies that every referenced original is present in the
candidate Git tree with matching hash and size. Files left only on disk by an
interrupted local run cannot be mistaken for committed evidence; a fresh checkout
and recollection resolves that failure.

Reports for successes, failures, and no-change runs are retained for 90 days;
candidate bundles for 14 days; publication evidence for 90 days. An unchanged
run may refresh the description of an already pending PR without changing its
data commit. Original historical timestamps are never invented to fill gaps.

## Local commands

Install the frozen dependencies in `requirements-county.txt`, then run from the
repository. Use a separate output root for a live trial:

```bash
python -m geode.pipeline.county_reacquisition \
  --root .geode_runtime/county-trial \
  --manifest "$PWD/_CONTROL_PLANE/COUNTY_REACQUISITION_PILOT.json" \
  --report-dir .geode_runtime/county-report
python -m pytest tests/test_county_reacquisition.py tests/test_publish_county_update.py -q
```

The report directory contains `report.json`, `changes.json`, and `summary.md`.
Inspect it alongside the source inventory and originals. Run the
[coverage dashboard](COVERAGE_AND_CCR_PILOT.md) separately to see inherited data
gaps; newly preserved originals do not repair a missing historical index.

## Next acceptance work

Review source-to-record fidelity, current and historical status, subsequent
amendments, and omitted catalog entries. Reconcile the full agreed category
checklist for both counties and select the municipal/district pilots. Demonstrate
unchanged and changed checks plus actual scheduled successes before expanding.
Use verified source text to rebuild canonical county records and indexes through
a separate review proposal; do not replace unresolved LFS pointers with a partial
collection presented as complete.
