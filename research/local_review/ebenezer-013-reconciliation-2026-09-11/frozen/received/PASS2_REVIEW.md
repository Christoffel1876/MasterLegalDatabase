---
assignment_id: EB-PDF-013
source_id: fort-collins-wildfire-code-sd005-05
pass: PASS2_REVIEW
reviewer: Ebenezer (Grok Bot)
model: unknown
utc_pass2_start: 2026-09-11T19:15:26Z
utc_pass2_complete: 2026-09-11T19:21:01Z
legal_currentness: not_verified
status: completed_pending_atlas_verification
prior_candidate_exposure_at_pass1_freeze: none
---

# PASS 2 — Candidate vs Images vs Frozen Pass 1

## 1. Metadata / hash verification (this pass)

| Asset | Expected SHA-256 | Observed (this pass) | Match |
| :--- | :--- | :--- | :--- |
| page-0001.png | 784847fd40560671999a74f7adc1b1149f8192347298515b2e8d5df40ebb39b9 | 784847fd40560671999a74f7adc1b1149f8192347298515b2e8d5df40ebb39b9 | YES |
| page-0002.png | 55c794cba773f3b968d087d9be19215b641f333b551c583d6dca9d104cc30d0b | 55c794cba773f3b968d087d9be19215b641f333b551c583d6dca9d104cc30d0b | YES |
| page-0003.png | c1241404a5fb4132569df2a431a68d25a3d2db701d2305b496e8bb8b4cc751f7 | c1241404a5fb4132569df2a431a68d25a3d2db701d2305b496e8bb8b4cc751f7 | YES |
| page-0004.png | 658cd341c98bc92bc241e48ae82d7efd118394c0a48c0194d0e535697ad39052 | 658cd341c98bc92bc241e48ae82d7efd118394c0a48c0194d0e535697ad39052 | YES |
| page-0005.png | 9061ea1354b1c71178d2ed10c62a9e3444fa963cabd2271fea8f5ed26a2dd849 | 9061ea1354b1c71178d2ed10c62a9e3444fa963cabd2271fea8f5ed26a2dd849 | YES |
| page-0006.png | 8df50a9b6e245c7c45f07ce1739fb5c9cba2d6d99d935c68db9d0db8d6316931 | 8df50a9b6e245c7c45f07ce1739fb5c9cba2d6d99d935c68db9d0db8d6316931 | YES |
| page-0007.png | 08c0444d4ea6ff1def3209a63be2383dfe12cecd52c5c408312eab393b3cf8d3 | 08c0444d4ea6ff1def3209a63be2383dfe12cecd52c5c408312eab393b3cf8d3 | YES |
| page-0008.png | 7d6ae0f60370b4adf01e818d8dc2368a5791b66aad2f0535e542554feb76c0af | 7d6ae0f60370b4adf01e818d8dc2368a5791b66aad2f0535e542554feb76c0af | YES |
| candidate.txt | 9fc7fe62d1d678407db0d228a6e5ddc2397765a1d2f6d5ab4430a7cac3922ea7 | 9fc7fe62d1d678407db0d228a6e5ddc2397765a1d2f6d5ab4430a7cac3922ea7 | YES |
| PASS1_frozen.md | 5db47cffa3ce52a65417707c1a8f084d1051e6af38e0b71307db422c09ebda2d | 5db47cffa3ce52a65417707c1a8f084d1051e6af38e0b71307db422c09ebda2d | YES (untouched) |
| PASS1_FREEZE_RECEIPT.json | 93a4561defaea1b41ab683dad5a762a8f3f83434e292216f612c6949084f8180 | 93a4561defaea1b41ab683dad5a762a8f3f83434e292216f612c6949084f8180 | YES (untouched) |
| original.pdf | 00e7446d7deac3499b86c4b8f15a5d802cc0c14dc2621409845ec13525cb01d2 | 00e7446d7deac3499b86c4b8f15a5d802cc0c14dc2621409845ec13525cb01d2 | YES (discovery-005 raw path; hash-only; text not extracted this pass) |
| packet manifest (batch-4) | ee87ef2806e3cf9b955dbceca927087918ed0906894879a8597d7436ad67db0b | not present in `/workspace/geode-013/` | assignment-supplied only; not independently hashed |

**Access scope:** Compared `candidate.txt` to all eight page PNGs (Read + Pillow crops under `crops/` and `crops_p2/`) and to frozen Pass 1. Did **not** open `03-custody`, `04-verification`, OCR evidence, Sherlock/Atlas, or EB-PDF-014. PDF text not extracted. `legal_currentness: not_verified`.

