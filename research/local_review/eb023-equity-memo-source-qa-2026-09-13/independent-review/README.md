---
title: EB023 complete four-page source-fidelity review
date: 2026-09-13
source_id: larimer-equity-fee-memo-sd007-05
status: complete_source_fidelity_review_pending_root_acceptance
legal_currentness: not_verified
---

# Four-page Larimer staff memo review

All four complete source images were directly inspected before this review phase’s OCR comparison. A complete 82-block source transcription was frozen in SOURCE_FIRST.json at 04:42:19 UTC, then all 181 raw OCR observations were compared and three source crops inspected. This is not blind QA: the reviewer prepared the source packet earlier and knew the parent’s concerns. No external Ebenezer report was consulted. Root’s unfinished notes were read only afterward and are copied with their historical incomplete status unchanged.

The memo is addressed to the Board of County Commissioners from Rebecca Everette, Community Development Director, for Admin Matters, December 19, 2023. It recommends changes; it is not an executed adopting resolution. January 2, 2024 is stated as a proposed implementation date, expressly conditional on adoption. Attachments A and B are listed but are not included in the four-page PDF. The original acquisition time remains unknown; the supplied official URL is a provenance claim. Repository receipt time is separately preserved.

SOURCE_QA.json and its strict schema bind all 82 reviewed blocks, the exact original PDF and four page images, all 9,796 candidate bytes (9,344 original OCR body bytes plus packaging), and all 181 original engine observations. The engine assigned confidence 1 to every observation, including corrupted page 4 words. Confidence is not a fidelity certificate. The raw candidate and OCR JSON/text are byte-for-byte copies, never corrected in place.

The special-event table has four logical rows in five physical fragments and 14 characteristic bullets. Tier 2 begins on page 3 and continues on page 4 with its $100 DNR fee and two remaining characteristics. The empty page 4 label cell is a continuation, not a new fee category. Source amounts, including `$1000` without a comma, are retained. The DNR footnote covers events on or adjacent to DNR-owned or managed land and separately describes negotiated staffing fees. Full Road Closure is a separate $500 row, additional to the permit fee, excluding block-party closures. No total, applicable tier, adoption or present legal effect is inferred.

There are five corrected OCR wording blocks on page 4: the Tier 2 staffing clause, Tier 3 parenthesized greater-than label, two conflated Tier 3 roadway/transportation bullets, and `years` in the follow-up paragraph. The source is readable in the preserved crops. Raw observation 18 conflates two separate source bullets and is explicitly linked to both rather than silently duplicated as two independent source passages. OCR table reading order is separately reconstructed from source rows/columns. Nineteen prose bullets and two attachment bullets are preserved alongside the table bullets.

Source anomalies remain: `Staff recommend` versus `Staff recommends`, `January, 2 2024`, the doubled `and` in the Attachment B label, the printed study years, and the colored raster marks through the follow-up-review line. Those marks are not certified as a deletion or operative change. Quote style, line wrapping, leading OCR bullet artifacts and line-end hyphen continuation are explicitly normalized for wording comparison; exact source font codepoints are not certified.

The packet custody copy is a selected EB023 subset. Its original complete packet manifest also names EB024 and other artifacts not duplicated here. The copied manifest and schema are verified, and every selected listed payload retains its original manifest hash. The frozen 63-line raw intake snapshot is checked only for this source’s exact selected line, not asserted as an independent review of all other records. No raw/control-plane, source QA outside this folder, lookup or inventory file was changed.

Run the read-only verifier:

```sh
/private/tmp/geode-status-venv/bin/python -B /absolute/path/to/this/folder/validate_review.py
```

Optional exact complete-page rerender adds `--rerender --pdftoppm /path/to/pdftoppm`. Preparation used Poppler 26.05.0 at 300 dpi. The verifier checks exact source crops, source/native condition, every OCR span and candidate marker, all table associations, source qualifications and selected custody. It does not rerun Apple Vision or certify legal effect. Fourteen in-memory corruptions test word/fee/row/note/byte/provenance/owner/currentness failures; no originals are mutated.

Historical unsealed draft and validation attempts are retained separately. In particular, an initial comparison incorrectly flagged the literal masthead separator, and an initial validator attempted to look up the upstream manifest’s own schema among its payloads. Both were corrected before closure; unchanged source-first evidence and raw candidates were preserved. Final validation and test results are recorded separately in VERIFICATION.json.
