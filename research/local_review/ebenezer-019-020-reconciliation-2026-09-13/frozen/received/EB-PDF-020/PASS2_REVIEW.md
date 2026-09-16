# PASS2_REVIEW — EB-PDF-020

- assignment_id: EB-PDF-020
- source_id: weld-ehs-fees-2026-atlas-directed
- authority_id (collection context only): CO-COUNTY-WELD
- reviewer: Ebenezer (Grok Bot) / executor Grok Bot
- pass: 2 (candidate vs caption-mediated page representations vs frozen Pass 1)
- review_method: caption_mediated_source_first
- visual_verification: pending_atlas_direct_image_review
- legal_currentness: not_verified
- utc_pass2_start: 2026-09-13T01:35:56Z
- utc_candidate_release: 2026-09-13T01:36:13Z
- utc_pass2_end: 2026-09-13T01:38:59Z
- expected_pages: 3
- inspected_pages_pass2: 3
- pass1_pages_inspected: 3
- status: completed_pending_atlas_verification
- prior_candidate_exposure_at_pass1_freeze: none (candidate sealed through freeze)
- candidate_opened_pass2: yes (after SHA verify; post-freeze only)
- custody_opened: false
- verification_opened: false
- materials_018_019_opened: false
- full_packet_manifest_opened: false
- last_authorized_document: true (stop after EB-PDF-020; no 021)
- hard_stop_utc: 2026-09-13T03:55:00Z

## Integrity checks (Pass 2 start)

| asset | expected SHA-256 | observed | match |
|-------|------------------|----------|-------|
| candidate.txt | e54c8a008fe12cdb6704851c1009afab1c5d9186d6aff90c5fcc63e85b36f67a | e54c8a008fe12cdb6704851c1009afab1c5d9186d6aff90c5fcc63e85b36f67a | yes |
| PASS1_frozen.md | 8bf0b21f79a4bd0ffca3c98daf83f6c1989b3e7508d8f03269693aa2e75bc527 | 8bf0b21f79a4bd0ffca3c98daf83f6c1989b3e7508d8f03269693aa2e75bc527 | yes (untouched) |
| PASS1_FREEZE_RECEIPT.json | 0defcfc6322c3c28dfe37c4aa740569c09f37074cff6ec6cd9219622902b5808 | 0defcfc6322c3c28dfe37c4aa740569c09f37074cff6ec6cd9219622902b5808 | yes (untouched) |
| PASS1_NOTES.md | 7822ca5ef3ece601a590cc08d0838319fe4ae7b6e6e16c7b2a1f8ad91f8eb57b | 7822ca5ef3ece601a590cc08d0838319fe4ae7b6e6e16c7b2a1f8ad91f8eb57b | yes (untouched) |
| page-0001.png | 0838c4594f3de2ff3afa1469dd12272df506aa33103b610f4fab5b45fb71d7f7 | 0838c4594f3de2ff3afa1469dd12272df506aa33103b610f4fab5b45fb71d7f7 | yes |
| page-0002.png | a32edee282c120754aeaca4d5fc5273c83bd14e428ed6b99628931802d31ca8c | a32edee282c120754aeaca4d5fc5273c83bd14e428ed6b99628931802d31ca8c | yes |
| page-0003.png | fb6ddbe0e95bb64a4088fd3daebb41c6dd63136d3ce06aa3ff3fa9121e5403fa | fb6ddbe0e95bb64a4088fd3daebb41c6dd63136d3ce06aa3ff3fa9121e5403fa | yes |
| START_HERE.md | 35f5dbb4104c1cea73084fa3939228c91a7caf1339540a4033e431849122924f | 35f5dbb4104c1cea73084fa3939228c91a7caf1339540a4033e431849122924f | yes |
| SOURCE_ONLY_IDENTITIES.json | 3242cf6cc99cead3c78cf0adf76aad7eb91aae153ed19ee2005f97a13caf81f7 | 3242cf6cc99cead3c78cf0adf76aad7eb91aae153ed19ee2005f97a13caf81f7 | yes |
| packet_manifest (bound) | b9e843e783a65a238d1a7e1106a5d0a49ea08f7ffbb59b9ca02d841e7639a112 | bound via MANIFEST_SHA256.txt content + Pass1 / identities (full custody-bearing packet not opened) | bound |
| original.pdf (bound) | 852801c5ad0056c7b0dde6300e66e86f2e4235ce0efc16471d5210d74aa17ed3 | not present under /workspace/geode-020/; SHA from identities/Pass1/assignment only | bound_not_rehashed_locally |