## 2. Caption-mediation / method disclosure

- Full-page PNGs and crops inspected via **Read** (caption-mediated vision). Captions are **not** source quotations and are **not** OCR.
- User-message page attachments were also caption-mediated; not treated as source text.
- Caption hallucinations / conflicts **rejected** after crop re-reads this pass:
  - Full `page-0003.png` caption claimed “variance” was **not** struck; tight crops (`crops/p3b2.png`, `crops_p2/p3_amend2.png`, `crops_p2/p3_name_zoom.png`) confirm **~~variance~~** strike + yellow **modification** (twice), and ~~[NAME OF JURISDICTION]~~ + yellow **the City of Fort Collins**.
  - One crop caption invented section **503.2.3** Shrubs / claimed yellow replacement also struck; Pass1 crop `crops/p7_item19.png` and full page-0007 show **503.2.5** and yellow replacement **without** strike through the new penalties text.
  - One crop caption invented **“Section 503.4.2 Materials”** under exception 7; source shows **12. Section 502.1.2 Materials**.
- Limitation: not certified unaided pixel inspection. Exact Unicode (quotes, apostrophes, §, dashes, ellipsis) and exact underscore lengths not claimed from raster.
- Graphical strikethrough / yellow highlight / green redaction / yellow border are **visual draft markup only** — do **not** establish enacted legal effect.
- Printed name **Madelene Shehan** (Approving Attorney) is type; signature lines blank; **no handwriting** observed. Office titles (Mayor / City Clerk) are not signatures.

## 3. Coverage (both passes)

| Physical page | File | Printed folio | Pass 1 | Pass 2 reinspection | Notes |
| :---: | :--- | :---: | :---: | :---: | :--- |
| 1 | page-0001.png | - 1 - | YES | Full Read + prior strips | Duplicate **C.**; ORDINANCE NO. **XXX** |
| 2 | page-0002.png | - 2 - | YES | Full Read + J/K/date crops | Three green date redactions |
| 3 | page-0003.png | - 3 - | YES | Full Read + title/variance/name zooms | Strike+yellow amendments |
| 4 | page-0004.png | - 4 - | YES | Full Read + exemption/§103 crops | April 1, 2026 yellow clauses; struck §103 |
| 5 | page-0005.png | - 5 - | YES | Full Read + defs crops | AHJ / CODE OFFICIAL / CWRC Map |
| 6 | page-0006.png | - 6 - | YES | Full Read + exception yellow crops | Chapter **X**; deleted 502.1.2 |
| 7 | page-0007.png | - 7 - | YES | Full Read + deletions/item19 crops | Items 13–19; penalties mid-sentence |
| 8 | page-0008.png | - 8 - | YES | Full Read + top/mid/sig crops | Blank dates/signatures; printed attorney |

**All 8 expected pages covered in Pass 1 and Pass 2.** Status eligible for `completed_pending_atlas_verification`.

## 4. Discrepancy findings (candidate vs source images)

Candidate is machine_native_text_unreviewed (PyMuPDF `get_text`). Packaging markers `===== PHYSICAL PDF PAGE N OF 8 =====` are **not** source text. Native extraction omits graphics and most typography.

