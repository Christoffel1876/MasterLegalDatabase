---
review_id: atlas-grand-junction-ordinance5269-source-review-2026-09-11
source_id: grand-junction-ordinance5269
source_sha256: 79795d6650664c33808b3877e97b04fd31a84ab1a6bda8ab658c3153cbbe3993
reviewer: Atlas
mode: candidate_aware_direct_source_review
physical_pages: 29
full_page_images_viewed: 29
native_bytes: 68078
native_lines: 1008
annotations: 37
legal_currentness: not_verified
effective_date: null
effective_date_status: conflicting_source_statements_unresolved
semantic_rule_units_created: false
---

# Grand Junction Ordinance 5269: source review

**The source contains two incompatible explicit effective-date statements.** The ordinance body on physical page 27 says September 1, 2025. The certification on physical page 29 says August 18, 2025. This review preserves both and does not select a controlling date. This qualification is additive: the earlier discovery inspected pages 1, 28 and 29, and its frozen records remain unchanged.

| Physical page and region | Visible source reading | Exact preserved native bytes |
| --- | --- | --- |
| 27, “MISCELLANEOUS PROVISION,” immediately above “PUBLIC HEARING” | “The adopted ordinance shall be effective as of September 1, 2025.” | `page-27.native.txt[1326:1391]`: `The adopted ordinance shall be effective as of September 1 ,2025.` |
| 29, lower-left certification/publication block | “Effective: August 18, 2025” | `page-29.native.txt[798:824]`: `Effective: August 18, 2025` |

Offsets are zero-based UTF-8 bytes with the end excluded. The respective excerpt hashes are `8a516080b79816eba7b34ffb815e2b2a482a1c47307c822d13b28dd70054b041` and `7f5a22e0e076dc7cbbafc1490a7fc69dc000675d6b12d7f9afe6a4582b1dabba`. Annotation `GJO-001` binds both. [Page 27 image](page-27.png) and [page 29 image](page-29.png) allow direct review; [page 27 native bytes](page-27.native.txt) and [page 29 native bytes](page-29.native.txt) preserve extraction spacing exactly.

## What was inspected and preserved

Atlas directly viewed all 29 complete 120 dpi Poppler page images, including page 23's turnaround graphic and page 24's table. This was candidate-aware source review, with the earlier three-page discovery known. Every embedded native byte was preserved using PyMuPDF 1.28.2, `get_text('text', flags=195, sort=False)`: 68,078 UTF-8 bytes in 1,008 exhaustive line spans. Native text contains OCR-like errors and is **not a corrected transcription**.

The scope is complete page coverage for structure and selected language, not certification of every character, dimension, condition, or graphic label. The 120 literal native heading candidates are navigation aids, not a complete legal-section inventory. The 37 annotations identify source observations and boundaries, not enforceable rule units. Several annotations bind entire page text to retain surrounding conditions; narrower references identify particular anomalies and fee clauses.

`original.pdf` is an unchanged copy of discovery event E007: 6,329,749 bytes, SHA-256 shown above, ordinary TLS HTTP 200 completed at `2026-09-11T20:06:16.705965Z`. The requested and final URLs recorded in the copied access receipt are the same official endpoint:

`https://www.gjcity.org/DocumentCenter/View/15790/2024-IFC-Adoption-Ordinance-No-5269`

The receipt's `events/E007/...` paths identify the historical discovery package, not additional files inside this source-review directory. This review includes the exact response PDF and receipt, but does not replicate the discovery headers or claim to perform another retrieval. The earlier official-page referral is recorded as the basis in that receipt; its HTML is retained in the separate frozen discovery package. PDF creation/modification metadata is July 21, 2025 and names a RICOH device; that metadata is not proof of legal adoption, publication, or effectiveness.

## Instrument and adoption scope

The title and section 15.44.010 identify a **City of Grand Junction** instrument adopting the **2024 International Fire Code by reference**, with Appendices **B, C, D, E, F, G, H, I, N and O**, subject to the ordinance's modifications. Page 27 also adopts unamended IFC sections as published and states a conflict-repeal provision with its own exception. The 29 pages contain local provisions and amendments; they do not reproduce the entire referenced model-code volume. The text also refers to TEDS, other municipal provisions, NFPA standards and Council fee resolutions that were not collected or reconciled in this task.

The city definitions and delegation provisions do not establish adoption by Mesa County or by a separate rural fire district. Printed introduction and second-reading/adoption dates are June 18 and July 16, 2025. The page 29 certification is dated July 21 and lists publication on June 21 and July 19. These are distinct source-stated events; none resolves the conflicting effective dates. No later amendments, publication records, current code compilation or legal effect were verified here.

## Page map

| Physical pages | Principal source content |
| --- | --- |
| 1 | Title and recitals; 15.44.010 adoption and appendices; enforcement begins. |
| 2 | City definitions; amendments; permit fee resolution reference; retained operational-permit list begins. |
| 3-4 | Retained list and continuing compliance; tent/mobile-stage and LP-gas permits and exceptions; appeal board; definitions begin. |
| 5-6 | Fire/material/occupancy definitions and size qualifications; vegetation removal and exceptions. |
| 7-8 | Outdoor burning, prohibitions, exceptions, permits, other approvals and extinguishment authority. |
| 9-10 | Different burning distances; general/agricultural limits; seasonal, time, material and attendance conditions; prescribed burns. |
| 11-12 | Attendance; 12 no-permit categories with qualifications; cost recovery; egress devices, sky lanterns and abandoned premises. |
| 13 | Abatement notice, assessment, collection and penalties; placarding authority. |
| 14-16 | Micromobility egress; conditional emergency plans; road/turning standards, loop lanes and shared driveways; housing-site hydrants. |
| 17-18 | Conditional small-system permit exception; sprinkler/alarm changes; false-alarm conditions and fees; existing-building and tent exceptions. |
| 19-20 | Tire storage; LP-gas documents, prohibitions and exceptions; approved equipment; NFPA reference replacement. |
| 21-22 | NFPA 855-23; alternative fire flow; looped water supply and six exceptions; private access/driveways. |
| 23-25 | Turnaround figure; grade provisions; sprinkler-exception table; intermediate turnarounds and signs; access/sprinkler and valet-trash provisions. |
| 26-27 | New permit categories and hearing opportunity; flammable/LP/explosive storage; appeals and penalties; general adoption, repeal, effective clause and hearing. |
| 28-29 | Reading dates, printed roles, signature marks and seals; certification, publication dates and conflicting effective statement. |

