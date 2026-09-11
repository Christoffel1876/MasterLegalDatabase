# PASS 2 — Source-to-OCR Comparison Review

## 1. Metadata

| Field | Value |
| :--- | :--- |
| assignment_id | EB-PDF-012 |
| source_id | larimer-data-center-moratorium-sd004-04 |
| expected_pages | 2 |
| utc_pass2_start | 2026-09-11T18:53:18Z |
| utc_pass2_complete | 2026-09-11T18:57:00Z |
| reviewer | Ebenezer (Grok Bot) |
| model | unknown |
| legal_currentness | not_verified |
| pass | PASS2_REVIEW |
| status | completed_pending_atlas_verification |
| prior_candidate_exposure (at Pass1 freeze) | none |
| candidate opened this pass | YES |

## 2. Hash verification (this pass)

| Asset | Expected SHA-256 | Observed SHA-256 | Match |
| :--- | :--- | :--- | :--- |
| candidate.txt | f8fcdc8faee762730ba8c09498b6458f42b17681256f30c5bbf6d32d14872981 | f8fcdc8faee762730ba8c09498b6458f42b17681256f30c5bbf6d32d14872981 | YES |
| page-0001.png | 178199b0e8546d8b1a743b780875b66ecad7b5d87067d888a8e41c331ca42464 | 178199b0e8546d8b1a743b780875b66ecad7b5d87067d888a8e41c331ca42464 | YES |
| page-0002.png | 13b1c95d918ed6bf268bd48c5ed05d04e67508392bb59f76630324ff55d6bfba | 13b1c95d918ed6bf268bd48c5ed05d04e67508392bb59f76630324ff55d6bfba | YES |
| PASS1_frozen.md | f6e085f5c759a61fb026383c14593af10ba480ec6bf67760bc733a5483e14c62 | f6e085f5c759a61fb026383c14593af10ba480ec6bf67760bc733a5483e14c62 | YES (untouched) |
| PASS1_FREEZE_RECEIPT.json | 81cffb86dd37b2dbf7f359f76e2d2188a5c38c8ec42777316b8a7fe1c329434b | 81cffb86dd37b2dbf7f359f76e2d2188a5c38c8ec42777316b8a7fe1c329434b | YES (untouched) |
| original.pdf | d5de580139ba20bb5e80b4226b583ebc033eef693884dedeff0a8dddcfe3696c | d5de580139ba20bb5e80b4226b583ebc033eef693884dedeff0a8dddcfe3696c | YES (discovery raw path only; not in workdir; text not extracted) |
| packet manifest (batch-3) | 86431bd0f0c252bf845d4749131dc5adfc54e618dee76294473d1ad9e6cb75d6 | not present on disk | assignment-supplied only; not independently hashed |

Engine: uncorrected Apple Vision OCR rev 3 (native PyMuPDF empty). Status was `machine_ocr_unreviewed`. Physical-page markers in candidate are **packaging**, not source text. Engine confidence is **not** an accuracy finding (several conf=1.0 observations are wrong).

## 3. Image-viewing method / caption-mediation disclosure

- Full pages `page-0001.png` / `page-0002.png` inspected via **Read** (caption-mediated vision).
- User-message attachments of the same pages were also caption-mediated; not treated as source quotations.
- Pass1 Pillow crops under `/workspace/geode-012/crops/` plus new Pass2 crops under `crops_pass2/` re-read via Read.
- ocr-evidence JSON opened for hard-spot observation order/text only; confidence not used as accuracy.
- **Captions are NOT source quotations.** They truncated, disagreed on stray-mark locus, invented/varied signer spellings, and occasionally hallucinated typography (e.g. transient “comma after COLORADO”, “Attrorney”). Glyph decisions prefer agreement of Pass1 blind transcript + multiple tight crops; remaining conflicts marked **[UNCERTAIN]**.
- Printed titles separated from handwriting notes. **Signer identity is not certified from printed office titles.**
- `legal_currentness: not_verified.`

## 4. Physical-page coverage

| Page | File | Pass1 covered | Pass2 reinspect | Candidate compared | Notes |
| :--- | :--- | :---: | :---: | :---: | :--- |
| 1 | page-0001.png | YES | YES (full + crops) | YES | Recording banner, title, 7 WHEREAS, 5 bullets, stray mark, folio `1` |
| 2 | page-0002.png | YES | YES (full + crops) | YES | Banner, WHEREAS 8, resolving clause, operative, definition, hearing, expire, date hand, Chair/Deputy/seal/counsel |

Both complete physical pages received both passes → status eligible for `completed_pending_atlas_verification`.

## 5. Discrepancy table (candidate vs source images)

Severity: **critical** = wrong legal/identity token or major omission/invention; **minor** = typography/line-break/packaging; **info** = packaging or style loss.