| Finding ID | Source SHA-256 | Page | Printed label | Location / region | Candidate wording | Source-supported wording / alternatives | Error type | Severity | Visual explanation |
| :--- | :--- | :---: | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| EB013-P2-001 | 55c794cba773f3b968d087d9be19215b641f333b551c583d6dca9d104cc30d0b | 2 | - 2 - | Recitals **J** and **K** date fields | `on ____________, 2025, and ______________, 2025` / `dated ________________, 2025` | Month/day under three solid **neon-green rectangular redactions** before `, 2025`; underlying characters unreadable through green; candidate underscores are consistent with PDF text layer under/beside redaction graphics | omitted_graphic_markup / redaction_vs_text_layer | critical | Images show green blocks; native text extracts underscore placeholders, not green |
| EB013-P2-002 | c1241404a5fb4132569df2a431a68d25a3d2db701d2305b496e8bb8b4cc751f7 | 3 | - 3 - | §101.1 Title amendment | `[NAME OF JURISDICTION]the City of Fort Collins` (no markup; no space after `]`) | ~~[NAME OF JURISDICTION]~~ + yellow ==the City of Fort Collins==; no space after `]` is source-true | omitted_strike_and_highlight | critical | Candidate concatenates struck placeholder + replacement as one live string |
| EB013-P2-003 | c1241404a5fb4132569df2a431a68d25a3d2db701d2305b496e8bb8b4cc751f7 | 3 | - 3 - | §102.9 Historic Structures | `A variance modification is authorized` … `and the variance modification is` | `A ~~variance~~ ==modification==` … `the ~~variance~~ ==modification==` | omitted_strike_and_highlight | critical | Both “variance” struck; both “modification” yellow; candidate reads as dual live words |
| EB013-P2-004 | c1241404a5fb4132569df2a431a68d25a3d2db701d2305b496e8bb8b4cc751f7 | 3 | - 3 - | Item 3 deleted §102.9.1 | Live paragraph `102.9.1 Historic preservation exemption. The authority having jurisdiction may…` | Instruction “deleted in its entirety” + entire body **struck through** | omitted_deletion_strike | critical | Struck deleted text appears as operative wording in candidate |
| EB013-P2-005 | 658cd341c98bc92bc241e48ae82d7efd118394c0a48c0194d0e535697ad39052 | 4 | - 4 - | Item 5 / SECTION 103 | Both old §103.1–103.3 body and replacement header appear as live text; no strike/yellow | Old **SECTION 103** + 103.1–103.3 **fully struck**; replacement **SECTION 103—CODE COMPLIANCE AGENCY** yellow; body continues p.5 yellow | omitted_strike_and_highlight | critical | Dual live SECTION 103 blocks without draft markup |
| EB013-P2-006 | 9061ea1354b1c71178d2ed10c62a9e3444fa963cabd2271fea8f5ed26a2dd849 | 5 | - 5 - | §106.1 replace | Both `106.1 General. An AHJ has the authority to establish fees.` and `106.1 Fees.…` live | ~~106.1 General…~~ deleted; ==106.1 Fees…== yellow replacement | omitted_strike_and_highlight | critical | Candidate presents both as concurrent live text |
| EB013-P2-007 | 9061ea1354b1c71178d2ed10c62a9e3444fa963cabd2271fea8f5ed26a2dd849 | 5 | - 5 - | §301.1 Scope | `based on the findings of fact Colorado Wildfire Resiliency State Code Map (CWRC Map),…` | `based on the ~~findings of fact~~ ==Colorado Wildfire Resiliency State Code Map (CWRC Map), … Board,==` | omitted_strike_and_highlight / concatenation | critical | Struck phrase + yellow replacement concatenated |
| EB013-P2-008 | 8df50a9b6e245c7c45f07ce1739fb5c9cba2d6d99d935c68db9d0db8d6316931 | 6 | - 6 - | §302.1 Declaration | `based on the findings of fact CWRC Map.` | `based on the ~~findings of fact~~ ==CWRC Map==.` | omitted_strike_and_highlight / concatenation | critical | Same pattern as EB013-P2-007 |
| EB013-P2-009 | 8df50a9b6e245c7c45f07ce1739fb5c9cba2d6d99d935c68db9d0db8d6316931 | 6–7 | - 6 - / - 7 - | Items 12–18 deleted landscaping/tree sections | Full deleted bodies for 502.1.2, 502.1.3, 502.1.4, 503.2.4, 503.2.4.1, 503.2.5, 503.3.2 appear as live text | Each “deleted in its entirety” + body **struck through** | omitted_deletion_strike | critical | Mass deleted content readable as if still in force in candidate |
| EB013-P2-010 | 08c0444d4ea6ff1def3209a63be2383dfe12cecd52c5c408312eab393b3cf8d3 | 7–8 | - 7 - / - 8 - | Item 19 C101.3.7 | Both fees line and civil-infraction paragraph live; no yellow | ~~C101.3.7… establish fees.~~ + yellow ==Any person who violates… separate offense.== (crosses p.7–8) | omitted_strike_and_highlight | critical | Dual C101.3.7 paragraphs without markup |
| EB013-P2-011 | (all pages with italics) | 1–8 | various | Italicized titles / defined terms | Plain roman in candidate (e.g. `2025 Colorado Wildfire Resiliency Code`, `Coloradoan`, `roof covering`, `wildland-urban interface`, `code official`, `building`/`structure`/`approved`) | Source shows italics on many code titles and defined terms (Pass1 inventory; some residual UNCERTAIN) | omitted_italics | minor | Native text extraction does not preserve italic face |
| EB013-P2-012 | 55c794cba773f3b968d087d9be19215b641f333b551c583d6dca9d104cc30d0b | 2 | - 2 - | Recital **K** | `Attached as Exhibit A` | `Attached as` + **underlined** `Exhibit A` | omitted_underline | minor | Underline not in candidate |
| EB013-P2-013 | 55c794… / c124140… / … / 08c044… | 2–7 | - 2- – - 7 - | Article IX / §5-371 block | No border indicated | Thin **yellow rectangular border** around inserted Chapter 5 Article IX / amendments (continues p.2–7 into p.8 yellow clause) | omitted_border_graphic | minor | Draft framing graphic absent from candidate |
| EB013-P2-014 | 658cd341c98bc92bc241e48ae82d7efd118394c0a48c0194d0e535697ad39052 | 4 | - 4 - | §102.10 exemptions 2–4 (and p.6 exceptions 3,4,6) | Full `compared to the condition … April 1, 2026…` as unmarked text | Same words present but **yellow-highlighted** as local additions | omitted_highlight | minor | Substantive words match; draft addition markup missing |
| EB013-P2-015 | 9061ea1354b1c71178d2ed10c62a9e3444fa963cabd2271fea8f5ed26a2dd849 | 5 | - 5 - | Yellow additions (103.1 entity; 105.2 clause; AHJ def; CODE OFFICIAL last sentence; etc.) | Words present unmarked | Yellow highlight on additions | omitted_highlight | minor | Text present; addition markup missing |
| EB013-P2-016 | 8df50a9b6e245c7c45f07ce1739fb5c9cba2d6d99d935c68db9d0db8d6316931 | 6 | - 6 - | Exception **7** (historic / Chapter X) | Full exception text unmarked | Entire exception **yellow-highlighted**; **Chapter X** placeholder preserved in both | omitted_highlight | minor | Candidate preserves Chapter X (good); omits yellow |
| EB013-P2-017 | (all) | 1–8 | various | Page packaging | Printed folio `- N -` appears near **top** of each candidate page block (after draft banner) | On images, folio is **bottom-centered** footer | extraction_order / layout | minor | PyMuPDF reading order; not a content invention |
| EB013-P2-018 | 784847fd40560671999a74f7adc1b1149f8192347298515b2e8d5df40ebb39b9 | 1 | - 1 - | Recital lettering | Two consecutive `C.` labels preserved | Two consecutive **C.** labels (source anomaly) | none (preserved) | info | Candidate correctly retains duplicate **C.**; do not “fix” |
| EB013-P2-019 | 784847fd40560671999a74f7adc1b1149f8192347298515b2e8d5df40ebb39b9 | 1 | - 1 - | Title | `ORDINANCE NO. XXX, 2025` | `ORDINANCE NO. XXX, 2025` | none (preserved) | info | Placeholder XXX retained |
| EB013-P2-020 | 7d6ae0f60370b4adf01e818d8dc2368a5791b66aad2f0535e542554feb76c0af | 8 | - 8 - | Signature / effective-date block | Underscore blanks; `Approving Attorney: Madelene Shehan`; no ink | Blank underscores; printed attorney name only; **no handwritten signatures** | none (aligned) | info | Separate printed name from absent handwriting |
| EB013-P2-021 | (all) | 1–8 | header | Draft banner | `DRAFT FOR DISCUSSION ONLY -` / `SUBJECT TO FURTHER REVIEW AND REVISION` | Same banner every page | none (preserved) | info | Draft status preserved |
| EB013-P2-022 | c1241404a5fb4132569df2a431a68d25a3d2db701d2305b496e8bb8b4cc751f7 | 3 | - 3 - | §101.1 quote marks | Curly/smart quotes around `this code` in candidate (`“this code.”`) | Source appears to use curly quotes (caption); exact code point not certified from raster | unicode_uncertain | unresolved | Exact quote code points not claimed |
| EB013-P2-023 | 55c794cba773f3b968d087d9be19215b641f333b551c583d6dca9d104cc30d0b | 2 | - 2 - | Green redaction interiors | Underscores in text layer | Month/day glyphs under green **unreadable**; unresolved as to whether underscores alone or other characters underlie green | unresolved_redaction | unresolved | Do not invent dates |

