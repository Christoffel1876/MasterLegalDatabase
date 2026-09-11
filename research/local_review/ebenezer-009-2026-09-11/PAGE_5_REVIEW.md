---
title: EB009 page 5 source-layout review
prepared_at: 2026-09-11T17:38:24.420507+00:00
source_id: larimer-building-fees-sd004-06
physical_page: 5
status: proposed_for_root_review
legal_currentness: not_verified
---

# Page 5 review

The two material layout findings are supported: the source order is **Table 1-E / Electrical A–D → Other Inspections 1–9 → Table 1-F / Document Imaging**. The native text places Table 1-F before Other Inspections, which can misassign the electrical continuation to the imaging table. The corrected heading belongs only above Document Imaging. Table 1-E continuation is review structure; the box does not repeat that caption.

## Evidence and method

- Original PDF SHA-256: `1ac4dde1a7bbbd8ebf3b26bf8719c5c6854bbbd4844c221f54729d36bb193b2c`.
- Complete page PNG SHA-256: `3381afcddc5f8370c45f6c2cd9f6753cfd09b60727ecb9f3629ecf941827a7f3`.
- Native page JSON SHA-256: `e4cfd8516e916509691142da1c898f7348ae4b1248f8b79448b07bbd09173617`; native text SHA-256: `f046257f08bee5b070ee31a85f393c26ee87f96fe8d81c4296b0bc706a534569`.
- Inspected the complete page image and four direct PDF crops at 300 dpi. The full page shows the numbered box ending before the centered Table 1-F caption and the six-row imaging grid.
- Layout coordinates provide reproducible corroboration: Other Inspections heading is about y=395 PDF points; Table 1-F about y=598; Document Imaging heading about y=633. These coordinates support the image reading and do not replace it.
- This comparison used the native text and Ebenezer reports; it is not a blind pass. Root separately reviews the page-1 cross-reference context.

## External finding dispositions

| Reference | Disposition | Finding |
|---|---|---|
| EB009-P2-001 | supported | The full image and boundary crop put Table 1-F below the Other Inspections border and above the Document Imaging border; the native stream emits it before Other Inspections. Relocate the caption once, preserving all intervening numbered items. |
| EB009-P2-002 | supported | Other Inspections 1–9 is the electrical continuation block, while Table 1-F labels Document Imaging. Page 5 does not repeat a Table 1-E caption inside Other Inspections. Use ordered block/table metadata to bind the list to 1-E. Do not insert a fabricated source heading. Root separately verifies page-1 table-reference context. |
| EB009-P2-004 | supported | Living Area: is visibly part of the first residential row/stub beside the <=1000 wording and $147. Join the stub and first row in the explicit row pairing; preserve the source words Less than or equal to rather than substituting a mathematical glyph. |
| EB009-P2-006 | qualified | The native stream contains two U+0020 spaces in round down  to. The rendered example has a visibly wider gap, but raster inspection does not certify the underlying count/type of whitespace characters. The proposed one-space readability normalization is not a proven content insertion error. Normalize whitespace only under a declared presentation policy, retaining native evidence unchanged. Do not certify exact source space count. |
| EB009-P2-008 | supported | All six imaging categories and fees are present; explicit pairing follows the visible grid. The 30-page overlap is printed. Represent six pairs after the corrected Table 1-F heading; preserve both conflicting boundary wordings. |
| PASS1-page5-Other-item7 | additional_pass1_correction | PASS1 adds a long dotted leader between inspections and Actual Cost. The source crop shows blank alignment space in item 7; the dotted leader is in item 8. Use a declared column separator or blank alignment for item 7. Preserve a note that item 8 has a dot leader without asserting the exact count or codepoints. |
| PASS1-page5-Document-Imaging-heading | additional_pass1_correction | PASS1 repeats Document Imaging Fees as a standalone bold heading and a Markdown table header. The source shows one spanned Document Imaging Fees heading. Keep one source heading; identify any repeated table label as reviewer formatting rather than a second source occurrence. |
| PASS1-page5-Section109.7-and-units | supported | The tight crop supports the visually joined Section109.7 form. The repeated IBC in the citation and absence of /hour after $54.00 in item 2 are visible. Preserve Section109.7 IBC/NEC $54.00; do not correct citations or supply a missing hourly unit. Do not extend this into an exact-codepoint certification. |

## Proposed ordered transcripts

These are bounded page-5 research transcriptions. Pipe characters mark reviewer-added column/pair separators. Line wraps and alignment whitespace are normalized; the native bytes remain unchanged. Exact whitespace codepoints and dot-leader counts are not certified.

