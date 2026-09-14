# PASS1_frozen — EB-PDF-017

- assignment_id: EB-PDF-017
- source_id: greeley-water-sewer-proposed-pif-notice-sd008-08
- authority_id (collection context only): CO-MUNICIPAL-GREELEY
- reviewer: Ebenezer (Grok Bot) / executor Grok Bot
- pass: 1
- review_method: caption_mediated_source_first
- visual_verification: pending_atlas_direct_image_review
- legal_currentness: not_verified
- prior_candidate_exposure: none (candidate / 02-candidate-text / 03-custody / 04-verification / full packet manifest / PREPARATION_RECEIPT / validator / prior Atlas-Sherlock-Ebenezer analyses / 015–016 materials not opened)
- utc_start: 2026-09-12T22:16:06Z
- expected_pages: 2
- inspected_pages: 2 (full-page PNG representations + region crops; caption-mediated only)
- printed_identity (brief): City of Greeley Water and Sewer — Notice of Changes in Plant Investment Fees to Weld County homebuilders/contractors (notice dated November 20, 2020; fee schedule effective March 1, 2021)
- image_method: Cursor Read tool on complete source-page files `page-0001.png` and `page-0002.png`, plus Pillow region crops re-Read via the same tool. No OCR as Pass-1 substitute. No native PDF text extraction. `original.pdf` was not present in the workdir; its SHA-256 was taken only from `SOURCE_ONLY_IDENTITIES.json` (file bytes not hashed locally).
- captions_assistance: ASSISTED. (1) User/chat message included pre-supplied `image_description` blocks for both pages before tool Reads. (2) Every Read of a PNG returned a caption/mediated description, not raw pixel access to the reviewer. Captions treated as non-authoritative assisted claims. Caption internals (possible OCR/model interpretation) unknown. Never labeled as direct pixel inspection or blind visual transcription.
- packet_manifest_sha256 (bound; file not opened): dcb4565ae9a3ce007f7a96e0fcc74cd6ebe8664b435cb1a278d8a75a2f152397
- activation_sha256 (ACTIVATION.md verified): fc9f78bbdc4a9d416ab946bb435de96957cc3d5a748d2063e912eea1d350e3de
- SOURCE_ONLY_IDENTITIES_sha256 (verified): 29ea8ec18e6343e66bff79e6786eba26eb37dbdd09e7bed61fc4a5f26ea9afd5
- original_pdf_sha256 (from identities only; PDF absent from workdir): edfd4eecc57657bec922b8e0e63597fbf2fc957936d8f26a1a457b195dac145c

## Page image SHA-256 (verified before transcription)

| file | sha256 | size_bytes (workdir) |
|------|--------|----------------------|
| page-0001.png | b0b7286c93903ef7e290b155d2b0e7aec29873bbb026933fb8553f9fcb1112c5 | 503504 |
| page-0002.png | e3c95387f25424a5620ed74dcbeacc657aaab5310f8b299f214d483ff8368d82 | 174573 |

Page dimensions (Pillow, not visual): both 2550×3300 px.

## Coverage table

| physical_page | file | printed_page_label (tool-reported) | method | source representation received | unviewed_or_unresolved |
|---------------|------|--------------------------------------|--------|--------------------------------|-------------------------|
| 1 | page-0001.png | none reported (letter page; no page number in captions) | caption_mediated_source_first; full-page Read + crops: header/logo, heading, body, signoff, footer | mediated full-page + crop captions | Exact logo geometry/colors beyond caption; exact Unicode of bullet separators in footer; inch-mark / quote glyphs on any sizes if present; handwritten signature presence confirmed absent by caption but not pixel-verified; serif vs other typeface claims are caption assertions; margins/whitespace not exhaustively mapped |
| 2 | page-0002.png | none reported (schedule page; no page number in captions) | caption_mediated_source_first; full-page Read + crops: header, left tap-size table, right SFR table, lower blank | mediated full-page + crop captions | Exact table border geometry; whether blank lower half has faint marks beyond “uniform white” caption; exact inch-mark / quote Unicode on tap sizes (3/4", 1", etc.); whether $ appears only on first data rows (caption-consistent but not pixel-verified); any footnotes/notes below tables (captions report none; unchecked beyond caption); font family claims conflict across captions (serif vs sans-serif) → unresolved |

## Typography / layout notes (global; caption-reported)

- Page 1: formal letterhead with centered City of Greeley logo (navy “City of” / “Greeley”; tan/gold “Colorado”; navy cowboy-hat line art; tan/gold mountain/wave flourishes); centered date; centered all-caps notice heading; left-aligned body; closing/signature block without handwritten signature (caption); footer contact line above thin rule; motto below rule.
- Page 2: three-line centered all-caps header; two side-by-side bordered tables in upper portion; large blank lower region (crop caption: uniform white).
- No strike-through, insertions, deletions, or handwriting reported in any caption.
- legal_currentness: not_verified — notice/adoption/effective dates and fee amounts are transcribed as printed claims only; not treated as currently adopted law.

---

## Page 1 — Notice letter

**Printed label:** none (tool-reported)

**Visual (caption-reported):** White page; centered logo; centered date and all-caps heading; left-aligned letter body; signature block; footer with contact line, horizontal rule, motto.