Candidate nature (per START_HERE): `machine_native_text_unreviewed`, PyMuPDF 1.28.2 `Page.get_text("text", sort=False, flags=195)`. Native bytes/order/Unicode/line breaks preserved. Physical-page markers are **packaging**, not source text. Candidate not presumed correct. Preparation hash/extraction checks are not an accuracy verdict.

## Method / disclosure

- Reinspected all three full-page PNGs via Cursor Read (caption-mediated). Created Pass 2 section and line crops under `/workspace/geode-020/crops/` and re-read those crops. Compared `candidate.txt` to caption-reported source representations and to `PASS1_frozen.md` (frozen; not modified).
- **Caption-mediation disclosure:** ASSISTED. (1) Activating user message included pre-supplied `image_description` blocks for all three pages (also disclosed at Pass 1; this pass is NOT labeled blind). (2) Every Read of a PNG returned a mediated caption, not raw pixels to the reviewer. Full-page captions smash words together; section/line crops were used to re-check disputed spellings and fee associations. Captions may contain OCR/model interpretation and may share errors with the candidate. Never labeled direct pixel inspection or blind visual transcription.
- Assistance supplier/model: unknown (Read image_description pipeline). Tool outputs preserved in `tool_outputs/` and `crops/`.
- No OCR-as-substitute; no native PDF text extraction; no network/source research; no 03-custody / 04-verification / full data manifest / PREPARATION / prior reviews / EB-PDF-018/019 materials opened.
- legal_currentness: **not_verified** — printed title year 2026 and fee figures are printed claims only; not evidence of adoption, effect, completeness, or currentness.

## Coverage table (Pass 2)

| physical_page | file | printed_label (tool-reported) | pass2 inspection | both_passes |
|---------------|------|-------------------------------|------------------|-------------|
| 1 | page-0001.png | 1 (centered footer) | full-page Read + section crops (header, body art, child care, food a/b/c, institution) + line crops (coordinator app, coordinator fee, unit inspection) + footer crop | yes |
| 2 | page-0002.png | 2 (centered footer) | full-page Read + section crops (header, misc, OWTS a/b, meth, bacteriological) + line crops (file review, contractor Weld, contractor other, cleaners) + footer crop | yes |
| 3 | page-0003.png | 3 (centered footer) | full-page Read + section crops (header, chem a/b/c, metals note, misc lab, oil/gas, NOTE) + line crops (phenolphthalein, Atimony, Cholrite, mosquitoe, Gasses) + footer crop | yes |

Assisted procedure covered all three expected physical pages in both passes → status `completed_pending_atlas_verification` (does **not** mean glyphs/regions were pixel-verified).

## Discrepancy table (candidate vs source representation)

Findings use IDs `EB020-P2-NNN`. Severity: **critical** = wrong operative fee/amount/basis, missing/extra fee line, or wrong service↔fee association; **minor** = candidate wording/truncation that does not change the fee amount or row association, reading-order/linearization, whitespace/formatting packaging; **info** = agreements, preserved source anomalies, packaging markers.