**Severity counts:** critical **10** (EB013-P2-001 … 010); minor **7** (011–017); info/preserved **4** (018–021); unresolved **2** (022–023).  
*(Info rows are not defects; critical+minor+unresolved = 19 actionable/uncertain findings.)*

**Counts for receipt:** `critical: 10`, `minor: 7`, `unresolved: 2` (plus residual italics UNCERTAIN noted in §6; green dates counted in unresolved).

## 5. Source anomalies preserved (do not silently “fix”)

1. Draft banner every page.  
2. Ordinance number **XXX, 2025**.  
3. Duplicate recital label **C.**  
4. Three green date redactions (J×2, K×1).  
5. Strike + yellow draft markup throughout §5-371 (graphical only; not enacted effect).  
6. Yellow border around Article IX / amendments.  
7. Exception 7 **Chapter X** placeholder.  
8. Baseline date **April 1, 2026** in yellow comparison clauses.  
9. Blank introduction / passage / effective-date / Mayor / City Clerk lines.  
10. Printed Approving Attorney **Madelene Shehan** only (no handwritten signature).

## 6. Residual visual UNCERTAIN (source typography)

| Item | Pass 2 note |
| :--- | :--- |
| *habitable* vs *habitable space* (p.4 item 8) | Tight crop `crops/p4b3.png` favors italics on **habitable** only (+ *Accessory structures*, *occupiable*); “space” roman. Full-page caption sometimes said phrase italics — prefer crop. |
| “building official” in yellow CODE OFFICIAL sentence (p.5) | Defs crop shows *code official* / *code official’s* italic; **building official** appears roman (resolves Pass1 UNCERTAIN toward not italic). |
| Struck “Tree crowns…” italics (p.7 §§503.2.4 / 503.2.4.1) | Still mild UNCERTAIN; §503.3.2 struck body more clearly italic on Tree crowns sentence. |
| Struck 502.1.2 Exception italics (*Ignition-resistant plantings*, *Immediate Zone*) | Pass1 under-marked vs some captions; mild UNCERTAIN / see errata. |
| Exact underscore lengths on p.8 blanks | Approximate only. |

