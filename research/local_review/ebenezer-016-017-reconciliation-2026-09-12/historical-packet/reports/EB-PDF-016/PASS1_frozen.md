# PASS1_frozen — EB-PDF-016

- assignment_id: EB-PDF-016
- source_id: greeley-development-impact-fee-memo-sd008-07
- authority_id (collection context only): CO-MUNICIPAL-GREELEY
- reviewer: Ebenezer (Grok Bot) / executor Grok Bot
- pass: 1
- review_method: caption_mediated_source_first
- visual_verification: pending_atlas_direct_image_review
- legal_currentness: not_verified
- prior_candidate_exposure: none
- utc_start: 2026-09-12T22:07:28Z
- expected_pages: 3
- inspected_pages (assisted representations): 3
- assistance_supplier/tool: Cursor Read tool (caption-mediated image descriptions); assistance model/supplier internals unknown
- assistance_disclosure: Read does not expose raw pixels to the reviewer; each page/crop return is a caption/mediated description that may include OCR or model interpretation and can share errors with a later candidate. Chat activation also supplied prior image_description blocks for the same three PNGs; those were treated as additional non-authoritative captions, not as certified transcription. Pillow crops were re-Read for regional coverage; still caption-mediated. This pass is ASSISTED, not direct pixel inspection and not blind visual transcription.
- sealed_materials_not_opened: candidate / 02-candidate-text; 03-custody; 04-verification; full packet manifest.json; PREPARATION_RECEIPT; validator; prior Atlas/Sherlock/Ebenezer analyses for this source; EB-PDF-015 and EB-PDF-017 materials; native PDF text extraction / OCR as Pass1 substitute
- packet_manifest_sha256 (assignment-supplied; file not opened): dcb4565ae9a3ce007f7a96e0fcc74cd6ebe8664b435cb1a278d8a75a2f152397
- activation_sha256 (ACTIVATION.md independently hashed): fc9f78bbdc4a9d416ab946bb435de96957cc3d5a748d2063e912eea1d350e3de
- SOURCE_ONLY_IDENTITIES_sha256 (independently hashed): 29ea8ec18e6343e66bff79e6786eba26eb37dbdd09e7bed61fc4a5f26ea9afd5
- original_pdf_sha256 (independently hashed; PDF bytes not text-extracted): 9effbd15196898c16105913ee21032db52ad1e259f4f9def0586804726f78709

## Page image SHA-256 (verified before review)

| file | sha256 | size_bytes |
|------|--------|------------|
| page-0001.png | 897dddf6df53617e3a20a252adf1a70151dcc11722cda9719227e20bd894e17c | 567833 |
| page-0002.png | aac84312750eeafac8e707fda7f9d4f215be0dcbcb11c1b1b086c355ad350d2e | 536314 |
| page-0003.png | 98513c20960e97d94bae033957e0b75b95e32572b0eb74ce6a136103b3e8cb60 | 157212 |
| original.pdf | 9effbd15196898c16105913ee21032db52ad1e259f4f9def0586804726f78709 | 651009 |

Image geometry (Pillow metadata only; not pixel reading): each page PNG 2550×3300 RGB.

## Coverage table

| physical_page | file | printed_page_label (tool-reported) | representation received | method | unchecked / unresolved |
|---------------|------|------------------------------------|-------------------------|--------|-------------------------|
| 1 | page-0001.png | none observed; running title "2026 Development Impact Fee Schedule" top-right | full-page Read + header/body/bullets/EAF-para/table crops | caption_mediated_source_first | Exact logo geometry; exact dash/hyphen Unicode in table title and bullet dashes; exact bold/weight styling; footer content if any below table (captions did not clearly report a footer); transposed-vs-horizontal table layout noted below |
| 2 | page-0002.png | none observed; same running title top-right | full-page Read + intro/police/fire/park/trails/storm crops | caption_mediated_source_first | Exact Unit-column blanks vs merged cells; "Sq. Ft" vs "Sq. Ft." punctuation; Police Retail/Restaurant fee triple has conflicting crop captions (see anomalies); exact column-header row repeat under section headers; horizontal rule at bottom only partially characterized |
| 3 | page-0003.png | none observed; same running title top-right | full-page Read + table + lower-blank crops | caption_mediated_source_first | Numeric column headers absent on this page (continuation); Unit spelling "Square Feet" vs page-2 "Sq. Ft"; large blank lower ~75% of page (intentionally empty per captions); no footer text reported |

