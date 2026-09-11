# PASS 2 — Candidate vs Image Comparison (EB-PDF-011)

## 1. Metadata

| Field | Value |
| :--- | :--- |
| assignment_id | EB-PDF-011 |
| source_id | larimer-fee-increase-memo-sd004-lc-09 |
| expected_pages | 1 |
| utc_pass2_start | 2026-09-11T18:43:43Z |
| utc_pass2_end | 2026-09-11T18:46:50Z |
| status | completed_pending_atlas_verification |
| legal_currentness | not_verified |
| candidate_status | machine_native_text_unreviewed |
| candidate_engine | PyMuPDF native text (NOT OCR) |
| reviewer | Ebenezer (Grok Bot) |
| pass | PASS2 |
| prior_materials_used | PASS1_frozen.md (read-only; not edited); PASS1_NOTES.md; PASS1_FREEZE_RECEIPT.json; candidate.txt; page-0001.png + Pillow crops under crops_p2/ |
| native_evidence_json | not_opened |
| original_pdf_opened | hash-verified only at `/workspace/geode-discovery-004/larimer/raw/fee_increase_memo.pdf` (same SHA as assignment); PDF not used as transcription authority — page PNG + crops decide |

## 2. Hash references

| Asset | SHA-256 | Role / notes |
| :--- | :--- | :--- |
| packet manifest | 36dcce0e4b4712069e663a7950c1c21ebd2ef31dc6a53321b0a59ba72cc59db4 | cited from assignment / Pass1 freeze (file not present in workdir) |
| original.pdf | 17a50621a9669c37876bef67cbeeba930d95b0520abc6a210a23bfd7f40b1d19 | **verified** this pass against discovery copy |
| page-0001.png | 39b8e679e3709ec002883799412a21bc9bc6b60c6f0998fa44e81704fd8b853f | **verified** match this pass |
| candidate.txt | 5d8cbcad2b5c8dd72c8ba4092358607c78041a80457a56e7adac82e52bc1a768 | **verified** this pass (sha256sum); matches assignment expected |
| PASS1_frozen.md | a4c4a3102cdd29e01402e80df4a35dac13cafcaf2809a26720bf45866cabd09a | **unchanged**; verified; **not edited** |
| PASS1_FREEZE_RECEIPT.json | 5ce23f28d5f51770f34f50514c200803d67093c946dbd0bed5054032794897f8 | **unchanged**; verified |

## 3. Image-viewing method / limits

- Compared `candidate.txt` (PyMuPDF native text, `machine_native_text_unreviewed`) to the single page PNG.
- Page image inspected with the **Read** tool (returns **caption-mediated** vision descriptions — **not** source quotations and **not** OCR) plus **Pillow crops** under `/workspace/geode-011/crops_p2/` covering letterhead/wordmark/pipe area, address/`Larimer.org`, H1, H2 both lines, full P1/P2 paragraphs, individual body lines, `year’s`/`2.29%` zoom, Director apostrophe zoom, lower blank field, and corners.
- **Caption mediation disclosed:** captions can truncate, paraphrase, invent, or inject context. Known mediation noise this pass:
  - Assignment-chat / full-page caption paraphrased Section 1 body (omitted “passed a resolution”; shortened agency citation) — **rejected**; line crops + candidate preserve the full printed sentence.
  - `year_pct` crop caption once called the apostrophe in `year’s` “straight”; `p1_l4b` / `director_zoom` captions called curly/smart — **unresolved at code-point level from pixels**; candidate and Pass1 use U+2019; captions are not authority for Unicode.
  - One address-related caption listed the phone with hyphens in a “Key Data” gloss while the same crop’s transcription correctly used dots — **rejected**; image + candidate use `970.498.7690`.
  - Early mis-boxed crops (before Y-band recalibration) returned bar-only or wrong bands; discarded after recalibration from ink-row runs.
