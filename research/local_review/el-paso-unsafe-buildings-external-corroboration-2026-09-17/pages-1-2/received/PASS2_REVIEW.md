# PASS2_REVIEW — EB-PAGES-2026-09-17-01

assignment_id: EB-PAGES-2026-09-17-01
scope: physical_pages_1_2_only
pass1_frozen_sha256: 0ae3c17ebffde35dea6f4aaaaf95faffb656f38f4ad1f713eb3235ed655a533d
pass1_freeze_receipt_sha256: af0ec28114e0d78a4f5d043f21d05f3cd4eadc57972ca73405946b6f250e0f68
candidate_sha256: 1df3237486f55773f61aefe9d7ca605a1e8ca4617d4d525662a17b31002d57bf
candidate_path: candidate/candidate.txt
candidate_method: unchanged PyMuPDF native text; 1.28.2 (per MANIFEST)
utc_candidate_open: 2026-09-17T20:46:14Z
utc_pass2: 2026-09-17T20:46:48Z
review_method: caption_mediated_source_first then candidate compare
legal_currentness: not_verified
visual_verification: pending_atlas_direct_image_review
pass1_unchanged: true

## Method

- Pass1 was frozen and hashed **before** opening `02-candidate/candidate.txt`.
- Pass2 compares released candidate text to caption-mediated Pass1 / page images. Captions are not direct pixels.
- Source anomalies ≠ extraction errors. Packaging/recording headers in the candidate stream are not body source text.
- No Atlas/Plato priors consulted.

## Candidate exact text (released)

See `candidate/candidate.txt` (SHA-256 `1df3237486f55773f61aefe9d7ca605a1e8ca4617d4d525662a17b31002d57bf`). Summary of structure as released:

- Page-1 header: RESOLUTION NO. 17-321 / BOARD OF COUNTY COMMISSIONERS / COUNTY OF EL PASO, STATE OF COLORADO
- Title line as extracted: `RESOLUTION ADOPTING ORDINANCE N0. 18-03, REQUIRING THE REMOVAL OF UNSAFE BUILDINGS` (note `N0.` with digit zero in candidate bytes)
- Six WHEREAS blocks + NOW/BE IT RESOLVED + BE IT FURTHER RESOLVED naming **Darryl Glenn** / **Mark Waller**
- Embedded recording-line noise mid/end page-1: `Chuck Broerman 11/22/2017 09:11:15 AM Doc $0.00 8 Rec $0.00` plus barcode ASCII art
- Page-2 continuation + `DONE THIS 21ˢᵗ day o f November 2017, at Colorado Springs, Colorado.`
- Candidate page-2 **does not** carry the ATTEST / BOCC signature-block layout seen in Pass1 image captions

## Findings

### Critical (0)

None claimed at glyph-certified level (visual_verification still pending).

### Material / high (candidate extraction)

1. **Severe mid-paragraph fragmentation / garbage glyphs (p1 WHEREAS bodies):** Candidate inserts hard breaks and corrupted tokens such as `unincoroorated`, `Countv`, `uoon`, `adiacent`, `nearbv`, `orooerties`, and scattered letter-spaced runs (`t o C .R.S.`, `Bo ar d of`, etc.). Pass1 caption assembly did not show these as source wording. **Class: candidate extraction artifacts** (PyMuPDF native extract on scanned page), not source anomalies. Location: physical page 1, WHEREAS clauses. Impact: high — unusable as literal statute text without repair. Proposed source-supported correction: restore contiguous legal prose per source images (Atlas direct review for final glyphs).

2. **Title `N0.` (digit zero) vs `NO.` (letters):** Candidate title uses `ORDINANCE N0. 18-03`. Pass1 captions read `NO.` / ordinance **18-03**. **Class: likely candidate extraction error** (0/O confusion). Location: page 1 title. Impact: medium. Proposed correction: `ORDINANCE NO. 18-03` pending Atlas glyph check.

