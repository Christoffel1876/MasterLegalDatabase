# PASS2_REVIEW.md — EB-PDF-019
## Weld County Code Ordinance 2026-01 (weld-ordinance-26-01-atlas-directed)

```
assignment_id: EB-PDF-019
source_id: weld-ordinance-26-01-atlas-directed
authority_id: CO-COUNTY-WELD
expected_physical_pages: 5
reviewer: Ebenezer (Grok Bot)
workdir: /workspace/geode-019b/
pass2_utc_start: 2026-09-13T01:29:38Z
candidate_release_utc: 2026-09-13T01:29:45Z
pass2_utc_completion: 2026-09-13T01:32:00Z
review_method: caption_mediated_source_first
visual_verification: pending_atlas_direct_image_review
legal_currentness: not_verified
assistance_supplier_tool: Cursor Read (image file → caption/description mediation)
native_pdf_ocr_or_extraction_used_as_pass2_substitute: false
status: completed_pending_atlas_verification
```

---

## PRIOR-EXPOSURE & METHOD RE-DISCLOSURE (required for Pass 2)

This Pass 2 is **assisted** and **not** blind visual transcription. Direct pixel review was **not** performed.

| Field | Value |
|---|---|
| review_method | `caption_mediated_source_first` |
| visual_verification | `pending_atlas_direct_image_review` |
| prior_exposure_label | `fresh_attempt_after_interrupted_prior_pass1_with_no_surviving_artifacts` |
| interrupted_prior_pass1 | ~2026-09-12T22:43Z; usage-limit cancel; **no** surviving Pass1 artifacts |
| Pass1 frozen (this attempt) | Opened after gate; SHA `d2b2aabb572951f86c61743ad387db4bba3de7e2477e2424e6fe7fc9d97f080c` |
| candidate exposure | First opened this Pass 2 after Pass1 freeze + receipt + chat-hash gate |
| activating user-message image descriptions | Present in chat; treated as **non-authoritative**; Pass2 primary mediation is Cursor **Read** of `page-000N.png` + preserved Pass1 `tool_outputs/` captions |
| recollection contamination | Possible unreliable model recollection from interrupted attempt; comparison basis is caption mediation + candidate bytes only |
| never upgraded | Caption access is **not** claimed as direct image / pixel access |

**Physical-page markers** (`===== PHYSICAL PDF PAGE N OF 5 (PACKAGING MARKER) =====`) are **packaging**, not source-transcription errors.

---

## INTEGRITY BINDINGS (Pass 2 verified)

| Object | SHA-256 | Status |
|---|---|---|
| candidate.txt | `2ba00b91a33612e279a0553f5e573af795df27a11329d695ea307ea78ae2dfee` | **MATCH** expected |
| PASS1_frozen.md | `d2b2aabb572951f86c61743ad387db4bba3de7e2477e2424e6fe7fc9d97f080c` | **re-hash confirmed** |
| PASS1_FREEZE_RECEIPT.json | `97b96a99e29ca04960c6d55f1515ed7613ba57d770585e71c6d447488f290c76` | **re-hash confirmed** |
| PASS1_NOTES.md | `c4195bd8ab1f70ab22db1061edcdbbae5a8f6626fda56c74b580163eb9a5f374` | **re-hash confirmed** |
| START_HERE.md | `35f5dbb4104c1cea73084fa3939228c91a7caf1339540a4033e431849122924f` | verified |
| data-manifest digest (opaque) | `b9e843e783a65a238d1a7e1106a5d0a49ea08f7ffbb59b9ca02d841e7639a112` | verified |
| original.pdf (declared) | `2ba9073aa06420e41a5dce98fade56278df96729630f5d61d3ab1c910e839eb0` | declared only; **absent** from workdir |
| page-0001.png | `04de77358b0830d989a14995a09d0fee7fcab3a0adf4286d5f95fc8aa53cb4b6` | verified |
| page-0002.png | `09f6709e45bbba5e2a34515de406679ab4d6bdacf18e1e66e20dde111520bdc7` | verified |
| page-0003.png | `f025c5a7ebd938459ffa7e4840f4d0f9f9cde092d6964da64f1913ffcad94846` | verified |
| page-0004.png | `68fab481ae6e9d7cd758bdc1912befa322505a8575f38eb3dea84ce5131021c3` | verified |
| page-0005.png | `468e7ed723a4a2609eda3b30db46daf7696637a9e8e11c1c6635560800cee5ef` | verified |

