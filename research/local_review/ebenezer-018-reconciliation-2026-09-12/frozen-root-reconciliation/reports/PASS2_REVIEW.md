# PASS2_REVIEW — EB-PDF-018

- assignment_id: EB-PDF-018
- source_id: weld-building-fees-sd008-01
- authority_id (collection context only): CO-COUNTY-WELD
- reviewer: Ebenezer (Grok Bot) / executor Grok Bot
- pass: 2 (candidate vs caption-mediated page representations vs frozen Pass 1)
- review_method: caption_mediated_source_first
- visual_verification: pending_atlas_direct_image_review
- legal_currentness: not_verified
- utc_pass2_start: 2026-09-12T22:40:27Z
- utc_candidate_release: 2026-09-12T22:40:40Z
- utc_pass2_end: 2026-09-12T22:43:15Z
- expected_pages: 5
- inspected_pages_pass2: 5
- pass1_pages_inspected: 5
- status: completed_pending_atlas_verification
- prior_candidate_exposure_at_pass1_freeze: none
- candidate_opened_pass2: yes (after SHA verify; post-freeze only)
- custody_opened: false
- verification_opened: false
- materials_019_020_opened: false
- full_packet_manifest_opened: false
- stop_after_note: finite queue continues to 019/020 only under separate Atlas dispatch; this Pass2 does not open 019/020

## Integrity checks (Pass 2 start)

| asset | expected SHA-256 | observed | match |
|-------|------------------|----------|-------|
| candidate.txt | 3c00b78086a8d596f4a86afa677cd8507ccf471f58fd5cde9bd730d96d25ef51 | 3c00b78086a8d596f4a86afa677cd8507ccf471f58fd5cde9bd730d96d25ef51 | yes |
| PASS1_frozen.md | 7bdbb994023df7e3ab4b475d1a58b0b7e76409a78231f43ea61bb69378029158 | 7bdbb994023df7e3ab4b475d1a58b0b7e76409a78231f43ea61bb69378029158 | yes (untouched) |
| PASS1_FREEZE_RECEIPT.json | 0eae0da5c6e1937fae4fa996b9740da36ea4c08f147e31ad4c1f133a29245eb7 | 0eae0da5c6e1937fae4fa996b9740da36ea4c08f147e31ad4c1f133a29245eb7 | yes (untouched) |
| PASS1_NOTES.md | 4c7ab7c7e62fad7bd435cffae467f9b7fb5e48d18e22e33cfee9d3571eb03694 | 4c7ab7c7e62fad7bd435cffae467f9b7fb5e48d18e22e33cfee9d3571eb03694 | yes (untouched) |
| page-0001.png | f5f9b05d556c781e76a2174164f6df455916bc4e127614a257c0f20367774f80 | same | yes |
| page-0002.png | ae113eca8434b9144915b8b1edd3f3ab9e2356a6a4e3c1a47df0ef1d9aaecbaa | same | yes |
| page-0003.png | 8a5ec2d214f29331bfb13300b220a0e96304b32e147899ecdb6b070200ad8283 | same | yes |
| page-0004.png | 03423d98ce2a996f97622dbf75215a6a94e49ebecea093b3fff16c427182ddf9 | same | yes |
| page-0005.png | 3b6ec39274b6a80f162312d6fe555608570cad8274cf0b7874ec090f620856fe | same | yes |
| START_HERE.md | 142ca7e336f197d3636f362f3044e5a6f716c11950817e38daeefc996b5b948a | same | yes |
| SOURCE_ONLY_IDENTITIES.json | 1c07c1b39db7798b0fea34c224fe7d06beecb6bac5ab77fbf549ce25674b5564 | same | yes |
| MANIFEST_SHA256.txt content (opaque digest) | b9e843e783a65a238d1a7e1106a5d0a49ea08f7ffbb59b9ca02d841e7639a112 | same | yes |
| packet_manifest (bound) | b9e843e783a65a238d1a7e1106a5d0a49ea08f7ffbb59b9ca02d841e7639a112 | bound via MANIFEST_SHA256.txt / Pass1 (full custody-bearing packet not opened) | bound |
| original.pdf (bound) | 8fb5dc78f67407a22857160f107a0253da42320e9e502387be573ef53cab9f27 | not present under /workspace/geode-018/; SHA from identities/Pass1 only | bound_not_rehashed_locally |

Candidate nature (per START_HERE): `machine_native_text_unreviewed`, PyMuPDF 1.28.2 `Page.get_text("text", sort=False, flags=195)`. Native bytes/order/Unicode/line breaks preserved. Physical-page markers are **packaging**, not source text. Candidate not presumed correct.

## Method / disclosure

