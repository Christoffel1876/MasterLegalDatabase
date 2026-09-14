# PASS1_frozen — EB-PDF-018

- assignment_id: EB-PDF-018
- source_id: weld-building-fees-sd008-01
- authority_id (collection context only): CO-COUNTY-WELD
- reviewer: Ebenezer (Grok Bot) / executor Grok Bot
- pass: 1
- review_method: caption_mediated_source_first
- visual_verification: pending_atlas_direct_image_review
- legal_currentness: not_verified
- prior_candidate_exposure: none (candidate / 02-candidate-text / 03-custody / 04-verification / full packet manifest.json / INVENTORY / PREPARATION_RECEIPT / validator / prior Atlas-Sherlock-Ebenezer analyses / 019–020 materials not opened)
- utc_start: 2026-09-12T22:36:29Z
- expected_pages: 5
- inspected_pages: 5 (full-page PNG representations + region crops; caption-mediated only)
- printed_identity (brief): Weld County Building Permit & Inspection Fee Schedule — JANUARY 2026 (building valuation fee tiers; manufactured structure & plan review fees; road/county facilities/drainage & electrical fees; plumbing/mechanical cost-of-job fees; building valuation per sq ft table; Chapter 20 impact fees)
- image_method: Cursor Read tool on complete source-page files `page-0001.png` … `page-0005.png`, plus Pillow region crops re-Read via the same tool. No OCR as Pass-1 substitute. No native PDF text extraction. `original.pdf` was not present in the workdir; its SHA-256 was taken only from `SOURCE_ONLY_IDENTITIES.json` (file bytes not hashed locally).
- captions_assistance: ASSISTED. (1) User/chat message included pre-supplied `image_description` blocks for all five pages before tool Reads. (2) Every Read of a PNG (full page or crop) returned a caption/mediated description, not raw pixel access to the reviewer. Captions treated as non-authoritative assisted claims. Caption internals (possible OCR/model interpretation) unknown. Never labeled as direct pixel inspection or blind visual transcription.
- packet_manifest_sha256 (bound; file not opened): b9e843e783a65a238d1a7e1106a5d0a49ea08f7ffbb59b9ca02d841e7639a112
- START_HERE_sha256 (verified): 142ca7e336f197d3636f362f3044e5a6f716c11950817e38daeefc996b5b948a
- SOURCE_ONLY_IDENTITIES_sha256 (verified): 1c07c1b39db7798b0fea34c224fe7d06beecb6bac5ab77fbf549ce25674b5564
- original_pdf_sha256 (from identities only; PDF absent from workdir): 8fb5dc78f67407a22857160f107a0253da42320e9e502387be573ef53cab9f27

## Page image SHA-256 (verified before transcription)

| file | sha256 | size_bytes (workdir) |
|------|--------|----------------------|
| page-0001.png | f5f9b05d556c781e76a2174164f6df455916bc4e127614a257c0f20367774f80 | 462090 |
| page-0002.png | ae113eca8434b9144915b8b1edd3f3ab9e2356a6a4e3c1a47df0ef1d9aaecbaa | 426440 |
| page-0003.png | 8a5ec2d214f29331bfb13300b220a0e96304b32e147899ecdb6b070200ad8283 | 317058 |
| page-0004.png | 03423d98ce2a996f97622dbf75215a6a94e49ebecea093b3fff16c427182ddf9 | 615773 |
| page-0005.png | 3b6ec39274b6a80f162312d6fe555608570cad8274cf0b7874ec090f620856fe | 410183 |

Page dimensions (Pillow, not visual): all 2550×3300 px.

## Coverage table

