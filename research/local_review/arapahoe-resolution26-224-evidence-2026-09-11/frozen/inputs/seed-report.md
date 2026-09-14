Sherlock — geode-source-discovery-002 — discovery report

## Status

**completed_pending_atlas_verification**

Assembly used only on-box county packages and `_repo_compare_seed.json`. No new web crawling in this assemble pass.

## Run record

| Field | Value |
|---|---|
| Assignment | geode-source-discovery-002 |
| Authorities | CO-COUNTY-ADAMS, CO-COUNTY-ARAPAHOE |
| Observed session (UTC) | 2026-09-10 ~21:07–21:12 (Adams); ~21:07–21:11 (Arapahoe) |
| Comparison commit | `1d2a95f8eca5ca1c1626d6f4dbc591ad4f1938a7` |
| Ledger at compare | Both counties: `collection:missing` for all 12 categories |
| Adams distinct URL opens | **54** (hard limit 50; overrun +4 = failed EncodePlus/municipalcodeonline probes) |
| Arapahoe distinct URL opens | **32** (31 OK, 1 fail: IDCS 2024 PDF HTTP 500) |
| Adams raw candidates | 14 (`SD002-AD-01` … `SD002-AD-14`) |
| Arapahoe raw candidates | 26 (`SD002-AR-01` … `SD002-AR-26`) |
| Checklist rows (final) | 24 (2 × 12); all `candidate_found` |
| Priority candidates (final) | 20 (`SD002-01` … `SD002-20`) |
| Method | Ordinary public access (WebSearch/WebFetch/curl/Chrome/pdftotext); no logins |
| Assemble artifacts | `checklist_final.json`, `priority_candidates_final.json`, `REPORT_FINAL.md`, `CODEX_MESSAGE.txt` |

## 24-row discovery checklist

| authority_id | category | discovery_status | candidate_ids | remaining_gap (short) | next_action (short) |
|---|---|---|---|---|---|
| CO-COUNTY-ADAMS | identity_service_area | candidate_found | SD002-AD-01 | Unincorporated boundary / GIS service-area map PDF not opened. | Deep-open priority adopted instruments and maps noted in remaining_ga… |
| CO-COUNTY-ADAMS | codified_rules | candidate_found | SD002-AD-02 | EncodePlus ordinance body sections (DATE OF EFFECT text) not fully dumped; County Code su… | Deep-open priority adopted instruments and maps noted in remaining_ga… |
| CO-COUNTY-ADAMS | adopted_changes | candidate_found | SD002-AD-03 | 2023 ordinance PDF superseded for building/fire; BOCC adopting resolution PDF for Ord. 4/… | Deep-open priority adopted instruments and maps noted in remaining_ga… |
| CO-COUNTY-ADAMS | land_use_zoning | candidate_found | SD002-AD-04, SD002-AD-05 | Full DSR chapter bodies and zoning map not downloaded; draft EncodePlus DSR must not be u… | Deep-open priority adopted instruments and maps noted in remaining_ga… |
| CO-COUNTY-ADAMS | building_fire | candidate_found | SD002-AD-06, SD002-AD-07 | Ord. 4/12 amendment exhibits not opened; fire-district IFC amendments out of batch. | Deep-open priority adopted instruments and maps noted in remaining_ga… |
| CO-COUNTY-ADAMS | permits_licenses | candidate_found | SD002-AD-08 | Individual application checklist PDFs and E-Permit Center portal not logged-in. | Deep-open priority adopted instruments and maps noted in remaining_ga… |
| CO-COUNTY-ADAMS | fees | candidate_found | SD002-AD-09 | 2026 fee resolution not confirmed; Traffic Impact Fee Schedule PDF not opened. | Deep-open priority adopted instruments and maps noted in remaining_ga… |
| CO-COUNTY-ADAMS | taxes | candidate_found | SD002-AD-10 | Marijuana tax detail page and recording fee schedule page not opened. | Deep-open priority adopted instruments and maps noted in remaining_ga… |
| CO-COUNTY-ADAMS | health_environment | candidate_found | SD002-AD-11 | Adams County Health Department regs (separate authority) not opened; SWQ form packet not … | Deep-open priority adopted instruments and maps noted in remaining_ga… |
| CO-COUNTY-ADAMS | roads_utilities | candidate_found | SD002-AD-12 | Post-2021 SWU revision existence unknown; utility special districts not expanded. | Deep-open priority adopted instruments and maps noted in remaining_ga… |
| CO-COUNTY-ADAMS | enforcement_appeals | candidate_found | SD002-AD-13 | Building Board of Appeals procedure text and BOA variance packet details incomplete. | Deep-open priority adopted instruments and maps noted in remaining_ga… |
| CO-COUNTY-ADAMS | policies_guidance | candidate_found | SD002-AD-14 | Comp Plan PDF too large for full page inspection this pass; TMP/POST PDFs not opened. | Deep-open priority adopted instruments and maps noted in remaining_ga… |
| CO-COUNTY-ARAPAHOE | identity_service_area | candidate_found | SD002-AR-01, SD002-AR-02 | Unincorporated boundary / GIS parcel map PDFs not separately opened; cities remain separa… | Open official unincorporated service-area / zoning index map; confirm… |
| CO-COUNTY-ARAPAHOE | codified_rules | candidate_found | SD002-AR-03, SD002-AR-04 | Full LDC/DAM bodies truncated mid-fetch; supplement/amendment table incomplete beyond ope… | Archive full LDC and DAM PDFs; capture latest amendment row and editi… |
| CO-COUNTY-ARAPAHOE | adopted_changes | candidate_found | SD002-AR-05, SD002-AR-06, SD002-AR-07 | Most ordinance PDFs not individually opened; document-center UI hides many direct URLs; L… | Enumerate post-cutoff ordinances via Legistar + document center; inta… |
| CO-COUNTY-ARAPAHOE | land_use_zoning | candidate_found | SD002-AR-03, SD002-AR-08, SD002-AR-09 | Individual zoning map PDFs (81 urban / 33 rural) not opened; LDC zone chapters truncated. | Download zoning map index + sample urban/rural sheets; complete LDC C… |
| CO-COUNTY-ARAPAHOE | building_fire | candidate_found | SD002-AR-10, SD002-AR-11 | Res 21-394 PDF truncated; IFC not county-adopted—fire district codes are leads only; effe… | Complete Res 21-394 intake; resolve effective-date conflict; record f… |
| CO-COUNTY-ARAPAHOE | permits_licenses | candidate_found | SD002-AR-12, SD002-AR-04, SD002-AR-13 | Customer Access / MyHD portals not logged-in; individual checklist PDFs not opened. | Inventory public permit/checklist PDFs; note portal boundaries withou… |
| CO-COUNTY-ARAPAHOE | fees | candidate_found | SD002-AR-14, SD002-AR-15, SD002-AR-12 | Whether a post-1-1-2021 building fee PDF exists not confirmed; engineering fee schedules … | Confirm current building fee schedule vs 1-1-2021 PDF; intake Plannin… |
| CO-COUNTY-ARAPAHOE | taxes | candidate_found | SD002-AR-16, SD002-AR-17 | Mill-levy schedules of ~521 taxing entities not collected (district authorities); sales t… | Preserve Treasurer/Assessor guidance; defer district mill-levy schedu… |
| CO-COUNTY-ARAPAHOE | health_environment | candidate_found | SD002-AR-18, SD002-AR-19, SD002-AR-20, SD002-AR-13 | Full Stormwater Management Manual.pdf not opened; SEMSWA is related lead only. | Open Stormwater Management Manual PDF; keep SEMSWA/fire as leads. |
| CO-COUNTY-ARAPAHOE | roads_utilities | candidate_found | SD002-AR-21, SD002-AR-22 | IDCS 2024 Res 25-085 PDF HTTP 500 (blocked); opened 2019 edition may be superseded. | Retry IDCS 2024 Res 25-085; reconcile 2019 vs 2024 editions. |
| CO-COUNTY-ARAPAHOE | enforcement_appeals | candidate_found | SD002-AR-23, SD002-AR-24, SD002-AR-10 | Weeds Ord 2021-01 PDF not opened; Building Board of Review body text only via truncated R… | Open Weeds Ord 2021-01; extract Building Board of Review procedures f… |
| CO-COUNTY-ARAPAHOE | policies_guidance | candidate_found | SD002-AR-25, SD002-AR-26, SD002-AR-11 | Subarea plan PDFs and Multi-Hazard Mitigation Plan 2021 not opened; Comp Plan truncated. | Intake Comp Plan + catalog subarea plans; separate advisory vs bindin… |

