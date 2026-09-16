# PASS2_REVIEW — EB-PDF-014

- assignment_id: EB-PDF-014
- source_id: fort-collins-land-use-article-1-sd005-07
- reviewer: Ebenezer (Grok Bot) / executor Grok Bot
- pass: 2 (candidate vs images vs frozen Pass 1)
- legal_currentness: not_verified
- utc_pass2_start: 2026-09-11T19:30:42Z
- utc_pass2_end: 2026-09-11T19:34:57Z
- expected_pages: 7
- inspected_pages_pass2: 7
- pass1_pages_inspected: 7
- status: completed_pending_atlas_verification
- prior_candidate_exposure_at_pass1_freeze: none
- candidate_opened_pass2: yes (after SHA verify)
- custody_opened: false
- verification_opened: false
- eb013_materials_opened: false

## Integrity checks (Pass 2 start)

| asset | expected SHA-256 | observed | match |
|-------|------------------|----------|-------|
| candidate.txt | a31bfdec7d300e43690236b7fdacd9dd89c9f431fc48fe9077e9ae09c13a1105 | a31bfdec7d300e43690236b7fdacd9dd89c9f431fc48fe9077e9ae09c13a1105 | yes |
| PASS1_frozen.md | c4692567ad268a3f3a2a211c5851b8cc4d45ee2faf8d0a73feb837451eda9e8c | c4692567ad268a3f3a2a211c5851b8cc4d45ee2faf8d0a73feb837451eda9e8c | yes (untouched) |
| PASS1_FREEZE_RECEIPT.json | 17e379291fa92c054dbfea95e04c3e8495704279940303541c53bc7bfb6d5ecd | 17e379291fa92c054dbfea95e04c3e8495704279940303541c53bc7bfb6d5ecd | yes (untouched) |
| page-0001.png | 7ed3f49842c2039bb73f2776d3ad373a7955e6d0b36ebebd5ae4c2e23f141b2c | same | yes |
| page-0002.png | a3c3dbe905ac1901d482f474671c474f10d30ed8d33ee11219f332e4a2e5248e | same | yes |
| page-0003.png | 6c4696f83452f7eafd6f3f8c79a762f37f01bedd8c6e8ac6f6be61ec040a0ca3 | same | yes |
| page-0004.png | 812fc96f8f1a01e7301aaf6f7a725201e2fdfd666a8e0e62c89d65a224c234fc | same | yes |
| page-0005.png | 4c3e9b0d1e956212d3c025fb0c2936358b5f596d3f91c5c8045fdce38476fb3f | same | yes |
| page-0006.png | b84cd01abd9808f61997c651f2810de27df956ca46d09b391fa15bc9f5decbc9 | same | yes |
| page-0007.png | dadd797082f6f669395a1a230fac4a40fd324befe7f8a4d48f2afd2db4ea1288 | same | yes |
| packet_manifest (bound) | ee87ef2806e3cf9b955dbceca927087918ed0906894879a8597d7436ad67db0b | bound via Pass1 receipt / assignment (file not re-opened outside workdir) | bound |
| original.pdf (bound) | 555a05553af57619c818c5b9ab90d1b751e161a307d8bb65fc73141991a73d2a | not present under /workspace/geode-014/ at Pass2; SHA bound from assignment/Pass1 | bound_not_rehashed_locally |

Candidate nature (per Pass 2 prompt): machine_native_text_unreviewed, PyMuPDF 1.28.2 `Page.get_text("text", sort=False, flags=195)`. Physical-page markers are packaging, not source text.

## Method / disclosure

- Reinspected all 7 full-page PNGs via Read; re-read Pass1 crops; created additional Pass2 crops (page-1 bottom, page-3 top/bottom, page-4 transition bands).
- Compared candidate.txt to painted page pixels and to PASS1_frozen.md (frozen; not modified).
- **Caption-mediation disclosure:** Vision returns remain caption-mediated and non-authoritative. Conflicting caption claims were cross-checked with wider/alternate crops. Notable false caption: one page-4 body crop description alleged a centered `- 4 -` between the Article list and the first Division 1.1 paragraph; transition-band crops and candidate page-4 extract show **no** such mid-page marker (Pass1 correctly omitted it). Logo icon placement captions continue to conflict (beside vs beneath wordmark). Chat `image_description` blocks are not substitute quotations.
- No OCR; no network/source research; no 03-custody / 04-verification / EB-PDF-013 materials opened.
- legal_currentness: **not_verified** (printed titles/dates do not establish operative law).

## Coverage table (Pass 2)

