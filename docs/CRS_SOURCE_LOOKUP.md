---
title: Reviewed CRS source-passage lookup
created: 2026-09-12
scope: three_sections_in_one_preserved_2026_source
legal_currentness: not_verified
---

# Reviewed CRS source-passage lookup

Use this command to retrieve the complete reviewed source selection for
**CRS-1-1-101, CRS-1-1-102 or CRS-1-1-103** from the preserved 2026 Title 1 PDF:

```sh
python scripts/crs_source_lookup.py --section CRS-1-1-102
```

The output is typed JSON. It includes a section heading, every statutory paragraph,
and all associated source-history notes, editor's notes, cross-references and case
annotation material, each separately classified. Across the three selections,
there are six complete paragraphs and 19 native regions. These are source-review
counts, not counts of legal requirements or complete state-law coverage.

Section 102(1) includes its continuation from physical page 4 onto page 5 as one
paragraph with two fragments. Section 103 includes the editor's note, annotation
heading and complete case annotation on page 6. Ancillary material is always
returned with its section; it is not silently removed or presented as statutory
body text. Case commentary is not independently verified as a case holding.

Each fragment identifies its physical and printed page, native-file and image
hashes, half-open UTF-8 byte offsets, exact text and text hash, visible location,
and the source review's qualification. Complete paragraph text concatenates the
declared fragments without inserting or correcting bytes. Native line breaks,
spacing and typography-related extraction artifacts remain unchanged.

The command uses its own repository location to find the existing source package,
so it also works outside the checkout:

```sh
python "/path/to/MasterLegalDatabase/scripts/crs_source_lookup.py" \
  --section CRS-1-1-103
```

Use the project's Python environment with Pydantic, PyMuPDF and Beautiful Soup
available. `--source /path/to/source-package` can point to an exact portable copy;
its frozen hashes and closed inventory must still match. It cannot select a
different title, edition or source. No source is downloaded during lookup.

The Python API is `lookup(source_packet: Path, section_id: str,
mode="source_only") -> Result`, with `mode` passed by keyword. The exact selected
IDs are required; this is not free-text or fuzzy search. An unselected ID returns
`outside_scope` and exit status 2, describing only the lookup boundary.

`source_only` is the default mode. Every other mode, including `current_law`,
returns `refused_mode`, no passages and exit status 2. Integrity or verification
failure raises an error and returns no passages. There is no fee calculation,
formula, interpretation or applicability decision.

## Custody and date limits

The official source URL is
[the preserved 2026 Title 1 PDF](https://olls.info/crs/crs2026-title-01.pdf),
supported by the retained Office of Legislative Legal Services referral. Its
direct HTTP receipt records acquisition from **2026-09-12T22:13:16.539063Z** to
**2026-09-12T22:13:17.603959Z**, HTTP 200 and verified TLS. Acquisition time remains
separate from source-review preparation, the printed 2026 edition, PDF metadata
and historical dates appearing in source notes. The catalog's session statement
is returned as a source claim. No legal effective date is assigned.

The accepted source review inspected complete physical pages 1–6 with native-text
context; it was candidate-aware, not blind. Contents listings on the opening pages
are not section hits. The section 104 tail on page 6 is custody context and is
excluded from results. The complete PDF has 1,008 pages; preserving it does not
mean the entire title was reviewed. Exact Unicode encoding comes from native
bytes, not visual certification of each code point.

Every result has `legal_currentness: not_verified`, `research_only: true` and
`answer_safe: false`. Successful verification supports this preserved source
selection; it does not establish current law, completeness, absence of other law,
or applicability to a person's situation.

The older `geode.pipeline.research_catalog` prototype remains a separate,
metadata-only view of inherited 2025 records. Its original-source custody gap is
unchanged. The new 2026 PDF is not treated as recovery of the missing 2025 source.

## Verification and evidence

Each admitted query checks the complete source inventory, exact bytes, safe paths
and selected IDs, then runs the pinned original semantic verifier in an isolated
child. Its executable dependencies are hash-checked and compiled from verified
bytes. The child prohibits network, subprocess activity and filesystem writes.
The source package is checked again after verification and after adaptation.
Missing continuations or notes, swapped classifications, changed offsets, source
replacement, path escapes and symlinks are rejected.

The command reuses
[the preserved source-review package](../research/local_review/crs-2026-title1-source-review-2026-09-12/REPORT.md).
The [integration audit](audits/FOUR_HOUR_RUN_2026-09-12/CRS_LOOKUP/README.md)
contains the adaptation diff, typed check receipt, exported result schema,
complete examples and measured focused-test output. It identifies the preserved
prototype subset explicitly. No raw source, index, registry, coverage ledger or
2025 prototype is rewritten by this integration.
