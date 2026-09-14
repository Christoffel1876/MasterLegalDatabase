---
title: Gunnison Resolution 23-22 complete source review
status: source_review_only
source_currentness: not_verified
answer_safe: false
external_reports_consulted: false
---

# Gunnison Resolution 23-22 source review

This portable package preserves the exact 682,037-byte, 16-page county source and a
complete candidate-aware direct-image review. Read `SOURCE_QA.md` and the strict
`SOURCE_QA.json` together. No new official download or external report was used.

The source was received from Sherlock and entered the repository at
2026-09-13T15:57:35.577123Z. The original reported URL and HTTP acquisition remain
unverified claims. The source's hearing/adoption text, recording stamp and
January 1, 2024 effective wording (with an item 8 exception) remain distinct source
assertions. This review does not authenticate signatures or certify current law.

All sixteen native page texts are empty. The unchanged Apple Vision output is in
`ocr/`; the first sandbox failure is in `ocr-attempt-1/`. The same existing engine
was run once outside that sandbox on these local images, without network access,
installation or permission-setting changes. Its exact executable and Swift source
are retained. Per-page receipts record actual invocation times and output hashes.
The engine itself reports its OS version and Vision revision 3. Settings are
accurate English recognition, language correction off, automatic language detection
off, minimum text height zero, CPU only. Machine confidence values are not reviewer
confidence or legal certainty.

`transcripts/` contains separately authored reviewed printed text. The OCR remains
unchanged even where it omitted the page 14 appeals paragraph or corrupted the
recording stamps. Handwriting, signature-like marks, seal, barcodes, subscripted
numbers and the three struck spans are separately classified. The transcript
normalizes font and quotation-glyph encoding; it is not a pixel-perfect facsimile.
The exact source images govern any glyph ambiguity. No referenced code book or
included-by-reference appendix is reconstructed.

Every transcript byte is covered by contextual blocks. Offsets are UTF-8 byte
offsets in these reviewed transcripts, never fictitious native-text offsets.
Full-page containing boxes are deliberately broad. The 13 integer-bound crops
reproduce exact RGB source-image pixels. Original OCR line boxes remain normalized,
bottom-origin engine observations rather than independently verified word geometry.
All 27 climatic-design entries retain their parent headings, including the page 8
Manual J continuation. Page 13 retains the continuation of page 12 Exception #2.

## Offline verification

From any directory, with Pydantic 2, jsonschema and PyMuPDF 1.28.2 available:

```sh
python -B /path/to/package/validate_qa.py --root /path/to/package
python -B /path/to/package/validate_qa.py --root /path/to/package --rerender --pdftoppm /path/to/pdftoppm
```

The default verifier reads only this package. It never invokes the repository,
OCR, network or a historical intake transaction. Optional rerendering writes only
to a disposable temporary directory. Full PNG byte reproduction requires the same
Poppler rendering behavior; the preserved command used 150 dpi and complete pages.
The validator checks bytes, scope, source relationships, all transcript partitions,
design associations, strikes and continuations. It cannot prove a human/agent visual
judgment merely because a hash matches.

Run the meaningful refusal tests from outside the packet so caches and coverage
outputs do not alter its closed file set:

```sh
PYTHONDONTWRITEBYTECODE=1 python -B -m pytest /path/to/package/test_validate_qa.py -q -p no:cacheprovider
```

The original source, raw OCR and initial failure are immutable. Preparation-history
files retain superseded schema drafts and the additive corrections to a punctuation
reading and design-parent mapping. `FINAL_MANIFEST.json` enumerates every payload;
its own bytes are bound by the delivery receipt supplied to Atlas.