| ID | source_sha256 (page) | phys | label | location | candidate wording | source-supported / notes | error_type | severity |
|----|----------------------|------|-------|----------|-------------------|--------------------------|------------|----------|
| EB020-P2-001 | 0838c459…d7f7 | 1 | 1 | FOOD PROTECTION / Special Event Coordinator Application | `Special/Temproary Event Coordinator Application Fee` / `$150.00` | Pass 1 + food_b crop + line crop `p1_line_coordinator_app.png` report `Special/Temporary Event Coordinator Application Fee` / `$150.00`. Candidate misspells Temporary as Temproary. Fee amount agrees. | candidate_wording_mismatch | minor |
| EB020-P2-002 | 0838c459…d7f7 | 1 | 1 | FOOD PROTECTION / Coordinator hourly line | `Special/Temporary Event Coordinator Fee (plan review time and additional miscellaneous time, if applicab` / `$100.00/hour` | Pass 1 + food_b + line crop report `… if applicable` (full word; closing parenthesis not pixel-confirmed). Candidate truncates `applicable` to `applicab` and lacks a closing `)`. Fee/basis `$100.00/hour` agrees. | candidate_truncation | minor |
| EB020-P2-003 | 0838c459…d7f7 | 1 | 1 | INSTITUTION SERVICES / unit inspection | `Secure Transportion Services Unit Inspection Fee` / `$100.00/hour` | Pass 1 + institution crop + line crop `p1_line_transportion.png` report `Secure Transportation Services Unit Inspection Fee` / `$100.00/hour`. Candidate drops the `a` in Transportation. Neighboring lines keep `Transportation`. Fee agrees. | candidate_wording_mismatch | minor |
| EB020-P2-004 | fb6ddbe0…03fa | 3 | 3 | WATER QUALITY - CHEMICAL / second analyte | `Alkalinity, Phenophthalein (hydroxide, carbonate, bicarbonate)` / `$18.00` | Pass 1 + chem_a crop + line crop `p3_line_phenolphthalein.png` report `Alkalinity, Phenolphthalein (hydroxide, carbonate, bicarbonate)` / `$18.00`. Candidate omits the `l` after `o`. Fee agrees. | candidate_wording_mismatch | minor |
| EB020-P2-005 | 0838c459…d7f7 | 1 | 1 | header placement | Header `WELD COUNTY DEPARTMENT OF PUBLIC HEALTH AND ENVIRONMENT` / `ENVIRONMENTAL HEALTH SERVICES - 2026 FEE SCHEDULE` appears after Institution Services, before printed `1` | Source captions place the same two header lines at the top of page 1 (and pages 2–3). Native extract reading-order; wording of the header itself agrees. | reading_order_linearization | minor |
| EB020-P2-006 | 0838c459…d7f7 / a32edee2…ca8c | 1–2 | 1 / 2 | child-care ranges; OWTS labels | `Facility Inspection Fee  5-20 Children` (two spaces); `OWTS  Permit` / `OWTS  Repair/Alteration Permit` / `Commercial OWTS  New Permit` (two spaces after OWTS) | Captions do not support a semantic extra word. Treated as native-extract whitespace packaging, not a printed extra token. | whitespace_packaging | minor |
| EB020-P2-007 | a32edee2…ca8c / fb6ddbe0…03fa | 2–3 | 2 / 3 | meth note wrap; Additional Metals wrap; NOTE spacing | Meth parenthetical on its own indented line; Additional Metals wraps after `Molybdenum,`; `NOTE:` followed by two spaces in candidate | Source crops show the same words as continuation/wrap. Line-break/indent/double-space are extract linearization, not different wording. | extract_line_split_spacing | minor |
| EB020-P2-008 | all three | 1–3 | 1–3 | section-head underlines, leader dots, bold | Plain text only | Captions report underlined/bold uppercase section heads and right-aligned fee column. Native extract omits underline/leader/alignment metrics. | formatting_chrome_omitted | minor |
| EB020-P2-009 | all three | 1–3 | — | extract wrappers | `===== PHYSICAL PDF PAGE N OF 3 (PACKAGING MARKER) =====` | Packaging only; **not** source-transcription errors | packaging_marker | info |
| EB020-P2-010 | all three | 1–3 | 1–3 | every fee amount / basis checked | See candidate amounts | All caption-reported dollar amounts, hourly bases, `/pp`, `/company`, `3 x Stated Fee`, `Market Rate`, and not-to-exceed caps ($895 / $775 / $620) agree with Pass 1 and section crops. No fee-association error found. | agreement_fee_amounts | info |
| EB020-P2-011 | fb6ddbe0…03fa | 3 | 3 | Additional Metals list | `Additional Metals: Aluminum, Atimony, Barium, Beryllium, Cadmium, Cobalt, Potassium, Molybdenum,` / `Nickel, Silver` / `$23.00` | Line crop + chem_c/d captions report **Atimony** (not Antimony). Candidate matches source-supported spelling. Pass 1 had Antimony\|Atimony unresolved. | source_anomaly_candidate_matches | info |
| EB020-P2-012 | fb6ddbe0…03fa | 3 | 3 | market-rate examples | `but are not limited to:  Cholrite, Sulfide and Pseudomonas Aeruginosa.` | Line crop + chem_d captions report **Cholrite** (not Chlorite). Candidate matches. Pass 1 had Chlorite\|Cholrite unresolved. | source_anomaly_candidate_matches | info |
| EB020-P2-013 | fb6ddbe0…03fa | 3 | 3 | zoonotic line | `Zoonotic Testing (rabies, tularemia, plague, WNV mosquitoe pool, etc.)` / `Market Rate` | Line crop + misc-lab crop report **mosquitoe** (extra e). Candidate matches. Pass 1 flagged as possible caption error. | source_anomaly_candidate_matches | info |
| EB020-P2-014 | fb6ddbe0…03fa | 3 | 3 | oil & gas first analyte | `Dissolved Gasses (methane, ethane, propane)` / `$89.00` | Line crop + oil/gas crop report **Gasses** (double s). Candidate matches. Pass 1 flagged as unresolved. | source_anomaly_candidate_matches | info |
| EB020-P2-015 | a32edee2…ca8c | 2 | 2 | File Review Fees | `File Review Fees Per Appendix 5-D, Chapter 5, of the Weld County Code` (no fee token on following line) | Misc crop + line crop `p2_line_filereview.png`: same wording; no numeric fee in the fee column. Code-only reference confirmed. | agreement_code_only_fee | info |
| EB020-P2-016 | a32edee2…ca8c | 2 | 2 | OWTS cleaner licenses | `Systems Cleaners License` / `$75.00`; `Renewal of System Cleaners License (Annually)` / `$50.00` | OWTS-b crop: plural `Systems` on the base license; singular `System` on the renewal. Candidate matches; do not normalize. | source_anomaly_candidate_matches | info |
| EB020-P2-017 | a32edee2…ca8c | 2 | 2 | Systems Contractor lines | `Systems Contractor License- test taken in Weld` / `$100.00`; `Systems Contractor License- Test taken in another location` / `$75.00` | Line crops: hyphen with no space after `License`; second line capital `Test`. Candidate matches crops. Pass 1 had spaced hyphen and lowercase `test` on the second line. | agreement_hyphen_capitalization | info |
| EB020-P2-018 | 0838c459…d7f7 / fb6ddbe0…03fa | 1 / 3 | 1 / 3 | two autoclave lines | p.1 `Autoclave Sterilization Spore Test (Steam)` / `$13.00`; p.3 `Autoclave Spore Test` / `$14.00` | Both lines present in source captions. Distinct labels and amounts; no reconciliation performed. | agreement_distinct_autoclave_lines | info |
| EB020-P2-019 | all three | 1–3 | — | document status | (n/a) | Title `2026 FEE SCHEDULE` and printed amounts ≠ verified adopted/effective/current law | legal_currentness_not_verified | info |
| EB020-P2-020 | fb6ddbe0…03fa | 3 | 3 | pH line | `PH/Temperature` / `$18.00` | Chem_b crop same capitalization `PH/Temperature` (not asserted as `pH`). Candidate matches Pass 1. | agreement_preserved_capitalization | info |
| EB020-P2-021 | a32edee2…ca8c | 2 | 2 | Fax Fee | `Fax Fee (up to 10 pages, $.50 per each additional page)` / `$5.00+` | Misc crop agrees, including `$5.00+` and `$.50`. | agreement_fax_fee | info |
| EB020-P2-022 | a32edee2…ca8c | 2 | 2 | meth permit | `Methamphetamine Lab Decontamination Permit - Covers up to 4 hours of staff time.` / `$400.00` plus continuation `(Review and inspection activities in excess of 4 hours will be billed at an hourly rate.)`; hourly `$100.00/hour` | Meth crop agrees on wording, 4-hour cover, excess hourly billing, and amounts. | agreement_meth_lines | info |

