---
title: Sherlock SH-EXT-003 — Chaffee + Gunnison county source discovery
assignment_id: SH-EXT-003
status: partial_pending_atlas_verification
actual_start_utc: 2026-09-13T02:15:50Z
prepared_at_utc: 2026-09-13T02:21:26Z
delivery_folder: 20260913T021737Z
start_here_sha256: 2d247e3ecce7d495c0a654a61be88eeee27ede9e21e0f30a1525ce3f3ec5b47c
instructions_sha256: d4fdb99427930b2749e1358126ed65c05c0de15b28ae171cbfb38f75e7027656
final_manifest_sha256: 47363aa29ca229e5b20f60dca1e9abca401e09c9a3fb4fd9f312bed9a621a4ce
research_cutoff_utc: 2026-09-13T03:05:00Z
report_cutoff_utc: 2026-09-13T03:20:00Z
review_status: pending_intake
legal_currentness: not_verified
answer_safe: false
next_assignment_authorized: false
---

# SH-EXT-003 report

## Caps
| Metric | Used | Cap |
|---|---|---|
| Public actions | **30** | 40 |
| Distinct URLs | **30** | 30 |
| Chaffee actions | **20** | 20 |
| Gunnison actions | **10** | 20 |
| Retained body bytes | **1600233** | 80,000,000 |

Hidden network requests: **not measured**. Research stopped on **distinct URL cap 30/30** (reserve refused for next Gunnison DocumentCenter candidate). Chaffee county action cap **20/20** earlier. No SH-EXT-004.

## Gunnison — retained original PDFs
| ID | Pages | SHA-256 (prefix) | Path claim |
|---|---|---|---|
| SHEXT003-A026 | 3 | `53bd127e25d3…` | Res 2025-24 Building Permit Fees schedule |
| SHEXT003-A027 | 16 | `41dc3a6c9620…` | Res 2023-22 2021 Code Adoption / IWUIC amendments |
| SHEXT003-A028 | 4 | `0b2dc2e2bdff…` | 2021 IWUIC Update Resolution |

Filename/path date and adoption claims are **not** independently verified legal effect.

## Gunnison — LUR gap
- SHEXT003-A008 Land-Use-Resolution: HTTP **302**, Location to DocumentCenter View/3157 (not auto-followed).
- SHEXT003-A025/A030: HTTP **301** HTML shells (`625b6929…`); Location renames slug to **Amended-March-5-2026** — hop **not** opened (distinct URL cap).
- No LUR **original_pdf** bytes in this delivery.

## Chaffee — catalogs only
- Homepage / adopted codes / commissioners HTML **200** retained.
- `search.chaffeecounty.org` land-use seed: **transport_error** (curl 6 DNS).
- Many Document path follows: **curl 3** (unencoded spaces) or **302** small bodies toward `cms2.revize.com` (Locations logged; not followed as PDF).
- **Zero** Chaffee `original_pdf` retained. County action budget exhausted before percent-encoded retries.

## Priorities
11 candidates (`SHEXT003-01`…`11`): 7 Gunnison (3 PDFs + 4 catalogs), 4 Chaffee catalogs. Checklist 24/24 rows. Backlog **45** unopened leads (municipal links labeled out-of-scope for county ownership).

## Stop
SH-EXT-003 complete for this dispatch. Packet originals unchanged. No SH-EXT-004.
