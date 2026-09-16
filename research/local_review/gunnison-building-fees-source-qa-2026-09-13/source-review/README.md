---
reviewer: Plato
status: complete_visible_source_fidelity_review_qualified_handwriting
legal_currentness: not_verified
answer_safe: false
---
# Gunnison building permit fee resolution: three-page source review

This packet preserves the received Resolution 25-24 PDF and a complete scoped
review of its visible text. The county issuer is `CO-COUNTY-GUNNISON`. The proposed
source ID is `gunnison-building-fees-resolution-2025-24-sh-ext-003`; this packet
makes no assertion that canonical intake has occurred.

Read `SOURCE_QA.json` and `REVIEWED_TRANSCRIPT.md`. There are 34 ordered text or
graphic-observation blocks and 12 fee components. Page 3 is prose with four
bullets, not a ruled table. Each component retains its complete clause, valuation
context and recording condition. General and mechanical subsections remain
separate. No fee total is calculated.

Plato inspected all three fresh full 300 dpi Poppler images, then compared the
unchanged native extraction and local OCR. This is candidate-aware review, not a
blind external review. Every native extraction is zero bytes; native offsets are
therefore empty. The separate Apple Vision candidate preserves every raw
observation and its exact derived UTF-8 byte span. `reviewed/` contains the visual
transcript and separate annotations, with exhaustive per-block byte spans. These
are derived transcript offsets, never represented as source-native offsets.

The first sandboxed OCR call returned `nilError`; its original receipt and outputs
remain in the packet. The same local executable then succeeded outside that
sandbox on the three known images, without network or configuration changes.
The original executable and Swift source are preserved as evidence, but the
read-only verifier does not execute OCR or import another research package.

Seven crops were viewed. The early `p3-stamp.png` crop cuts off the right stamp
column because of its chosen bounds. It remains unchanged; the additive
`p3-stamp-complete.png` preserves and displays the complete stamp. No clipping of
the source page is inferred. `preimages/initial-review/` preserves the earlier
metadata before the reviewer label, mixed handwriting type and full-stamp note
were corrected. It is historical, superseded metadata, not a second accepted
review. Earlier generation scripts preserve their actual historical behavior and
are not intended to overwrite or regenerate this frozen directory.

Source anomalies remain: “recommended and increase of,” “or the Building Safety
Journal,” and Exhibit A versus ATTACHMENT A. The source-stated adoption date,
referenced memo dates and visible recorder-stamp time have separate roles. The
recording condition is not converted into an independently verified effective
date. Handwriting, signatures and seal are qualified visual observations; no
identity or execution authenticity is certified. Exactly 5,000 square feet is
not supplied where the source only states greater-than and less-than cases.

The retained reservation/result timestamps and publisher URL are reported
custody claims. They are not independently observed HTTP acquisition times.
Local byte identities, rendering and OCR receipts are independently checked.
The entire prior recommendation is copied for custody, but this QA covers only
A026, not its other recommended sources.

From any working directory, run:

```sh
PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-status-venv/bin/python -B \
  '/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-13/plato-gunnison-fees-source-qa/verify_review.py'
```

Add `--rerender` to compare all three complete page pixel buffers using the
recorded local Poppler executable. The ordinary verifier is portable with Python,
Pydantic, jsonschema and PyMuPDF; the optional rerender requires that documented
renderer path. Closed inventory checks include all originals, preimages,
receipts, candidate bytes, models and verification scripts. Hashes prove custody
and reproducibility, not semantic truth or current law.
