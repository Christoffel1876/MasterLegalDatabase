---
title: Atlas directed access check — two Weld public PDFs
date: "2026-09-11"
status: two_exact_pdf_sources_recovered_pending_intake
activity: independent_Atlas_directed_access_check
sherlock010_dispatched: false
sherlock010_completed: false
legal_currentness: not_verified
---

Both exact Weld PDF leads were recovered through ordinary public HTTPS. This was an independent Atlas attempt; it neither activates nor completes Sherlock010.

| Exact target | HTTP result | Retained bytes | Physical pages | Native text pages | Measured SHA256 |
|---|---|---:|---:|---:|---|
| Ord26-01.3rd-adopted.pdf | 200, application/pdf | 125,953 | 5 | 5 | `2ba9073aa06420e41a5dce98fade56278df96729630f5d61d3ab1c910e839eb0` |
| 2026-ehs-fee-schedule_final.pdf | 200, application/pdf | 174,911 | 3 | 3 | `852801c5ad0056c7b0dde6300e66e86f2e4235ce0efc16471d5210d74aa17ed3` |

The first two attempts, at 19:48:36 UTC, returned curl exit 6 with `Could not resolve host: www.weld.gov`, no HTTP status and no response bodies. Those were client/transport failures, not publisher 403 responses or tool preflight rejections. Their cause is not established by the curl output.

One narrowly authorized ordinary-TLS retry was made per exact URL. The ordinance completed at 2026-09-11T19:49:18.706875Z and the EHS schedule at 2026-09-11T19:49:19.040662Z. Both returned HTTP 200 with TLS verification successful and no redirects. There were four deliberate request attempts total, two distinct URLs, no automated retry and no later source request. No user-agent impersonation, authentication workaround, TLS disabling, hidden route, Mac configuration or browser control was used.

The exact received PDFs are under `authorized-http-retry/ATLAS-WELD-03/ord26-01.3rd-adopted.pdf` and `authorized-http-retry/ATLAS-WELD-04/2026-ehs-fee-schedule_final.pdf`. Each also retains its unchanged response-body bytes, raw response headers, curl metadata, stderr and timed receipt. The first failed attempts remain unchanged in the top-level attempt folders. The two round receipts are separately preserved; `RESULT.json` reconciles all four events and inventories the evidence.

PyMuPDF 1.28.2 opened both originals without repair or encryption. Native extraction was used only to count nonblank pages and UTF-8 bytes: 9,284 for the ordinance and 7,367 for the EHS schedule. No transcription, visual page review, legal interpretation or currentness determination was performed.

Both measured PDF digests equal the historical digest strings supplied in the prepared queue. This is a measured new-body-versus-recorded-hash comparison, not a comparison with reopened historical Windows files. Referral anchors, ownership/adoption evidence, amendments and present applicability were not opened or verified. The filenames, successful downloads and native text do not establish adopted or current law. No repository source, raw archive, control plane, ledger, queue, bot or Git state was changed.
