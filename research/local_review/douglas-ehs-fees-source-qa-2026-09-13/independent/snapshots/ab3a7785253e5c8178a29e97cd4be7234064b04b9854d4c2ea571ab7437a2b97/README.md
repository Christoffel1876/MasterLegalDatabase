---
title: "Douglas environmental-health fee source QA"
status: source_qa_portable_pending_intake
review_date: 2026-09-13
legal_currentness: not_verified
---

# One page, with complete table and note associations

This package preserves Atlas's frozen source-first transcription and source QA, plus an additive candidate-aware check of the one-page Douglas County environmental-health fee PDF. It contains **44 rows / 220 displayed cell positions**, including **218 nonblank native cell lines and two visibly blank fee cells**. Ten header lines, two complete notes and two captions account for all **232 native lines / 4,923 unchanged UTF-8 bytes**. The image-only department wordmark is separate from native text.

The original PDF SHA-256 is `35e90b9c3b73b414155ed965898c8c270757f1c367cbe50d7645956039dbb687` (149,173 bytes). Atlas's frozen pass1 remains `e9db13cf88f77d2ad9bf2c4d0d3975eb162d58eff2afc8a0e85a4911eeb76a6f`; original SOURCE_QA remains `69f962f1caa58f9fcf90970aed1a05d7ccdbba6bb39b69f78ff0f15012896df4`. Neither these files nor the source, native candidate, supplied images, acquisition records or earlier builders were changed.

The independent check directly viewed the complete original PNG, all five supplied crops, and a separate full Poppler rendering. All 44 rows, their authority/program/fee-type/unit/fee positions, the captions and the full notes agree at that resolution. No additional transcription erratum was found. This check knew the earlier summary and transcription; it is **candidate-aware**, not a blind review, an external Ebenezer review or independent-model diversity.

## Source distinctions retained

- The top 27 rows sit under “Fees Set By Douglas County Board of Health - Effective November 1, 2025”; the lower 17 rows sit under “Fees Set By State Legislation - Effective September 1, 2025”. Both columns are labeled “2026 Fee”. These are separate printed source claims, not independently established legal dates.
- STATE-01 actually prints `$0.00`. STATE-16 and STATE-17 leave the fee column blank. The two blank cells remain null, with their exact displayed regions and no invented native line or zero.
- STATE-12's source spelling is **“Intial Inspection”**. The existing additive erratum preserves the frozen pass1's “Initial” while recording the image-supported source spelling. Native text already reproduces the source typo.
- The HACCP rows retain `Hourly` in the unit column and `Up to $620` in the fee column. No fee calculation is performed.
- OWTS double-star links retain the complete `$23` assessment and `$20` / `$3` distribution wording. The retail-food single-star note retains the source's awkward “fee $43 of each” and “Increases to $55 in 2025.” No arithmetic or implied additional charge is supplied.
- The issuing source is Douglas County Health Department. Row citations and the county/state captions are preserved literally; this package does not resolve statutory authority or classify the lower table as a separately acquired state law.

The native extraction places both captions after the table bodies and notes. `SOURCE_QA.json` restores their visual associations without rewriting the native bytes. Display fields only replace NBSP with space and U+2010 with ASCII hyphen and trim leading/trailing whitespace; exact native fields and byte offsets preserve everything else. This does not certify Unicode identity from pixels.

## Evidence and reproduction

`INDEPENDENT_REVIEW.json` binds the original inputs, every checked row, five exact crop settings, the separate Poppler image, source-date qualifications and review limits. `SOURCE_QA.json` binds each nonblank cell to an original native line, UTF-8 offsets, unrotated line box and the 90-degree displayed transformation. The source MediaBox is 612 × 792 points and the rotated page is 792 × 612 points.

The original full PNG is PyMuPDF 1.28.2 at 150 dpi (1,650 × 1,275 pixels). All five supplied crops use a 4× matrix and explicit displayed-PDF clips. The initial-inspection clip `[205, 479, 605, 492]` was supplied by root after creation, then independently reproduced byte-for-byte; no original crop timestamp is invented. The other clips are in the frozen builder. Despite its filename, `two-authority-captions-crop.png` shows the county caption/header only; the state caption has its own crop.

The additional Poppler render uses `pdftoppm` 26.05.0, `-r 150 -f 1 -l 1 -singlefile -png`, with unchanged source bytes. Its SHA-256 is `40e9f4378acdb3934a558b142a94980a987027fb59a7d7a28e25bf84b603fc14`. The validators use only package-local evidence and never execute the old builders or acquisition code.

```bash
PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-status-venv/bin/python -I -B "/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-12/douglas-ehs-source-qa/validate_package.py" --rerender
```

Default verification already replays native extraction, every row/cell/context association, exact byte offsets, rotations, blank regions, the full PyMuPDF PNG and all five crops. `--rerender` additionally reproduces the Poppler image in a temporary directory. A copied package works without the original repository or handoff paths. Python, Pydantic, jsonschema, Pillow, PyMuPDF and—only for the additional replay—Poppler are required. Different renderer versions may fail byte-exact reproduction; that is not permission to weaken a source check.

## Custody and limits

The retained E017 event records a direct HTTP 200 request to `https://www.douglasco.gov/documents/fee-schedule.pdf/` on September 12, 2026 from 23:34:38.261907Z to 23:34:39.577252Z. Its source hash matches this PDF. That acquisition event is distinct from the source's printed dates and any future repository intake time.

The acquisition event includes hashes/path references for transport sidecars and private-header originals that are not copied here. This source-QA package contains the public header file; the broader public custody wrapper is separate. Its validator checks the retained event/source identity, not unavailable transport evidence.

This is source QA only. No adopting instrument, legal currentness, statutory interpretation, county-wide coverage, canonical intake, monitoring enrollment or production lookup publication is established. No source or prior QA record is promoted by this package. Earlier review status strings remain dated evidence of the earlier stage.
