---
title: Sherlock SH-EXT-004 — Chaffee corrected links
assignment_id: SH-EXT-004
status: completed_pending_atlas_verification
actual_start_utc: 2026-09-13T15:40:35Z
prepared_at_utc: 2026-09-13T15:41:39Z
delivery_path: /Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-13/sherlock-deliveries/SH-EXT-004
start_here_sha256: c5ff150d2d8390ebac122eb25078ad0853f75c40c6759782769ff94a129b8e0e
final_manifest_sha256: 4485cb16ddbf4dbd0e1b7b7b505961d3d7e67d6fb59bae4194763e4117536c04
research_cutoff_utc: 2026-09-13T17:45:00Z
report_cutoff_utc: 2026-09-13T18:00:00Z
review_status: pending_intake
legal_currentness: not_verified
answer_safe: false
next_assignment_authorized: false
sh_ext_003_preserved: true
---

# SH-EXT-004 report

## Caps
| Metric | Used | Cap |
|---|---|---|
| Public actions | **4** | 4 |
| Distinct URLs | **4** | 4 |
| Retained body bytes | **166875** | 60,000,000 |

Hidden network requests: **not measured**. Automatic redirects: **disabled** (`--retry 0 --max-redirs 0`, no `-L`). Helper `public_requests_by_helper`: 0.

## Outcomes (exact TARGETS.json encoded URLs)

| Action | Label | HTTP | Role | Bytes | SHA-256 | Location (unopened) |
|---|---|---|---|---|---|---|
| SHEXT004-A001 | Application Forms & Fees | 200 | original_html | 85120 | `bdad2052d6747e3066b42c7a857f4905d52f9464c36213d905936e709962e625` | — |
| SHEXT004-A002 | Applications & Fees | 200 | original_html | 81160 | `51d29dcca8700c13a1fe62aa871e4a77bc7b0793b6f1f5c51cb497c75bbb978d` | — |
| SHEXT004-A003 | 2025 BOCC Ordinance 2026-02 | 302 | unknown | 334 | `405cac7c193ed4338f0065abd00f220bc087411790f0c89bd5403b8cc338f5d6` | `https://cms2.revize.com/revize/chaffeecounty/Documents/Departments/Building Department/Adopted Codes & Design Criteria/2026-02 Ordinance Adopting the CWRC with Local Amendments_RECORDED.pdf?t=202606021136110` |
| SHEXT004-A004 | 2026 BOCC Ordinance 2026-01 | 302 | unknown | 261 | `35504079c37e870057b11530fc9a3c23aca757b5f57e363c07d0caca8844059b` | `https://cms2.revize.com/revize/chaffeecounty/2026-01 Ordinance Chaffee County Electric Preferred Amendments_RECORDED.pdf?t=202608031134050` |

## Source vs tool-derived
- A001/A002: retained **original_html** fee catalogs (source bytes). Observed document links → BACKLOG only; **not opened**.
- A003/A004: HTTP **302**; retained small HTML “Document Moved” shells (`body_role=unknown` as recorded; not `%PDF`). **Location** points at `cms2.revize.com` publisher paths (spaces unencoded in Location) — preserved as **unopened** leads. No hop followed. **No ordinance original_pdf** in this delivery.
- PDF magic/page parse: N/A for HTML/shells. Source QA: **not_performed**. Visible label vs filename year mismatches preserved (not repaired).

## Method limitations
- curl without `-L`; Location never followed; no retries/searches/browser alternates/follow-ups.
- Transfer bounds from helper `max_next_body_bytes` / `max_transfer_seconds`, rechecked against positive seconds before 17:45Z each launch.
- COMPARISON is the 64-manual-PDF subset at `512684a…` only.

## Historical comparison (metadata only)
```json
[
  {
    "action_id": "SHEXT004-A001",
    "body_sha256": "bdad2052d6747e3066b42c7a857f4905d52f9464c36213d905936e709962e625",
    "digest_in_manual_subset": false,
    "exact_url_in_manual_subset": false
  },
  {
    "action_id": "SHEXT004-A002",
    "body_sha256": "51d29dcca8700c13a1fe62aa871e4a77bc7b0793b6f1f5c51cb497c75bbb978d",
    "digest_in_manual_subset": false,
    "exact_url_in_manual_subset": false
  },
  {
    "action_id": "SHEXT004-A003",
    "body_sha256": "405cac7c193ed4338f0065abd00f220bc087411790f0c89bd5403b8cc338f5d6",
    "digest_in_manual_subset": false,
    "exact_url_in_manual_subset": false
  },
  {
    "action_id": "SHEXT004-A004",
    "body_sha256": "35504079c37e870057b11530fc9a3c23aca757b5f57e363c07d0caca8844059b",
    "digest_in_manual_subset": false,
    "exact_url_in_manual_subset": false
  }
]
```

## Backlog
**163** unopened leads (2 Location + catalog hrefs; static assets filtered).

## Stop
SH-EXT-004 complete. Prior SH-EXT-003 bytes unchanged. **No SH-EXT-005.**
