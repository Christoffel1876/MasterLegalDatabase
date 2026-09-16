# Additive Pass2 methods + findings classification — EB-PDF-022

issued_utc: 2026-09-13T01:59:12Z
attempt: EB-PDF-022_pueblo-planning-fees-atlas-directed_20260913T014929Z
originals_unchanged: true
not_a_renewed_blind_or_independent_pass: true
legal_currentness: not_verified

## Truthful Pass2 method (page-by-page)

Question: after candidate release, was each original page image **re-opened** for Pass2, or did comparison use only **retained Pass1 captions**?

| Physical page | Image | Re-opened after candidate release? | What Pass2 actually compared |
|---|---|---|---|
| 1 of 4 | `source/page-0001.png` | **No** | Retained Pass1 `Read` caption (`tool_outputs/page-0001_READ_caption.md`) vs released candidate/native page 1. |
| 2 of 4 | `source/page-0002.png` | **No** | Retained Pass1 `Read` caption vs candidate/native page 2. |
| 3 of 4 | `source/page-0003.png` | **No** | Retained Pass1 `Read` caption vs candidate/native page 3. |
| 4 of 4 | `source/page-0004.png` | **No** | Retained Pass1 `Read` caption vs candidate/native page 4. |

**Note:** A Task/executor Pass1 report was later retained at `tool_outputs/PASS1_TASK_executor.md` (SHA `33577b9f5956e6d665a543f1bea37d4488f198fb42c9c8c15e4e4c3c993843e7`) after the written Pass2 path; it was **not** a post-release image re-open. Written `PASS2_REVIEW.md` compared retained Read captions to candidate. No page image was re-`Read` or re-attached after candidate release for Pass2.

**Unperformed:** post-release re-opening of any of the four PNGs for Pass2; renewed blind Pass1; pixel-level glyph audits beyond retained captions. Keep unperformed comparisons unperformed.

Candidate identity verified against unchanged packet manifest expected SHA (`3bb121e500207a0c721f4301c76030d00bf6b135c8cb43d723619cd6548c0dc5`), not self-hash-as-expected.

## Root source QA (Atlas) — preserve as source observations

| Item | Classification | Notes |
|---|---|---|
| Both **nor** clauses in Commercial Site Plan remodel fee types (`…without addition that increases building footprint nor site improvements`) | **source anomaly** / source wording | Confirmed by root QA. Preserve; not extraction errors. |
| Awkward Subdivision wording: `$105 Plus per Lot (≥11)` and `Deferred Filing+` | **source anomaly** | Confirmed by root QA. Appears in both Pass1 captions and candidate — preserve; do not normalize. |

## Classification of proposed Pass2 findings (existing PASS2_REVIEW.md IDs)

| ID | Classification | Disposition |
|---|---|---|
| EB022-P2-001 (`2-13-26` / header early in native order) | **reading order** (native extract packaging) | Not a printed-content error. |
| EB022-P2-002 (Subdivision awkward phrasing) | **source anomaly** (root-confirmed) | Not a new extraction error; preserve candidate/source wording. |
| EB022-P2-003 (contact line extra spaces before www) | **unresolved** (space-count mediation) | Unperformed pixel confirmation. |
| EB022-P2-004 (leading spaces before some Fees) | **unresolved** (spacing mediation) | Unperformed pixel confirmation. |

Task-only caption notes not elevated to new Pass2 errors without pixel re-open (remain caption mediation / unresolved if not in written PASS2): e.g. reported `$150_` on CCN/RCN, gold separator variance, page mis-labels in captions.

## Scope

- Additive only; PASS1/PASS2/receipt originals unchanged.
- No 023; no public research; no source edits.
