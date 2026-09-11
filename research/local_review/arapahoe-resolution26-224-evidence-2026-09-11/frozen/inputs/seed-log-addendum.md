# Sherlock — geode-source-discovery-002 — addendum (log reconciliation)

**Issued:** 20260910T215637Z  
**Basis:** Atlas log-reconciliation request after 004 delivery; **existing notes/logs only** — no new source opens  
**Parent artifacts preserved unchanged:** prior 002 report/JSON and earlier addenda  
**Status:** Atlas-feedback-based; `pending_intake`; `legal_currentness: not_verified`

## Exact URL-set comparison (existing delivered lists)

| Set | Adams | Arapahoe |
|---|---:|---:|
| Checklist `urls_searched` | **45** | **30** |
| Attempt log distinct URLs | **54** | **32** |
| Log-only (in log, not checklist) | **12** | **2** |
| Checklist-only (in checklist, not log) | **3** | **0** |

Combined: **14 log-only − 3 checklist-only = 11 net**. That net figure is **not** proof that 11 additional URLs “complete” the checklist. The current lists enumerate **86** distinct log targets (54+32); the **union of log ∪ checklist** is **89** distinct URLs. Actual attempt completeness remains **qualified**.

Do **not** retry failed or undocumented endpoints.

## The 3 Adams checklist-only EncodePlus URLs

These appear in checklist `urls_searched` (linked to SD002-AD-03 / building_fire rows) but have **no matching entry** in `attempted_urls-adams.json`:

1. `https://online.encodeplus.com/regs/adamscounty-co-cc/doc-viewer.aspx?secid=6`
2. `https://online.encodeplus.com/regs/adamscounty-co-cc/doc-viewer.aspx?secid=10`
3. `https://online.encodeplus.com/regs/adamscounty-co-cc/doc-viewer.aspx?secid=155`

**Classification from existing evidence (same for all three):** **discovered-but-unopened** (not **attempted-but-omitted**).

**Evidence:**
- No attempt-log row records these exact URLs (so they were not logged as HTTP attempts; this is not a missing log line for a completed open).
- Neighboring EncodePlus `doc-viewer.aspx` targets **were** logged (e.g. `secid=-1` TOC dump OK; `secid=186`/`20`/`156` partial TOC-only; several failed content.aspx/docviewercontent probes for other secids).
- Checklist assembly lists these secids under adopted_changes/building_fire alongside SD002-AD-03 / AD-06 / AD-07, consistent with TOC-derived catalog URLs expanded into `urls_searched` without a per-secid open event.

**Times:** unknown / not observed for these three URLs (preserve unknown; do not invent).

## SD002-12 byte-wording qualification

Atlas recovered bytes at the **alternate filename**  
(`Adopted Building Codes and Amendments.pdf`) whose digest  
`1622d58968fbc2a837bdb94c487d2401f2c941c3946199532f67918a4ad2cb8a`  
matches **three** historical `county_arapahoe_building_resolution` manifest records associated with  
`Resolution.2021.Building.I-Codes.FinaltoSet.pdf`.

**Qualification:** Atlas did **not** fetch both live filename endpoints and did **not** recover the old Windows original. Therefore **current equality between the two live URLs is unverified**. Treat SD002-12 as recovered legacy-matching bytes at the alternate URL / manifest relationship — not as proof the two live endpoints presently serve identical bytes.

Accepted date distinctions and the **internal PDF conflict** (page 2: 2016-10-01 vs page 47: 2022-04-01) remain **unchanged**.

## Disposition

Short correction only. No earlier files modified. After this addendum and delivered 004, Sherlock **stops** for Atlas’s next assignment.
