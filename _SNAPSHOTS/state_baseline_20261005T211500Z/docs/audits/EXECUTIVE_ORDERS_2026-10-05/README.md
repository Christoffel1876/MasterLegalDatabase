# 2026 B/D executive-order source and native package

This portable research package retains all21 B/D signed PDFs listed in the
observed official2026Governor catalog: B001–002 andD001–019. It contains84physical
native-text pages and191,521UTF8native bytes; no page has empty native text.

The21row catalog is a read-only browserDOM projection, with exact delegated Drive
links and source-displayed dates/titles. It is not original HTTPHTML. Three browser
navigations occurred; browser resource bytes are unavailable. The temporary tab was
closed. The inherited535-record index is frozen comparison metadata: it lists only
D001–008 for2026, and its listed files are not evidence of retained originals.

Two independently authorized, separately retained request batches supplied the
originals: `new13` used27HTTPrequests/8,350,665bytes and `current8` used16requests/
2,697,319bytes. All43events, including separately recorded same-file303redirects,
are retained under `batches/`. No login, CAPTCHA or external message was used.

`SOURCES.jsonl` identifies documents by complete B/D citations and exact source
file identities. `PAGES.jsonl` binds physical pages to original hashes and native
text under `native/`. B001 andD001 remain distinct; no ambiguous canonical IDs
are assigned. All metadata was validated before writing; original responses remain
unchanged. The catalog's former workstation index path is projected to the
portable `prior/inherited-index.jsonl`, retaining its original hash and row data.

Use Python with `pydantic` and `pymupdf`, then pass the externally supplied manifest
SHA256. These commands perform no network requests or writes:

```sh
python -B verify.py verify --root . --manifest-sha256 EXTERNAL_SHA256
python -B verify.py query --root . --manifest-sha256 EXTERNAL_SHA256 \
  --mode citation --text 'D 2026 019' --limit 1
python -B verify.py query --root . --manifest-sha256 EXTERNAL_SHA256 \
  --mode phrase --text 'pollinators' --limit 2
```

Verification checks closed file membership and hashes; strict metadata models;
full21row source-set equality; governor catalog, citation, delegated file-ID and
receipt joins; per-batch request/byte limits; separately recorded redirects; PDF
structure and complete physical-page sequence; and direct native-text replay.
A query first verifies the entire package and returns bounded full-page matches.
No match proves no legal absence.

Native extraction remains unreviewed against images. The package does not verify
current legal force, later amendments, supersession, applicability, or PDFsignature
authenticity. Aappointments, Cclemency, earlier-year completeness, and continuous
monitoring remain outside scope. No canonical corpus or legalstatus is promoted.
