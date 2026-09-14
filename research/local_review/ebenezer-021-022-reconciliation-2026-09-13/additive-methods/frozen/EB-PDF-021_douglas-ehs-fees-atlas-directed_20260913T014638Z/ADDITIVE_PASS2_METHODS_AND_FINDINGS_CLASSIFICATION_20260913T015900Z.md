# Additive Pass2 methods + findings classification — EB-PDF-021

issued_utc: 2026-09-13T01:59:12Z
attempt: EB-PDF-021_douglas-ehs-fees-atlas-directed_20260913T014638Z
originals_unchanged: true
not_a_renewed_blind_or_independent_pass: true
legal_currentness: not_verified

## Truthful Pass2 method (page-by-page)

Question: after candidate release, was each original page image **re-opened** for Pass2, or did comparison use only **retained Pass1 captions**?

| Physical page | Image | Re-opened after candidate release? | What Pass2 actually compared |
|---|---|---|---|
| 1 of 1 | `source/page-0001.png` | **No** | Retained Pass1 captions only: (1) Cursor `Read` image_description caption saved under `tool_outputs/page-0001_READ_caption.md`; (2) Task/executor caption-mediated report retained under `tool_outputs/page-0001_TASK_executor.md` — compared to released `candidate/candidate.txt` and `page-0001.native.txt` after manifest identity verify. |

**Unperformed:** post-release direct pixel re-inspection of `page-0001.png`; renewed blind Pass1; any page-by-page pixel↔candidate glyph audit beyond retained captions. Those comparisons remain **unperformed** and are not claimed here.

Candidate identity was verified against the **unchanged packet manifest** expected SHA (`769ea3a5ddd245c987e34303fef76e3bbd471c4d5d59cf46cbde1419508c9609`), not a self-hash-as-expected.

## Root source QA (Atlas) — preserve as source observations

| Item | Classification | Notes |
|---|---|---|
| `Intial` in `Change of Ownership or Site Evaluation (Intial Inspection)` | **source anomaly** | Confirmed by root QA. Candidate preserves source. Pass1 Read freeze prose that said `Initial` was **caption normalization** (EB021-P2-001). Do not propose correcting candidate to `Initial`. |

## Classification of proposed Pass2 findings (existing PASS2_REVIEW.md IDs)

| ID | Classification | Disposition |
|---|---|---|
| EB021-P2-001 (`Intial` vs Read `Initial`) | **caption normalization** (of Pass1 Read path) vs **source anomaly** (`Intial` confirmed) | Not a candidate extraction error. |
| EB021-P2-002 (EHS fee-type `/` vs `//`) | **unresolved** (caption mediation variance) | Unperformed pixel confirmation. |
| EB021-P2-003 (`Re-Inspection` casing) | **unresolved** (mediation) | Unperformed pixel confirmation. |
| EB021-P2-004 (Pass1 Read authority grouping vs per-row candidate) | **caption normalization / mediation limitation** in coarser Read Pass1 path | Task caption aligned better with candidate; not counted as candidate fee error. |
| EB021-P2-005 (native title order) | **reading order** (native extract packaging) | Not a printed-content error. |

## Scope

- Additive only; PASS1/PASS2/receipt originals unchanged.
- No 023; no public research; no source edits.
