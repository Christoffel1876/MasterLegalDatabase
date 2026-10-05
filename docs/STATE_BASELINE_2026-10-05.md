---
title: Colorado state source baseline — October 5, 2026
status: CCR retained-catalog PDF baseline; wider state collection remains open
legal_currentness: not_verified
answer_safe: false
---

# Colorado state source baseline — October 5, 2026

The CCR collection now retains a PDF for **all 1,156 rule identities in the
captured 25-department catalogs**, with **39,460 physical pages** of reproducible
native text. **1,155 identities also have their paired Word source.** The remaining
Word export is Transportation rule 3475, version 12137, **2 CCR 601-27**; its
ten-page PDF is retained and searchable. Public Health's **238 of 238** listed
identities now have both source formats.

This closes the PDF acquisition and native-text inventory for the retained CCR
catalogs. Those catalogs carry mixed **August 13 and August 29, 2026** publication
cutoff claims. Their observations span September 10 through October 5. This is
not a statement that every operative rule, incorporated document, historical
version, or October 5 legal change is captured. A publisher's complete PDF can
be an editorial notice, repeal notice, or navigation page rather than substantive
rule text.

## Changes in this checkpoint

| Work | Verified result |
|---|---:|
| Newly acquired Public Health PDF/Word pairs | 88 identities / 5,923 PDF pages |
| Existing Public Health V1 files newly included in native search | 20 PDFs / 313 pages |
| Department of Local Affairs source replay and native search | 26 PDFs / 180 pages; all 87 source originals replayed |
| Transportation's remaining PDF, with failed Word evidence kept separately | 1 PDF / 10 pages |
| Distinct CCR native-text union | **1,156 PDFs / 39,460 pages** |
| New 2026 B/D executive-order identities recovered | 13 PDFs / 49 pages |
| Previously indexed 2026 D orders with missing originals reacquired | 8 PDFs / 35 pages |
| Complete observed 2026 B/D catalog PDF inventory | **21 PDFs / 84 pages** |
| Latest 2025 COPRRR archive reports reacquired | 17 PDFs / 782 pages |

The October 5 native additions increase the previous **1,021-PDF / 33,034-page**
CCR search inventory by **135 PDFs / 6,426 pages**. Only 88 of those are new
complete source pairs; the remaining 47 close native-search gaps in existing
or separately retained source evidence. Counts use exact PDF hashes and physical
page identities, without counting the V1-to-V2 projection as a new acquisition.

The governor's official catalog was accessible in a normal browser despite a
failed direct HTTP request. The newly retained orders are **B 2026 001–002** and
**D 2026 009–019**. Full letter-qualified citations are preserved because the
inherited unqualified `EO-2026-001` identifier already denotes D 2026 001.
The eight previously indexed orders D 2026 001–008 now also have fresh source
PDFs, giving **21 of 21 observed B/D catalog entries** retained originals. The
verified research package preserves letter-qualified citations until canonical
ingestion handles that identity distinction. Appointments, clemency orders,
other years, and rescission/currentness review are outside this finite recovery.

The 17 COPRRR PDFs came from public Drive links exposed by the official report
archive. The inherited connector hashed each record summary, not the original
PDF bytes. Those summary hashes are preserved separately, with historical PDF
hashes recorded as unknown. A difference between these two kinds of hashes is
not evidence that a publisher changed the document. The newly retained PDFs
supply original source custody that the inherited metadata lacked.

## Evidence and reproduction

The final [identity-to-PDF ledger](audits/CCR_IDENTITY_PDF_BASELINE_2026-10-05/INDEX.json)
proves every retained selector has its exact source PDF and matches the native
PDF/page union. The source-pair audit is
[`CCR_SOURCE_BASELINE_2026-10-05.json`](../_CONTROL_PLANE/CCR_SOURCE_BASELINE_2026-10-05.json).
It reconstructs Public Health and Transportation listing denominators and
replays the older departmental source evidence and every selected agency capsule.
The stronger Local Affairs replay is recorded separately in
[`RECEIPT.json`](audits/CCR_DEPARTMENT12_NATIVE_2026-10-05/RECEIPT.json).

The 88 new source pairs, their expected native manifests, and portable rebuild
commands are in the
[`additions index`](audits/CCR_BASELINE_ADDITIONS_2026-10-05/INDEX.json).
The final seven-ledger PDF/page union and the three native addenda are in the
[`native completion index`](audits/CCR_NATIVE_COMPLETION_2026-10-05/INDEX.json).
Generated CCR native packages remain local and can be rebuilt from the committed
originals; only the ten-page standalone Transportation extraction is committed
directly. Word signature checks do not establish PDF/Word equivalence.

The [executive-order package](audits/EXECUTIVE_ORDERS_2026-10-05/README.md) and
[COPRRR package](audits/COPRRR_2026-10-05/README.txt) retain their originals,
native text, citations, receipt evidence, and independent offline verifiers.

The existing whole-department publisher flags remain **23 of 25**. The final
source inventory proves coverage across immutable, independently verified
captures; it does not retroactively mark the Public Health or Transportation
packages as admitted by the whole-department publisher. No collector ceilings
were raised, and no daily monitoring scope was expanded.

## Work still required for the wider state baseline

The state collection is not closed across all layers. The
[`legacy index materialization audit`](audits/STATE_BASELINE_2026-10-05/LEGACY_INDEX_MATERIALIZATION.json)
distinguishes existing derived files from original source paths that are absent
from this checkout. The newer CCR and CRS research packages use separate
provenance and do not silently satisfy unrelated old paths.

| Layer | Next acceptance work |
|---|---|
| CRS and Constitution | Reconcile the separate 47-PDF / 46,882-page September acquisition with section-level structure, inherited paths and currentness; preserve its existing publication boundary. |
| CCR | Consolidated publisher admission; resolve or explicitly support the one missing Word format; review substantive content, incorporated materials and source/current-law changes after the retained cutoffs. |
| Bills | Audit and restore/reacquire source custody for the inherited 12,453-record collection; verify session coverage and source-to-output joins. |
| Register and eDocket | Verify coverage behind the 8,120 inherited rows and 443 referenced source paths; complete the bounded live collection plan. |
| Executive orders | Ingest the 21 retained B/D originals, including 13 new identities, without ID collisions; audit prior years, other order types, source custody and supersession. |
| Session laws | Audit and restore/reacquire source custody behind 437 inherited records and verify the covered sessions. |
| AG opinions and COPRRR | Recover missing AG originals and broaden historical coverage; resolve the three observed 2025 Sunrise report gaps; reconcile fresh COPRRR acquisitions with inherited records. |

The current AG catalog exposes one 2026 opinion already present in the inherited
index, but its original PDF request returned an empty HTTP 202 response. The
COPRRR Music Therapists Sunrise PDF returned HTTP 403; the HVAC Technicians and
Fence Installers PDF URLs were preserved without further requests to the blocked
host. These gaps remain explicit. No outside contact was made.

Native extraction is unreviewed against page images except for previously
documented limited reviews. Search results provide source discovery, not legal
advice or approval for external reliance. County, municipal, and district
expansion remains separate from this state checkpoint.
