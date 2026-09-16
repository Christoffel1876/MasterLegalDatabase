---
title: Portable Larimer equity resolution source review
status: source_review_only
legal_currentness: not_verified
---

# Source-only review

Start with [SOURCE_QA.md](SOURCE_QA.md) and its [typed record](SOURCE_QA.json).
Both pages of the retained scanned original were directly viewed. The complete
printed body is transcribed in 21 page-local blocks; five execution regions and
12 source observations remain separate. Both PDF native text layers are empty.

The literal printed year `20243`, eight eligibility categories, 25% authorization,
application-time request, discretion and renewal qualification are preserved.
Filled date/signature/seal areas are visual observations, not authenticated execution.
No Attachment A or complete fee schedule is supplied or reconstructed.

This is internal Atlas source QA with prior intake metadata, not an external blind
review. Original acquisition remains unknown and custody is received_review_package.
No canonical source, inventory, fee rule, legal status or coverage was promoted.

Run from any directory using Python with Pydantic 2, jsonschema and PyMuPDF 1.28.2:

```sh
PYTHONDONTWRITEBYTECODE=1 python /path/to/validate_review.py
```

Add `--rerender` to reproduce both pages and three crops with Poppler pdftoppm
26.05.0. Temporary render files are removed; the package and original are unchanged.
Pin `MANIFEST.json` outside this directory. It inventories all files except itself.
Do not run the archived one-time `build_review.py`; it refuses file replacement.
