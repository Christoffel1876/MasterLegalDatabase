---
title: Colorado Register August 10 contents-page diagnosis
date: 2026-09-12
status: source_alteration_confirmed_notice_status_unresolved
legal_currentness: not_verified
scope: One Register issue; no corpus changes or collector run
---

# Two source rows disappeared; the safeguard correctly stopped the refresh

The later direct SOS response contains **48 notice rows rather than the archived
50**. Two proposed notices are absent from both the proposed-rulemaking table and
the calendar of hearings. No replacement row appears. The other 48 parsed rows
are identical except for their shifted row numbers. This demonstrates a source
page change against the preserved local baseline; a parser regression is not
supported by these bytes. It does **not** establish that either rulemaking was
withdrawn, terminated, reidentified, or made legally ineffective.

| Preserved notice ID | Docket | Archived source designation | Old row | Source-stated hearing |
|---|---|---|---:|---|
| RM-2026-daily-6ae185cdffa4fdedd5bb | 2026-00337 | Division of Insurance; 3 CCR 702-4; LIFE, ACCIDENT AND HEALTH, Series 4-2 Accident and Health (General) | 5 | September 2, 2026 |
| RM-2026-daily-fe6fe04b708089735009 | 2026-00328 | Medical Services Board; 10 CCR 2505-10; MEDICAL ASSISTANCE - STATEMENTS OF BASIS AND PURPOSE AND RULE HISTORY | 18 | September 11, 2026 |

The CCR citations come from previously preserved hearing-detail evidence, not
new detail requests. The hearing dates are source statements, not an explanation
for removal. In particular, the September 2 hearing was already past when the
archived contents page was collected; do not infer a simple passed-hearing rule.

