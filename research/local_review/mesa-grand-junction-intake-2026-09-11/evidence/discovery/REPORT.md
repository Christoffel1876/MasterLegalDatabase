---
title: Atlas bounded source discovery — Mesa County and Grand Junction
date: 2026-09-11
task_id: atlas-mesa-grand-junction-discovery-2026-09-11
status: complete_with_explicit_gaps
legal_currentness: not_verified
completeness: not_assessed
scope: discovery_and_preservation_only
---

# Mesa County and Grand Junction: bounded discovery

This Atlas pass retained three actual official PDF responses and seven successful HTML responses. It identified eight priority resources across four requested categories for each authority. These are discovery and preservation results, not eight completed legal categories. No registry, raw archive, ledger, repository file or Git state was changed.

Public work stopped at **13 events and 12 distinct requested URLs**, at **20:06:42 UTC**, within the 20-event/12-target limit and before the 20:25 UTC deadline. There were ten HTTP 200 responses, two HTTP 301 responses and one initial DNS failure. The same Mesa URL succeeded on one ordinary-TLS retry. No HTTP 403 was returned, and no search, browser, authentication, hidden API or automatic redirect/retry was used. Every attempt has its own retained command metadata, headers, stderr and typed receipt.

The response bodies total **9,762,972 bytes**, of which **9,762,162 bytes** are HTTP 200 bodies. The three PDFs total **9,258,844 bytes and 250 structural pages**. Eight pages were visually inspected: Mesa land code pages 1–3; Grand Junction Ordinance 5269 pages 1, 28 and 29; both fire-fee pages. Native text from every PDF page is retained. The remaining 242 pages were not visually reviewed.

## Starting evidence and historical comparison

Exact input hashes and relevant extracted rows are in `INPUTS.json` and `inputs/`. Their hashes match commit **f160dec2792a2efbcbfee8d37fd3c72477e83cb1**. The initially observed HEAD was `69a33703a9fecb5119816ae02d4ba32d40753a55`; HEAD advanced during parallel root work, so the precise file/commit check is recorded instead of assuming the earlier commit.

- **CO-COUNTY-MESA**: 21 registry source IDs. The inherited download manifest contains 724 rows, 21 source IDs and 67 distinct requested URLs for this authority: 711 `downloaded` and 13 `failed` rows.
- **CO-MUNICIPAL-GRAND_JUNCTION**: 9 registry source IDs. The inherited manifest contains 10 rows, 8 source IDs and 9 distinct requested URLs, all marked `downloaded`.
- Both recovery-ledger authority records have 12 `missing` cells, `not_assessed` completeness and `not_verified` currentness. Their dated 2025 Census references do not certify current operating status.

The complete 48,390-line historical manifest was streamed for exact priority-URL and digest comparisons. Requested URLs are counted separately from parent `source_url` associations. The freshly retrieved Mesa PDF digest equals **41 historical records** across multiple category aliases. These are repeated records of identical bytes, not 41 independent legal documents. The two retained Grand Junction PDFs have no digest match in that manifest. None of the three PDF digests occurs in the separately hashed current 40-record manual raw manifest. These limited comparisons do not prove corpus-wide novelty or a change in law. Changed HTML hashes can reflect navigation or rotating notices.

## Eight priority resources

Each row is one resource URL. Catalogs and unopened leads are labeled explicitly.

