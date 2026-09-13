---
title: "Greeley fresh custody preservation"
status: public_custody_preserved_no_canonical_change
date: 2026-09-13
legal_currentness: not_verified
---

# A separate, later acquisition of the same three Greeley documents

This public package preserves four recorded complete HTTP 200 responses from September 12, 2026, 23:50:43–23:50:45 UTC: the City's building-permits page and three exact linked Sitecore CDN PDFs. All three freshly received PDFs are byte-for-byte identical to their existing canonical archive files and the original PDFs in the earlier Greeley source-QA package. The City parent HTML is also identical to the earlier preserved parent.

| Existing canonical source ID | PDF pages | Bytes | SHA-256 |
|---|---:|---:|---|
| `greeley-building-fees-sd008-06` | 1 | 152,164 | `fa8a90dae00525c2dcb62ef4d69aeb84b7032a0fd2dc64f45c1685981e9becd4` |
| `greeley-development-impact-fee-memo-sd008-07` | 3 | 651,009 | `9effbd15196898c16105913ee21032db52ad1e259f4f9def0586804726f78709` |
| `greeley-water-sewer-proposed-pif-notice-sd008-08` | 2 | 74,466 | `edfd4eecc57657bec922b8e0e63597fbf2fc957936d8f26a1a457b195dac145c` |

All three belong to `CO-MUNICIPAL-GREELEY` / `10_Municipal_Authorities`. Weld County addressees in the utility notice do not change its issuer. The distinct roles remain a building fee schedule, a departmental fee-adjustment memorandum, and a proposed utility-fee notice with a conditional schedule. This package makes no current-law or adoption determination and repeats no new full visual or table review.

## What the later evidence establishes

`fresh/` holds unchanged copies of every file in the completed four-request directory, plus the unchanged acquisition script. The script is inert evidence; the validator never executes it. Exact receipt values, public response headers, body hashes/sizes, reservations, URL identity, no-redirect results, serial recorded timestamps, and the existing PDF framing/page counts are checked offline. Every selected CDN URL occurs exactly once as an anchor in the fresh City HTML. `PRESERVATION.json` binds each anchor's exact UTF-8 byte interval and markup. DOM labels include the site's icon-label strings (`home`, `add_business`, `water_drop`); this is not a fresh rendered-webpage inspection.

The parent response's HTTP `Date` is September 8 even though the recorded GET was September 12. That header and all `Last-Modified` values remain server/cache metadata, separate from locally recorded request/completion times and from any legal date. This package did not make a network request and does not independently attest the earlier transport by inference from matching bytes. The copied script requests normal HTTPS using OS curl trust and contains no redirect/retry or TLS-verification bypass option; a separate TLS handshake/certificate transcript was not retained.

The new acquisition does **not** prove Sherlock's earlier transport, earlier acquisition timestamps, continuous availability, document currentness or legal effectiveness. Existing canonical `received_at=2026-09-11T19:15:24.670419Z`, `acquisition_method=received_review_package`, and null `official_source_url` are unchanged. The exact City-to-CDN link is preserved as evidence, without broadening the manual-intake host allowlist.

Source-date qualifications are unchanged: the building document has a 2024 title/table label and an unlabeled 8/18/2026 footer; the development-impact memorandum is not its cited adopting instrument and separately discusses later Water/Sewer PIF adoption; the utility notice conditions its proposed March 1, 2021 timing on adoption. Later source QA and external reconciliation remain their own dated, qualified records.

## Public distribution check and exclusions

The recorded header dictionaries contain only `cache-control`, `content-length`, `content-type`, `date`, `etag`, `last-modified`, and the allowed optional `location`. Eight dictionaries were checked: four standalone receipts and their four copies in the summary. All error texts are empty. The declared lexical credential/header scan of fresh JSON, HTML and the acquisition script found no matches. No redaction was needed in this package.

Complete response headers were captured in memory by the original script and were not retained: cookies, authorization fields and other nonallowlisted fields are absent from its saved receipts. Their original values or count cannot now be verified independently. The lexical scan does not prove the absence of every possible secret, and compressed PDF streams were not subjected to a new full content review. The original public source bodies and script are unchanged.

`prior/` contains three exact selected raw-manifest rows and three exact source-provenance rows, schemas, the prior QA package manifest, the three prior QA JSON/schema/Markdown records, and the old City parent. The row bindings retain original whole-file digests, original row indexes, exact selected-line hashes and lengths. Unrelated full manifests and complete old QA packages are deliberately omitted. The fresh PDF bodies represent the equal canonical/QA original bytes without copying them three times. Offline verification recomputes all included bytes and selected-row/QA source bindings; it cannot recompute omitted whole manifests, reopen canonical files, or rerun old visual/native QA from these subsets. Absolute original-path labels are historical provenance, not paths the validator opens.

## Portable verification and later integration

```bash
PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-status-venv/bin/python -I -B "/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-12/greeley-fresh-custody-preservation/validate_package.py"
```

The directory can be copied and that verifier run in the copied location. It requires Python, Pydantic, jsonschema, BeautifulSoup and PyMuPDF, but no repository modules, credentials or network. It verifies the closed inventory, declared schemas, original report copies, three source identities, byte hashes, PDF structure, exact anchors, public-header scan and unchanged selected historical custody. The package contains no apply command.

`http-bindings.jsonl` provides three proposed records compatible with the existing inventory's `HttpBinding` structure. They point to each fresh receipt's `/sha256`, `/http_status`, and `/finished_at`. Paths are explicitly **package-relative**; prefix them with the actual repository destination if a later reviewed integration is authorized. `/finished_at` is the recorded response-completion time, not the earlier original acquisition or repository receipt. These proposals have `integration_status=not_applied`; this task does not edit inventory, raw manifests, ledger, registry or source QA.

Ten focused offline checks passed. They exercise exact package verification, source-byte changes, a hidden nested manifest, a symlink, false HTTP status/completion, a private header, timing/length errors, wrong anchor offsets and a swapped prior QA source. `CHECKS.json` and the exact test-output files retain the invocation and results. These are custody checks, not a new review of fee amounts.