## 7. Errata vs Pass 1 (separate table only — frozen file not modified)

| Erratum ID | Pass 1 location | Original Pass 1 wording / claim | Revised Pass 2 interpretation | Severity |
| :--- | :--- | :--- | :--- | :--- |
| EB013-P1-E01 | Page 6, Exception 6 yellow markup | `500 ==square feet compared to the condition of the structure on April 1, 2026, as determined based on city and county records.==` | Yellow begins at **compared** (after `500 square feet `); `square feet` is **not** inside the yellow run. Confirmed via `crops_p2/p6_btw.png` / `p6_yl3.png`. | minor |
| EB013-P1-E02 | Page 5, CODE OFFICIAL UNCERTAIN | `[UNCERTAIN: whether “building official” … is italicized]` | Reinspection defs crop: **building official** appears **not** italicized; *code official* is. Soft resolution of uncertainty (not a substantive text error). | minor / clarification |
| EB013-P1-E03 | Page 6, struck 502.1.2 Exception | Pass1 left `Ignition-resistant plantings` / `Immediate Zone` unmarked for italics in struck Exception | Some captions indicate those terms were italic in source before/within strike; mark as under-italics risk in Pass1 struck block. Mild. | minor |
| EB013-P1-E04 | Page 4 item 8 UNCERTAIN | Competing *habitable* space vs *habitable space* | Prefer crop reading: *habitable* + roman “space”. Clarification. | minor / clarification |

No Pass 1 erratum for duplicate **C.**, XXX, green redactions, Chapter X, or variance strikes — those were correctly preserved. Frozen `PASS1_frozen.md` left **unchanged**.

## 8. Candidate strengths (agreement)

- Substantive prose of recitals A–K and Sections 1–3 largely matches images when markup is ignored.  
- Preserves source anomalies: XXX, duplicate C., Chapter X, April 1, 2026, blank date/signature underscores, Madelene Shehan.  
- Includes deleted/struck bodies (good for recovery) but **without** strike cues (bad for enacted-vs-draft distinction).  
- Ellipses `. . .` in §202 definitions present.  
- Em dash form `SECTION 103—CODE COMPLIANCE AGENCY` present in candidate.

## 9. Limitations

- Caption-mediated vision; not certified unaided pixel inspection.  
- No 03-custody / 04-verification / OCR / Sherlock / Atlas / EB-PDF-014 opened.  
- Packet manifest not in workdir for independent hash.  
- Graphical markup ≠ enacted effect.  
- `legal_currentness: not_verified`. Printed dates and draft title do not establish operative law.

## 10. Status

`completed_pending_atlas_verification` — all 8 physical pages fully covered in Pass 1 and Pass 2; hashes verified; Pass 1 freeze untouched.
