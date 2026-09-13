---
title: Douglas County and Pueblo City guarded source intake
status: PREPARED_NOT_APPLIED
prepared_date: 2026-09-13
---

This packet prepares two already acquired and source-reviewed PDFs. It has not applied canonical intake. Root must review this packet and explicitly select `--apply`. No new public request was made during preparation.

| Canonical source ID | Issuer / layer | Original | Earlier recorded acquisition |
| --- | --- | --- | --- |
| `douglas-ehs-fees-atlas-directed` | Douglas County Health Department / `08_County_Authorities` | 149,173 bytes, one page; SHA256 `35e90b9c3b73b414155ed965898c8c270757f1c367cbe50d7645956039dbb687` | September 12, 23:34:38.261907–23:34:39.577252 UTC; direct HTTP 200 |
| `pueblo-planning-fees-atlas-directed` | City of Pueblo / `10_Municipal_Authorities` | 228,376 bytes, four pages; SHA256 `0ba13c07bede5bf07c24dd8bbbe604c61745e8a73be773a7987e26dfa601414b` | September 13, 00:23:01.971515–00:23:02.695819 UTC; final HTTP 200 after the separately retained HTTP 301 |

Both exact publisher bodies match the accepted source QA originals. The frozen custody preserves the official parent HTML, visible anchor and its URL, response events, available public headers, and the Pueblo redirect. Douglas's issuer remains the county even though its two table captions distinguish county-set fees from fees attributed to state legislation. Pueblo is the city, not Pueblo County. Blank Douglas fees remain blank in the accepted QA.

Douglas prints `2026 Fee`, a county caption claiming November 1, 2025, and a state-legislation caption claiming September 1, 2025. Pueblo prints `2-13-26` on all four pages. These are source claims. Neither an adoption date nor legal currentness is established here. Earlier HTTP acquisition times stay separate from the actual future repository `received_at`, which is frozen only when an approved apply creates `execution/INTENT.json`.

The preserved review subset includes exact SOURCE_QA, review summaries, root acceptance and the source package manifest. It references the complete accepted packages at `research/local_review/douglas-ehs-fees-source-qa-2026-09-13` and `research/local_review/pueblo-planning-fees-source-qa-2026-09-13`. This intake verifier checks that subset's bytes and source association. It does not rerun the complete visual QA or claim those omitted image/test files are included here. Review was Atlas candidate-aware source QA, not a blind external review or independent-model diversity.

The initial Douglas proposal correctly failed strict host validation. Its error summary and builder preimage remain in `preparation-history`. Root then independently verified the preserved official domain chain, added only `www.douglasco.gov`, and tested the host boundary. The transaction pins the resulting `geode/constants.py` SHA256 `58f2073fb806d6dd13d229a7f57444e288d4b6cabe92abc395c1ce198cf8ef64` and all 13 other transitive local modules. No URL was nulled or relabeled to bypass validation.

The transaction preserves the exact 61-row raw manifest and 62-row ledger byte prefixes. Both end with their original newline. It appends one deterministic two-record suffix, without reserializing existing JSONL, and separately replaces the typed report. The expected result is 63 raw records / 64 ledger records; the previously missing ledger-only executive-order original stays explicitly missing. All new records remain `archived_pending_pipeline`.

Before mutation, the transaction validates the approved two-source ID/authority/layer/final-URL tuples, source SHA and bytes, current final-record host/layer/path rules, all exact control prefixes, current policy/queue guards, all transitive code pins, and current reconciliation. It scans raw files at matching sizes and LFS pointers for duplicate hashes, and refuses unrelated transaction states, symlinks or special files. Independent legacy comparison covers 48,390 legacy records and the two registries; it is separate from the raw-file scan. Snapshots and originals use immutable atomic creation. Control files use exact-before-byte checks and atomic replacement. Each interrupted boundary resumes the same intent, timestamp, suffix and source paths. Repeated completed apply verifies rather than adding rows.

`reference/` retains the reviewed Springs implementation and tests unchanged. This new copy changes the selected source identities, mixed county/city layers, exact 61/62 baseline, 63/64 result, transaction prefix, current runtime pins and preparation loader. The new loader verifies the sealed prepared data directly; it does not execute a preparation-supplied verifier. The unused legacy `VERIFIER_SHA` constant was removed in the root-requested readability revision. The helper recognizes this handoff layout and the approved durable `prepared-transaction` layout; `--root` is always available explicitly.

From this folder, prepare-only verification and focused fixture tests are:

```sh
PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-status-venv/bin/python -B validate_package.py --live --root '/Users/mcoors/Documents/Project Geode/MasterLegalDatabase'
PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-status-venv/bin/python -B -m pytest -q -p no:cacheprovider test_transaction.py
```

Root-only commands, after review (the first is still read-only):

```sh
PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-status-venv/bin/python -B transaction.py --root '/Users/mcoors/Documents/Project Geode/MasterLegalDatabase' --dry-run
PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-status-venv/bin/python -B transaction.py --root '/Users/mcoors/Documents/Project Geode/MasterLegalDatabase' --apply
PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-status-venv/bin/python -B transaction.py --root '/Users/mcoors/Documents/Project Geode/MasterLegalDatabase' --verify
```

A failed or interrupted apply must use the same packet and execution directory; do not delete the intent or rebuild timestamps. The outer inventory explicitly excludes the future `execution/` directory, whose contents are checked by the transaction validator. An offline package check does not certify that intake occurred. Retain the external final manifest digest when copying; `validate_package.py --expected-manifest DIGEST` checks that independent pin.

59 focused tests passed with 94% branch-inclusive transaction coverage. They include real selected-source preflight, exact prefix preservation, mixed-layer paths, ID/URL/owner swaps, conflicts, original immutability, interruptions, idempotency, unsafe paths, locks and code/policy mutations. The early root-directory pytest invocation failed before collection because `transaction` was outside its import path; the corrected folder-scoped runs passed. Full suite, new source review, inventory joins, lookup release, monitoring enrollment and legal-currentness promotion are outside this preparation.

The complete first 100-file packet is preserved byte-for-byte under `historical/first-prepared-9a12c339/`, including its original final manifest. This revision only reformats new code, names the fixed identity map and removes the unused constant; original source, proposed records, acquisition evidence and exact historical control prefixes remain unchanged.
