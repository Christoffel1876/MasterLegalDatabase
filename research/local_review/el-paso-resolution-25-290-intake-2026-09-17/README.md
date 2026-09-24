---
title: El Paso Resolution 25-290 custody intake
date: 2026-09-17
legal_currentness: not_verified
answer_safe: false
---

# One official-linked original preserved

Resolution 25-290 is now a county manual-original source with acquisition method
`manual_official_download`. The exact unchanged PDF is 116,282 bytes and two scanned pages.
The official parent anchor and complete HTTP 200 receipt are bound to the same source SHA.
The recorded download completed on September 16 at 21:52:46.950742Z; actual repository
intake occurred on September 17 at 20:56:10.956815Z. Neither clock substitutes for the
printed DONE date of October 28, 2025 or recording stamp of October 29, 2025.

The archive manifest has 71 originals; the ledger has 72 records, including the unchanged
missing EO history. Both old JSONL byte prefixes are preserved exactly and snapshotted.
The research inventory is 71 sources / 38 reviewed / 33 unmapped. All 70 prior rows and
38 review joins remain unchanged. This source's separate source-review package is retained;
no new review schema, complete-review credit, currentness or legal-answer status is added.

The fixed transaction was adapted from the retained Gunnison implementation (reference
copies included, never executed). It captures checked inputs, freezes actual intake time
once, validates request/record/official host, uses a cooperative lock, recognizes only
monotone partial states and refuses foreign suffixes. It derives the report only from the
captured ledger plus one record. No generic mutating append or reconciliation is called.
The scope does not promise a lock against unrelated noncooperating writers.

Sixteen offline transaction cases and 185 focused inventory cases passed. Live read-only
preflight, postverification and deterministic inventory checks passed. The new test
normalization requires the exact historical manifest prefix plus exactly this source;
old frozen receipts keep their historical hashes unchanged. The full suite belongs to root.

From the repository root, read-only:

```bash
PYTHONDONTWRITEBYTECODE=1 ../.geode-venv/bin/python -B research/local_review/el-paso-resolution-25-290-intake-2026-09-17/verify_intake.py
```

`PREPARATION.json` and `PROVENANCE.json` retain their truthful pre-application null receipt
fields. The final actual clock is in `execution/INTENT.json`, `execution/RECEIPT.json`, the
canonical record and `FINAL_AUDIT.json`. No source body was edited or repaired. The static
and execution files are now closed by `FINAL_MANIFEST.json`; rerunning apply is unnecessary.
Exact logs and the canonical PDF may be ignored by Git and require explicit inclusion by
the publishing owner. Selected custody inputs are a bounded subset of the unchanged full
Resolution evidence package, whose manifest is separately pinned.
