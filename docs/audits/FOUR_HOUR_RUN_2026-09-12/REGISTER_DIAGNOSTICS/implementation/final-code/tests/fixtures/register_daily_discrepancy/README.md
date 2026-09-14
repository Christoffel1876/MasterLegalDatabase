---
title: August 10 Register source-disappearance regression fixtures
status: preserved_source_snapshots_for_offline_tests
legal_currentness: not_verified
---

# Source custody and scope

`archived.html` is the exact 65,439-byte SOS contents page already preserved in
the repository, SHA256
`3feabe5bec0a599ade2d9829bb2f7df3866f56f95f99b24f8c556c012203ea93`.
Its recorded retrieval is September 9, 2026 at 23:33:47.917699 UTC.

`fresh.html` is the exact 63,228-byte response received September 12, 2026 at
22:57:02.021975 UTC, SHA256
`8f346e73c4d3af81e7c643d5129966c4420f60c42523d51d6db317dd40eac3a1`.
The complete capture is frozen outside the repository in
`handoffs/run-2026-09-12/register-daily-diagnosis/`. The response was HTTP 200 with
no redirect and `text/html;charset=ISO-8859-1`; no response headers are copied here.

Both bodies came from the exact URL:

`https://www.sos.state.co.us/CCR/RegisterContents.do?publicationDay=08/10/2026&Volume=49&yearPublishNumber=15&Month=8&Year=2026`

The bodies retain original scripts, markup, whitespace and source text. They are
test input only. Tests never execute the scripts or request any linked source.

`selected_provenance.jsonl` contains the 50 Pydantic-validated provenance records
for this issue, serialized from the earlier complete provenance stream.
`selection.json` binds the full original stream digest, selected IDs, output
digest and both original HTML digests; its schema is adjacent. This selection
does not claim to copy or revalidate all source files named by those records.

The later table has 48 rows: proposed dockets 2026-00337 and 2026-00328 and their
calendar entries are absent. All common notice rows match apart from row
numbering. The cause and legal status remain unresolved. No fixture or test
authorizes notice deletion, reidentification, a gate waiver or a current-law claim.
