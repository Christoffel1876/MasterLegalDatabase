---
title: Sherlock008 Weld County and Greeley received-package PDF intake
date: 2026-09-11
received_at: 2026-09-11T19:15:24.670419Z
status: archived_pending_pipeline
legal_currentness: not_verified
semantic_or_coverage_promotion: false
---

# Intake result

Four PDFs (11 pages; 1,091,614 bytes) were preserved as new canonical originals: the
five-page Weld County building fee schedule, one-page Greeley building fee schedule,
three-page Greeley development-impact-fee memorandum and two-page Greeley proposed
water/sewer PIF notice with tables. Every original remains byte-identical to both the
received package and the independently audited frozen copy. This intake checks PDF
structure and custody; the prior audit inspected all 11 pages for roles, dates and
bounded source anomalies, without certifying every numerical cell.

The current deduplication check screened all 538 ordinary files under `_RAW_ARCHIVE`,
plus the current 34-row raw manifest and 35-row ledger. No existing raw file had any
of the four candidate sizes, and neither current manifest contained their digests.
No historical digest or missing LFS pointer was treated as an available original.

The raw manifest now has 38 records; the ledger has 39. The same missing ledger-only
EO original remains explicitly missing. Both prior JSONL files are exact byte
prefixes of the new versions. Three preimage snapshots and frozen before/after
transaction copies preserve the append. Reconciliation predicted four additions,
applied four, and then returned no additions or report changes on a repeat dry-run.

# Source evidence and limits

- **Weld:** `official_source_url=null`. The successful browser download's exact
  version path, final URL and acquisition time remain unconfirmed. The supplied
  `/v/3/` request is explicitly reconstructed context, not an accepted successful
  URL. Preserve `JANUARY 2026` and the source's `Revised 012/25` separately.
- **Greeley:** the three exact Sitecore PDF URLs are supported by retained official
  Greeley HTML anchors and curl body/header evidence. The existing intake allowlist
  rejects the direct Sitecore host, so `official_source_url=null` also remains in
  these manual records. Exact requested/final URLs, reported times and official
  referral evidence remain in typed provenance. No allowlist or policy was changed.
- **Greeley building fees:** the title says 2024, the table says `Effective -2024`,
  and the footer says `8/18/2026` without a date-role label. None establishes currentness.
- **Greeley 2026 impact memo:** November 1, 2025 is the memorandum date; March 1,
  2026 is its stated effective date. The memorandum separately describes future
  December adoption of water/sewer PIFs; those are not adopted rates in this document.
- **Greeley PIF notice:** November 20, 2020 notice describes future December 16 Board
  consideration and March 1, 2021 effectiveness **assuming adoption**. It remains a
  proposed/conditional notice with an attached schedule, not verified adopted fees.
  Weld County addressees do not change its City of Greeley ownership.

Repository receipt time is distinct from original acquisition. No new request was
made. The HTTP header copies are explicitly derived: only `Set-Cookie` response
header lines were removed, with all other bytes retained. Original complete header
hashes are bound to the frozen independent audit. Server response and Last-Modified
dates are transport metadata, not adoption, publication or effectiveness dates.

The official-only request API cannot truthfully encode `received_review_package`.
Validated `ManualSourceIntakeRecord` objects, the existing write-once raw helper and
existing reconciliation workflow were used, preserving exact JSONL prefixes. No
production code, intake policy, blocked queue, registry, legal text, rules or
coverage statuses were changed. `prepare_intake.py` is the guarded one-time audit
script; do not rerun it to refresh sources.

# Validation

From the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python research/local_review/weld-greeley-intake-sherlock008-2026-09-11/validate_intake.py
```

The read-only validator checks strict Pydantic records and exported JSON Schema,
transaction hashes/prefixes and snapshots, current manifest and ledger identities,
all four canonical PDF hashes/page counts, frozen-audit bindings, exact official
HTML links and retained HTTP metadata. It permits later append-only intakes while
requiring this transaction and its four originals to remain unchanged.

All records remain `archived_pending_pipeline`, with `legal_currentness=not_verified`
and no semantic or coverage promotion. There was no source crawl, full-corpus
regeneration, commit, push or bot message.