| physical_page | file | printed_page_label (tool-reported) | method | source representation received | unviewed_or_unresolved |
|---------------|------|--------------------------------------|--------|--------------------------------|-------------------------|
| 1 | page-0001.png | none reported (schedule page; no page number in captions) | caption_mediated_source_first; full-page Read + crops: title, valuation table, manufactured/plan-review lower | mediated full-page + crop captions | Exact leader-dot counts; exact table border geometry; whether “$2000” vs “$2,000” glyph spacing in row 2 end-phrase; whitespace/margins; any faint footer marks beyond caption silence |
| 2 | page-0002.png | none reported | caption_mediated_source_first; full-page Read + crop of premove/demolition region | mediated full-page + crop captions | Exact leader-dot counts; comma presence variance on County Facilities SFD amount ($1636.00 vs $1,636.00 across captions); exact dash/en-dash glyphs in ranges; margins |
| 3 | page-0003.png | none reported; footer “Revised 012/25” (tool-reported) | caption_mediated_source_first; full-page Read + crops: fee tiers, footer/NOTE box | mediated full-page + crop captions | Exact double-border geometry of NOTE box; grey fill shade; whether investigation-fee standalone line punctuation matches NOTE box; dash glyphs in “2 hrs”; margins |
| 4 | page-0004.png | none reported | caption_mediated_source_first; full-page Read + horizontal table-band crops + notes crop | mediated full-page + band/crop captions covering all use-group rows | Exact cell alignment/kerning; whether “Building Use Group” header text is fully visible left of IA (header crop showed left cell partially cut as “Building”); exact N.P. vs “N.P” spacing; dollar signs absent on table body (caption reports bare decimals) — not pixel-confirmed; notes separator glyphs (- vs –) |
| 5 | page-0005.png | none reported | caption_mediated_source_first; full-page Read + crops: header, road fees, facilities/drainage | mediated full-page + crop captions | Exact underline geometry under section headers; period presence after “sq. ft” inconsistently reported across crops vs full-page; leader-dot counts; whether “Fees” column header appears only under Road section |

## Typography / layout notes (global; caption-reported)

- Black text on white; clean sans-serif (caption claim).
- Pages 1–2, 5: dotted leader lines between labels and amounts.
- Page 1: black header row with white text on building-permit valuation table.
- Page 3: double-bordered NOTE box (crop: light grey fill); footer “Revised 012/25” bottom-right outside box.
- Page 4: large bordered valuation grid; “Construction Classification” spanning IA–VB.
- Page 5: underlined chapter/section headers (caption).
- No handwriting/signatures reported. No strike-through/insertions/deletions reported.
- legal_currentness: not_verified — printed dates/fees are transcription claims only; not treated as currently adopted law.

---

## Page 1 — Building permit & inspection fee schedule (title page)

**Printed label:** none (tool-reported)

**Visual (caption-reported):** Title + JANUARY 2026; valuation fee table; manufactured structure fees; plan review fees; leaders on lower lists.

**Transcribed text (reading order; caption-mediated):**

```
WELD COUNTY BUILDING PERMIT & INSPECTION FEE SCHEDULE
JANUARY 2026
```

### Building Permit Fees (table)

Header (caption): Total Valuation | Fee (calculated according to building valuation per sq. ft.)

| Total Valuation | Fee |
| :--- | :--- |
| $1 to $500 | $24 |
| $501 to $2,000 | $24 for the first $500 plus $3.00 for each additional $100 or fraction thereof, to and including $2000 |
| $2,001 to $25,000 | $69.00 for the first $2,000 plus $14.48 for each additional $1,000 or fraction thereof, to and including $25,000 |
| $25,001 to $50,000 | $402.00 for the first $25,000 plus $10.32 for each additional $1,000 or fraction thereof, to and including $50,000 |
| $50,001 to $100,000 | $660.00 for the first $50,000 plus $7.34 for each additional $1,000 or fraction thereof, to and including $100,000 |
| $100,001 to $500,000 | $1027.00 for the first $100,000 plus $7.00 for each additional $1,000 or fraction thereof, to and including $500,000 |
| $500,001 to $1,000,000 | $3827.00 for the first $500,000 plus $5.00 for each additional $1,000 or fraction thereof, to and including $1,000,000 |
| $1,000,000 and up | $6327.00 for the first $1,000,000 plus $3.00 for each additional $1,000 or fraction thereof |

### Manufactured Structure Permit Fees

```
Manufactured homes block & tied in established park (includes electric) ..... $460.00
Manufactured homes temporarily stored on property ..... $85.00
Commercial manufactured structures ..... see building valuation per sq ft
Manufactured home single family dwelling ..... see building valuation per sq ft
Engineered foundations (Crawlspace, basement or permanent installation) ..... see building valuation per sq ft
```

