---
title: Sherlock 011 local intake audit
audited_at: 2026-09-12T22:18:04.797759+00:00
status: qualified_partial_delivery_with_failures
legal_currentness: not_verified
production_intake_performed: false
---

The delivery contains **15 genuine original PDFs (351 structural pages)** that can be considered for typed preservation after source-role review. This audit does not accept the batch as fully conforming: the 50-target cap was exceeded, two earlier response bodies are missing from the delivered versions, and the requested source-level schemas/review extent were not supplied. No original was ingested.

Custody froze 153 delivery files plus 15 preparation/comparison inputs at 2026-09-12T22:08:54.656702Z. The latest addendum declares complete at 22:07:06Z. All frozen copies matched their original files during copying. Original HTTP dates remain Sherlock-supplied claims, distinct from this Atlas receipt time.

| Measure | Independently checked local result |
| --- | --- |
| Public activity | 66 deliberate events / 66 exact requested targets; 80-event cap passed, **50-target cap failed**. One additional non-public STOP record. |
| HTTP evidence | 88 response header blocks: 66 finals plus 22 redirects; 65 unique final URLs and 21 redirect-only URLs. Header chains reconcile to logged finals. |
| Bodies | 63 paths / 60 current digests / 16,768,999 actual bytes, including 193,498 error-body bytes. Event claims total 17,112,685 bytes. |
| PDF-named files | 27: **15 PDFs, 12 HTML**. All PDFs parse without repair/encryption; no text or visual certification. |
| Checklist / priorities | Exactly 24 unique authority/category rows and 20 unique priorities; all priority event/body bindings match. |
| Historical comparison | Full pinned 48,390-row manifest: 39 digest-hit rows / 15 source IDs / four digests, all El Paso. 79 requested-URL hits versus 207 source_url parent associations. |
| Manual comparison | Frozen 46-row raw manifest and 47-row ledger: no exact URL/digest matches. This is not universal absence. |

**Custody corrections.** `raw/el_paso/index.html` is shared by E001/E043 and now contains E043’s planning homepage. E001’s claimed homepage digest `75c50637f46f8bc0624588780e0400067b80401280ab89e524ae97cb9ea41d3b` is not present in received files or tar members. E020/E021 reuse the oEmbed path; E020’s digest `41bab1490d0d0914fda432d30cb3310fcbd65429ea62ad134350929857fe7466` is similarly missing. E006/E027 reuse an identical fire-page body. Do not treat later bytes as the earlier response.

The 137-entry supplied inventory matches the earlier 144-file tar, with seven additional metadata members. Its `logs/attempted_urls.json` entry is stale against the loose current file. The tar and loose versions preserve identical **66 public event records**; only STOP timing/notes and top-level metadata differ. Both versions are preserved. The tar is an earlier assembly, not a complete representation of the later addenda.

**Source-role corrections.** SD011-13 and SD011-20 are HTML document viewers for proposed/draft material, not PDFs. SD011-07 redirects to an amendments-not-yet-codified page. The city adopted-changes checklist explicitly cites proposed/draft material, so it does not establish an adopted instrument. PPRBD retains its separate issuer/service-area context. Its `/Codes` URL was attempted/403, contradicting its unopened-backlog entry; `/FeeSchedule` E047 ends at a `Shared/NotFound` HTML page with status 200. The separate `/Information/FeeSchedule` priority is a different resource.

El Paso roads/utilities is marked `searched_not_found`, but its note says a portal was linked and unopened; preserve it as an unsearched/linked gap. The backlog’s vague descriptions do not supply a complete exact unopened URL list. All explicit checklist referral URLs do appear among requested/final/redirect URLs, but the E001 homepage body association is broken. Three LDC PDFs have inherited official URLs and recorded digest matches but no matching fresh anchor in the received HTML.

**Privacy and portability.** Six retained header files have Set-Cookie fields (five PPRBD, one Spotify). Raw private originals remain unchanged under `received/`; `public-headers/` contains separately named derivatives with removed-field names/counts and original/derived hashes in AUDIT.json. No cookie values are echoed here. Do not publish the received tree wholesale.

**Prioritized real-PDF preservation proposals.** These are exact measured originals, not findings of adoption/current law. The detailed typed records include requested/final URLs, claim times, file hashes, source anchors, prior IDs and limits. Use the existing typed intake pipeline after root review; do not copy loose files directly into canonical indexes.

