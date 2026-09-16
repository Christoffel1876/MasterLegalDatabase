---
issued: 2026-09-11
status: prepared_for_atlas_dispatch
legal_currentness: not_verified
---

# Pass 2 — source-to-OCR comparison

This assignment covers **EB-PDF-012 only**, source `larimer-data-center-moratorium-sd004-04`, complete physical pages **1 and 2**. Start no new document at or after **2026-09-11 20:50:00 UTC**. Stop all work by **2026-09-11 21:20:00 UTC**, preserving any partial result truthfully. Check actual UTC before starting. No EB-PDF-013 or further document is authorized.

Begin only after the unchanged pass 1, freeze receipt and recorded hash exist. Verify the candidate against the manifest before opening it. Status is `machine_ocr_unreviewed`. Native PyMuPDF extraction was empty on both pages. The candidate instead preserves Apple Vision revision 3 output from the full-page 300 dpi PNGs: every observation text is kept in returned order, joined with one LF. No words were corrected, normalized, filtered or inferred. Physical-page start/end markers are packaging, not source text.

Under `02-candidate-text/larimer-data-center-moratorium-sd004-04/ocr-evidence/`, exact raw engine JSON is retained with observation order, text, confidence and boxes. Strict page records bind source/page/image, actual OS version, adapter hash, settings, recorded output-file timestamp basis, derivation time and text hashes. Apple Vision JSON is not Tesseract TSV and has no Tesseract PSM; those fields are explicitly not applicable. Engine confidence is not an accuracy finding. OCR can omit, invent or reorder text, especially signatures and handwriting.

Reinspect both source images in full, including every region where the candidate agrees with pass 1. Return physical-page coverage and discrepancy tables. Each discrepancy needs source SHA256, physical page, location/region, candidate wording, source-supported wording or unresolved alternatives, error type, severity, explanation and visual support. Record uncertainty before inference. Preserve source anomalies and separate printed names from signature/handwriting notes. Do not infer adoption, effective date, amendment completeness or legal currentness beyond the exact source wording. If pass 1 needs correction, add an errata table rather than editing the frozen file. Disclose captions, summaries, assistance, exposure and tool limits.

Save `PASS2_REVIEW.md`, hash it, and save `COMPLETION_RECEIPT.json` binding unchanged pass-1/source/images/candidate/manifest and pass-2 hashes. Record actual UTC times, both-pass page coverage, unresolved regions, reviewer/model and time/cost if known (otherwise unknown). Use `completed_pending_atlas_verification` only if both complete pages received both passes; otherwise use `partial` or `blocked` and explain exactly. Keep `legal_currentness: not_verified`. Deliver the result and exact paths, then stop.
