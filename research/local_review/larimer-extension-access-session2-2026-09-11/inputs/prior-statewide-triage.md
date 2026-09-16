---
title: Statewide next-intake triage
reviewer: Atlas
date: 2026-09-11
scope: read_only_local_evidence_and_planning
legal_currentness: not_verified
network_requests: 0
repository_changes: false
---

# Statewide next-intake triage

**Reconcile the existing evidence assignments before using the coverage ledger as a download queue.** The seven authorities represented by today's 46 manual originals still have all 84 of their checklist cells marked `missing` in the older recovery ledger. These cells mean no evidence is assigned there; they do not mean the newly retained documents are absent. A future mapping pass should connect exact source IDs and review scopes while retaining incomplete/currentness flags. No mapping or promotion was performed here.

This is a working-tree snapshot with 21 exact input file hashes in `TRIAGE.json`, not a Git commit certification. It includes current registries, recovery ledger, manual archive/ledger/report, historical attempts, ownership corrections and selected research entry points. No source was opened on the web; no source discovery, tests, pipeline execution or repository writes occurred. The limited byte checks described below are read-only custody checks.

## Identity is not collection coverage

| Authority group | What is actually represented | Limit |
| --- | --- | --- |
| Counties | 64 named identities in the recovery ledger; local registry has 64 homepage rows plus 931 county-source rows | The identity crosswalk uses the 2025 Gazetteer; the current active-government universe and legal-source coverage are not certified. |
| Municipalities | 273 dated incorporated-place reference identities in the ledger; inherited registry has 128 identity rows and 2,075 source rows spanning 272 named municipality IDs plus `CO-MUNICIPAL-STATEWIDE` | The statewide source bucket is not a municipality. The 2025 reference includes Bonanza with FUNCSTAT I and adds Sheridan Lake; registry prose still describes the older reconciliation. These are dated geography findings, not a 2026 operating-status audit. |
| Districts and provider | Named district roles are `CO-DISTRICT-BVSD` and `CO-DISTRICT-WEST_METRO_FIRE`; `CO-DISTRICT-DENVER_WATER` keeps its legacy ID but is classified `public_provider` | There is no verified statewide district denominator. DOLA's 3,820 attribute rows, 3,600 distinct nonzero LGIDs and 220 zero-ID rows are discovery data; status/type codes and service-area overlaps remain unresolved. |

The shared 12-category checklist is: identity/service area, codified rules, adopted changes, land use/zoning, building/fire, permits/licenses, fees, taxes, health/environment, roads/utilities, enforcement/appeals and policies/guidance. Exact keys are preserved in the recovery ledger. Not every category necessarily applies to every authority; an unassessed cell is not proof of either applicability or exemption.

The recovery ledger contains 340 authority roles and 4,080 checklist cells: 4,026 `missing`, 45 `legal_documents_preserved` and nine `supporting_evidence_only`. Its 120 source records include catalog/proof material as well as legal publications. Six pilots are Clear Creek, Jefferson, Golden, Georgetown, West Metro and Denver Water. No category is certified complete, current or legally reviewed. Do not turn these counts into a percentage of Colorado law collected.

## Attempts, retained bytes and reviews are separate

| Evidence set | Read-only observation | What it does not establish |
| --- | --- | --- |
| `_CONTROL_PLANE/LOCAL_DOWNLOAD_MANIFEST.jsonl` | Streamed 48,390 historical rows: 39,050 `downloaded` claims and 9,340 `failed`; 3,056 source IDs, 10,046 distinct requested/source URLs and 11,098 reported digests | Rows repeat attempts and aliases. A downloaded status is not retained bytes or legal review. |
| Legacy `raw_path` references | All 34,107 distinct paths were absent at their normalized repository location; normalization retained the suffix beginning `_RAW_ARCHIVE/` from inherited Windows paths | This is path absence, not global hash absence. Seventeen current manual PDFs and 21 ledger source records match historical digests at other paths. |
| `_RAW_ARCHIVE/manual_intake/manual_source_intake_manifest.jsonl` | 46 distinct PDF hashes, 299,898,215 bytes; all 46 present files matched their recorded size and SHA-256 in this read-only check | Nine records use `manual_official_download`; 37 use `received_review_package`. Received originals, browser-derived material and disputed acquisition associations retain their own qualifications. A hash does not authenticate enactment. |
| `_CONTROL_PLANE/MANUAL_SOURCE_INTAKE_LEDGER.jsonl` and report | 47 control records: the 46 local PDFs plus ledger-only `EO-2019-007`, whose referenced original is missing | The older source-limitation register's “resolved” narrative does not recreate the missing executive-order file. It is outside the geographic priorities below. |
| `research/local_review/README.md` | Navigation distinguishes scoped checked passages, full-page source structure, tables, drafts and later external-review supplements | Intake and later review packages overlap by source hash. Their source/page totals must not be added; a completed excerpt check is not whole-document or current-law certification. |

