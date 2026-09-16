# PASS2_REVIEW — EB-PDF-015

- assignment_id: EB-PDF-015
- source_id: greeley-building-fees-sd008-06
- authority_id: CO-MUNICIPAL-GREELEY
- reviewer: Ebenezer (Grok Bot) / executor Grok Bot
- pass: 2 (candidate vs caption-mediated source reading vs frozen Pass 1)
- legal_currentness: not_verified
- utc_pass2_start: 2026-09-12T22:03:10Z
- utc_pass2_end: 2026-09-12T22:06:30Z
- expected_pages: 1
- inspected_pages_pass2: 1
- pass1_pages_inspected: 1
- status: completed_pending_atlas_verification
- prior_candidate_exposure_at_pass1_freeze: none
- candidate_opened_pass2: yes (after SHA verify)
- custody_opened: false
- verification_opened: false
- materials_016_017_opened: false

## Integrity checks (Pass 2 start)

| asset | expected SHA-256 | observed | match |
|-------|------------------|----------|-------|
| candidate.txt | aec7efa7edbd9e26a8ce7bbd9685431c386043fc074567a1b3db334e9f528334 | aec7efa7edbd9e26a8ce7bbd9685431c386043fc074567a1b3db334e9f528334 | yes |
| PASS1_frozen.md | 7700629a1a32c57da2b620bf6d9ed388a219cdf79f22a1742b62c2e666870e7f | 7700629a1a32c57da2b620bf6d9ed388a219cdf79f22a1742b62c2e666870e7f | yes (untouched) |
| PASS1_FREEZE_RECEIPT.json | f171562156f15e3151c5ab6cabf9683429b57481e61d8dbb36fefca7a6f01526 | f171562156f15e3151c5ab6cabf9683429b57481e61d8dbb36fefca7a6f01526 | yes (untouched) |
| page-0001.png | 051102365c1fc699736227afacc4065c157e32ac6d7d8dd77b4becb9698d8210 | 051102365c1fc699736227afacc4065c157e32ac6d7d8dd77b4becb9698d8210 | yes |
| ACTIVATION.md | fc9f78bbdc4a9d416ab946bb435de96957cc3d5a748d2063e912eea1d350e3de | fc9f78bbdc4a9d416ab946bb435de96957cc3d5a748d2063e912eea1d350e3de | yes |
| SOURCE_ONLY_IDENTITIES.json | 29ea8ec18e6343e66bff79e6786eba26eb37dbdd09e7bed61fc4a5f26ea9afd5 | 29ea8ec18e6343e66bff79e6786eba26eb37dbdd09e7bed61fc4a5f26ea9afd5 | yes |
| packet_manifest (bound) | dcb4565ae9a3ce007f7a96e0fcc74cd6ebe8664b435cb1a278d8a75a2f152397 | bound via SOURCE_ONLY_IDENTITIES / Pass1 receipt (manifest file not opened) | bound |
| original.pdf (bound) | fa8a90dae00525c2dcb62ef4d69aeb84b7032a0fd2dc64f45c1685981e9becd4 | not present under /workspace/geode-015/; SHA bound from assignment/Pass1/SOURCE_ONLY | bound_not_rehashed_locally |

Candidate nature (per assignment): machine_native_text_unreviewed; PyMuPDF. Physical-page markers are packaging, not source text.

Pass1 freeze window (unchanged): utc_start 2026-09-12T22:00:31Z; utc_freeze 2026-09-12T22:02:26Z.

## Method / disclosure (required re-disclosure)

| Field | Value |
|---|---|
| review_method | caption_mediated_source_first |
| visual_verification | pending_atlas_direct_image_review |
| tool | Read (caption-mediated) on full page + Pass1 crops + new Pass2 crops |
| assistance | Captions are NOT source quotations; may omit, invent, or misread details. Unknown caption internals (possible OCR/model interpretation). Chat `image_description` blocks are not substitute quotations. |

**This is NOT direct pixel inspection and NOT blind visual transcription.** Work is ASSISTED and pending Atlas's actual image verification.

### Representations re-read (all caption-mediated)

1. Full page: `/workspace/geode-015/page-0001.png`
2. Pass1 Pillow crops re-Read:
   - `crops/header.png`, `crops/table.png`, `crops/table_bottom_rows.png`
   - `crops/other_fees.png`, `crops/footnotes_zone.png`
   - `crops/sales_tax_electrical.png`, `crops/sales_tax_body.png`
   - `crops/electrical_and_date.png`, `crops/footer.png`