- Page markers `===== PHYSICAL PDF PAGE … =====` in candidate are **packaging only**, not printed source text.
- PASS1_frozen used only as a **finder aid**; neither PASS1 nor candidate was assumed correct when they agree or disagree — image pixels (via Read + crops) decide.
- Source anomalies are **preserved**, not “fixed” (tables `1-A, 1-B, 1-C, and 1-E` with **1-D omitted**; `traffic generating` without hyphen; TCEF heading with **no percent**; mixed-case `Larimer.org`; dotted phone).
- `legal_currentness: not_verified`. Printed effective dates July 1, 2026 / October 1, 2026 reported as printed only.
- Did **not** open native-evidence JSON. Did **not** modify PASS1_frozen.md, PASS1_FREEZE_RECEIPT.json, source images, or candidate.txt.

## 4. Page coverage

| Physical page | File | Candidate section present | Image+crops re-inspected | Compared | Notes |
| :---: | :--- | :---: | :---: | :---: | :--- |
| 1 of 1 | page-0001.png | YES | YES — full raster + letterhead, wordmark/pipe, address, H1, P1 lines, H2 both underlined lines, P2 lines, lower blank, corners | YES | Reading order matches visual top→bottom; wording/numbers agree; only minor whitespace/layout notes |

**Coverage statement:** Expected page 1 of 1 compared in both Pass 1 (frozen blind transcript) and Pass 2 (candidate vs image). Ink content occupies approximately y 150–1806 of 3300; remainder blank.

## 5. Findings

| finding_id | physical_page | location | candidate_text | text_visibly_supported_by_image | proposed_correction_or_alternatives | error_type | severity | explanation |
| :--- | :---: | :--- | :--- | :---: | :--- | :--- | :--- | :--- |
| EB011-P2-001 | 1 | Letterhead wordmark | `LARIMER COUNTY  \|  COMMUNITY DEVELOPMENT` (ASCII spaces: two before and two after `\|`; trailing spaces on line) | partial (words/pipe yes; spacing no) | Prefer visual single space each side of `\|`: `LARIMER COUNTY \| COMMUNITY DEVELOPMENT` (exact tracking not claimed) | whitespace / spacing | minor | Pixel gaps around the pipe (~38–41 px) are on the order of one word-space each side in this letterspaced caps line, not two. Native PyMuPDF commonly emits extra spaces around separators when PDF tracking is present. Words, `|`, and all-caps form match the image. |
| EB011-P2-002 | 1 | Most extracted lines | Trailing ASCII space(s) on wordmark, address, headings, body lines, and `October 1, 2026  ` (two trailing spaces) | no (spaces not “printed” as separate glyphs) | Strip trailing line whitespace for display; do not treat as printed characters | whitespace | minor | Typical native-text line padding. Does not alter recoverable wording. |
| EB011-P2-003 | 1 | Letterhead / heading chrome | Candidate is plain text only — no vertical bar, horizontal rule, teal ink, or underlines | n/a (non-text) | Document layout separately; text candidate is not expected to encode chrome | layout_not_in_text | minor | Image shows teal vertical bar + rule + teal letterhead type; black bold underlined H1/H2 (H2 underline per line). Absence from native text is expected, not a wording error. |

### Finding counts

| Severity | Count |
| :--- | ---: |
| critical | 0 |
| minor | 3 |
| unresolved | 1 |

### Unresolved (not counted as candidate wording errors)

| id | physical_page | topic | note |
| :--- | :---: | :--- | :--- |
| EB011-P2-U001 | 1 | Apostrophe code points in `Director’s` / `year’s` | Raster + conflicting captions cannot certify U+2019 vs U+0027 vs lookalikes. Candidate emits U+2019 for both; Pass1 preferred typographic appearance with the same caveat. **Do not “fix” to ASCII.** Residual Unicode uncertainty only. |

## 6. PASS1 errata (PASS1_frozen.md not edited)

