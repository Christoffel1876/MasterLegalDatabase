---
title: Atlas Sherlock009 custody and acquisition audit
assignment_id: geode-source-discovery-009
review_mode: candidate_aware_direct_page_and_custody_review
status: accept_custody_with_provenance_and_claim_corrections
legal_currentness: not_verified
reviewed_at: 2026-09-11T19:25:10.535238+00:00
production_changes: false
network_requests: 0
---

# Disposition

Accept the frozen delivery as received evidence with the corrections below. It contains three new PDF artifacts (27 structural pages), not eight newly collected resources. Exact publisher acquisition is unverified; attachment 5539 is explicitly a browser-print derivative. No record is promoted to legally current, adopted, certified, or complete.

The review consulted the frozen candidate package and root source precheck. It is not blind. I directly inspected all two staff-memo pages, all five rendered-addendum pages, and minutes physical pages 1, 9 and 10: ten full pages. The other 17 minutes pages were structurally checked, not visually certified.

# Custody and scope

97 unchanged delivery files / 71,496,968 bytes; all six advertised hashes pass. All 51 inventory files (19,290,536 bytes), five top-level aliases, and 33 nested aliases match. The main archive includes all inventoried files; the smaller browser archive has 33 files and omits 18 inventory items available in the main archive/loose package. No symlinks, unsafe tar paths or differing alias bytes were found.

# Per-artifact classification

| ID | Retained PDF | Pages inspected / total | Disposition |
|---|---|---:|---|
| SD009-01 | `july13_attachment_5519.pdf` | 1, 2 / 2 | staff recommendation; received pdf download claim not http verified |
| SD009-02 | `july13_addendum_5539.pdf` | 1, 2, 3, 4, 5 / 5 | unsigned extension draft; browser print derivative |
| SD009-03 | `feb09_minutes.pdf` | 1, 9, 10 / 20 | board minutes; received pdf download claim not http verified |

Full source hashes:
- SD009-01: `a1a3dc6c43ba6d9d5e4dafb984d611f224f3f56a0ff10ee659c06e23f52caf2b` (138,232 bytes).
- SD009-02: `7d2d2fef60bb94a83076b060cd46fe0b2864ad2538c7115fa24b1ce6cc1f80d0` (1,037,205 bytes).
- SD009-03: `88e4c7dcceb70d55e286b809471da7531dc1f5493f080d4487a8988706d9f0bc` (10,203,605 bytes).

The addendum metadata identifies Chrome 151 / Skia PDF and a September 11 print time. The staff memo has Aspose metadata dated June 30 / July 6. The minutes have Microsoft Print To PDF metadata dated February 17 and an Administrative Matters filename, while the visible first-page heading says Land Use Hearing. Metadata and filenames do not establish publication, legal dates, certification, or acquisition.

# Findings

## ATLAS-SD009-01 — accept: Immutable delivery custody passes

97 original files (71,496,968 bytes) were copied first and rehashed; no symlinks. All six advertised hashes, 51 inventory entries, five top-level aliases and 33 nested aliases match. Main tar has 54 matching safe file members and all 51 inventoried files. Browser tar has 33 matching files and omits 18 inventory entries that are present in the main package/loose delivery. Archive copies are not additional source captures.

Evidence: `CUSTODY_RECEIPT.json`, `structural-facts.json`.

## ATLAS-SD009-02 — correct: 12 rows do not prove 12 public attempts

The consolidated log has 12 public rows and one local reread, with nine distinct targets: eight HTTPS URLs and one search pseudo-URI. B003 folds a spinner failure and one retry into one public row, establishing at least 13 public attempts. The underlying browser list also separates navigate/download actions that cannot be mapped to exact additional HTTP requests from this package. The known lower bound is within 30 events/20 targets, but complete cap compliance and exact count cannot be certified.

Evidence: `received/20260911T190213Z/logs/attempted_urls.json`, `received/20260911T190213Z/logs/browser_attempts.json`.

## ATLAS-SD009-03 — qualify: Browser acquisition remains reconstructed