The page-by-page map and exact native references are in `SOURCE_QA.json`.

## Conditions and fee references that should remain attached

- The operational-permit deletion has an explicit retained list across pages 2-3. The following text preserves other-code compliance and other city administrative review. It does not support a blanket “no permits required” claim.
- Tent provisions distinguish baseline thresholds, recreational/funeral exceptions, special uses and mobile stages. The construction-tent exception itself uses “operational permit”; that wording is retained.
- Burning provisions preserve different distances, fuel definitions, weather restrictions, owner permission, attendance, permits, no-permit categories and other-agency requirements. The prescribed-burn clause is discretionary and conditional. The leaf-volume wording on pages 6 and 10 is preserved without reconciling its legal relationship.
- Section 901.3.1's small sprinkler/alarm modification permit exception is conditioned on approved scope-of-work letter review and guidance compliance. It is not an unconditional exemption, and this review does not decide how it relates to separate review fees.
- Looped-water, access-road, dead-end, driveway and sprinkler exceptions contain different thresholds and approvals. “May,” “shall,” “shall not,” and exceptions remain in the unedited page text. The explosive-storage restriction expressly says it “shall not prohibit” specified safeguarded storage; it is not summarized as an absolute ban.
- Section 105.1.7, false-alarm fee clause 907.6.6.4.3 and the printed 15.44.90 appeals clause refer to Council resolutions. They do not supply or authenticate a complete dollar schedule.
- Burning cost recovery (307.7, page 12) and abandoned-premises enforcement (311.3, page 13) have different notice, cost and collection conditions. The former includes its 20-day payment, possible 20 percent collection charge and 8 percent annual interest language; the latter includes actual costs plus 10 percent administration, a 20-day assessment payment provision and a separate 10 percent collection penalty. No combined calculation or automatic liability is created.

## Source anomalies and visual limitations

| Physical page | Observation retained without correction |
| --- | --- |
| 2 | The operational list repeats 105.5.39 for mobile food preparation vehicles and organic coatings, with 105.5.36 Open Burning between. |
| 17 | The amendment instruction refers to 907.6.6.4, while the body heading prints 970.6.6.4. The body also prints “multifunction” in an alarm passage. |
| 19 | The tire-storage instruction deletes 3405.1 through 3405.7, while the replacement includes 3405.8. |
| 20 | The technical-report sentence ends at “prior to the equipment” before the next section heading, with no terminal period visible. No missing words are supplied. |
| 23 | The turnaround graphic's geometry and colored dimensions are not faithfully represented by embedded text. All graphic numbers are not certified. Red dimension labels are not treated as legislative strikeouts. |
| 23 | The grade body states an 8 percent maximum and 4 percent turnaround maximum, followed by an exception for grades steeper than 10 percent as approved. The contrast is not repaired or interpreted. |
| 24 | Table D103.4.1 is headed “FIRE SPRINKLER PROVISION EXCEPTION.” Native columns are interleaved. The “Over 750” entry spans the first two columns and requires special approval; no independent width is inferred. |
| 27 | The appeals heading prints 15.44.90 and refers to section 109. Earlier board language refers to 112.1. Neither numbering is silently normalized. |
| 28-29 | Signature marks and seals are visible; their identity and authenticity are not certified. Page 28 prints Cody Kennedy, President of the Council, and a City Clerk role. Page 29 prints Deputy City Clerk, which native text garbles. |

The scoped table reading on page 24 associates 0-300 feet with 20-foot width and no required turnaround. Both 301-500 and 501-750 feet associate 20-foot width with the same listed alternatives: 120-foot hammerhead, 60-foot “Y,” or 90-foot-diameter cul-de-sac in accordance with Figure D103.1. This association is an image-supported observation with the table's sprinkler-exception heading retained, not a general access rule.

No operative-body strikethrough was identified in the full-page review. Textual “delete” and “replace” instructions describe amendments; they do not make this a visually tracked comparison against a prior code. Absence of observed strike marks is scoped to these renders, not an authentication claim.

## Offline validation and use

`SOURCE_QA.json` is validated against strict Pydantic models and its JSON Schema. `MANIFEST.json` hashes the local package. The read-only verifier checks the exact source digest, copied HTTP receipt binding, 29 native page extractions, exhaustive line coverage, image hashes, heading references and every annotation's byte range and digest. It rejects Python optimized mode because its evidence assertions must remain enabled. Use PyMuPDF 1.28.2, Pydantic 2 and jsonschema:

```bash
python /absolute/path/to/grand-junction-ordinance5269-source-review-2026-09-11/review.py --verify
```

Verification proves those bindings, not legal correctness, the completeness of all conditional rules, a controlling effective date, or current law. This source-only package makes no repository, ledger, registry, raw-manifest or semantic-rule changes. The unresolved effective dates and uncollected referenced instruments must accompany any later navigation or intake summary.
