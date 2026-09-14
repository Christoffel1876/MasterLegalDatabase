# PASS2_REVIEW — EB-PDF-023

assignment_id: EB-PDF-023
source_id: larimer-equity-fee-memo-sd007-05
attempt: EB-PDF-023_larimer-equity-fee-memo-sd007-05_20260913T022031Z
pass1_frozen_sha256: 0f60f4320a9b4505b862bed051483642d30c5af94dee7f2eb889a26a66f3eda7
utc_pass2: 2026-09-13T02:24:16Z
legal_currentness: not_verified
candidate_type: machine_ocr_unreviewed (Apple Vision revision-three per START_HERE)
direct_pixel_inspection_claimed: false

## Candidate + packet verification

| Check | Result |
|---|---|
| MANIFEST.json SHA vs MANIFEST_SHA256.txt | **MATCH** `dbb8f0a6…2e89` |
| `validate_packet.py` | **Not completed** — `ModuleNotFoundError: No module named 'jsonschema'`. Fallback manual per-file SHA for all larimer-equity paths: **26 OK / 0 fail**. |
| Workdir original.pdf SHA | **MATCH** SOURCE_ONLY / manifest |
| Candidate expected (manifest) | `492c339ed0aac2eafa36228d3810df91eb70ddd555cf7c553b929bbfca544968` |
| Candidate actual | `492c339ed0aac2eafa36228d3810df91eb70ddd555cf7c553b929bbfca544968` |
| Self-hash-as-expected? | **NO** |
| Empty native.txt pages | Present (SHA e3b0c442… empty) — consistent with OCR-only candidate path |

## Pass2 method — page-by-page re-open (required)

| Physical page | Image re-opened after candidate release? | How |
|---|---|---|
| 1 | **Yes** | Fresh Cursor `Read` of `source/page-0001.png` after release; retained `pass2_reopen/page-0001_PASS2_REOPEN_READ.md`. Task reopen also dispatched (prompt retained). |
| 2 | **Yes** | Fresh `Read` after release; retained reopen note. |
| 3 | **Yes** | Fresh `Read` after release; retained reopen note. |
| 4 | **Yes** | Fresh `Read` after release; retained reopen note. |

**Assistance disclosure (Pass2):** caption-mediated `Read` image_description recheck — **not** direct pixel inspection. Comparing only earlier Pass1 captions does **not** satisfy this procedure; each page representation was re-opened.

## Agreement (high level)

- Memo identity, dates, Purpose/Background structure, fee-schedule recommendations, equity extension to 2027, special-event tier fee amounts ($200/$100/$25; $500/$250; $1000/$500/$250; Full Road Closure $500), Wildfire Review / Next Steps / Attachments themes agree between fresh reopen captions and candidate where OCR is intact.
- Attachment A wording `January, 2 2024` appears in both fresh caption and candidate — treat as **source anomaly** / shared wording, not a caption-only invention.

## Findings

### Critical / material OCR wording errors (candidate vs fresh caption-mediated source reading)

| ID | Page | Region | Candidate (excerpt) | Source-supported (caption reopen) | Category | Severity |
|---|---|---|---|---|---|---|
| EB023-P2-001 | 4 | Tier 2 staffing bullet | `Sheriff's Office o Jepartment of Natural Resources staffing bevond norma operations` | `Sheriff's Office or Department of Natural Resources staffing beyond normal operations` | OCR wording error | critical |
| EB023-P2-002 | 4 | Tier 3 impacts | `adiacent property`; `Moders,tand adjacet nespobothon`; `removal O1 parking` | `adjacent property`; moderate-to-severe transportation impacts wording; `removal of parking` | OCR wording error | critical |
| EB023-P2-003 | 4 | Tier 3 label | `1>1500 people)` | `Tier 3 (>1500 people)` | OCR / glyph error | critical |
| EB023-P2-004 | 4 | Next Steps | `every five vears` | `every five years` | OCR wording error | minor |

### Other

| ID | Classification | Notes |
|---|---|---|
| EB023-P2-005 | **source anomaly** | Attachment A `January, 2 2024` comma placement — in candidate and caption reopen; preserve; not an extraction “fix.” |
| EB023-P2-006 | **reading order** / packaging | Physical-page markers; LARIMER COUNTY logo text fragments mid-flow in OCR candidate | Not printed-body errors |
| EB023-P2-007 | **caption compression** (Pass1 freeze) | Pass1 freeze prose summarized some paragraphs; fresh Pass2 reopen + candidate provide fuller body — Pass1 freeze unchanged; not rewritten |
| EB023-P2-008 | **unresolved** | Faint yellow highlight on page 4 Next Steps — caption-reported mark only | Pending Atlas pixels |

## Counts

- critical: 3
- minor: 1 (+ classifications above)
- packaging excluded from content-error counts: yes

## Limitations

- Pass2 remains caption-mediated on reopen; not direct pixels.
- `validate_packet.py` blocked on missing `jsonschema`; manual hashes used.
- Task Pass1/Pass2 executor outputs retained when available; do not silently upgrade to pixel claims.
- legal_currentness: not_verified