### 1. Electrical Permit Fees (1-E)

```text
Table 1-E
Electrical Permit Fees
Fees are based on A, B, C, or D below.

A. Residential Electrical Installation: (new, remodel, addition) (round sq. ft. up to next 100 for calculation)
Residential Installation – Based on enclosed living area only | FEE
Living Area: Less than or equal to 1000 square feet | $147
1,001 square feet but not more than 1,500 square feet | $203
1,501 square feet but not more than 2,000 square feet | $261
Greater than 2001 square feet | $261 + $12 per each additional 100 sq. ft.
EXAMPLE: (2235 sq. ft.) first 2000 sq. ft. = $261 + (2 (235 rounded down to next 100) x $12 = 24) = $285

B. Commercial and other fees: Including some residential installations not based on square footage (non-habitable area, garage, shop, solar, etc.). These fees are calculated from the customer’s total cost (contract price), including materials, items and labor- whether provided by the contractor or the property owner.
Valuation of Installation – (Based on cost to customer of labor, material and items) | FEE
Less than or equal to $2000 = $147 (base fee) | $147
$2001 or more | $147 + $12 per thousand of job valuation
EXAMPLE: The installation cost is $5,150 (round down to $5,000) = $147 + (5 x $12 = $60) = $207

C. Mobile/Modular/Manufactured Home Set | $133
D. Temporary Construction Meter | $ 66
```

### 2. Other Inspections and Fees: (1-E)

```text
Other Inspections and Fees:
1. Inspections outside of normal business hours (minimum charge two hours) $54.00/hour
2. Re-inspection fees assessed per IRC Section R108.8/IBC Section109.7 IBC/NEC $54.00
3. Inspections when no fee is specifically indicated (minimum charge one hour) $54.00/hour
4. A penalty fee will be assessed up to or equal to the electrical permit fee for work commenced without first obtaining a building permit per IRC Section R108.6/IBC Section 109.4/NEC
5. A Code Compliance (CC) fee will be assessed on permits associated with a CC case…$100
6. Trim permit. If a permit expires after the rough-in inspection has been completed, inspected, and approved by the electrical inspector, but before the final inspection is approved, a TRIM permit must be obtained. The fee is based on the valuation of the remaining electrical work to be inspected. Minimum trim permit fee is $147.00
7. Use of outside consultants for inspections | Actual Cost
8. Docket fee for Board of Appeals | $55.00
9. Solar permit fees are capped by state law at $500 for residential installations and $1,000 for commercial installations.
```

### 3. Document Imaging Fees (1-F)

```text
Table 1-F
Document Imaging Fees
Residential Plans | No Fees required
Commercial plans submitted on digital disc. | No Fees required
Commercial plans 10 pages and under | $18
Commercial plans 11 pages to 30 pages | $36
Commercial plans 30 to 50 pages | $100
Commercial plans greater than 50 pages | $100 plus $2 for each additional page
```

## Preserved source anomalies and limits

- A says round square feet up to the next 100; its example says 235 rounded down and ends at $285. Both are retained without reconciliation.
- The A upper row literally says Greater than 2001 square feet, not greater than 2000 or 2001 and up.
- B retains the source terms non-habitable, labor- whether, the cost basis including owner-provided inputs, and its round-down example.
- D displays $ 66 with a visible gap; this transcription preserves a separating space without certifying exact encoded whitespace.
- Other item 2 retains the visually joined Section109.7 and repeated IBC text, and displays $54.00 without /hour.
- Other item 4 uses electrical permit fee and first obtaining a building permit; these are not made consistent by editing.
- Other item 6 retains the expiration/rough-in/final-inspection conditions, valuation of remaining work, and minimum $147.00.
- Other item 9 is a source assertion about state-law caps, not an independently verified legal conclusion here.
- Imaging rows 11 pages to 30 pages ($36) and 30 to 50 pages ($100) overlap at 30. The source overlap is preserved.
- The no-fee digital-disc row retains the terminal period in disc.; the greater-than-50 row retains $100 plus $2 for each additional page.

PASS1’s invented dotted leader in item 7 should be removed; the source uses blank alignment there. Its duplicated Document Imaging heading is reviewer formatting, not a second source heading. The single-space claim in EB009-P2-006 is not established as an extraction insertion error; a readable one-space rendering is acceptable only under the stated whitespace policy.

Source conditions, amounts, units and exceptions are retained. The page-30 overlap and rounding inconsistency are not resolved. This review does not determine current law or validate the source’s claims about state-law caps. Findings on other physical pages remain outside this proposal.
