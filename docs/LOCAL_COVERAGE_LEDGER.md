---
title: Local authority collection and review process
status: partial_collection
updated: 2026-09-10
---

# Local authority collection and review process

The machine-readable work queue is
`_CONTROL_PLANE/LOCAL_COVERAGE_LEDGER.json`. It records authority identities,
dated directory evidence, preserved source files, and a category checklist for
every listed authority. It is a collection inventory, not a complete list of
current Colorado local law.

The inherited layer indexes and the new collection ledger measure different
things. `geode.pipeline.coverage_dashboard` reports what the inherited indexes,
source registries, and historical download log contain. The ledger records the
separately verified originals collected during recovery. Neither a registered URL
nor a preserved PDF is counted as a fully reviewed current rule.

## Process

1. Reconcile each named authority against dated official directories. Retain
   spelling aliases, inactive-government flags, boundary ambiguities, and
   unresolved classifications. A district boundary dataset is a discovery queue,
   not an automatic count of active regulatory governments.
2. Investigate every checklist category: identity/service area, codified rules,
   adopted changes, land use/zoning, building/fire, permits/licenses, fees, taxes,
   health/environment, roads/utilities, enforcement/appeals, and policies/guidance.
   These are questions to investigate; the checklist does not assume each authority
   regulates every subject. An absent link is not evidence that a category is
   legally inapplicable.
3. Preserve exact original bytes from official sources and their explicitly
   delegated publishers. Record requested and final URLs, retrieval time, hash,
   format, source role, and currentness limits. Respect access restrictions and
   record blocked or unattempted work. Discovery runs use explicit request and
   byte budgets; their results are not exhaustive crawls.
4. Extract all substantive text, including scans, tables, exceptions and local
   amendments. Keep source navigation, forms, process guidance and binding legal
   text distinct. Report unreadable pages and extraction limits before using the
   text to answer legal questions.
5. Reconcile adoption, effective dates, repeals and supersession against the
   underlying ordinances/resolutions. Compare uncodified changes with the code's
   stated supplement date. Review fees, local model-code amendments and scope.
   Human/legal review remains pending for this batch.
6. Promote only reviewed records through the existing ingestion and verification
   gates. Until a separately tested review contract exists, this collection schema
   rejects claims of complete coverage or verified current law.
7. Add reviewed source catalogs and document identities to scheduled monitoring
   in deliberate, tested batches. Detect newly published links as pending review
   work before expanding a fixed download manifest. Preserve each previous edition
   and verify actual scheduled-run receipts as well as source freshness.

## Status meanings

| Field | Meaning |
|---|---|
| `missing` | This ledger has no preserved evidence assigned to that category. |
| `supporting_evidence_only` | Directory, catalog, guidance or form evidence is preserved. |
| `legal_documents_preserved` | At least one legal document or fee schedule is preserved; completeness, currency and legal interpretation remain unverified. |
| `partial` | Some evidence exists, with explicit remaining collection/reconciliation work. |
| `not_verified` / `pending` | Currentness and legal review are still open. |

Preserved-source counts measure captures, not distinct obligations. An identical
original can support several categories or be observed at more than one URL.
Identity counts also do not identify all overlapping authorities applicable to
a property or activity.

## Reproduce the checks

Use the frozen dependencies in `requirements-ci.txt` and `requirements-county.txt`.

```bash
python -m geode.pipeline.local_coverage \
  --ledger _CONTROL_PLANE/LOCAL_COVERAGE_LEDGER.json --root . \
  --output-dir .geode_runtime/local-coverage-report
python -m pytest tests/test_local_coverage.py tests/test_municipal_directory.py -q
python -m geode.validate --layer all
```

The ledger checker verifies all declared originals offline, including their exact
hashes and sizes, archive confinement, readable formats and delegated-source
catalog links. It checks every authority/category/evidence reference and derives
collection states from source roles. It does not authenticate legal force,
interpret a rule, or contact a publisher to establish present-day currency.

The ordinary scheduled county collector still checks its original four catalogs
and thirty selected documents. This collection batch does not expand that daily
manifest or install the deferred always-on Mac collector. Missing legacy LFS data
and failures of hosted collection remain visible limitations.
