---
title: "Colorado Register source discrepancy: August 10, 2026 issue"
recorded_date: 2026-09-12
status: public_subset_source_discrepancy_preserved_legal_status_unresolved
legal_currentness: not_verified
---

# Preserved source discrepancy

The archived August 10 issue has 50 notice rows. The independently captured September 12
contents page has 48: dockets **2026-00337** and **2026-00328** are absent, with their hearing
calendar entries also absent. The 48 common notice rows match except for row numbering.
The two later hearing-detail pages remain accessible; each has the same 16 labeled table
fields as its archived counterpart. Their whole HTML bodies differ. This package does not
explain the discrepancy or authorize deleting, renaming or changing the status of either notice.

| Docket | Preserved notice ID | Printed hearing date | Later detail fields |
|---|---|---|---|
| 2026-00337 | RM-2026-daily-6ae185cdffa4fdedd5bb | 09/02/2026 | 16 unchanged |
| 2026-00328 | RM-2026-daily-fe6fe04b708089735009 | 09/11/2026 | 16 unchanged |

[Official issue URL](https://www.sos.state.co.us/CCR/RegisterContents.do?publicationDay=08/10/2026&Volume=49&yearPublishNumber=15&Month=8&Year=2026),
[official docket 337 detail URL](https://www.sos.state.co.us/CCR/DisplayHearingDetails.do?trackingNumber=2026-00337),
and [official docket 328 detail URL](https://www.sos.state.co.us/CCR/DisplayHearingDetails.do?trackingNumber=2026-00328)
identify the captured sources. These links are provenance, not a fresh currentness check.

## Evidence and chronology

- `historical-diagnosis/FRESH_COMPARISON.json` preserves the 50/48 comparison, complete parsed
  rows, notice IDs, old/fresh source hashes, byte counts and source capture times.
- `historical-diagnosis/REMOVED_ROW_FRAGMENTS.json` binds four exact original HTML slices.
- `hearing-details/DETAIL_REVIEW.json` binds both old and fresh detail originals and every
  labeled table field to exact HTML byte ranges and fragment hashes.
- `CUSTODY_RECEIPT.json` identifies all 115 exact copies, three exclusions, six passive views,
  actual packaging/check times and preservation limits.

The archived issue records retrieval on September 9 at 23:33:47.917699 UTC. A September 12
22:54:29 local DNS failure yielded no publisher response. The separately authorized route
attempt returned the fresh issue body at 22:57:01.533049–22:57:02.021975 UTC, HTTP 200,
without redirects. The two separately authorized detail requests returned HTTP 200 at
23:05:07.621905–23:05:07.929394 and 23:05:07.954918–23:05:08.168857 UTC, without redirects.
No requests were made while assembling this package.

The historical diagnosis's statements that no fresh details had been opened describe its
own earlier phase. The subsequent detail records add evidence without altering that frozen
history. The hosted failure was run 34694019784; its prepared baseline and exact issue HTML
were not preserved in the received hosted artifacts. The later local source comparison does
not establish byte equality with that hosted response or the time the rows disappeared.

## Public subset and passive display

This is **not either complete original local packet**. It contains 96 of 97 diagnosis files
and 19 of 21 detail files. Exactly three raw response-header files containing Set-Cookie
fields remain local. The copied historical complete manifest still lists its omitted raw
header; the outer custody receipt explicitly reconciles that absence. Original hashes are
retained, with separately named public-header derivatives. No derivative replaces an
original under its original filename.

During packaging, all three original-to-public transformations were directly rechecked:
remove sensitive header fields and folded continuations, preserve all other bytes. Only
Set-Cookie fields were present among the named sensitive fields. Exact omitted values were
also checked for matches in the selected copied payloads; none was found. This limited check
is not a comprehensive secret audit. A portable recipient can verify the public bytes and
recorded bindings, but cannot replay removal against private originals that were not exported.

Original HTML remains exact evidence. Use these escaped, script-free byte displays for
human inspection; they are not new publisher responses or visual transcriptions:

- Issue: [archived](passive-views/issue-old.html), [later capture](passive-views/issue-fresh.html).
- Docket 337: [archived](passive-views/hearing-337-old.html),
  [later capture](passive-views/hearing-337-fresh.html).
- Docket 328: [archived](passive-views/hearing-328-old.html),
  [later capture](passive-views/hearing-328-fresh.html).

## Offline verification

Run with Python, Pydantic 2, jsonschema and BeautifulSoup available. The preserved parser
imports its copied dependency closure. The local audit environment is:

```bash
PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-status-venv/bin/python -I -B \
  "/Users/mcoors/Documents/Project Geode/MasterLegalDatabase/research/local_review/register-source-discrepancy-2026-09-12/verify_public_package.py"
```

The verifier works from any working directory, closes the complete public inventory before
and after replay, checks exported schemas, source hashes, byte slices, metadata/source ID
association, both 16-field tables, HTTP receipt bindings and passive views. It invokes only
the copied offline parser/comparison in isolated subprocesses, with no collection or writes.
The copied original full-packet verifier expects the excluded raw header and is intentionally
not the verifier for this selected export. Do not execute historical capture/preparation
scripts as part of verification.

Hash inventories establish integrity relative to their recorded identities; retain the outer
manifest digest independently. They do not authenticate publisher intent or confer legal
status. There is no operative-rule ingestion, current-law finding, coverage promotion,
notice migration, workflow rerun or publication in this evidence package.
