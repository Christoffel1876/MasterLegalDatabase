---
title: Hazardous Materials and Waste Management research addendum — September 24, 2026
status: partial_research_scope
legal_currentness: not_verified
answer_safe: false
---

# Public Health agency 141 research addendum

This separate addition preserves **17 whole PDF/Word rule pairs and 883 physical
PDF pages** from Public Health's Hazardous Materials and Waste Management Division.
The source responses were already retained on September 23; this addition made
no new source requests. It preserves the department's full 18-agency catalog,
the selected agency's full 53-row rule listing and the selected histories,
including their 246 archived version rows. Archived document bodies are not
included merely because their history rows are present.

Complete selected files can include editorial histories, indexes or reserved
notices. Retaining those files does not establish that every substantive part of
the cited code is present in this package.

The [addendum index](audits/CCR_PH141_RESEARCH_2026-09-24/INDEX.json) binds the
source capture, reproducible native output, input plan and exact original/page
hash ledgers. The source capture has **60 files totaling 23,637,316 bytes**.
The [earlier 11-package index](CCR_AGENCY_RESEARCH_2026-09-24.md) remains unchanged.
Together these two September 24 additions cover **159 rule pairs / 7,117 pages**
in 12 packages, with 591 source-package files totaling 195,849,395 bytes.
These installed-package totals include repeated parent evidence and metadata;
they are not network download totals.

The broader research index contains **1,009 distinct PDF hashes and 32,050 physical
pages across 23 packages**. This is an exact hash/page union with the preceding
992-PDF / 31,167-page ledger, with no overlapping PDF hashes. The previous output
ledgers were rechecked and normalized; the prior 22 packages were not re-extracted
for this addendum. A physical page is counted by original PDF hash plus page number,
not by citation aliases, repeated package copies or rendered page labels.

## Rebuild and search

Run these offline commands from the repository root with the project dependencies,
including pinned PyMuPDF 1.28.2. The output directory must be new.

```bash
python -B -m geode.pipeline.ccr_agency_text build \
  --source 02_Regulations_CCR/_verification/agency_scopes/2026-09-24/public-health-141-G01 \
  --capture-sha256 51657265d4199ab7d034fe64920eeaa44aee73709be0b0f4de95ab47d4aa349d \
  --output .geode_runtime/ccr-agency-2026-09-24/PH141-G01
python -B -m geode.pipeline.ccr_agency_text verify \
  --root .geode_runtime/ccr-agency-2026-09-24/PH141-G01 \
  --manifest-sha256 0cf30bf0f6d0bef777779262ad939fd0ef87afd7292e08c16bcce5816e93a5e0
python -B -m geode.pipeline.ccr_agency_text query \
  --root .geode_runtime/ccr-agency-2026-09-24/PH141-G01 \
  --manifest-sha256 0cf30bf0f6d0bef777779262ad939fd0ef87afd7292e08c16bcce5816e93a5e0 \
  --mode citation --text '6 CCR 1007-1' --limit 1
```

The committed native manifest describes the generated directory, not the audit
folder containing the manifest copy. Native text and embedded-source duplicates
are rebuilt locally rather than committed again. Queries return whole physical
pages with source identities and scope; a miss is not evidence of legal absence.

## Remaining scope

Only 17 of this agency's 53 listing rows are selected. Rule 2945 is wholly excluded:
its 147-page PDF was retained, but its paired Word source is missing from the checked
evidence. The twelve additional histories collected on September 24 remain a
separate document-acquisition queue. The other unselected rows and agencies are
not assumed absent or never previously collected.

Source “current” labels, publication cutoff and dates remain recorded claims.
Word checks recognize signatures only; they do not establish text fidelity or
PDF/Word equivalence. Native PDF extraction remains `machine_extraction_unreviewed`
and may lose visual markup, retain struck wording or distort tables. Referenced
external codes can require separate preservation and verification even when the
local rule PDF has been collected in full.

This addition does not promote canonical publisher state, legal-currentness or
answer safety. The separate CCR departmental collection remains 23 of 25; Public
Health and Transportation are unfinished. County, municipal and district coverage
also remains partial, and no daily-monitoring schedule changes here.
