---
title: County source reacquisition on September 10, 2026
date: 2026-09-10
---
# County source reacquisition — September 10, 2026

The first bounded source check preserved **four official catalog pages and 30
directly linked PDFs**, totaling **42,290,819 bytes**. All final document responses
were HTTP 200, passed PDF parsing, and required no password. Their SHA256 hashes
were independently rechecked after download. This establishes source access and
preservation for the selected batch, **not complete or legally current county
coverage**.

No tracked corpus, registry, or index was changed by discovery. The inherited
latest LFS objects remain unresolved; this work does not reconstruct them.

## Exact collection scope

Every link in each preserved page's `#page` content region was inventoried.
The four pages contain **88 distinct directly linked document URLs**. The initial
batch selects 30 of those documents; the other 58 remain explicit exclusions.

| Official catalog | Direct documents listed | Selected | Selected PDF bytes | Selection |
| --- | ---: | ---: | ---: | --- |
| [Jefferson zoning](https://www.jeffco.us/2460/Zoning-Resolution) | 51 | 2 | 29,067,535 | Complete zoning PDF, document 1828; wildfire resiliency code, document 57852. |
| [Jefferson land-use policies](https://www.jeffco.us/303/Land-Use-Planning) | 17 | 17 | 1,679,632 | Every document directly listed on this particular catalog page. |
| [Clear Creek codes](https://www.clearcreekcounty.us/196/Codes-Regulations) | 7 | 7 | 8,271,661 | Animal control, onsite wastewater, matters of state interest, road design, snowmobiles, subdivision, and zoning PDFs. |
| [Clear Creek ordinances](https://www.clearcreekcounty.us/339/County-Ordinances) | 13 | 4 | 2,798,253 | Ordinances 16, 17, 18, and 19: open fires, burning permits, fire-code provisions and fees, and short-term-rental licensing. |

Selected PDFs total **41,817,081 bytes and 1,092 pages**. The catalog HTML adds
473,738 bytes. All 17 Jefferson land-use documents were collected from that page,
but this does not establish that the page lists every applicable county policy,
fee, permit, or later amendment. Category names above follow publisher labels
and require substantive review.

The complete Jefferson zoning PDF is 27,312,142 bytes. An initial attempt capped
at 25 MB failed without a saved body. Its declared size was then checked with
HEAD, and a retry capped at 30 MB succeeded. The failed attempt remains in the
evidence record. The aggregate ceiling stayed at **100,000,000 bytes**, with no
additional documents or recursive crawling.

## Visible exclusions and unresolved coverage

The 58 omitted document URLs comprise:

- **48 separately published Jefferson zoning section files.** The whole zoning
  PDF was selected, but equivalence to every separately published section has
  not been verified.
- **One Jefferson WUI overlay map PDF.** Its separately linked interactive map
  was also left outside the selected document batch. Spatial applicability
  remains unresolved.
- **Nine other Clear Creek ordinance PDFs.** The complete catalog text and links
  were preserved, including its repeal and replacement labels; those nine
  document bodies were not collected.

Clear Creek's codes page also links to separate adopted-building-code and
marijuana-licensing/excise-tax pages. Those two nested pages were recorded as
unresolved discovery targets and were not followed. Its county-ordinance link
points to one of the four catalogs already collected.

Publisher labels describing repeal, replacement, adoption, or effective dates
remain source evidence for review. Their presence does not independently prove
the currently operative rule or resolve later changes. Notices, amendments,
fees, and requirements published outside these four pages remain outside this
batch. The planned two-county, two-municipality, two-district pilot is still
incomplete, and this discovery did not activate county monitoring.

## Evidence and historical matches

**15 of the selected PDFs match a SHA256 previously recorded for the same
authority in the inherited download manifest.** Each matching attempt's row,
source identifier, URL, and retrieval time is retained. These matches recover
bytes corresponding to recorded historical hashes; they do not validate the
inherited manifest's classifications or establish legal currency.

All raw evidence and the richer discovery manifest remain local under the
ignored directory `.geode_runtime/county-discovery-2026-09-10/`:

- `source-manifest.json`: exact catalog/document URLs, source identifiers, visible
  anchor labels, descriptive catalog labels, categories, all catalog links,
  exclusions, hashes, lengths, timestamps, redirect destinations, PDF page counts,
  and inherited-hash matches.
- `catalogs/*.html`: the four original catalog responses; corresponding headers
  and the zoning document's size check are retained separately.
- `documents/*.response`: the original PDF bytes. The complete zoning document
  uses `jefferson-zoning-document-1828.retry1.response`.

This directory supports a deterministic replay without requesting sources again.
It is local evidence, not a published archive. The collection package must copy
validated originals into durable storage and retain its own reviewed manifest
before claiming that publication or restoration is complete.

Clear Creek's codes page uses visible anchor text `Link to page`; descriptive
names appear in `aria-label` and adjacent titles. Ordinance 17 splits its label
over two anchors to the same URL. The manifest preserves the exact normalized
visible anchor separately from descriptive context, so validation does not
invent a label or count that ordinance twice.

Retrieval used ordinary curl, HTTPS with certificate verification, and a
descriptive Project Geode user agent. No account, impersonation, browser-cookie
reuse, or access-control workaround was used. The older local downloader was
inspected but not run: it uses a broader registry-driven flow and would mutate
shared manifests. The next step is a separate, explicit-manifest collection
package that preserves this selected scope and presents its evidence for review.
That package is now documented in the [county pilot guide](../COUNTY_REACQUISITION_PILOT.md).
