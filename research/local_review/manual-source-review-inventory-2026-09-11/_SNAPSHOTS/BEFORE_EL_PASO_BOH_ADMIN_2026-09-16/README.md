---
title: Manual source and recorded review inventory
legal_currentness: not_verified
answer_safe: false
---

# Manual source/review inventory

70 custody rows; 36 have an explicit review link and 34 have no allowlisted review link.
These are source-custody counts, not statewide coverage or current-law readiness.

From the repository root:

```bash
python -m geode.pipeline.manual_review_inventory --root . --check
```

| Source ID | Authority | Recorded review kind |
| --- | --- | --- |
| arapahoe-planning-fees-sd002-14 | CO-COUNTY-ARAPAHOE | checked_tables |
| larimer-land-use-code-sd004-01 | CO-COUNTY-LARIMER | metadata only |
| larimer-building-amendments-sd004-02 | CO-COUNTY-LARIMER | metadata only |
| larimer-wildfire-code-sd004-03 | CO-COUNTY-LARIMER | metadata only |
| larimer-data-center-moratorium-sd004-04 | CO-COUNTY-LARIMER | checked_passages |
| larimer-owts-regulations-sd004-05 | CO-COUNTY-LARIMER | metadata only |
| larimer-building-fees-sd004-06 | CO-COUNTY-LARIMER | checked_passages |
| larimer-development-review-fees-sd004-07 | CO-COUNTY-LARIMER | checked_tables |
| larimer-rural-road-standards-sd004-08 | CO-COUNTY-LARIMER | metadata only |
| larimer-comprehensive-plan-volume-1-sd004-09 | CO-COUNTY-LARIMER | metadata only |
| larimer-fee-increase-memo-sd004-lc-09 | CO-COUNTY-LARIMER | source_structure |
| larimer-governing-policies-sd004-lc-14 | CO-COUNTY-LARIMER | metadata only |
| fort-collins-ibc-amendments-sd005-02 | CO-MUNICIPAL-FORT_COLLINS | metadata only |
| fort-collins-irc-amendments-sd005-03 | CO-MUNICIPAL-FORT_COLLINS | metadata only |
| fort-collins-iecc-amendments-sd005-04 | CO-MUNICIPAL-FORT_COLLINS | metadata only |
| fort-collins-imc-amendments-sd005-event-08 | CO-MUNICIPAL-FORT_COLLINS | metadata only |
| fort-collins-wildfire-code-sd005-05 | CO-MUNICIPAL-FORT_COLLINS | source_structure |
| fort-collins-land-use-article-1-sd005-07 | CO-MUNICIPAL-FORT_COLLINS | source_structure |
| fort-collins-land-use-article-2-sd005-08 | CO-MUNICIPAL-FORT_COLLINS | metadata only |
| fort-collins-land-use-article-3-sd005-event-12 | CO-MUNICIPAL-FORT_COLLINS | metadata only |
| fort-collins-land-use-article-4-sd005-event-13 | CO-MUNICIPAL-FORT_COLLINS | metadata only |
| fort-collins-land-use-article-5-sd005-event-14 | CO-MUNICIPAL-FORT_COLLINS | metadata only |
| fort-collins-ifgc-amendments-sd005-event-19 | CO-MUNICIPAL-FORT_COLLINS | metadata only |
| fort-collins-ipc-amendments-sd005-event-20 | CO-MUNICIPAL-FORT_COLLINS | metadata only |
| fort-collins-ispsc-amendments-sd005-event-21 | CO-MUNICIPAL-FORT_COLLINS | metadata only |
| fort-collins-iebc-amendments-sd005-event-22 | CO-MUNICIPAL-FORT_COLLINS | metadata only |
| fort-collins-ipmc-amendments-sd005-event-23 | CO-MUNICIPAL-FORT_COLLINS | metadata only |
| fort-collins-land-use-article-6-sd005-event-24 | CO-MUNICIPAL-FORT_COLLINS | metadata only |
| fort-collins-land-use-article-7-sd005-event-26 | CO-MUNICIPAL-FORT_COLLINS | metadata only |
| fort-collins-meeting-packet-9909c320-sd005-09 | CO-MUNICIPAL-FORT_COLLINS | metadata only |
| fort-collins-meeting-packet-98ce54e6-sd005-11 | CO-MUNICIPAL-FORT_COLLINS | metadata only |
| larimer-equity-fee-memo-sd007-05 | CO-COUNTY-LARIMER | checked_tables |
| larimer-equity-fee-resolution-sd007-04 | CO-COUNTY-LARIMER | checked_passages |
| larimer-february-meeting-packet-sd007-08 | CO-COUNTY-LARIMER | metadata only |
| weld-building-fees-sd008-01 | CO-COUNTY-WELD | checked_tables |
| greeley-building-fees-sd008-06 | CO-MUNICIPAL-GREELEY | checked_tables |
| greeley-development-impact-fee-memo-sd008-07 | CO-MUNICIPAL-GREELEY | checked_tables |
| greeley-water-sewer-proposed-pif-notice-sd008-08 | CO-MUNICIPAL-GREELEY | checked_tables |
| weld-ordinance-26-01-atlas-directed | CO-COUNTY-WELD | source_structure |
| weld-ehs-fees-2026-atlas-directed | CO-COUNTY-WELD | checked_tables |
| mesa-land-development-code-atlas-directed | CO-COUNTY-MESA | metadata only |
| grand-junction-ifc-ordinance-5269-atlas-directed | CO-MUNICIPAL-GRAND_JUNCTION | source_structure |
| grand-junction-fire-fees-atlas-directed | CO-MUNICIPAL-GRAND_JUNCTION | checked_tables |
| grand-junction-ordinance-5340-atlas-directed | CO-MUNICIPAL-GRAND_JUNCTION | checked_passages |
| mesa-planning-fees-2017-2018-atlas-directed | CO-COUNTY-MESA | checked_tables |
| mesa-building-fees-exhibit-a-atlas-directed | CO-COUNTY-MESA | checked_tables |
| el-paso-planning-fees-sd011 | CO-COUNTY-EL_PASO | checked_tables |
| el-paso-boh-ehs-fees-sd011 | CO-COUNTY-EL_PASO | checked_tables |
| el-paso-ordinance-26-01-sd011 | CO-COUNTY-EL_PASO | metadata only |
| el-paso-ldc-wildfire-appendix-e-sd011 | CO-COUNTY-EL_PASO | metadata only |
| el-paso-open-burning-22-001-sd011 | CO-COUNTY-EL_PASO | metadata only |
| el-paso-ldc-chapter-1-sd011 | CO-COUNTY-EL_PASO | metadata only |
| el-paso-ldc-chapter-2-sd011 | CO-COUNTY-EL_PASO | metadata only |
| el-paso-ldc-chapter-5-sd011 | CO-COUNTY-EL_PASO | metadata only |
| el-paso-unsafe-buildings-18-03-sd011 | CO-COUNTY-EL_PASO | metadata only |
| el-paso-boh-admin-regulations-sd011 | CO-COUNTY-EL_PASO | metadata only |
| el-paso-boh-bylaws-sd011 | CO-COUNTY-EL_PASO | checked_passages |
| el-paso-boh-bylaws-spanish-sd011 | CO-COUNTY-EL_PASO | checked_passages |
| el-paso-boh-ehs-fees-spanish-sd011 | CO-COUNTY-EL_PASO | checked_tables |
| colorado-springs-code-services-fees-2015-atlas-directed | CO-MUNICIPAL-COLORADO_SPRINGS | checked_tables |
| colorado-springs-construction-fees-atlas-directed | CO-MUNICIPAL-COLORADO_SPRINGS | checked_tables |
| douglas-ehs-fees-atlas-directed | CO-COUNTY-DOUGLAS | checked_tables |
| pueblo-planning-fees-atlas-directed | CO-MUNICIPAL-PUEBLO | checked_tables |
| pueblo-county-planning-fees-sh-ext-002 | CO-COUNTY-PUEBLO | checked_tables |
| gunnison-building-fees-resolution-2025-24-sh-ext-003 | CO-COUNTY-GUNNISON | checked_passages |
| gunnison-building-code-resolution-2023-22-sh-ext-003 | CO-COUNTY-GUNNISON | checked_passages |
| gunnison-iwuic-resolution-2022-33-sh-ext-003 | CO-COUNTY-GUNNISON | checked_passages |
| chaffee-cwrc-ordinance-2026-02-atlas-directed | CO-COUNTY-CHAFFEE | checked_passages |
| chaffee-electric-ordinance-2026-01-atlas-directed | CO-COUNTY-CHAFFEE | checked_passages |
| chaffee-planning-application-fees-atlas-directed | CO-COUNTY-CHAFFEE | checked_tables |

