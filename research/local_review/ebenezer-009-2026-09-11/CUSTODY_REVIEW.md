---
title: EB-PDF-009 custody and derivation review
assignment_id: EB-PDF-009
source_id: larimer-building-fees-sd004-06
verified_at_utc: "2026-09-11T17:37:18.981071+00:00"
status: byte_integrity_and_derivation_verified_pending_visual_review
legal_currentness: not_verified
custody_receipt_sha256: 1d6827eced75091aeb49f9f61502065c76df7df5f9fb4835079f851a0dadf7ed
---

# EB-PDF-009 custody and derivation review

All supplied expected hashes match. Four reports/receipts are preserved as exact `.txt` copies under `received/`; the original Markdown files are unchanged. No discrepancies were found in the packet or derivation bindings.

## Verified scope

- Source PDF: 269,277 bytes, five pages; exact match to the pinned Sherlock004 archive member and manifest hash.
- Manifest and native-page JSON pass their supplied JSON Schemas; all five native records additionally pass the strict Pydantic model.
- All five PNGs match manifest hashes, sizes, and 2550 × 3300 dimensions. Independent Poppler 26.05.0 rendering at 300 dpi reproduced each PNG byte-for-byte.
- PyMuPDF 1.28.2, `Page.get_text("text", sort=False, flags=195)`, reproduced every page’s UTF-8 text exactly. All native evidence source/page/text hashes and candidate byte offsets agree.
- Rebuilding the five-page candidate with its declared packaging markers reproduced all 12,736 bytes and SHA-256 `9556e48b0bd77506576fa4eda189d3751528b4d529aae01c30ed7a378f2fc071`.
- All SHA-256 references embedded in the four returned reports/receipts resolve to verified artifacts.
- Archive, prior audit/custody receipt, supplied inventory and priority-candidate provenance files also match their manifest bindings.

## Frozen return files

| Original | Frozen copy | Bytes | SHA-256 |
|---|---|---:|---|
| `PASS1_frozen.md` | `received/PASS1_frozen.txt` | 21,047 | `bdb41679bc42301267b6655ed8341b900149b98c515c9685c38a2260697ebae2` |
| `PASS1_FREEZE_RECEIPT.md` | `received/PASS1_FREEZE_RECEIPT.txt` | 1,815 | `4754a2d198dd30c8799d6edfece663cef8e126b3ea2ac1dc156198f8ba958b0b` |
| `PASS2.md` | `received/PASS2.txt` | 12,533 | `6487919030d15adf3b7767437d7daa5235602a9906de0377bca75725eebbf787` |
| `PASS2_COMPLETION_RECEIPT.md` | `received/PASS2_COMPLETION_RECEIPT.txt` | 2,087 | `43f8f439ed9177ec43742feb2cc8302370d4165d3aecac81dcb7b8f12c086358` |

The PASS1 freeze-receipt hash was observed during this audit; the user supplied no expected hash for that receipt. The other three return-file hashes match the values supplied through Atlas.

## Existing repository intake

The source also matches `_RAW_ARCHIVE/manual_intake/08_County_Authorities/larimer-building-fees-sd004-06/20260911T171343Z_building_fee_sched_2022.pdf` byte-for-byte. Physical line **7** of `_RAW_ARCHIVE/manual_intake/manual_source_intake_manifest.jsonl` validates as `ManualSourceIntakeRecord`; its `record_id` matches the packet source ID, and its path, hash, and size match the original. Its status remains `archived_pending_pipeline`; `received_at` records repository intake, not original acquisition. No new raw intake was needed or performed. The receipt preserves the exact manifest and record-line hashes.

## Timing and independence

The reviewer claims PASS1 start at 17:15:54Z, freeze at 17:24:32Z, PASS2 start at 17:25:39Z and completion at 17:30:40Z on 2026-09-11. These are claims preserved from the returned receipts.

- Review timestamps, actual page-viewing coverage, prior candidate exposure, and freeze-before-pass2 order are reporter claims. Filesystem mtimes and current hashes do not independently prove those events.
- The received PASS1 digest is bound consistently by both receipts and PASS2, but this audit did not witness a pre-candidate freeze or the reviewer session.
- The reviewer explicitly reports caption-mediated Read plus Pillow crops and automatic vision-caption assistance. This audit does not classify the review as independently blind or unaided.
- Actual audit/custody time, filesystem mtime, claimed review times, packet extraction/render timestamps and upstream source acquisition time are distinct.

## Review boundary

- Byte identity and reproducibility do not establish accurate row associations, visual transcription, legal applicability, current fee rates, adoption, amendment completeness, or present legal force.
- No page images were visually reviewed in this task; substantive findings remain for Atlas review.
- Native text, including its reading order, was reproduced without changes. Candidate remains machine_native_text_unreviewed.
- Original PDF provenance is the delivered Sherlock004 archive. Its upstream URL and acquisition time remain supplied log claims; no network replay occurred.
- The packet manifest is preserved with status prepared_not_sent; this audit records receipt separately and does not mutate that historical preparation record.

`custody-receipt.json` SHA-256: `1d6827eced75091aeb49f9f61502065c76df7df5f9fb4835079f851a0dadf7ed`. No repository files, source files, or returned reports were edited.