| PASS1 locus | PASS1 statement | Pass 2 disposition |
| :--- | :--- | :--- |
| Layout note (§ Page 1 transcript) | “justified-looking body paragraph” | **Revise characterization:** P1/P2 crops read as **left-aligned / ragged-right**, not true full justification. Wording transcript itself is unaffected. |
| Apostrophe Limitations | Typographic `’` appearance; code point not claimed | **Confirm residual uncertainty** (EB011-P2-U001). Candidate U+2019 is consistent with Pass1 preference; no Pass1 wording errata. |
| Section 1 continuous prose | Full Building Permit paragraph incl. tables 1-A…1-E, 2.29%, July 1, 2026 | **Reconfirmed** vs image crops + candidate (exact continuous prose match). |
| Section 2 continuous prose | TCEF paragraph; `traffic generating` (no hyphen); no percent in heading | **Reconfirmed** (`p2_full`, `p2_l4`, `h2_both`) + candidate. |
| Anomalies list | 1-D omitted; TCEF heading date-only; `Larimer.org` mixed case; dotted phone | **Confirmed** vs image; preserved in candidate. |
| Remainder of page | Blank below ~y 1806; no footer/page number/signature | **Confirmed** (`lower_blank`, corner crops). |

## 7. Agreements worth recording (esp. preserved anomalies)

| Topic | Candidate | Image / PASS1 | Notes |
| :--- | :--- | :--- | :--- |
| Wordmark tokens | `LARIMER COUNTY` … `COMMUNITY DEVELOPMENT` with `\|` | Wordmark crop | Agreement on tokens; spacing per EB011-P2-001 |
| Address / contact | `Director’s Office, P.O. Box 1190, Fort Collins, Colorado 80522-1190, 970.498.7690, Larimer.org` | Address + `Larimer.org` crops | **Preserve** dotted phone; mixed-case site; U+2019 in Director’s |
| H1 | `Building Permit Fee Increase of 2.29% on July 1, 2026` | H1 crop; underlined | Agreement |
| Building tables list | `1-A, 1-B, 1-C, and 1-E` | P1 / tables crops | **Preserve** omission of 1-D |
| CPI citation | `US Department of Labor/Bureau of Labor Statistics` … `Denver-Boulder-Greeley` | P1 lines | `US` without periods; slash with no spaces |
| Increase / effective (building) | `2.29%` … `July 1, 2026` | H1 + P1 | Agreement; no space before `%` |
| H2 two-line form | `Transportation Capital Expansion Fee Increase Effective` / `October 1, 2026` | `h2_both`; each line underlined | **No percent** in heading — preserved |
| TCEF body | Colorado Construction Cost Index; CDOT; since 1998; `new traffic generating development` | P2 crops | **Preserve** unhyphenated `traffic generating` |
| Reading order | Letterhead → H1 → P1 → H2 → P2 | Full page | Native order matches visual (unlike multi-column fee schedules) |
| Line wrap points | Six lines each body paragraph as in candidate | Pass1 wrap map + crops | Agreement |
| Signatures / memo date / fee tables | none in candidate | none on image | Agreement |
| Packaging markers | `===== PHYSICAL PDF PAGE 1 OF 1 =====` | not printed | Packaging only |
| Printed effective dates | July 1, 2026 / October 1, 2026 | Present | Printed only; `legal_currentness: not_verified` |

## 8. Completion statement

- **Page 1 of 1** was inspected against the image in **Pass 1** (frozen blind transcript) and again in **Pass 2** (candidate vs image + crops).
- Candidate SHA-256 **verified** as `5d8cbcad2b5c8dd72c8ba4092358607c78041a80457a56e7adac82e52bc1a768`.
- PASS1_frozen SHA-256 **unchanged** at `a4c4a3102cdd29e01402e80df4a35dac13cafcaf2809a26720bf45866cabd09a` (not edited).
- PASS1_FREEZE_RECEIPT SHA-256 **unchanged** at `5ce23f28d5f51770f34f50514c200803d67093c946dbd0bed5054032794897f8`.
- Status: `completed_pending_atlas_verification`.
- `legal_currentness: not_verified`.
- **No critical** findings. Substantive wording, dates, percentages, table IDs, and source anomalies agree with the image; findings are minor whitespace/layout notes plus residual apostrophe Unicode uncertainty.
- **Stop after EB-PDF-011** for this document; EB-PDF-012 is excluded (no candidate).

---
END PASS2
