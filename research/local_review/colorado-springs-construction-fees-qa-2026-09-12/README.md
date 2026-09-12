# Colorado Springs Construction Services source QA

This package reviews the complete seven-page **Construction Services Fee Schedule**, issued by the Colorado Springs Fire Department, Division of the Fire Marshal. It preserves 128 fee rows, nine tables, thirteen definitions, three in-table notes, and every native line. It does not calculate fees or certify current law.

Read [SOURCE_QA.md](SOURCE_QA.md) for the table and complete qualifications. [SOURCE_QA.json](SOURCE_QA.json) contains exact native UTF-8 offsets, physical pages, source-image coordinates, row associations, and context links. The seven unchanged native files total 14,423 bytes. The source PDF is 258,393 bytes, SHA256 `e35de501a011fe55f03140bf91aef54226997d896fec0b6308a2eac9bd40909a`.

Atlas directly inspected all seven full 200 dpi Poppler images before extracting native text, then compared every fee row and complete paragraphs. The title and role were already known; this was source-first review, not a blind transcription. The original observation freeze is preserved, including abbreviated working notes. Twelve crops document detailed checks; the first A-4 crop was mispositioned and retained alongside the correctly positioned follow-up. No native wording or numerical correction was made.

Every fee record requires the complete global plan-review note, implementation statement, other-schedule reference and technology-fee row. Linked table notes and definitions must accompany source-only reuse. The construction table spans pages 2–4, the miscellaneous table pages 4–5, and the re-inspection definition pages 6–7. These continuations are enforced. Context links retain source qualifications; they do not decide which conditions legally apply to a project.

The PPRBD collection and conditional deduction clause is preserved in full, separately from the City's role as issuer. High-pile storage and hazardous-material fees point to a different Code Services schedule. This package does not review that other schedule. The printed date **Effective 07/01/2026** is a source claim, with adoption and legal currentness unverified.

The original response was retained by Atlas's ordinary HTTPS GET from the exact official URL shown in the receipts: request reserved at 2026-09-12T23:10:46.676197Z, complete HTTP 200 response at 23:10:47.380038Z, no redirects. The copied response body equals the source PDF. These are two copies of one document, not two documents. Only public response headers are retained; no cookie or authentication values are present. Server `Date` and `Last-Modified` are not legal dates. The original pre-execution plan still says `PREPARED_NOT_DISPATCHED`; the separate immutable event receipts record actual execution. Plan references to earlier parent HTML are not opened by this verifier or included as authenticated originals here.

## Verify offline

Requires Python, Pydantic 2, jsonschema and PyMuPDF **1.28.2**. Run from any working directory:

```sh
PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-status-venv/bin/python -I -B "/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-12/colorado-springs-construction-fees-qa/validate_review.py"
```

For a portable copy, run its `validate_review.py`, or pass `--root /absolute/copied/package`. Use the real directory path: symlinks in the package or its ancestors are refused. The validator checks the closed file inventory, strict models and schema, exact PDF identity/page count, reproduced native text and geometry, every line's exclusive assignment, table/column associations, complete context, crops, and source-response custody. It never uses the network, runs the downloader, or reads the original repository.

`verify_render.py` optionally reproduces the full PNGs in a temporary directory using Poppler. Byte equality is renderer/environment-specific; source and retained image integrity are checked by the ordinary verifier independently. `test_review.py` exercises actual mutation refusals. `TEST_RECEIPT.json` records the focused run. Preparation scripts are retained as provenance and are not invoked by the read-only verifier. Do not rerun them against this frozen package.

The inventory establishes integrity against the externally retained final manifest hash; it cannot prove that source wording is currently operative or replace direct human source judgment. The package has no canonical raw-manifest, coverage-ledger, legal-rule or answer-safe promotion.
