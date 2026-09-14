---
title: EB-PDF-009 validation scope
date: 2026-09-11
status: scoped_checks_passed_full_corpus_blocked
legal_currentness: not_verified
---

# Completed checks

- Strict Pydantic review/block/evidence models and the exported JSON Schema passed.
- All referenced file sizes and SHA-256 values match; four original report/receipt
  files are unchanged. All three user-supplied report/receipt hashes match.
- Five source PNGs reproduce byte-for-byte using Poppler 26.05.0 at 300 dpi.
- Five native page streams and the full 12,736-byte candidate reproduce with
  PyMuPDF 1.28.2, sort=False, flags=195. Every saved native excerpt is present in
  its unchanged physical-page record.
- The PDF matches the already-preserved raw file and the validated manual intake
  record at physical line 7. No new manual-intake manifest entry was written.
- Atlas directly checked all five complete images and targeted page-five crops;
  independent source reviewers checked pages 1–4 and page 5. The final seven
  blocks were compared with those images and accepted with explicit whitespace,
  dot-leader and source-anomaly qualifications.
- New Markdown frontmatter parses; no production code or existing tracked file
  changed in this research intake.

# Full-corpus limitation

The required `python -m geode.validate --layer all` check was run and returned
the same two inherited errors: the county `_index.jsonl` remains an unresolved
Git LFS pointer, and validating LOCAL_REVIEW_SUMMARY.json encounters the missing
LOCAL_REVIEW_QUEUE.jsonl data. The summary JSON itself is readable. Those files
are unchanged against the pre-intake HEAD. This is not a full-corpus clean result.

These checks verify evidence identity and bounded transcription structure. They
do not establish adoption, legal applicability, effective dates, currentness,
source URL acquisition, complete fee coverage or correct interpretation of the
source's internal contradictions. External timing and blind-order statements
remain reviewer claims, not certifications based on file mtimes.
