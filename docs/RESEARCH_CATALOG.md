---
title: Isolated CRS research catalog
status: three_record_derived_metadata_prototype
legal_currentness: not_verified
answer_safe: false
---

# Isolated CRS research catalog

This offline prototype finds metadata for exactly three derived Title 1 sections:

- `CRS-1-1-101` — Short title.
- `CRS-1-1-102` — Applicability.
- `CRS-1-1-103` — Election code liberally construed.

The built package is `.geode_runtime/research_catalog/crs-first3-v1`. Its manifest SHA-256 is
`230077e63761ab368367c6e7e834d9b298a1bfab65d7a07b32aa189488520acb`.
The catalog filename is `RESEARCH_CATALOG.local-subset.v1.jsonl`.

Results contain metadata and exact byte locations in frozen derived files. They do not return
statutory body text as a verified legal answer. The package preserves the complete CRS index,
Title 1 metadata file and Title 1 Markdown for custody; **only the three selected sections are
admitted and bound across those inputs**. Copying complete files does not validate every row.

Original custody remains unresolved: the inherited source path names a former Windows checkout
and is never opened. Recorded source URLs, retrieval/update dates, the 2025 edition label and
any effective-date field remain inherited claims. Package creation time is separate from source
acquisition. Every result retains `derived_record_only`, `answer_safe: false` and
`legal_currentness: not_verified`. A missing match says nothing about legal absence or applicability.

To resume in a new terminal, set these paths and use the existing package. The Python executable
below is the current local verification environment; substitute another environment containing
the project's dependencies if that temporary environment is no longer available.

```bash
GEODE_ROOT="/Users/mcoors/Documents/Project Geode/MasterLegalDatabase"
GEODE_PYTHON="/private/tmp/geode-status-venv/bin/python"
GEODE_PACKAGE="$GEODE_ROOT/.geode_runtime/research_catalog/crs-first3-v1"
cd "$GEODE_ROOT"

PYTHONDONTWRITEBYTECODE=1 "$GEODE_PYTHON" -B -m geode.pipeline.research_catalog query \
  --package "$GEODE_PACKAGE" --list-records

PYTHONDONTWRITEBYTECODE=1 "$GEODE_PYTHON" -B -m geode.pipeline.research_catalog query \
  --package "$GEODE_PACKAGE" --query "Short title"
```

Queries search section IDs and titles, not the complete statutory body. Results contain at most
three records. Every non-refused query validates the closed package inventory, exact input hashes,
selected record/body bindings, schema and implementation contracts before returning JSON.

When running outside the repository, explicitly provide the module search path. The absolute
`--package` path alone does not make the `geode` Python module importable. Do not add `-I`, which
ignores `PYTHONPATH`.

```bash
cd /private/tmp
PYTHONPATH="$GEODE_ROOT" PYTHONDONTWRITEBYTECODE=1 \
  "$GEODE_PYTHON" -B -m geode.pipeline.research_catalog query \
  --package "$GEODE_PACKAGE" --list-records
```

Current-law mode and detected legal questions are refused before opening package evidence:

```bash
PYTHONPATH="$GEODE_ROOT" PYTHONDONTWRITEBYTECODE=1 \
  "$GEODE_PYTHON" -B -m geode.pipeline.research_catalog query \
  --package "$GEODE_PACKAGE" --list-records --mode current-law
```

| Exit | JSON status | Meaning |
| --- | --- | --- |
| 0 | `built` | A new isolated package was created. |
| 0 | `matched` | Selected metadata matched the query or list request. |
| 0 | `no_matching_record` | No admitted metadata matched; no absence conclusion. |
| 1 | `invalid` | Input, path, package, binding or query-contract validation failed. |
| 2 | `refused_current_law` | The requested legal-answer mode is unsupported. |

Malformed command-line options can instead produce normal argparse usage output and exit 2.
Handled validation and I/O failures use the stable JSON envelope; do not treat an error as an
empty result.

A fresh build is optional when resuming. It must use a **new direct-child directory** under
`$GEODE_ROOT/.geode_runtime/research_catalog/`; names permit lowercase letters, digits, hyphens
and underscores, begin with a lowercase letter or digit, and have at most 80 characters. Existing
output directories are refused, including an unchanged prior package.
For example, from any working directory after setting the variables above:

```bash
PYTHONPATH="$GEODE_ROOT" PYTHONDONTWRITEBYTECODE=1 \
  "$GEODE_PYTHON" -B -m geode.pipeline.research_catalog build \
  --root "$GEODE_ROOT" \
  --output "$GEODE_ROOT/.geode_runtime/research_catalog/crs-first3-fresh-copy"
```

Builds admit only the fixed input hashes and selected IDs. Changed inputs or implementation
contracts require review; do not edit the manifest, schema or pins merely to make validation pass.
The catalog and manifest are deterministic for the same contracts and inputs; `receipt.json`
records the actual creation time separately. Staging is checked before publishing the new directory.

This package is ignored local research output. It is not connected to the normal retrieval
backend, search database or answer pipeline, and it replaces none of the missing original LFS
catalog/index/queue objects. It makes no coverage or current-law promotion.