3. New Pass2 crops (`crops_p2/`):
   - `sales_tax_full_band.png`, `sales_tax_rates_zoom.png`, `sales_tax_paragraph.png`
   - `item6_band_0.png` … `item6_band_3.png`, `item6_terminal.png`
   - `effective_bar.png`, `footer_date.png`

Compared: candidate.txt (after SHA verify) ↔ caption-mediated source reading ↔ PASS1_frozen.md (frozen; not modified).

No OCR substitute; no network/source research; no 03-custody / 04-verification; no EB-PDF-016/017 materials opened beyond identities already present in SOURCE_ONLY_IDENTITIES.json (016/017 page/PDF bytes not opened). `original.pdf` absent in workdir (pages-only OK).

## Coverage table (Pass 2)

| physical_page | file | printed_label (caption) | pass2 inspection | both_passes |
|---------------|------|-------------------------|------------------|-------------|
| 1 of 1 | page-0001.png | none reported (single-page schedule; no “Page N” label captioned) | full page + Pass1 crops + Pass2 crops (header/table/other-fees/sales-tax/item6/footer) | yes |

Declared assisted procedure covered page 1 in both passes → status eligible for `completed_pending_atlas_verification` while `visual_verification` remains `pending_atlas_direct_image_review`.

## Discrepancy table (candidate vs caption-mediated source)

Findings use IDs `EB015-P2-NNN`. Severity: **critical** = spurious/misleading page-attributed operative text not supported by source representation; **minor** = order, chrome omission, formatting/spacing/Unicode packaging; **info** = agreements / source anomalies correctly preserved / caption conflicts handled.

| ID | source_sha256 (page) | phys | location | candidate wording | source-supported / notes | error_type | severity |
|----|----------------------|------|----------|-------------------|--------------------------|------------|----------|
| EB015-P2-001 | 05110236…8d8210 | 1 | extract order (top of candidate) | `City Sales Tax` then `Temporary Electrical Inspection Fee` appear before title/`Total Job Valuation` | Captions place those black-bar titles visually below footnotes / near page bottom; bodies appear later in candidate without re-stating headers in visual order | reading_order | minor |
| EB015-P2-002 | 05110236…8d8210 | 1 | logo lockup | title `City of Greeley` present; logo-only `Colorado` / hat-mountain graphic text not extracted as lockup | Caption: logo includes “City of” / “Greeley” / “Colorado” + stylized hat/mountains | omission_graphic_text | minor |
| EB015-P2-003 | 05110236…8d8210 | 1 | packaging markers | `===== PHYSICAL PDF PAGE 1 OF 1 (PACKAGING MARKER) =====` … END marker | Packaging only; not printed source chrome | packaging_marker | minor |
| EB015-P2-004 | 05110236…8d8210 | 1 | items 1–5 fee cells | `$75.00 per hour1` / `Actual costs2` (baseline digits) | Captions show superscript ¹ / ² | formatting_superscript_flattened | minor |
| EB015-P2-005 | 05110236…8d8210 | 1 | item 6 terminal punctuation | ends `…in addition to the permit fees.` | Pass1 + `crops/other_fees.png` + `crops/footnotes_zone.png` caption majority: terminal sequence `fees.-` (period then hyphen). One Pass2 band caption truncated/`fee.` singular — retain conflict; **do not silently “fix” source**. Candidate lacks trailing hyphen present in majority captions | omission_source_anomaly_punctuation | minor |
| EB015-P2-006 | 05110236…8d8210 | 1 | Table 1-A / fee tiers 1–8 | All eight valuation bands and fee formulae (incl. $23.50, $3.05/$100, $14.00, $10.10, $7.00, $5.60, $4.75, $3.65 bases) | Caption-mediated table + bottom-row crops agree with candidate (modulo line wraps) | agreement | info |
| EB015-P2-007 | 05110236…8d8210 | 1 | Other Inspections items 1–9 + footnotes | Wording incl. Section 109.8, Section 106, 65 percent, $75 / $175 / SFD | Aligns with Pass1 transcript and crop captions (modulo EB015-P2-004/005) | agreement | info |
| EB015-P2-008 | 05110236…8d8210 | 1 | City Sales Tax rates | `4.11%` of 45% … and `4.11%` of 50% | **Pass2:** full page + `sales_tax_body` + `sales_tax_electrical` + `electrical_and_date` + `footer` + `sales_tax_full_band` all caption **4.11%** twice. Candidate matches. Pass1’s one-time `footer.png` **1.11%** reading **did not reproduce** on Pass2 re-Read of same crop — treat as non-reproducing caption false positive; still **pending Atlas** digit authentication | sales_tax_rate_agreement_vs_pass1_conflict | info |
| EB015-P2-009 | 05110236…8d8210 | 1 | Temporary Electrical + footer date | `$45.00 per inspection…`; `8/18/2026` | Captions agree; title year 2024 vs footer 8/18/2026 preserved (source anomaly; no effectiveness inference) | source_anomaly_date_vs_title_year | info |
| EB015-P2-010 | 05110236…8d8210 | 1 | Effective bar | `Building Fees Table 1-A (Effective -2024)` | Pass1 + `crops_p2/effective_bar.png` caption: hyphen immediately before 2024 (`-2024`); one alternate full-page caption once spaced `- 2024` — spacing micro-unresolved | agreement_with_spacing_uncertainty | info |