## Global layout / marks (tool-reported; pending Atlas verification)

- Formal City of Greeley Finance Department memorandum + multi-page fee schedule tables.
- Logo (tool-reported): blue "Greeley" / "City of" / gold-tan "Colorado" with stylized cowboy-hat and hills graphic.
- No handwriting, signatures, strike-through, insertions, or deletions reported on any page.
- No stamped seals reported.
- legal_currentness: not_verified — title/date/fee schedule do not prove adoption, effect, completeness, or current force.

---

## Page 1 — Finance Department Memorandum / EAF methodology

**Printed label:** none (physical page 1 of 3)

**Running title (top right, tool-reported):** 2026 Development Impact Fee Schedule

**Header / memo fields (assisted reading):**

```
[City of Greeley Colorado logo — left]

FINANCE DEPARTMENT
MEMORANDUM

DATE: November 1, 2025
FROM: City of Greeley, Colorado
RE: 2026 Development Impact Fees
```

**Body paragraphs (assisted reading; wording from overlapping full-page + crop captions):**

```
In the 2023 adoption of the Police, Fire, Park, Trails, Storm Drainage, and Transportation development impact fees, the methodology to adjust fees annually was adopted. City of Greeley Code Chapter 4.64.055(b) states that the fees will be recalculated by applying the Economic Adjustment Factor (EAF).

The EAF is determined on an annual basis, using six weighted data variables, considered to be representative of economic growth, the cost of materials and services associated with constructing capital projects, and general economic conditions. The variables include:
```

**Bulleted variables (bold metric names tool-reported; dash glyph Unicode not claimed):**

```
• Percent change in Greeley Utility Customer Accounts – representing the growth and scope of public services;
• Percent change in CDOT Construction Cost Index – representing the cost of providing transportation networks;
• Percent change in Engineering News Records Construction Cost Index – representing material costs associated with capital projects;
• Percent change in Engineering News Records Building Cost Index – representing labor costs associated with capital projects;
• Percent change in Assessed Value of Greeley Real Property – representing growth and the economic value of real property assets; and
• Percent change in Greeley MSA Employment – representing a general indicator of the economic health of the area.
```

**EAF calculation paragraph (assisted):**

```
The 2026 EAF was calculated using the most reliable and consistent annual data sets from the previous full year. Since the EAF is calculated on November 1, 2025, for the 2026 fee year, the percent change was calculated using year end 2024 compared to year end 2023.
```

Note: captions consistently report "year end" without a hyphen; hyphenation not certified from pixels.

**Table (assisted): title tool-reported as** `2026 EAF – Weighting and Percent Change by Indicator`

Layout note (important): tighter crop captions report indicators as **column headers** with two data rows labeled **Weight** and **% change** (horizontal layout). Some summary captions transpose this into Indicator/Weight/% Change columns. Assisted primary layout reading (crop-preferred):

| (row label) | Greeley Utility Customers | CDOT CCI | ENR CCI | ENR BCI | Assessed Value | Greeley MSA Employment | Economic Adjustment Factor |
|-------------|---------------------------|----------|---------|---------|----------------|------------------------|----------------------------|
| Weight | 25.0% | 15.0% | 5.0% | 5.0% | 25.0% | 25.0% | (empty / none reported) |
| % change | -6.79% | -0.22% | -0.19% | 5.28% | -4.68% | 2.32% | **-2.07%** (bold tool-reported) |

Weights sum to 100.0% as reported. Final EAF **-2.07%** preserved as printed association; arithmetic not independently verified as legal truth.

**Page 1 unchecked:** exact logo vectors; any micro-print under table; exact en-dash vs hyphen in title "EAF – Weighting…".

---

## Page 2 — Fee schedule (Police through Storm Drainage)

**Printed label:** none (physical page 2 of 3)

**Running title (top right):** 2026 Development Impact Fee Schedule

**Introductory paragraphs (assisted):**