The 46 manual records cover Arapahoe (1), Larimer (14), Weld (3), Mesa (3), Fort Collins (19), Greeley (3) and Grand Junction (3). They are 21 county-layer and 25 municipality-layer records. Their hashes do not overlap the 120 recovery-ledger source hashes, but these are different inventories with different roles; adding 120 and 46 would not give a legal-document coverage total.

Examples of review scope matter: Arapahoe's two-page fee table has 36 checked rows; Larimer building-fee reviewed text does not certify all five pages' numerical tables; Greeley's three sources have six full pages of source QA; Mesa's building exhibit has a separate full five-page table review; Grand Junction Ordinance 5269 has 29 pages of structural/selected-language review, not every-character certification. Fort Collins' eight-page wildfire source is still a discussion draft after review. The research-only Larimer extension package and Arapahoe resolution attachment are retained outside the raw manifest and must not be counted as additional authenticated enacted originals.

## Five next documentary priorities

The order below targets specific gaps supported by retained evidence. It is not a population ranking or an estimate of regulatory burden. Each can end with a documented unresolved result; failure to locate an instrument does not establish that it never existed.

### 1. CO-COUNTY-LARIMER

**Existing IDs:** `larimer-data-center-moratorium-sd004-04`, `larimer-february-meeting-packet-sd007-08`.

Separate executed February and July extension instruments and final July action are not supplied. The unsigned addendum is a browser-print derivative; received minutes have disputed exact download association.

**Next intake:** Seek the exact executed extension instruments and their official record references, starting from the already retained meeting evidence rather than another agenda-packet dump.

**Acceptance boundary:** Retain each actual official original with its adoption/execution/term statements and referral. Preserve the literal August 25, 2025 draft date and April 7, 2026/reception recital as unresolved until evidence reconciles them. Failure to locate is not proof of absence.

**Read first:**

- `research/local_review/larimer-extension-evidence-sherlock009-2026-09-11/received-pdfs/july13_attachment_5519.pdf`
- `research/local_review/larimer-extension-evidence-sherlock009-2026-09-11/received-pdfs/july13_addendum_5539.pdf`
- `research/local_review/larimer-extension-evidence-sherlock009-2026-09-11/received-pdfs/feb09_minutes.pdf`
- `research/local_review/ebenezer-012-2026-09-11/ATLAS_REVIEW.md`

### 2. CO-MUNICIPAL-FORT_COLLINS

**Existing IDs:** `fort-collins-wildfire-code-sd005-05`, `fort-collins-fee-catalog-atlas-sd004-14`.

The eight-page wildfire candidate is a discussion draft with placeholders and blank execution fields. Nineteen manual PDFs and a structured fee HTML snapshot are retained; retention is not a final enacted code or authenticated adoption chain.

**Next intake:** Prioritize the final adopting ordinance and enacted wildfire amendments matching or superseding the retained draft; use the existing code catalog to select the exact instrument, not a whole new city crawl.

**Acceptance boundary:** Keep the draft unchanged and distinguish final text from struck bodies, highlights and blank fields. Bind adopting instrument identity, publication/edition and any effective-date statements. Keep City, Poudre Fire Authority and Larimer County fee contexts separate.

**Read first:**

- `research/local_review/ebenezer-013-2026-09-11/README.md`
- `research/local_review/ebenezer-013-reconciliation-2026-09-11/README.md`
- `research/local_review/fort-collins-fee-catalog-2026-09-11/extraction.json`
- `research/local_review/fort-collins-intake-2026-09-11/README.md`

### 3. CO-COUNTY-MESA / CO-MUNICIPAL-GRAND_JUNCTION

**Existing IDs:** `mesa-land-development-code-atlas-directed`, `mesa-planning-fees-2017-2018-atlas-directed`, `mesa-building-fees-exhibit-a-atlas-directed`, `grand-junction-ifc-ordinance-5269-atlas-directed`, `grand-junction-fire-fees-atlas-directed`, `grand-junction-ordinance-5340-atlas-directed`.

Six PDFs are already retained. Mesa adopting instruments remain uncollected; planning-school expiration differs between PDF (2020) and HTML (2022); building exhibit refers to an absent separately labeled Table 3B. City Ordinance 5269 gives incompatible September 1 and August 18, 2025 effective statements.

**Next intake:** Use one directed county/city batch to retrieve the cited fee adoption/suspension instruments and any official clarification or later instrument resolving the city effective-date conflict; do not redownload these six PDFs as newly missing.