### Counts

- critical: **0**
- minor: **5** (EB015-P2-001 … 005)
- info (agreements / preserved anomalies / caption handling): **5** (006–010)
- unresolved themes (below; not double-counted as critical/minor): **6**

## Errata vs Pass 1 (separate table only; PASS1_frozen.md unchanged)

| erratum | Pass1 original | Pass2 revised interpretation | basis |
|---------|----------------|------------------------------|-------|
| E1 | Sales-tax caption conflict: majority **4.11%** vs one `crops/footer.png` reading **1.11%** on “all other construction”; preferential 4.11% with 1.11% flagged unresolved | Strengthen preferential reading to **4.11% / 4.11%** (both clauses). Pass2 re-Read of `footer.png` and all sales-tax crops report **4.11%** only; **1.11% did not reproduce**. Candidate also has **4.11%** twice. Still **not** Atlas-authenticated pixels — conflict closed as non-reproducing caption artifact for assisted review only | Pass2 multi-crop + candidate agreement; same-file footer re-Read |
| E2 | Item 6 terminal captioned `.-`; listed unresolved for Atlas | Affirm `fees.-` as majority captioned source anomaly; newly note **candidate omits trailing hyphen** (Pass1 had no candidate compare). One Pass2 item-6 band caption truncated / singular `fee.` — keep micro-glyph unresolved for Atlas | `other_fees` + `footnotes_zone` vs candidate line ending; band crop cut-off |
| E3 | Logo graphic variants (sun/mountain vs cowboy hat) unresolved | Pass2 `header.png` caption: mountains + blue cowboy-hat outline — still caption-mediated; exact lockup geometry/colors remain unresolved pending Atlas | header crop re-Read |

No Pass1 operative fee-tier or sales-tax **wording** revision required beyond E1 preferential strengthening. PASS1_frozen.md / PASS1_FREEZE_RECEIPT.json **not modified**.

## Source anomalies (must preserve; not “fixes”)

1. Item 6 terminal sequence captioned as period-hyphen `fees.-` (majority); do not normalize away.
2. Title year **2024** vs footer date **8/18/2026** — preserved; `legal_currentness: not_verified`.
3. `(Effective -2024)` hyphenation/spacing as printed — preserve; do not “correct” spacing.
4. Item 9 lacks short bold heading style used for items 6–8 (caption note; emphasis unverified).

## Unresolved regions

1. Exact painted glyphs for sales-tax percent digits — assisted captions unanimous at 4.11% in Pass2, but `visual_verification` still pending Atlas direct image review.
2. Exact item-6 terminal codepoints (`fees.-` vs truncated band caption).
3. Exact Unicode/kerning/spaces in Effective bar and throughout fee prose.
4. Logo fine detail (hat/mountain geometry, colors) beyond captions.
5. Any seals/stamps/watermarks/margin codes not described by captions.
6. Superscript geometry vs candidate baseline `1`/`2`; leader dots / micro-typography if any.

## Pass1 agreement summary (body)

Building Permit Fees Table 1-A eight tiers, Other Inspections items 1–9 prose (Section 109.8 / 106, 65 percent, $75/$175), footnotes ¹/² substance, City Sales Tax structure (45%/75,000 residential vs 50% other), Temporary Electrical $45.00, and footer date align among Pass1 frozen transcript, Pass2 caption re-Reads, and candidate (modulo reading order, packaging markers, flattened superscripts, and item-6 trailing hyphen omission).

## Final status

- Expected page **1 of 1** received full Pass 1 and full Pass 2 assisted inspection.
- PASS1_frozen.md / PASS1_FREEZE_RECEIPT.json **not modified**; re-hash confirmed.
- review_method: **caption_mediated_source_first**
- visual_verification: **pending_atlas_direct_image_review**
- status: **completed_pending_atlas_verification**
- legal_currentness: **not_verified**

## End of PASS2_REVIEW
