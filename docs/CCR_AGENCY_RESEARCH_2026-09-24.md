---
title: Public Health and Transportation source research — September 24, 2026
status: partial_research_scope
legal_currentness: not_verified
answer_safe: false
---

# Public Health and Transportation source research

This dated addition preserves 142 selected rule identities as 142 PDF/Word pairs
and makes 6,234 physical PDF pages reproducible as native-text research. The
11 portable source packages include the department catalogs, complete selected
agency listings, rule-history pages and exact document responses used to establish
each source relationship. They are **partial agency research captures**: the
completed departmental collection count remains **23 of 25**, and statewide
legal completeness is not established.

| Selected scope | Rule pairs / distinct PDFs | Physical PDF pages | Packages |
|---|---:|---:|---:|
| Public Health agency 132 | 43 | 4,594 | 4 |
| Public Health agency 142 | 6 | 85 | 1 |
| Public Health agency 143 | 19 | 277 | 1 |
| Public Health agency 144 | 32 | 810 | 2 |
| Public Health agency 145 | 1 | 1 | 1 |
| Transportation, selected rules across seven agencies | 41 | 467 | 2 |
| **Total** | **142** | **6,234** | **11** |

The [machine-readable index](audits/CCR_AGENCY_RESEARCH_2026-09-24/INDEX.json)
contains exact repository paths, manifest hashes, input plans, counts and build
commands. Its SHA-256 is
`7680496f30c81eac4bca6d0dbd3f27627e3f105053c4fac5fe8fa00468fe024b`.
The source packages contain 531 files totaling 172,212,079 bytes, including repeated
parent evidence and metadata. This is an installed-package count, not a measure
of newly downloaded network bytes. Earlier retained sources are included alongside
the 58 Public Health pairs acquired on September 24.

## Rebuild and search

Run from the repository root with the project dependencies, including the pinned
PyMuPDF 1.28.2. All commands below are offline. Use a fresh output directory;
an existing complete or interrupted package is preserved and cannot be overwritten.

```bash
python -B -m geode.pipeline.ccr_agency_text build \
  --source 02_Regulations_CCR/_verification/agency_scopes/2026-09-24/public-health-PH-A142-01 \
  --capture-sha256 1205db27909c8da314a4383aa9de133594a18bdf8744de2152c5554b39701409 \
  --output .geode_runtime/ccr-agency-2026-09-24/PH-A142-01
python -B -m geode.pipeline.ccr_agency_text verify \
  --root .geode_runtime/ccr-agency-2026-09-24/PH-A142-01 \
  --manifest-sha256 1279f8c145f6a7a96180ead669644b528a1ec3f03a1ac8bd5306e34f8c134ec5
python -B -m geode.pipeline.ccr_agency_text query \
  --root .geode_runtime/ccr-agency-2026-09-24/PH-A142-01 \
  --manifest-sha256 1279f8c145f6a7a96180ead669644b528a1ec3f03a1ac8bd5306e34f8c134ec5 \
  --mode citation --text '6 CCR 1009-1' --limit 1
```

The index has equivalent build and verification commands for all 11 packages.
Committed `*-native-manifest.json` files describe the expected **generated output
directories**. Their member paths are relative to those generated directories,
not to the audit folder containing the manifest copies. The original source files
are committed; the generated native text is rebuilt locally to avoid a second
copy of the corpus in Git.

Queries return complete physical pages with source URL, original hash, rule,
version, date and extraction scope. See the [native-text command guide](CCR_AGENCY_TEXT.md)
and [source-capture verification guide](CCR_AGENCY_CAPTURE_V2.md) for caps,
whole-PDF selections and refusal behavior.

## What remains unresolved

Transportation rule `21/124/3475` (`2 CCR 601-27`, version `12137`) is excluded as
a whole rule. Its exact consolidated Word handler returned an HTML error body
even though HTTP status was 200. The valid PDF and an unrelated eDocket document
do not establish that the required Word source was recovered. Transportation is
therefore still incomplete under the department collection contract.

Public Health's department catalog contains 18 agencies. These five agency scopes
and the [earlier agencies 137/138/140 snapshot](CCR_AGENCY_RESEARCH_SNAPSHOT.md)
do not cover the department. Other histories and document pairs remain to collect;
archived version bodies are not included merely because their history rows exist.

Native extraction is `machine_extraction_unreviewed`. It can miss visual markup,
retain struck text, distort tables or yield blank text for scans. Word validation
checks format signatures only. Source labels such as repealed, reserved, dates and
version designations remain the source's statements at recorded acquisition times.
Neither extraction nor a source's “current” label establishes legal applicability.

No canonical department state, daily-monitoring schedule, county/municipal
coverage claim or legal answer gate is changed by these partial research packages.
A query with no hits does not prove that a requirement is absent from Colorado law.
