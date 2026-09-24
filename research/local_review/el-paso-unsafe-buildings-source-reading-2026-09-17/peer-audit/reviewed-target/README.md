# Unsafe-buildings extraction defect review

Atlas directly displayed all eight pages of the retained El Paso Resolution17-321 / Ordinance18-03 PDF. The unchanged native extraction contains damaged words, a destroyed cost-recovery condition, and omitted execution/attestation material. REVIEW.json records23 bounded findings, including source anomalies that must not be repaired and unresolved seal text. CORRECTED_READING.md is a candidate-aware readable derivative with explicit gaps and normalization, pending separate peer review.

The source remains the exact archived eight-page327,510-byte artifact, SHA25686eed9d885a9cec1cb01528318f66f8eed525ddb0860655a1983865bfa196d00. It was originally received through Sherlock, with original HTTP acquisition not independently witnessed. The raw original and canonical intake record remain unchanged. The full canonical custody note is retained under inputs/.

All eight complete images were rendered by the actual command:

    pdftoppm -r 120 -png <canonical-original.pdf> pages/page

The page8 execution crop was rendered from the same original by:

    pdftoppm -f 8 -l 8 -singlefile -r 240 -x 150 -y 760 -W 1690 -H 650 -png <canonical-original.pdf> page-8-execution-crop

These commands are preparation descriptions; per-command wall-clock times were not separately captured. Review date is2026-09-17. Native candidate uses PyMuPDF1.28.2 `page.get_text()`, preserved with physical-page packaging markers. This packet is not a blind/source-first experiment; root had seen native excerpts before displaying source pages. No external report informed the initial review. Ebenezer was assigned only pages1–2 in a separate packet.

Run `python -B verify.py` to check closed file membership, every hash/size, schema/Pydantic validation, exact native reproduction, canonical source binding and finding excerpts. Add `--rerender` to compare the eight full-page PNGs and page8 crop using local Poppler. Mechanical verification does not prove visual comprehension or legal validity.

No full seal transcription, handwriting identity, operative-currentness, complete amendment/repeal chain or municipal election is certified. No corrected PDF, atomic rule record, or inventory review promotion is produced. A future accepted correction must preserve this package and identify the superseding derivative explicitly.