| ID | Authority / category | Resource and evidence | Result and remaining boundary |
|---|---|---|---|
| MG-01 | Mesa / land use | [2020 Land Development Code, amended April 23, 2024](https://www.mesacounty.us/sites/default/files/2024-10/Land%20Development%20Code%20-%202020%20%28Amended%2004-23-24%29.pdf) | Actual 219-page PDF preserved (E012); same bytes as historical digest. Cover and first two contents pages checked. Later adopted amendments, maps and full text review remain open. |
| MG-02 | Mesa / fees | [Planning Fees](https://www.mesacounty.us/departments-and-services/community-development/planning/applications-and-fees-planning-department-0) | Exact `Fees` anchor on retained E010; this endpoint was **not opened**. No amounts or adopting authority verified. |
| MG-03 | Mesa / building and fire | [Building Department](https://www.mesacounty.us/departments-and-services/community-development/building) | Exact E013 anchor; endpoint **not opened**. Actual county code adoptions, amendments, fees and fire-district instruments are missing from this pass. |
| MG-04 | Mesa / changes | [PRO2026-0092 hearing notice](https://www.mesacounty.us/sites/default/files/2026-09/PRO2026-0092%20Mesa%20County%202020%20Land%20Development%20Code%20-%20Hearings%20Planning%20Commission%20October%2015%2C%202026%20and%20Board%20of%20Commissioners%20November%2017%2C%202026.pdf) | E006 labels future hearings on October 15 and November 17, 2026. PDF **not opened**; not an adopted amendment claim. |
| MG-05 | Grand Junction / land use | [Officially linked municipal-code publisher entry](https://ecode360.com/GR4464) | Exact city E009 referral; publisher endpoint **not opened**. Title 21, supplement cutoff and later changes remain unreconciled. |
| MG-06 | Grand Junction / building and fire | [Ordinance 5269: 2024 IFC adoption and amendments](https://www.gjcity.org/DocumentCenter/View/15790/2024-IFC-Adoption-Ordinance-No-5269) | Actual 29-page PDF preserved (E007); title and concluding adoption/certification pages checked. Later amendments and separate building Ordinance 5268 remain unverified. |
| MG-07 | Grand Junction / fees | [Fire Prevention Service Fees](https://www.gjcity.org/DocumentCenter/View/15794/Fire-Prevention-Fee-Schedule) | Actual two-page PDF preserved (E008), both pages viewed. No printed edition/adoption/effective date observed. This is not the complete city development-fee corpus. |
| MG-08 | Grand Junction / changes and land use | [Ordinance 5340 catalog document link](https://www.gjcity.org/DocumentCenter/View/18335) | Official E009 places it under the last-30-days adopted heading. E011 returned **301, not PDF bytes**. Exact redirect destination is retained but unopened at the target limit. |

`REPORT.json` contains eight separate authority/category checklist cells, exact anchor labels, source IDs, event references, and gaps. `LEGACY_COMPARISON.json` gives exact historical requested-URL, parent-URL and digest counts per priority.

## Material distinctions

**Mesa proposals are separate from its displayed code edition.** The current-code URL now redirects to a page titled “Current Land Development Code 2020, Amended 04-23-24 and Updates.” It places the retained 2024-amended PDF under “Current,” then separately lists July 24, 2026 proposed-draft and additions/deletions files. A September 3, 2026 heading revises hearing dates. Those revision and hearing dates are not adoption or effective dates. No future hearing occurrence or final action was checked.

**Shared building administration does not merge legal authorities.** Mesa's retained Community Development page says its Building Department serves the county, De Beque, Collbran, Palisade and the City of Grand Junction. The land-use catalog specifically addresses unincorporated county areas. Grand Junction's fire page also discusses its Rural Fire Protection District. City ordinances and district instruments must remain separately attributed; the county building service description does not establish county ownership of city laws.

**Ordinance 5269 supports a specific adoption record, not current-law certification.** Page 1 adopts the 2024 IFC with specified appendices and local amendments to Chapter 15.44. Page 28 states introduction June 18, 2025 and passage on second reading July 16, 2025. Page 29 states publications June 21 and July 19, certification July 21, and effective date August 18, 2025. Signature marks and a seal are visible; signer identity/authenticity was not certified. Twenty-six internal amendment pages were not visually reviewed. The registry's separate building Ordinance 5268 was not opened.

**The fire fee schedule is a useful next table-review candidate.** Both pages were retained and viewed, but native extraction moves group headings after numeric rows. A later transcription should bind every row to its visible group and preserve tier boundaries, additional inspection charges and conditional multipliers. PDF metadata dates are not adoption dates. The same official catalog also links a different `/DocumentCenter/View/563/Fire-Prevention-Bureau-Fees-PDF` endpoint; it was not opened or reconciled. No fee number was promoted into structured rules.

**Grand Junction's ordinance page mixes stages.** Proposed measures and last-30-days adopted measures have separate headings. Ordinance 5340's tree-preservation title and adopted-stage label are supported by the retained catalog, while actual instrument text, adoption date, effectiveness and code incorporation remain unverified. The exact unopened redirect is `https://www.gjcity.org/DocumentCenter/View/18335/Ordinance-No-5340?bidId=`. A rolling 30-day page cannot establish a complete amendment history.

The city's development page expressly warns that informational items referencing the 2018 IFC are being updated. The 2024 adoption does not establish that every linked form or guide has already been revised. The county pages' Stage 1 fire-restriction banner was observed, but no sheriff order or jurisdiction chain was collected.

## Custody and next step

`events/` retains exact response bodies and source metadata. `pdf-inspection/` contains structural receipts, native page text and the eight viewed page renders. `CUSTODY.json` and its schema bind all frozen package files; `validate_package.py` performs read-only schema, hash, event-limit, referral, PDF/native and inspection-scope checks.

Six city header captures contain server `Set-Cookie` fields. They remain local custody. A future distributable package should retain original hashes and use separately hashed redacted header derivatives; originals must not be silently edited.

A useful later batch would retrieve the exact unresolved Mesa Fees/Building links and Grand Junction 5340 redirect, then reconcile the complete building and fee adoption chains. That work was **not performed or activated** here. No task, bot, scheduler, source promotion or follow-on crawl was created.
