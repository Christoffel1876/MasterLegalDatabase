# PASS2_REVIEW — EB-PDF-017

- assignment_id: EB-PDF-017
- source_id: greeley-water-sewer-proposed-pif-notice-sd008-08
- authority_id (collection context only): CO-MUNICIPAL-GREELEY
- reviewer: Ebenezer (Grok Bot) / executor Grok Bot
- pass: 2 (candidate vs caption-mediated page representations vs frozen Pass 1)
- review_method: caption_mediated_source_first
- visual_verification: pending_atlas_direct_image_review
- legal_currentness: not_verified
- utc_pass2_start: 2026-09-12T22:18:05Z
- utc_candidate_release: 2026-09-12T22:18:12Z
- utc_pass2_end: 2026-09-12T22:20:42Z
- expected_pages: 2
- inspected_pages_pass2: 2
- pass1_pages_inspected: 2
- status: completed_pending_atlas_verification
- prior_candidate_exposure_at_pass1_freeze: none
- candidate_opened_pass2: yes (after SHA verify; post-freeze only)
- custody_opened: false
- verification_opened: false
- materials_015_016_opened: false
- full_packet_manifest_opened: false
- last_authorized_document: true (stop after EB-PDF-017; no 018)

## Integrity checks (Pass 2 start)

| asset | expected SHA-256 | observed | match |
|-------|------------------|----------|-------|
| candidate.txt | b1bbe00ab454ec987faa397abd811b5981fe7ffb05f1d9b20ee0932f10e12ef8 | b1bbe00ab454ec987faa397abd811b5981fe7ffb05f1d9b20ee0932f10e12ef8 | yes |
| PASS1_frozen.md | 7bde39eda5b4042f21a43ac90759d7d6fc5659e8d8c5fd1db48f001d631c2643 | 7bde39eda5b4042f21a43ac90759d7d6fc5659e8d8c5fd1db48f001d631c2643 | yes (untouched) |
| PASS1_FREEZE_RECEIPT.json | 09f730535facc1639608132f7ccce7c5873ab0fae9fbb08fad7e938ba28b2eff | 09f730535facc1639608132f7ccce7c5873ab0fae9fbb08fad7e938ba28b2eff | yes (untouched) |
| PASS1_NOTES.md | 7281e862de45bb81a816770e4cc363fbbda9ed09c739ff5c6d81bacf075c9e9e | 7281e862de45bb81a816770e4cc363fbbda9ed09c739ff5c6d81bacf075c9e9e | yes (untouched) |
| page-0001.png | b0b7286c93903ef7e290b155d2b0e7aec29873bbb026933fb8553f9fcb1112c5 | same | yes |
| page-0002.png | e3c95387f25424a5620ed74dcbeacc657aaab5310f8b299f214d483ff8368d82 | same | yes |
| ACTIVATION.md | fc9f78bbdc4a9d416ab946bb435de96957cc3d5a748d2063e912eea1d350e3de | same | yes |
| SOURCE_ONLY_IDENTITIES.json | 29ea8ec18e6343e66bff79e6786eba26eb37dbdd09e7bed61fc4a5f26ea9afd5 | same | yes |
| packet_manifest (bound) | dcb4565ae9a3ce007f7a96e0fcc74cd6ebe8664b435cb1a278d8a75a2f152397 | bound via Pass1 / SOURCE_ONLY_IDENTITIES (full custody-bearing packet not opened) | bound |
| original.pdf (bound) | edfd4eecc57657bec922b8e0e63597fbf2fc957936d8f26a1a457b195dac145c | not present under /workspace/geode-017/; SHA from identities/Pass1 only | bound_not_rehashed_locally |

Candidate nature (per activation): `machine_native_text_unreviewed`, PyMuPDF 1.28.2 `Page.get_text("text", sort=False, flags=195)`. Native bytes/order/Unicode/line breaks preserved. Physical-page markers are **packaging**, not source text. Candidate not presumed correct.

