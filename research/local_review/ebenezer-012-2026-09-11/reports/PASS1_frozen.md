# PASS 1 — Independent Visual Transcription (FROZEN)

## 1. Metadata

| Field | Value |
| :--- | :--- |
| assignment_id | EB-PDF-012 |
| source_id | larimer-data-center-moratorium-sd004-04 |
| expected_pages | 2 |
| utc_start | 2026-09-11T18:47:51Z |
| utc_freeze | 2026-09-11T18:51:58Z |
| packet (batch-3) manifest SHA-256 | 86431bd0f0c252bf845d4749131dc5adfc54e618dee76294473d1ad9e6cb75d6 (assignment-supplied; local packet file not present in `/workspace/geode-012/`; not independently hashed this pass) |
| original.pdf SHA-256 | d5de580139ba20bb5e80b4226b583ebc033eef693884dedeff0a8dddcfe3696c (assignment-supplied; independently confirmed by hashing `/workspace/geode-discovery-007/raw/recorded-resolution-establish-temporary-moratorium-data-center-facilities-larimer-county-colorado.pdf` only — PDF text **not** extracted; PDF not used as transcription source) |
| page-0001.png SHA-256 | 178199b0e8546d8b1a743b780875b66ecad7b5d87067d888a8e41c331ca42464 |
| page-0002.png SHA-256 | 13b1c95d918ed6bf268bd48c5ed05d04e67508392bb59f76630324ff55d6bfba |
| candidate SHA (withheld) | f8fcdc8faee762730ba8c09498b6458f42b17681256f30c5bbf6d32d14872981 (assignment-supplied; file **not opened**, not hashed from disk this pass) |
| reviewer | Ebenezer (Grok Bot) |
| model | unknown |
| auth_packet | EBENEZER_NEXT_PACKET_012_2026-09-11 |
| prior_candidate_exposure | none |
| prior_atlas_sherlock_consultation | none for this document |
| legal_currentness | not_verified |
| pass | PASS1_frozen (blind visual transcription only) |
| status | pass1_frozen_pending_pass2 |

## 2. Access / hash verification

| Asset | Expected SHA-256 | Observed SHA-256 (this pass) | Match |
| :--- | :--- | :--- | :--- |
| page-0001.png | 178199b0e8546d8b1a743b780875b66ecad7b5d87067d888a8e41c331ca42464 | 178199b0e8546d8b1a743b780875b66ecad7b5d87067d888a8e41c331ca42464 | YES |
| page-0002.png | 13b1c95d918ed6bf268bd48c5ed05d04e67508392bb59f76630324ff55d6bfba | 13b1c95d918ed6bf268bd48c5ed05d04e67508392bb59f76630324ff55d6bfba | YES |
| original.pdf (discovery raw, hash-only) | d5de580139ba20bb5e80b4226b583ebc033eef693884dedeff0a8dddcfe3696c | d5de580139ba20bb5e80b4226b583ebc033eef693884dedeff0a8dddcfe3696c | YES |
| packet manifest.json | 86431bd0f0c252bf845d4749131dc5adfc54e618dee76294473d1ad9e6cb75d6 | not present in workdir | not independently hashed |

**Access scope (this pass):** Inspected only `/workspace/geode-012/page-0001.png` and `page-0002.png` (and Pillow crops derived from those PNGs). Read `PASS_1_PROMPT.md`. Hashed the matching source PDF path above without extracting text. Did **not** open, read, or hash from disk any `candidate.txt`, `02-candidate-text`, ocr-evidence, native extraction, Sherlock, Atlas, EB-PDF-010/011 materials, or discovery derived/HTML text of this resolution. Directory listing at start showed only `PASS_1_PROMPT.md`, `page-0001.png`, `page-0002.png`.

**Image geometry:** Both pages 2550×3300 px, RGB (letter 8.5×11 in at 300 dpi appearance).

## 3. Image-viewing method / caption-mediation disclosure

- Page images were inspected with the **Read** tool. Read returns **caption-mediated vision captions** (model-generated descriptions of the pixels). **Captions are NOT source quotations** and are **not** OCR output.
- The user-message attachments of the same two pages were also caption-mediated; those captions were **not** treated as source text.
- Captions can truncate, invent, or inject prior-conversation / metadata context. Examples this pass: a full-page caption invented a right-edge “..” near the page-1 folio that a tight crop showed as **blank**; captions sometimes rendered the stray tick as `i` or `/`. Glyph decisions below prefer **tight Pillow crops** of the pixels, with remaining conflicts marked **[UNCERTAIN]**.
- Dense legal lines, recording header, stray mark, handwritten date, signatures, and seal were **cropped with Pillow** and re-read via Read.
- Limitation: **not** certified full visual coverage equivalent to unaided pixel inspection. Typographic quotes, exact Unicode code points, justification spacing, and bullet glyph code points are **described**, not claimed as exact code points from raster.
- Printed names are transcribed from printed type. Handwriting / signature-mark presence is described separately; **signer identity is not inferred from adjacent printed office titles**.
- `legal_currentness: not_verified`. A filename, reception stamp, or `source_id` is not evidence that the moratorium is presently in force.

