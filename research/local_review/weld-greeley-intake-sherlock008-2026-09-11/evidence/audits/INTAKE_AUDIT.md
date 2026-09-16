---
title: Atlas SD008 independent intake audit
assignment: geode-source-discovery-008
prepared_at: 2026-09-11T19:07:54.775826+00:00
comparison_commit: 0bc3658f6c7c9f378a5083884714dc4111677afd
disposition: retain_with_corrections_pending_intake
legal_currentness: not_verified
review_status: pending_intake
repository_changed: false
---

# Weld County and Greeley intake audit

Retain the delivery with the qualifications below. All 110 received files are frozen as read-only copies and rehashed; no source originals were modified. This is evidence intake, not a current-law or complete-corpus certification.

**Verified:** 41 logged events / 38 exact requested targets; 16 priorities; 24 checklist rows. All seven advertised hashes, 91 inventory files and six aliases agree. The 94-file tar covers every inventory file. All four Atlas export files match actual pinned Git blobs.

Full visual inspection covered Weld fee schedule pages 1-5, Greeley building fees page 1, Greeley PIF notice/table pages 1-2, and Greeley 2026 impact memo/tables pages 1-3. Dates, roles, table structure and bounded anomalies were checked; this does not certify every numerical cell. Sources are the exact PDFs under `received/20260911T184800Z/raw/`.

## ATLAS-SD008-01: Complete delivered custody and consistent file hashes

**accepted_with_limits.** All seven announced hashes, 91 inventory file hashes/sizes and six aliases agree. Tar has 94 regular files and seven directories, covering every inventory file; no unsafe members, duplicates or mismatched tar bytes. All 110 loose files, including Atlas export, frozen.

Accept byte custody only; tar excludes outside-attempt Atlas export by design, preserved in full loose custody.

Evidence: hash-summary-20260911T185715Z.txt; artifact_inventory.json; package tar.

## ATLAS-SD008-02: 41/38 are internally consistent recorded counts, not a certified exhaustive activity log

**qualify.** 38 curl events plus three reconstructed browser retries; 38 exact requested URLs and no target over two logged attempts. Notes additionally mention GitHub get_commit/search and WebFetch/search snippets without per-action records; browser child stopped before final summary.

Recorded counts are below 60/40 but complete cap compliance cannot be independently certified. No invented additional count or timestamp; source requests, GitHub comparison calls and possible WebFetch/search activity need separate accounting if acquisition is audited.

Evidence: attempted_urls.json; logs/browser_attempts_reconstructed.json; derived/repo_compare_notes.md; checklist.json.

## ATLAS-SD008-03: Weld PDF exact acquisition URL is not proven