### Plan Review Fee for Building/Manufactured Home Permits

```
Major Plan Review ..... 70% of building valuation fee
  New single family dwelling & all commercial buildings
  New utility buildings over 3,000 sq ft
Minor Plan Review ..... $80.00
  Residential additions/alterations & utility buildings additions/alterations under 1,000 sq ft
  Manufactured home single family dwelling on engineered foundation
  New utility buildings under 3,000 sq ft
```

**Notes / anomalies preserved:**
- Row 2 end-phrase uses `$2000` without comma (caption); other thresholds use commas — preserved as reported.
- Some fee bases omit `.00` ($24) while others include it — preserved.
- “per sq ft” vs “per sq. ft.” variance between sections — preserved as captioned.
- No silent arithmetic normalization of tier breakpoints.

---

## Page 2 — Impact, drainage, premove, demolition, electrical fees

**Printed label:** none (tool-reported)

**Visual (caption-reported):** Six bold section headings; dotted leaders; residential electrical by sq ft; other electrical by valuation.

**Transcribed text (reading order; caption-mediated):**

### Road Impact Fee

```
All new single family dwellings will be assessed ..... $3,794.00
All commercial & industrial buildings will be assessed ..... see attached
```
(Full-page caption also phrased first line as “All new single family dwellings: $3,794.00” — same amount; “will be assessed” present in chat/full captions inconsistently; amount $3,794.00 consistent.)

### County Facilities Impact Fee

```
All new single family dwellings ..... $1636.00
All new commercial & industrial structures ..... see attached
```
(Caption variance: some captions show `$1,636.00` with comma; crop/full Read also `$1636.00` without comma — unresolved which glyph form is on the page; amount digits 1636 consistent.)

### Drainage Fee

```
All land uses* ..... $0.22 per impervious sq ft area
* The impervious area of streets or driveways within the public right-of-way adjacent to the parcel shall be included up to the centerline of the street. Gravel roads and driveways shall be counted as 50% impervious.
```

### Premove Inspection Fees

```
Move-In Dwelling ..... $230.00
Move-In Utility Structure ..... $230.00
```

### Demolition Permit Fees

```
Dwelling/Manufactured Home/Utility Structure ..... $80..00
Commercial Structures ..... see cost of job table
```

**ANOMALY (preserved):** Demolition dwelling line amount captioned as `$80..00` (two consecutive periods / double decimal) on both full-page and crop Reads — not normalized to $80.00.

### Electrical Permit Fees

**Residential** (caption note: includes single family residences, duplexes, condominiums, townhouses and construction and extensive remodeling and additions, based on enclosed living area):

```
0 to 500 sq ft ..... $43.00
501 sq ft to 1,000 sq ft ..... $60.00
1,001 sq ft to 1,500 sq ft ..... $83.00
1,501 sq ft to 2,000 sq ft ..... $90.00
Per 100 sq ft in excess of 2,000 sq ft ..... $6.00
```

**All Other Electrical Fees** (caption: computed on dollar value of electrical installations, including labor and materials, excluding mobile home and travel trailer parks / total cost to customer):

Valuation of Work (actual cost to customer – labor and materials) [dash glyph unresolved]:

```
Not more than $300 ..... $43.00
$301 to $2,000 ..... $50.00
$2,001 to $3,000 ..... $59.00
$3,001 to $50,000 ..... $17.00 per $1,000 or fraction thereof of total valuation
More than $50,000 ..... contact Weld County Building Department
Construction Meter (Temporary) ..... $43.00
```

---

## Page 3 — Building, plumbing & mechanical fees per cost of job

**Printed label:** none in body; footer tool-reported: `Revised 012/25`

**Visual (caption-reported):** Tier list with leaders; Other Inspections hourly list; investigation-fee sentence; large double-bordered NOTE box (grey fill per crop); revision string bottom-right.

**Transcribed text (reading order; caption-mediated):**

