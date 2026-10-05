---
title: El Paso LDC Chapter 2 scoped review integration
date: 2026-09-16
legal_currentness: not_verified
answer_safe: false
---

# Scoped metadata integration

The isolated review checkout now has 70 original-source rows, 38 scoped review links and
32 unmapped rows. One checked-passages link covers the accepted seven-page LDC Chapter 2
review: 119 passages and five structural links. All 70 authority joins, the prior 37
review joins, the other 69 rows and all custody fields remain unchanged.

Seven exact preimages are retained under the inventory package's named
`_SNAPSHOTS/BEFORE_EL_PASO_LDC_CHAPTER_2_2026-09-16` directory. Atomic-write helpers also
retained their timestamped preimages. Only the module allowlist, scoped tests, join plan,
inventory JSON and generated README changed. The two inventory schema companions and
accepted source-review wrapper are unchanged.

Actual focused tests pass all 175 cases; the inventory check and accepted wrapper verifier
pass. Three command logs and exact UTC boundaries are retained. The first passing test run
is retained under history; the final run follows a whitespace-only test-line wrap.

From the selected repository root:

```bash
PYTHONDONTWRITEBYTECODE=1 ../.geode-venv/bin/python -B research/local_review/el-paso-ldc-chapter-2-inventory-integration-2026-09-16/verify_integration.py --root .
```

The printed effective date remains unverified source wording. No currentness, official
HTTP acquisition or legal-answer status changed. Later external partial review and a
separate resolution handoff are outside this integration. Root owns the separately
identified inherited read/hash-race repair, full regression tests and publication; this
receipt records the exact metadata integration before that follow-up repair.

The receipt verifier requires the matching repository and source package, which are
referenced by exact hashes rather than duplicated here. Manifest-bound `.log` files must
be included explicitly despite ignore rules.
