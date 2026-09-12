---
title: Exact CRS Title 1 original-custody investigation
status: original_not_recovered
prepared_on: 2026-09-12
selected_records: [CRS-1-1-101, CRS-1-1-102, CRS-1-1-103]
legal_currentness: not_verified
answer_safe: false
catalog_changed: false
---

# Outcome

The missing **2025 SGML/zip original was not recovered**. Its byte identity remains
unknown. No replacement was written to the repository, and the existing three-record
prototype still has unresolved original custody. No 2025 PDF was located in this
bounded search, so no comparison to a new statutory representation was performed.

The useful recovery route is now specific: obtain the original package and its
acquisition receipt from the former source checkout or backup; failing that, request
the identified 2025 Title 1 source/version through the published OLLS channel after
Michael authorizes contact. A new publisher delivery would be independently retained
evidence, not automatically the same bytes as the missing historical package.

# What the local evidence establishes

The unchanged prototype manifest is
`230077e63761ab368367c6e7e834d9b298a1bfab65d7a07b32aa189488520acb`.
Its existing read-only query verifier passed before public investigation. Its seven
files are copied exactly under `inherited/prototype/`. Full input files remain custody
copies; only sections 1-1-101, 1-1-102 and 1-1-103 are admitted to the prototype.

The expected repository `_RAW_ARCHIVE/crs/` directory and its named zip/title file
are absent. A bounded workspace filename search found no `CRSDATA20251001.zip` or
`title01.txt`; this is not a search of the former Windows machine, cloud storage,
email or every disk. The recorded 2025 edition, July 2, 2026 ingestion/retrieval dates
and Windows path remain inherited claims.

Two distinctions prevent false recovery:

- `UPDATE_LOG.jsonl` records four Title 1 ingestion hashes. The writer computes
  them from **rendered Markdown**, not SGML or zip bytes. The July 2 hash matches
  frozen `body.md` (`6acc70dac37bf035daba04bd0b554b985ac61f4e52424d227d2584e3cfe86ac5`).
  These hashes cannot authenticate a recovered original. The output count changed
  from 877 to 876 during earlier runs; that is not established as a legal amendment.
- `stage_crs_archive` fixes the destination filename `CRSDATA20251001.zip` and
  defaults the directory date to `2025-10-01`. That path is not proof of the
  publisher's original filename, package generation date or acquisition date.

The supporting repository files and four exact selected update records are frozen
under `inherited/`. No known zip/title SGML digest was found in those inspected records.

# Official references preserved today