The exact inspected issue URL is
[Colorado Register, August 10, 2026](https://www.sos.state.co.us/CCR/RegisterContents.do?publicationDay=08/10/2026&Volume=49&yearPublishNumber=15&Month=8&Year=2026).
No other public source was opened for this diagnosis.

## Evidence and access limits

- Archived HTML: `baseline/_RAW_ARCHIVE/register/daily/3feabe5bec0a599ade2d9829bb2f7df3866f56f95f99b24f8c556c012203ea93.html`,
  65,439 bytes; SHA256 `3feabe5bec0a599ade2d9829bb2f7df3866f56f95f99b24f8c556c012203ea93`;
  recorded retrieval `2026-09-09T23:33:47.917699Z`.
- Fresh exact response: `authorized-route/fresh/event-01.body`, 63,228 bytes;
  SHA256 `8f346e73c4d3af81e7c643d5129966c4420f60c42523d51d6db317dd40eac3a1`;
  actual request interval `2026-09-12T22:57:01.533049Z`–`22:57:02.021975Z`;
  HTTP 200, no redirect, `text/html;charset=ISO-8859-1`.
- The initial sandbox route failed DNS at `22:54:29Z`: curl exit 6, no HTTP
  status, headers, or source body. This is preserved separately in
  `FETCH_RECEIPT.json`; it was not a publisher denial. Root explicitly authorized
  one further attempt outside that sandbox. Both scripts enforce normal TLS,
  5 MB/body, 30 seconds total, and at most two same-authority HTTPS redirects.
  There were two transport attempts, one actual HTTP response, and no redirect.
  No cookies or authorization were sent; no further attempts followed success.
- Raw fresh headers contain Set-Cookie and remain **local custody only** at
  `authorized-route/fresh/event-01.headers`. For a public repository handoff use
  `authorized-route/fresh/event-01.public.headers` and
  `PUBLIC_HEADER_DERIVATIVE.json`; the derived hash is
  `e6f83cc237b45b68d91cf64bf4f7b6e4bc1b5126e2e5c740e7f81ef8ccb508b6`.
  It removes complete Set-Cookie fields, retaining all other bytes. Do not copy
  this entire local packet publicly without excluding the original raw headers.
- `REMOVED_ROW_FRAGMENTS.json` binds four exact HTML byte slices. The old proposed
  rows occupy source lines 326–339 and 521–534; their calendar rows occupy
  1226–1230 and 1304–1308. `contents-source.diff` is a decoded line comparison,
  not a substitute for the original bytes. Passive wrapper identifiers also
  changed; removing only that known wrapper still produces different content
  fingerprints. The missing docket strings occur nowhere in the fresh HTML.

## What the offline replay proves

`FRESH_COMPARISON.json` is the final typed result; its schema is adjacent. It
contains all 48 parsed source rows, the 48 matched archived IDs and the exact two
missing IDs. The parser is the unchanged copied local implementation. All 50
archived rows resolve through 22 exact archived hearing-detail pages, reproduce
their stored notices and agree with state/provenance. The metadata and index
streams each validate 8,120 rows and have identical ID sets. This is schema/ID
checking, not complete substantive verification of those 8,120 notices.

`ARCHIVED_REPLAY.json` preserves the earlier archived-only checkpoint after the
initial DNS failure. Its `fresh_http_body_available:false` and DNS limitation
describe that checkpoint; the later successful capture and `FRESH_COMPARISON`
supersede that access limitation. No original checkpoint was silently changed.

The complete hosted log records requests 1–167. The affected issue is request
96, followed by 71 detail/document requests. Both missing notices' old document
and hearing-detail URLs are absent from the entire log; this agrees with the
later direct response. The report remains failed, with two earlier issues
completed, no changed paths, and zero published additions/updates.

The hosted checkout logged commit
`1d2a95f8eca5ca1c1626d6f4dbc591ad4f1938a7`, then ran pending-data preparation.
Its actual prepared `baseline.json`, state and fresh response were not uploaded
with the five report artifacts. The runner-image commit near the top of the log
is not the repository commit. This audit did not use Git or fetch the prepared
tree. The local state is internally consistent; exact hosted prepared-state
equality and hosted-response byte equality remain unknown. Thus a pending-state
mismatch is not demonstrated, but these artifacts cannot independently exclude
additional hosted-only differences.

The packet copies only the parser import closure, relevant corpus/state files,
one old contents page, 22 old resolution pages and the two missing notices'
original linked DOCX files. The copied state names other sources; their presence
in that file does not mean this packet copied or revalidated them. The DOCX files
were copied and hashed without text extraction or legal-status review.

## Minimum next change, for separate implementation approval

1. Keep the removal gate at `geode/pipeline/register_daily.py:678` and all notices
   intact. Add a strict mismatch diagnostic carrying issue URL, old/fresh source
   hashes, exact missing IDs/dockets, old/fresh row counts and observed source
   rows. Preserve the offending fresh HTML and sanitized transport receipt under
   the run-report directory on failure. Today `_refresh` retains source bytes
   only in memory until the transaction; `refresh_register:517` reduces the
   failure to a string, and `write_run_report:797` cannot preserve its evidence.
2. Add a source-table preflight before attachment fetching. A missing previously
   observed source docket can fail with evidence immediately; ambiguous
   multi-rule/docket identities must still require full identity resolution.
   Do not replace the final ID gate with a weaker docket-only comparison. Use
   these two complete HTML fixtures to reproduce 50→48, unchanged common rows,
   exact missing IDs, and intact corpus/state after failure. Also test a moved
   row, a changed citation, duplicate docket rows, malformed tables, restored
   rows, altered passive wrappers, evidence write failure and no-change replay.
3. Upload the prepared publisher baseline and hashed state/implementation
   identities on failure as well as success. `scripts/publish_register_update.py:120`
   writes `register-candidate/baseline.json`, but the workflow's failure artifact
   retains only `register-refresh/`. Do not expose credential-bearing headers.
4. Before any migration that resumes publication over this discrepancy, review
   the two exact already observed hearing-detail URLs below in a separately
   bounded task. Preserve any explanation as source evidence. If uncertainty
   remains, the run must retain a source-presence discrepancy rather than
   silently deleting records, changing their IDs/status, waiving the gate, or
   reporting a clean/no-change refresh. No such migration is implemented here.

Possible next evidence targets, **not opened in this diagnosis**:

- `https://www.sos.state.co.us/CCR/DisplayHearingDetails.do?trackingNumber=2026-00337`
- `https://www.sos.state.co.us/CCR/DisplayHearingDetails.do?trackingNumber=2026-00328`

## Verification

From any directory:

```bash
PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-status-venv/bin/python -I -B \
  '/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-12/register-daily-diagnosis/verify_diagnosis.py'
```

The verifier checks a closed hash inventory before running either offline
replay, checks JSON schemas, exact fragments and the public-header derivative,
reproduces both results and checks every payload again afterward. Neither replay
runs the collector, writes the corpus, queries Git, or opens a source. No full
test suite, workflow rerun, notice deletion, publishing or production edit was
performed for this diagnosis.
