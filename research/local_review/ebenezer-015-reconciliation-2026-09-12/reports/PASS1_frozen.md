# PASS1_frozen.md — EB-PDF-015

## Method disclosure (required)

| Field | Value |
|---|---|
| assignment_id | EB-PDF-015 |
| source_id | greeley-building-fees-sd008-06 |
| reviewer | Ebenezer (Grok Bot) |
| review_method | caption_mediated_source_first |
| visual_verification | pending_atlas_direct_image_review |
| tool | Read (caption-mediated) |
| assistance | Captions are NOT source quotations; may omit, invent, or misread details. Unknown caption internals (possible OCR/model interpretation). |
| prior_candidate_exposure | none |
| legal_currentness | not_verified |
| status | assisted Pass 1 complete for expected page representation; pending Atlas direct image verification |

**This is NOT direct pixel inspection and NOT blind visual transcription.** Work is ASSISTED and pending Atlas's actual image verification.

### Representations read (all caption-mediated)

1. Full page: `/workspace/geode-015/page-0001.png` (SHA-256 `051102365c1fc699736227afacc4065c157e32ac6d7d8dd77b4becb9698d8210`)
2. Pillow crop re-Reads (still caption-mediated; disclose each):
   - `crops/header.png`
   - `crops/table.png`
   - `crops/other_fees.png`
   - `crops/sales_tax_electrical.png`
   - `crops/footer.png`
   - `crops/sales_tax_body.png`
   - `crops/electrical_and_date.png`
   - `crops/table_bottom_rows.png`
   - `crops/footnotes_zone.png`

No native PDF extraction or OCR substitute was run for Pass 1. `original.pdf` was not present in the workdir (pages-only identity from SOURCE_ONLY_IDENTITIES.json). Candidate / custody / verification / full manifest / PREPARATION_RECEIPT / validate_activation.py / prior reviews were NOT opened.

---

## Coverage table

| Physical page | Expected | Source representation | Printed page label (caption-reported) | Method | Regions covered (caption) | Unchecked / unresolved |
|---:|:---:|---|---|---|---|---|
| 1 of 1 | yes | page-0001.png + crops above | none reported (single-page schedule; no “Page N” label captioned) | caption_mediated_source_first | Header/logo/title; Table 1-A bar; Building Permit Fees table (8 tiers); Other Inspections and Fees 1–9; footnotes ¹ ²; City Sales Tax; Temporary Electrical Inspection Fee; footer date | Exact glyph/Unicode/spacing; leader dots; micro-typography; logo fine detail beyond caption; any margin/seal/mark not described; caption conflict on one sales-tax digit (see below); item-6 terminal punctuation; item-9 heading style |

---

## Caption-mediated transcript (printed body)

Evidentiary basis: tool captions only. Wording below is the assisted reading as reported across full-page and crop captions. Where captions conflict, both are retained; no silent resolution.

### Header / frontmatter

- Logo (top left, caption): “City of” / “Greeley” / “Colorado” with stylized mountain / sun or cowboy-hat graphic (captions vary on graphic detail).
- Main title (centered, caption): **City of Greeley** / **2024 Building Permit Fee Schedule**

### Sub-header bar

- Left (caption): **Total Job Valuation** (described as white box / black text on or beside black bar)
- Right (caption): **Building Fees Table 1-A (Effective -2024)**  
  Note: hyphenation/spacing in “(Effective -2024)” preserved as captioned; exact spacing not pixel-verified.

### Building Permit Fees table

Column heads (caption): **Total Valuation** | **Fee**

| Total Valuation (caption) | Fee (caption) |
|---|---|
| $1 to $500 | $23.50 |
| $501 to $2,000 | $23.50 for the first $500.00, plus $3.05 for each additional $100.00 or fraction thereof, to and including $2,000.00 |
| $2,001 to $25,000 | $69.25 for the first $2,000.00, plus $14.00 for each additional $1,000.00 or fraction thereof, to and including $25,000.00 |
| $25,001 to $50,000 | $391.25 for the first $25,000.00, plus $10.10 for each additional $1,000.00 or fraction thereof, to and including $50,000.00 |
| $50,001 to $100,000 | $643.75 for the first $50,000.00, plus $7.00 for each additional $1,000.00 or fraction thereof, to and including $100,000.00 |
| $100,001 to $500,000 | $993.75 for the first $100,000.00, plus $5.60 for each additional $1,000.00 or fraction thereof, to and including $500,000.00 |
| $500,001 to $1,000,000 | $3,233.75 for the first $500,000.00, plus $4.75 for each additional $1,000.00 or fraction thereof, to and including $1,000,000.00 |
| $1,000,001 and up | $5,608.75 for the first $1,000,000.00, plus $3.65 for each additional $1,000.00 or fraction thereof |

### Other Inspections and Fees (numbered list, caption)

