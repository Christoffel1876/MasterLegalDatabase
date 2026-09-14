---
title: Arapahoe planning fees - Atlas reviewed transcription
reviewed: 2026-09-10
status: checked_transcription_pending_legal_review
legal_currentness: not_verified
publication_scope: local_only
---

# Arapahoe planning fee review

Atlas checked all 36 fee-table rows and the surrounding text on both supplied
PDF pages. The machine text detached several application labels and fee symbols
and placed the agency warning before the page body. The checked JSON and
readable table restore the associations visible in the source. The original PDF,
page images, native extraction and Ebenezer reports remain unchanged.

- `reviewed-table.json`: validated source-bound rows, amounts, bases, setup-fee
  exceptions, conditions, policy boxes, revision history and visual annotations.
- `reviewed-table.schema.json`: the strict schema exported from the Pydantic model.
- `TABLE_TRANSCRIPTION.md`: readable transcription generated from the same records.
- `ATLAS_DISPOSITION.md`: disposition of all 20 numbered reviewer findings. Some
  findings are correct reproductions or uncertain typography, not extraction errors.
- `candidate.txt`, `reports/`, page PNGs, manifest and HTTP receipt: unchanged
  evidence supporting the comparison. Local packet-relative paths inside the
  frozen manifest retain their original context; current repository paths are
  recorded in the reviewed JSON.
- `intake-record.json`: custody record for the unchanged PDF under
  `_RAW_ARCHIVE/manual_intake/08_County_Authorities/arapahoe-planning-fees-sd002-14/`.

Two proposed corrections were rejected: inserting a space into `No.26-224`
and moving the ordinary Wireless row after Extension. A visible mark near
Management was preserved as an annotation rather than called an invented
extraction character. The EFR dollar sign lost its row association; a loose
dollar sign remains in the native extraction.

The transcription retains both Preliminary Plat tiers at $2,000 each, the
Plan/Plat wording difference, and the unusual `1-.6 DAM` citation. It also keeps
the $500 setup-fee exception language, deposit/refund terms, the resubmittal
charge condition and the housing reduction cap. It does not calculate a bill
or resolve the relationship between separate Certificate of Designation rows.

## Verification and limits

All source, render, native-extraction, packet and frozen-review hashes were
checked. Replaying native extraction produced the exact packaged page text.
The PDF has two readable, unencrypted pages. Separate image reviews checked
each page's rows, followed by a comparison of the final records. Pydantic,
JSON Schema and exact reference/hash checks passed. One location annotation
was corrected after final review: Conservation follows Site Analysis in the
indented block below Rural Cluster.

The earlier disposition records the proposed integration stage. This README
records its completion. Source custody is `archived_pending_pipeline`; the
research table is not in the recovery coverage ledger or answer-safe fee layer.
The existing OCR-excerpt model was not used for native PDF text. No OCR metadata
or proof of legal currency was manufactured.

The source's September 8, 2026 revision and reference to Resolution 26-224 do
not establish that resolution's adoption or effective date. Those fields remain
null. Its adopting instrument, later amendments, geographic applicability and
eligibility definitions need review. Engineering and outside-agency fees are
separate sources. Full transcription of these two pages is not a complete
Arapahoe County fee inventory.
