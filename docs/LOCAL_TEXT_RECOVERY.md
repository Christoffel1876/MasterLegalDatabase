---
title: Local code, scan and fee evidence recovery
status: research_only
updated: 2026-09-10
---

# Local code, scan and fee evidence recovery

This collection makes previously inaccessible local publications available for
research while retaining exact originals and unresolved legal questions. It does
not establish complete Colorado local-law coverage or certify current law.

## Read the evidence in order

1. `_CONTROL_PLANE/LOCAL_COVERAGE_LEDGER.json` identifies authority, source,
   retrieval time, original bytes and remaining subject gaps.
2. `_CONTROL_PLANE/MUNICIPAL_EXPORTS_2026-09-10.json` binds the Golden and
   Georgetown exports to official municipal referrals, publisher client/product
   IDs, publication editions, table-of-contents roots and embedded dependencies.
3. `09_Municipal_Authorities/_verification/municipal_exports/text.jsonl`
   contains research text with physical-page or publisher-node citations.
4. `_DERIVED/local_ocr/scans-2026-09-10/` and
   `_DERIVED/local_ocr/fees-2026-09-10/` contain unreviewed machine text, ordered
   page receipts, source hashes and explicit collection summaries.
5. `research/local_review/amendment-excerpts-2026-09-10.json` and
   `research/fees/fee-scan-excerpts-2026-09-10.json` record specified passages
   compared with source-page images, including explicit OCR corrections.
6. `research/fees/fee-reconciliation-2026-09-10.json` records sampled fee findings,
   source conflicts and open amendment chains. It is not a fee calculator.

## Preserved editions and boundaries

Golden's export contains 1,202 physical PDF pages, Supplement 20, through
Ordinance 2292 adopted April 28, 2026. The publisher reports an update on
July 20, 2026. Georgetown's public print export contains 1,384 ordered chunks
covering all 22 requested top-level contents nodes, Supplement 15, through
Ordinance 4 enacted April 23, 2024. Its publisher update is July 11, 2024.
Chunks include headings and other material; they are not a count of legal duties.
All 12 linked Georgetown images are preserved, including one logo and 11
substantive geology, hazard and slope plates.

The proof validator verifies the municipal referral and publisher identity
chain, complete physical pages or ordered print chunks, source hashes and
linked images. It does not prove that the publisher included every enactment,
that maps remain current, or that incorporated external codes are collected.
Georgetown's later ordinances remain separate from its older consolidated code.

Golden's public download service returned a temporary signed URL. The original
PDF bytes are preserved. The durable response evidence deliberately removes the
signed query, retaining its stable storage URL and the original response's hash.
The exact signed response remains local runtime evidence and is excluded from
Git. Offline validation can recompute the PDF and redacted response hashes; it
cannot recompute the excluded original response hash. The vendor application
JavaScript also remains local runtime evidence; the repository stores its public
URL, original hash and an explicitly derived endpoint-inspection summary instead
of the unrelated vendor bundle. Offline checks verify that summary, not the
excluded original script bytes. Both limits are explicit in the manifest and
validation result.

## OCR is a separate evidence layer

The baseline contains all 316 pages of 22 image-only PDFs. The supplement covers
all 48 pages of four further PDFs, including Golden's mixed text/scanned fee
schedule. All 364 physical pages have records; no page cap was used. There were
no engine failures. There are 267 flagged pages, including one with no recognized
text. The blank result is Clear Creek document 14432, physical page 12; visual
inspection showed a white page with small scan speckles and no visible text.

The baseline receipt intentionally retains `status: failed` because empty OCR
cannot certify text coverage. The supplement is `fully_collected`. That label
means its machine page records are present, never legally reviewed or accurate
in every character. CI accepts only the explicitly identified baseline blank
page and verifies all receipts and original hashes; it does not suppress general
OCR errors. Every page remains `machine_ocr_unreviewed` even when a separate
record checks an excerpt from it.

The on-device Apple Vision adapter uses accurate English recognition, revision 3,
CPU processing and no language correction. PDFs are rendered as full pages at
300 DPI in RGB. Each page records engine/OS settings, source/page identity,
rendered-image and text hashes, line boxes and confidence. High confidence alone
does not establish accuracy. Handwritten dates and legal citations showed errors.
Images remain reproducible from the immutable PDF and recorded render settings;
large transient render files are excluded from Git.

`verified_local_ocr` refuses an existing output directory. A later OCR pass must
create another immutable collection. `--source-id` selects an entire PDF, including
mixed native and scanned pages. Ordinary Linux CI verifies the saved evidence
without requiring Apple Vision or network access.

```bash
python -m geode.pipeline.local_coverage \
  --ledger _CONTROL_PLANE/LOCAL_COVERAGE_LEDGER.json --root .
python -m geode.pipeline.municipal_code_export \
  --manifest _CONTROL_PLANE/MUNICIPAL_EXPORTS_2026-09-10.json --root .
python -m geode.pipeline.local_text_review --root . \
  --review research/local_review/amendment-excerpts-2026-09-10.json
python -m geode.pipeline.verified_local_ocr --root . \
  --ledger _CONTROL_PLANE/LOCAL_COVERAGE_LEDGER.json \
  --output _DERIVED/local_ocr/fees-2026-09-10 --validate-only
```

Validating the baseline through the OCR CLI returns exit code 1 for its declared
blank page. `validate_ocr_collection` separately returns the verified summary;
callers must inspect its status, failed pages and blank pages.

## Next substantive review

- Reconcile Georgetown's post-April-2024 ordinances with its consolidated code,
  including overlapping changes to Chapter 15.20 and charter-dependent dates.
- Reconcile Golden's post-April-2026 code changes and the adopting instruments
  for the comprehensive fee schedule and separately published building fees.
- Resolve the fee conflicts recorded in the fee study, including inspection
  minimums, truck-haul fees, duplicated labels, unit omissions and waiver routes.
- Review remaining OCR tables, exceptions, citations and incorporated external
  codes before extracting canonical obligations or calculating costs.
- Continue statewide municipality, county and special-district collection; the
  two municipal exports do not close the statewide coverage gaps.

The always-on Mac collector setup remains deferred until the user has access to
that machine. This evidence recovery does not install or enable a new schedule.