## Method / disclosure

- Reinspected both full-page PNGs via Cursor Read (caption-mediated); re-read Pass1 crops (`p1_header_logo`, `p1_heading`, `p1_body`, `p1_signoff2`, `p1_footer`, `p2_header`, `p2_table_tap`, `p2_table_sfr`, `p2_lower_blank`); created additional Pass2 crops (`p2pass_p1_footer_tight`, `p2pass_p1_body_phone`, `p2pass_p2_tables_band`, `p2pass_p2_header_rules`).
- Compared `candidate.txt` to caption-reported source representations and to `PASS1_frozen.md` (frozen; not modified).
- **Caption-mediation disclosure:** ASSISTED. (1) Chat pre-supplied `image_description` blocks for both pages. (2) Every Read of a PNG returned a mediated caption, not raw pixels to the reviewer. Captions non-authoritative; internals unknown. Never labeled direct pixel inspection or blind visual transcription. Chat descriptions are not substitute quotations.
- Notable caption conflict handled: one signoff crop caption alleged lowercase `water and Sewer` in the body call-to-action; full-page, body crop, Pass1, and candidate all show `Water and Sewer Department` — false caption rejected.
- No OCR-as-substitute; no native PDF text extraction; no network/source research; no 03-custody / 04-verification / EB-PDF-015/016 work products opened.
- legal_currentness: **not_verified** — notice/adoption/effective dates and fee amounts are printed claims only.

## Coverage table (Pass 2)

| physical_page | file | printed_label (tool-reported) | pass2 inspection | both_passes |
|---------------|------|-------------------------------|------------------|-------------|
| 1 | page-0001.png | none | full-page Read + Pass1 crops + Pass2 footer/body-phone crops | yes |
| 2 | page-0002.png | none | full-page Read + Pass1 crops + Pass2 tables-band/header-rules crops | yes |

Assisted procedure covered both expected physical pages in both passes → status `completed_pending_atlas_verification` (does **not** mean glyphs/regions were pixel-verified).

## Discrepancy table (candidate vs source representation)

Findings use IDs `EB017-P2-NNN`. Severity: **critical** = wrong operative fee/date/party wording or spurious page-attributed text not supported by source representation; **minor** = omissions of chrome/graphics, reading-order/linearization, formatting/spacing packaging; **info** = agreements, preserved source anomalies, packaging markers, rejected false captions.

