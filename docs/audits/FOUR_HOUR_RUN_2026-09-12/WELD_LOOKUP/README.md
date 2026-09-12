---
title: Weld environmental-health source lookup acceptance
date: 2026-09-12
status: verified_scoped_implementation
legal_currentness: not_verified
---

# Weld lookup acceptance

The lookup now exposes the preserved Weld County environmental-health schedule:
137 rows in11 groups, with complete group/label/fee/note associations,313 exact
native lines, and separate page context. A visibly blank fee stays null. Printed
zero fees, market rates, hourly conditions, caps and source anomalies stay unchanged.
Grand Junction's57 rows and Greeley's19 entries remain available.

Atlas independently reviewed the implementation and ran eight real CLI examples
from outside the checkout: full lists for all three sources, blank/zero/condition
Weld cases, a contract-note-only match and refusal of current-law mode. All passed;
the frozen Weld evidence hashes were unchanged. The source package was not rewritten.

Focused validation: **144 passed**,95.90% combined line/branch coverage (97.37%
statements,90.70% branches). Full project validation: **2,024 passed,124 warnings,
314.97 seconds**, process exit0. Overall geode coverage is77.58% (displayed78%),
below the repository's90% target; this change does not resolve that legacy baseline.
The test log retains warnings, including resource warnings, rather than hiding them.

`ROOT_ACCEPTANCE.json` records actual command timings, result identities and checks.
`VERIFICATION.json` binds final code, logs, coverage and example outputs by exact hash.
Example JSON records were validated against the production result model before saving.
No new legal interpretation, fee arithmetic or currentness decision is implemented.
The lookup remains a fixed-source research tool; missing original catalog/index/queue
blobs, statewide completeness, adoption and amendment chains remain separate work.

Run the examples in `docs/RESEARCH_SOURCE_LOOKUP.md` from the repository root using
the project Python environment. This audit is a historical validation record;
new code changes require their own checks and must not overwrite this evidence.