| ID | Src SHA (page) | Page | Location | Candidate wording | Source-supported / alternatives | Error type | Sev | Explanation / visual support |
| :--- | :--- | :---: | :--- | :--- | :--- | :--- | :---: | :--- |
| D01 | page-0001 …2464 | 1 | WHEREAS1 cite `C.R.S. §29-20-101` | `C.R.S. 829-20-101` | `C.R.S. §29-20-101` (section symbol; no space after §) | substitution / invention | **critical** | Apple Vision replaced `§` with digit `8`. Pass1 + cite crop (`p1_cite_l1-3.png`) show `§`. Conf=1.0 on bad obs. |
| D02 | page-0001 …2464 | 1 | 4th WHEREAS lead word | `WHERŁAS,` | `WHEREAS,` | substitution (Ł for E) | **critical** | Crop `p1_w4.png` shows normal bold `WHEREAS,`. Candidate/engine invent Latin `Ł`. |
| D03 | page-0001 …2464 | 1 | Footer folio | *(omitted)* | printed centered `1` | omission | **minor** | Folio visible (`p1_pagenum*`, footer). Not in candidate observations. |
| D04 | page-0001 …2464 | 1 | Stray tick near 6th WHEREAS | *(omitted)* | stray overlay present; **not** part of word sequence | omission of anomaly | **minor** | Source anomaly preserved as non-text. Candidate correctly omits from word stream but does not flag. Exact locus **[UNCERTAIN]** (see errata E1). |
| D05 | page-0002 …bfba | 2 | Hearing line `1st Floor` | `1s Floor` | `1st Floor` with superscript *st* | omission (superscript) | **critical** | Crop `p2_1st_floor.png` / hearing crop: superscript `st` present. Candidate drops `t`. |
| D06 | page-0002 …bfba | 2 | Handwritten date after `DATED THIS DAY,` | `fanuary 27,2026` | Best visual: `January 27, 2026`; competing `January 27, 202.6` **[UNCERTAIN]** | handwriting misread + spacing | **critical** | OCR invented leading `f`, dropped space after comma. Printed phrase is only `DATED THIS DAY,`. Date is handwriting — not certified execution date. |
| D07 | page-0002 …bfba | 2 | Chair signature ink | split obs `fodyc` then later `Shadduck-MNally` | Ink resembles **Jody Shadduck-McNally** (hyphenated); printed title only `Chair` | handwriting garble / reorder | **critical** | Signature mark present. OCR invents `fodyc`, drops `J`, mangles McNally→`MNally`, splits name across observations. **Not certified as signer identity.** |
| D08 | page-0002 …bfba | 2 | Deputy County Clerk ink | `wus` / `muy` | Signature mark present; spelling **unresolved** (competing caption readings) | handwriting garble | **critical** | Printed: `ATTEST:` + `Deputy County Clerk`. Ink not resolved to a single spelling. OCR fragments are not source-supported names. **Not certified.** |
| D09 | page-0002 …bfba | 2 | Circular seal | `#LA` / `SEAL` / `COLORADO` | Arc: ★ LARIMER COUNTY CLERK ★; center SEAL; bottom COLORADO | omission + invention | **critical** | Seal crop shows LARIMER / COUNTY / CLERK with stars; OCR invents `#LA`, omits LARIMER COUNTY CLERK. |
| D10 | page-0002 …bfba | 2 | Counsel header | `APPROVED AS TO FORNI:` | `APPROVED AS TO FORM:` | substitution (M→NI) | **critical** | Crop `p2_approved.png` / ap_block: `FORM:`. |
| D11 | page-0002 …bfba | 2 | Counsel printed title | `Astistant Depury County Attostes` | `Assistant Deputy County Attorney` | multi-substitution | **critical** | Printed title under line. Candidate invents Astistant/Depury/Attostes. |
| D12 | page-0002 …bfba | 2 | Counsel signature ink | `rants withet` | Ink present; visual resembles Frank + middle + Hay/Hays/Haug-like surname **[UNCERTAIN]** | handwriting garble | **critical** | Presence only certified. OCR string not source-supported. **Not certified as signer.** |
| D13 | page-0002 …bfba | 2 | Resolving clause lineation | `NOW, THEREFORE,` ¶ `BE IT RESOLVED…` ¶ `COMMISSIONERS…` | Two source lines: (1) `NOW, THEREFORE, BE IT RESOLVED BY THE BOARD OF COUNTY` (2) `COMMISSIONERS OF THE COUNTY OF LARIMER, STATE OF COLORADO THAT:` | observation re-segmentation | **minor** | Words largely preserved; line grouping differs from raster. No comma between COLORADO and THAT (Pass1 confirmed; tight crop). |
| D14 | page-0002 …bfba | 2 | Definition quotes | straight `"data center facility"` | typographic/curly double quotes observed | style normalization | **minor** | Exact Unicode not claimed; candidate uses ASCII quotes. |
| D15 | page-0002 …bfba | 2 | `Board's` | ASCII apostrophe `Board's` | typographic apostrophe observed | style normalization | **minor** | |
| D16 | both | — | Page markers | `===== PHYSICAL PDF PAGE … =====` | not on source pages | packaging | **info** | Per prompt: packaging, not source text. |
| D17 | page-0001 …2464 | 1 | `et seq.` | upright `et seq.` | italic *et seq.* in source | style loss | **minor** | |
| D18 | page-0001 …2464 | 1 | Other `§` cites | `§30-11-101(2)`, `§ 30-11-107`, `§ 30-28-115` | matches mixed spacing | OK | — | Second+ cites kept `§`; only first cite failed (D01). |

