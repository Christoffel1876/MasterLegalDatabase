---
title: Mesa historical planning fee schedule source review
reviewer: Atlas
date: 2026-09-11
status: all_three_pages_source_rows_and_associations_reviewed
review_mode: atlas_candidate_aware_not_blind
legal_currentness: not_verified
adoption_effectiveness: not_verified
---

# Historical planning fees — full source review

All three physical pages and four targeted crops were directly viewed. This is internal Atlas candidate-aware QA; pages 1–2 were already viewed in the earlier directed-gap audit. No external reviewer or blind pass is claimed. The original PDF and all **13,127 native UTF-8 bytes** remain unchanged, partitioned into **201 source lines**.

The typed record binds **77 source rows in 17 groups and 231 cells**. One row is a recording-payment instruction with no amount. Null is not zero. The historical application columns are **2009 FEE** and **2017–18 FEE**, as printed, followed by separate supplemental/product/agency fee sections. The school land-dedication unit is per residential dwelling unit. No arithmetic, current-fee calculation or source-year conflict resolution is performed.

Source SHA256: `af11318af2ce3ea5e4b1af313f348ab851a855a76418e3878d1a166c084dadb6`. Exact [official PDF](https://www.mesacounty.us/sites/default/files/2022-12/planning-fee-schedule.pdf) response ended at `2026-09-11T20:17:18.212943+00:00`. Retrieval/upload times do not establish enactment. The PDF itself labels the suspension **2017 & 2018**, qualified by other fees potentially remaining.

## Source findings and qualifications

- **MPF-01** — The PDF labels its suspension 2017 & 2018 and retains other-fee and extraordinary-cost qualifications. Historical columns do not prove current zero fees or an all-fees waiver.
- **MPF-02** — The appeal row shows 275.00 in both years. The trailing native 1 is visually a raised footnote marker. Preserve native 275.001, with separate visible-footnote annotation. Refund condition remains attached.
- **MPF-03** — Conditional-use text says fewer than 200 employees OR less than 10 acres; next row more than 200 employees OR 10 acres or more. The source does not resolve overlaps or exactly 200 employees by itself. Keep literal comparisons and permit-extension parent; do not interpret precedence.
- **MPF-04** — The last acreage tier has base 675.00 plus55.00per 25 acres in 2009; the 2017–18 column prints 0.00 on each line. Separate continuation line and parent; no multiplication, rounding or invented acreage bracket.
- **MPF-05** — Planning-hearing 2017–18 value has no asterisk; Board-hearing value has **; postcard values have *. The quantity and adjustment note remain. Preserve marker mismatch as source typography; no marker harmonization.
- **MPF-06** — PDF states 1 October 2020 expiration; four named school districts appear as per-dwelling fee categories. Retained HTML separately states 1 October 2022. Leave conflict unresolved; no acquired extension/resolution and no district-law ownership promotion.
- **MPF-07** — Imagery options include 10.00 per sm with no minimum and customer CD media/labor; or 25.00 per square mile with 2-square-mile/50.00 minimum and county material/labor. Literal CDW is retained. Do not blend options, repair terminology or infer present availability/pricing.
- **MPF-08** — Four CGS review classes preserve dwelling-unit/acreage thresholds, payment with submittal and repeated warning that the eventual bill may be larger. Treat source amounts as historical stated submittal charges, not caps; retain separate CGS payee.
- **MPF-09** — Recording instruction specifies checks or money orders only payable to Mesa County Clerk and Recorder, without an amount. Null amount remains unknown, not zero.

## Separate HTML evidence

The retained official webpage snapshot is a separate source. It states suspension effective **2017 to present** and school-dedication resolution expiration **1 October 2022**. The PDF states **1 October 2020**. Both original assertions are retained with independent body/text hashes and byte bounds; neither supersedes the other in this review. The governing resolution or extension was not acquired. No network request was made for this review.

## Reviewed source rows

The readable tables remove dotted leader padding and collapse whitespace for display only. Exact native strings, source lines, glyph coordinates, amounts, markers and all conditions remain unchanged in JSON and candidate.txt. Bracketed text is reviewer annotation. The appeal cell displays its visible superscript marker separately; native `275.001` is preserved unchanged and is not treated as a three-decimal amount. Asterisks remain literal.

### P1-GENERAL — physical page 1: Application fees — general and Conditional Use

| Source item | 2009 FEE | 2017–18 FEE |
|---|---|---|
| Accessory Dwelling Unit | 80.00 | see Short Form |
| Administrative Adjustment | 80.00 | 0.00 |
| Agricultural Division | 275.00 | 0.00 |
| Agricultural Housing Renewal | 10.00 | 0.00 |
| Appeals of Administrative Decisions | 275.00 | 275.00 [superscript 1] |
| Fewer than 200 employees or less than 10 acres | 525.00 | 0.00 |
| More than 200 employees or 10 acres or more | 975.00 | 0.00 |
| Permit extension | half of original fee | 0.00 |
| Extinguishment of Utility Easement | 105.00 | 0.00 |
| Land Use Development Code Text Amendment | 80.00 | 0.00 |
| Land Use Master Plan Map Amendments | 500.00 | 0.00 |

Table context: C-YEARS, C-EXTRAORDINARY.
Row P1-GENERAL-R05: C-APPEAL.
Row P1-GENERAL-R06: C-CONDITIONAL.
Row P1-GENERAL-R07: C-CONDITIONAL.
Row P1-GENERAL-R08: C-CONDITIONAL.

### P1-MAJOR — physical page 1: Major Subdivision

| Source item | 2009 FEE | 2017–18 FEE |
|---|---|---|
| Sketch Plan | 225.00 | 0.00 |
| \* Concept Plan – Fee + acreage (see acreage fee chart below) | 690.00 | 0.00 |
| Final Plan | 620.00 | 0.00 |
| Final Plat | 225.00 | 0.00 |

Table context: C-YEARS, C-MAJOR, C-EXTRAORDINARY.
Row P1-MAJOR-R02: C-ACREAGE.

### P1-MISC — physical page 1: Minor Subdivision and Oil & Gas Drilling

| Source item | 2009 FEE | 2017–18 FEE |
|---|---|---|
| Minor Subdivision | 275.00 | 0.00 |
| Oil & Gas Drilling | 80.00 | 0.00 |

Table context: C-YEARS, C-EXTRAORDINARY.

### P1-PUD — physical page 1: Plan Unit Development (PUD)

| Source item | 2009 FEE | 2017–18 FEE |
|---|---|---|
| Sketch Plan | 225.00 | 0.00 |
| \* Concept Plan/Rezone – Fee + acreage (see acreage fee chart below) | 665.00 | 0.00 |
| Final Plan | 620.00 | 0.00 |
| Final Plat | 225.00 | 0.00 |

Table context: C-YEARS, C-PUD, C-EXTRAORDINARY.
Row P1-PUD-R02: C-ACREAGE.

### P1-ACREAGE — physical page 1: ACREAGE FEE CHART (All zones other than AFT Majors)

| Source item | 2009 FEE | 2017–18 FEE |
|---|---|---|
| 5-10 Acres | 140.00 | 0.00 |
| 11-15 Acres | 195.00 | 0.00 |
| 16-20 Acres | 255.00 | 0.00 |
| 21-50 Acres | 395.00 | 0.00 |
| 51-75 Acres | 560.00 | 0.00 |
| 76-100 Acres | 675.00 | 0.00 |
| 101 or More Acres | 675.00 | 0.00 |
| [continuation of 101 or More Acres tier] | Fee Plus $55.00 per 25 acres | 0.00 |

Table context: C-YEARS, C-ACREAGE, C-EXTRAORDINARY.
Row P1-ACREAGE-R08: C-ACREAGE-BASE.

### P1-PROPERTY — physical page 1: Property Line Adjustments

| Source item | 2009 FEE | 2017–18 FEE |
|---|---|---|
| Boundary Line Adjustment (unplatted land) | 275.00 | 0.00 |
| Legal and Physical | 275.00 | 0.00 |
| Re-Subdivision (previously platted land) | 470.00 | 0.00 |

Table context: C-YEARS, C-PROPERTY, C-EXTRAORDINARY.

### P1-LAST — physical page 1: Other application fees

| Source item | 2009 FEE | 2017–18 FEE |
|---|---|---|
| Residential/Agricultural Site Plan (paid at Building Permit) | 10.00 | 0.00 |
| Driveway Permit | 10.00 | 0.00 |
| Rezoning | 500.00 | 0.00 |

Table context: C-YEARS, C-EXTRAORDINARY.

### P2-APPLICATIONS — physical page 2: Application fees (continued)

| Source item | 2009 FEE | 2017–18 FEE |
|---|---|---|
| Short Form (Change of Use, Commercial Site Plan, Annual Events, Daycare, Accessory Dwelling Unit, Ag Labor Housing, Exempt Home Occupation) | N/A | 0.00 |
| Sign Permit | 10.00 | 0.00 |
| Simple Land Division | 275.00 | 0.00 |
| Site Plan – Major | 275.00 | 0.00 |
| Site Plan – Minor | 80.00 | 0.00 |
| Street Name Change | 155.00 | 0.00 |
| Thirty-five Acre Parcels Created by Plat | No Fee | No Fee |
| Vacation - Right-of-Way / Access | 445.00 | 0.00 |
| Written Interpretations | 80.00 | 0.00 |
| Zoning Variances | 300.00 | 0.00 |

Table context: C-YEARS, C-EXTRAORDINARY.

### P2-CONTINUATION — physical page 2: CONTINUATION FEES

| Source item | 2009 FEE | 2017–18 FEE |
|---|---|---|
| Display Ad for Planning Commission Hearing | $40.00\*\* | $0.00 |
| Display Ad for Board of County Commission Hearing | $40.00\*\* | $0.00\*\* |
| Property Owner Notification Postcards | $.45\* | $0.00\* |

Table context: C-YEARS, C-CONTINUATION, C-POSTCARDS, C-EXTRAORDINARY.

### P2-SCHOOL — physical page 2: School Land Dedication Fee Per Residential Dwelling Unit

| Source item | Fee as printed | Conditions as printed |
|---|---|---|
| Mesa County Valley School District #51 | $920.00 |  |
| Plateau Valley School District #50 | 920.00 |  |
| DeBeque School District 49JT | 920.00 |  |
| Delta County School District 50J | 920.00 |  |

Table context: C-CONTINUING, C-SCHOOL-EXPIRY.

### P2-TIF — physical page 2: Transportation Impact Fee (TIF)

| Source item | Fee as printed | Conditions as printed |
|---|---|---|
| Fee collected at Planning Division | $1902.00\* | (\*Fee is $1902 for a Single Family Residence) |

Table context: C-CONTINUING, C-TIF.

### P2-COPIES — physical page 2: Copies

| Source item | Fee as printed | Conditions as printed |
|---|---|---|
| 8 ½ x 11 | $.25 |  |
| 8 ½ x 14" | 1.00 |  |
| 11" x 17" | 2.00 |  |
| Oversized | 5.00 |  |

Table context: C-CONTINUING, C-COPIES.

### P2-PUBLICATIONS — physical page 2: Publications

| Source item | Fee as printed | Conditions as printed |
|---|---|---|
| Land Development Code | $30.00 |  |
| Master Plan | 100.00 |  |
| Countywide Land Use Plan with Appendix | 30.00 |  |
| Rural Planning Area | 15.00 |  |
| Joint Urban Planning Area | 15.00 |  |
| Land Use and Development Policies | 15.00 |  |
| Area Plans | 15.00 |  |
| Road Access Policy | 10.00 |  |

Table context: C-CONTINUING, C-PUBLICATIONS, C-PRINT-PRICE.

### P3-GIS — physical page 3: GIS Product Fee Schedule Plotting

| Source item | Fee as printed | Conditions as printed |
|---|---|---|
| 8 ½ X 11 | $5.00 |  |
| 11 X 17 | 5.00 |  |
| 24 X 36 | 8.00 |  |
| 36 X 48 | $15.00 |  |
| Minimum Plotting/Printing Charge | $5.00 Per Sheet |  |

Table context: C-GIS.

### P3-IMAGERY — physical page 3: Digital Imagery

| Source item | Fee as printed | Conditions as printed |
|---|---|---|
| File size: 30-33 megabytes per square mile | $10.00 per sm (No Minimum) | Mesa County provides Computer and CDW Customer provides CD media and labor |
| Or | $25.00 per square mile. (2 square mile minimum $50.00 Minimum Charge) | Mesa County provides all material and labor. |

Table context: C-IMAGERY.

### P3-CGS — physical page 3: Colorado Geological Survey (CGS) Review

| Source item | Fee as printed | Conditions as printed |
|---|---|---|
| Very Small Residential Subdivision Review (1-3 dwelling units and less than 100 acres) Paid with the submittal | $600.00 | When CGS bills applicant the fee may be larger |
| Small Subdivision Review (Greater than 3 dwelling units and less than 100 acres) Paid with the submittal | $950.00 | When CGS bills applicant the fee may be larger |
| Large Subdivision Review (Greater than or equal to 100 acres and less than 500 acres) Paid with the submittal | $1550.00 | When CGS bills applicant the fee may be larger |
| Very Large Subdivision Review (Greater than or equal to 500 acres) Paid with the submittal | $2500.00 | When CGS bills applicant the fee may be larger |

Table context: C-CGS-PAYEE.

### P3-RECORDING — physical page 3: Recording Fees

| Source item | Fee as printed | Conditions as printed |
|---|---|---|
| Recording Fees: | [no amount stated] | CHECKS or MONEY ORDERS ONLY payable to Mesa County Clerk and Recorder. |

Table context: exact source row conditions.

## Bound parent headings, notes and exceptions

These blocks preserve source wording exactly, including original capitalization, source years and markers. They can repeat text already present in a row when that text supplies a shared condition.

### C-YEARS — physical page 1

Exhibit A; suspended 2017 & 2018 with other-fee qualification; original 2009 and 2017–18 headings. Yellow highlight on latter is graphical, not a native word change.

```text
Exhibit A 
 
Mesa County Planning 
Application Fees have been 
suspended for 2017 & 2018* 
(*other fees may remain in 
effect) 
2017 & 2018 
 
TYPE OF APPLICATION 
2009 FEE 2017- 18 FEE
```

### C-APPEAL — physical page 1

Superscript 1 requires refund when appeal upheld by Board of County Commissioners; not a zero fee.

```text
1Note: if appeal is upheld by Board of County Commissioners, the fee will be refunded to appellant.
```

### C-CONDITIONAL — physical page 1

Conditional Use is parent of both employee/acreage alternatives and permit extension; preserve all or/and comparisons literally.

```text
Conditional Use
```

### C-MAJOR — physical page 1

Parent heading for four distinct stages.

```text
Major Subdivision
```

### C-PUD — physical page 1

Literal Plan Unit Development, not silently corrected to Planned.

```text
Plan Unit Development (PUD)
```

### C-ACREAGE — physical page 1

Asterisk cross-reference; chart excludes AFT Majors as printed; not silently reclassified.

```text
 
* 
ACREAGE FEE CHART (All zones other than AFT Majors)
```

### C-ACREAGE-BASE — physical page 1

The following Fee Plus line belongs to this 101-or-more tier; preserve base and additional amounts separately.

```text
101 or More Acres........................................................................................................... 675.00 
0.00
```

### C-PROPERTY — physical page 1

Parent Property Line Adjustments.

```text
Property Line Adjustments
```

### C-CONTINUATION — physical page 2

Continuation-fee heading; year columns continue the application table.

```text
CONTINUATION FEES
```

### C-POSTCARDS — physical page 2

Source retains one/two-asterisk patterns; Times number of postcards and adjustment wording preserved, not normalized to identical markers.

```text
Property Owner Notification Postcards…………………………………………….… 
$.45* 
$0.00* 
.................................................................................................................... Times number of postcards 
** Increase or decrease in the cost of the display ad or the postcard expenses will cause adjustments in these 
fees.
```

### C-EXTRAORDINARY — physical page 2

Applicant responsibility for all extraordinary processing costs; no blanket fee waiver.

```text
Payment of all extraordinary costs incurred for processing any development application 
shall be the responsibility of the applicant.
```

### C-CONTINUING — physical page 2

Source explicitly says fees continue 2017 & 2018; school fee unit is per residential dwelling unit. No post-period effect inferred.

```text
THE FOLLOWING FEES WILL CONTINUE TO BE COLLECTED IN 2017 & 2018 
 
Supplemental County Fees 
 
School Land Dedication Fee Per Residential Dwelling Unit
```

### C-SCHOOL-EXPIRY — physical page 2

Literal 1 October 2020 expiration and annual review with school districts; inconsistent HTML 2022 is separate.

```text
School Land Dedication resolution expires 1 October 2020 and annual reviews will be coordinated with the School 
Districts.
```

### C-TIF — physical page 2

Collected at Planning Division; starred $1902 for single-family residence, not generalized all-use rate.

```text
Transportation Impact Fee (TIF) 
Fee collected at Planning Division ............................................................................................$1902.00* 
(*Fee is $1902 for a Single Family Residence)
```

### C-COPIES — physical page 2

Copies heading; sizes and prices retained.

```text
Copies
```

### C-PUBLICATIONS — physical page 2

Publication prices, not regulatory filing fees.

```text
Publications
```

### C-PRINT-PRICE — physical page 2

Printed on request at current printer’s price; source qualifier retained.

```text
— Printed on request at current printer’s price
```

### C-GIS — physical page 3

Maps/orthophotos/other drawings, black-and-white or color; minimum per-sheet charge retained in its own row.

```text
GIS Product Fee Schedule Plotting 
Maps, Ortho photos, Other drawings (B & W or Color):
```

### C-IMAGERY — physical page 3

Technical product description and two material/labor options preserved; no recalculation of minimum.

```text
Digital Imagery: 
The following color digital images are available from Mesa County for the Grand Valley Area. 
So far we have about 1099 square miles orthorectified. 
Format: .tif files with associated .tfw (coordinate file) 
Coordinate system: UTM, Zone 12 NAD 83 
Resolution: ½ Meter 
Tile format: 1 square mile section 
File size: 30-33 megabytes per square mile ..........................$10.00 per sm (No Minimum) 
Mesa County provides Computer and CDW Customer provides CD media and labor 
Or $25.00 per square mile. (2 square mile minimum $50.00 Minimum Charge) 
Mesa County provides all material and labor.
```

### C-CGS-PAYEE — physical page 3

Checks or money orders payable to Colorado Geological Survey; separate state agency, not school district or county planning fee.

```text
Other Fees: 
 
Colorado Geological Survey (CGS) Review Checks or Money Orders payable to Colorado Geological 
Survey
```

## Validation and scope

The portable validator replays source/native/page/crop hashes; matches all source lines to rows or contexts; reconstructs every cell from its original byte occurrence and glyph box; checks historical-column left/right positions; preserves required parent, refund, extraordinary-cost and payee links; and rejects bounded tampering cases. All CGS class thresholds and repeated larger-bill qualifications remain in their source rows.

```sh
PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-status-venv/bin/python "/Users/mcoors/Documents/Project Geode/handoffs/atlas-reviews/mesa-planning-fees-source-review-2026-09-11/validate_review.py"
```

This validates extraction custody and source associations. It does not establish legal currentness, completeness of county fees, actual fee liability, adoption/effectiveness, present product availability, or ownership of school-district or CGS law. No repository, canonical source, ledger, Git, bot or scheduler changes were made.
