# PASS2_REVIEW — EB-PDF-016

- assignment_id: EB-PDF-016
- source_id: greeley-development-impact-fee-memo-sd008-07
- authority_id (collection context only): CO-MUNICIPAL-GREELEY
- reviewer: Ebenezer (Grok Bot) / executor Grok Bot
- pass: 2
- review_method: caption_mediated_source_first
- visual_verification: pending_atlas_direct_image_review
- legal_currentness: not_verified
- prior_candidate_exposure (Pass1): none
- Pass2 candidate exposure: after independent SHA-256 verify of candidate.txt against expected hash; opened only for Pass2 comparison
- utc_start: 2026-09-12T22:11:39Z
- utc_candidate_release: 2026-09-12T22:11:55Z
- utc_completion: 2026-09-12T22:14:46Z
- expected_pages: 3
- inspected_pages Pass2 (assisted): 3
- inspected_pages Pass1 (assisted, frozen): 3
- assistance_supplier/tool: Cursor Read tool (caption-mediated image descriptions) on full-page PNGs and existing Pillow crops under crops/; assistance model/supplier internals unknown
- assistance_disclosure: Read does not expose raw pixels to the reviewer; each page/crop return is a caption/mediated description that may include OCR or model interpretation and can share errors with the candidate. Chat activation also supplied prior image_description blocks for the same three PNGs (treated as non-authoritative captions). No direct pixel inspection; no blind visual transcription; no native PDF text extraction / OCR as Pass2 substitute. Pass1 freeze not modified.
- sealed_not_opened: 03-custody; 04-verification; full packet manifest.json; PREPARATION_RECEIPT; validator; prior Atlas/Sherlock/Ebenezer analyses for this source; EB-PDF-015 and EB-PDF-017 materials beyond activation cross-refs already in workdir instructions

## Bound identities (independently re-hashed this pass)

| artifact | sha256 | bytes |
|----------|--------|------:|
| PASS1_frozen.md | fda6410d73cf0f2cf88a14ccd3d52af4f9c5deda6e7103f6c8ebe63bf5d9b6a2 | 16127 |
| PASS1_FREEZE_RECEIPT.json | dfd03e2cd7162931cbb0f96f5e28b9c1cd7a8f0213bd3168e2ced656884004a3 | 3841 |
| candidate.txt | 1c45252c6c814258f5a2e8380001f282a609ad9db81ec3947655b871346296f9 | 7530 |
| original.pdf | 9effbd15196898c16105913ee21032db52ad1e259f4f9def0586804726f78709 | 651009 |
| page-0001.png | 897dddf6df53617e3a20a252adf1a70151dcc11722cda9719227e20bd894e17c | 567833 |
| page-0002.png | aac84312750eeafac8e707fda7f9d4f215be0dcbcb11c1b1b086c355ad350d2e | 536314 |
| page-0003.png | 98513c20960e97d94bae033957e0b75b95e32572b0eb74ce6a136103b3e8cb60 | 157212 |
| ACTIVATION.md | fc9f78bbdc4a9d416ab946bb435de96957cc3d5a748d2063e912eea1d350e3de | 13367 |
| SOURCE_ONLY_IDENTITIES.json | 29ea8ec18e6343e66bff79e6786eba26eb37dbdd09e7bed61fc4a5f26ea9afd5 | 4396 |
| packet_manifest (assignment-supplied; file not opened) | dcb4565ae9a3ce007f7a96e0fcc74cd6ebe8664b435cb1a278d8a75a2f152397 | n/a |

PASS1 re-hash confirmation: PASS1_frozen.md and PASS1_FREEZE_RECEIPT.json match freeze-time SHAs exactly (unchanged). candidate.txt matches expected native-unreviewed SHA. Page PNGs and original.pdf match Pass1 / assignment identities.

Candidate status note: machine_native_text_unreviewed (PyMuPDF 1.28.2 Page.get_text text/sort=False/flags=195 per activation). Physical-page markers are packaging, not source text.

---

## Coverage table (Pass2)