## 4. Full page-by-page verbatim transcript

Layout note: body appears fully justified serif; **WHEREAS** / title / resolving clause are bold. Recording banner is bold sans/serif smaller type at top left. Line breaks below follow visible wrapped lines as closely as raster allows; whitespace/dot-leaders are not counted.

### Page 1 (`page-0001.png`) — physical page 1 of 2

**Recording banner (top left, two lines, bold):**

```text
RECEPTION #20260005307, 2/5/2026 1:21:07 PM, 1 of 2, Electronically Recorded
Tina Harris, Clerk & Recorder, Larimer County, CO
```

**Centered title (bold, two lines, all caps):**

```text
RESOLUTION TO ESTABLISH A TEMPORARY MORATORIUM ON
DATA CENTER FACILITIES IN LARIMER COUNTY, COLORADO
```

**Body:**

**WHEREAS,** the Board of County Commissioners of the County of Larimer, State of Colorado, has
authority to plan for and regulate the use of land pursuant to the Local Government Land Use Control
Enabling Act, C.R.S. §29-20-101, *et seq.*; C.R.S. §30-11-101(2) concerning the adoption and
enforcement of resolutions and ordinances regarding health, safety and welfare issues as otherwise
prescribed by law; C.R.S. § 30-11-107 concerning powers of Boards of County Commissioners;
C.R.S. § 30-28-115 concerning the promotion of health, safety, convenience, order and/or welfare of
the community through land use regulations; and other applicable state and federal statutes and
common law grants of authority to best protect and promote the health, safety, and general welfare of
the present and future inhabitants of Larimer County, including but not limited to:

*(Citation spacing is inconsistent in the source: `§29-20-101` and `§30-11-101(2)` have **no** space after `§`; `§ 30-11-107` and `§ 30-28-115` **have** a space after `§`. `et seq.` appears italic. Serial-comma use is mixed: “health, safety and welfare” vs later “health, safety, and general welfare”.)*

Bullet list (filled circular bullets; `•` is a conventional stand-in, not a claimed code point):

- Regulating development and activities in hazardous areas;
- Protecting lands from activities which would cause immediate or foreseeable material
  danger to significant wildlife habitat and would endanger a wildlife species;
- Providing for phased development of services and facilities;
- Regulating the use of land on the basis of the impact of the use on the community or
  surrounding areas; and
- Otherwise planning for and regulating the use of land so as to provide planned and
  orderly use of land and protection of the environment in a manner consistent with
  constitutional rights.

**WHEREAS,** pursuant to C.R.S. section 30-28-121, the Board may promulgate temporary regulations
not to exceed six months, by resolution and without a public hearing, prohibiting or regulating in any
part of or all of the unincorporated territory of the county, structures used or to be used for any
business, residential, industrial or commercial purpose; and

*(This recital uses the word “section”, not `§`.)*

**WHEREAS,** there has been significant interest in developing data center facilities within Larimer
County, which are large-scale facilities designed to house computer systems and associated
components such as telecommunications and storage systems; and

**WHEREAS,** data center facilities can have significant impacts on infrastructure, including demands
on electrical power, water supply, telecommunications networks, and transportation systems, as well
as potential impacts on surrounding land uses, natural resources, public services, and the character of
the community; and

**WHEREAS,** the Larimer County Land Use Code does not currently contain specific regulations,
standards, or definitions addressing the unique characteristics and impacts of data center facilities; and

**WHEREAS,** the Board has determined that it is necessary to temporarily suspend acceptance of
applications for data center facilities while appropriate regulations, standards, and definitions can be
developed through a comprehensive public process involving the Planning Commission and the
Board; and

**[STRAY MARK — not part of the word sequence]** Small isolated glyph sitting **above the baseline** of the first line of this sixth WHEREAS, over the space between “that” and “it” in “determined that it is necessary”. Appearance: thin diagonal tick / prime / undotted italic *i*-like mark. Competing caption readings `i` vs `/`. **Unresolved as to intended character; transcribed as a stray overlay, not inserted into the sentence.**

**WHEREAS,** based on the information presented and provided, the Board has determined that a
temporary moratorium is necessary to ensure planned, orderly development of data center facilities
consistent with the character and welfare of Larimer County by enacting appropriate regulations; and

**Footer:** centered printed folio `1` near bottom margin. No printed page-2-style seal. No barcode observed. Tight crop of the far-right edge near the folio was blank (a full-page caption’s “..” there is **rejected**).