Browser clocks are unknown; no successful PDF response headers, redirect chain or saved download-link attributes accompany the notes. Do not promote browser_200_pdf/browser_200_pdf_minutes to observed HTTP status. Five Mac HTTP200 bodies are identical SPA shells, and the hub body is HTTP403; those headers do not authenticate the separately retained browser PDFs. No denied access was retried during this audit.

Evidence: `received/20260911T190213Z/logs/attempted_urls.json`, `received/20260911T190213Z/exports/browser_session_summary.json`, `received/20260911T190213Z/logs/SD009-E001.headers.txt`, `received/20260911T190213Z/logs/SD009-E006.headers.txt`.

## ATLAS-SD009-04 — correct: Attachment 5539 is a browser-print derivative

The frozen PDF is valid received evidence, but its byte hash binds a rendered browser print, not an exact publisher-original PDF. The summary explicitly discloses this and Chrome/Skia metadata is consistent. Keep this classification with every later use; the downloaded-original claim for the other two PDFs is likewise not independently HTTP-verified.

Evidence: `received/20260911T190213Z/exports/browser_session_summary.json`, `received/20260911T190213Z/raw/july13_addendum_5539.pdf`.

## ATLAS-SD009-05 — correct: Same exact claimed URL binds different artifacts

SD007-B012 and SD009-B005 both claim https://larimercoco.portal.civicclerk.com/event/2812/files/agenda/3563. SD007 retained a 194-page packet (15933b2b…); SD009 retained a 20-page minutes document (88e4c7dc…). This is stronger than same path family. Treat the minutes URL as an unresolved acquisition association; do not infer a genuine source replacement, legal update or stable direct download endpoint.

Evidence: `received/20260911T190213Z/logs/attempted_urls.json`, `comparison-evidence/sd007/logs/attempted_urls.json`, `comparison-facts.json`.

## ATLAS-SD009-06 — correct: Printed 2025 is clear, not OCR uncertainty

The priority JSON draft_effective_as_of_ocr value suggests 2026 with uncertainty. Direct inspection of addendum physical page 5 shows August 25, 2025 clearly. Preserve 2025 as a literal draft date and flag its inconsistency without repairing the source. Expiry February 25, 2027 is conditional on no earlier termination/further extension; execution fields are blank.

Evidence: `received/20260911T190213Z/priority_candidates_final.json`, `page-evidence/july13_addendum_5539-p05.png`.

## ATLAS-SD009-07 — qualify: Draft recital and title differences remain unresolved

Addendum physical page 3 cites April 7, 2026 / Reception No. 20260016505, whereas prior recorded January material and the staff memo use a different origin date. No retained final instrument reconciles these. Page 2 says Establish and the body title says EXTEND. Neither the retrospective recital nor the July hearing language certifies adoption of this unsigned draft.

Evidence: `page-evidence/july13_addendum_5539-p02.png`, `page-evidence/july13_addendum_5539-p03.png`, `page-evidence/july13_addendum_5539-p05.png`.

## ATLAS-SD009-08 — accept: Staff recommendation and minutes action are distinct

The two-page July staff memo recommends February 25, 2027 and has a suggested motion; Attachment A is referenced but not included in that file. February minutes page 10 records an August 25, 2026 extension motion carried 3-0. This is useful evidence of recorded Board action, with no separate executed February resolution provided. Only minutes pages 1, 9 and 10 were visually reviewed.

Evidence: `page-evidence/july13_attachment_5519-p02.png`, `page-evidence/feb09_minutes-p10.png`.

## ATLAS-SD009-09 — qualify: Negative search and nonposting claims have limited support

S001 preserves a December 19 fee-search query but no search response/result list; its clock equals report assembly. No separate 2008 CPI search event/result is retained. The July file list is a narrative array, not a preserved rendered DOM or complete catalog response. Unlocated in this package does not establish that an executed instrument or later minutes do not exist.

Evidence: `received/20260911T190213Z/logs/attempted_urls.json`, `received/20260911T190213Z/exports/browser_session_summary.json`, `received/20260911T190213Z/report-20260911T191427Z.md`.

## ATLAS-SD009-10 — correct: Eight priorities are not eight resources

