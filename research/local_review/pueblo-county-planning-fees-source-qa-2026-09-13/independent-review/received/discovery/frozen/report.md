---
title: Sherlock SH-EXT-002 — Pueblo County fee/adopting-instrument gap
assignment_id: SH-EXT-002
status: partial_pending_atlas_verification
actual_start_utc: 2026-09-13T01:56:34Z
prepared_at_utc: 2026-09-13T01:58:07Z
delivery_folder: 20260913T015719Z
start_here_sha256: a91112d2f24a873d55b9c8ac4c5f907bc0faac0ab8299c09feaec831109ae061
directed_proposal_sha256: d365eecb0dd9453b36ad0ab4a1cfcad06ad4a3d8257ea29670ebce4f9135e5a5
audit_manifest_sha256: 6c293354c1e55b369a821d29e559503143ec918645fd392204fa1be0cd6bc366
research_stop_utc: 2026-09-13T02:15:00Z
delivery_deadline_utc: 2026-09-13T02:25:00Z
review_status: pending_intake
legal_currentness: not_verified
answer_safe: false
sh_ext_001_r1_preserved: true
---

# SH-EXT-002 report

## Caps
| Metric | Used | Cap |
|---|---|---|
| Public actions | **2** | 6 |
| Distinct URLs | **2** | 4 |
| Body bytes (A001+A002) | **81082** | 20,000,000 |
| Per-body max observed | **75214** | 10,000,000 |

Hidden network requests: **not measured**. Stopped further opens because no eligible same-host adopting-instrument URL was observed in retained successful bodies; commissioner source stopped on 403.

## Target 1 — fee PDF (success)
- Requested exact href (unchanged encoding): proposal target1
- Outcome: HTTP **200**, `original_pdf`, **2** pages, sha `1c9fda2c8bacb414468947664d6edb6640845081fcb1a5366dccf0c58720a084`, 75214 bytes
- Visual scope: **both pages** (full document; tiny)
- Filename/label claim "Adopted 5.8.25" preserved as **filename claim only** — not proven adoption/effective date
- On-page date/adoption text hits: none extracted
- No printed `pueblocounty.gov` adopting-instrument URL in PDF text
- Historical pin comparison: **no_match_within_pinned_legacy_selected** (byte hits=0, url-only=0)

## Target 2 — commissioners catalog (denied)
- Outcome: HTTP **403**, `error_body` retained sha `d4074fa6d9f4ac22d763ea65b9419241dac025322e2f57b9393dfd2bf5b43854`
- **No retry / no browser alternate** (assignment rule)
- Role remains catalog lead, not adoption instrument
- Historical pin comparison: **no_match_within_pinned_legacy_selected**

## Remaining gaps
- Adopting/executed instrument for the fee schedule **unresolved**
- Two distinct URL slots and four action slots unused for lack of freshly observed eligible links

## Stop
SH-EXT-002 complete for this dispatch. No next batch. Prior SH-EXT-001/R1 unchanged.

## Visual inspection (caption-mediated)

Both PDF pages rasterized. **CAPTION_MEDIATED_REVIEW**: fee tables only; no signature/execution block or ordinance number observed on face. Issuer not clearly titled on page face in that review; provenance = exact `pueblocounty.gov` URL + A031 label. Filename Adopted 5.8.25 remains unverified.
