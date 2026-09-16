---
title: Atlas structural audit of Sherlock005 collection delivery
assignment_id: geode-source-discovery-005
reviewed_at_utc: 2026-09-11T17:29:15Z
reviewer: Atlas / Codex independent structural reviewer
attempt_folder: 20260911T171254Z
comparison_commit: be73a9c2bbc00c81f73392d847f8dc8c6234735c
disposition: retain_delivered_evidence_with_log_and_provenance_qualifications
legal_currentness: not_verified
review_status: pending_intake
network_requests: 0
pdf_transcription_performed: false
original_inputs_modified: false
---

# Disposition

The submitted final log contains **36 events / 27 distinct requested targets**,
but a separate retained Mac JSONL records **seven earlier TLS failures omitted
from that final log**. The combined documented count is **43 events / 27 targets**;
the reported but unlogged IBC spot-check would make it at least 44 if confirmed.
The 12 priority resource IDs/URLs are unique. All 40 inventoried paths exist with
matching sizes/hashes; their aliases resolve consistently. Retain these delivered
bytes and their provenance pending intake. Do not equate the 19 retained PDF
artifacts, four short catalog-note exports, or two meeting packets with completed
legal coverage or adopted/current instruments.

Three corrections are needed to the bookkeeping: seven TLS-failed attempts were
dropped from the final log; the report's extra Mac IBC-PDF 403 spot-check has no
corresponding event; and retry descriptions undercount the actual repeats.
Qualify the four WebFetch exports as selected
derived notes, not full original HTML or complete fee tables. Retain the original
report/logs unchanged and record any correction additively using real or unknown
times. This review performed no public requests or source PDF transcription.

## Verified delivery versions and aliases

The following six published checksums were independently recomputed and match:

| File | SHA-256 |
|---|---|
| `report-20260911T172611Z.md` | `5ce48b5f95758466fef99e5c4c7ea773c6e349ab7a9828f869882ebdc85cf856` |
| `attempted_urls.json` | `76bff20333643a83cc4971268afa0280bf5b412eac775924873befe257d74201` |
| `priority_candidates_final.json` | `6754e9bbb3b9e19daa105811bd4eb14bb4a42b538328e00f8868b58c59c23bda` |
| `artifact_inventory.json` | `a42da64c2c0cb338e852b5b4aed7a83766a147b266eec0607dfe32d6c00c9813` |
| `backlog.json` | `fcbc97ed65fe1812a125fd9f6618803566a673b71c97f57d517298d85702b655` |
| Attempt-folder `geode-discovery-005-package.tar.gz` | `34ff40001ce67434ddab4f8f1450f9e711296e6b557753622e6f0f41f19c27ee` |

The first five live at `handoffs/sherlock-source-discovery-005/`; the archive is
under `20260911T171254Z/`, with its reported 193,493,914-byte size. `ACTIVE_ATTEMPT.txt`
identifies that folder. Top-level report and priorities are byte-identical to the
attempt-folder copies. Top-level attempted log and backlog are byte-identical to
the attempt's `logs/attempted_urls.json` and `logs/backlog.json`. The original
worker files are earlier stages, not silently substituted final deliverables.

All 40 inventory absolute paths agree with their attempt-relative mappings and
their measured lengths/digests. All 36 event body paths and referenced metadata
paths exist; event body hashes match the inventory. All priority local paths
exist and are inventoried. Files in `raw_mac_retries/` match the corresponding
`raw/` copies, including header sidecars. No path alias mismatch was found.

The inventory represents **40 paths / 35 distinct content hashes**:
19 `pdf_original`, 10 `error_shell`, eight `webfetch_export`, two `viewer_shell`,
and one `html_or_shell`. The eight export entries are four notes duplicated in
`raw/` and `exports/`; the two viewer shells have identical bytes. They are not
eight separately recovered catalogs or two recovered ordinance PDFs. Header and
metadata sidecars exist outside this 40-body/export list, so 40 is not a count of
every file in the transfer archive. Structural and legal validity of the PDF
contents are outside this audit.

