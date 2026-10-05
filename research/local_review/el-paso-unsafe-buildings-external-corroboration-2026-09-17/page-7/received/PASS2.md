# PASS2 — EB-PAGE7-2026-09-17-02 (candidate vs Pass1; Pass1 unchanged)

assignment_id: EB-PAGE7-2026-09-17-02
attempt_id: EB-PAGE7-2026-09-17-02_20260917T204914Z
scope: physical_page_7_only
pass2_utc: 2026-09-17T20:54:18Z
review_method: caption_mediated
legal_currentness: not_verified
visual_verification: pending_atlas_direct_image_review
candidate_method: PyMuPDF 1.28.2 native (unchanged per packet)
candidate_path: 02-candidate/candidate.txt
candidate_sha256: ea2b28f7025e5a834be08f164d039dfb5541aae40395d2ff7899cf687ffed493
pass1_frozen_path: PASS1_frozen.md
pass1_frozen_sha256: ccdcc1c3102bdf1d25f8beaa997b171b036c294f7f62c17e7be104799c95c6cb
pass1_modified_after_freeze: false

## Comparison summary

Candidate is a damaged extraction of page 7. Legal structure (§§11.1–11.3, Section 12 / 12.1–12.3, Section13 Safety Clause, Section14 Severability Clause heading) is recognizably present, but mid-§11.2 is corrupted into non-text glyph garbage, and multiple missing-space and character-substitution anomalies appear elsewhere. Errata classify **extraction anomalies** (candidate vs Pass1 source reading). Pass1 is not rewritten.

## Critical

### C1 — §11.2 mid-paragraph catastrophic corruption
- **Pass1:** continuous prose: "If the owner fails to pay the cost of securing or removal within ten (10) calendar days after the Director mails an invoice for such cost, the whole cost thereof, including five percent (5%) for inspection and incidental costs in connection therewith, may be assessed upon the lot, parcel or tract…"
- **Candidate:** after "or otherwise. If" inserts multi-line mojibake / control-like glyphs (e.g. `thP f'\ltnPr…`, `ua..........`, `l.11..... .IJIJ. .....'-'LVI`) before recovering near "mails an invoice…"
- **Class:** extraction anomaly (PyMuPDF). Candidate unusable as literal transcript for that span.

### C2 — §11.2 five-percent glyph damage
- **Pass1:** `five percent (5%)`
- **Candidate:** `five percent ( 5~/o)` (space inside parens; `~/o` for `%`)
- **Class:** extraction anomaly.

## High / material

### H1 — Missing spaces (pattern)
Candidate glues words Pass1 reads as spaced, including: `ofthis`→`of this`; `ofthe`→`of the` (multiple); `Ifa`→`If a`. Also mid-word line breaks in §12.3 (`w`/`arrant`, `i`/`ssued`).

### H2 — §11.1 Section 4.9 parenthetical spacing
- **Pass1:** `Section 4.9 (2)(c)`
- **Candidate:** `Section 4.9 (2)( c )`
- **Class:** extraction anomaly (absolute source spacing still UNCERTAIN pending Atlas).

### H3 — §11.2 punctuation before "may be assessed"
- **Pass1:** `therewith, may be assessed`
- **Candidate:** `therewith; may be assessed`
- **Class:** extraction anomaly vs caption-mediated Pass1.

### H4 — §11.2 `parcel` corruption
- **Pass1:** `parcel`
- **Candidate:** `p3_rcel`
- **Class:** extraction anomaly.

### H5 — §11.3 ten percent digit confusion
- **Pass1:** `ten percent (10%)`
- **Candidate:** `ten percent (I0%)` (capital I for 1)
- **Class:** extraction anomaly.

### H6 — Letter substitutions / OCR-like damage in §11.3 and §12.2
Examples (candidate → Pass1): `generai`→`general`; `inciuding`→`including`; `arid`→`and`; `propert"y`→`property`; `assessn1ents`→`assessments`; `tJ1is`→`this`; `factuai`→`factual`; `reasonabiy`→`reasonably`; `buiiding`→`building`.

## Medium / formatting

### M1 — Apostrophe in Attorney's / Attorney’s
Pass1 froze typographic `Attorney’s` (UNCERTAIN curly vs straight). Candidate uses straight `Attorney's`. Not scored as Pass1 error.

### M2 — Section13 / Section14 spacing (AGREEMENT)
Both report `Section13:` / `Section14:` with no space after "Section". Shared reading; still UNCERTAIN vs true glyphs pending Atlas.

### M3 — Section 12 heading (AGREEMENT)
Both: `Section 12: Administrative Entry and Seizure Warrant.`

### M4 — Candidate banner
`=== PHYSICAL PDF PAGE 7 ===` is extraction wrapper, not ordinance text.

### M5 — Soft wraps / trailing spaces
Candidate hard-wraps mid-sentence; Pass1 uses paragraph prose. Formatting-only.

## Agreements (material)

- Structure of 11.1, recoverable 11.2, 11.3, 12.1–12.3, Safety Clause body, Severability heading-only on page 7.
- Deadlines/amounts when not corrupted: 10 calendar days (invoice); 5% (when not `5~/o`); 30 calendar days; 10% (when not `I0%`); 10 calendar days (warrant execution); first-class mail; El Paso County Treasurer; Colorado tax-collection cross-ref.
- Safety Clause citizens of El Paso County, Colorado — agreement.
- Section14 body absent on page 7 (heading only) — agreement.

## Method limits

Caption-mediated Pass1 cannot claim pixel-final glyphs; Atlas direct-image review remains authoritative for UNCERTAIN items (Section13/14 spacing, apostrophe form, exact 4.9 parenthetical spaces). Candidate §11.2 damage is independently severe.

## Counts

- critical: 2 (C1, C2)
- high/material: 6 (H1–H6)
- medium/formatting: 5 (M1–M5)
- Pass1 post-freeze edits: 0

## End PASS2
