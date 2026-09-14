---
title: County hosted access and local collection on September 10, 2026
date: 2026-09-10
---
# County hosted access and local collection

The [first hosted county run](https://github.com/Christoffel1876/MasterLegalDatabase/actions/runs/34502202635)
failed at the official Clear Creek Codes & Regulations catalog:
`https://www.clearcreekcounty.us/196/Codes-Regulations` returned HTTP 403. The
workflow had checked two Jefferson catalogs, accepted 245,769 bytes, and checked
zero selected documents. Its report recorded `validation_passed: false`,
`manifest_complete: false`, and an empty change list. Publication was skipped.

This establishes an access failure from the GitHub-hosted run. Response headers
and body were not retained, so the specific server or network policy causing
the denial is unknown. The failure does not establish missing or repealed law.
No identity change, impersonation, alternate route, or access-control workaround
was attempted.

A separate fresh local run started at `2026-09-10T16:30:08.868991Z` and succeeded
using the same strict collector, selected URLs, descriptive user agent, verified
TLS, and one-second pacing. It checked all four catalogs and 30 PDFs, totaling
42,290,819 bytes, and produced exactly 36 allowed candidate paths: 34 original
files and two verification files. Every source matched the earlier discovery
hash and size; the PDFs contain 1,092 pages, and 15 match same-authority hashes
recorded in the inherited download manifest. This is a successful local
collection, not a successful hosted daily run.

Independent verification checked schema validation, all 30 exact catalog labels,
source associations, all original hashes and sizes, the manifest digest, and
preservation-only status with unknown legal status. The catalog inventory contains
89 URL/label pairs for 88 distinct document URLs. The other 58 documents and the
previously documented discovery gaps remain outside the selected batch.

The local report and independent verification are retained under
`.geode_runtime/county-local-live-2026-09-10-report/`; the failed hosted report is
retained as a GitHub run artifact and locally under
`.geode_runtime/county-hosted-34502202635/`. Locally collected evidence is presented
through the separate county data proposal, without claiming a successful hosted
validation run.

The daily workflow remains enabled at 13:17 UTC and reports failures explicitly.
It cannot publish a partial batch when a required source is inaccessible. Resolve
access through a supported automated-access endpoint or an explicitly configured
collector host that can use the official sources normally. A successful complete
scheduled run is required before reporting county automation as operational.
