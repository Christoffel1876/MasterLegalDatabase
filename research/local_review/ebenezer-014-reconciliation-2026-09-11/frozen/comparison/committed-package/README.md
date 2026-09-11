---
title: EB014 Fort Collins Article 1 — portable Atlas source review
prepared_at: 2026-09-11T19:23:01.763409+00:00
extraction_review_status: atlas_seven_page_source_review_complete
external_review_status: external_review_pending
legal_currentness: not_verified
---

# Result and boundaries

This portable package retains the completed candidate-aware Atlas review of all seven physical pages of the supplied Article 1 PDF. It preserves all **13,579 native UTF-8 bytes**, 27 exhaustive native chunks, 29 observations, 36 observation spans, ten checked crop images and twelve embedded PDF links. No substantive word or number correction was identified in the underlying source review. The source, candidate and custody files are exact copies.

External EB014 review remains **pending receipt and reconciliation**. No external report was consulted. Edition, adoption and effective dates remain null and unverified; this does not establish that the document lacks an edition or legal history. Source adoption-by-reference wording does not establish present legal effect. No RuleUnit, coverage or current-law status was promoted.

[reviewed-text.json](reviewed-text.json) contains exact native text with separate visibility, reading-order, image-only and anomaly observations. [candidate.txt](candidate.txt) remains the complete original candidate, including page markers. There is no cleaned or reconstructed legal text.

# Source distinctions retained

- The cover's article banner is visible; its native `1-0` footer is not visible in the checked rendering. The contents page's native banner and `1-1` footer are also not visible. None of those native bytes is deleted. Visible printed labels begin on physical page 4 with `1-1` and continue through physical page 7 with `1-4`.
- City of Fort Collins logo words, accessibility artwork and the photograph remain separate image observations. Their source regions and image hashes are retained; no fictitious native offsets, captions, identities or dates are added.
- Purpose items A–L continue with M–N. Their following qualification stays attached: generally not binding standards, with the source's explicit-reference exception, Sections 1.2.4, 6.8.2 and 6.14.4, and contextual limit. Item M's missing terminal period is preserved.
- Physical page 6 visibly contains the inline `interpretation - 4 - and application` wording. It is retained as a source anomaly. The paragraph continuing onto physical page 7 remains associated with 1.2.4, before 1.2.5.
- Physical page 7's `Articles 2, 3, or 4 a standard` gap and lowercase `it` following `the City.` remain unchanged. Conflict clauses A and B and the complete severability paragraph stay intact.
- All twelve actual PDF annotations are retained: three URI links on page 2 and nine internal contents links on page 3. Their targets are distinct from printed labels. No target was opened; no links are invented for the last two contents entries.

# Custody and portability

Working references are package relative. The complete original source audit is retained under `audit/`; its frozen historical paths and pre-packaging limitations are preserved there. The typed review changes only those file-reference paths into local bindings, and the validator checks that every other source-audit field remains exact. The old helper script is historical evidence; use the portable validator below.

The frozen 31-record raw manifest's physical line 18 and source-provenance line 6 bind the 340,287-byte PDF to its existing received-review intake. Actual repository receipt remains September 11, 2026 at 18:29:00.820696 UTC. Original source acquisition time is unknown. Supplied HTTP URL, time, status and inferred referral route remain claims; this task made no new official download.

The full custody documents also describe other sources, whose PDFs are outside this package. The original packet manifest and preparation record include EB013; that source is not reviewed here. The previously audited 193 MB archive is identified in custody but was not reopened or copied.

# Offline validation

Use Python with Pydantic 2, jsonschema and PyMuPDF:

```sh
PYTHONDONTWRITEBYTECODE=1 python /absolute/path/to/ebenezer-014-2026-09-11/validate_package.py
```

An explicit `--package /absolute/path/to/ebenezer-014-2026-09-11` is also supported. Validation requires no repository imports, original handoff directory, network or writes. It verifies the complete file inventory, source/candidate/page hashes, all seven fresh native extractions, exhaustive native partitions and exact observation bounds, unchanged source-audit visibility and wording, all twelve PDF link mappings, ten source-crop pixel reproductions, and retained custody. Byte validation does not independently certify visual judgment or legal currentness.