Candidate status (per START_HERE): `machine_native_text_unreviewed` (PyMuPDF 1.28.2, `Page.get_text("text", sort=False, flags=195)`). Not presumed correct.

---

## PAGE COVERAGE LOG (Pass 2 reinspection)

| Physical page | File | Printed label (tool-reported) | Pass2 representation | Method |
|---:|---|---|---|---|
| 1 | page-0001.png | **Not reported** (no Final Reading / Page 1) | Pass1 caption + Pass2 fresh Read | caption_mediated_source_first |
| 2 | page-0002.png | Final Reading / Page 2 | Pass1 caption + Pass2 fresh Read | caption_mediated_source_first |
| 3 | page-0003.png | Final Reading / Page 3 | Pass1 caption + Pass2 fresh Read | caption_mediated_source_first |
| 4 | page-0004.png | Final Reading / Page 4 | Pass1 caption + Pass2 fresh Read | caption_mediated_source_first |
| 5 | page-0005.png | Final Reading / Page 5 | Pass1 caption + Pass2 fresh Read | caption_mediated_source_first |

All five expected pages rechecked under the declared assisted method (including regions where Pass1 and candidate agree). Footer IDs `2026-0765` / `ORD2026-01` reported on all five pages (bottom right on source; near page-block top in candidate linearization).

Pass2 tool notes: `/workspace/geode-019b/tool_outputs/pass2/page-000N_pass2_reinspect.md`

---

## FINDINGS TABLE

Finding IDs: `EB019-P2-NNN`. Severity: **critical** = real wording/association error vs caption-supported source; **minor** = packaging/linearization/typography/omitted graphic; **informational** = source anomaly preserved / agreement note; **unresolved** = cannot settle from captions.

### EB019-P2-001 — Packaging page markers (not source errors)
| Field | Value |
|---|---|
| physical_page | 1–5 |
| printed_label | n/a (packaging) |
| region | candidate page delimiters |
| candidate_wording | `===== PHYSICAL PDF PAGE N OF 5 (PACKAGING MARKER) =====` / `===== END PHYSICAL PDF PAGE N ... =====` |
| source_supported | Not printed body text; extraction packaging |
| category | packaging_marker |
| severity | minor (harmless packaging) |
| visual_explanation | Per assignment rules, physical-page markers are packaging, not source-transcription errors. |

### EB019-P2-002 — Footer linearization order
| Field | Value |
|---|---|
| physical_page | 1–5 |
| printed_label | pages 2–5: Final Reading / Page N; page 1: none reported |
| region | footer identifiers `2026-0765` / `ORD2026-01` |
| candidate_wording | Footers appear near the **top** of each candidate page block (after packaging marker) |
| source_supported (caption) | Footers at **bottom right** |
| category | harmless_linearization |
| severity | minor |
| visual_explanation | PyMuPDF text order moves margin/footer tokens; wording of IDs matches captions. |

### EB019-P2-003 — Source anomaly "I. though T." preserved
| Field | Value |
|---|---|
| physical_page | 2 |
| printed_label | Final Reading / Page 2 |
| region | Sec. 23-2-160 application list, item I–T span |
| candidate_wording | `I. though T. - No change.` |
| source_supported (caption) | Same: `I. though T.` (Pass1 caption, Pass2 Read, activating description all report "though") |
| category | source_anomaly_preserved (not a candidate error) |
| severity | informational |
| visual_explanation | Apparent source typo ("though" vs expected "through"). Candidate correctly preserves reported source wording. Atlas may confirm glyph. |

### EB019-P2-004 — Weld County seal graphic omitted from candidate
| Field | Value |
|---|---|
| physical_page | 5 |
| printed_label | Final Reading / Page 5 |
| region | right of vote tally |
| candidate_wording | *(no seal / graphic text)* |
| source_supported (caption) | Circular Weld County seal present (1861; wheat/gear/livestock motifs — exact inventory caption-variable) |
| category | omitted_graphic |
| severity | minor |
| visual_explanation | Expected for machine-native text extraction; not a wording substitution. Seal presence remains for Atlas pixel review. |