- Reinspected all five full-page PNGs via Cursor Read (caption-mediated); re-read Pass1 crops (`p1_title`, `p1_table`, `p1_lower`, `p2_top`, `p2_demo_drainage`, `p3_tiers`, `p3_footer`, `p4_*` bands/notes, `p5_header`, `p5_road`, `p5_facilities_drain`); created Pass2 crops (`p2pass_p1_plan_review`, `p2pass_p2_facilities`, `p2pass_p3_other_insp`, `p2pass_p4_s_rows`).
- Compared `candidate.txt` to caption-reported source representations and to `PASS1_frozen.md` (frozen; not modified).
- **Caption-mediation disclosure:** ASSISTED. (1) Chat pre-supplied `image_description` blocks for all five pages. (2) Every Read of a PNG returned a mediated caption, not raw pixels to the reviewer. Captions non-authoritative; internals unknown. Never labeled direct pixel inspection or blind visual transcription.
- Rejected one cut-off crop caption that paraphrased the Drainage footnote differently from full-page/Pass1/candidate agreement (`streets or driveways` / `right-of-way`).
- No OCR-as-substitute; no native PDF text extraction; no network/source research; no 03-custody / 04-verification / EB-PDF-019/020 materials opened.
- legal_currentness: **not_verified** — printed fee schedule dates and amounts are transcription claims only.

## Coverage table (Pass 2)

| physical_page | file | printed_label (tool-reported) | pass2 inspection | both_passes |
|---------------|------|-------------------------------|------------------|-------------|
| 1 | page-0001.png | none | full-page Read + Pass1 crops + Pass2 plan-review crop | yes |
| 2 | page-0002.png | none | full-page Read + Pass1 crops + Pass2 facilities crop | yes |
| 3 | page-0003.png | footer `Revised 012/25` | full-page Read + tiers/footer crops + Pass2 other-inspections crop | yes |
| 4 | page-0004.png | none | full-page Read + Pass1 band/notes crops + Pass2 S-row crop | yes |
| 5 | page-0005.png | none | full-page Read + Pass1 road/facilities-drain crops | yes |

Assisted procedure covered all five expected physical pages in both passes → status `completed_pending_atlas_verification` (does **not** mean glyphs/regions were pixel-verified).

## Discrepancy table (candidate vs source representation)

Findings use IDs `EB018-P2-NNN`. Severity: **critical** = wrong operative fee/date/party wording or spurious page-attributed text not supported by source representation; **minor** = omissions of chrome/graphics, reading-order/linearization, formatting/spacing packaging; **info** = agreements, preserved source anomalies, packaging markers.