| Rank | Event / priority | Physical pages | Source / role boundary |
| --- | --- | --- | --- |
| 1 | SD011-E053 / SD011-01 | 5 | [El Paso County Planning Fee Schedule PDF (2026 filename)](https://epc-assets.elpasoco.com/wp-content/uploads/sites/12/fees/Fee-Schedule-2026-ADA.pdf) |
| 2 | SD011-E065 / SD011-08 | 5 | [El Paso County BoH 2024 EHS Fee Schedule Ch3](https://epc-assets.elpasoco.com/wp-content/uploads/sites/18/2025/06/3-BoH-2024-EHS-Fee-Schedule-Chapter-3_Acc-Checked-June-2025.pdf) |
| 3 | SD011-E023 / SD011-05 | 23 | [El Paso County Ordinance 26-01 PDF](https://epc-assets.elpasoco.com/wp-content/uploads/sites/5/Ordinance-26-01-Accessible.pdf) |
| 4 | SD011-E052 / SD011-09 | 18 | [LDC Appendix E Wildfire Resiliency PDF](https://epc-assets.elpasoco.com/wp-content/uploads/sites/12/LDC-Resolution/Appendix-E-Wildfire-Resiliency-Requirements-ADA.pdf) |
| 5 | SD011-E013 / SD011-06 | 14 | [El Paso County Open Burning Ordinance 22-001 PDF](https://epc-assets.elpasoco.com/wp-content/uploads/sites/5/CTB/Ordinances/22-001-Open-Burning-Ordinance.pdf) |
| 6 | SD011-E010 / SD011-03 | 72 | [El Paso County LDC Chapter 1 PDF](https://epc-assets.elpasoco.com/wp-content/uploads/sites/12/LandUseCode/EPC-Land-Use-Code-Chapter-1-2016.pdf) |
| 7 | SD011-E011 / SD011-04 | 7 | [El Paso County LDC Chapter 2 PDF](https://epc-assets.elpasoco.com/wp-content/uploads/sites/12/LandUseCode/EPC-Land-Use-Code-Chapter-2-2016.pdf) |
| 8 | SD011-E012 / SD011-02 | 172 | [El Paso County LDC Chapter 5 PDF](https://epc-assets.elpasoco.com/wp-content/uploads/sites/12/LandUseCode/New-LDC-Chapter-5.pdf) |
| 9 | SD011-E022 / supporting source | 8 | [18-03](https://epc-assets.elpasoco.com/wp-content/uploads/sites/5/18-03-Unsafe-Buildings-Accessible.pdf) |
| 10 | SD011-E054 / supporting source | 1 | [School District Fees](https://epc-assets.elpasoco.com/wp-content/uploads/sites/12/fees/School-District-Fees-Current-2010.pdf) |
| 11 | SD011-E064 / supporting source | 7 | [Administrative Regulations](https://epc-assets.elpasoco.com/wp-content/uploads/sites/18/2025/06/2-BoH.Regulation.Chapter.2.Admin_.Regs_.2011_1Acc-Checked-June-2025.pdf) |
| 12 | SD011-E062 / supporting source | 5 | [Bylaws](https://epc-assets.elpasoco.com/wp-content/uploads/sites/18/2025/06/1-BoH.Regulation.Chapter.1.Bylaws.2011_0Acc-Checked-June-2025.pdf) |
| 13 | SD011-E063 / supporting source | 6 | [Bylaws (Spanish)](https://epc-assets.elpasoco.com/wp-content/uploads/sites/18/2025/06/1-SpanishBoh.-Regulation-Chapter1-SpanishAcc-Checked-June-2025.pdf) |
| 14 | SD011-E066 / supporting source | 6 | [Fee Schedule and Civil Penalties (Spanish)](https://epc-assets.elpasoco.com/wp-content/uploads/sites/18/2025/06/3-Spanish-BoH-2024-EHS-Fee-Schedule-Chapter-3_EspanolAcc-Checked-June-2025.pdf) |
| 15 | SD011-E055 / supporting source | 2 | [Colorado Geological Survey (CGS) Fee Update](https://epc-assets.elpasoco.com/wp-content/uploads/sites/12/Misc/CGS/ColoGeoSurvey-Land-Use-Review-Referral-and-Fee-Guide-June-18-2026.pdf) |

English/Spanish Board of Health documents remain distinct; translation equivalence is unverified. The county-hosted Colorado Geological Survey guide requires underlying-issuer/layer review and should not automatically become county legislation. The three historical LDC chapter recoveries do not constitute a complete current code. Eleven PDF digests had no match in the compared legacy manifest; this is not proof of new discovery or a new edition.

**Two exact unopened future leads.** The saved HTML contains a PDF.js iframe at line 330. The target is the `file` parameter decoded once; canonical self-links, footer policy links and CSS references are not the document download. No request was made here.

- SD011-13: [https://coloradosprings.gov/system/files/2026-01/UDC%20Scrub%20-%20Phase%201%20Proposed%20Changes_V1.pdf](https://coloradosprings.gov/system/files/2026-01/UDC%20Scrub%20-%20Phase%201%20Proposed%20Changes_V1.pdf). Proposed/draft source only; not in the 011 requested or final URL sets.
- SD011-20: [https://coloradosprings.gov/system/files/2026-07/Chapter%202-Article%201%20%28Business%20License%20Code%29%20DRAFT%20proposed%207.27.2026.pdf](https://coloradosprings.gov/system/files/2026-07/Chapter%202-Article%201%20%28Business%20License%20Code%29%20DRAFT%20proposed%207.27.2026.pdf). Proposed/draft source only; not in the 011 requested or final URL sets.

**Verification.** Run from any working directory:

```sh
PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-status-venv/bin/python -I -B \
  "/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-12/sherlock011-atlas-audit/validate_audit.py"
```

The validator checks the closed inventory, strict JSON schemas, receipt/copy hashes, actual PDF structure, body mismatches and public-header derivation without following historical absolute paths, fetching public sources, extracting legal text or changing production files. `AUDIT.json` is the detailed decision record; `DECISION_RECEIPT.json` binds the report and validation inputs.