### EB019-P2-005 — Possible spacing after "12." before DATA CENTERS (conflicting captions)
| Field | Value |
|---|---|
| physical_page | 4 |
| printed_label | Final Reading / Page 4 |
| region | Sec. 23-3-330 item 12 |
| candidate_wording | `12. DATA CENTERS.` (space after period) |
| source_supported | Pass2 Read: space present (agrees with candidate). Activating-message description claimed `12.DATA CENTERS.` without space. Pass1 caption had space. |
| category | uncertain_glyph_or_spacing |
| severity | unresolved |
| visual_explanation | Caption conflict; no direct pixels. Do not treat as confirmed candidate error. |

### EB019-P2-006 — *Greeley Tribune* italicization / typography
| Field | Value |
|---|---|
| physical_page | 5 |
| printed_label | Final Reading / Page 5 |
| region | Publication timeline lines |
| candidate_wording | plain `Greeley Tribune` |
| source_supported | Some captions mention italicization of newspaper name; exact italic vs roman **not** claimable from captions |
| category | typography_unverified |
| severity | unresolved |
| visual_explanation | Typography/Unicode styling not authenticated by caption mediation. |

### EB019-P2-007 — Signatures / attestation ink vs printed facsimile
| Field | Value |
|---|---|
| physical_page | 5 |
| region | Approved as to Form / Attest blocks |
| candidate_wording | Printed names: Bruce Barker, County Attorney; Esther E. Gesick, Clerk to the Board |
| source_supported | Labels confirmed; handwriting vs printed signature images **not** pixel-verified |
| category | mark_presence_unresolved |
| severity | unresolved |
| visual_explanation | Do not infer wet-ink authorship from nearby printed labels. |

### EB019-P2-008 — Page 1 "Final Reading" / page number header absence (agreement)
| Field | Value |
|---|---|
| physical_page | 1 |
| region | top-left header |
| candidate_wording | No `Final Reading` / `Page 1` lines |
| source_supported | Pass1 + Pass2 captions likewise omit any Page 1 Final Reading header |
| category | agreement_note |
| severity | informational |
| visual_explanation | Consistent candidate↔caption agreement; Atlas should still confirm no omitted header. |

### EB019-P2-009 — Substantive ordinance text agreement (DATA CENTER core)
| Field | Value |
|---|---|
| physical_pages | 1–5 |
| region | definition; noise 65 dB(C); water/will-serve; I-1/I-2/I-3 placements; timeline; votes |
| candidate_wording | See candidate.txt (DATA CENTER definition; 65 dB(C) at property boundary in 23-2-160 U.1 and 23-2-250 A; C.R.S. 29-20-301 water; electricity will-serve; DATA CENTERS as I-1 USR item 5 / I-2 SPR item 9 / I-3 SPR item 12; adoption 2026-04-06; effective 2026-04-15; Chair Nay / four Ayes) |
| source_supported | Pass2 captions agree on these substantive points |
| category | agreement_substantive |
| severity | informational |
| visual_explanation | No caption-supported wording conflict found for these core terms. Pending Atlas pixel verification. |

### EB019-P2-010 — Line-wrap hyphenation in citation (Section 14-9-40)
| Field | Value |
|---|---|
| physical_page | 3 |
| region | Sec. 23-2-250 A noise clause |
| candidate_wording | `Section 14-` then newline `9-40` |
| source_supported | Captions present continuous `Section 14-9-40` |
| category | extraction_linewrap |
| severity | minor |
| visual_explanation | Harmless PDF text wrap; not a changed citation. |

### EB019-P2-011 — Quotation style on “will serve”
| Field | Value |
|---|---|
| physical_pages | 2, 3 |
| region | electricity will-serve letter requirements |
| candidate_wording | curly/smart quotes `“will serve”` |
| source_supported | Captions likewise show curly quotes |
| category | agreement_punctuation |
| severity | informational |
| visual_explanation | Candidate quote style consistent with caption reports; exact Unicode code points still pending Atlas. |