| physical_page | file | printed_label (pixels) | pass2 inspection | both_passes |
|---------------|------|------------------------|------------------|-------------|
| 1 | page-0001.png | none (cover) | full + top/bottom crops | yes |
| 2 | page-0002.png | none (accessibility) | full + links crop | yes |
| 3 | page-0003.png | none (TOC) | full + TOC + top/bot crops | yes |
| 4 | page-0004.png | 1-1 | full + list/paras/transition bands | yes |
| 5 | page-0005.png | 1-2 | full + prior section crops | yes |
| 6 | page-0006.png | 1-3 | full + dash4/auth/purpose crops | yes |
| 7 | page-0007.png | 1-4 | full + 1.3.2/1.3.3 crops | yes |

## Discrepancy table (candidate vs source pixels)

Findings use IDs `EB014-P2-NNN`. Severity: **critical** = spurious or misleading page-attributed text / wrong operative labeling not supported by painted pixels; **minor** = order, omission of non-body chrome, formatting/spacing/Unicode packaging; **info** = source anomalies correctly preserved (not candidate errors).

| ID | source_sha256 (page) | phys | label | location | candidate wording | source-supported / notes | error_type | severity |
|----|----------------------|------|-------|----------|-------------------|--------------------------|------------|----------|
| EB014-P2-001 | 7ed3f498…141b2c | 1 | (none) | top-of-extract / footer region | `1-0 \| ARTICLE 1 \| CITY OF FORT COLLINS - LAND USE CODE` | No footer or `1-0` label visible on painted cover (bottom strip solid light blue) | spurious_ghost_text | critical |
| EB014-P2-002 | 7ed3f498…141b2c | 1 | (none) | main title block reading order | `General Purpose` / `and Provisions` then `ARTICLE 1` | Visual order: banner; logo; large `ARTICLE 1`; then `General Purpose` / `and Provisions` | reading_order | minor |
| EB014-P2-003 | 7ed3f498…141b2c | 1 | (none) | logo wordmark | (absent from candidate body) | Visible logo text `City of` / `Fort Collins` (+ stylized graphic) | omission_graphic_text | minor |
| EB014-P2-004 | a3c3dbe9…e5248e | 2 | (none) | logo | (absent) | Visible `City of` / `Fort Collins` logo at top | omission_graphic_text | minor |
| EB014-P2-005 | a3c3dbe9…e5248e | 2 | (none) | photograph | (no text; omitted) | Bottom-third color streetscape photo is graphical, not prose — expected native omission | omission_non_text | minor |
| EB014-P2-006 | a3c3dbe9…e5248e | 2 | (none) | hyperlink styling | plain email / phrase / URL strings | Email, “A Request for Reasonable Accommodation”, and URL appear blue+underlined; destinations beyond visible strings unknown | formatting_link_style | minor |
| EB014-P2-007 | 6c4696f8…40a0ca3 | 3 | (none) | top-of-extract | `1-1 \| ARTICLE 1 \| CITY OF FORT COLLINS - LAND USE CODE` and indented `ARTICLE 1 – GENERAL PURPOSE and PROVISIONS` | TOC page has neither running Article-1 banner nor `1-1` footer (top/bottom crops empty of those strings) | spurious_ghost_text | critical |
| EB014-P2-008 | 812fc96f…c234fc | 4 | 1-1 | extract order | Footer line appears before body headings | Footer `1-1 \| ARTICLE 1 \| …` is at bottom of painted page; native extract places it early | reading_order_footer | minor |
| EB014-P2-009 | 4c3e9b0d…476fb3f | 5 | 1-2 | extract order | Same early footer/`ARTICLE 1 – …` banner placement pattern | Banner top-left; footer bottom — visual order differs from native extract | reading_order_footer | minor |
| EB014-P2-010 | b84cd01a…5decbc9 | 6 | 1-3 | extract order | Same early footer/banner pattern | Same as pages 4–5/7 | reading_order_footer | minor |
| EB014-P2-011 | dadd7970…ea1288 | 7 | 1-4 | extract order | Same early footer/banner pattern | Same | reading_order_footer | minor |
| EB014-P2-012 | 4c3e9b0d…476fb3f | 5 | 1-2 | (C) *Our Climate Future* | Plain `Our Climate Future` (no italic marker) | Phrase appears italicized on painted page | formatting_italics_omitted | minor |
| EB014-P2-013 | multiple | 3–7 | — | before some `1.x.x` headings | U+202F narrow no-break spaces in candidate | Spacing glyph not claimed from pixels; native packaging | unicode_spacing_artifact | minor |
| EB014-P2-014 | 4c3e9b0d…476fb3f | 5 | 1-2 | 1.2.1 TITLE quotes | Mixed straight `"` and curly `“”` around titles/LUC/Code | Quotation glyph shapes approximate from pixels; Pass1 already flagged uncertainty | unicode_quotes_mixed | minor |
| EB014-P2-015 | 812fc96f…c234fc | 4 | 1-1 | (“LUC” or “Code”) | Curly quotes in candidate | Appears curly on page; agrees with Pass1 uncertainty resolution toward curly | agreement_typo_graphics | info |
| EB014-P2-016 | 6c4696f8…40a0ca3 / dadd7970…ea1288 | 3 / 7 | TOC / 1.3.2 | title | `…standards and Conflict with other laws` / `…AND CONFLICT WITH OTHER LAWS` | Source anomaly: repeated Conflict/CONFLICT — **preserved** in candidate and Pass1 | source_anomaly_preserved | info |
| EB014-P2-017 | dadd7970…ea1288 | 7 | 1-4 | 1.3.2(A) | `Articles 2, 3, or 4 a standard or requirement in Article 5` | Source anomaly: missing “and” — **preserved** | source_anomaly_preserved | info |
| EB014-P2-018 | dadd7970…ea1288 | 7 | 1-4 | 1.3.3 | `…of the City. it is the further intent…` | Source anomaly: lowercase `it` — **preserved** | source_anomaly_preserved | info |
| EB014-P2-019 | b84cd01a…5decbc9 | 6 | 1-3 | 1.2.4 Applicability | `interpretation - 4 - and application` | Source anomaly: embedded `- 4 -` — **preserved**; confirmed on dash crop | source_anomaly_preserved | info |
| EB014-P2-020 | b84cd01a…5decbc9 | 6 | 1-3 | 1.2.3 AUTHORITY | `Charter of The City of` + newline + `Fort Collins` | Capital `The` visible on Authority crop; candidate line-wraps but keeps `The` | agreement | info |
| EB014-P2-021 | 812fc96f…c234fc | 4 | 1-1 | between Article list and first para | (no `- 4 -` in candidate page 4) | No mid-page `- 4 -` on painted page 4 (false caption on one crop ignored) | caption_false_positive_rejected | info |

