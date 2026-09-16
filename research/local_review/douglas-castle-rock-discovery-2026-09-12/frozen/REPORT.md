---
title: "Douglas County and Town of Castle Rock: bounded source discovery"
date: 2026-09-12
status: completed_pending_root_verification
legal_currentness: not_verified
private_header_originals_present: true
---

# Result and limits

Eight genuine PDFs were preserved from exact official links, totaling **403 physical pages**.
The collection used **31 deliberate request events and 30 distinct exact requested URLs**:
21 HTTP 200 responses, eight explicit HTTP 301 responses, one HTTP 403 response, and one
local DNS failure that did not reach the publisher. The initial DNS failure received one
ordinary verified-TLS route retry. Redirects were separate logged requests; none was followed
automatically. No web search, account, form, outside message, access-denial retry, hidden route,
Git command or canonical source/registry/ledger edit was used.

Public activity ran from **2026-09-12T23:30:32.585997Z** to
**2026-09-12T23:37:12.235005Z**, then stopped. Total retained response bodies are 14,428,668
bytes, including error and redirect bodies. The 50-event/35-target cap was a ceiling, not a
target. `ATTEMPT_LOG.json` and the original per-event receipts distinguish requested URL,
HTTP effective URL, redirect Location, actual times, type, body and header hashes.

All 403 pages have unchanged native PyMuPDF text preserved as **machine text, unreviewed**.
Fourteen complete-page renders were directly inspected for source identity, dates, blank
execution fields and important layout. This is not a complete transcription, fee-row review,
current-law certification or comprehensive county/municipal regulatory inventory.

# Actual retained PDF resources

| Priority | Issuer and resource | Pages | Source identity / qualification |
|---|---|---:|---|
| DCR-01 | Douglas County code amendments bundle | 108 | `E018`, SHA `1c1a8b6a01b6d1a0688763892bca40a7a869e7d3aeb0e229de1567afe8ad5901`; attachment, not full incorporated model codes |
| DCR-02 | Douglas County Building Division Fees | 4 | `E015`, SHA `171b0f5cbc8ff97137f6b8ad726ace0b5b1b3c7b773cab41f1d42930c783a0b8`; printed 6/29/2018 |
| DCR-03 | Douglas County environmental-health schedule | 1 | `E017`, SHA `35e90b9c3b73b414155ed965898c8c270757f1c367cbe50d7645956039dbb687`; separate county/state fee tables |
| DCR-04 | Douglas County O-026-004 fire-code instrument | 11 | `E019`, SHA `7bae2202a56b4bb4572975f520e130aaaed9f1c0737dbcbd94f778327c2ea78e`; unsigned, final date blank |
| DCR-05 | Douglas County O-026-XXX alternate fire-code instrument | 11 | `E026`, SHA `dd76d86c0e3cc29237607cd8f54490834304d49f21d972ee5e4a5cfe1c4bcd7a`; placeholder draft, distinct bytes |
| DCR-07 | Castle Rock Development Services Fee Schedules | 25 | `E013`, SHA `effed38cdfbed3bdc16932336c2b87a151fd8a2dcf53bd0592b77eada9f72c62`; cover states effective July 1, 2026 |
| DCR-08 | Castle Rock Development Procedures Manual | 57 | `E028`, SHA `e1ff722637735f18f69e30c6dc764a0c7d7d07c3ea0c7c3efba256d842ebedc1`; sampled overview updated May 21, 2015 |
| DCR-09 | Castle Rock Transportation Design Criteria Manual | 186 | `E031`, SHA `eb555ffa33ca78330ea8b11445ba2340c9ef3bdc5401ca638f6c715cdbd70dd7`; inner title April 2023 |

The other four priorities are exact non-PDF resources: blocked county code referral DCR-06,
town adoption-summary HTML DCR-10, town fire-permit guidance DCR-11, and the town code
provider's application shell DCR-12. Their body retention does not imply code-text retention.
Exact URLs, referral event chains, source roles, physical-page references, source-stated dates
and byte-bound snippets are in `DISCOVERY.json`. None is approved for canonical intake here.

# Material version and ownership findings