---

## COUNTS

| Severity | Count |
|---|---:|
| critical | **0** |
| minor | **4** (P2-001 packaging; P2-002 footer order; P2-004 omitted seal; P2-010 linewrap) |
| informational | **4** (P2-003 source typo; P2-008 header absence; P2-009 substantive agreement; P2-011 quotes) |
| unresolved | **3** (P2-005 spacing 12.; P2-006 italics; P2-007 signatures) |

**No critical candidate wording/association errors** were established under caption mediation.

---

## PASS1 ERRATA TABLE (separate; frozen PASS1 unchanged)

| Errata ID | Pass1 location | Original Pass1 reading | Pass2 revised / clarified reading | Basis |
|---|---|---|---|---|
| EB019-P1E-001 | Page 3 top / 23-2-240 continuation | Pass1 stated page-3 caption **begins** at Amend Sec. 23-2-250 and marked leading `Remainder of Section – No change` for 23-2-240 as **UNRESOLVED** / possibly omitted | Pass2 fresh Read **does** report leading `Remainder of Section – No change.` before Amend Sec. 23-2-250; **candidate includes the same line** | Pass2 Read of page-0003.png; candidate.txt lines 84–85 |
| EB019-P1E-002 | Page 1 Whereas / ordaining | Marked `[caption-paraphrase]`; exact sentences unchecked | Pass2 Read supplies near-full Whereas + Now-therefore quotes that **align with candidate** | Pass2 Read page-0001; candidate lines 9–20 |
| EB019-P1E-003 | Page 2 Sec. 23-2-160 lead | Paraphrased as preapplication conference only | Candidate + Pass2 purpose language include written/graphic demonstration of Chapter compliance; consistent with Pass2 caption | Pass2 Read page-0002; candidate lines 46–50 |
| EB019-P1E-004 | Page 3 Sec. 23-2-260 E.1/3/5/6 | Marked unchecked / not quoted | Pass2 confirms: `1. - No change.`; `3. - No change.`; `5. and 6. - No change. Insert new 7.` matching candidate | Pass2 Read page-0003; candidate lines 101–107 |
| EB019-P1E-005 | Page 4 I-1 F. lead | Pass1 paraphrase used “established” | Candidate/Pass2: `constructed, occupied, operated and maintained` | Pass2 Read page-0004; candidate lines 123–126 |
| EB019-P1E-006 | Page 3 23-2-250 preamble | Caption-paraphrase only in Pass1 | Pass2 near-quote matches candidate preamble | Pass2 Read page-0003; candidate lines 86–90 |

Frozen `PASS1_frozen.md` bytes were **not** rewritten.

---

## REGIONS STILL UNCHECKED / PENDING ATLAS

1. Exact glyphs, en-dashes, micro-spaces, leader dots, font metrics.
2. Full bodies of every “No change” span (source intentionally omits; nothing further to extract).
3. Item-12 spacing conflict among captions (EB019-P2-005).
4. Seal motif inventory and signature ink vs facsimile.
5. *Greeley Tribune* italicization.
6. original.pdf local bytes (file absent; declared SHA only).
7. Any mark/color not mentioned by captions (captions report black on white; no strike-through).
8. Page 1 header absence at true pixel level.

---

## LEGAL CURRENTNESS

`legal_currentness: not_verified`. Printed adoption/effective dates and titles are **not** evidence the ordinance is adopted, effective, complete, applicable, or current as law. No source-wide certification authorized.

---

## MATERIALS NOT OPENED

- EB-PDF-018 materials
- EB-PDF-020 page images / candidate / reviews (SOURCE_ONLY_IDENTITIES.json lists 020 identity hashes only; no 020 content review)
- full custody-bearing packet manifest (opaque digest only)
- 03-custody / 04-verification / PREPARATION receipt
- native PDF text extraction / OCR as Pass2 substitute

---

## STATUS

`completed_pending_atlas_verification` — declared **caption-mediated** procedure covered all **5** expected physical pages in **both** Pass1 and Pass2. This does **not** mean all text, regions, or glyphs were visually verified. Atlas direct image review remains required.

END PASS2_REVIEW.md
