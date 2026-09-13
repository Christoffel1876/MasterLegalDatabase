---
title: Gunnison IWUIC Resolution 2022-33 source-fidelity review
reviewer: Plato
status: complete_visible_source_fidelity_review_qualified_handwriting
legal_currentness: not_verified
---

This package reviews all four physical pages of the preserved Gunnison County resolution scan. It contains 43 ordered text and annotation passages and 14 Exhibit A amendment instructions. These are source-review units, not a count of enforceable rules. No underlying IWUIC volume or later amendment chain was reviewed.

Plato prepared EB-PDF-028 and had already seen its pages for render completeness. This is candidate-aware review, not a blind or external Ebenezer review. All four full page images and seven exact pixel crops were directly inspected; the unchanged candidate was then compared. `INSPECTION.json` records this sequence retrospectively without inventing per-display timestamps. No Grok report, public source request, other language, or other edition was consulted.

`REVIEWED_TRANSCRIPT.md` is the readable full transcript. `SOURCE_QA.json` is the strict typed record, with `/checked_passages`, `/amendment_instructions`, `/scope` and `/limitations`. Every reviewed passage points to its physical page/image and exact half-open UTF-8 range in `reviewed/page-NNNN.txt`. The range includes the passage's two-LF separator. Bracketed graphic and handwriting descriptions are reviewer annotations, separate from source wording. The 6,692 reviewed bytes include those annotations.

All four native PyMuPDF extractions are empty. The original Apple Vision outputs preserve all 5,734 OCR text bytes, observation order and bounding boxes; the original packaged candidate is 6,186 bytes including its page markers. These raw outputs are unchanged. Native, OCR, candidate and reviewed-transcript offsets have separate fields. OCR was Apple Vision revision 3, accurate en-US, language correction off; the original engine and rendering receipts remain preserved. OCR re-execution is not claimed by this review.

The source SHA256 is `0b2dc2e2bdff25b849b29de9285e993d7a353a9209cffbccad2ebc79c7f7b99d`, 114,843 bytes. The source ID is `gunnison-iwuic-resolution-2022-33-sh-ext-003`, authority `CO-COUNTY-GUNNISON`, layer `08_County_Authorities`. The copied canonical record and actual intake receipt bind repository receipt time `2026-09-13T15:57:35.577123Z`. Acquisition remains `received_review_package`: the supplied URL and download times are reported claims, not independently verified official HTTP observations. The canonical archive path is recorded as a claim and is never opened by the portable verifier.

The visible citation is `C.R.S §38-28-201`; the source's 2015 recitals, “on the September” grammar, and Proposed exhibit heading remain intact. The two Section 502.2 headings stay separate. Both vegetation-plan sentences retain their incomplete grammar; no “be” or mandatory obligation is inserted. The hardened-zone paragraph is explicitly linked across pages 3–4, including `0-5 feet minimum` and all material examples. References to Tables 502.1, 503.1 and 603.2 are amendment instructions; no table grids occur in this document.

The resolution distinguishes recordation-triggered applicability to major/minor-impact land-use change permits from the January 1, 2023 start for new building permit applications. These remain source assertions. The source-stated hearing/adoption dates, recorder imprints, typed names, handwritten insertions and seal are not proof of present law or execution authenticity. Apparent attestation handwriting is qualified. No deletion strike was identified; printed underlines and the words Delete/Replace are not applied as edits to any other document.

`COPY_RECEIPT.json` binds 33 selected exact packet copies. The full original packet manifest is included as custody evidence, but this is an explicitly selected subset, not a copy of every EB027/028 payload. Historical receipt fields describing pending review or pending binding remain unchanged; this later QA does not rewrite their chronology. The pre-style source/script/test-log copies are retained as historical preparation evidence.

Run from any directory using Python with Pydantic 2, jsonschema and PyMuPDF 1.28.2:

```sh
PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-status-venv/bin/python -B '/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-13/plato-gunnison-iwuic-source-qa/verify_review.py'
PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-status-venv/bin/python -B '/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-13/plato-gunnison-iwuic-source-qa/verify_review.py' --rerender
PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-status-venv/bin/python -B -m pytest -q -p no:cacheprovider '/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-13/plato-gunnison-iwuic-source-qa/test_review.py'
```

The first command is portable and read-only. The second requires the recorded Poppler 26.05.0 wrapper (or an explicitly supplied `--renderer` with the same checked wrapper identity) and writes only temporary render files outside the package. It compares all four complete PNG bytes. The verifier captures exact buffers once before parsing, checks the closed inventory, schemas, original and receipt identities, all OCR/paragraph spans, date and amendment associations, and every crop's source pixel slice. It does not open historical paths, fetch sources or import another research package's executable code.

The 23 focused tests passed, including resealed source-word changes, altered currentness/handwriting classifications, omitted nested targets, lost continuation links, original candidate and image corruption, invented native offsets, wrong receipt times, unsafe links and a late-file-replacement check. All four rendered PNGs matched the packet images. These checks support reproducible custody and structure; they are not independent proof of visual transcription or legal effect. No canonical records, inventory, lookup adapters, source packets or external reports were changed.