### Counts

- critical: **0**
- minor: **8** (EB020-P2-001 … 008)
- info: **14** (EB020-P2-009 … 022)
- unresolved themes (below): **8** (not double-counted as critical/minor)

## Errata vs Pass 1 (separate table; PASS1_frozen unchanged)

| erratum | Pass1 original | Pass2 revised interpretation | basis |
|---------|----------------|------------------------------|-------|
| E1 | Additional Metals: Antimony\|Atimony [CAPTION VARIANT UNRESOLVED] | Source-supported printed form is **Atimony** (candidate matches). Still pending Atlas pixel confirmation. | p3_line_atimony.png + p3_chem_c/d captions; candidate `Atimony` |
| E2 | Market-rate examples: Chlorite\|Cholrite [CAPTION VARIANT UNRESOLVED] | Source-supported printed form is **Cholrite** (candidate matches). Still pending Atlas pixels. | p3_line_cholrite.png + p3_chem_d; candidate `Cholrite` |
| E3 | `mosquitoe` flagged as possible source typo or caption error | Treat as **source-supported** spelling (candidate matches). Still pending Atlas pixels. | p3_line_mosquitoe.png + p3_misc_lab |
| E4 | `Dissolved Gasses` flagged as possible source spelling or caption | Treat as **source-supported** spelling (candidate matches). Still pending Atlas pixels. | p3_line_gasses.png + p3_oilgas |
| E5 | File Review Fees: no dollar amount; Per Appendix 5-D, Chapter 5, of the Weld County Code | Affirm. Candidate likewise has no fee token. | p2_line_filereview.png + p2_misc |
| E6 | `Systems Contractor License - test taken in another location` (spaced hyphen; lowercase test) | Revise toward `Systems Contractor License- Test taken in another location` (no space after hyphen; capital Test) | p2_line_contractor_other.png; candidate |
| E7 | `Systems Contractor License - test taken in Weld` (spaced hyphen) | Revise toward `Systems Contractor License- test taken in Weld` (no space after hyphen; lowercase test) | p2_line_contractor_weld.png; candidate |
| E8 | Coordinator Application `Temporary`; Coordinator Fee `if applicable`; Unit Inspection `Transportation`; analyte `Phenolphthalein` | Affirm Pass 1 source-supported wording. These are **candidate** mismatches (001–004), not Pass 1 wording errors. | Pass 2 line/section crops |