**Acceptance boundary:** Separate county ownership from joint building administration and city enactments. Preserve both dates and the 2017/2018 schedule label. Treat Ordinance 5340 October 5, 2026 effect as future at receipt, not already operative. Record a bounded unlocated result for missing Table 3B rather than inventing it.

**Read first:**

- `research/local_review/mesa-grand-junction-directed-intake-2026-09-11/README.md`
- `research/local_review/mesa-building-fees-atlas-source-review-2026-09-11/SOURCE_REVIEW.md`
- `research/local_review/grand-junction-ordinance5269-atlas-source-review-2026-09-11/SOURCE_REVIEW.md`

### 4. CO-MUNICIPAL-GREELEY

**Existing IDs:** `greeley-building-fees-sd008-06`, `greeley-development-impact-fee-memo-sd008-07`, `greeley-water-sewer-proposed-pif-notice-sd008-08`.

The 2020 utility notice makes March 2021 conditional on adoption; the later impact memo anticipates further utility adoption. The building schedule has 2024 headings plus an unlabeled 8/18/2026 footer.

**Next intake:** Request the bounded final adopted water/sewer PIF instrument and matching adopted schedule/edition, then the adopting basis for the building schedule; retain the already reviewed notice and memo as supporting history.

**Acceptance boundary:** Bind Board/city instrument identity and actual table edition, exceptions and date roles. Do not promote the 2021 proposal, the 2026 footer or a future-action memo to current fee law. Weld County contractor recipients do not transfer authority ownership.

**Read first:**

- `research/local_review/greeley-fees-atlas-source-review-2026-09-11/README.md`
- `research/local_review/weld-greeley-intake-sherlock008-2026-09-11/README.md`

### 5. CO-DISTRICT-WEST_METRO_FIRE

**Existing IDs:** `west-metro-codes`, `west-metro-2024-adoption`, `west-metro-fees`.

Adoption and fee guidance are retained, while official service boundaries, local adoption overlap, incorporated code and the fee adoption chain remain unverified. Fees are supporting_evidence_only in the ledger.

**Next intake:** Complete one named fire-district intake bundle: official service-area/governance evidence plus the exact adopting fee instrument and code-adoption/overlap records. Use it as the district intake pattern before expanding an unverified statewide district universe.

**Acceptance boundary:** Retain authority-specific evidence and boundary dates; keep shared county/city service relationships separate. No count of active districts is inferred from 3,820 DOLA attribute rows or 3,600 nonzero LGIDs. Denver Water remains separately classified public_provider.

**Read first:**

- `_CONTROL_PLANE/LOCAL_COVERAGE_LEDGER.json`
- `_RAW_ARCHIVE/local/coverage/0d3dff775d65a8c93f80824a6c12f19073c4beeac1a304e04f3f00e319696d6f.pdf`
- `_RAW_ARCHIVE/local/coverage/d691467b750ed3afa3c3fcf06a566bde889d6aef31d76ae7481380db67bf27cb.html`

## Known blockers versus unassessed work

Two observed inputs remain literal LFS pointers: `_CONTROL_PLANE/LOCAL_REVIEW_QUEUE.jsonl` expects SHA-256 `c65a0f190fd5d5dca7810c47afc7e6843cd78520242add1fe6951545fe92ad00`, 72,395,471 bytes; `08_County_Authorities/_index.jsonl` expects `e896fc157617cfd9cd9839bf2bf955d893b66d7de514107e8b3c98dc4795c806`, 172,131,787 bytes. No recovery attempt or corpus validation was made in this task. They remain missing original inputs, not a reason to synthesize replacement history. Retrieval-readiness analysis is separate.

For other counties and municipalities, catalog/source-registry entries and historical attempts require individual custody and role assessment. `candidate_found`, a landing page, an inherited “downloaded” cell, or a directory identity cannot certify a complete code or absence of later amendments. Conversely, missing recovery-ledger assignments must not trigger duplicate acquisition of already retained sources. The Boulder correction policy remains the authority for the three retired county misattributions; this triage neither restores them nor transfers all city-hosted documents to county ownership.

Golden and Georgetown already have preserved publisher exports, and the selected OCR batch already has all 364 page records with explicit low-confidence/blank-page limits. Their next work is amendment/fee-chain and scoped text reconciliation, not another blanket code export or a claim that every page is reviewed. Weld Ordinance 26-01 and the 2026 environmental-health fee schedule have also been reacquired and reviewed; neither should remain a “missing original” request just because older discovery could not fetch it.

All report paths above are relative to `MasterLegalDatabase/`. Only this planning handoff was written. No schedule, bot assignment, code change, ledger update or new collection task was created.