IDs SD009-01 through SD009-08 are unique and all retain CO-COUNTY-LARIMER / pending_intake / not_verified. Only 01–03 bind new PDF artifacts; 04 references an existing SD007 packet; 05–08 are gap placeholders, and 07 combines a fee-adopting instrument and Attachment A schedule. Keep resource and gap counts separate.

Evidence: `received/20260911T190213Z/priority_candidates_final.json`.

## ATLAS-SD009-11 — correct: Backlog strings are missing targets, not discovered URLs

All four backlog url fields contain descriptive labels, not URLs. Normalize them as unlocated targets with URL null, preserving the original file. Staff memo page 1 also visibly supplies three exact YouTube links for January 27, February 9 and June 29 meetings, absent from the backlog; these are unopened video leads, not this audit's sources or proof of the final executed instruments.

Evidence: `received/20260911T190213Z/logs/backlog.json`, `page-evidence/july13_attachment_5519-p01.png`.

## ATLAS-SD009-12 — accept: Exact pinned and current comparisons do not imply current law

All four exported blobs were hash/size checked and independently matched git cat-file at exact commit 0bc3658f6c7c9f378a5083884714dc4111677afd. Full 48,390-row historical manifest and 12-row manual manifest have no direct/linked target URL or incoming hash matches; source registry and county coverage have no exact target URL matches. Current 48,390/38-row manifests likewise have no three incoming hashes, but current manual row 34 matches the old SD007 packet. Among 542 ordinary files under current _RAW_ARCHIVE, no incoming PDF even shares a size, so none shares its bytes. These are custody/deduplication facts, not proof of new law or original acquisition.

Evidence: `comparison-facts.json`.

# Bounded image-supported excerpts

**SD009-01, physical page 2, Suggested Motion**

> I move that the Board of County Commissioners approve the resolution to extend the temporary moratorium on data center facilities until February 25, 2027.

Staff-proposed motion, not a vote or adopted instrument. Line wrapping is normalized.

**SD009-02, physical page 3, First recital identifiers**

> April 7, 2026; Reception No. 20260016505

Two exact identifiers from the first recital, presented as selected excerpts with a separator; not a continuous full-sentence transcription. The recital remains unreconciled.

**SD009-02, physical page 4, Last paragraph**

> This moratorium, as extended, is effective in all of unincorporated Larimer County.

Literal unsigned-draft territorial statement; not a certification of present scope or enforceability.

**SD009-02, physical page 5, Effective/expiry paragraph**

> This resolution shall be effective as of August 25, 2025, and shall expire on February 25, 2027, unless earlier terminated or further extended pursuant to statute.

Literal 2025 retained; line wrapping normalized. Draft with blank DATED, Chair and attestation fields.

**SD009-03, physical page 10, Motion immediately before 5:30 p.m. recess**

> Commissioner Stephens moved that the Board of County Commissioners approve the resolution to extend the temporary moratorium on data center facilities until August 25, 2026.
> 
> Motion carried 3-0.

Directly inspected minutes text, with line wrapping normalized. No independent certification of minutes or exact download endpoint; not the separate executed resolution.

# Unresolved work

- Exact publisher acquisition URL, HTTP status and original-byte provenance for the retained minutes; resolve the exact agenda/3563 association conflict.
- Publisher-original bytes for attachment 5539; current artifact is a browser print.
- Executed/signed/recorded February 9 extension instrument, independently bound to the recorded minutes motion.
- July final minutes or vote and final executed/recorded extension instrument; reconcile literal 2025 and April 7/20260016505 recital before any currentness conclusion.
- December 19, 2023 fee-adopting instrument and Attachment A schedule; equity-reduction resolution remains a separate instrument.
- Numbered 2008 CPI authorization resolution and scope; search completeness is not demonstrated.

Three exact unopened video leads from the July staff memo (not fetched in this audit):

- https://www.youtube.com/watch?v=XOBwdU0Q4fU
- https://www.youtube.com/watch?v=URFMFqDK0zc
- https://www.youtube.com/watch?v=J0rUVvvjkB8

The immutable originals remain unchanged. The audit and schema are local handoff artifacts only; no repository, control-plane, raw archive, registry or legal-currentness changes were made. Standalone machine-check results are recorded separately after running `validate_audit.py`.