### Source anomalies correctly preserved in candidate (when present)

- Operative syntax redundancy: “shall not accept … facilities, including …, shall be accepted or processed” — **preserved** (do not “fix”).
- “shall expire **on** thirty days thereafter” — **preserved**.
- “definitions, standards and conditions” (no serial comma) — **preserved**.
- “large scale” unhyphenated vs Industrial-Scale / High-Intensity hyphenated — **preserved**.
- “2026 at 3:00 pm” (no comma after year; lowercase pm) — **preserved**.
- Mixed § spacing on later cites — **preserved**.

## 6. Errata vs Pass1 (do not edit PASS1_frozen.md)

| ID | Pass1 statement | Pass2 correction / note | Sev |
| :--- | :--- | :--- | :---: |
| E1 | Stray mark “over the space between ‘that’ and ‘it’” | Reinspection: mark is a thin diagonal tick **above the baseline** of the 6th WHEREAS first line; crop captions variously place it above **that** / near **determined** / above **ne** in **necess**. Still a non-lexical stray. Location phrasing in Pass1 is slightly over-precise → prefer “above first line of 6th WHEREAS near ‘determined that it is necessary’”. | minor |
| E2 | Deputy / counsel ink readings | Remain **unresolved**; Pass2 captions added competing spellings (Lucy/Lacy/Linnie/Guy-like; Frank Haug/Hay/Hays). No certification. Pass1 uncertainty stands. | info |
| E3 | — | No material body-text errata found vs Pass1 for printed paragraphs; Pass1 blind transcript aligns with reinspection on operative/definition/hearing/expire wording. | — |

## 7. Handwriting / seal summary (printed vs ink)

| Region | Printed | Ink / device | Candidate | Pass2 stance |
| :--- | :--- | :--- | :--- | :--- |
| Date line | `DATED THIS DAY,` | Handwriting ~ January 27, 2026 (competing 202.6) | `fanuary 27,2026` | Presence yes; OCR wrong; date not certified |
| Chair | `Chair` | Resembles Jody Shadduck-McNally | `fodyc` + `Shadduck-MNally` | Presence yes; identity **not certified** |
| Attest | `ATTEST:` / `Deputy County Clerk` | Unresolved cursive | `wus` / `muy` | Presence yes; identity **not certified** |
| Seal | — | ★ LARIMER COUNTY CLERK ★ / SEAL / COLORADO | `#LA` / SEAL / COLORADO | Device present; OCR incomplete/invented |
| Counsel | `APPROVED AS TO FORM:` / `Assistant Deputy County Attorney` | Unresolved Frank+… | FORNI / rants withet / Astistant… | Printed titles clear; ink **not certified** |

## 8. Agreement regions (candidate ≈ Pass1 ≈ source)

Recording banners (both pages); title; WHEREAS 2, 3, 5, 6, 7 body words (aside from stray); bullet list wording; WHEREAS 8; operative 30-day paragraph including syntax anomaly; definition body (aside from quote style); geographic effect sentence; hearing schedule content except `1st`→`1s`; expire sentence including “on thirty days”; board name block printed lines.

## 9. Unresolved regions

1. Exact character identity of page-1 stray tick.
2. Handwritten year `2026` vs `202.6` detachment.
3. Deputy County Clerk signature spelling.
4. Assistant Deputy County Attorney signature spelling (Frank + middle + surname).
5. Exact Unicode for curly quotes, typographic apostrophe, superscript `st`, bullet discs.
6. Packet manifest file not on disk for independent hash.

## 10. Counts

| Class | Count |
| :--- | ---: |
| critical findings | 11 (D01,D02,D05–D12) |
| minor findings | 6 (D03,D04,D13–D15,D17) |
| info / packaging | 1 (D16) |
| unresolved regions | 6 |
| Pass1 errata rows | 2 substantive (E1–E2) |

## 11. Limitations

- Caption-mediated vision even with crops; not certified unaided pixel inspection.
- Did not silently “correct” candidate to wishful reading; findings document differences.
- PASS1_frozen.md and PASS1_FREEZE_RECEIPT.json were not modified.
- No determination of whether moratorium is presently in force (`legal_currentness: not_verified`).
- Time/cost: unknown.

## 12. Conclusion

Both pages covered in Pass1 and Pass2. Candidate is faithful machine OCR of printed body in many stretches but contains **critical** §→8 and WHEREAS→WHERŁAS substitutions, superscript loss (`1s`), and severe handwriting/seal/counsel garbling. Status: **`completed_pending_atlas_verification`**.