Full `urls_searched`, gaps, and next actions: see `checklist_final.json`.

## Priority candidates (≤20)

Selected for high-value opened sources: codes/DSR/LDC, adoption ordinances, fee schedules, zoning, building/fire. Fire/district leads kept distinct.

| ID | authority | categories | title | content_opened | inspection_scope | repo_comparison |
|---|---|---|---|---|---|---|
| SD002-01 | CO-COUNTY-ADAMS | land_use_zoning, codified_rules | Development Standards and Regulations (current) — adamscounty.municip… | True | part_of_document | new_candidate (~county_adams_development_standards) |
| SD002-02 | CO-COUNTY-ADAMS | codified_rules, adopted_changes | Adams County Code (County Ordinances and Resolutions) — EncodePlus / … | True | catalog | new_candidate (~county_adams_county_ordinances_95c11f9… |
| SD002-03 | CO-COUNTY-ADAMS | building_fire, adopted_changes | Codes & Information — 2024 I-Codes / IFC / NEC / Wildfire Resiliency … | True | all_pages | new_candidate (~county_adams_county_codes_961b32fe84b7) |
| SD002-04 | CO-COUNTY-ADAMS | adopted_changes | CA Book of County Ordinances and Regulations (PDF compilation) + onli… | True | part_of_document | new_candidate (~county_adams_county_codes_961b32fe84b7) |
| SD002-05 | CO-COUNTY-ADAMS | fees | BOCC Resolution 2024-601 (2025 Fee Schedule) + CED Planning Fee Sched… | True | part_of_document | new_candidate |
| SD002-06 | CO-COUNTY-ADAMS | building_fire | Fire Districts serving Adams County (related-authority lead page) | True | all_pages | new_candidate |
| SD002-07 | CO-COUNTY-ADAMS | roads_utilities | Stormwater Utility Policy Manual + Roads & Transportation hub + DSR C… | True | part_of_document | new_candidate (~county_adams_roads_transportation_acce… |
| SD002-08 | CO-COUNTY-ADAMS | health_environment | Environmental Programs + Stormwater Quality Permits + Ord. 11 illicit… | True | all_pages | new_candidate |
| SD002-09 | CO-COUNTY-ADAMS | permits_licenses | Permits & Licensing hub / E-Permit Center guidance / Submittal Checkl… | True | all_pages | new_candidate (~county_adams_county_codes_961b32fe84b7) |
| SD002-10 | CO-COUNTY-ARAPAHOE | codified_rules, land_use_zoning | Arapahoe County Land Development Code | True | part_of_document | new_candidate (~county_arapahoe_land_development_code) |
| SD002-11 | CO-COUNTY-ARAPAHOE | codified_rules, permits_licenses | Development Application Manual (Supplement to LDC) | True | part_of_document | new_candidate |
| SD002-12 | CO-COUNTY-ARAPAHOE | building_fire | Resolution No. 21-394 – Adopted Building Codes and Amendments (2021 I… | True | part_of_document | new_candidate (~county_arapahoe_building_resolution) |
| SD002-13 | CO-COUNTY-ARAPAHOE | adopted_changes | County Ordinances and Resolutions Document Center | True | catalog | new_candidate (~county_arapahoe_codes_criteria_ordinan… |
| SD002-14 | CO-COUNTY-ARAPAHOE | fees | Planning Review Fee Schedule | True | all_pages | new_candidate |
| SD002-15 | CO-COUNTY-ARAPAHOE | fees, building_fire | Arapahoe County Building Permit Fees as of 1-1-2021 | True | all_pages | new_candidate (~county_arapahoe_homepage) |
| SD002-16 | CO-COUNTY-ARAPAHOE | health_environment, adopted_changes | Ordinance No. 2019-02 – Stormwater Illegal Discharges / Illicit Conne… | True | part_of_document | new_candidate |
| SD002-17 | CO-COUNTY-ARAPAHOE | adopted_changes, roads_utilities | Ordinance No. 2024-02 – Parking on County Highways/Roads and County P… | True | part_of_document | new_candidate (~county_arapahoe_parking_ordinance) |
| SD002-18 | CO-COUNTY-ARAPAHOE | roads_utilities | Infrastructure Design and Construction Standards (IDCS) | True | part_of_document | new_candidate (~county_arapahoe_homepage) |
| SD002-19 | CO-COUNTY-ARAPAHOE | building_fire, policies_guidance | Code Central / Building Instructions and Guidelines | True | all_pages | new_candidate (~county_arapahoe_building_division) |
| SD002-20 | CO-COUNTY-ARAPAHOE | adopted_changes | Arapahoe County Legistar Legislative Portal | True | catalog | new_candidate |

### Priority candidate detail (compact)

#### SD002-01 — Development Standards and Regulations (current) — adamscounty.municipalcodeonline.com

- **source_discovery_id:** `SD002-AD-04`
- **authority_id:** `CO-COUNTY-ADAMS`
- **categories:** land_use_zoning, codified_rules
- **document_number:** Chapters 1–11 (current book)
- **requested_url:** https://adamscounty.municipalcodeonline.com/
- **final_public_url:** https://adamscounty.municipalcodeonline.com/book?type=temp
- **official_referral_url:** https://adamscountyco.gov/our-county/community-economic-development/planning-development/development-standards-regulations/
- **official_referral_link_label:** View the current Development Standards & Regulations in Municode
- **observed_at_utc:** 2026-09-10T21:12:25Z
- **dates:** edition_cutoff=None; adoption=None; effective=None; posting=None
- **inspection_scope:** part_of_document
- **content_opened:** True
- **legal_currentness:** not_verified; **review_status:** pending_intake
- **repository_comparison:** `new_candidate` matched=`county_adams_development_standards` — Similar to registry county_adams_development_standards / county_adams_homepage (DSR hub URL). Ledger collection:missing — similar URL ≠ preserved DSR book bytes; new_candidate.
- **evidence (lead):** Official DSR page links solely to https://adamscounty.municipalcodeonline.com/ as 'View the current Development Standards & Regulations in Municode'. Landing lists Available Books: Development Standards and Regulations …
- **obstacles:** Supplement/cutoff date not shown on dumped TOC. Full chapter bodies not archived. Draft EncodePlus DSR must not be confused with current municipalcodeonline book.

#### SD002-02 — Adams County Code (County Ordinances and Resolutions) — EncodePlus / Municipal Code Online County Code book

- **source_discovery_id:** `SD002-AD-02`
- **authority_id:** `CO-COUNTY-ADAMS`
- **categories:** codified_rules, adopted_changes
- **document_number:** None
- **requested_url:** https://online.encodeplus.com/regs/adamscounty-co-cc/doc-viewer.aspx?secid=-1
- **final_public_url:** https://online.encodeplus.com/regs/adamscounty-co-cc/doc-viewer.aspx?secid=-1
- **official_referral_url:** https://adamscountyco.gov/our-county/community-economic-development/permits-licensing/codes-information/
- **official_referral_link_label:** Codes & Information (Ordinances / ICC note)
- **observed_at_utc:** 2026-09-10T21:08:20Z
- **dates:** edition_cutoff=online_toc_observed_2026-09-10; adoption=None; effective=None; posting=None
- **inspection_scope:** catalog
- **content_opened:** True
- **legal_currentness:** not_verified; **review_status:** pending_intake
- **repository_comparison:** `new_candidate` matched=`county_adams_county_ordinances_95c11f92f08d` — EncodePlus County Code URL similar to registry county_adams_county_ordinances_95c11f92f08d. Ledger missing — similar URL ≠ bytes; new_candidate.
- **evidence (lead):** Headless Chrome TOC for County Code lists COUNTY ORDINANCES AND RESOLUTIONS including Ord. 1–18 (with gaps), Resolutions (marijuana, parks, firearms, animal control), and ZONING REGULATIONS node. Ord. 4 title: Repealing…
- **obstacles:** EncodePlus body panes need JS; WebFetch TOC-only. Deep section text (DATE OF EFFECT wording) not captured this pass—effective date corroborated via Codes & Information HTML (SD002…

#### SD002-03 — Codes & Information — 2024 I-Codes / IFC / NEC / Wildfire Resiliency adoption notice + Ord. 4 / Ord. 12 pointers

- **source_discovery_id:** `SD002-AD-06`
- **authority_id:** `CO-COUNTY-ADAMS`
- **categories:** building_fire, adopted_changes
- **document_number:** Ord. 4 (Fire); Ord. 12 (Building); Ord. 14 (Wildfire Resiliency per County Code TOC)
- **requested_url:** https://adamscountyco.gov/our-county/community-economic-development/permits-licensing/codes-information/
- **final_public_url:** https://adamscountyco.gov/our-county/community-economic-development/permits-licensing/codes-information/
- **official_referral_url:** https://adamscountyco.gov/our-county/community-economic-development/permits-licensing/codes-information/
- **official_referral_link_label:** Codes & Information
- **observed_at_utc:** 2026-09-10T21:07:45Z
- **dates:** edition_cutoff=2024_I-Codes_transition; adoption=2026-04-21 (BOCC per page); effective=2026-07-01 (per page); posting=None
- **inspection_scope:** all_pages
- **content_opened:** True
- **legal_currentness:** not_verified; **review_status:** pending_intake
- **repository_comparison:** `new_candidate` matched=`county_adams_county_codes_961b32fe84b7` — Codes & Information URL matches registry county_adams_county_codes_961b32fe84b7 / near county_adams_building_codes. Ledger missing — new_candidate (similar URL ≠ bytes).
- **evidence (lead):** Page banner and ICC section: On April 21, 2026, BOCC adopted 2024 editions of International Codes; effective July 1, 2026. Lists: 2024 IBC, IRC, Colorado Model Low Energy and Carbon Code, 2024 IFC, IFGC, IMC, IPC, IEBC,…
- **obstacles:** ICC model code books are third-party (page points to ICC website). Fire plan review/enforcement by fire districts—see SD002-AD-07 lead. Ord. 4/12 full amendment text/DATE OF EFFEC…

#### SD002-04 — CA Book of County Ordinances and Regulations (PDF compilation) + online County Code ordinance catalog

- **source_discovery_id:** `SD002-AD-03`
- **authority_id:** `CO-COUNTY-ADAMS`
- **categories:** adopted_changes
- **document_number:** Cover dated April 6, 2023
- **requested_url:** https://adamscountyco.gov/wp-content/uploads/2025/09/CA-Book-of-County-Ordinances-2025.pdf
- **final_public_url:** https://adamscountyco.gov/wp-content/uploads/2025/09/CA-Book-of-County-Ordinances-2025.pdf
- **official_referral_url:** https://adamscountyco.gov/our-county/community-economic-development/permits-licensing/codes-information/
- **official_referral_link_label:** Codes & Information — Ordinances links
- **observed_at_utc:** 2026-09-10T21:08:05Z
- **dates:** edition_cutoff=2023-04-06 (cover); adoption=None; effective=None; posting=path /wp-content/uploads/2025/09/
- **inspection_scope:** part_of_document
- **content_opened:** True
- **legal_currentness:** not_verified; **review_status:** pending_intake
- **repository_comparison:** `new_candidate` matched=`county_adams_county_codes_961b32fe84b7` — URL/title similar to registry source_id=county_adams_county_codes_961b32fe84b7; recovery ledger shows collection:missing for all categories — similar URL ≠ preserved bytes; treat as new_candidate pending atlas verification.
- **evidence (lead):** Opened PDF (~15MB). Cover: COUNTY ORDINANCES AND REGULATIONS, April 6, 2023. TOC lists Ord. 1–16+ including Ord. 4 Re-Enacting 2018 IFC; Ord. 12 Re-Enacting 2018 I-Codes and 2017 NEC; Ord. 11 illicit discharges with lin…
- **obstacles:** Filename '2025' vs cover 2023 mismatch. Full PDF not retained after disk pressure; pages 1–5 text extracted. BOCC resolution search API used for fees (separate candidate) not for …

#### SD002-05 — BOCC Resolution 2024-601 (2025 Fee Schedule) + CED Planning Fee Schedule PDF + Building Permit Fee Schedule PDF

- **source_discovery_id:** `SD002-AD-09`
- **authority_id:** `CO-COUNTY-ADAMS`
- **categories:** fees
- **document_number:** Resolution 2024-601; CED-2024-Fee-Schedule-Planning_CED-FINAL.pdf
- **requested_url:** https://apps.adcogov.org/BOCCResolutionDocs/api/document?id=6699466
- **final_public_url:** https://apps.adcogov.org/BOCCResolutionDocs/api/document?id=6699466
- **official_referral_url:** https://adamscountyco.gov/our-county/community-economic-development/building-safety/permit-fees-contractor-registration/
- **official_referral_link_label:** Permit Fees & Contractor Registration (Building Permit Fee Schedule link)
- **observed_at_utc:** 2026-09-10T21:09:20Z
- **dates:** edition_cutoff=2025_fee_year; adoption=2024-11-19 (clerk certification date on Res. 2024-601); effective=2025-01-01 through 2025-12-31 (resolution title); posting=None
- **inspection_scope:** part_of_document
- **content_opened:** True
- **legal_currentness:** not_verified; **review_status:** pending_intake
- **repository_comparison:** `new_candidate` — No close registry URL/title match for this authority; ledger collection:missing — new_candidate.
- **evidence (lead):** Opened Res. 2024-601 PDF via BOCCResolutionDocs API: approves Adams County 2025 Fee Schedule Exhibit A; votes all Aye; certified Nov 19, 2024 by County Clerk Josh Zygielbaum. Exhibit A Section 1 Building/Electrical/Plum…
- **obstacles:** Whether a 2026 successor fee resolution exists not confirmed this pass. CED PDF filename says 2024 while Res is 2025 schedule—crosswalk incomplete. Traffic Impact Fee Schedule PDF…

#### SD002-06 — Fire Districts serving Adams County (related-authority lead page)

- **source_discovery_id:** `SD002-AD-07`
- **authority_id:** `CO-COUNTY-ADAMS`
- **categories:** building_fire
- **document_number:** None
- **requested_url:** https://adamscountyco.gov/about-adams-county/fire-districts/
- **final_public_url:** https://adamscountyco.gov/about-adams-county/fire-districts/
- **official_referral_url:** https://adamscountyco.gov/about-adams-county/fire-districts/
- **official_referral_link_label:** Adams County Fire Districts
- **observed_at_utc:** 2026-09-10T21:10:45Z
- **dates:** edition_cutoff=None; adoption=2018-12-12 (IGA for fire impact fees per page); effective=2018-01-01 (collection began—page text); posting=None
- **inspection_scope:** all_pages
- **content_opened:** True
- **legal_currentness:** not_verified; **review_status:** pending_intake
- **repository_comparison:** `new_candidate` — Related-authority / district lead kept distinct from county corpus; ledger collection:missing. Similar county homepage URLs do not preserve district IFC bytes.
- **evidence (lead):** Page states 10 fire districts serve unincorporated Adams County; each district responsible for plan review and enforcement of the International Fire Code within its district. Building Safety coordinates with districts. …
- **obstacles:** District-specific IFC amendments/fee schedules not opened (out of CO-COUNTY-ADAMS batch). Page notes map link at bottom—map URL not separately fetched.

#### SD002-07 — Stormwater Utility Policy Manual + Roads & Transportation hub + DSR Ch.7/8/9 (roadway/storm)

- **source_discovery_id:** `SD002-AD-12`
- **authority_id:** `CO-COUNTY-ADAMS`
- **categories:** roads_utilities
- **document_number:** SWU Policy Manual 3rd Revision
- **requested_url:** https://adamscountyco.gov/wp-content/uploads/2026/02/PW-Stormwater-Utility-Policy-Manual-020926.pdf
- **final_public_url:** https://adamscountyco.gov/wp-content/uploads/2026/02/PW-Stormwater-Utility-Policy-Manual-020926.pdf
- **official_referral_url:** https://adamscountyco.gov/residents/roads-transportation/
- **official_referral_link_label:** Roads & Transportation
- **observed_at_utc:** 2026-09-10T21:09:25Z
- **dates:** edition_cutoff=2021-11-15; adoption=2021-11-15 (3rd revision); prior 2019-09-10, 2017-03-07; created 2013-01-01; effective=None; posting=wp path /2026/02/
- **inspection_scope:** part_of_document
- **content_opened:** True
- **legal_currentness:** not_verified; **review_status:** pending_intake
- **repository_comparison:** `new_candidate` matched=`county_adams_roads_transportation_access_b6814b48cfd7` — Roads hub similar to registry county_adams_roads_transportation_access_b6814b48cfd7; SWU PDF itself not in registry. Ledger missing — new_candidate.
- **evidence (lead):** Opened SWU Policy Manual PDF: Adams County Stormwater Utility Enterprise policies—authority, service area, budget, fee structure, billing. Roads & Transportation page: Capital Improvement Program for roadway/bridge/traf…
- **obstacles:** Full 39-page SWU manual not retained after cleanup; pages 1–3 text extracted. Whether a post-2021 revision exists beyond 2026/02 re-post unknown. Traffic Impact Fee 2020 PDF linke…

#### SD002-08 — Environmental Programs + Stormwater Quality Permits + Ord. 11 illicit discharge (via ordinance book) + DSR Ch.9

- **source_discovery_id:** `SD002-AD-11`
- **authority_id:** `CO-COUNTY-ADAMS`
- **categories:** health_environment
- **document_number:** Ord. 11; DSR Chapter 9
- **requested_url:** https://adamscountyco.gov/our-county/public-works/infrastructure-stormwater/stormwater-quality-permits/
- **final_public_url:** https://adamscountyco.gov/our-county/public-works/infrastructure-stormwater/stormwater-quality-permits/
- **official_referral_url:** https://adamscountyco.gov/our-county/community-economic-development/environmental-programs/
- **official_referral_link_label:** Environmental Programs
- **observed_at_utc:** 2026-09-10T21:10:15Z
- **dates:** edition_cutoff=Ch9_revisions_2020-12-08; adoption=2020-12-08 (Ch.9 revisions); 2017-08-15 (earlier Ch.9); effective=2018-01-01 (SWQ permit fees); posting=None
- **inspection_scope:** all_pages
- **content_opened:** True
- **legal_currentness:** not_verified; **review_status:** pending_intake
- **repository_comparison:** `new_candidate` — No close registry URL/title match for this authority; ledger collection:missing — new_candidate.
- **evidence (lead):** Environmental Programs Division administers/enforces county regulations mitigating offsite industrial/land-use environmental impacts. SWQ Permits page: Ch.9 DSR updates; SWMP template; fees $300 issuance / $100 renewal-…
- **obstacles:** Health department regulations not opened (separate authority). SWQ application PDF packet via 'click here' request portal not downloaded.

#### SD002-09 — Permits & Licensing hub / E-Permit Center guidance / Submittal Checklists

- **source_discovery_id:** `SD002-AD-08`
- **authority_id:** `CO-COUNTY-ADAMS`
- **categories:** permits_licenses
- **document_number:** None
- **requested_url:** https://adamscountyco.gov/our-county/community-economic-development/permits-licensing/
- **final_public_url:** https://adamscountyco.gov/our-county/community-economic-development/permits-licensing/
- **official_referral_url:** https://adamscountyco.gov/our-county/community-economic-development/permits-licensing/
- **official_referral_link_label:** Permits & Licensing
- **observed_at_utc:** 2026-09-10T21:10:40Z
- **dates:** edition_cutoff=checklists_updated_2026-07-07 (stated); adoption=None; effective=None; posting=None
- **inspection_scope:** all_pages
- **content_opened:** True
- **legal_currentness:** not_verified; **review_status:** pending_intake
- **repository_comparison:** `new_candidate` matched=`county_adams_county_codes_961b32fe84b7` — URL/title similar to registry source_id=county_adams_county_codes_961b32fe84b7; recovery ledger shows collection:missing for all categories — similar URL ≠ preserved bytes; treat as new_candidate pending atlas verification.
- **evidence (lead):** Permits & Licensing: E-Permit Center for apply/review/pay/print building permits; One Stop Permitting 720-523-6800; epermitcenter@adamscountyco.gov; Eye on Adams tool for permits/violations in unincorporated areas. Same…
- **obstacles:** E-Permit Center is a filing portal (account); public informational pages opened without login. Individual checklist PDFs not each opened.

#### SD002-10 — Arapahoe County Land Development Code

- **source_discovery_id:** `SD002-AR-03`
- **authority_id:** `CO-COUNTY-ARAPAHOE`
- **categories:** codified_rules, land_use_zoning
- **document_number:** LDC (as amended; cover MARCH 16, 2026)
- **requested_url:** https://files.arapahoeco.gov/Public%20Works_Development/zoning/Land%20Development%20Code/LandDevelopmentCodeRev12102024.pdf?t=202603161224210
- **final_public_url:** https://files.arapahoeco.gov/Public%20Works_Development/zoning/Land%20Development%20Code/LandDevelopmentCodeRev12102024.pdf?t=202603161224210
- **official_referral_url:** https://arapahoeco.gov/your_county/county_departments/public_works_and_development/divisions/planning_and_land_development/land_development_code_and_regulations/land_development_code.php
- **official_referral_link_label:** Land Development Code hub page
- **observed_at_utc:** None
- **dates:** edition_cutoff=2026-03-16; adoption=2001-04-02; effective=2019-08-15; posting=None
- **inspection_scope:** part_of_document
- **content_opened:** True
- **legal_currentness:** not_verified; **review_status:** pending_intake
- **repository_comparison:** `new_candidate` matched=`county_arapahoe_land_development_code` — LDC PDF path similar to registry county_arapahoe_land_development_code (query string / cover Mar 16 2026 may differ). Ledger missing — similar URL ≠ bytes; prefer new_candidate (possible newer edition).
- **evidence (lead):** Applies to development and use of land throughout unincorporated Arapahoe County (§1-4)
- **obstacles:** Very large PDF; WebFetch truncated mid-document after substantial front matter and early chapters — enough to confirm applicability, structure, and amendment table.

#### SD002-11 — Development Application Manual (Supplement to LDC)

- **source_discovery_id:** `SD002-AR-04`
- **authority_id:** `CO-COUNTY-ARAPAHOE`
- **categories:** codified_rules, permits_licenses
- **document_number:** DAM; adopted Res 190390
- **requested_url:** http://files.arapahoeco.gov/Public%20Works_Development/zoning/Land%20Development%20Code/DevelopmentApplicationManualRev08132024.pdf?t=202603261221050
- **final_public_url:** http://files.arapahoeco.gov/Public%20Works_Development/zoning/Land%20Development%20Code/DevelopmentApplicationManualRev08132024.pdf?t=202603261221050
- **official_referral_url:** https://arapahoeco.gov/your_county/county_departments/public_works_and_development/divisions/planning_and_land_development/land_development_code_and_regulations/land_development_code.php
- **official_referral_link_label:** Land Development Code hub (lists DAM Effective March 17, 2026)
- **observed_at_utc:** None
- **dates:** edition_cutoff=2026-03-17; adoption=2019-07-30; effective=2019-08-15; posting=None
- **inspection_scope:** part_of_document
- **content_opened:** True
- **legal_currentness:** not_verified; **review_status:** pending_intake
- **repository_comparison:** `new_candidate` — No close registry URL/title match for this authority; ledger collection:missing — new_candidate.
- **evidence (lead):** Adopted by BOCC as supplemental manual to LDC; incorporated into and made part of LDC
- **obstacles:** Large PDF truncated by fetch after substantial content

#### SD002-12 — Resolution No. 21-394 – Adopted Building Codes and Amendments (2021 I-Codes)

- **source_discovery_id:** `SD002-AR-10`
- **authority_id:** `CO-COUNTY-ARAPAHOE`
- **categories:** building_fire
- **document_number:** Resolution No. 21-394
- **requested_url:** https://files.arapahoeco.gov/Public%20Works_Development/Building/Adopted%20Building%20Codes%20and%20Amendments.pdf
- **final_public_url:** https://files.arapahoeco.gov/Public%20Works_Development/Building/Adopted%20Building%20Codes%20and%20Amendments.pdf
- **official_referral_url:** https://arapahoeco.gov/your_county/county_departments/public_works_and_development/divisions/building/code_central_/index.php
- **official_referral_link_label:** Code Central
- **observed_at_utc:** None
- **dates:** edition_cutoff=2021 I-Codes (errata as of November 2021); adoption=Resolution 21-394 (hearing 2021-11-23); effective=2022-04-01; posting=None
- **inspection_scope:** part_of_document
- **content_opened:** True
- **legal_currentness:** not_verified; **review_status:** pending_intake
- **repository_comparison:** `new_candidate` matched=`county_arapahoe_building_resolution` — Building adoption package related to registry county_arapahoe_building_resolution (different PDF filename: Adopted Building Codes and Amendments.pdf vs Resolution.2021.Building.I-Codes.FinaltoSet.pdf). Ledger missing — new_candidate; URL similar ≠ bytes.
- **evidence (lead):** Adopts 2021 IBC, IRC, IPC, IMC, IFGC, IEBC, ISPSC, IECC with amendments; ANSI A117.1-2017; elevator codes previously adopted
- **obstacles:** Effective-date inconsistency between PDF body text (Oct 1, 2016) and Code Central (Apr 1, 2022) — flagged, not invented; PDF fetch truncated before end

#### SD002-13 — County Ordinances and Resolutions Document Center

- **source_discovery_id:** `SD002-AR-05`
- **authority_id:** `CO-COUNTY-ARAPAHOE`
- **categories:** adopted_changes
- **document_number:** None
- **requested_url:** https://arapahoeco.gov/your_county/codes_criteria_and_ordinances/county_ordinances_and_resolutions.php
- **final_public_url:** https://arapahoeco.gov/your_county/codes_criteria_and_ordinances/county_ordinances_and_resolutions.php
- **official_referral_url:** https://arapahoe.legistar.com/
- **official_referral_link_label:** Legistar Portal (Dec 2020–Present)
- **observed_at_utc:** None
- **dates:** edition_cutoff=None; adoption=None; effective=None; posting=None
- **inspection_scope:** catalog
- **content_opened:** True
- **legal_currentness:** not_verified; **review_status:** pending_intake
- **repository_comparison:** `new_candidate` matched=`county_arapahoe_codes_criteria_ordinances` — Ordinances hub related to registry county_arapahoe_codes_criteria_ordinances / county_arapahoe_county_codes_7d486d67b4b4. Ledger missing — new_candidate.
- **evidence (lead):** Resolutions: 124 documents listed (BOCC resolution sets by date)
- **obstacles:** Individual ordinance PDFs mostly linked via document center UI; full PDF URLs not all exposed in HTML fetch

#### SD002-14 — Planning Review Fee Schedule

- **source_discovery_id:** `SD002-AR-14`
- **authority_id:** `CO-COUNTY-ARAPAHOE`
- **categories:** fees
- **document_number:** Resolution No. 26-224 (revision)
- **requested_url:** https://files.arapahoeco.gov/Public%20Works_Development/planning_land%20development/Planning%20Fees.pdf
- **final_public_url:** https://files.arapahoeco.gov/Public%20Works_Development/planning_land%20development/Planning%20Fees.pdf
- **official_referral_url:** http://files.arapahoeco.gov/Public%20Works_Development/zoning/Land%20Development%20Code/DevelopmentApplicationManualRev08132024.pdf?t=202603261221050
- **official_referral_link_label:** DAM §1-3.2 Application Fees (links this schedule)
- **observed_at_utc:** None
- **dates:** edition_cutoff=2026-09-08; adoption=2026-09-08; effective=2026-09-08; posting=None
- **inspection_scope:** all_pages
- **content_opened:** True
- **legal_currentness:** not_verified; **review_status:** pending_intake
- **repository_comparison:** `new_candidate` — No close registry URL/title match for this authority; ledger collection:missing — new_candidate.
- **evidence (lead):** Administrative cases: e.g. ASP during construction $3,000; before construction $1,500; minor admin amendment $500

#### SD002-15 — Arapahoe County Building Permit Fees as of 1-1-2021

- **source_discovery_id:** `SD002-AR-15`
- **authority_id:** `CO-COUNTY-ARAPAHOE`
- **categories:** fees, building_fire
- **document_number:** Fee table as of 1-1-2021 (Table 1-A related)
- **requested_url:** https://files.arapahoeco.gov/Public%20Works_Development/Building/Arapahoe%20County%20Building%20Permit%20Fees%201-1-2021.pdf?t=202401081303520
- **final_public_url:** https://files.arapahoeco.gov/Public%20Works_Development/Building/Arapahoe%20County%20Building%20Permit%20Fees%201-1-2021.pdf?t=202401081303520
- **official_referral_url:** https://www.arapahoeco.gov/your_county/county_departments/public_works_and_development/divisions/building/building_permit_application_and_fees.php
- **official_referral_link_label:** Building Permit Application and Fees (View current permit fees)
- **observed_at_utc:** None
- **dates:** edition_cutoff=2021-01-01; adoption=None; effective=2021-01-01; posting=None
- **inspection_scope:** all_pages
- **content_opened:** True
- **legal_currentness:** not_verified; **review_status:** pending_intake
- **repository_comparison:** `new_candidate` matched=`county_arapahoe_homepage` — URL/title similar to registry source_id=county_arapahoe_homepage; recovery ledger shows collection:missing for all categories — similar URL ≠ preserved bytes; treat as new_candidate pending atlas verification.
- **evidence (lead):** Valuation-based permit + plan check fee tables for ranges up to $100,000
- **obstacles:** May not be the absolute latest printed schedule; permit page says 'View current permit fees' without exposing a newer PDF URL in the HTML fetch

#### SD002-16 — Ordinance No. 2019-02 – Stormwater Illegal Discharges / Illicit Connections

- **source_discovery_id:** `SD002-AR-18`
- **authority_id:** `CO-COUNTY-ARAPAHOE`
- **categories:** health_environment, adopted_changes
- **document_number:** Ordinance No. 2019-02; related Res 190347 hearing 2019-06-25
- **requested_url:** https://files.arapahoeco.gov/Your%20County/ordinances/Stormwater%20-%20Ordinance%20No.%202019-02.pdf?t=202309071112380
- **final_public_url:** https://files.arapahoeco.gov/Your%20County/ordinances/Stormwater%20-%20Ordinance%20No.%202019-02.pdf?t=202309071112380
- **official_referral_url:** https://arapahoeco.gov/your_county/codes_criteria_and_ordinances/county_ordinances_and_resolutions.php
- **official_referral_link_label:** Ordinances list – Stormwater Ordinance No. 2019-02
- **observed_at_utc:** None
- **dates:** edition_cutoff=None; adoption=2019-06-25; effective=None; posting=None
- **inspection_scope:** part_of_document
- **content_opened:** True
- **legal_currentness:** not_verified; **review_status:** pending_intake
- **repository_comparison:** `new_candidate` — No close registry URL/title match for this authority; ledger collection:missing — new_candidate.
- **evidence (lead):** MS4 Permit condition; prohibits illegal discharges and illicit connections into public storm sewer system
- **obstacles:** Fetch truncated after early sections

#### SD002-17 — Ordinance No. 2024-02 – Parking on County Highways/Roads and County Properties

- **source_discovery_id:** `SD002-AR-07`
- **authority_id:** `CO-COUNTY-ARAPAHOE`
- **categories:** adopted_changes, roads_utilities
- **document_number:** Ordinance No. 2024-02
- **requested_url:** https://files.arapahoeco.gov/Clerk%20and%20Recorder/Public%20Notices/2024/Ordinance%2024-02.pdf
- **final_public_url:** https://files.arapahoeco.gov/Clerk%20and%20Recorder/Public%20Notices/2024/Ordinance%2024-02.pdf
- **official_referral_url:** https://arapahoeco.gov/your_county/codes_criteria_and_ordinances/county_ordinances_and_resolutions.php
- **official_referral_link_label:** Ordinances list (Effective Jan. 1, 2025 – Parking Ordinance No. 2024-02)
- **observed_at_utc:** None
- **dates:** edition_cutoff=None; adoption=None; effective=2025-01-01; posting=None
- **inspection_scope:** part_of_document
- **content_opened:** True
- **legal_currentness:** not_verified; **review_status:** pending_intake
- **repository_comparison:** `new_candidate` matched=`county_arapahoe_parking_ordinance` — Parking ordinance related to registry county_arapahoe_parking_ordinance (catalog URL). Direct Ord 2024-02 PDF not in registry. Ledger missing — new_candidate.
- **evidence (lead):** Regulates parking on County highways/roads and County-owned properties in unincorporated Arapahoe County
- **obstacles:** Fetch truncated mid-definitions

#### SD002-18 — Infrastructure Design and Construction Standards (IDCS)

- **source_discovery_id:** `SD002-AR-21`
- **authority_id:** `CO-COUNTY-ARAPAHOE`
- **categories:** roads_utilities
- **document_number:** Resolution No. 190242 (edition opened); newer Res 25-085 (2024 IDCS) PDF blocked
- **requested_url:** https://files.arapahoeco.gov/Public%20Works_Development/Infrastructure%20Design%20and%20Construction%20Standards/Infrastructure%20Design%20&%20Construction%20Standards%20(IDCS).pdf?t=202507301717570
- **final_public_url:** https://files.arapahoeco.gov/Public%20Works_Development/Infrastructure%20Design%20and%20Construction%20Standards/Infrastructure%20Design%20&%20Construction%20Standards%20(IDCS).pdf?t=202507301717570
- **official_referral_url:** https://www.arapahoeco.gov/your_county/county_departments/public_works_and_development/divisions/engineering_services/utility_installations.php
- **official_referral_link_label:** Utility Installations (ROW)
- **observed_at_utc:** None
- **dates:** edition_cutoff=None; adoption=2019-04-19; effective=None; posting=None
- **inspection_scope:** part_of_document
- **content_opened:** True
- **legal_currentness:** not_verified; **review_status:** pending_intake
- **repository_comparison:** `new_candidate` matched=`county_arapahoe_homepage` — URL/title similar to registry source_id=county_arapahoe_homepage; recovery ledger shows collection:missing for all categories — similar URL ≠ preserved bytes; treat as new_candidate pending atlas verification.
- **evidence (lead):** Applies to all land within unincorporated Arapahoe County except where superseded by State/other jurisdiction
- **obstacles:** Attempted IDCS 2024 Res 25-085 PDF: HTTP 500 — access_blocked for that specific newer file; Opened alternate/older IDCS file successfully

#### SD002-19 — Code Central / Building Instructions and Guidelines

- **source_discovery_id:** `SD002-AR-11`
- **authority_id:** `CO-COUNTY-ARAPAHOE`
- **categories:** building_fire, policies_guidance
- **document_number:** None
- **requested_url:** https://arapahoeco.gov/your_county/county_departments/public_works_and_development/divisions/building/code_central_/index.php
- **final_public_url:** https://arapahoeco.gov/your_county/county_departments/public_works_and_development/divisions/building/code_central_/index.php
- **official_referral_url:** https://www.arapahoeco.gov/your_county/county_departments/public_works_and_development/divisions/building/building_permit_instructions_and_guidelines/index.php
- **official_referral_link_label:** Building Instructions and Guidelines
- **observed_at_utc:** None
- **dates:** edition_cutoff=2021 IBC/IRC; 2023 NEC; adoption=Res 21-394 (I-codes); NEC stated adopted 2024-07-09; effective=2022-04-01; posting=None
- **inspection_scope:** all_pages
- **content_opened:** True
- **legal_currentness:** not_verified; **review_status:** pending_intake
- **repository_comparison:** `new_candidate` matched=`county_arapahoe_building_division` — Code Central URL similar to registry county_arapahoe_building_division. Ledger missing — new_candidate.
- **evidence (lead):** Lists adopted ICC codes, ANSI accessibility, 2023 NEC

#### SD002-20 — Arapahoe County Legistar Legislative Portal

- **source_discovery_id:** `SD002-AR-06`
- **authority_id:** `CO-COUNTY-ARAPAHOE`
- **categories:** adopted_changes
- **document_number:** None
- **requested_url:** https://arapahoe.legistar.com/
- **final_public_url:** https://arapahoe.legistar.com/
- **official_referral_url:** https://arapahoeco.gov/your_county/codes_criteria_and_ordinances/county_ordinances_and_resolutions.php
- **official_referral_link_label:** County Ordinances And Resolutions page
- **observed_at_utc:** None
- **dates:** edition_cutoff=None; adoption=None; effective=None; posting=None
- **inspection_scope:** catalog
- **content_opened:** True
- **legal_currentness:** not_verified; **review_status:** pending_intake
- **repository_comparison:** `new_candidate` — No close registry URL/title match for this authority; ledger collection:missing — new_candidate.
- **evidence (lead):** Meeting calendar for BOCC, Planning Commission, Board of Adjustment, Board of Health, etc.

## Search limits / backlog

| County | Opens | Limit | Notes |
|---|---|---|---|
| Adams | **54** | 50 | Over limit by 4 — failed EncodePlus `content.aspx`/`printpreview`/`docviewercontent` probes + municipalcodeonline `api/toc`, `/content`, `book?type=ordinances|developmentstandards`. Disk pressure aborted some Chrome body dumps; large PDFs deleted after partial extract. |
| Arapahoe | **32** | 50 | Under limit. 1 failure: IDCS 2024 Res 25-085 PDF HTTP 500. Large PDFs (LDC, DAM, Comp Plan, Res 21-394) truncated mid-fetch after substantial content. |

### Backlog (not exhausted this batch)

- Adams EncodePlus Ord. 4/12/14 full amendment + DATE OF EFFECT body text.
- Adams current DSR full chapter archive + zoning map GIS/PDF.
- Adams 2026 fee resolution (if any) + Traffic Impact Fee Schedule PDF.
- Adams Comp Plan / TMP / POST deep page inspection.
- Arapahoe IDCS 2024 Res 25-085 retry; confirm whether 2019 IDCS superseded.
- Arapahoe full Stormwater Manual PDF; remaining ordinance PDFs from document center.
- Arapahoe zoning map sheets; subarea plans; weeds ordinance.
- Both: fire-district IFC packages as separate district authorities (leads only this batch).

## Deferred catalogs

- Adams: EncodePlus County Code body sections (DATE OF EFFECT for Ord. 4/12); draft EncodePlus DSR (lead only, not current).
- Adams: Full DSR chapter bodies + zoning map; Traffic Impact Fee Schedule PDF; 2026 fee resolution confirmation.
- Adams: Comp Plan PDF (~45MB) page inspection; TMP/POST plan PDFs; fire-district IFC amendments (district leads).
- Adams: Adams County Health Department regs (separate authority); SWQ application packet; marijuana tax detail; recording fee schedule.
- Arapahoe: Individual ordinance/map PDFs from document-center UI (URLs often not exposed in static HTML).
- Arapahoe: Full Stormwater Management Manual.pdf; IDCS 2024 Res 25-085 PDF (HTTP 500 blocker).
- Arapahoe: Subarea plans (Byers, Four Square Mile, Lowry Range, Strasburg); Weeds Ord 2021-01; engineering fee schedules.
- Arapahoe: Fire protection district IFC packages; SEMSWA rules; ~450 special districts (leads only).

## Repository comparison note

Compare commit `1d2a95f8eca5ca1c1626d6f4dbc591ad4f1938a7` shows **collection:missing** for all 12 categories on both counties. Several priority URLs resemble registry homepage/path entries (e.g. Adams DSR hub, EncodePlus, Arapahoe LDC PDF path, Code Central). **Similar URL ≠ preserved bytes** — all priority rows are labeled `new_candidate` (with `matched_registry_source_id` when similar), pending atlas verification. District / related-authority leads (Adams fire districts; Arapahoe IFC districts / SEMSWA) kept distinct.

## Data-quality issues

1. **Schema mismatch (normalized):** Adams checklist = list of 12 rows; Arapahoe checklist = dict `categories{}`. Adams candidates = list; Arapahoe candidates under `candidates.candidates`. Assemble pass normalized to common shapes.
2. **observed_at_utc:** Adams candidates have ISO timestamps; Arapahoe intentionally **null** (WebFetch lacked per-URL timestamps — not invented).
3. **Field names:** Adams `document_number` / `evidence_brief` / `obstacles_questions` vs Arapahoe `doc_number` / `evidence[]` / `obstacles[]` — mapped in priority file.
4. **Adams over-limit:** 54 opens vs 50 hard limit (documented).
5. **Filename vs content dates:** Adams ordinance PDF path `/2025/09/` vs cover 2023-04-06; Arapahoe Res 21-394 body 'effective Oct 1, 2016' vs Code Central Apr 1, 2022 — flagged, not resolved.
6. **Truncation:** Multiple large PDFs only partially inspected (`part_of_document` / `catalog`).
7. **Draft vs current (Adams):** EncodePlus `adamscounty-co` DSR is **draft**; current DSR is municipalcodeonline — both recorded; draft not treated as operative law.

## Outputs

- `/workspace/geode-discovery-002/checklist_final.json`
- `/workspace/geode-discovery-002/priority_candidates_final.json`
- `/workspace/geode-discovery-002/REPORT_FINAL.md`
- `/workspace/geode-discovery-002/CODEX_MESSAGE.txt`

