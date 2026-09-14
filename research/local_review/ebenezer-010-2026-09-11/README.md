---
title: Atlas integration of Ebenezer EB-PDF-010
date: 2026-09-11
status: seven_page_native_order_review_preserved
legal_currentness: not_verified
source_intake_status: archived_pending_pipeline
---

# Reviewed result

All seven physical pages have a reviewed source-order native-text copy. Every original native UTF-8 byte is retained exactly once; only exhaustive, nonoverlapping original intervals are reordered. The untouched candidate, seven images, seven native receipts, source custody, independent Atlas audits and exact external reports are preserved alongside it.

[reviewed-source-order.txt](reviewed-source-order.txt) restores displaced document and section headings, the Property Status Information fee/scope, subdivision group label, Major Special Review use list, Location and Extent exemption, fire-agency Scope Fee pairs, CGS qualifications/rate and event-tier associations. Original extraction line breaks, spaces, punctuation and candidate page markers remain unchanged. [ASSOCIATION_NOTES.md](ASSOCIATION_NOTES.md) keeps explanatory annotations outside the source text. This is not a reconstruction of original table geometry or a glyph-perfect transcription certificate.

The twelve external findings have nine accepted and three qualified dispositions. Two separate completion-receipt summaries omit the literal `$7` prefix from `$7,881.21` and `$7,337.70`; those summary literals are rejected. The full PASS2 report and checked source contain the correct complete amounts. The received receipt stays unchanged; a shell-substitution mechanism is plausible but not proven by the delivered files.

The source's `its'`, `principle`, two distinct $550.36 rows, $7,881.22/$7,881.21 difference, Tier 3 unclosed parenthesis and PFA/LFRA asymmetry remain unchanged. No arithmetic, rounding correction, fee total, operative-date determination or law interpretation was introduced. Additional Processes on page 2 is a separate peer group under Land Division, not merged into the subdivision list.

Atlas's pages1–3 audit and the separate pages4–7 audit were produced before those reviewers consulted the external reports. External timing, blindness, caption mediation and completeness statements remain attributed claims. Referenced PASS1_NOTES.md and reviewer crop folders were not delivered and are not certified here. The original PDF was reportedly absent from the external PASS1 workspace; Atlas independently binds the matching repository original and reproduces all native pages.

This package concerns EB010 only. The unchanged copied packet manifest also names EB011; that does not mean EB011 was reviewed here. Source acquisition/currentness, amendment completeness and county-wide coverage remain unverified. No source bytes, raw manifest, control-plane record, coverage state or semantic RuleUnit was changed or promoted.

# Verify locally

Run from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python research/local_review/ebenezer-010-2026-09-11/validate_package.py --native-replay
```

The strict Pydantic models and exported schemas check custody, all seven page receipts, exact file inventory, candidate offsets, exhaustive byte partitions, external report dispositions and pending intake status. Native replay requires PyMuPDF; this package was prepared using version 1.28.2, `sort=False`, `flags=195`. Full-corpus validation is outside this bounded research intake.