| ID | source_sha256 (page) | phys | label | location | candidate wording | source-supported / notes | error_type | severity |
|----|----------------------|------|-------|----------|-------------------|--------------------------|------------|----------|
| EB018-P2-001 | 8a5ec2d2…8283 | 3 | footer Revised 012/25 | NOTE box vs footer order | `Revised 012/25` appears **before** NOTE paragraph in extract | Visual/caption: NOTE double-border box above; footer bottom-right below box. Native extract reading-order only | reading_order_footer_before_note | minor |
| EB018-P2-002 | 8a5ec2d2…8283 | 3 | (none) | Other Inspections last line | `…approved plans.$80.00 per hour` (no space after period) | Crop/full captions: fee abuts `plans.` without leader; candidate preserves abutment | source_spacing_preserved_not_error | info |
| EB018-P2-003 | ae113eca…cbaa | 2 | (none) | Demolition dwelling amount | `$80..00` | Full-page + demo crop: double period `$80..00` — candidate matches source anomaly | agreement_source_anomaly | info |
| EB018-P2-004 | 8a5ec2d2…8283 | 3 | (none) | Cost-of-job third tier | `$40,0001 to $60,000` … `$571.69` | Full-page + tiers crop: `$40,0001` — candidate matches | agreement_source_anomaly | info |
| EB018-P2-005 | 8a5ec2d2…8283 | 3 | Revised 012/25 | footer | `Revised 012/25` | Footer crop confirms literal `012/25` — candidate matches | agreement_source_anomaly | info |
| EB018-P2-006 | 3b6ec392…56fe | 5 | (none) | Road Hotel/Motel Room | `$2401` (no thousands comma) | Road crop + full-page: `$2401` vs other four-digit fees with commas — candidate matches | agreement_source_anomaly | info |
| EB018-P2-007 | ae113eca…cbaa / 3b6ec392…56fe | 2 / 5 | (none) | Facilities SFD amount forms | p2 `$1636.00`; p5 `$1,636` | Pass2 facilities crop confirms p2 **no comma**; p5 road/facilities captions confirm **with comma**. Digits 1636 agree; punctuation differs by page — both preserved in candidate | agreement_cross_page_comma_variance | info |
| EB018-P2-008 | f5f9b05d…4f80 | 1 | (none) | valuation table body | `$1027.00` / `$3827.00` / `$6327.00`; row-2 end `$2000` | Captions: same no-comma bases / `$2000` end-phrase — candidate matches | agreement_page1_fees | info |
| EB018-P2-009 | 03423d98…ddf9 | 4 | (none) | valuation grid cells | All sampled rows/cells incl. N.P., Oil and gas sites*, R-1 hotels, S-2 lowercase storage, U Utility 66.20 | Match Pass1 and caption-mediated table; associations label→IA…VB preserved despite line-broken extract | agreement_page4_table | info |
| EB018-P2-010 | 03423d98…ddf9 | 4 | (none) | table extract shape | Use-group then nine values as successive lines | Harmless native linearization of grid; not wrong associations | reading_order_table_linearization | minor |
| EB018-P2-011 | both | 1–5 | — | wrappers | `===== PHYSICAL PDF PAGE N OF 5 (PACKAGING MARKER) =====` | Packaging only; **not** source-transcription errors | packaging_marker | info |
| EB018-P2-012 | both | 1–5 | — | leaders / whitespace | Long runs of `…` / `.` leaders; trailing spaces; multi-blank lines | Native extract packaging; leader-dot counts not claimed | whitespace_leader_packaging | minor |
| EB018-P2-013 | f5f9b05d…4f80 / 8a5ec2d2…8283 | 1 / 3 | — | table header / NOTE box | Plain text only | Black header row white text; double-border grey NOTE box — chrome omitted from plain extract | omission_formatting_chrome | minor |
| EB018-P2-014 | 3b6ec392…56fe | 5 | (none) | some Road “sq. ft” tails | Office / Warehouse lines without trailing `.` after `ft` in candidate; other lines with `ft.` | Captions inconsistently report trailing period; glyph-level unresolved — do not treat as confirmed fee-wording error | uncertain_trailing_period | minor |
| EB018-P2-015 | ae113eca…cbaa | 2 | (none) | County Facilities SFD line | `All new single family dwellings.` then leaders then `$1636.00` | Period after `dwellings` before leaders appears in candidate; captions emphasize amount form more than the period — minor/uncertain punctuation packaging | uncertain_period_before_leaders | minor |
| EB018-P2-016 | both | 1–5 | — | underlines / borders / leaders as graphics | (omitted as graphics) | Underlined Chapter 20 headers; table rules; leaders as visual chrome — expected native omission beyond text glyphs extracted | omission_non_text_graphics | minor |
| EB018-P2-017 | both | 1–5 | — | document status | (n/a) | JANUARY 2026 / Revised 012/25 / fee amounts ≠ verified current adopted law | legal_currentness_not_verified | info |
| EB018-P2-018 | f5f9b05d…4f80 | 1 | (none) | Minor Plan Review | `$80.00` (single decimal) | Plan-review crop confirms `$80.00` — distinct from demolition `$80..00` | agreement_minor_plan_review | info |
| EB018-P2-019 | 3b6ec392…56fe | 5 | (none) | Agricultural Commercial (Road) | label embeds `1,000 sq. ft` then fee `… per 1,000 sq. ft.` | Road crop confirms label includes unit text — candidate preserves | agreement_ag_commercial_label | info |
| EB018-P2-020 | ae113eca…cbaa | 2 | (none) | Electrical / Road / Drainage operative lines | Residential tiers; valuation tiers to `$50,000`; Construction Meter `$43.00`; Road SFD `$3,794.00`; Drainage `$0.22` | Agree with Pass1 and captions; fuller electrical prose in candidate than Pass1 summary — consistent with source captions | agreement_page2_operative | info |

### Counts

- critical: **0**
- minor: **7** (EB018-P2-001, 010, 012, 013, 014, 015, 016)
- info: **13** (EB018-P2-002, 003, 004, 005, 006, 007, 008, 009, 011, 017, 018, 019, 020)
- unresolved themes (below): **8** (not double-counted as critical/minor)

## Errata vs Pass 1 (separate table; PASS1_frozen unchanged)

| erratum | Pass1 original | Pass2 revised interpretation | basis |
|---------|----------------|------------------------------|-------|
| E1 | Other Inspections plan-review line transcribed with spaced leaders: `plans ..... $80.00` | Source/candidate abutment form `plans.$80.00` (no leader / no space after period) is better supported | p3_tiers + p2pass_p3_other_insp + candidate L144 |
| E2 | Page-2 County Facilities SFD caption variance `$1636.00` vs `$1,636.00` left unresolved | Prefer **`$1636.00` without comma** on page 2; page 5 remains `$1,636` with comma | p2pass_p2_facilities + full page-2 Read; p5 crops |
| E3 | Full-page caption once suggested `.$80.00` leading-dot fee forms on first three Other Inspections lines | Treat as leader-dot mis-segmentation; fees are `$80.00` after leaders (single decimal) — not `.$80` anomaly | p2pass_p3_other_insp / p3_tiers |
| E4 | Pass1 summary shortened electrical “other fees” prose | Affirm candidate’s longer native prose as matching fuller captions; Pass1 was condensation, not contradictory | page-2 full Read vs candidate L105–107 |