## Attempt accounting and retry findings

The final log has consecutive event indices 1-36, 27 literal requested URLs, and
claimed UTC times from 17:14:11 through 17:18:38.746442 on September 11. It includes
29 box events / 25 box targets and seven later Mac curl events. The additional
seven Mac urllib failures are different events, not aliases of the curl log.
Combining them gives 29 box + 14 Mac = **43 documented events / 27 targets**.
The earlier Mac attempts already introduced the two OrdRes targets. Both 43/27
and the possible 44/27 count remain below the **60-event / 40-target** caps.

### LOG-000: seven earlier TLS failures omitted from the final log

`logs/mac_retry_attempts.jsonl` records seven `mac_urllib_retry` GET attempts,
sequences 101-107, from **17:18:08.693570Z to 17:18:11.133427Z**. Each failed with
`SSLCertVerificationError` / unable to get local issuer certificate, before an
HTTP status was available. They cover the four catalogs, PFA and two OrdRes URLs.
`logs/mac_retry_attempts.json` instead records seven later `mac_curl_retry` events,
also numbered 101-107, from **17:18:36.627544Z to 17:18:38.746442Z**. These later
events are the ones incorporated as final events 30-36. Same sequence number or
target does not make two different-time/tool/outcome actions one event.

The earlier JSONL records zero bytes and the empty-content SHA-256 for paths that
now contain later nonempty curl bodies. These are reused destinations, not
currently available empty originals. Preserve the failure records and their old
hash/size claims; do not rebind those TLS events to the current 403/viewer bytes.
Their `ok_html` / `viewer_shell_or_html` labels cannot establish successful
content when the same records show TLS failure and no HTTP response. Failed
attempts count under the assignment even when no source body was received.

### LOG-001: extra Mac IBC spot-check is not recorded

The final report explicitly says Mac curl also received 403 when spot-checking
the IBC PDF. Its exact requested URL is:

```text
https://www.fortcollins.gov/files/sharedassets/city/v/5/planning-development-amp-transportation/community-development/building-services/building-code/24-ibc-final-amendments.pdf
```

This target appears only as **event 5, box, HTTP 200**. Neither the seven-entry
Mac retry log nor the final 36-event log contains the reported Mac IBC check.
No corresponding Mac IBC body/receipt is identified in the delivered inventory.
Therefore the report and complete-attempt claim do not reconcile. If that action
occurred as described, the minimum becomes **44 events / 27 targets**; it is a
repeat, not a new distinct target. The report alone does not establish its actual
time, method details or precise response. Supply the existing receipt or record
the unknowns; if the sentence is mistaken, correct it explicitly. Do not invent
a timestamp or silently treat the reported action as nonexistent.

### LOG-002: repeat flags and the one-retry instruction

| Target | Event indices / results |
|---|---|
| Building Code catalog | 1 box 403; 15 WebFetch success; urllib 101 TLS failure; 30 Mac curl 403 |
| Land Use Code catalog | 2 box 403; 16 WebFetch success; urllib 102 TLS failure; 31 Mac curl 403 |
| Fee Schedules catalog | 3 box 403; 17 WebFetch success; urllib 103 TLS failure; 32 Mac curl 403 |
| Public Notices catalog | 4 box 403; 18 WebFetch success; urllib 104 TLS failure; 33 Mac curl 403 |
| Poudre fire-code page | 29 box 403; urllib 105 TLS failure; 34 Mac curl 403 |
| OrdRes 19288428 | urllib 106 TLS failure; 35 Mac curl viewer shell |
| OrdRes 23389379 | urllib 107 TLS failure; 36 Mac curl viewer shell |

The four catalogs each have **three repeated actions after the first attempt**,
although events 15-18 are marked `retry: false`. Different tool/egress does not
erase a deliberate repeat of the same public target. PFA has two repeats; each
OrdRes target has one repeat after its initial TLS failure. This is more than the
packet's one-controlled-retry expectation, even though overall caps were not
reached. The Mac retry sought original bytes after a successful reported text
view; preserve that distinction rather than claiming only one repeat occurred.