**qualify.** Original derived note says likely /v/*/ and exact final URL pending browser summary; later reconstructed B003 chooses /v/3 without retained success headers or referral HTML.

Preserve real PDF hash and face title, but mark requested-version/final-URL provenance unconfirmed. Do not attach a successful live source/referral certification from the failed curl /v/3 event.

Evidence: derived/weld_2026_bldg_fee_extract.json; logs/browser_attempts_reconstructed.json; SD008-01; SD008-02.

## ATLAS-SD008-04: PIF effective date and role require the express adoption condition

**correct.** Page 1 says the changes will become effective March 1, 2021 assuming they are adopted; consideration at December 16, 2020 meeting was future to notice. Page 2 is attached proposed table.

Replace unqualified effective date/utility_fee_schedule interpretation with a proposed or conditional date and pre-adoption notice role. Greeley owns it despite Weld addressees.

Evidence: SD008-08; raw/greeley/2021_water_sewer_plant_investment_fees.pdf physical pages 1-2.

## ATLAS-SD008-05: Preserve multiple printed date roles and source anomalies

**qualify.** Weld face JANUARY 2026 and p3 Revised 012/25 are distinct. Greeley face 2024/Effective -2024 and unlabeled footer 8/18/2026 coexist. Weld visibly prints $80..00, $40,0001 and overlapping tiers.

No silent correction, inferred adoption or currentness from filenames, footer or response Last-Modified.

Evidence: SD008-01 pages 1-3; SD008-06 page 1.

## ATLAS-SD008-06: 2026 impact memorandum includes its stated effective date and narrower utility boundary

**qualify.** Nov 1, 2025 memorandum cites 4.64.055(b), p2 March 1, 2026 effective date and roughly 120-day notice; average -2.07%. Thirty fee rows span pages 2-3; PIF adoption separately future December.

Record date as the memorandum statement; retain all pages and category/unit columns. Do not certify adopted methodology, currentness, PIF amounts or recomputed arithmetic.

Evidence: SD008-07 physical pages 1-3.

## ATLAS-SD008-07: Text excerpts are not complete fee-table extraction

**correct.** Building and impact text_excerpt each truncate at 2,500 characters. Building cuts item 9 and omits two footnotes/tax/temp-electrical/footer; impact excludes effective-date paragraph and all fee tables. Two-page PIF text has both tables but flattened column order.

Use intact PDFs as source. Native/derived text requires structured layout review before table use. Weld text_full retains headings/data but is not a certified numeric or semantic extraction.

Evidence: derived/greeley_fee_extracts.json.

## ATLAS-SD008-08: Exact pinned comparison corrects family-match shorthand

**qualify.** All four Atlas export files match actual Git blobs at exact 0bc3658. Full 48,390-row legacy manifest across all owners and 12-row manual manifest have zero delivered raw digest matches. Eight compared URLs match 44 legacy requested rows, plus 313 parent-source-only rows. No legacy final_url field exists. Weld 288 rows split 258 downloaded/30 failed; Greeley 13 split 7/6.

Initial alternate-checkout notes are history, not final counts. New Greeley failed filenames are not exact matches to the different old failed PDF paths. No prior-original equality or content inference from old wrapper hash. Preserve exact URL/parent/digest distinctions.

Evidence: atlas-pinned-comparison/EXPORT.json; derived/pinned_compare_runtime.json; derived/repo_compare_notes.md.

## ATLAS-SD008-09: Official Sitecore referrals and redirects are supported at the retained scope

**qualify.** Three PDF URLs appear as exact main-content anchors; response headers show HTTP200 PDFs and content-length agreement. Sitecore public-links-url-direct header is not an observed external storage redirect. Greeley old-host and canonical path redirects are retained separately.

Bind requested and final URLs from logs/headers for each source. Do not invent a CDN/storage destination. HTTP Last-Modified is server metadata, not legal publication/adoption.

Evidence: raw/greeley/building_permits_and_inspections.html; logs/SD008-E012.headers.txt; logs/SD008-E035.headers.txt; logs/SD008-E036.headers.txt; logs/SD008-E037.headers.txt.

## ATLAS-SD008-10: Backlog needs exact resources and blocked-versus-unopened separation

**correct.** Backlog has two non-URL placeholders; minutes.weld.gov is labelled discovered-unopened despite E030 HTTP403. Exact 14 design Sitecore links and FEB 2026 Building Valuation Data link are already present in retained official HTML; all are unattempted.

Use exact audit links for unopened leads; minutes portal is attempted/blocked. Ord26-01 and EHS PDF are legitimate unopened historical leads. Scope is incomplete, not absence of law.

Evidence: backlog.json; raw/greeley/design_criteria.html; raw/greeley/building_permits_and_inspections.html.

## ATLAS-SD008-11: Checklist and priority semantics need bounded bindings

**qualify.** 24 unique authority/category rows use 12 keys each; all 24 distinct referral URLs were attempted. 16 unique priority requested resources include four PDFs, two error bodies, two shells, six substantive/portal/catalog HTML and two unopened leads. SD008-10 and 12 omit explicit primary path/hash although those files exist; Weld adopted_changes searched_not_found conflicts with its known pinned adopted-instrument lead.

Audit binds each exact primary and related captures. Keep found, raw retained, extracted, adopted and current statuses separate; use candidate_found/unopened lead for known Weld change, not a claim no adopting instrument exists.

Evidence: checklist.json; SD008-04; SD008-05; SD008-10; SD008-12.

## ATLAS-SD008-12: County and municipal ownership must stay distinct

**qualify.** Weld PDF title and Greeley PDFs/official page identity distinguish the two authorities. Weld homepage also occurs under New Raymer and Grover IDs in 15 legacy direct-request rows; source_parent matches are especially broader than document ownership.

Retain these as historical ownership-review candidates, not automatic reassignment. Mailing addresses/addressees do not establish applicability, municipal boundaries or a full service area.

Evidence: SD008-01; SD008-08; SD008-10; pinned legacy manifest.

## Remaining boundaries

- No live requests, source reacquisition, repository edits, bot messages, commits or currentness promotion.
- Direct visual inspection of all eleven pages was for roles/dates/structure and bounded anomalies; not an exhaustive row-by-row numerical certification or blind PDF review.
- Poppler failed with fontconfig errors and was terminated; inspected renders use PyMuPDF 1.28.2.
- Original source authority signatures, adopting instruments, legal currency and full county/city coverage remain unverified.
- Successful Weld browser final version URL and full child activity record remain unavailable.
- Atlas supplied LOCAL_SOURCE_REGISTRY, COUNTY_SOURCE_COVERAGE and two manifests; the MUNICIPAL_SOURCE_REGISTRY was not in that four-file export and is not certified by this audit.

Machine-readable audit and custody receipt both validate with strict Pydantic and their exported JSON Schema. `pinned-comparison-facts.json` contains exact legacy rows/owners and per-priority comparisons; `html-link-facts.json` records exact retained referral links. Original acquisition claims remain distinguishable from Atlas byte and visual checks.