---

### Page 2 (`page-0002.png`) — physical page 2 of 2

**Recording banner (top left, two lines, bold):**

```text
RECEPTION #20260005307, 2/5/2026 1:21:07 PM, 2 of 2, Electronically Recorded
Tina Harris, Clerk & Recorder, Larimer County, CO
```

**WHEREAS,** Larimer County reserves the right to extend this moratorium if additional time is needed
to complete the regulatory process.

**Resolving clause (bold, two lines, all caps):**

```text
NOW, THEREFORE, BE IT RESOLVED BY THE BOARD OF COUNTY
COMMISSIONERS OF THE COUNTY OF LARIMER, STATE OF COLORADO THAT:
```

*(Comma after LARIMER; **no** comma between COLORADO and THAT. Trailing colon.)*

**Operative paragraph (justified):**

Larimer County shall not accept applications or engage in pre-submittal activities for data center
facilities, including but not limited to planning applications, building permits, engineering permits, or
other development applications related to data center facilities, shall be accepted or processed by the
Larimer County Planning and Community Development Department for a period of thirty (30) days
from the effective date of this resolution, or until appropriate definitions, standards and conditions can
be considered by the Planning Commission for adoption into the Larimer County Land Use Code and
adopted by the Board, whichever comes first, or unless further renewed or amended by separate action.

*(Source syntax preserved: “shall not accept … facilities, including …, shall be accepted or processed …”. Serial comma **absent** in “definitions, standards and conditions”.)*

**Definition paragraph:**

For purposes of this moratorium, a “data center facility” means a purpose-built structure, a substantial
modification to an existing structure, or an integrated group of structures that is designed and used
primarily to house computer servers, data storage systems, large scale digital data processing, and/or
networking equipment, and associated infrastructure including but not limited to cooling systems,
backup power systems, telecommunications facilities, and battery storage, sometimes referred to as
Digital Infrastructure Facilities, Industrial-Scale Computing Facilities, or High-Intensity Computing
Facilities typically operating on a scale requiring significant electrical power consumption, water
consumption and/or infrastructure support.

*(Typographic / curly double quotation marks around `data center facility` observed; exact Unicode not claimed. “large scale” is **unhyphenated**; “purpose-built”, “Industrial-Scale”, and “High-Intensity” **are** hyphenated.)*

This moratorium is effective in all of unincorporated Larimer County.

The Board will hold an open meeting to allow public comment on the merits of the temporary
moratorium imposed by this resolution and to determine whether the moratorium should be
terminated, extended, or otherwise amended. The hearing will be held on Monday, February 9, 2026
at 3:00 pm in the Board’s public Hearing Room, 1st Floor, 200 West Oak Street, Fort Collins,
Colorado 80522. Notice of this hearing shall be published in a newspaper of general circulation
in Larimer County at least 14 days prior to the hearing date.

*(“2026 at 3:00 pm”: **no** comma after the year. “pm” lowercase. “1st” has a superscript ordinal *st*. “Board’s” uses a typographic apostrophe. “Hearing Room” initial-capped.)*

This resolution shall be effective as of the date of signature and shall expire on thirty days thereafter,
unless continued pursuant to statute.

*(Wording preserved: “shall expire **on** thirty days thereafter”.)*

**Date line (printed + handwriting):**

Printed: `DATED THIS DAY,`

**[HANDWRITING — not printed]** Ink on/after the printed phrase, underlined in part. Best visual reading: **January 27, 2026**. Competing reading **January 27, 202.6** because the final digit is detached after a period-like mark / underline terminus following `202`. The leading `J` loop extends upward into the line above (“statute.”). **Do not treat either reading as a certified date of execution.**

**Board block (printed, all caps):**

```text
THE BOARD OF COUNTY COMMISSIONERS
LARIMER COUNTY, COLORADO
```

**Chair signature block:**

- Printed title under the line: `Chair`
- **[SIGNATURE MARK PRESENT]** Ink over/above the line. Visual appearance of the ink (not taken from the printed title): resembles **Jody Shadduck-McNally** (hyphenated). **Not certified as signer identity.**

**Attest block:**

Printed: `ATTEST:`

- Printed title under the line: `Deputy County Clerk`
- **[SIGNATURE MARK PRESENT]** Ink over/above the line, with a long terminal cross-stroke. Handwriting **not fully resolved**. Competing visual readings of a given name beginning with J or K (resembling “Jenny” / “Kristin” / “Kristy”) and a surname with a prominent cross-bar (resembling “Frey” / similar). **Unresolved. Not certified as signer identity; not inferred from the printed office title.**

**Seal (printed circular device, center of signature row):**

