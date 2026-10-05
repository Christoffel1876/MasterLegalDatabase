---
title: 2026 B/D executive order source and native package
as_of: 2026-10-05
status: research-evidence
legal_currentness: not_verified
answer_safe: false
---

# 2026 B/D executive order source and native package

This portable research package retains all 21 B/D signed PDFs listed in the
observed official 2026 Governor catalog: B001–002 and D001–019. It contains 84
physical pages of native text and 191,521 UTF-8 bytes. No page has empty native text.

The 21-row catalog is a read-only browser DOM projection, with exact delegated
Drive links and source-displayed dates and titles. It is not original HTTP HTML.
Three browser navigations occurred; browser resource bytes are unavailable. The
temporary tab was closed. The inherited 535-record index is frozen comparison
metadata. It lists only D001–008 for 2026, and a listed source path does not prove
that an original file is retained.

The inherited index's per-record `sha256` field hashes the UTF-8 `full_text`
stored in the historical corpus. It is not a raw PDF byte hash. Historical PDF
byte hashes are unknown, so comparing these text hashes with freshly acquired
PDF hashes cannot establish whether publisher files changed. The package's
`prior_index.sha256` is a separate whole-file integrity hash of the frozen index.
Fresh originals have their own raw byte hashes in `SOURCES.jsonl`.

Two independently authorized, separately retained request batches supplied the
originals: `new13` used 27 HTTP requests and 8,350,665 response bytes; `current8`
used 16 requests and 2,697,319 response bytes. All 43 events, including separately
recorded same-file 303 redirects, are retained under `batches/`. No login, CAPTCHA
or external message was used.

`SOURCES.jsonl` identifies documents by complete B/D citations and exact source
file identities. `PAGES.jsonl` binds physical pages to original hashes and native
text under `native/`. B001 and D001 remain distinct; no ambiguous canonical IDs
are assigned. Metadata was validated before writing; original responses remain
unchanged. The catalog's former workstation index path is projected to the portable
`prior/inherited-index.jsonl`, retaining the original whole-file hash and row data.

Use Python with `pydantic` and `pymupdf`, then pass the externally supplied manifest
SHA-256. These commands perform no network requests or writes:

```sh
python -B verify.py verify --root . --manifest-sha256 EXTERNAL_SHA256
python -B verify.py query --root . --manifest-sha256 EXTERNAL_SHA256 \
  --mode citation --text 'D 2026 019' --limit 1
python -B verify.py query --root . --manifest-sha256 EXTERNAL_SHA256 \
  --mode phrase --text 'pollinators' --limit 2
```

Verification checks closed file membership and hashes; strict metadata models;
full 21-row source-set equality; Governor catalog, citation, delegated file ID and
receipt joins; per-batch request and byte limits; separately recorded redirects;
PDF structure and complete physical page sequence; and direct native text replay.
A query first verifies the entire package and returns bounded full-page matches.
A query with no matches does not prove legal absence.

Native extraction remains unreviewed against images. The package does not verify
current legal force, later amendments, supersession, applicability, or PDF signature
authenticity. A appointments, C clemency, earlier-year completeness, and continuous
monitoring remain outside scope. No canonical corpus or legal status is promoted.