```
Building, Plumbing & Mechanical Permit Fees Per Cost of Job
Up to $20,001 ..... $115.41
$20,001 to $40,000 ..... $397.50
$40,0001 to $60,000 ..... $571.69
$60,001 to $80,000 ..... $702.92
Over $80,000 ..... $827.88
```

**ANOMALY (preserved):** Third tier start captioned as `$40,0001` (five digits after comma / trailing 1) on full-page and crop — not corrected to $40,001.

```
Other Inspections and Fees:
Inspections outside of normal business hours (minimum charge – 2 hrs) ..... $80.00 per hour
Inspections for which no fee is specifically indicated ..... $80.00 per hour
Reinspection fee ..... $80.00 per hour
Additional plan review required by changes, additions or revisions to approved plans ..... $80.00 per hour
```

```
Investigation fee – per Building Official – shall be 50% of the amount of the permit fee as established by the BOCC
```

**NOTE box (caption; double-line border; grey fill reported on crop):**

```
NOTE: When work for which a permit is required by the Weld County Code is started or proceeds PRIOR to obtaining a permit, an additional investigation fee shall be added to the cost of the permit. The investigation fee shall be 50% of the fee established by separate action by the Weld County Board of County Commissioners. In no event shall the investigation fee exceed the amount set by separate action by the Board of County Commissioners. The payment of such investigation fee shall not relieve any persons from fully complying with the requirements of the Weld County Code in the execution of the work, nor from any other penalties prescribed within the Weld County Code
```

Footer (outside box, bottom-right):

```
Revised 012/25
```

**Notes / anomalies preserved:**
- `Revised 012/25` preserved literally (not normalized to 12/25 or 01/2025).
- `$40,0001` preserved.
- PRIOR capitalized in NOTE (caption).

---

## Page 4 — Building Valuation Per Square Foot

**Printed label:** none (tool-reported)

**Visual (caption-reported):** Centered title; “Construction Classification” over columns IA IB IIA IIB IIIA IIIB IV VA VB; left column Building Use Group; Notes below table.

**Column headers:** Building Use Group | IA | IB | IIA | IIB | IIIA | IIIB | IV | VA | VB

**Table body (caption-mediated from full-page + band crops; values as reported, no $ signs in cells):**

