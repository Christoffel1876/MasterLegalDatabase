---
title: Pueblo County and City of Pueblo fee-source discovery
status: complete_bounded_discovery_with_county_gap
prepared: 2026-09-13
legal_currentness: not_verified
answer_safe: false
---

# Result

One City of Pueblo planning fee PDF was preserved from an exact official referral
and one same-host redirect. Pueblo County's starting page returned HTTP403 and
the county source stopped. The authorities remain separate:
`CO-MUNICIPAL-PUEBLO` and `CO-COUNTY-PUEBLO`.

The city original is four physical pages, 228,376 bytes, SHA256
`0ba13c07bede5bf07c24dd8bbbe604c61745e8a73be773a7987e26dfa601414b`.
It is titled “FEE SCHEDULE” under the City of Pueblo's Planning & Community
Development heading. The exact original is `sources/city-pueblo-planning-fees/original.pdf`.

## Acquisition and official link

Five attempted events and four distinct exact URLs used 358,366 retained body
bytes. All four HTTP responses had complete retained bodies: two HTTP200s, one
HTTP301 and one HTTP403. The fifth event was a zero-byte local sandbox/DNS
transport failure before an HTTP response. No private response headers or cookie
values were saved.

| Event | Result | Scope |
| --- | --- | --- |
| E001 | No HTTP response; zero bytes | Initial county hub attempt in the network-restricted sandbox |
| E002 | HTTP200; 124,009 bytes | Official City of Pueblo fee page |
| E003 | HTTP403; 5,818 bytes | One explicitly authorized ordinary-network retry of E001; county source stopped |
| E004 | HTTP301; 163 bytes | Exact city PDF link from E002; same-host Location retained |
| E005 | HTTP200; 228,376 bytes | Exact final PDF response |

The city page was
`https://www.pueblo.us/393/Fee-Schedule`.
Its single selected anchor says “planning and zoning department fee schedule” and
has href `/DocumentCenter/View/21956/Fee-Schedule-110218-COR-LUP-FEE`.
The observed HTTP301 led to the exact final URL
`https://www.pueblo.us/DocumentCenter/View/21956/Fee-Schedule?bidId=`.
The trailing empty query value is preserved, not normalized away.
Final PDF acquisition completed `2026-09-13T00:23:02.695819Z`.
There is no repository intake timestamp because this task did not apply an intake.

The county page was
`https://www.pueblocounty.gov/planning-and-development-department/application-information-page-and-checklists`.
Its publisher denial followed the documented sandbox-permission correction;
there was no publisher-denial retry, alternate identity, alternate route or TLS
bypass. The initial task's reported label
“Fee Schedule Adopted5.8.25-Revised(2).pdf” remains an unverified lead. This packet
does not have a successful county page, a verified county PDF URL or county fee bytes.

## Source and date scope

All four pages have uncorrected native text, totaling 4,923 UTF-8 bytes. Per-page
files and exact concatenation offsets are preserved. Only complete physical pages
1 and 4 were directly viewed for this discovery, using Poppler144dpi renders.
Pages2 and3 were not visually inspected by this task. Any separate later full
source QA is outside this frozen discovery and is not incorporated here.

Both viewed pages visibly print `2-13-26` at the bottom without an adoption or
effective-date label. The URL's older `110218` slug, the response filename
`FEE%20SCHEDULE%202-13-26_202602181221267689.pdf`, and PDF creation/modification
metadata are separate source/file claims. None establishes adoption, enactment,
effectiveness, supersession or continuing legal currentness.

The native extraction puts the printed footer before the body rows and does not
capture the full graphic city logo. It is not a certified reading order or a
reviewed numeric table. Page1 contains nested conditions and repeated visit/size
tiers; page4 retains vacation's road-vacation exception and per-plat note, separate
residential/nonresidential fee entries within the Variance row, and a wireless row. These are observed
structure examples, not calculated charges or full-table certification.

Poppler rendered both first/last pages slowly. A targeted termination was attempted
after a long wait but the process had already completed; `kill` returned “no such
process.” Separate PyMuPDF1.28.2 first/last renders were also produced. The offline
verifier replays the fast PyMuPDF renders and native extraction; Poppler PNGs are
hash-bound without rerunning the slow renderer. See `RENDERING.json` under the source.

## Existing evidence comparison

The complete current61-row manual-source manifest, complete48,390-row inherited
download manifest, and both source registries were checked by exact URL/string
and PDF-SHA equality. The four attempted URLs and city PDF hash have no exact
matches in those named files. This is not proof that no related or equivalent
Pueblo source exists elsewhere. Matching does not normalize URLs, compare text
similarity, scan every raw original or infer freshness from download attempts.

Full file hashes, sizes and scan counts are in `COMPARISON.json`. The manual
manifest is copied exactly. Selected county/municipal registry and ledger records
are retained, along with all413 inherited download rows containing “pueblo” in the
original line. Those413 entries include repeated attempts and are not413 distinct
collected sources. Full legacy/registry files are not duplicated; the portable
verifier cannot independently reconstruct the omitted full-file negative scan.

## Gaps and next decision

- County fee link and bytes remain unavailable after HTTP403. Do not guess the
  download path or reinterpret the initial filename as verified adoption evidence.
- Other city documents visible on the official page, including PUD material,
  development flowcharts and an affordable-housing expedited-review resolution,
  remain unopened. One selected PDF is not the city's entire fee universe.
- Complete fee-row associations, all conditions on pages2–3, and the relation to
  adopting instruments or later changes remain outside this discovery review.
- This packet supports a separate custody/intake decision for the city PDF. It
  does not change canonical data, registry, coverage, lookup results or legal status.

## Portable verification

From another directory, using PyMuPDF1.28.2, Pydantic2 and BeautifulSoup4:

```sh
python -I -B /path/to/pueblo-fee-discovery/verify.py
```

This checks the closed inventory, strict schemas, event/body/time budgets,
official HTML anchor and redirect chain, exact PDF bytes, structural pages,
uncorrected native text and first/last fallback renders. `capture.py` and
`reference_transport.py` are preserved acquisition tools, not the offline entrypoint.
Do not invoke them for another batch. No additional public requests are authorized
by this packet. The captured sources remain `legal_currentness: not_verified` and
`answer_safe: false`.