1. Inspections outside of normal business hours (minimum charge, two hours) — **$75.00 per hour¹**
2. Re-inspection fees assessed under provisions of Section 109.8 — **$75.00 per hour¹**
3. Inspections for which no fee is specifically indicated (minimum charge, one-half hour) — **$75.00 per hour¹**
4. Additional plan review required by changes, additions, or revisions to plans (minimum charge, one-half hour) — **$75.00 per hour¹**
5. For use of outside consultants for plan checking and inspections, or both — **Actual costs²**
6. **Major Plan Review Fees.** When a plan or other data are required to be submitted by Section 106, a plan review fee shall be paid at the time of submitting plans and specifications for review. Said plan review fee shall be 65 percent of the building permit as shown in the fee table above. The plan review fees specific to this section are separate fees from the permit fees and are in addition to the permit fees.-  
   *(Caption anomaly: terminal sequence reported as period followed by hyphen `.-`; preserve; not normalized.)*
7. **Minor Plan Review Fees.** A $75 plan review fee will be assessed on all residential and commercial additions, remodels, and utility buildings under 1,000 square feet.
8. **Mobile Home Setup Fee.** All mobile home setup permit fees will be $175.
9. Plan review fees for stock plans or rewrites shall be $175 per application for SFD and $175 for multi-family buildings.  
   *(Caption note: item 9 may lack a bold short heading style used for 6–8; exact emphasis unverified.)*

### Footnotes (caption)

- **¹** Or the total hourly cost to the jurisdiction, whichever is the greatest. This cost shall include supervision, overhead, equipment, hourly wages and fringe benefits of the employees involved.
- **²** Actual costs include administrative and overhead costs.

### City Sales Tax (caption)

- Header bar: **City Sales Tax**
- Body (majority of captions, including dedicated `sales_tax_body` / `electrical_and_date` crops):  
  Computed at **4.11%** of **45%** of the value of new residential construction, if said value is seventy-five thousand dollars ($75,000) or less per unit. For all other construction, the amount collected shall be **4.11%** of **50%** of the total value of construction.
- **Caption conflict (unresolved):** one crop (`crops/footer.png`) reported the “all other construction” rate as **1.11%** of 50%. Tighter re-crops reported **4.11%**. Retain both readings; do not assert a resolved glyph without Atlas pixel verification. Preferential reading for transcript continuity: **4.11%** (multi-crop majority), with **1.11%** flagged as possible caption misread pending Atlas.

### Temporary Electrical Inspection Fee (caption)

- Header bar: **Temporary Electrical Inspection Fee**
- Body: **$45.00** per inspection for all temporary electrical services on all single-family dwellings, multi-family dwellings, and commercial projects.

### Footer (caption)

- Bottom right, lighter/gray smaller type: **8/18/2026**
- Anomaly note: title year “2024” vs footer date “8/18/2026” — preserved; legal_currentness not_verified; no inference about adoption/effectiveness.

### Marks / handwriting

- Caption reports: entirely printed; **no handwriting** observed in available representations.
- No strike-through, insertions, or blank fillable fields reported in captions.
- Color: logo blue/gold-brown reported; body predominantly black on white; reversed white-on-black section bars.

---

## Unchecked / unrepresented / unresolved regions

1. Exact letterforms, Unicode code points, kerning, spaces, and punctuation micro-glyphs (especially item 6 terminal `.-`).
2. Logo graphic fine detail (caption variants: sun/mountain vs cowboy hat outline).
3. Any seals, stamps, watermarks, or margin text not described by captions.
4. Printed page number / form number / document control codes if present but uncaptioned (none reported).
5. Sales-tax percent digit conflict: **4.11%** vs **1.11%** (see above).
6. Item 9 heading/bold styling relative to items 6–8.
7. Regions outside each crop’s frame were not represented in that crop’s caption (mitigated by full-page + overlapping crops, but not by direct pixels).
8. `original.pdf` bytes not opened in this workdir (identity SHA only from SOURCE_ONLY_IDENTITIES).

---

## Limitations

- Caption-mediated assistance only; captions are not quotations of the source.
- Completeness of transcription is **not authenticated** by caption availability.
- Arithmetic correctness of fee tiers was **not** calculated or verified.
- Document is **not** certified current, adopted, or legally effective (`legal_currentness: not_verified`).
- Result remains **pending_atlas_direct_image_review**.

---

## Identity bindings (Pass 1)

| Object | SHA-256 |
|---|---|
| page-0001.png | 051102365c1fc699736227afacc4065c157e32ac6d7d8dd77b4becb9698d8210 |
| original.pdf (identity only; file absent in workdir) | fa8a90dae00525c2dcb62ef4d69aeb84b7032a0fd2dc64f45c1685981e9becd4 |
| frozen packet manifest (from SOURCE_ONLY_IDENTITIES; file not opened) | dcb4565ae9a3ce007f7a96e0fcc74cd6ebe8664b435cb1a278d8a75a2f152397 |
| ACTIVATION.md | fc9f78bbdc4a9d416ab946bb435de96957cc3d5a748d2063e912eea1d350e3de |
| SOURCE_ONLY_IDENTITIES.json | 29ea8ec18e6343e66bff79e6786eba26eb37dbdd09e7bed61fc4a5f26ea9afd5 |

expected_pages: 1  
inspected_pages (caption-mediated representations): 1  
utc_start: 2026-09-12T22:00:31Z  