- Outer cable/chain ring; inner dotted circle.
- Arc text: `LARIMER` (left) `COUNTY` (top) `CLERK` (right).
- Five-point stars at about 9 o’clock and 3 o’clock.
- Center: `SEAL` with paired dash-and-dot ornaments above and below.
- Bottom arc: `COLORADO`.
- Seal presence: **yes** (printed impression / graphic).

**Counsel block (right):**

Printed small caps/all-caps: `APPROVED AS TO FORM:`

- **[SIGNATURE MARK PRESENT]** Ink above a short line. Visual appearance uncertain; resembles **Frank** plus a short middle element and a surname resembling **Hay** (e.g. “Frank N. Hay” / “Frank n Hay”). **Unresolved. Not certified as signer identity.**
- Printed title under the line: `Assistant Deputy County Attorney`

**Footer:** No printed folio `2` observed at bottom center (unlike page 1’s `1`). Bottom dark pixels are the seal’s lower arc, not a page number.

## 5. Coverage table

| Page | File | Region | Inspected | Transcript attempted | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | page-0001.png | full page | YES | YES | Read + Pillow bands |
| 1 | | recording banner | YES | YES | Reception #, timestamp, 1 of 2 |
| 1 | | title | YES | YES | Two-line centered caps |
| 1 | | WHEREAS 1 + C.R.S. cites | YES | YES | § spacing mixed; *et seq.* italic |
| 1 | | 5 bullets | YES | YES | Filled discs |
| 1 | | WHEREAS 2–5, 7 | YES | YES | |
| 1 | | WHEREAS 6 + stray mark | YES | YES | Stray tick above “that it” |
| 1 | | folio `1` | YES | YES | Centered |
| 1 | | right-edge near folio | YES | blank | Caption “..” rejected |
| 2 | page-0002.png | full page | YES | YES | Read + Pillow bands |
| 2 | | recording banner | YES | YES | Same reception; 2 of 2 |
| 2 | | WHEREAS 8 | YES | YES | Extension reservation |
| 2 | | NOW THEREFORE clause | YES | YES | No comma before THAT |
| 2 | | operative 30-day paragraph | YES | YES | Syntax anomaly preserved |
| 2 | | definition | YES | YES | Curly quotes; hyphenation mix |
| 2 | | geographic effect | YES | YES | unincorporated Larimer County |
| 2 | | hearing notice | YES | YES | Feb 9, 2026; 1st Floor; 3:00 pm |
| 2 | | expire / dated | YES | YES | “on thirty days”; handwritten date |
| 2 | | board name | YES | YES | printed |
| 2 | | Chair ink vs printed Chair | YES | presence + visual reading | identity not certified |
| 2 | | Deputy Clerk ink | YES | presence; reading unresolved | identity not certified |
| 2 | | circular SEAL | YES | YES | LARIMER COUNTY CLERK / COLORADO |
| 2 | | APPROVED AS TO FORM ink | YES | presence; reading unresolved | identity not certified |
| 2 | | printed folio 2 | YES | none observed | |

## 6. Uncertainties / source anomalies (recorded before inference)

1. **Caption mediation** — captions are not source quotations; they hallucinated at least one right-edge mark.
2. **Stray glyph** on page 1 between “that” and “it” — tick / prime / undotted *i*; not inserted into the sentence. **[UNCERTAIN character]**
3. **§ spacing** mixed (`§29-20-101` / `§30-11-101(2)` vs `§ 30-11-107` / `§ 30-28-115`). Preserved.
4. **Serial commas** mixed across recitals vs operative “definitions, standards and conditions”. Preserved.
5. **Operative syntax** “shall not accept …, shall be accepted or processed”. Preserved; not repaired.
6. **Handwritten date** January 27, 2026 vs January 27, 202.6. **[UNCERTAIN]**
7. **Chair ink** resembles Jody Shadduck-McNally; **not certified**; printed word is only `Chair`.
8. **Deputy County Clerk ink** not resolved to a single spelling. **[UNCERTAIN]**
9. **Assistant Deputy County Attorney ink** not resolved to a single spelling. **[UNCERTAIN]**
10. **Typographic quotes / apostrophe / superscript `st` / bullet disc** — described, exact code points not claimed.
11. **No printed `2`** at page-2 footer (page 1 has `1`).
12. **legal_currentness: not_verified.** Reception 2/5/2026 and hearing date February 9, 2026 are transcribed as printed/stamped only.
13. **“shall expire on thirty days thereafter”** — “on” preserved.
14. **“large scale” vs “Industrial-Scale” / “High-Intensity”** hyphenation mix preserved.

## 7. Limitations

- Blind image-only pass. Candidate / native / OCR / Sherlock / Atlas / 010 / 011 not opened.
- Vision is caption-mediated even with crops.
- Handwriting identity is not authenticated.
- Packet manifest file was not on disk in the workdir for independent hashing.
- PDF opened only as a SHA-256 of bytes, not as a text source.
