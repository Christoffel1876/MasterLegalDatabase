---
title: EB013 Fort Collins wildfire draft - physical pages 5-8 source QA
prepared_at: 2026-09-11T19:10:55.784026+00:00
review_mode: candidate_aware_visual_QA
external_reports_consulted: false
source_status: visibly_draft
legal_currentness: not_verified
source_or_candidate_modified: false
---

# Scope and result

All four complete supplied page images and nine original-PNG diagnostic crops were inspected. The unchanged native slices were compared after the first full-image pass and reproduced from the exact eight-page PDF with PyMuPDF1.28.2, sort=False, flags195. This is candidate-aware QA, not a blind pass; no Ebenezer013 report was consulted. Pages1-4 are outside this subtask.

No lexical/numeric correction was identified on pages5-8. The main extraction risks are visual amendment marks and cross-page associations. The strict JSON preserves every native byte in 39 nonoverlapping observations covering all8,177 native bytes, with separate graphical annotations and source-order IDs. Original line breaks, punctuation and underscores stay unchanged.

# Material associations and marks

- Page5: all103.1 highlighted;105.2 adds the highlighted local/state/federal-regulations phrase. Entire old106.1 General sentence is struck and new106.1 Fees highlighted, referring to Section109, not a numeric fee. Preserve both definitions, three spaced ellipses, and the exact quoted titles. In301.1 only findings of fact is struck; preceding the remains. The long CWRC-map replacement is highlighted. Item10's302.1 heading continues onto page6.
- Page6:302.1 repeats the findings-of-fact strike and CWRC Map highlight. All seven401.1 exceptions were checked, including at-least50feet;120squarefeet and greater-than-or-equal-to10feet; less-than25percent wall/roof conditions; written twenty-five in exception5; more-than500squarefeet addition threshold; and older-than50years exception7 with may/if, literal Chapter X and possible additional conditions. April1,2026 comparisons based on city/county records occur in3,4,6, not5. Entire502.1.2 Materials AND its Exception are struck.
- Page7: six complete old bodies are struck:502.1.3,502.1.4,503.2.4,503.2.4.1,503.2.5,503.3.2. Their unstruck deletion instructions must remain distinct. Preserve deleted numerical wording such as10-inch,4.5feet,6-10feet and whichever is less. OldC101.3.7 literally says AHJ authority to establish fees and is struck; do not correct the source anomaly. Highlighted replacement continues after approved construction into page8.
- Page8: highlighted continuation includes §1-15(f), civil infraction and a separate offense for each continued day. Sections2-3 follow outside the yellow outline; preserve the prohibition on changing substantive Code provisions. First/second-reading and effective-date fields are blank, with printed2025. Both signature lines are blank. Madelene Shehan is a printed approving-attorney label, not an authenticated signature.

The page8 header is complete: my direct top crop of the original2550×3300 PNG shows both full draft-warning lines. An earlier full-page conversation preview looked clipped; no source-header omission is recorded.

Every page's footer is before the body in native extraction order. Source-order IDs move only that metadata position conceptually; this audit does not rewrite the candidate. Blank-line underscore counts are retained as native bytes but are not asserted to be countable physical glyphs.

# Integrity and limits

Source SHA256: `00e7446d7deac3499b86c4b8f15a5d802cc0c14dc2621409845ec13525cb01d2` (169449 bytes). Candidate SHA256: `9fc7fe62d1d678407db0d228a6e5ddc2397765a1d2f6d5ab4430a7cac3922ea7` (19785 bytes). Every page image/evidence file, crop, native byte interval and candidate offset is bound in SOURCE_REVIEW.json and validated against SOURCE_REVIEW.schema.json.

The source is visibly a discussion draft. No adopted effect, actual effective date, currentness, signature identity, complete code coverage or semantic RuleUnit promotion is claimed. No source, candidate, repository code, control ledger or external report was changed; no network or bot contact occurred.
