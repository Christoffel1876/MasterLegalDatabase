---
title: Mesa County and Grand Junction directed source gaps
prepared_by: Atlas
prepared_date: 2026-09-11
status: research_evidence_only
legal_currentness: not_verified
completeness: not_assessed
public_stop_at: '2026-09-11T20:17:43.011756Z'
---

# Directed source evidence

Seven exact public HTTPS requests returned HTTP 200, preserving **1,911,314 response bytes**: four HTML pages and three PDFs totaling **1,742,822 bytes and 13 physical pages**. No automatic redirects, retries, denied routes, authentication, contact, or hidden endpoints were used. The first three targets came from the frozen discovery package; four additional requests followed exact links on those pages. Collection stopped well before the 20:35 UTC deadline.

The successful bodies and original headers are in `events/E001` through `E007`. `ACCESS_AUDIT.json` binds exact URLs, receipt times, ownership, fifteen bounded observations, all native page bytes, and selected images. Eight full pages were visually inspected, not all thirteen. No complete fee transcription or legal-currentness finding is made.

## Preserved sources

| Event | Exact source | Role and custody |
|---|---|---|
| E001 | [Mesa planning fees](https://www.mesacounty.us/departments-and-services/community-development/planning/applications-and-fees-planning-department-0) | Official county webpage; 44,963 bytes. |
| E002 | [Mesa Building Department](https://www.mesacounty.us/departments-and-services/community-development/building) | County service catalog; 44,058 bytes. Shared administration does not change municipal or district ownership. |
| E003 | [Grand Junction Ordinance 5340](https://www.gjcity.org/DocumentCenter/View/18335/Ordinance-No-5340?bidId=) | Exact previously retained HTTP 301 destination, manually requested once; five-page city ordinance and certification, 1,485,560 bytes. SHA256 `ee803ba2d03f7d7ba93b9135812244f904a83ab36a7f06f8434c93554a2eeb78`. |
| E004 | [Mesa planning fee exhibit](https://www.mesacounty.us/sites/default/files/2022-12/planning-fee-schedule.pdf) | Three-page historical fee schedule; 66,049 bytes. SHA256 `af11318af2ce3ea5e4b1af313f348ab851a855a76418e3878d1a166c084dadb6`. |
| E005 | [Mesa adopted-code page](https://www.mesacounty.us/departments-and-services/community-development/building/adopted-codes-and-regulations-building) | Official county adoption catalog, not the missing local ordinance; 40,764 bytes. |
| E006 | [Mesa permit and plan-review fees](https://www.mesacounty.us/departments-and-services/community-development/building/permit-and-plan-review-fees-building) | Exact official referral to Exhibit A; 38,707 bytes. |
| E007 | [Mesa building Exhibit A fee schedule](https://www.mesacounty.us/sites/default/files/2026-04/Exhibit%20A%20Mesa%20County%20Building%20Department%20Fee%20Schedule%202024%20ADA.pdf) | Five-page schedule labeled adopted by its referring catalog; 191,213 bytes. SHA256 `421aa92efa159b484a091f1ade3589f6abb8a060bb880ec0c0a09e0472e4b9e7`. |

## Bounded findings and unresolved chains

**Mesa planning fees:** the HTML states an application-fee suspension effective 2017 to present, with other fees potentially remaining. Its table contains older year labels. The linked PDF expressly labels its schedule 2017 & 2018. Page 2 of that PDF says the school-dedication resolution expires **1 October 2020**; the webpage says **1 October 2022**. These are conflicting source statements, not corrected dates. The underlying resolution, any extension, and current supplemental fee authority were not acquired. The historical exhibit retains an appeal fee/refund exception and applicant responsibility for extraordinary processing costs; zeroes in other application rows are not an all-fees waiver.

**Mesa building adoption:** the official catalog says its county ordinance adopting and amending building codes cannot be posted, citing HB21-1110. The underlying instrument remains missing; no phone or email contact was attempted. Model-code, state-rule and guidance links remain unopened. The page separately describes January 1, 2027 timing for named electrical/plumbing codes. That statement does not establish a present county or city adoption chain.

**Mesa building fees:** selected pages 1, 3 and 5 preserve maximum/discretionary review charges and source conditions. The source's printed `coast` wording and `$500,00.01` valuation boundary are retained, not repaired. Its 2003 IBC reference is expressly limited to valuation values; other definitions and requirements refer to the adopted version. Filename `2024`, upload directory `2026-04`, PDF metadata and receipt time are not adoption or effective dates. No adoption/effective date was observed on those selected pages; the adopting instrument was not acquired.

**Grand Junction Ordinance 5340:** full pages 1, 4 and 5 were directly viewed. The source identifies a city Title 21 significant-tree amendment with strike/underline conventions. Page 4 states introduction August 5 and second-reading adoption September 2, 2026. Page 5 states certification September 8, publications August 8 and September 5, and **effective October 5, 2026**, after this receipt. These distinct dates are not collapsed into current effectiveness. Signature marks and seals were seen, without authenticating identities. Pages 2–3 were not visually reviewed: page 2 native text is empty and page 3's native text is visibly deficient as extracted. Those are extraction gaps, not assertions that the original pages lack substantive content. No clean consolidated amendment or complete redline transcription is produced.

County schedule references to school districts and the building department's municipal service area do not establish district enactments or assign city ordinances to Mesa County. Grand Junction fire-fee review is separate and was not duplicated here.

## Legacy comparison and verification

The full historical local-download manifest was streamed: **48,390 lines**, SHA256 `dce2b392bc3e81bbb21e31f2a837fdb498d5aa9a79f5b034942a777a82041c51`. Its bytes also matched the file at commit `f160dec2792a2efbcbfee8d37fd3c72477e83cb1`. None of the seven exact requested URLs, exact parent URLs, or seven response digests matched those records. This is a bounded exact comparison, not proof of global document novelty or a change in law. Different URL spellings, other archives and related instruments were not inferred equivalent. The frozen contemporaneous manual-intake manifest contains 43 rows and no matching response digest. It is retained as a dated comparison snapshot, not a live ledger.

The standalone validator replays exact file hashes, all thirteen native page extractions, all eleven saved page renders (only eight were viewed), fifteen byte-bound observations, response/TLS metadata and every observed referral. The full historical 33 MB manifest is not copied into this package; its measured absence comparison is recorded but cannot be recomputed from this portable subset alone. All source/currentness status remains unverified. No repository or canonical records were changed.

Run without producing cache files:

```sh
PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-status-venv/bin/python validate_audit.py
```

`events/E003/headers.txt` contains a response `Set-Cookie` header. It remains exact local custody evidence. Any distributable derivative must exclude/redact that value and explicitly bind the unchanged original hash; no credential or cookie was sent with the requests. The prior seed headers were not copied; its exact redirect is instead bound by the retained original curl metadata and redirect body.