No Pass1 **operative fee amounts** (other than punctuation/spacing refinements above), tier associations, or Chapter 20 category→amount mappings require substantive numeric revision. Frozen Pass1 file not modified.

## Source anomalies / preserved features (not “fixes”)

1. Demolition dwelling amount `$80..00` (double period) — preserved in candidate.
2. Cost-of-job tier start `$40,0001` — preserved.
3. Footer `Revised 012/25` — preserved literally.
4. Road Impact Hotel/Motel Room `$2401` (no comma) — preserved.
5. Facilities SFD `$1636.00` (p2, no comma) vs `$1,636` (p5, with comma) — both preserved.
6. Valuation bases `$1027.00` / `$3827.00` / `$6327.00`; row-2 end-phrase `$2000` — preserved.
7. S-2 label lowercase `storage` vs S-1 `Storage` — preserved.
8. Agricultural Commercial Road label embeds `1,000 sq. ft.` — preserved.
9. `plans.$80.00` abutment on Other Inspections last line — preserved.
10. legal_currentness: not_verified.

## Unresolved regions / glyphs

1. Exact Unicode for leader dots, dashes/en-dashes, underline weight.
2. Exact table border geometry / black header fill / NOTE double-border grey shade.
3. Page-5 trailing period after some `sq. ft` strings (Office/Warehouse vs others).
4. Whether period after page-2 `dwellings` before leaders is printed punctuation or extract artifact.
5. Individual page-4 cell kerning/alignment at glyph level (values agree at caption level).
6. `original.pdf` bytes absent from workdir — identity SHA only; not locally re-hashed.
7. Exact printed page numbers (none reported in captions).
8. All glyph-level / pixel-level verification pending Atlas direct image review.

## Pass1 agreement summary

- Page-1 title, JANUARY 2026, eight valuation tiers, manufactured fees, Major 70% / Minor `$80.00`: **agree**.
- Page-2 Road `$3,794.00`, Facilities `$1636.00`, Drainage `$0.22`, Premove `$230.00`, Demolition `$80..00`, electrical tiers: **agree**.
- Page-3 cost-of-job tiers incl. `$40,0001`, Other Inspections `$80.00/hr`, investigation/NOTE text, `Revised 012/25`: **agree** (order of footer vs NOTE is extract-only).
- Page-4 full valuation matrix + notes: **agree** (sampled all rows via captions/crops).
- Page-5 Chapter 20 Road/Facilities/Drainage schedules incl. `$2401` and `$1,636`: **agree**.
- PASS1_frozen.md / PASS1_FREEZE_RECEIPT.json re-hashed unchanged at Pass2 start.

## Binding hashes (inputs)

- packet_manifest_sha256 (bound): b9e843e783a65a238d1a7e1106a5d0a49ea08f7ffbb59b9ca02d841e7639a112
- START_HERE_sha256: 142ca7e336f197d3636f362f3044e5a6f716c11950817e38daeefc996b5b948a
- original_pdf_sha256 (bound): 8fb5dc78f67407a22857160f107a0253da42320e9e502387be573ef53cab9f27
- candidate_sha256: 3c00b78086a8d596f4a86afa677cd8507ccf471f58fd5cde9bd730d96d25ef51
- PASS1_frozen_md_sha256: 7bdbb994023df7e3ab4b475d1a58b0b7e76409a78231f43ea61bb69378029158
- PASS1_FREEZE_RECEIPT_sha256: 0eae0da5c6e1937fae4fa996b9740da36ea4c08f147e31ad4c1f133a29245eb7
- page-0001.png: f5f9b05d556c781e76a2174164f6df455916bc4e127614a257c0f20367774f80
- page-0002.png: ae113eca8434b9144915b8b1edd3f3ab9e2356a6a4e3c1a47df0ef1d9aaecbaa
- page-0003.png: 8a5ec2d214f29331bfb13300b220a0e96304b32e147899ecdb6b070200ad8283
- page-0004.png: 03423d98ce2a996f97622dbf75215a6a94e49ebecea093b3fff16c427182ddf9
- page-0005.png: 3b6ec39274b6a80f162312d6fe555608570cad8274cf0b7874ec090f620856fe

## Chronology note

Reported UTC times are wall-clock observations from the executor environment. Filesystem mtimes are not independent proof of blind order or completion. Pass1 freeze (`utc_freeze` 2026-09-12T22:39:15Z) preceded candidate open; Pass2 reinspected all five pages after candidate SHA verify.
