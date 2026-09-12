---
title: Manual source and recorded review inventory
legal_currentness: not_verified
answer_safe: false
---

# Manual source/review inventory

59 custody rows; 19 have an explicit review link and 40 have no allowlisted review link.
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
| larimer-equity-fee-memo-sd007-05 | CO-COUNTY-LARIMER | metadata only |
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
| el-paso-planning-fees-sd011 | CO-COUNTY-EL_PASO | metadata only |
| el-paso-boh-ehs-fees-sd011 | CO-COUNTY-EL_PASO | metadata only |
| el-paso-ordinance-26-01-sd011 | CO-COUNTY-EL_PASO | metadata only |
| el-paso-ldc-wildfire-appendix-e-sd011 | CO-COUNTY-EL_PASO | metadata only |
| el-paso-open-burning-22-001-sd011 | CO-COUNTY-EL_PASO | metadata only |
| el-paso-ldc-chapter-1-sd011 | CO-COUNTY-EL_PASO | metadata only |
| el-paso-ldc-chapter-2-sd011 | CO-COUNTY-EL_PASO | metadata only |
| el-paso-ldc-chapter-5-sd011 | CO-COUNTY-EL_PASO | metadata only |
| el-paso-unsafe-buildings-18-03-sd011 | CO-COUNTY-EL_PASO | metadata only |
| el-paso-boh-admin-regulations-sd011 | CO-COUNTY-EL_PASO | metadata only |
| el-paso-boh-bylaws-sd011 | CO-COUNTY-EL_PASO | metadata only |
| el-paso-boh-bylaws-spanish-sd011 | CO-COUNTY-EL_PASO | metadata only |
| el-paso-boh-ehs-fees-spanish-sd011 | CO-COUNTY-EL_PASO | metadata only |

## Limits

- All 46 rows are exact manual-source custody identities, not a percentage of geographic, documentary or legal coverage. The legacy local coverage ledger is pinned and unchanged.
- Authority identities are explicit provenance assignments bound to the same source SHA and source ID; these assignments are not independent adjudications of legal authority.
- Verified HTTP time is populated only from preserved direct successful response evidence; received-package acquisition claims remain separately reported and qualified. Repository intake time is never substituted for acquisition.
- Review JSON and its exact allowlisted schema are checked. This inventory does not rerun every original visual, native-span, table or package verifier and does not independently recertify the recorded review.
- A review link preserves only its stated scope. Partial passages, draft annotations and source-structure checks remain distinct from complete text or numeric certification. Overlapping reviews and copied packages are not additive coverage.
- Null review means no explicit allowlisted review join in this inventory, not proof that the document has no native text, prior title-page inspection or other historical review. Recorded provenance retains those limits.
- Historical pending external-review labels remain frozen source-first context; later reconciliations are separate additive records and do not change the original bytes.
- All sources remain research-only, legal_currentness not_verified, answer_safe false. No calculation, applicability, legal-effect, current-law, rule-unit, canonical-index or coverage promotion is made.
- 2026-09-12 El Paso custody update: 13 received PDFs have explicit authority/source/hash joins only; title-role checks are not mapped as full-document or numeric-table review. Their verified HTTP acquisition and legal currentness remain unknown. All previous 19 scoped review links and 46 source rows are retained unchanged; the legacy coverage ledger is untouched.

Exact artifact hashes, recorded scope fields, provenance claims and timestamps are retained in inventory.json. Linked scopes overlap and must not be summed.
