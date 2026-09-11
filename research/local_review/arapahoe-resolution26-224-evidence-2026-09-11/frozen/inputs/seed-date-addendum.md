# Sherlock — geode-source-discovery-002 — addendum (Atlas feedback)

**Issued:** 20260910T213206Z  
**Basis:** Atlas-feedback-based (ATLAS_STRUCTURAL_REVIEW.md + ATLAS_SOURCE_REVIEW.md + existing on-box county packages)  
**Parent artifacts preserved unchanged:** `report-20260910T211727Z.md`, `checklist_final.json`, `priority_candidates_final.json`  
**Status:** `completed_pending_atlas_verification` / `pending_intake` / `legal_currentness: not_verified`  
**Scope:** Bounded addendum only — **no new crawl**, no restart, no alteration of original report/JSON bytes.

## 1) Open-count accounting (batch cap vs internal allocation)

- Atlas batch cap for 002 = **100** distinct public targets. Claimed **54 (Adams) + 32 (Arapahoe) = 86** is within that batch cap.
- The Adams “overrun” of +4 concerns Sherlock’s **internal 50/50 county allocation**, not an Atlas batch-limit breach.
- Delivered checklist `urls_searched` enumerated **75** distinct strings (Adams 45, Arapahoe 30). That checklist list is **not** the complete opens log.
- **Attempt logs exist** from the original research packages (were not copied into the Mac handoff with the first 002 delivery). They are attached with this addendum:
  - `attempted_urls-adams.json` — `distinct_url_count: 54` (includes failed EncodePlus/MCO probes)
  - `attempted_urls-arapahoe.json` — `open_attempt_count: 32` (31 success, 1 fail)
- Difference checklist 75 vs claimed 86 = **11** URLs present in attempt logs but not individually listed in checklist `urls_searched`. Those 11 are **recoverable from the attached logs** (not invented). No new timestamps were created for this addendum beyond the `observed_at_utc` values already stored in those log files.

### Failed URLs recovered from existing logs

**Adams (7 failed entries in log):**
1. `https://adamscounty.municipalcodeonline.com/book?type=ordinances` — HTTP 500 (“book or node does not exist”)
2. `https://adamscounty.municipalcodeonline.com/book?type=developmentstandards` — HTTP 500
3. `https://adamscounty.municipalcodeonline.com/api/toc` — HTTP 404
4. `https://adamscounty.municipalcodeonline.com/content` — HTTP 403
5. `https://online.encodeplus.com/regs/adamscounty-co-cc/content.aspx?secid=186` — HTTP 404
6. `https://online.encodeplus.com/regs/adamscounty-co-cc/docviewercontent.aspx?secid=186` — HTTP 404
7. `https://online.encodeplus.com/regs/adamscounty-co-cc/printpreview.aspx?secid=186` — HTTP 404

**Arapahoe (1 failed entry — complete newer IDCS URL):**
1. `https://files.arapahoeco.gov/Public%20Works_Development/Infrastructure%20Design%20and%20Construction%20Standards/IDCS%202024%20Reso%2025-085%20Adopted%2020250311.pdf` — HTTP 500

## 2) SD002-12 — recovered legacy bytes (not a wholly new source)

Atlas fresh download of  
`https://files.arapahoeco.gov/Public%20Works_Development/Building/Adopted%20Building%20Codes%20and%20Amendments.pdf`  
has SHA-256:

`1622d58968fbc2a837bdb94c487d2401f2c941c3946199532f67918a4ad2cb8a`

That digest matches inherited `LOCAL_DOWNLOAD_MANIFEST.jsonl` records for **`county_arapahoe_building_resolution`** associated with the older filename  
`Resolution.2021.Building.I-Codes.FinaltoSet.pdf`.

**Correction:** Treat SD002-12 as **recovered legacy bytes under an alternate URL**, not a wholly new historical source. Ledger `collection:missing` does **not** mean never collected. Fresh-byte equality to the live alternate URL is established by Atlas’s hash match; the original Windows archive paths remain unavailable in the pinned tree.

## 3) SD002-14 — revision confirmed; adoption/effective not established by revision header

Atlas direct download of Planning Fees PDF:
- SHA-256 `ce519b6fe89546cf85a77934fcbdb6b6bf08473e19c545cf4c51414e1cdcb818`
- Supports **Revised 09-08-2026** and **Resolution No. 26-224**

**Correction:** Preserve the **2026-09-08 revision** observation. Leave **adoption** and **effective** as **unknown / not observed** pending acquisition of Resolution 26-224. Do not assign 2026-09-08 to adoption and effective solely from the revision header. A cached web-tool copy showed a 2022 revision; fresh bytes support the 2026 revision — cache cannot contradict the newly retrieved bytes (no hash for the cached version).

## 4) SD002-12 internal PDF date conflict + Code Central referral distinctness

Atlas page inspection of the same building PDF:
- **Physical page 2:** October 1, 2016 in an adoption/implementation sentence
- **Physical page 47:** April 1, 2022 as this resolution’s effective date; unincorporated permit-application cutoff; rescission of replaced prior versions

**Correction:** Preserve an **internal PDF conflict** (page 2 vs page 47), not merely website-versus-PDF. Do not silently repair page 2.

Code Central’s actual `Resolution NO. 21-394` anchor targets:
`Resolution.2021.Building.I-Codes.FinaltoSet.pdf?t=202602230955100`  
Keep that referral target **distinct** from the alternate downloaded filename `Adopted Building Codes and Amendments.pdf` used in SD002-12. Same resolution number / related package ≠ automatic byte identity without the hash evidence above.

## 5) Metadata discipline (intake guidance; originals unchanged)

- Preserve **unknown** per-source timestamps where null (especially Arapahoe `observed_at_utc`); do not invent retrospective times.
- Split grouped originals (e.g. SD002-05 fee bundle) in eventual intake; retain grouping only as discovery context.
- Do not turn URL directory path strings into posting dates.
- Do not convert clerk certification into adoption (see SD002-05 certification vs adoption clause).
- Complete failed newer IDCS URL is supplied above from existing Arapahoe attempt log.

## Attachments delivered with this addendum

| File | Role |
|---|---|
| `attempted_urls-adams.json` | Existing Adams open-attempt log (54) |
| `attempted_urls-arapahoe.json` | Existing Arapahoe open-attempt log (32) |
| this addendum markdown | Atlas-feedback corrections |

## Disposition

Addendum is **Atlas-feedback-based**, `pending_intake`, `legal_currentness: not_verified`. Parent 002 report remains useful discovery evidence. No changes to batch 003. Sherlock awaits the next Atlas assignment.