| physical_page | file | printed_page_label | representation | method | unchecked / unresolved |
|---------------|------|--------------------|----------------|--------|-------------------------|
| 1 | page-0001.png | none; running title "2026 Development Impact Fee Schedule" TR | full-page Read + header/table/body crops | caption_mediated_source_first | Logo fine vectors; en-dash vs hyphen in "EAF – Weighting…"; bullet dash Unicode; table layout transpose in some captions |
| 2 | page-0002.png | none; same running title | full-page Read + intro/police/police_comm/police_fire/fire/park/storm/hdr crops | caption_mediated_source_first | **Police Retail/Restaurant fee triple+ caption conflict (A1 expanded)**; Unit blank vs merge geometry; Sq. Ft period; intro Fee/Fees wording variant in one crop |
| 3 | page-0003.png | none; same running title | full-page Read + table/rows/title/lower-blank crops | caption_mediated_source_first | Numeric column headers omitted on page; Unit spelling Square Feet vs page-2 Sq. Ft; large blank lower region |

Assisted procedure covered all 3 expected physical pages in Pass1 and Pass2.

---

## Pass1 comparison summary

- Pass1 freeze left intact; no edits to PASS1_frozen.md / PASS1_FREEZE_RECEIPT.json.
- Stable fee rows (Police residential; Fire; Park; Trails; Storm; Transportation) re-agree with Pass1 majority readings and with candidate amounts.
- EAF weights/% changes / final **-2.07%** re-agree (weighted check ≈ -2.066 → printed -2.07; arithmetic not asserted as legal truth).
- Anomaly A1 (Police Retail/Restaurant) **preserved and expanded**: majority/full-context still $1,004 | -2.09% | $983 (matches candidate); edge-cut crops continue to invent alternate triples (Pass1 alts plus new Pass2 alts). Not certified.
- Pass1 errata: none required (see separate table). Working readings retained; A1 alternative inventory only expanded.

---

## Discrepancy / findings table

Findings ID scheme: EB016-P2-NNN. Materiality: critical = wrong/untrusted fee or identity that could misstate amounts; minor = packaging/linearization/typography without changing associated amounts; unresolved = caption conflict or glyph-level uncertainty pending Atlas.

### EB016-P2-001 — Police Development Fee Retail/Restaurant amount triple (CRITICAL / UNRESOLVED)

- assignment/source: EB-PDF-016 / greeley-development-impact-fee-memo-sd008-07
- physical_page: 2 (page-0002.png SHA aac84312750eeafac8e707fda7f9d4f215be0dcbcb11c1b1b086c355ad350d2e)
- printed_label: none (running title only)
- region: Police Development Fee → Retail/Restaurant row → 2025 Fee / % Change / 2026 Fee
- exact candidate wording: `Retail/Restaurant` / `1,000 Sq. Ft of Building` / `$1,004` / `-2.09%` / `$983`
- source-supported wording / alternatives (caption-mediated; NOT pixel-certified):
  - Majority / full-page / wider police+fire crops (Pass1 + Pass2): **$1,004 | -2.09% | $983**
  - Pass1 conflicting crop alts (preserved): $1,381 | -2.32% | $1,349 ; $1,001 | -0.90% | $992
  - Pass2 new conflicting crop alts (edge-cut Retail row): p2_police.png → $1,034 | -3.38% | $999 ; p2_police_comm.png → $1,021 | -2.06% | $999
- error_category: caption_instability / unresolved_glyph_association (not a confirmed candidate wording error; candidate matches majority only)
- materiality/severity: **critical** (fee dollars) + **unresolved**
- visual explanation: When Retail/Restaurant sits at the bottom edge of a tight crop, mediated captions invent inconsistent fee triples; wider context captions and the candidate converge on $1,004/-2.09%/$983. Atlas direct image review required before any certified reading. Anomaly preserved; do not collapse alternatives.
- Pass1 link: Anomaly A1 — expanded, not overturned.

### EB016-P2-002 — Candidate page-1 leading "-A" artifact (MINOR)

