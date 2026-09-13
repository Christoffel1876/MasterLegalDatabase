# PASS2_REVIEW — EB-PDF-022

assignment_id: EB-PDF-022
source_id: pueblo-planning-fees-atlas-directed
attempt: EB-PDF-022_pueblo-planning-fees-atlas-directed_20260913T014929Z
pass1_frozen_sha256: b95635b228c638cb0af1fa4df60a796b38104d7afe11fe4bd0a8f6eaaceb8b1d
utc_pass2: 2026-09-13T01:51:15Z
legal_currentness: not_verified
review_method: caption_mediated_source_first + candidate/native compare
direct_pixel_inspection_claimed: false

## Candidate identity verification

| Field | Value |
|---|---|
| Manifest path | `02-candidate-text/pueblo-planning-fees-atlas-directed/candidate.txt` |
| **Expected SHA-256 from unchanged packet manifest** | `3bb121e500207a0c721f4301c76030d00bf6b135c8cb43d723619cd6548c0dc5` |
| Actual SHA-256 | `3bb121e500207a0c721f4301c76030d00bf6b135c8cb43d723619cd6548c0dc5` |
| Match | **YES** |
| Self-hash-as-expected? | **NO** |
| Native page SHAs | p1 6418a4b0…e3b5; p2 41f1e61e…994b; p3 8f7ef134…950f; p4 215df7e6…6801 (all match manifest) |
| Packaging markers | excluded from error counts |

## Agreement

- Header contact line, department name, FEE SCHEDULE title, and Applications/Fees grid content agree across Read captions and candidate for pages 1–4.
- Fee amounts and formulas (including Commercial Site Plan bullets, Marijuana new/renewal, Rezoning tiers, Public Notice Fees) match.
- Subdivision lines in candidate are exactly: `$100 + $160 per Lot (≤10), $105 Plus per Lot (≥11)` and `$100 Deferred Filing+ $50 per lot` — same awkward wording as caption; **not** a Pass1-only garble. Preserve as shared source/candidate wording pending Atlas pixels.
- Wireless row punctuation `Facilities, (Tower or Antenna,)` matches candidate.
- Footer string `2-13-26` present on each page (candidate places it early in native reading order after contact — packaging/order, not content mismatch).

## Findings

### Critical
None.

### Minor / mediation

| ID | Severity | Topic | Notes |
|---|---|---|---|
| EB022-P2-001 | minor | Native reading order | `2-13-26` and some header blocks appear before table body in candidate extract order; physical layout places footer bottom-right per captions. Packaging/reading-order only. |
| EB022-P2-002 | minor | Subdivision awkward phrasing | `$105 Plus per Lot` and `Deferred Filing+` appear in both caption and candidate — preserve; do not normalize. Pending Atlas confirmation of exact printed glyphs. |
| EB022-P2-003 | minor | Contact line spacing | Candidate shows extra spaces before `www.pueblo.us` (`\|   www`). Caption mediation may collapse spaces; unresolved exact space count. |
| EB022-P2-004 | minor | Leading spaces before some Fees | Candidate shows leading space before some $ amounts (e.g. Certificate of Economic Hardship). Spacing/mediation only. |

## Counts

- critical: 0
- minor: 4
- packaging excluded: yes

## Limitations

- Caption-mediated; pending Atlas verification.
- legal_currentness: not_verified
- Task executor Pass1 output retained when available under tool_outputs/; freeze used Read captions as primary retained mediation for this attempt.
