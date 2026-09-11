---
title: Mesa County and Grand Junction — portable Atlas discovery evidence
date: 2026-09-11
package_id: mesa-grand-junction-discovery-2026-09-11
status: research_only_discovery_custody
legal_currentness: not_verified
completeness: not_assessed
canonical_intake_status: not_asserted_by_this_package
---

# Mesa County and Grand Junction discovery evidence

This package preserves the completed, bounded Atlas discovery pass for **Mesa County** and the **City of Grand Junction** as separate authorities. It contains 350 byte-identical files from the frozen local handoff and six explicitly redacted header derivatives. The six cookie-bearing header originals remain only in the unchanged local handoff; their original hashes and sizes are recorded here.

Read [the frozen report](frozen/REPORT.md) for the findings, eight priority resources and remaining gaps. [REPORT.json](frozen/REPORT.json) contains eight authority/category checklist cells. Every cell retains `legal_currentness: not_verified` and `completeness: not_assessed`.

The frozen discovery recorded:

- 13 public events and 12 distinct requested URLs: ten HTTP 200 responses, two HTTP 301 responses and one DNS failure.
- Three preserved PDFs with 250 structural pages. Eight full pages were visually checked; all native page text was retained. This was not a full transcription or legal review of 250 pages.
- Eight priority leads across land use, building/fire, fees and change instruments for each authority.
- Explicit gaps for unopened Mesa fee/building links, Grand Junction code-publisher text, a recent ordinance's unfollowed redirect, later amendments and authority boundaries.

The Mesa code's historical digest equality, Grand Junction's stated IFC adoption dates and undated fire-fee schedule keep their original qualifications. No new source request or page review occurred during packaging. Any later fee-table review, canonical intake or other work must be documented separately; none is asserted by this package.

## What is preserved

| Path | Meaning |
|---|---|
| `frozen/` | 350 exact files from the 356-file original handoff, including original reports, receipts, schemas, PDF response bodies, native text, page renders and comparison extracts. Six sensitive header files are deliberately absent. |
| `redacted/` | Six header derivatives. Each of the three `Set-Cookie` values per header was replaced in its entirety by `[REDACTED]`. All other bytes, including HTTP status and redirect `Location`, were preserved during construction. |
| `package-record.json` | Strict typed additive status, the six original-to-derivative mappings, original hashes/sizes, derivative hashes/sizes and exact verification exceptions. |
| `evidence-manifest.json` | Strict typed inventory of every distributed file except itself. |
| `validate_package.py` | Read-only portable wrapper around the unchanged frozen semantic validator. |

The frozen final manifest has SHA256 `ac6be3540538777548338de819f4ee03b55d85bd4ca347272247a4fcdb5af547`. The exact comparison input commit remains `f160dec2792a2efbcbfee8d37fd3c72477e83cb1`; packaging does not rebase or refresh its historical comparisons.

## Header redactions and historical references

Only these original paths are omitted from `frozen/`:

- `events/E004/headers.txt`
- `events/E005/headers.txt`
- `events/E007/headers.txt`
- `events/E008/headers.txt`
- `events/E009/headers.txt`
- `events/E011/headers.txt`

Each maps to `redacted/<event-id>/headers.redacted.txt`. The original sensitive header bytes cannot be reconstructed or rehashed from this distributable copy. Their original digests are custody declarations bound to the unchanged historical manifests. The new derivative digests are independently verifiable here. The originals were checked locally before omission and were not edited.

The frozen report and receipts still describe the original local handoff, its historical paths, 356 files and 353 pre-validation hash checks. Those documents are unchanged historical evidence. This README and `package-record.json` explain the six-file exception; they do not silently revise earlier receipts.

The package's ordinary validator verifies the original final manifest, every retained original and every distributed derivative. It then reuses the frozen verifier with two explicit adaptations:

1. Remove precisely the six declared, absent original-header rows from that verifier's byte-validation input. Its 347 remaining pre-validation file checks remain intact.
2. Route only those six original-header references to their labeled redacted derivatives for status/redirect checks.

No hash function, recorded size, source body, native text, report, checklist or legal meaning is substituted. The adapter does not claim that absent original header bytes were checked in the distributable environment.

## Portable validation

Use Python 3.11 or later with Pydantic 2, `jsonschema` and **PyMuPDF 1.28.2**. From this directory or another working directory, run the top-level wrapper by its absolute path:

```sh
PYTHONDONTWRITEBYTECODE=1 python /absolute/path/to/mesa-grand-junction-discovery-2026-09-11/validate_package.py
```

The wrapper reads only local package files and prints its result. It needs no network, original handoff location, Git history or live control-plane files. Run without Python's `-O` option because the frozen verifier uses assertions. Use this top-level wrapper, not `frozen/validate_package.py` directly: the latter correctly expects the six original header files, which are absent here.

The copied `frozen/capture.py` and `frozen/build_report.py` are historical implementation artifacts. Do not execute them to refresh or rebuild this package. No collector, publisher, scheduler, bot assignment or follow-on task was activated.