Events 35/36 correctly are retries when the earlier JSONL is included, despite
appearing as first attempts in the incomplete final log. The worker backlog had
left those portals unopened before the Mac actions; the first urllib portal
attempts should not be described as retries of a box failure. Calling the final
Mac group the whole Mac attempt history omits the first seven attempts.
Article-7 `v/3` 404 and `v/2` success correctly remain two distinct target URLs.
This audit does not infer access-control evasion or a motive from the retry labels.

## TEXT-001: WebFetch notes are not full catalog or table originals

Inspected all four delivered `.webfetch.md` files. Their contents are short
structured JSON/narrative observations with selected headings, links and values:

| Export | Bytes | Actual retained scope |
|---|---:|---|
| Building Code | 2568 | Document-title/size hints, selected fire referral and an effective-date paraphrase. |
| Land Use Code | 1529 | Seven article labels, four selected ordinance/packet links and a transitional-code URL. |
| Fee Schedules | 889 | Thirteen occupancy/rate values, a 35%/65% split, category/date notes, and mentions of regional/PFA fees. |
| Public Notices | 511 | A brief conclusion about links and selected scope, not the complete notice page. |

The fee export does **not** preserve complete development-review, utility PIF/WSR,
capital-expansion, county or PFA fee tables, service-area details, exemptions,
conditions or their adoption instruments. Its `webfetch_extracted_tables_partial`
scope is directionally cautious, but “HTML table content” and “WebFetch tables”
can overstate the actual note artifact. Treat SD005-10 as **derived selected fee
observations pending comparison**, not a complete fee schedule or original HTML.
The other three exports likewise provide leads/notes rather than full pages.

`retained_bytes: true` can accurately describe the note bytes, but must not imply
retained publisher HTML or an unmodified full WebFetch response. No preserved raw
tool transcript demonstrates that these concise JSON structures are the complete
tool output. Their exact authorship/transformation should remain explicit or
unknown rather than presumed verbatim.

Events 15-18 assign HTTP 200 and `text/markdown; charset=utf-8` to these derived
artifacts. The saved sidecar repeats those assertions; it is not an original
publisher response header. Keep export media type/tool success distinct from
observed server HTTP status and content type. The four identical reported
retrieval times are preserved as claims; neither their equality nor filesystem
times independently verify the tool-call chronology.

## PROV-001: inferred targets and incomplete referral proof

The worker report explicitly says actual SharedAssets hrefs were unavailable
from the WebFetch markdown and seven additional successful PDF URLs were inferred
from catalog titles and historical filename/version patterns: IFGC, IPC, ISPSC,
IEBC, IPMC, and land-use Articles 6/7. Preserve this acquisition basis. A successful
GET at a plausible official-host URL does not by itself prove that the current
catalog linked that exact edition or that the document was adopted.

The ten historical target URLs have a different, inherited-manifest basis. The
packet URLs are present in the retained selected-link notes, but the exact live
HTML anchor wording and complete referral chain are not independently preserved
in those notes. Do not promote paraphrased labels into verified literal anchors.
The four user-assigned catalog URLs are legitimate entry points; their self-
referral fields are not proof of a separate official outbound anchor.

The OrdRes header sidecars retain redirects through the public CookieCheck route
to final `DocView.aspx` URLs with `:443` and `&cr=1`; final log URLs agree. The body
hash for both is `c308fb5a3b976bd60ee8a1aa783adc78d8f940ca0bc8c1155ad527c60de8318a`.
The preserved shell result supports access limitations, not either ordinance's
contents. No session-cookie values are reproduced in this audit.

## SCOPE-001: priorities, adoption claims and authority

All 12 IDs, requested URLs and final public URLs are unique; every priority has a
logged target and resolvable artifact paths. All carry authority
`CO-MUNICIPAL-FORT_COLLINS`, `legal_currentness: not_verified`, and
`review_status: pending_intake`. Remaining PDF artifacts are traceable through
inventory/event URLs even without priority IDs. No dangling selected priority
reference was found. The delivered backlog correctly moves the two OrdRes targets
from the worker's unopened backlog into opened-viewer-shell status.