- physical_page: 1
- region: above / adjacent to running title in native extract stream
- candidate: line begins `-A` then `2026 Development Impact Fee Schedule`
- source-supported: captions report running title only; no "-A" on face of memo
- error_category: extraction/packaging artifact
- materiality: minor (not a printed schedule amount)
- note: distinguish from source text; packaging markers elsewhere also not source.

### EB016-P2-003 — EAF table native linearization vs visual grid (MINOR / HARMLESS LINEARIZATION)

- physical_page: 1
- region: table "2026 EAF – Weighting and Percent Change by Indicator"
- candidate: emits Weight label, then multi-line indicator names (Greeley Utility Customers … Employment), then weight values, then "Economic Adjustment Factor" text block, then "% change" and the seven percent values including **-2.07%**
- source-supported (crop-preferred Pass1/Pass2): indicators as **column headers**; two data rows **Weight** and **% change**; EAF column empty on Weight row; **-2.07%** on % change row (bold tool-reported)
- Some captions still transpose to Indicator|Weight|% Change columns — same instability as Pass1; values agree either way.
- error_category: harmless_linearization / caption_layout_ambiguity
- materiality: minor (amounts associate correctly once layout understood)

### EB016-P2-004 — Bullet glyph private-use character (MINOR)

- physical_page: 1
- region: six EAF variable bullets
- candidate: leading `` (private-use / symbol font bullet)
- source-supported: captions describe ordinary bullets; exact Unicode not certified
- error_category: typography/Unicode substitution in native extract
- materiality: minor

### EB016-P2-005 — Page-2 schedule header wrap linearization (MINOR)

- physical_page: 2
- region: column headers
- candidate order fragment: `Fee Structure` / `2025` / `%` / `2026` / `Fee` / `Change` / `Fee` then section `Police Development Fee` / `Unit`
- source-supported: headers Fee Structure | Unit | 2025 Fee | % Change | 2026 Fee (Unit under Fee Structure span per captions)
- error_category: harmless_linearization
- materiality: minor

### EB016-P2-006 — Page-3 Transportation Industrial reading-order placement (MINOR)

- physical_page: 3 (page-0003.png SHA 98513c20960e97d94bae033957e0b75b95e32572b0eb74ce6a136103b3e8cb60)
- region: Transportation table rows
- candidate: lists four Residential labels, Retail/Restaurant + unit, Office & Other Services + unit, then six 2025 fees, six % changes, six 2026 fees, **then** Industrial + unit + its triple
- source-supported: Industrial is the last data row in visual order with same columns; amounts $3,273 | -2.08% | $3,205 agree
- error_category: harmless_linearization
- materiality: minor

### EB016-P2-007 — Candidate packaging whitespace and page markers (MINOR)

- pages: 1–3
- candidate: large runs of blank lines; `===== PHYSICAL PDF PAGE N OF 3 (PACKAGING MARKER) =====` fences
- source-supported: not printed on pages
- error_category: packaging (activation-disclosed)
- materiality: minor

### EB016-P2-008 — Page-3 numeric column headers omitted (UNRESOLVED / SOURCE FEATURE)

- physical_page: 3
- region: table header row
- candidate: prints `Transportation Development Fee` and `Unit` only; no `2025 Fee` / `% Change` / `2026 Fee` labels on this page
- source-supported: captions agree headers for numeric columns are absent (continuation from page 2)
- error_category: source_layout_continuation (candidate faithful to omission)
- materiality: unresolved association for readers of page 3 alone; amounts match page-2 column semantics by parallel structure
- not a candidate error

### EB016-P2-009 — Residential Unit column blank vs merged-cell geometry (UNRESOLVED)

- pages: 2–3
- candidate: no Unit tokens on residential rows (description carries sq ft language)
- source captions: Unit cells empty / blank for residential; Pass2 one full-page caption wrongly restated Unit as "Heated living space" (caption error — reject)
- error_category: geometry/glyph uncertainty
- materiality: unresolved (non-amount); candidate association OK

### EB016-P2-010 — Unit spelling page-2 "Sq. Ft" vs page-3 "Square Feet"; period after Ft (UNRESOLVED)

