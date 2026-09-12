# El Paso planning fees: source review

This package preserves the five-page planning fee schedule with **104 fee rows, 15 footnotes and three General Notes**, all directly inspected against full source images. It is research evidence, with legal currentness unverified. The page-3 erosion-label tail remains clipped and unresolved; this is not a claim of completely legible extraction.

Read `SOURCE_QA.md` for the tables and complete notes, and `SOURCE_QA.json` for the typed scope and custody. `REVIEWED_GRID.json` binds every row/cell to page pixels and separate visual-transcript UTF-8 offsets. Every fee row links to `P1-COLUMNS`; its application-fee cell carries global footnote 1, which says the $37.00 technology fee is **included**. Row-specific superscripts remain separate. Blank cells, literal TBD, project codes, exceptions and discretionary notes are retained without fee calculations.

All five native text extractions are empty. There are no invented native offsets. `native/candidate.txt` contains packaging markers only. Initial observations and the full manual visual draft were frozen before OCR was consulted. `VISUAL_ERRATA.json` records three later image-confirmed corrections to that draft, while retaining it unchanged: a semicolon after “Interior Lot Lines,” source “Commerical,” and source “preformed.” `REVIEWED_GRID.json` is the separate corrected grid; it is not a rewrite of the earlier freeze.

The existing local Apple Vision binary failed twice in the initial execution context, then completed one authorized retry on all five pages. The original failure limitations, actual successful invocation times, binary/source hashes, OS version, settings and uncorrected outputs are retained. The OCR output is a comparison aid, not a source of legal accuracy. It misread the comma in $12,145.00 and omitted or misread several project codes and superscript markers. The source's clipped ending is not completed from OCR.

The original PDF SHA256 is `c3bd819da169a58328e7bdfcd8ea65e4a751326a65dce325ad19e5bc868b3e12`. “Effective Date May 1, 2026” is a printed source claim, not a verified effective/adoption date. Actual repository receipt `2026-09-12T22:59:48.795762Z` is separately bound to the completed received-package intake receipt. Claimed earlier HTTP acquisition remains unverified. The earlier discovery batch's exceeded request scope and missing prior non-PDF bodies remain disclosed.

Run the portable read-only verifier from any working directory:

```sh
PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-status-venv/bin/python -I -B "/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-12/el-paso-planning-fees-source-review/validate_review.py"
```

It needs Python, Pydantic 2, PyMuPDF and jsonschema. It does not run OCR, access the network or require the original repository. It checks closed-file inventory; strict schemas; source/page/empty-native bindings; all visual rows, cells, offsets, superscripts, blanks and section links; the exact three-change reconciliation; crop pixels; retained full-page render replay; OCR comparison; and separate received-package provenance. Hash checks do not replace visual judgment. Keep the final manifest hash outside the folder.

`verify_images.py` can independently reproduce all five full pages with Poppler; the recorded replay matched exact PNG bytes. The default verification uses that retained, source-bound replay receipt and does not require Poppler or Apple Vision. `test_review.py` contains **28 focused offline checks**, including rehashed semantic tampering, row/column swaps, missing or duplicated evidence, path escape, symlinks, invented native text, erased clipping, changed custody and false currentness. The passing log and typed receipt are retained.

Preparation scripts are historical implementation records and must not be rerun in this frozen package. They refuse most overwrites or archive draft metadata, but they are not the read-only entry point. The complete original PDF, old visual draft, raw OCR outputs and original copied custody remain unchanged. No production code, raw source, registry, ledger or Git state was edited by this source-review task.