```
For 2026, based on the methodology (applying the economic adjustment factor to the 2025 fee, rounding the result to zero decimals and comparing it to the 2025 fee), the Police, Fire, Park, Trails, Storm Drainage, and Transportation development impact fees will decrease an average of -2.07%.

The Water and Sewer board establishes the Water and Sewer Plant Investment Fees (PIF), the equivalent to impact fees. These will be adopted in December.

The fee adjustment requires public notification approximately 120 days before the March 1, 2026 effective date. The fee changes by type of Development Impact Fee are presented on the attached schedule.
```

Notes:
- Parenthetical methodology wording preserved as captioned; exact parentheses/commas not Unicode-certified.
- "Development Impact Fee" vs "Fees" in the last sentence: crop caption used singular "Fee"; full-page summaries varied — singular "Fee" retained as crop-preferred; alternate "Fees" unresolved.
- "attached schedule" ends the intro; Transportation section continues on page 3.

**Schedule table columns (tool-reported header):** Fee Structure | Unit | 2025 Fee | % Change | 2026 Fee

### Police Development Fee

| Fee Structure | Unit | 2025 Fee | % Change | 2026 Fee |
|---|---|---:|---:|---:|
| Residential 1,200 square feet or less of heated living space | (blank) | $156 | -1.92% | $153 |
| Residential 1,201 square feet to 1,500 square feet of heated living space | (blank) | $276 | -2.17% | $270 |
| Residential 1,501 square feet to 1,800 square feet of heated living space | (blank) | $314 | -1.91% | $308 |
| Residential 1,801 square feet or more of heated living space | (blank) | $334 | -2.10% | $327 |
| Retail/Restaurant | 1,000 Sq. Ft of Building | **UNRESOLVED — see anomaly A1** | **UNRESOLVED** | **UNRESOLVED** |
| Office & Other Services | 1,000 Sq. Ft of Building | $539 | -2.04% | $528 |
| Industrial | 1,000 Sq. Ft of Building | $275 | -2.18% | $269 |

**Anomaly A1 — Police Retail/Restaurant fee triple (caption conflict):**
- Majority/full-page + continuation-crop consistent assisted reading: **$1,004 | -2.09% | $983**
- Conflicting crop caption (partial cut-off): $1,381 | -2.32% | $1,349
- Conflicting crop caption (partial cut-off): $1,001 | -0.90% | $992
Primary working reading for association checks: $1,004 / -2.09% / $983, **pending Atlas direct image review**. Do not treat as certified glyphs.

Unit wording for non-residential on page 2 commonly captioned `1,000 Sq. Ft of Building` (period after Ft inconsistent across captions).

### Fire Development Fee

| Fee Structure | Unit | 2025 Fee | % Change | 2026 Fee |
|---|---|---:|---:|---:|
| Residential 1,200 square feet or less of heated living space | (blank) | $409 | -1.96% | $401 |
| Residential 1,201 square feet to 1,500 square feet of heated living space | (blank) | $718 | -2.09% | $703 |
| Residential 1,501 square feet to 1,800 square feet of heated living space | (blank) | $815 | -2.09% | $798 |
| Residential 1,801 square feet or more of heated living space | (blank) | $869 | -2.07% | $851 |
| Retail/Restaurant | 1,000 Sq. Ft of Building | $2,235 | -2.06% | $2,189 |
| Office & Other Services | 1,000 Sq. Ft of Building | $1,200 | -2.08% | $1,175 |
| Industrial | 1,000 Sq. Ft of Building | $613 | -2.12% | $600 |

### Park Development Fee

| Fee Structure | Unit | 2025 Fee | % Change | 2026 Fee |
|---|---|---:|---:|---:|
| Residential 1,200 square feet or less of heated living space | (blank) | $3,036 | -2.08% | $2,973 |
| Residential 1,201 square feet to 1,500 square feet of heated living space | (blank) | $5,334 | -2.06% | $5,224 |
| Residential 1,501 square feet to 1,800 square feet of heated living space | (blank) | $6,048 | -2.07% | $5,923 |
| Residential 1,801 square feet or more of heated living space | (blank) | $6,449 | -2.06% | $6,316 |

