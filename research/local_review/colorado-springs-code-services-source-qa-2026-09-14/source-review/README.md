---
reviewer: Plato
review_date: 2026-09-14
source_status: preserved_2015_schedule
legal_currentness: not_verified
---
# Colorado Springs Code Services source review

This is Plato's candidate-aware internal review of all seven physical pages. Plato prepared the source packet and knew earlier metadata concerns. Full images were inspected before the native comparison in this turn; no Ebenezer report or Atlas's new direct-image notes were consulted. This is not an independently blinded external review.

`SOURCE_QA.json` preserves all 18,343 native bytes in 670 line records, each with exact native/candidate byte offsets, digest, page coordinates and text color. The unchanged 18,497-byte candidate retains its page markers. There are 197 fee associations (38 on page 2; 30 on page 3; 40 on page 4 including the textual closeout reference; 53 two-column rows on page 5; 36 on page 6), 15 note/context records and ten definition/body mappings. These counts do not mean 197 separate legal fees or physical grid rows.

All seven full PNGs and 14 exact pixel crops were directly displayed. White native figures on page 1 and white “2015 Proposed changes” on pages 2–6 are preserved as nonvisible extraction text, excluded from fee rows; the verifier checks white pixels at those exact glyph bounds. Page 7's native order is repaired only through additive heading/body references. Source spelling, threshold anomalies, the Medical Squad drafting question and every literal fee string remain unchanged. `REVIEWED_TRANSCRIPT.md` makes the reviewed fee/category/context mappings readable; `SOURCE_QA.json` remains the exact-byte reference, including headings, footers and nonvisible text.

Each fee row retains its page's context records and all ten definitions. This conservative context envelope is deliberate: inclusion does not assert universal applicability. Consumers must retain source context, category and column references rather than infer a fee, unit, date or total. `n/a`, `n/c`, `no charge`, textual fee references and blank category cells are not converted to numeric values. Two page-2 associations share one physical M row.

The self-contained `inputs/` directory is an exact subset of the frozen source packet. It contains the original PDF, seven original full PNGs, untouched native/candidate text and selected custody. Its copied upstream manifest describes additional files deliberately not included here; it is not a claim of a complete upstream package or proof that every upstream asset was independently checked. No upstream executable is imported. The historical two-source intake receipt remains exact; this QA reviews only the Code Services source.

Run from any directory with the restored environment:

```sh
PYTHONDONTWRITEBYTECODE=1 '/Users/mcoors/Documents/Project Geode/.geode-venv/bin/python' -B '/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-14/plato-cs-code-fees-qa/verify_review.py'
```

The validator reads only its local package, validates the closed seal and exported Pydantic schema, captures verified buffers, replays native extraction/offsets and fee/context associations, checks the selected raw line and acquisition/intake receipts, and reconstructs all crops. It does not fetch, rerun OCR, write source data or certify currentness. Relocate the entire directory and invoke its local verifier with Python plus Pydantic, jsonschema and PyMuPDF 1.28.2.

The focused run passed 33 tests, including 12 corruption/refusal cases and 19 independent fee-value expectations. Five PyMuPDF SWIG deprecation warnings and one shutdown warning were reported. Initial unsealed construction attempts found a page-6 font-alignment tolerance issue and a duplicated manifest-schema asset; the predecessor files are preserved in `preimages/`. The final run is in `tests-first.log` (the first pytest run, after those construction checks). No full maintained suite was run for this handoff-only review.

The visible title says 2015. Original HTTP completion (2026-09-12T23:10:46.652367Z), repository receipt (2026-09-12T23:56:16.492216Z) and today's review are separate. Adoption, effective date, currentness, supersession and cross-document equivalence remain unverified. This packet creates no canonical intake, inventory join, lookup adapter or legal answer permission.