| ID | source_sha256 (page) | phys | label | location | candidate wording | source-supported / notes | error_type | severity |
|----|----------------------|------|-------|----------|-------------------|--------------------------|------------|----------|
| EB017-P2-001 | b0b7286c…1112c5 | 1 | (none) | letterhead logo | (logo wordmark absent from candidate body) | Caption-reported logo text `City of` / `Greeley` / `Colorado` + navy cowboy-hat / tan-gold wave graphic | omission_graphic_text | minor |
| EB017-P2-002 | b0b7286c…1112c5 | 1 | (none) | footer contact line | (absent) | `Water and Sewer Department • 1100 10th Street, Suite 300, Greeley, CO 80631 • (970) 350-9811 Fax (970) 350-9805` (bullet separators caption-reported; exact Unicode unresolved) | omission_footer_chrome | minor |
| EB017-P2-003 | b0b7286c…1112c5 | 1 | (none) | footer motto below rule | (absent) | `A City Achieving Community Excellence` below thin horizontal rule | omission_footer_motto | minor |
| EB017-P2-004 | e3c95387…368d82 | 2 | (none) | side-by-side tables | Titles then left headers then right headers then left first row + SFR row interleaved, then remaining left rows | Visual: two bordered tables side-by-side; native extract linearizes left/right — associations of labels→amounts remain correct when read carefully | reading_order_side_by_side_tables | minor |
| EB017-P2-005 | e3c95387…368d82 | 2 | (none) | column header / tap column | `Water` / newline / `Tap Size`; `    2"` with leading spaces | Source shows single header cell `Water Tap Size`; `2"` without material leading-space semantics | extract_line_split_spacing | minor |
| EB017-P2-006 | both | 1–2 | — | many lines | Trailing spaces and multi-blank-line runs | Native extract packaging; not treated as printed wording errors | whitespace_packaging | minor |
| EB017-P2-007 | e3c95387…368d82 | 2 | (none) | table chrome | Plain amounts/headers | Caption: first data row and headers bold; table grid borders present — plain-text extract omits bold/ruling | formatting_bold_borders_omitted | minor |
| EB017-P2-008 | both | 1–2 | — | rules / logo art | (graphics omitted) | Thin footer rule; page-2 table borders / header-adjacent rule(s); logo artwork — expected native omission | omission_non_text_graphics | minor |
| EB017-P2-009 | both | 1–2 | — | extract wrappers | `===== PHYSICAL PDF PAGE N OF 2 (PACKAGING MARKER) =====` | Packaging only; **not** source-transcription errors (Atlas note) | packaging_marker | info |
| EB017-P2-010 | e3c95387…368d82 | 2 | (none) | all PIF amounts | `$11,200`/`$6,800`; `18,700`/`11,400`; `37,300`/`22,800`; `59,700`/`36,400`; `130,700`/`79,700`; `223,900`/`136,700`; `466,500`/`284,800`; SFR `$11,200`/`$6,800` | All match Pass1 and caption-mediated table crops | agreement_fee_amounts | info |
| EB017-P2-011 | e3c95387…368d82 | 2 | (none) | `$` placement | `$` on first tap-size row and SFR row only | Caption-consistent first-row-only `$` on left table; SFR row has `$` | agreement_dollar_convention | info |
| EB017-P2-012 | b0b7286c…1112c5 | 1 | (none) | phones | Body `(350-9801)` present; footer `(970) 350-9811` / Fax `(970) 350-9805` absent | Source anomaly: local body form vs full footer form — both printed; candidate retains body only because footer omitted (see 002) | source_anomaly_phone_forms | info |
| EB017-P2-013 | e3c95387…368d82 | 2 | (none) | SFR vs 3/4" | Same `$11,200` / `$6,800` | Source shows matching amounts — preserved; no arithmetic check performed | source_anomaly_or_equivalence_preserved | info |
| EB017-P2-014 | b0b7286c…1112c5 | 1 | (none) | signature gap | Printed `Erik Dial` / title / org; no ink signature string | Captions report gap after `Sincerely,` and no handwritten signature | agreement_no_handwritten_signature | info |
| EB017-P2-015 | b0b7286c…1112c5 | 1 | (none) | body call line | `Please call the Water and Sewer Department (350-9801)…` | Reject signoff-crop caption claiming lowercase `water and Sewer`; Pass1/body/full-page/candidate agree on `Water` | caption_false_positive_rejected | info |
| EB017-P2-016 | b0b7286c…1112c5 | 1 | (none) | notice body | Nov 20, 2020; Dec 16, 2020 meeting; Mar 1, 2021 assumed effective; reverse-side schedule; heading to Weld County homebuilders/contractors; Erik Dial block | Agrees with Pass1 and body/heading crops | agreement_letter_body | info |
| EB017-P2-017 | both | 1–2 | — | document status | (n/a) | Printed notice/schedule dates ≠ verified current adopted law | legal_currentness_not_verified | info |

### Counts

- critical: **0**
- minor: **8** (EB017-P2-001 … 008)
- info: **9** (EB017-P2-009 … 017)
- unresolved themes (below): **7** (not double-counted as critical/minor)

## Errata vs Pass 1 (separate table; PASS1_frozen unchanged)

