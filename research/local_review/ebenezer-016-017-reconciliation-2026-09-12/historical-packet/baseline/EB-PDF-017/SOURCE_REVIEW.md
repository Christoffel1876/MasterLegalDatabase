---
title: EB017 Greeley proposed water and sewer PIF notice — source QA
prepared_at: 2026-09-11T19:38:12.347383+00:00
review_mode: candidate_aware_source_review_before_external_report
external_reports_consulted: false
legal_currentness: not_verified
native_changes: none
---

# Scope and result

Both full pages and two diagnostic crops were directly inspected. The notice is dated November 20,2020 and anticipates Board review on December 16,2020. Its March 1,2021 effective-date statement expressly says **assuming they are adopted**. The second-page heading alone does not establish adoption or current fees.

The two native pages retain all 1,316 bytes unchanged (797+519), with exact candidate offsets and exhaustive byte partitions. The table reconstruction binds all 24 data cells to native spans and PDF coordinates, preserving separate headings and all header positions.

# Page 2 left table

**Plant Investment Fees (PIFs) Based on Tap Size**

| Water Tap Size | Water PIF | Sewer PIF |
|---|---:|---:|
| 3/4" | $11,200 | $6,800 |
| 1" | 18,700 | 11,400 |
| 1-1/2" | 37,300 | 22,800 |
| 2" | 59,700 | 36,400 |
| 3" | 130,700 | 79,700 |
| 4" | 223,900 | 136,700 |
| 6" | 466,500 | 284,800 |

# Page 2 right table

**Plant Investment Fees (PIFs) Single Family Residential Units**

| [visibly blank source header] | Water PIF | Sewer PIF |
|---|---:|---:|
| Single Family - 3/4" | $11,200 | $6,800 |

The right-hand row interrupts the native stream between the first and second left-hand rows. It remains a separate table. Dollar signs are printed only in the four cells shown with `$`; none has been added to the other 12 amounts. The blank right-hand header is described here rather than invented as a source label.

# Image-only wording and distinct contacts

The City of Greeley / Colorado logo at the upper left and the full footer are absent from the native candidate. The footer reads:

> Water and Sewer Department • 1100 10th Street, Suite 300, Greeley, CO 80631 • (970) 350-9811 Fax (970) 350-9805
> A City Achieving Community Excellence

The round separators and spacing above are a readable transcription, not an exact Unicode claim. The body says **(350-9801)**; the footer says **(970) 350-9811**, with fax **(970) 350-9805**. These distinct numbers remain as printed. Erik Dial, Utility Finance Manager, Greeley Water and Sewer is a printed closing, not an authenticated handwritten signature.

# Source observations

- **EB017-O01** Notice date is November 20, 2020. Printed source date, not retrieval or adoption.
- **EB017-O02** The notice addresses Weld County homebuilders, building contractors and plumbing contractors. Greeley issuer and Water/Sewer context remain distinct from the recipients; this is not a Weld County fee enactment.
- **EB017-O03** The Board will review updated fees for adoption at its December 16, 2020 meeting. March 1, 2021 is expressly conditional on adoption. The page 2 effective-date heading must be read with the page 1 condition; this notice does not establish adoption or current applicability.
- **EB017-O04** The notice points to the schedule on its reverse; the delivered second page contains the two tables. Preserve the two-page source relationship, not two unrelated fee schedules.
- **EB017-O05** The body contact number is (350-9801). The image-only footer separately prints (970) 350-9811 and Fax (970) 350-9805. Do not silently harmonize different source numbers.
- **EB017-O06** Printed closing: Erik Dial / Utility Finance Manager / Greeley Water and Sewer. No handwritten signature is visible in the closing. A printed name/title is not signature authentication.
- **EB017-O07** Two side-by-side tables have separate headings and header rows; the first right-hand column header is blank. Native extraction interleaves their titles, headings and first data rows.
- **EB017-O08** Native order gives the first left row, then the right Single Family row, then resumes the left table at 1-inch. The typed table structures restore only visual row associations. No source characters are rewritten, and the right row is not appended within the left table.
- **EB017-O09** All 16 fee amounts were inspected. Dollar signs occur only on the first left row and the single-family row: four amount cells in total. The remaining 12 amount cells have no printed dollar sign; preserve that typographic fact rather than filling symbols into a source transcription.
- **EB017-O10** Seven left tap labels are 3/4",1",1-1/2",2",3",4",6". Displayed quote marks and the hyphenated fraction are retained as native characters; exact raster Unicode identity is not independently inferred.

# Validation and boundaries

`validate_source_review.py` checks strict schema validation, copied-input hashes, PDF re-extraction, all native byte partitions and candidate slices, exact cell/header anchors, cell geometry and every row association. It performs no network or writes. Image-only wording is a scoped direct visual finding, not machine-certified OCR.

No source, packet, candidate, repository, registry or control-plane file was edited. No external report was read and no message was sent externally. The notice’s recipients do not make it a Weld County enactment; all legal currentness remains unverified.
