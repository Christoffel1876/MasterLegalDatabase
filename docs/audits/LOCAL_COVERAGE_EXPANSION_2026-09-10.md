---
title: Local coverage expansion — September 10, 2026
status: partial_source_preservation
updated: 2026-09-10
---

# Local coverage expansion

This batch adds 52 originals (43,596,023 bytes) and integrates 54 previously preserved
county originals into a 106-source collection ledger. Every source has an official
requested/final URL, retrieval timestamp, exact SHA-256, byte count, document role
and explicit currentness limits. Nothing in this batch is promoted as verified
current law.

The ledger has 340 authority-role checklists: 64 counties, 273 municipal reference
identities, two district candidates and Denver Water as a public provider. Denver
and Broomfield each appear in county and municipal roles; this is not a count of
340 independent governments. Six authorities have focused source collection:
Jefferson County, Clear Creek County, Golden, Georgetown, Denver Water and West
Metro Fire. Every authority has twelve investigation categories, for 4,080 work
items; category applicability itself may still require verification.

## Named jurisdiction correction

Sheridan Lake town (Census GEOID 0869700) is the sole named municipality missing
from the 272 inherited municipal source IDs. The Census January 1, 2025 table has
273 incorporated-place records; the separate Colorado boundary extract has 273
names across 274 rows, with Hudson repeated. All 64 county and 272 inherited
municipal IDs matched the named federal references after documented aliases.
The ledger retains each source name, GEOID and source status in its identity basis.

The CML materializer had excluded the misspelling “Sheriden Lake” as nonmunicipal.
It now normalizes that spelling, retains the original name and evidence URL,
validates output records and separates generation time from unknown source
retrieval time. The existing historical queue and source registry are retained;
the corrected ledger adds Sheridan Lake as a pending identity without inventing
an official website or legal records.

The Census reference has 272 FUNCSTAT A entries and Bonanza FUNCSTAT I. It is not
represented as 273 currently operating governments. District discovery retrieved
3,820 public attribute rows, including 3,600 unique nonzero LGIDs and 220 unnamed
zero-ID rows. The latter are not invented authorities. District type/status codes
remain uninterpreted because the linked dictionary export failed. The restricted
LGIS directory was not traversed past its terms/reCAPTCHA gate.

Preserved evidence IDs: `census-incorporated-2025`, `census-counties-2025`,
`dola-municipal-names`, `dola-district-attributes`, `dola-district-data-metadata`,
`dola-terms`. Their exact archive paths are in the ledger.

## County collection

The bounded county pass preserved 26 additional sources: nineteen PDFs containing
278 pages and seven catalogs. Together with 54 earlier originals, the ledger now
contains 80 county source captures. It preserves all thirteen PDFs linked from
the observed Clear Creek ordinance catalog, including the nine omitted from the
first pilot. That catalog is not an exhaustive record of every adopted measure.
The original 88-link pilot inventory still has 49 uncollected URLs: 48 Jefferson
zoning sections and a wildfire-interface map.

Material findings, with ledger evidence IDs:

- `cc-building-r26-19`: 119 scanned pages. Visual review of physical pages 1–4
  identifies the 2026 building/fire adoption. Page 2 supplies the adoption,
  applicability language and rescission of R-24-82. OCR and the full amendment
  chain remain open.
- `cc-ordinance-16803`: the two-page Ordinance 4-A original provides repeal
  evidence beyond the previous catalog label. Extraction, effective-date and
  supersession review still remain necessary.
- `cc-marijuana-tax-link-16501` is a reporting form; `16502` is the resolution.
  The official catalog has their labels swapped. Exact labels are retained in
  provenance while document roles follow the inspected originals.
- `cc-marijuana-waivers` is a liability-release/indemnification form, not a
  fee-waiver enactment.
- `jeff-fire-code`, physical page 1 section B.2, distinguishes district fire
  codes. A county code alone cannot establish every parcel's applicable rules.
- The previously preserved 2020 and 2022 Clear Creek Planning fee documents
  remain unreconciled with adoption records and later fee changes. A Sheriff's
  fee catalog is not substituted for the Planning fee schedule.

County categories remain incomplete. The next pass needs OCR, the uncollected
building supplements, fee/adoption chains, health and road sources, uncodified
resolutions and district boundaries.

## Municipal and provider collection

Seventeen additional originals contain seven PDFs (126 pages) and ten HTML
responses. They are preserved evidence with the following limits:

| Authority | Preserved evidence | Remaining work |
|---|---|---|
| Golden | Official code links, building/process and tax guidance, outfitter form | Municode response is only an app shell. Obtain charter/code text, adoption instruments and complete current fees/forms. The outfitter form is dated 05/22. |
| Georgetown | Four signed 2026 adoption/amendment PDFs and enactment catalog | Four scans need OCR. Code/charter text and the complete fee schedule remain missing. Resolution 6 concerns water-system development fees; Ordinance 5 concerns wireless facilities. |
| Denver Water | 90-page operating rules and separate 2026 drought resolution | Reconcile intervening board actions, rates and boundaries. The drought resolution states October 1 effectiveness; do not apply future provisions as current on September 10. |
| West Metro Fire | District adoption resolution and permit-fee page | Scan needs OCR; incorporated IFC, district boundaries and municipality/county adoption overlap remain open. |

The five municipal/provider scans plus eleven new county scans produce sixteen
new image-only PDFs. Across all 106 sources, 22 PDFs need OCR. A detected text
layer in the other PDFs is not a guarantee of complete or accurate extraction.

## Next collection order

1. OCR and verify the preserved scans against original pages, starting with the
   2026 county and Georgetown amendments and the West Metro adoption.
2. Obtain full municipal code/charter text and reconcile adopted changes against
   each code supplement date; then reconcile the complete fee schedules.
3. Reconcile district identities and official service areas before attributing
   county/municipal/provider rules to a property or activity.
4. Work through the remaining category items, keeping unknown applicability and
   blocked sources visible; expand the fixed daily monitoring manifest only
   after the sources and collector behavior are tested.

## Verification boundary

The offline ledger check validates schemas, references, hashes, sizes, confined
archive paths, usable document formats, PDF page/text-layer metadata and catalog
links to delegated publishers. The schema rejects complete/current/reviewed
claims at this collection stage. Validation does not establish legal force,
complete extraction, present-day currency or statewide coverage.

The county daily collector still selects its original four catalogs and thirty
PDFs. Hosted collection has not been established as reliable, and the always-on
Mac setup remains deferred. Six historical LFS files remain missing; their
unavailability is not replaced by these partial source captures.

See `docs/LOCAL_COVERAGE_LEDGER.md` for the process and commands,
`docs/audits/LOCAL_COVERAGE_2026-09-10.md` for the category view, and
`_CONTROL_PLANE/LOCAL_COVERAGE_LEDGER.json` for the machine-readable evidence queue.

## Validation results

- Full repository suite: 1,109 tests passed.
- Focused ledger/directory/dashboard checks: 119 tests passed using frozen dependencies.
- Branch-inclusive coverage: ledger 98.54%, municipal directory 98.62%, existing dashboard 96.90%.
- All 106 archived source blobs match the ledger's SHA-256 and byte lengths in Git's index.
- Whole-corpus validation retains the same two inherited failures: the county index is an
  unavailable LFS pointer, and the local review-summary check cannot read its underlying
  missing LFS review queue. The summary JSON itself is not corrupted.
- These are integrity and regression results, not legal-currentness certification.
