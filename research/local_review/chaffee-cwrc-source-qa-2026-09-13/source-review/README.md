---
source_id: chaffee-cwrc-ordinance-2026-02-atlas-directed
authority_id: CO-COUNTY-CHAFFEE
review_status: checked_passages
legal_currentness: not_verified
answer_safe: false
---
# Chaffee CWRC ordinance — source-fidelity review

Ptolemy directly read all **14 full physical pages** and **28 exact full-width half-page crops**, then compared the unchanged local OCR candidate. This is acquisition-aware source-first review, not a blinded assessment. No external reviewer report or outside code edition was consulted. Root acceptance is separate from this review.

The scanned original is 1,146,747 bytes, SHA-256 `0688818dfd4d7726f1eb84b5b57c47580d01b094297a92d4ce88c600ccfe7eba`. Every page has **zero native text bytes** with the recorded PyMuPDF 1.28.2 extraction. The exact on-device Apple Vision outputs contain 432 observations and 26,991 candidate bytes. They are preserved unchanged. The separate checked transcript has 174 page-bound segments and 27,198 bytes; 48 OCR-line corrections are explicit. Handwriting guesses have null checked text rather than certified names.

Read `SOURCE_QA.json` for typed page, OCR, transcript, date, continuation and markup bindings. `CHECKED_PASSAGES.md` contains the complete printed wording and explicit amendment-mark notes. `transcript/` is a derived manual transcript, **not native text**. Checked text retains struck words; it must never be consumed as an unmarked consolidated code. Exact typography, fonts, ligatures and Unicode encodings cannot be established from this scan.

## Source findings and limits

- The instrument states adoption by reference of chapters 1–5 and Appendix A, B and C of the 2025 Colorado Wildfire Resiliency Code. Pages 4–14 contain Exhibit A amendments. The incorporated full code is not present or reconstructed here.
- Page 4 says “Section 102.4” before the heading “103.4.” Page 14 says “Section B101.3” before “Section 101.3.1.” Both mismatches remain.
- Page 6 visibly says “8 feet way.” In the fencing provision, the first “or” after “materials,” is struck; the entire vinyl-fencing exception is also struck. The later “or fire-retardant treated wood” is underlined.
- Page 12 reads “approval or water supply systems.” and uses heading 508.1.2. These are preserved. The cistern items use “under 75,000” and “exceeding 75,000”; this review supplies no exactly-75,000 case or calculation.
- Written-approval conditions, exceptions, negations, referenced editions, units and page continuations are retained. The payment-in-lieu passage supplies no dollar amount and expressly says payment alone does not constitute compliance.
- A recorder stamp and execution marks are visible. The printed chair label is “Gina Lucrezi, Chair”; handwriting identities and seal/signature authenticity are not certified. Recorder fee fields do not establish that every applicable fee is zero.

The printed introduction/reading, proposed-publication, adoption, adopted-publication and recording dates are distinct source claims. The effectiveness clause remains the literal **“30 days after publication as required by law”**. No calendar effective date is calculated. References to Salida, Buena Vista and Poncha Springs do not make this a municipal source or prove a municipality's adoption.

## Custody and offline validation

The exact prior retrieval packet is copied under `custody/retrieval/`, including its closed manifest. D001 was an actual ordinary-TLS HTTP 200 with no redirect, captured **2026-09-13T16:09:37.188686Z–16:09:37.730305Z**. That interval is fresh acquisition evidence, not a canonical repository receipt or legal date. Earlier parent/redirect evidence and the omission of nonselected response headers retain their original limitations. The other two retrieval outcomes are copied only to preserve the original packet's closure; they receive no source review here.

Only the following entrypoint is the portable read-only review verifier:

```sh
python -B /absolute/path/to/this/package/verify_source_review.py
```

It validates closed file membership, strict schemas, exact captured byte hashes, source/native re-extraction, complete OCR-line partitioning, checked-text offsets, source-page and continuation links, and replayed exact crop pixels. It does not independently perform visual reading or certify legal effect.

To replay all 14 complete images with the recorded Poppler executable:

```sh
python -B /absolute/path/to/this/package/verify_source_review.py \
  --rerender /absolute/path/to/pinned/pdftoppm
```

Poppler 26.05.0 executable SHA-256 is `de772e88ab9977ccde25def9b403bf42675d75f5dd82b19fbd7d8123ad183159`; renders use 300 dpi, PNG and the full original PDF. PyMuPDF 1.28.2 was recorded/tested. The verifier compares actual extraction/rendered bytes rather than claiming portability across every future renderer version. Dependencies are Python, Pydantic 2, jsonschema and PyMuPDF.

`prepare_ocr.py`, `prepare_crops.py`, `build_review.py`, `tools/` and copied historical retrieval scripts record preparation methods. **Do not rerun preparation or transport scripts in a frozen packet.** OCR is not automatically rerun by the verifier. Historical absolute paths in command receipts are evidence strings, never instructions to open another original or write to a canonical archive. The standalone manifest hash must be obtained from the sender or parent acceptance; a self-supplied manifest cannot authenticate itself.

Tests run entirely offline against immutable evidence buffers and temporary fixtures. `validation/` preserves test output and measured coverage for `models.py` and `verify_source_review.py`; it does not claim coverage of past network/OCR execution, image interpretation or the one-time builder. Snapshots preserve earlier draft/method-attribution versions. Their content is historical and is not the final review.

No canonical record, registry, raw archive, source inventory, semantic rule unit or currentness status was changed by this task.
