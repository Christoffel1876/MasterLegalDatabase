---
title: Reproduce DORA source-page search
as_of: 2026-09-23T20:14:51Z
status: verified_local_build
legal_currentness: not_verified
---

# Reproduce DORA source-page search

DORA's 213 retained PDFs now have native text for all 6,412 physical pages in two
bounded packages. Together with the nine earlier CCR packages, the local search
registry covers 850 unique PDFs and 24,933 physical pages across the 22 newly
collected departments. These are source-discovery figures, not counts of verified
rules or a percentage of Colorado law. Department 12, failed department collections
16 and 21, and unsupported Word documents are outside these native-search totals.

The original single-package proposal exceeded the 4,000-payload-file limit. The
version 2 selector assigns each complete PDF hash to one group, with every alias
and version association preserved. Each package retains all 697 original source
files and all 426 document associations; only its selected PDFs get native pages.
No limit was raised. Unselected PDF rows explicitly report no extraction and an
unknown physical-page count in that package. Every query, including a no-match
result, reports its selection scope.

| Package | Selected PDFs | Native physical pages | Payload files | Total bytes, including manifest |
| --- | ---: | ---: | ---: | ---: |
| DORA 1 | 105 | 3,206 | 3,914 | 142,062,295 |
| DORA 2 | 108 | 3,206 | 3,914 | 142,610,461 |

The selectors are disjoint and their union equals all 213 eligible PDF hashes in
the pinned department-18 inventory. Both groups passed actual build, verification,
exact-citation lookup and no-match scope checks. The original nine version 1
packages also replayed under the new implementation with their original manifest
identities. [The build receipt](audits/CCR_NATIVE_SELECTION_2026-09-23/BUILD_RECEIPT.json)
binds the plans, source inventories, reproduced manifests and counts.

## Build from this repository revision

Use the repository's pinned test/runtime dependencies, including PyMuPDF 1.28.2,
and run from the repository root. The plans deliberately use `root: "."`; an
arbitrary working directory is not interchangeable. All input hashes must match.
Both output directories must be new. These commands use retained local bytes and
make no network requests:

```bash
python -B -m geode.pipeline.ccr_source_text build \
  --plan _CONTROL_PLANE/ccr_native_plans/2026-09-23/dora-shard-1.json \
  --output .geode_runtime/ccr-dora/shard-1

python -B -m geode.pipeline.ccr_source_text build \
  --plan _CONTROL_PLANE/ccr_native_plans/2026-09-23/dora-shard-2.json \
  --output .geode_runtime/ccr-dora/shard-2
```

The native packages themselves are generated runtime artifacts, not extra copies
of their originals in this Git change. The two preserved output manifests under
`docs/audits/CCR_NATIVE_SELECTION_2026-09-23/` identify the completed local builds;
they do not imply that every named output file is adjacent in the repository.

## Verify and search

```bash
python -B -m geode.pipeline.ccr_source_text verify \
  --package .geode_runtime/ccr-dora/shard-1 \
  --manifest-sha256 0a617db80bdf078ca8807b87d380063cf47486d7348b1573530b051388276d25

python -B -m geode.pipeline.ccr_source_text verify \
  --package .geode_runtime/ccr-dora/shard-2 \
  --manifest-sha256 1c2ce9ef7cd31744718fb2239f729f7b69f3ba435dd6e9389827b9f2ce452f48

python -B -m geode.pipeline.ccr_source_text query \
  --package .geode_runtime/ccr-dora/shard-2 \
  --manifest-sha256 1c2ce9ef7cd31744718fb2239f729f7b69f3ba435dd6e9389827b9f2ce452f48 \
  --mode citation --text '3 CCR 701-1' --limit 1
```

The example finds 39 matching physical-page associations and returns one whole
source page. Search both packages for a broader source query; the registry does
not yet provide a federated command. Version 2 does not change the limits or
verification contract for version 1 packages.

Native extraction remains unreviewed against page images. It may flatten tables,
retain struck text, concatenate replacements or miss visual annotations. Source
current/future labels and dates remain recorded claims. These packages never
certify current legal applicability, and no match does not establish absence.

## Validation

The focused source-text suite passed 75 cases with 95.93% combined statement and
branch coverage. The maintained coverage-index verifier suite passed 25 cases with
93.22% combined coverage. Full release regression and GitHub CI are recorded
separately under the exact eventual commit; focused tests alone are not a release
claim. Original source bytes and prior failed attempts remain unchanged.
