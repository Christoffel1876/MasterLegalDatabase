---
title: Independent EB011 source and custody check
date: 2026-09-11
assignment_id: EB-PDF-011
source_id: larimer-fee-increase-memo-sd004-lc-09
status: source_fidelity_verified_with_portability_qualification
legal_currentness: not_verified
---

# Independent EB011 check

The complete one-page source supports the reviewed native text and both extracted
topics. No substantive wording, numeric, date, table-ID or reading-order defect
was found. The building statement retains 2.29%, July 1, 2026 and Tables 1-A,
1-B, 1-C and 1-E. The transportation heading separately retains October 1, 2026;
its paragraph prints no percentage or amount. No building percentage is carried
into that second topic.

Pydantic validation passed for the review, original packet and native page
records; the exported review and packet JSON schemas also passed. All 12 copy
receipts matched both their hashes/sizes and the original files. Seven completion
receipt hashes and four pass-1 hashes matched actual files. The whole 1,256-byte
native text was independently reproduced with PyMuPDF 1.28.2, `sort=False`,
`flags=195`; it equals the candidate's half-open byte slice `[56,1312)`, the native
page evidence and both reviewed text representations. Both heading/body pairs
match their recorded byte offsets.

A fresh Poppler 26.05.0 render at 300 dpi is byte-identical to the supplied
2550×3300 PNG. The complete page was directly viewed at its displayed 1376×1780
resolution, including the letterhead, both headings, both full paragraphs and
blank remainder. Typography, exact space counts and punctuation codepoints are
not certified from raster appearance. Keeping the native bytes unchanged is
appropriate; the external review's proposed spacing changes need not replace
the preserved text.

## Portability qualification

The copied `custody/PROVENANCE_RESOLUTION.json` resolves an appendable repository
manifest to a frozen **external handoffs path**. That frozen file exists and was
verified: 24,284 bytes, 12 records, SHA-256
`261eef34f4d0a951c05f1a2987598d6cfedb1aaedc4411c31602502c02205992`.
Its line 11 matches the EB011 line hash and size. However, the review directory
alone does not carry that historical manifest.

Add its exact copy, the resolution schema, and the native page-evidence schema
to the review package, with a new package-relative mapping receipt. Preserve all
frozen originals unchanged. The complete original packet manifest intentionally
contains EB010 as well as EB011. Describe it as historical context and enumerate
which dependencies the EB011 package locally resolves; do not imply that copying
one manifest makes both original document packages self-contained. Larger
upstream archive references can remain explicitly external custody context.

The one-off review model rejects unknown fields but does not enforce every
hash format, timestamp, path or cross-file relationship. The current files pass
independent exact checks; JSON Schema validation alone is not an equivalent
source-fidelity gate.

## Limits

This was a candidate-aware audit, not a blind transcription. External reviewer
blindness, caption handling and prior Atlas-review chronology remain documented
method claims; those actions were not independently replayed. The source is an
agency memo, not the underlying unnumbered 2008 resolution or a complete fee
schedule. Original HTTP acquisition, later amendments, legal applicability and
currentness remain unverified. No network requests or production changes were
made. The typed JSON audit records the exact inspected file hashes.