(No non-residential Park rows reported.)

### Trails Development Fee

| Fee Structure | Unit | 2025 Fee | % Change | 2026 Fee |
|---|---|---:|---:|---:|
| Residential 1,200 square feet or less of heated living space | (blank) | $456 | -1.97% | $447 |
| Residential 1,201 square feet to 1,500 square feet of heated living space | (blank) | $801 | -2.12% | $784 |
| Residential 1,501 square feet to 1,800 square feet of heated living space | (blank) | $906 | -2.10% | $887 |
| Residential 1,801 square feet or more of heated living space | (blank) | $967 | -2.07% | $947 |

(No non-residential Trails rows reported.)

### Storm Drainage Development Fee

| Fee Structure | Unit | 2025 Fee | % Change | 2026 Fee |
|---|---|---:|---:|---:|
| Impervious Area | Per Impervious Square Foot | $0.315 | -2.22% | $0.308 |

**Page 2 footer/marks:** horizontal line below table tool-reported; no page number reported. Transportation fees not on this page (continue page 3).

---

## Page 3 — Transportation Development Fee (continuation)

**Printed label:** none (physical page 3 of 3)

**Running title (top right):** 2026 Development Impact Fee Schedule

**Table:** section header row tool-reported as **Transportation Development Fee** with **Unit** in the unit column; numeric columns unlabeled on this page (continuation of 2025 Fee / % Change / 2026 Fee from page 2 — association inferred from parallel structure, not from printed headers on page 3).

| Transportation Development Fee | Unit | 2025 Fee (inferred col) | % Change (inferred) | 2026 Fee (inferred) |
|---|---|---:|---:|---:|
| Residential 1,200 square feet or less of heated living space | (blank) | $3,810 | -2.07% | $3,731 |
| Residential 1,201 square feet to 1,500 square feet of heated living space | (blank) | $7,037 | -2.06% | $6,892 |
| Residential 1,501 square feet to 1,800 square feet of heated living space | (blank) | $8,058 | -2.07% | $7,891 |
| Residential 1,801 square feet or more of heated living space | (blank) | $8,609 | -2.07% | $8,431 |
| Retail/Restaurant | 1,000 Square Feet of Building | $9,963 | -2.07% | $9,757 |
| Office & Other Services | 1,000 Square Feet of Building | $6,426 | -2.07% | $6,293 |
| Industrial | 1,000 Square Feet of Building | $3,273 | -2.08% | $3,205 |

Unit spelling note: page-3 captions prefer spelled-out `1,000 Square Feet of Building`; page-2 captions prefer abbreviated `1,000 Sq. Ft of Building`. Both retained as tool-reported; exact source spelling pending Atlas verification.

**Lower page:** large blank white region (~lower 2/3–3/4); no additional text, signatures, or notes reported.

---

## Unchecked / unresolved summary

1. All glyph-level / Unicode / typography claims — caption-mediated only; visual_verification pending Atlas.
2. Police Development Fee → Retail/Restaurant amounts (Anomaly A1) — conflicting captions.
3. Exact Unit-column blank vs merged-cell geometry for residential rows.
4. Exact dash characters (en-dash/em-dash/hyphen) in bullets and EAF table title.
5. Whether page-3 numeric columns reprint headers or omit them (captions say omit/unlabeled).
6. "year end" hyphenation; "Sq. Ft" period placement; singular/plural "Fee" in "type of Development Impact Fee".
7. Logo fine detail; any micro-footer beyond horizontal rules.
8. legal_currentness: not_verified.

## Printed identity (brief)

City of Greeley Finance Department memorandum dated November 1, 2025, RE: 2026 Development Impact Fees; Economic Adjustment Factor **-2.07%** for 2026 fee year (year-end 2024 vs 2023 data); schedule decreases Police/Fire/Park/Trails/Storm Drainage/Transportation fees averaging -2.07%; effective date March 1, 2026 after ~120 days public notification; Water/Sewer PIF separate (December adoption).

## Status

`partial_assisted_coverage_complete_pending_atlas_direct_image_review` — declared caption-mediated procedure covered all 3 expected physical pages; not a claim of certified visual transcription or legal currency.