| Building Use Group | IA | IB | IIA | IIB | IIIA | IIIB | IV | VA | VB |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A-1 Assembly, theaters, with stage | 337.41 | 325.40 | 315.80 | 303.35 | 283.46 | 275.24 | 292.98 | 264.14 | 254.04 |
| A-1 Assembly, theaters, without stage | 309.77 | 297.76 | 288.16 | 275.71 | 256.07 | 247.85 | 265.35 | 236.75 | 226.65 |
| A-2 Assembly, nightclubs | 269.42 | 261.52 | 253.31 | 243.65 | 228.21 | 222.01 | 235.29 | 207.53 | 199.66 |
| A-2 Assembly, restaurants, bars, banquet halls | 268.42 | 260.52 | 251.31 | 242.65 | 226.21 | 221.01 | 234.29 | 205.53 | 198.66 |
| A-3 Assembly, churches | 314.40 | 302.40 | 292.80 | 280.35 | 260.82 | 252.61 | 269.98 | 241.51 | 231.40 |
| A-3 Assembly, general, community halls, libraries, museums | 264.03 | 252.03 | 241.42 | 229.98 | 209.33 | 202.12 | 219.61 | 190.01 | 180.91 |
| A-4 Assembly, arenas | 308.77 | 296.76 | 286.16 | 274.71 | 254.07 | 246.85 | 264.35 | 234.75 | 225.65 |
| B Business | 298.43 | 287.83 | 277.50 | 265.76 | 242.70 | 234.06 | 255.55 | 216.90 | 206.96 |
| E Educational | 282.06 | 272.26 | 263.65 | 252.74 | 235.87 | 223.82 | 244.04 | 206.65 | 200.02 |
| F-1 Factory and industrial, moderate hazard | 164.17 | 156.25 | 146.41 | 140.89 | 125.45 | 119.36 | 134.33 | 104.02 | 96.87 |
| F-2 Factory and industrial, low hazard | 163.17 | 155.25 | 146.41 | 139.89 | 125.45 | 118.36 | 133.33 | 104.02 | 95.87 |
| H-1 High hazard, explosives | 153.17 | 145.25 | 136.41 | 129.89 | 115.76 | 108.67 | 123.33 | 94.33 | N.P. |
| H-2, H-3, or H-4 High hazard | 153.17 | 145.25 | 136.41 | 129.89 | 115.76 | 108.67 | 123.33 | 94.33 | 86.17 |
| H-5 Hazardous production materials | 298.43 | 287.83 | 277.50 | 265.76 | 242.70 | 234.06 | 255.55 | 216.90 | 206.96 |
| I-1 Institutional, supervised environment | 274.98 | 265.13 | 255.66 | 246.00 | 225.17 | 219.12 | 245.49 | 202.80 | 195.56 |
| I-2 Institutional, hospitals | 469.18 | 458.58 | 448.25 | 436.51 | 411.45 | N.P. | 426.30 | 385.65 | N.P. |
| I-2 Institutional, nursing homes | 323.68 | 313.08 | 302.75 | 291.01 | 269.45 | N.P. | 280.80 | 243.65 | N.P. |
| I-3 Institutional, restrained | 314.93 | 304.33 | 294.00 | 282.26 | 261.70 | 252.06 | 272.05 | 255.55 | 223.96 |
| I-4 Institutional, day care facilities | 274.98 | 265.13 | 255.66 | 246.00 | 225.17 | 219.12 | 245.49 | 202.80 | 195.56 |
| M Mercantile | 201.08 | 193.18 | 183.97 | 175.31 | 159.52 | 154.32 | 166.95 | 138.84 | 131.97 |
| Oil and gas sites* | 278.14 | 268.29 | 258.82 | 249.16 | 227.83 | 221.78 | 248.64 | 205.46 | 198.22 |
| R-1 Residential, hotels | 314.93 | 304.33 | 294.00 | 282.26 | 261.70 | 252.06 | 272.05 | 255.55 | 223.96 |
| R-2 Residential, multiple family | 232.26 | 222.41 | 212.94 | 203.28 | 183.19 | 177.15 | 202.77 | 160.82 | 153.58 |
| R-3 Residential, one- and two-family | 215.90 | 210.16 | 205.11 | 200.73 | 194.02 | 187.11 | 204.78 | 180.41 | 169.09 |
| R-4 Residential, care/assisted living facilities | 274.98 | 265.13 | 255.66 | 246.00 | 225.17 | 219.12 | 245.49 | 202.80 | 195.56 |
| S-1 Storage, moderate hazard | 152.17 | 144.25 | 134.41 | 128.89 | 113.76 | 107.67 | 122.33 | 92.33 | 85.17 |
| S-2 storage, low hazard | 151.17 | 143.25 | 134.41 | 127.89 | 113.76 | 106.67 | 121.33 | 92.33 | 84.17 |
| U Utility, miscellaneous | 117.65 | 110.72 | 103.00 | 98.58 | 87.79 | 82.02 | 93.83 | 69.49 | 66.20 |

**Notes section (caption-mediated):**

```
N.P. = Not Permitted
Private garages/storage: Wood frame: $29.33 per square foot - Masonry: $36.25 per square foot - Structural steel: $42.94 per square foot
Unfinished basements (all use groups): $21.38 per square foot - Finished basements (all use groups): $28.03 per square foot
Manufactured homes/prefab structures: Deduct 30% of value per table above.
Move-in dwelling: Deduct 60% of value per table above.
Crawl space: $10.69 per square foot
Breezeway, enclosed porch, patio, covered deck, uncovered deck: $15.90 per square foot
Greenhouse: $11.93 per square foot
Carports: $19.94 per square foot
* Electrical and building fees apply on oil and gas sites.
```

**Notes / anomalies preserved:**
- S-2 label captioned with lowercase “storage” (crop); S-1 uses “Storage” — preserved as reported, not normalized.
- H-1 VB = N.P.; I-2 hospitals/nursing IIIB and VB = N.P.
- Oil and gas sites row carries asterisk tied to notes footline.
- Table cell values are caption-mediated; individual glyph/decimal verification pending Atlas.