1. **County web migration and zoning gap.** The existing official
   [county homepage](https://www.douglas.co.us/) redirects to
   [douglasco.gov](https://www.douglasco.gov/). The legacy
   [Section 1 source](https://www.douglas.co.us/documents/section-1.pdf/) redirects through the
   new county domain to [eCode360 DO6971](https://ecode360.com/DO6971), which returned HTTP 403.
   No zoning code text was recovered. Several legacy source IDs reuse the same Section 1 URL
   for unrelated categories; those labels are not proof of coverage. No registry was changed.
2. **County fire-adoption evidence is incomplete.** The
   [county code catalog](https://www.douglasco.gov/building-division/adopted-building-codes/)
   says the 2024 IFC was adopted July 14, 2026. Its two adjacent links return distinct 11-page
   PDFs. One bears O-026-004; the other bears O-026-XXX on both its cover and appendix.
   Both leave the second/final-reading date and execution lines blank on physical page 2.
   They state first reading June 9, 2026. These source statements do not verify completed
   adoption. Printed names are not certified signers. The draft text preserves exceptions
   and names fire-protection and metropolitan districts as enforcement participants; it is
   not interchangeable with a Town of Castle Rock ordinance.
3. **County fee dates must stay separate.** The permit page currently links the building-fee
   PDF with a 6/29/2018 footer. Its relationship to the 2026 amendment bundle needs review.
   The one-page environmental schedule labels both rate columns “2026 Fee” but visibly
   assigns November 1, 2025 to the county Board of Health table and September 1, 2025 to the
   state-legislation table. Those captions occur at the end of native reading order.
   Keep the fee authorities, units, OWTS/state-charge footnotes and blank penalty amount
   cells separate. There was no fee calculation or full fee-table validation in this task.
4. **Town schedules and manuals differ in age and role.** The
   [town fee catalog](https://www.crgov.com/2982/Fee-Schedule) supplies a complete 25-page
   [schedule](https://www.crgov.com/DocumentCenter/View/50737/2026-Fee-Schedule-PDF) covering
   building, impact/system development, right-of-way, site-development and fire charges.
   It separately explains town/county use-tax portions. The
   [procedures manual](https://www.crgov.com/2199/Development-Procedures-Manual) is guidance
   used with municipal-code titles, not those complete titles. Its sampled overview carries
   a 2015 update date. The [infrastructure catalog](https://www.crgov.com/2198/Infrastructure-Design-Codes)
   says technical manuals are adopted by reference; only the transportation manual was
   downloaded in this pass. Water, wastewater, stormwater and other manuals remain unopened.
5. **Summaries and provider shells are not legal text.** The town
   [building-code summary](https://www.crgov.com/2178/Adopted-Building-Codes) reports June 30
   and July 1, 2026 changes. Its [fire page](https://www.crgov.com/1691/Permits-and-Inspections)
   says the page is being updated. The linked Municode IFC chapter returned HTTP 200 but
   only an application shell, with no substantive code text. This differs from the county
   provider's HTTP 403. No hidden API or access workaround was attempted.

# Baseline and comparison

`BASELINE_RECEIPT.json` pins 11 actual working files by exact hash, including the complete
48,390-line legacy download manifest, both source registries, coverage ledger, authority
metadata and manual-intake streams. The full legacy manifest was streamed across **all
owners**, not just the 33 rows naming these two authorities.

An earlier direct read of the Git HEAD/ref files yielded
`6d2d12ffeedab8454eefd6b4caaf94b1d1a97d58`; its precise observation time was not recorded.
At copy time the ref yielded `488bad1e02eb41abb744098a1aa4ff5af90120a6`. Working-file hashes
are separate from either commit: committed-blob equality was not checked. Parent reports
that the 59-raw/60-manual-ledger working baseline was committed in 488bad1. Later parent
checkpoints do not rewrite this frozen baseline. No Git commands were used.

The county index and retrieval catalog are still retained LFS pointer bytes in this baseline,
not their missing content. `LOCAL_REVIEW_SUMMARY.json` is present, parseable 498-byte JSON;
that observation does not establish that any original missing LFS object was recovered.
The pointer OIDs/sizes are preserved verbatim in the baseline receipt. Authority metadata
contains 64 county rows and 85 municipal rows; the latter is not a statewide municipality count.

`LEGACY_COMPARISON.json` records 16 matching historical rows, nine source IDs and seven
historical digests, all belonging to these two authorities. These are URL/parent-catalog
associations. **None of the eight PDF digests matches a digest in the full pinned legacy
manifest.** A bounded size-then-hash check found no matching-size ordinary files in the
currently present `_RAW_ARCHIVE` for these eight originals. That does not prove these PDFs
were never collected elsewhere or establish a new legal edition. Old Windows raw paths
remain historical claims, not opened local originals.

# Checklist, unopened leads and next intake

The strict checklist has 24 unique authority/category rows. It distinguishes discovered
candidates, blocked code routes and categories not searched. `UNOPENED_BACKLOG.json`
contains every distinct captured public HTTPS anchor not opened in this pass; this is a
lead inventory, **not authorization or a recommendation to bulk-fetch them**. Fragment,
contact/admin and non-HTTPS links are separately classified in the full discovery record.
Original HTML and complete derived anchor lists remain available per event.

The highest-value next review is the town's 25-page schedule and the county's one-page
mixed-authority health schedule, followed by reconciliation of the county fire drafts and
catalog dates. Canonical preservation can be proposed for exact originals after root
ownership/provenance checks; final-law labels and operative rule extraction must wait for
separate source review. County zoning/code access, town code text, adopting instruments,
county taxes and county engineering standards remain explicit gaps.

# Verification and private-header handling

Run only the read-only verifier:

```bash
PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-status-venv/bin/python -I -B \
  "/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-12/douglas-castle-rock-discovery/verify_discovery.py"
```

It checks closed hashes, schemas, event/redirect accounting, official referral anchors,
all 403 native-page extractions, exact source snippets, 24 category identities, 12 priority
bindings, all public-header derivatives and the full legacy comparison. Optional
`--rerender` checks every retained 150-DPI rendering. It never calls a capture helper or
opens network sources. Historical capture/build scripts are evidence, not verification commands.

Seven original response headers contain Set-Cookie fields. All original `private.headers`
files are **local only** and explicitly labeled in the manifest. Public-header derivatives
remove sensitive fields and folded continuations while retaining other bytes. Any repository
or external package must select those public derivatives and record the omissions; it must
not distribute this entire local folder without that selection. Original HTML is exact source
markup and should be displayed passively when used in user-facing review.