- pages: 2–3
- candidate page 2: `1,000 Sq. Ft of Building` (no period after Ft); page 3: `1,000 Square Feet of Building`
- source captions: same page-2 abbrev vs page-3 spelled-out pattern; period after "Ft" inconsistent across captions
- error_category: unresolved_glyph / possible faithful page difference
- materiality: minor/unresolved (not fee amounts)

### EB016-P2-011 — Intro sentence "Fee" singular / crop wording variant (UNRESOLVED)

- physical_page: 2
- region: third intro paragraph
- candidate: `The fee changes by type of Development Impact Fee are presented on the attached schedule.`
- Pass1 crop-preferred: singular "Fee" (matches candidate)
- Pass2 crop p2_hdr_cols (cut-off): captioned alternate `The fee adjustments of Development Impact Fees…` (incomplete)
- error_category: caption_instability on non-amount prose
- materiality: unresolved (prose); candidate retained as working reading matching Pass1

### EB016-P2-012 — Dash/hyphen Unicode in bullets and EAF title; "year end" hyphenation (UNRESOLVED)

- physical_page: 1
- candidate / captions: en-dash-like separators in bullets and title; "year end" without hyphen in candidate and Pass1
- error_category: unresolved_glyph
- materiality: minor/unresolved

### EB016-P2-013 — legal_currentness not verified (UNRESOLVED / STANDING)

- Title, November 1, 2025 date, March 1, 2026 effective-date language, and successful extraction do **not** prove adoption, effect, completeness, applicability, or current force.
- legal_currentness: **not_verified**

### Stable associations (no finding) — candidate ↔ Pass1 majority ↔ Pass2 re-read

Police residential; Fire all rows; Park; Trails; Storm Impervious Area `$0.315` / `-2.22%` / `$0.308` Unit `Per Impervious Square Foot`; Transportation all rows including Retail/Restaurant `$9,963` / `-2.07%` / `$9,757`; memo DATE/FROM/RE; EAF indicator weights and % changes as listed in Pass1.

---

## Pass1 errata table (separate; freeze unchanged)

| item | Pass1 frozen reading | Pass2 disposition |
|------|----------------------|-------------------|
| (none) | — | No Pass1 wording corrections. Anomaly A1 alternative inventory expanded in EB016-P2-001 only; primary working reading $1,004/-2.09%/$983 retained pending Atlas. |

---

## Unchecked / unresolved summary (Pass2)

1. All glyph-level / Unicode / typography claims — caption-mediated only; visual_verification pending Atlas.
2. **Police Retail/Restaurant fee triple** — EB016-P2-001 (critical unresolved).
3. Unit-column blank vs merged-cell geometry.
4. Dash characters in bullets and EAF title; "year end" hyphenation.
5. Page-3 numeric headers omitted (source feature; association inferred).
6. Sq. Ft period; Square Feet vs Sq. Ft across pages.
7. Intro Fee/Fees / "fee changes" vs crop "fee adjustments" caption variant.
8. Logo fine detail; any micro-footer beyond horizontal rules.
9. legal_currentness: not_verified.

## Counts

- critical: 1 (EB016-P2-001)
- minor: 6 (EB016-P2-002 … 007)
- unresolved (non-critical standing/glyph/layout): 6 (EB016-P2-008 … 013)
- Pass1 errata rows: 0

## Printed identity (brief)

City of Greeley Finance Department memorandum dated November 1, 2025, RE: 2026 Development Impact Fees; EAF **-2.07%** (year-end 2024 vs 2023); schedule decreases Police/Fire/Park/Trails/Storm Drainage/Transportation fees averaging -2.07%; public notice ~120 days before March 1, 2026 effective date; Water/Sewer PIF separate (December adoption). legal_currentness: not_verified.

## Status

`completed_pending_atlas_verification` — declared caption-mediated assisted procedure covered all 3 expected physical pages in both Pass1 and Pass2; not a claim of certified visual transcription, glyph verification, or legal currency. `review_method: caption_mediated_source_first`; `visual_verification: pending_atlas_direct_image_review`.
