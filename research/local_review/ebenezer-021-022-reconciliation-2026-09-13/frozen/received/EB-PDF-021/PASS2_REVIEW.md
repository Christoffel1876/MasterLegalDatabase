# PASS2_REVIEW — EB-PDF-021

assignment_id: EB-PDF-021
source_id: douglas-ehs-fees-atlas-directed
attempt: EB-PDF-021_douglas-ehs-fees-atlas-directed_20260913T014638Z
pass1_frozen_sha256: 1a9985bf678e80cec447223ef1c4e35ecad873619ae09874994beff5b78fe74e
utc_pass2: 2026-09-13T01:49:20Z
legal_currentness: not_verified
review_method: caption_mediated_source_first (Pass1) + candidate/native compare (Pass2)
direct_pixel_inspection_claimed: false

## Candidate identity verification (required)

| Field | Value |
|---|---|
| Manifest path | `02-candidate-text/douglas-ehs-fees-atlas-directed/candidate.txt` |
| **Expected SHA-256 from unchanged packet manifest `files[]`** | `769ea3a5ddd245c987e34303fef76e3bbd471c4d5d59cf46cbde1419508c9609` |
| Actual SHA-256 of opened candidate.txt | `769ea3a5ddd245c987e34303fef76e3bbd471c4d5d59cf46cbde1419508c9609` |
| Match | **YES** |
| Self-hash-as-expected used? | **NO** (manifest identity fields used) |
| Native page-0001.native.txt manifest SHA | `77546efbb12f57ac5ed0fab0e91597af743ddffa563530faa650e1bb4821ee4a` (matched) |
| Candidate status (prep) | machine_native_text_unreviewed; PyMuPDF 1.28.2 get_text flags=195 |
| Packaging markers | `===== PHYSICAL PDF PAGE … =====` excluded from error counts |

## Pass2 method

Compared frozen Pass1 (Read caption + retained Task executor caption of page-0001.png) to candidate.txt / native extract. Re-Read of page image was not required for fee-grid agreement checks already covered by retained captions; no pixel claim. Prior findings were not injected into Pass1 prompts; Pass2 may reference Pass1 vs candidate deltas only.

## Agreement (high level)

- Two table titles and effective dates match captions and candidate (titles appear at end of candidate native order — packaging/reading-order, not counted as content error).
- Fee amounts for Body Art, Child Care, Retail Food (Board), Land Use, Recreational Water, OWTS, and State Legislation retail licenses match between Task caption and candidate where both report values.
- Footnotes: OWTS $23/$20/$3 note and retail `fee $43 of each` … `Increases to $55 in 2025` agree (awkward wording preserved in candidate).
- Blank 2026 Fee for Penalty Assessment rows (25-4-1610 / 25-4-1611) agree (no invented amounts).
- `Intial Inspection` present in candidate; Task caption preserved `Intial`; coarser Read caption in freeze body had normalized to `Initial` — **do not treat Pass1 Read normalization as source proof against candidate**.

## Findings

### Critical
None.

### Minor / mediation

| ID | Severity | Topic | Notes |
|---|---|---|---|
| EB021-P2-001 | minor | Caption mediation vs freeze body — `Intial` | Candidate and Task caption: `Change of Ownership or Site Evaluation (Intial Inspection)`. Read-mediated freeze prose used `Initial`. Per Atlas 020 lesson, do **not** propose correcting candidate to `Initial` as caption normalization. Unresolved pending Atlas pixel check; candidate wording retained. |
| EB021-P2-002 | minor | EHS Plan Review fee-type slash | Task caption: some rows `//`, one row `/`; candidate uses single `/` throughout those long fee-type strings. Mediation discrepancy; not asserted as candidate error without pixels. |
| EB021-P2-003 | minor | Re-inspection casing | Candidate: `Re‐Inspection`; Task caption: `Re-inspection`. Casing/hyphen mediation only. |
| EB021-P2-004 | minor | Pass1 Read authority grouping | Initial Read caption lumped Retail Food / OWTS authorities; Task caption and candidate agree on per-row Authority (e.g., Late Fee & Education under 25-1-508; Installers/Cleaners under 25-1-109). Freeze body retained coarser Read structure — limitation of that caption path, not a candidate fee error. |
| EB021-P2-005 | minor | Native title order | Table title lines appear after body/footnotes in candidate (native extract order). Packaging/reading-order; titles themselves match. |

## Counts

- critical: 0
- minor: 5
- packaging markers excluded from error counts: yes

## Limitations

- Still caption-mediated; pending Atlas image verification.
- legal_currentness: not_verified
- original.pdf in workdir for identity only; not used as Pass2 text substitute beyond native extract already released post-freeze.