**Transcribed text (reading order; caption-mediated):**

[logo text, approximate layout]
```
City of
Greeley
Colorado
```
[graphic: stylized navy cowboy hat + tan/gold mountain/wave flourishes — geometry/colors pending Atlas pixel review]

```
November 20, 2020
```

```
NOTICE OF CHANGES IN PLANT INVESTMENT FEES
TO WELD COUNTY HOMEBUILDERS, BUILDING CONTRACTORS,
AND PLUMBING CONTRACTORS
```

```
Dear Homebuilder/Contractor:
```

```
The Water and Sewer Board will be reviewing updated plant investment fees for adoption at its December 16, 2020 board meeting. These changes will become effective on March 1, 2021, assuming they are adopted. A copy of the new plant investment fee schedule is printed on the reverse side of this notice.
```

```
The Water and Sewer Department welcomes your questions and can assist you in planning upcoming projects. Please call the Water and Sewer Department (350-9801) for more specific fee information.
```

```
Sincerely,

Erik Dial
Utility Finance Manager
Greeley Water and Sewer
```
[no handwritten signature reported in caption]

[footer contact line — separator glyph shown as bullet; exact code point unresolved]
```
Water and Sewer Department • 1100 10th Street, Suite 300, Greeley, CO 80631 • (970) 350-9811 Fax (970) 350-9805
```
[thin horizontal rule]

```
A City Achieving Community Excellence
```

**Notes / anomalies preserved:**
- Body phone uses local form `(350-9801)`; footer uses `(970) 350-9811` and Fax `(970) 350-9805` — both preserved as printed; no normalization.
- Text refers to schedule on the “reverse side” (consistent with expected_pages: 2).
- Notice date Nov 20, 2020; board meeting Dec 16, 2020; assumed effective Mar 1, 2021 if adopted.

---

## Page 2 — Plant investment fee schedule

**Printed label:** none (tool-reported)

**Visual (caption-reported):** Centered three-line header; left table (tap size); right table (single-family residential); remainder largely blank white.

**Transcribed text (reading order; caption-mediated):**

```
CITY OF GREELEY
WATER AND SEWER PLANT INVESTMENT FEES
EFFECTIVE MARCH 1, 2021
```
[caption also reports partial horizontal rules under header with a center gap — geometry pending Atlas review]

### Table A (left) — Plant Investment Fees (PIFs) Based on Tap Size

| Water Tap Size | Water PIF | Sewer PIF |
| :--- | ---: | ---: |
| 3/4" | $11,200 | $6,800 |
| 1" | 18,700 | 11,400 |
| 1-1/2" | 37,300 | 22,800 |
| 2" | 59,700 | 36,400 |
| 3" | 130,700 | 79,700 |
| 4" | 223,900 | 136,700 |
| 6" | 466,500 | 284,800 |

Caption-consistent formatting notes (not pixel-verified): column headers bold; numeric PIF columns right-aligned; dollar sign `$` shown on first data row only; subsequent rows use thousands commas without repeating `$`. Inch-mark / quote glyph Unicode on tap-size column unresolved (shown here as ASCII `"`).

### Table B (right) — Plant Investment Fees (PIFs) Single Family Residential Units

Title (caption): `Plant Investment Fees (PIFs) Single Family Residential Units`

| (blank header cell) | Water PIF | Sewer PIF |
| :--- | ---: | ---: |
| Single Family - 3/4" | $11,200 | $6,800 |

**Notes / anomalies preserved:**
- SFR row amounts match the 3/4" tap-size row in Table A (both $11,200 / $6,800) — preserved; no arithmetic check performed.
- No footnotes, notes, or additional tables reported below these two tables; lower page crop caption reports uniform white — still marked unchecked for faint marks pending Atlas direct image review.
- Header order recorded as printed: CITY OF GREELEY → WATER AND SEWER PLANT INVESTMENT FEES → EFFECTIVE MARCH 1, 2021.

---

## Unchecked / unresolved (summary)

1. All glyph-level Unicode (bullets `•`, inch marks/quotes on tap sizes, dashes, spaces) — unresolved code points retained as visible-mark placeholders where shown.
2. Exact logo artwork geometry and color values.
3. Exact table ruling, cell padding, and numeric alignment.
4. Whether `$` omission on rows 2–7 is typographic convention or caption omission — captions consistently claim first-row-only `$`.
5. Page 2 lower blank region: caption says featureless white; not pixel-verified for faint content.
6. Font family conflict across captions (serif vs sans-serif on page 2) — unresolved.
7. `original.pdf` bytes not present in `/workspace/geode-017/`; integrity of PDF file not locally re-hashed (identity SHA only).
8. No printed page numbers reported; physical-page markers in any later candidate packaging are packaging, not source-transcription errors (Atlas note acknowledged; candidate not opened).
9. legal_currentness: not_verified.

## Sealed materials confirmation

Not opened before this freeze: candidate / `02-candidate-text`, `03-custody`, `04-verification`, full custody-bearing packet manifest, PREPARATION_RECEIPT, validator, prior reviews, EB-PDF-015/016 work products. Opened only: ACTIVATION.md (hash-verified), SOURCE_ONLY_IDENTITIES.json (hash-verified), page-0001.png, page-0002.png, and derived crops under `crops/`.