3. **Recording/packaging text merged into candidate page-1 body:** Candidate includes Clerk stamp lines / barcode ASCII (`Chuck Broerman 11/22/2017…`, `Doc $0.00`, `Rec $0.00`) inside the page-1 text stream after the FURTHER RESOLVED authorization. Pass1 treated the stamp as page furniture, not resolution prose. **Class: packaging/recording header in extract — not source body text.** Impact: medium (contaminates body). Proposed correction: segregate stamp to metadata; do not treat as resolution wording.

### Medium (Pass1 caption limits vs candidate)

4. **Authorized-signatory printed names:** Candidate reads **Darryl Glenn** (President) and **Mark Waller** (President Pro Tempore). Pass1 freeze left spellings **UNCERTAIN** due to conflicting captions (Darryl/Darryl; Mark/Mark). **Class: Pass1 caption uncertainty**, not a proven candidate error. Do not rewrite Pass1. Atlas direct image review should settle glyphs. Impact: medium for identity strings.

5. **Page-2 signature blocks absent from candidate:** Pass1 captions show ATTEST (Chuck Broerman / Clerk and Recorder + seal) and BOCC (Darryl Glenn / President) with `signature_present: yes`. Candidate page-2 ends at DONE line without those blocks. **Class: candidate omission / extract incompleteness** relative to image content. Impact: high for execution evidence. Proposed correction: supply signature-block text/layout from source images (Pass1 already notes signature≠printed-name identity).

6. **DONE line spacing/superscripts:** Candidate `DONE THIS 21ˢᵗ day o f November 2017` shows spaced `o f` and Unicode superscript digits. Pass1 captions: handwritten fills **21st** and **November** in `DONE THIS 21st day of November, 2017, at Colorado Springs, Colorado.` **Class: mixed** — handwritten fills are source; odd spacing/superscripts likely extract artifacts. Impact: low–medium.

### Low / source anomalies retained

7. **Handwritten “Bocc” (p1)** and handwritten date fills (p2): source features; not extraction errors.
8. **Recording stamp present on p1 image:** source feature; candidate’s merge into body is the error (see #3).
9. **Pass1 title caption conflict 18-02 vs 18-03:** Pass1 already flagged; candidate supports **18-03**. Still pending Atlas glyph confirmation. Not counted as candidate discrepancy.

### Reclassification note

Pass1 under-literalism / caption compression on long WHEREAS strings is a **Pass1 method limit**, not a candidate defect. Candidate fullness with garbage tokens is **not** authority to rewrite Pass1.

## Errata (separate; Pass1 unchanged)

| # | Candidate text (excerpt) | Proposed source-supported correction | Page / locus | Uncertainty | Impact |
|---|---|---|---|---|---|
| E1 | fragmented WHEREAS / `unincoroorated` / `uoon` / `adiacent` / … | restore contiguous source prose | p1 WHEREAS | caption_mediated; atlas_pending | high |
| E2 | `ORDINANCE N0. 18-03` | `ORDINANCE NO. 18-03` | p1 title | atlas_pending | medium |
| E3 | Broerman stamp/barcode inside body stream | move to recording metadata only | p1 foot → wrongly inline | low on stamp content; medium on placement | medium |
| E4 | missing ATTEST/BOCC blocks | include from source images | p2 signature area | caption_mediated names | high |
| E5 | `day o f November` / `21ˢᵗ` | `day of November` / handwritten 21st | p2 DONE | low | low–medium |

## Overall judgment (caption-mediated)

Candidate is a damaged native extract of pages 1–2: useful for some headings/dates/names, unreliable for continuous legal prose, and incomplete on page-2 execution blocks. Pass1 remains the frozen source-first reading with explicit caption limits. `legal_currentness: not_verified`. `visual_verification: pending_atlas_direct_image_review`.

## Custody

- Pass1 / freeze receipt bytes unchanged after candidate open
- Original crop PNGs included under `crops/` (not regenerated histories)
- Scope remains pages 1–2 only; no next job