## Limits

- Every row is an exact manual-source custody identity, not a percentage of geographic, documentary or legal coverage. The legacy local coverage ledger is pinned and unchanged.
- Authority identities are explicit provenance assignments bound to the same source SHA and source ID; these assignments are not independent adjudications of legal authority.
- Verified HTTP time is populated only from preserved direct successful response evidence; received-package acquisition claims remain separately reported and qualified. Repository intake time is never substituted for acquisition.
- Review JSON and its exact allowlisted schema are checked. This inventory does not rerun every original visual, native-span, table or package verifier and does not independently recertify the recorded review.
- A review link preserves only its stated scope. Partial passages, draft annotations and source-structure checks remain distinct from complete text or numeric certification. Overlapping reviews and copied packages are not additive coverage.
- Null review means no explicit allowlisted review join in this inventory, not proof that the document has no native text, prior title-page inspection or other historical review. Recorded provenance retains those limits.
- Historical pending external-review labels remain frozen source-first context; later reconciliations are separate additive records and do not change the original bytes.
- All sources remain research-only, legal_currentness not_verified, answer_safe false. No calculation, applicability, legal-effect, current-law, rule-unit, canonical-index or coverage promotion is made.
- Historical custody-only stage: 2026-09-12 El Paso custody update: 13 received PDFs have explicit authority/source/hash joins only; title-role checks are not mapped as full-document or numeric-table review. Their verified HTTP acquisition and legal currentness remain unknown. All previous 19 scoped review links and 46 source rows are retained unchanged; the legacy coverage ledger is untouched.
- Historical planning-review stage: Later accepted planning-source review: one of the 13 El Paso PDFs now has a checked_tables link covering 104 scanned fee rows, 15 footnotes and three General Notes. Source native text is empty; text is manually read from images and the clipped P3-ENG-14 label remains unresolved. The other 12 El Paso sources have no mapped full review. The original 19 review links remain unchanged; 20 sources now have explicit scoped reviews, with no legal-currentness or coverage promotion.
- Later Colorado Springs intake: two municipal source originals bring this custody snapshot to 61 rows. The modern seven-page Construction Services schedule adds one explicit checked_tables review (21 mapped / 40 unmapped); the 2015 Code Services schedule remains metadata-only with no full numeric review mapping. All previous 20 review joins remain unchanged.
- Greeley later reacquisition: three existing sources have new verified HTTP evidence from September 12, 2026 exact-byte GETs. These completion times are later reacquisition events, not the original Sherlock acquisition or September 11 repository receipt. The original null canonical URLs, received_review_package methods, receipt times, authority provenance and review scopes remain unchanged. No continuous availability, legal currentness or retroactive acquisition verification is implied.
- This snapshot adds accepted Pueblo County fee, Larimer staff memo and El Paso English bylaws reviews. Review links describe source fidelity, not enactment, calculation, statewide completeness or current law. Earlier receipt/acquisition claims and null verified HTTP times remain unchanged. Pueblo County is distinct from the City of Pueblo; its reported reservation/result interval is not independently witnessed HTTP timing.
- September 13 later integration: three received Gunnison County originals add exact authority joins, bringing this snapshot to 67 sources. Actual repository receipt is 2026-09-13T15:57:35.577123Z; supplied HTTP times remain reported and verified HTTP fields remain null. Separate accepted source reviews add the two existing Spanish El Paso documents and the Gunnison building-fee resolution: 30 linked / 37 unmapped. Prior 64 authority and 27 review joins remain unchanged. The Spanish reviews do not certify English equivalence; Gunnison prose fee components are not table-row or legal-rule counts. All review scopes, missing native text, footer-year uncertainty and historical custody limitations are retained, with no coverage or current-law promotion.
- The three later Gunnison IWUIC/Chaffee review links preserve their original recorded source-fidelity scope and qualifications. Source QA pre-intake/pending-review fields remain historical; separate root acceptance and actual intake do not rewrite them.
- Chaffee direct HTTP completion times are separately bound to exact successful response receipts. Later repository receipt time does not establish adoption or current law.
- The final Gunnison code/Chaffee fee review links preserve original source wording, conditions, image/OCR/native distinctions and pending-review chronology. Root acceptance does not replace those historical fields or authenticate signatures/current applicability.
- The last Chaffee fee original has an actual 2026-09-13T17:02:09.370066Z repository receipt, separate from the observed 16:44:33.133961Z HTTP completion. Neither is a legal effective date.

Exact artifact hashes, recorded scope fields, provenance claims and timestamps are retained in inventory.json. Linked scopes overlap and must not be summed.
