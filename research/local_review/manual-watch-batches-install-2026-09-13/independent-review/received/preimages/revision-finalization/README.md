---
title: Prepared additional manual source watch batches
status: PREPARED_NOT_INSTALLED_OR_EXECUTED
prepared_date: 2026-09-13
public_requests: 0
production_writes: 0
legal_currentness: not_verified
---
# Prepared additional manual source watch batches

This handoff proposes six exact preserved sources in three named two-source batches. It adds two
ordinary versioned modules, eight config/schema files, four test modules, and one operator guide.
It leaves the existing Springs module, transport helper, config and saved run byte-identical.
No installation, public request, scheduler, baseline update, source promotion or Git operation
was performed by this preparation.

The [proposed guide](proposed/docs/MANUAL_SOURCE_WATCH_BATCHES.md) explains the API and its custody
limits. `INSTALL.patch` is an additive installation diff; `TRANSPORT_CHANGES.diff` compares the
new helper against the retained original. `ADAPTER_CHANGES.diff` shows the focused changes from
the earlier two-source adapter. All installation targets are new paths. Root must review and
perform any installation or HTTP execution separately.

`proposed/` contains the installation subset. The handoff's `load_proposed.py` and `conftest.py`
load these ordinary module files for local testing without modifying the repository package.
They do not compile modified source or override an existing helper's host policy. The old builder
and initial design are retained as preparation history; the final manifest and proposed files,
not a rerun of an intermediate generator, define this reviewed revision.

```bash
PYTHONDONTWRITEBYTECODE=1 /path/to/python -B verify_preparation.py
PYTHONDONTWRITEBYTECODE=1 /path/to/python -B verify_preparation.py \
  --root /path/to/MasterLegalDatabase
```

The first command checks this closed package without requiring the original workspace. The second
also hashes current canonical source/custody inputs and preflights all three selections. It does
not import historical research-package scripts or open any HTTP connection. Source PDFs remain
in the existing repository; they are not duplicated into this code-preparation package.

For the staged focused tests, use the same Python environment that supplies the repository's
Pydantic, PyMuPDF, BeautifulSoup, JSON Schema, pytest and pytest-cov dependencies:

```bash
PYTHONDONTWRITEBYTECODE=1 COVERAGE_FILE=/tmp/manual-watch-batches.coverage \
  /path/to/python -B -m pytest proposed/tests -q -p no:cacheprovider \
  --cov=proposed/geode/pipeline --cov-branch --cov-report=term-missing
```

The default transport is disabled in the offline tests; real socket-pair fixtures exercise
framing, slow headers/trailers and deadline closure without public HTTP. The test receipt records
coverage and exact hashes. `BASELINE_CHECKS.jsonl` is the earlier six-PDF structural/hash check;
its whole raw-manifest hash is a dated preimage, not a promise that unrelated later intake cannot
append records. The final validation checks exact selected row hashes and preserves old receipt
claims separately from later verified acquisitions.