No Pass 1 **operative fee amounts**, section membership, or service↔fee associations require revision.

## Source anomalies / preserved features (not “fixes”)

1. `Atimony` in Additional Metals (not normalized to Antimony).
2. `Cholrite` in market-rate examples (not normalized to Chlorite).
3. `mosquitoe` in zoonotic testing (not normalized to mosquito).
4. `Dissolved Gasses` (not normalized to Gases).
5. `Renewal of System Cleaners License` (singular System) vs `Systems Cleaners License` (plural Systems).
6. File Review Fees: code citation only; no numeric fee printed in the fee column.
7. Two different autoclave spore-test lines: Steam $13.00 (p.1) and Autoclave Spore Test $14.00 (p.3).
8. `PH/Temperature` capitalization as printed.
9. Fax Fee printed as `$5.00+` with `$.50` per additional page.
10. Do not calculate, repair arithmetic, or decide legal interpretation.

## Unresolved regions / glyphs

1. All glyph-level / pixel verification (pending Atlas direct image review). Caption agreement is not pixel proof.
2. Exact Unicode for hyphens/dashes (`-` vs en-dash), inch/quote marks, and the `+` on `$5.00+`.
3. Exact leader-dot counts, column alignment, underline weight, bold/font metrics.
4. Whether the coordinator-fee line prints a closing `)` after `applicable`.
5. Any faint marginalia, stamps, or marks captions did not mention.
6. `original.pdf` bytes absent from workdir — identity SHA only; not locally re-hashed or opened.
7. Full-page captions smash spaces (e.g. WELLDCOUNTY…); those smashed forms are tool artifacts, not claimed source spelling.
8. legal_currentness: not_verified.