---

## Page 5 — Chapter 20 Impact Fees

**Printed label:** none (tool-reported)

**Visual (caption-reported):** Centered underlined title “Chapter 20 Impact Fees”; three sections with underlined headers; leaders; drainage footnote.

**Transcribed text (reading order; caption-mediated):**

```
Chapter 20 Impact Fees
```

### Road Impact Fee Categories (Fees)

```
Single-Family Detached Dwelling ..... $3,794
Multi-Family Dwelling ..... $2,888
Mobile Home Park Pad ..... $2,049
Hotel/Motel Room ..... $2401
Shopping Center/Commercial ..... $5,353 per 1,000 sq. ft.
Office ..... $3,200 per 1,000 sq. ft.
Institutional/Quasi-Public ..... $1,520 per 1,000 sq. ft.
Manufacturing/Industrial ..... $2,561 per 1,000 sq. ft.
Warehouse ..... $963 per 1,000 sq. ft.
Mini-Warehouse ..... $745 per 1,000 sq. ft.
Agricultural Commercial 1,000 sq. ft. ..... $1,186 per 1,000 sq. ft.
```

**ANOMALY (preserved):** Hotel/Motel Room fee `$2401` without thousands comma (other four-digit fees use commas). Agricultural Commercial category label itself includes `1,000 sq. ft.`

### County Facilities Categories

```
Single-Family Detached Dwelling ..... $1,636
Multi-Family Dwelling ..... $1,126
Mobile Home Park Pad ..... $1,696
Hotel/Motel Room ..... $639
Shopping Center/Commercial ..... $1,261 per 1,000 sq. ft.
Office ..... $880 per 1,000 sq. ft.
Institutional/Quasi-Public ..... $343 per 1,000 sq. ft.
Manufacturing/Industrial ..... $385 per 1,000 sq. ft.
Warehouse ..... $164 per 1,000 sq. ft.
Mini-Warehouse ..... $83 per 1,000 sq. ft.
Agricultural Commercial ..... $330 per 1,000 sq. ft.
```

### Drainage Impact Fee

```
All Land Uses Sq. Ft. of Impervious Cover* ..... $0.22
* The impervious area of streets or driveways within the public right-of-way adjacent to the parcel shall be included up to the centerline of the street. Gravel roads and driveways shall be counted as 50% impervious.
```

**Cross-page note (not a legal conclusion):** Page 2 states SFD road impact $3,794.00 and facilities $1636/$1,636 and drainage $0.22; page 5 Chapter 20 lists matching SFD road $3,794 and facilities $1,636 and drainage $0.22, plus expanded categories — amounts transcribed only; no reconciliation asserted.

---

## Unchecked / unresolved (summary)

- All glyph-level / pixel-level verification pending Atlas direct image review.
- Exact leader-dot counts, dash vs en-dash, underline weight, table border geometry.
- Page 2 County Facilities SFD: `$1636.00` vs `$1,636.00` caption variance.
- Page 2 demolition `$80..00` and page 3 `$40,0001` and `Revised 012/25` and page 5 `$2401` — preserved as caption anomalies; pixel confirmation pending.
- Page 4 left header cell (“Building Use Group”) partially cut in header crop; full label from other captions.
- Page 5 “sq. ft.” trailing period inconsistently reported on some Office/Warehouse crop lines.
- `original.pdf` absent from workdir — SHA bound from SOURCE_ONLY_IDENTITIES only; PDF bytes not locally re-hashed; no PDF opened/extracted.
- legal_currentness: not_verified.

## Sealed materials not opened

Confirmed not opened this pass: candidate, 02-candidate-text, 03-custody, 04-verification, full manifest.json, INVENTORY, PREPARATION_RECEIPT, validator, prior reviews for this source, EB-PDF-019/020 materials.

## Status

`completed_pending_atlas_verification` for declared assisted Pass-1 procedure covering all 5 expected physical pages (caption_mediated_source_first). Does not mean all text/regions/glyphs were visually verified.