| erratum | Pass1 original | Pass2 revised interpretation | basis |
|---------|----------------|------------------------------|-------|
| E1 | Footer contact + motto transcribed with bullet separators; body vs footer phone forms preserved | Affirm Pass1 wording; add that **candidate omits entire footer** (findings 002–003) — not a Pass1 wording error | Pass2 footer crops + candidate absence of `1100 10th` / motto |
| E2 | Body: `Water and Sewer Department (350-9801)` | Affirm; reject alien signoff-crop caption lowercase `water` | Body/full-page captions + candidate |
| E3 | Page-2 font family conflict (serif vs sans-serif) unresolved | Remains unresolved; no Pass1 operative change | Conflicting Pass2 crop captions continue |
| E4 | “partial horizontal rules under header with a center gap” (caption) | Soften: exact header/table-top rule geometry still **unresolved**; Pass2 crops emphasize table top border / continuous rule — do not treat “center gap” as settled | Header-rules vs tables-band caption nuance |

No Pass1 **operative fee amounts**, notice dates, party names, or table row associations require wording revision.

## Source anomalies / preserved features (not “fixes”)

1. Body phone `(350-9801)` vs footer `(970) 350-9811` / Fax `(970) 350-9805` — both printed forms; do not normalize.
2. SFR row amounts equal 3/4" tap-size row amounts — preserved; no arithmetic validation claimed.
3. Left-table `$` on first data row only (caption-consistent).
4. Notice is proposed/assuming adoption as of the letter text — not treated as certified current law (`legal_currentness: not_verified`).

## Unresolved regions / glyphs

1. Exact Unicode code points for footer bullets, inch-mark/quote glyphs on tap sizes, dashes/spaces.
2. Exact logo artwork geometry and color values (caption hex approximations non-authoritative).
3. Exact table ruling, cell padding, numeric alignment.
4. Page-2 font family (serif vs sans-serif caption conflict).
5. Page-2 lower blank region: crop caption reports uniform white; not pixel-verified for faint marks.
6. `original.pdf` bytes absent from workdir — identity SHA only; not locally re-hashed.
7. Exact page-2 header underline / table-top rule geometry (Pass1 “center gap” vs Pass2 continuous-border captions).

## Pass1 agreement summary

- Page-1 notice letter body, dates, heading, salutation, Erik Dial block: **agree**.
- Page-2 header order CITY OF GREELEY → WATER AND SEWER PLANT INVESTMENT FEES → EFFECTIVE MARCH 1, 2021: **agree**.
- All seven tap-size rows and SFR row fee amounts: **agree**.
- Candidate omissions of logo/footer/motto are extract gaps relative to Pass1 source transcription, not Pass1 errors.
- PASS1_frozen.md / PASS1_FREEZE_RECEIPT.json re-hashed unchanged at Pass2 start and again at completion binding.

## Binding hashes (inputs)

- packet_manifest_sha256 (bound): dcb4565ae9a3ce007f7a96e0fcc74cd6ebe8664b435cb1a278d8a75a2f152397
- activation_sha256: fc9f78bbdc4a9d416ab946bb435de96957cc3d5a748d2063e912eea1d350e3de
- original_pdf_sha256 (bound): edfd4eecc57657bec922b8e0e63597fbf2fc957936d8f26a1a457b195dac145c
- candidate_sha256: b1bbe00ab454ec987faa397abd811b5981fe7ffb05f1d9b20ee0932f10e12ef8
- PASS1_frozen_md_sha256: 7bde39eda5b4042f21a43ac90759d7d6fc5659e8d8c5fd1db48f001d631c2643
- PASS1_FREEZE_RECEIPT_sha256: 09f730535facc1639608132f7ccce7c5873ab0fae9fbb08fad7e938ba28b2eff
- page-0001.png: b0b7286c93903ef7e290b155d2b0e7aec29873bbb026933fb8553f9fcb1112c5
- page-0002.png: e3c95387f25424a5620ed74dcbeacc657aaab5310f8b299f214d483ff8368d82

## Chronology note

Reported UTC times are wall-clock observations from the executor environment. Filesystem mtimes are not independent proof of blind order or completion. Pass1 freeze preceded candidate open; Pass2 reinspected both pages after candidate SHA verify.