## Pass1 agreement summary

- Headers, section inventory, and all fee amounts/bases/not-to-exceed caps: **agree**.
- Body art, child care, food protection (except candidate Temproary / applicab), institution (except candidate Transportion), miscellaneous, OWTS amounts, meth, bacteriological, chemical amounts, misc lab, oil & gas amounts, and Board-of-Commissioners NOTE: **agree**.
- Pass 1 unresolved spellings (Atimony, Cholrite, mosquitoe, Gasses, File Review Fees code-only) now have consistent crop+candidate support; recorded as errata E1–E5, not as candidate errors.
- PASS1_frozen.md / PASS1_FREEZE_RECEIPT.json / PASS1_NOTES.md re-hashed unchanged at Pass 2 start.

## Binding hashes (inputs)

- packet_manifest_sha256 (bound): b9e843e783a65a238d1a7e1106a5d0a49ea08f7ffbb59b9ca02d841e7639a112
- START_HERE_sha256: 35f5dbb4104c1cea73084fa3939228c91a7caf1339540a4033e431849122924f
- SOURCE_ONLY_IDENTITIES_sha256: 3242cf6cc99cead3c78cf0adf76aad7eb91aae153ed19ee2005f97a13caf81f7
- original_pdf_sha256 (bound): 852801c5ad0056c7b0dde6300e66e86f2e4235ce0efc16471d5210d74aa17ed3
- candidate_sha256: e54c8a008fe12cdb6704851c1009afab1c5d9186d6aff90c5fcc63e85b36f67a
- PASS1_frozen_md_sha256: 8bf0b21f79a4bd0ffca3c98daf83f6c1989b3e7508d8f03269693aa2e75bc527
- PASS1_FREEZE_RECEIPT_sha256: 0defcfc6322c3c28dfe37c4aa740569c09f37074cff6ec6cd9219622902b5808
- PASS1_NOTES_md_sha256: 7822ca5ef3ece601a590cc08d0838319fe4ae7b6e6e16c7b2a1f8ad91f8eb57b
- page-0001.png: 0838c4594f3de2ff3afa1469dd12272df506aa33103b610f4fab5b45fb71d7f7
- page-0002.png: a32edee282c120754aeaca4d5fc5273c83bd14e428ed6b99628931802d31ca8c
- page-0003.png: fb6ddbe0e95bb64a4088fd3daebb41c6dd63136d3ce06aa3ff3fa9121e5403fa

## Chronology note

Reported UTC times are wall-clock observations from the executor environment. Filesystem mtimes are not independent proof of blind order or completion. Pass 1 freeze (2026-09-13T01:35:09Z) preceded candidate open/release. Pass 2 reinspected all three pages after candidate SHA verify. This is the last assigned document; no 021.

END PASS2_REVIEW