The two PDF packets SD005-09/11 are correctly distinguished from certified
Ordinances 055/166, with adoption/effective/publication fields null and
`pdf_bytes_retained_not_page_reviewed`. Keep that distinction. The report's
meeting-date/title labels and “proxy for adopting/amending instrument” names
remain leads, not page-verified statements that the sought instrument is complete,
final or enacted. Proposed text, agenda inclusion, first readings, amendments and
certified adopted versions are different artifacts. A packet is not a substitute
for the adopting instrument or its publication record.

The report says 19 PDF artifacts were retained: ten building/wildfire documents,
seven land-use articles and two packets. This is an artifact count, not confirmation
that the full current code, all amendments or every article page is complete.
No physical page counts or legal PDF review are claimed by this structural audit.
Eight selected PDF priorities are provisional resource classifications supported
by URLs/titles, not independently verified enacted status.

Filename-year fields are explicitly identified and must remain nonlegal metadata.
Catalog effective-date statements are not the adoption dates of each linked PDF.
SD005-11's `2025-12-01/02` is an unresolved meeting-label range, not one verified
legal event. Actual city issuance and adoption of the wildfire document require
separate document evidence; a city-hosted state/model-code file is not automatically
a city ordinance. The catalog note itself calls it `local_amendment_pdf` while the
priority more cautiously uses `related_code_document`; prefer the qualified role.

Public Notices is correctly retained as a **mixed-stage catalog**. “No clear
direct PDF links” is the researcher's limited source-view result, not proof of no
relevant ordinances. City/county/PFA/utility fees remain separately attributable.
PFA is a related authority; the backlog's word “district” alone does not establish
its legal form, jurisdiction or City ownership.

## BACKLOG-001 and COMPARE-001: incomplete scope descriptions

The two exact Municode URLs are absent from the requested/final sets, consistent
with the unopened designation. The two OrdRes and one PFA URL reconcile with
their viewer/blocked events. Four WebFetch-only catalog names resolve to the
priority resources. However, the report's regional TCEF and PFA fee-PDF gaps have
no exact URLs in `backlog.json`; the export merely mentions their titles. The
Building Code notes also mention a Residential Air Tightness Testing Protocol and
full code chronology without exact target URLs or separate backlog entries.
Carry these as **unresolved title-only leads**, not fully specified unsearched
targets. Needed adoption instruments likewise remain collection gaps. “Accessible
scope complete” is a stopping description, not demonstrated exhaustion of all
permitted export routes or legal-source scope.

The assignment requires exact-target comparison across all authority owners at
the pinned commit. The report says the manifest was streamed **for Fort Collins**,
while some priority statuses say only “not in directed historical URL sample.”
Those bounded absence claims do not demonstrate the required global-owner search
or prove novelty. The same generic “Hash match is byte recovery only” note appears
on the two packet records despite their null historical hashes; it is boilerplate,
not a claim that those packet hashes matched. Retain exact digest comparisons
separately from sample misses and obtain the full comparison before new-version
classification. This audit did not rerun repository history or compare PDF text.

## Recommended additive disposition

Preserve the original delivery and accept its matching-byte custody checks.
Carry all seven earlier TLS failures into an additive reconciled log, retaining
the overwritten-path distinction. Resolve the reported IBC action and retry semantics from existing records, with
unknown times where necessary. Label the four saved exports as derived selected
observations, retain inferred-target and unverified-anchor qualifications, and
keep the missing exact backlog URLs unresolved. Do not run another source crawl
merely to repair bookkeeping. Source intake, PDF structure/content checks, actual
adoption chains and full historical comparison remain separate gates.

`findings-summary.json` records the verified counts and bounded findings in a
strict Pydantic-validated structure. Schema validation does not certify the source
law or completeness of the external research. All legal currentness remains
`not_verified`; nothing was posted externally or changed in the repository.