The [official statutory-data page](https://content.leg.colorado.gov/agencies/office-legislative-legal-services/colorado-revised-statutes-data)
returned ordinary TLS HTTP 200. It describes SGML text supplied as an unmodified zip
on request and links a request form. No public zip anchor occurs in the retained
content region. This establishes a published request route, not the absence of all
public archives. It names **Yelana Love** and `yelana.love@coleg.gov`; the inherited
registry instead spells the address `yelena`. No contact or form submission occurred.

The inherited 2025 title-download URL returned HTTP 404 once; it was not retried.
The [current OLLS publication page](https://content.leg.colorado.gov/agencies/office-legislative-legal-services/colorado-revised-statutes)
links a [2026 title-download page](https://content.leg.colorado.gov/agencies/office-legislative-legal-services/2026-crs-titles-download).
The latter states coverage of the 2026 Second Regular Session. Its Title 1 row links
the following exact resources on `olls.info`:

- `https://olls.info/crs/crs2026-title-01.pdf`
- `https://olls.info/crs/crs2026-title-01.htm`
- `https://olls.info/crs/crs2026-title-01.docx`

Those links were observed in retained official HTML; **none was opened or downloaded**
in this investigation. They are a distinct 2026 edition, not a substitute for 2025.
The original public CRS URL separately redirected to `/laws/colorado-revised-statutes`,
whose page refers visitors to LexisNexis; no LexisNexis request was made.

An [official December 4, 2025 memorandum](https://content.leg.colorado.gov/sites/default/files/2025-12/COLS%20-%20XDOME%20memo.pdf)
describes moving publications from WordPerfect/SGML to XDOME/XML for 2026. Both full
physical pages were directly inspected against native extraction. It reports two
unnamed titles and the Constitution used in a 2025 pilot; it does not identify Title
1 as one of them. The memo provides process context, not a released XML dataset,
public API or statutory text. It warrants checking the requested delivery format
explicitly rather than assuming the SGML-only description covers future releases.

Memo original: `events/E013/body.bin`, 40,376 bytes, SHA256
`e376eca290561967111e58aa2b442105c5f0ae282d99751961ce625c0a967bd9`.
Its printed date is separate from actual HTTP completion at
`2026-09-12T22:05:34.001467+00:00`. Native extraction totals 3,459 UTF-8 bytes on
two pages; logo geometry is not transcribed. Page renders use Poppler at 130 dpi.
The first render failed local font configuration and was interrupted without
producing pages; a preserved local configuration then rendered both pages successfully.

# Exact acquisition limits and custody

**14 deliberate actions / 11 exact target identities**, below the 20-action cap:
nine direct curl requests, one web-tool open, and four search queries. Direct
outcomes were five HTTP 200s, one 301, one 404 and two local DNS failures with no
HTTP response. Each failed request is retained, including zero-byte placeholders
explicitly marked as non-sources. The two DNS failures were followed by separately
logged ordinary authorized-network requests. The observed 301 was followed once as
a separate event; curl did not automatically follow redirects. No access denial,
authentication or TLS check was bypassed.

Retained response bodies total **290,978 bytes**: 248,324 from HTTP 200 and 42,654
from the 404 error page. Largest body is 59,321 bytes. No source reached the 25 MB
single-source or 100 MB total limit. Web-tool internal requests and wire bytes are
unobservable and are not represented as measured. Search results are derived tool
exports, not original publisher response bodies. A combined two-query call has
shared call-bracket times, not invented per-query timing.

`ATTEMPT_LOG.json` reconciles every action and points to immutable evidence. The
network transcript preserves requested URLs, observed response URLs/statuses,
redirect Location, actual local UTC brackets, exact original bytes and hashes.
The public web searches did not locate the exact 2025 title PDF or staged archive
name; search failure is not proof that no archive exists.

**Private custody qualification:** E004 and E006 response headers contain five
Set-Cookie lines in total. These private originals remain unchanged here. Before
any later repository/distributable copy, exclude those two original headers and
produce explicitly redacted derivatives with the original hashes retained. Do not
paste their values. Curl metadata also contains ordinary local connection details.

# Next bounded step

1. Preserve the exact historical-original gap. If an original is supplied, capture
   the transfer/official provenance and new hashes before using it; do not relabel
   a newly generated file as the missing original.
2. If independently approved, acquire the **observed 2026 Title 1 PDF** as a separate
   source. Keep its edition/cutoff, requested/final URL, official referral, native
   pages and acquisition time distinct. Compare only the three selected sections'
   headings, bodies and source notes with exact page/text bindings and any visual
   exceptions. Similarity is not original-byte identity or current-law certification.
3. Any publisher request should identify the 2025 Title 1 edition and desired source
   notes, seek package version/generation/cutoff provenance, and ask which historical
   source formats are retained. The recorded internal filename is a clue, not proof.

No additional discovery, catalog changes, source expansion or automatic next step
is authorized by this frozen report. Source format context does not make legal answers safe.

# Offline validation

Use the existing Python environment containing Pydantic 2, PyMuPDF 1.28.2 and
BeautifulSoup. Validation reads only this portable folder; it makes no network calls:

```bash
env -u PYTHONOPTIMIZE PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-status-venv/bin/python -B \
  '/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-12/crs-original-investigation/build_audit.py' --verify
```

The verifier checks strict report/event schemas, the closed file inventory and all
hashes, exact action accounting/budgets, frozen prototype hashes and three body/heading
spans, plus the memo's exact native-page extraction. It does not certify legal
currentness, unseen sources or the missing original. `--build` and `--freeze` were
one-time preparation operations and must not be rerun over this frozen packet.
