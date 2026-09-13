---
title: Independent Chaffee planning fee source audit
status: complete_source_audit_with_custody_wording_qualification
source_currentness: not_verified
answer_safe: false
---

# Independent source audit

All 49 fee rows in ten groups agree with direct inspection of both full source
pages and all eight Atlas crops. No amount, application-label or fee-condition
correction is needed. Each fee's native span immediately follows its own
application span, including repeated equal values. The verifier additionally
checks their original PDF line geometry and complete 3,769-byte native coverage.

The subdivision-exemptions group continues across the page break; the first four
page-2 entries precede the separate SUBDIVISIONS heading. The appeal-refund and
rental-license notes stay attached to their marked rows. The entire hourly
condition and the final Section 5.2.5.5 escrow paragraph remain included. No fee
expression is calculated or rewritten. The source's `< 2,500’` and `> 2,500’`
categories are preserved without inventing an exactly-2,500 category.

One wording qualification is needed: the draft's “Two new observed publicGET/receipt
chains” should be read as **one fresh successful fee-PDF GET**, completed at
2026-09-13T16:44:33.133961Z, following the separately retained earlier actual county
A003 HTTP 302 Location. Earlier A001/A002 requests retrieved other ordinance PDFs.
The original catalog capture remains received referral evidence. The full frozen
public retrieval package is retained for custody portability, but those other PDFs
receive no source review in this audit. No canonical intake was performed here.

The original 27-file draft is unchanged in `received/`. Atlas's subsequently added
crop-inspection receipt is preserved separately in `root-addendum/`; no historical
inspection time is rewritten. Popper directly viewed all eight crops and both
pages. A new exact page-2 header crop confirms its visible county emblem and
heading lines; the footer is also visible in the retained hourly-notes crop.
This is candidate-aware source QA, not a blind experiment or a current-law answer.

`AUDIT.json` is strict, schema validated and explicit about these limits.
`ROW_GEOMETRY.json` binds all application/fee native line boxes in PDF points.
`FINAL_MANIFEST.json` closes the entire package, including historical custody
payloads and empty `.runtime.lock` files; do not drop those files as cache-like junk.

## Read-only portable verification

```sh
PYTHONDONTWRITEBYTECODE=1 python -B /path/to/packet/validate_audit.py --root /path/to/packet
PYTHONDONTWRITEBYTECODE=1 python -B /path/to/packet/validate_audit.py --root /path/to/packet --pdftoppm /path/to/pdftoppm
```

The default verifier reads only this package and never invokes a downloader,
original builder, historical transaction or network request. Optional Poppler
replay writes to a disposable temporary directory. Dependencies are Pydantic 2,
jsonschema and PyMuPDF 1.28.2; exact rerender hashes require compatible Poppler.
Tests reject equal-value fee swaps, altered conditions, broadened note scopes,
missing continuations, changed source bytes, page swaps, crop changes and legal
status promotion. Integrity validation cannot independently prove a visual judgment.
