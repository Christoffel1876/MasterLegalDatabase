---
title: "Arapahoe Resolution 26-224 — portable related evidence"
packaged_at: "2026-09-11T20:11:19.620439+00:00"
disposition: "research_evidence_only_gap_open"
legal_currentness: "not_verified"
external_assignment: null
---

This package preserves the completed [bounded access audit](frozen/ACCESS_AUDIT.md), its typed report, source/custody and observed-link evidence. It adds no source review or public requests. The exact related two-page [resolution attachment](frozen/resolution/original.pdf) has SHA-256 **8f1e94f6332fc9c36ee479f4673e2f85a533b2b777f29cbfc9757c2adcd41e6c**. Both retained page images and all nine source-excerpt bindings are included.

The official-derived item **26-403** shows Passed and final action **9/8/2026**. That metadata is distinct from the attachment's blank resolution number, mover/seconder and vote fields. It does not establish an executed **Resolution 26-224**. The attachment's **effective immediately** wording remains qualified; its activation and the actual adoption/effective dates remain unverified. The meeting page's draft-minutes status also remains distinct.

The earlier fee PDF and EB006 records remain unchanged. No raw-manifest or ledger intake, semantic rule, coverage, legal-currentness or external-assignment promotion is made.

## Preserved files and one privacy exclusion

Of the original handoff's 36 files, **35 are copied exactly under `frozen/`**. The only omitted original is `http/E008.headers` (367 bytes, SHA-256 `78257b8f02bc6dee6582c744cebf7698b4b402d7bae242ba78c86d5cb2569b71`), because it contains a response session cookie. That original remains unchanged in the handoff.

[The redacted header derivative](derived/http/E008.headers.redacted.txt) replaces only the single Set-Cookie value-bearing line with an explicit marker, retaining all other header bytes. [package-status.json](package-status.json) binds the original and derivative hashes, transformation and distribution limit. URL credential fields in curl metrics were empty. No original session-cookie token is included.

The exact historical audit/inventory still refer to the original header. They describe the original handoff, not a claim that excluded bytes are present here. The portable verifier checks the allowed exclusion and all retained bytes; **it does not recompute the omitted original header's digest**. It reports that limitation explicitly. Do not run the old frozen capture helper or expect the unchanged historical validator to pass without its excluded header.

## Offline validation

With Python 3.11+, Pydantic 2, jsonschema and PyMuPDF **1.28.2**:

```sh
PYTHONDONTWRITEBYTECODE=1 python /path/to/arapahoe-resolution26-224-evidence-2026-09-11/validate_package.py
```

An explicit `--root /path/to/copied-package` is optional. The verifier checks typed status/audit records, complete inventory, original handoff hash bindings with the one declared exclusion, PDF/native/page-image reproduction and nine exact excerpts. It is read-only and offline; no live repository or original handoff path is opened. Validation establishes retained evidence integrity, not legal effect or human judgment. Keep the top-level inventory hash outside the package.