### Counts

- critical: **2** (EB014-P2-001, EB014-P2-007)
- minor: **12** (002–006, 008–014)
- info (incl. preserved anomalies / agreements): **7** (015–021)
- unresolved (see below): **5** themes (not double-counted as critical/minor)

## Errata vs Pass 1 (separate table; PASS1_frozen unchanged)

| erratum | Pass1 original | Pass2 revised interpretation | basis |
|---------|----------------|------------------------------|-------|
| E1 | Logo note: “[stylized graphic under logo]” | Revise to: stylized mountain/wave graphic is part of the City logo lockup; **exact** placement (beside vs beneath wordmark) remains **unresolved** under caption conflict — Pass1 already listed “exact logo geometry” unresolved; the “under” phrasing was over-specific | Pass2 logo crop captions conflict; do not treat “under” as settled |
| E2 | Medium confidence: capital `T` in “Charter of The City of Fort Collins” | Upgrade confidence to **confirmed** (wording unchanged) | Authority start crop clearly shows `The` |
| E3 | (implicit) no page-4 list/body `- 4 -` | Affirm Pass1 omission was correct; reject alien caption claiming centered `- 4 -` on page 4 between list and first paragraph | Transition-band crops; candidate page-4 lacks marker |

No Pass1 **operative wording** revisions required for Divisions 1.1–1.3 body text, purpose list (A)–(N), or preserved anomalies.

## Source anomalies (must preserve; not “fixes”)

1. TOC / §1.3.2 heading: repeated “Conflict” / “CONFLICT”.
2. §1.3.2(A): missing conjunction “and” between Articles 2/3/4 clause and Article 5 clause.
3. §1.3.3: second sentence begins with lowercase `it`.
4. §1.2.4: stray embedded `- 4 -` between “interpretation” and “and application” (page printed 1-3).
5. legal_currentness: not_verified.

## Unresolved regions

1. Exact Unicode codepoints for banner/footer dashes and many apostrophe/quotation glyphs (pixels vs candidate’s U+2013/U+2019/U+201C/U+201D mix).
2. Exact hyperlink destinations on page 2 beyond visible link text/URL.
3. Fine inventory of page-2 photograph (non-text).
4. Logo lockup geometry (icon beside vs beneath wordmark) under caption conflict.
5. Whether any invisible PDF text layer explains ghost `1-0` / TOC `1-1` extractions (pixels do not show them; layer not inspected beyond native candidate).

## Pass1 agreement summary (body)

Substantive Division 1.1 organization prose, 1.2.1–1.2.5, 1.3.1–1.3.3, purpose items (A)–(N), cross-refs `Sections 6.8.2 and 6.14.4`, `Section 6.2.2`, and Authority semicolon after “Colorado Constitution” align among painted pages, Pass1 frozen transcription, and candidate (modulo line breaks, early footer order, and packaging markers).

## Final status

- All **7** expected pages received full Pass 1 and full Pass 2 inspection.
- PASS1_frozen.md / PASS1_FREEZE_RECEIPT.json **not modified**.
- status: **completed_pending_atlas_verification**
- legal_currentness: **not_verified**

## End of PASS2_REVIEW
