---
title: Three accepted source review joins — prepared inventory only
status: prepared_not_installed
legal_currentness: not_verified
answer_safe: false
---

# Prepared inventory: 64 sources, 27 mapped reviews, 37 unmapped

This proposal adds one newly preserved Pueblo County original and three explicit review
links. It preserves all 63 prior authority joins and all 24 prior review joins. The
metadata of the first 63 source rows is unchanged except `reviews` and `review_status`
on the Larimer staff memo and El Paso English bylaws. The legacy coverage ledger stays
at its previous exact pin. These counts describe this custody inventory, not statewide
coverage or current-law readiness.

- Pueblo County `pueblo-county-planning-fees-sh-ext-002`: two-page, 88-physical-row source
  review, including conditional markers and continuations. Separate from City Pueblo.
  Actual repository receipt is 2026-09-13T04:55:23.097658Z. Earlier supplied URL, status
  and reservation/result times remain reported claims. Official raw URL and independently
  verified HTTP time remain null. Catalog 403 and adopting-document gaps remain.
- Larimer `larimer-equity-fee-memo-sd007-05`: complete four-page staff recommendation memo,
  82 source blocks and four logical table rows/five physical fragments. The source review
  retains OCR separately, proposal conditions, DNR qualifications and no adopted-effect claim.
- El Paso `el-paso-boh-bylaws-sd011`: all five English pages, 12,640 native bytes,
  170 nonblank lines and paragraph contexts. The visible 5/23/2012 footers are unlabeled
  dates, not independently verified adoption/effective dates. No Spanish equivalence claim.

The historical QA pending-acceptance or zero-intake fields are preserved. Later root
acceptances and actual intake are separately hash-bound in this preparation; historical
records have not been rewritten to manufacture a different sequence.

## Read-only checks

```bash
python -B verify_preparation.py
python -B verify_preparation.py --repository
python -B run_focused_tests.py
```

The first command is portable custody verification. The second and focused harness
require the original repository location and its exact accepted evidence. The harness
redirects only current plan/generated companion paths and the new historical checkpoint
to handoff files; it never invokes an installer or writes canonical data. Temporary test
fixtures and a handoff coverage output are the only test writes. Once sealed, run tests
from a disposable exact copy if preserving the seal is required.

## Root-only installation boundary

No apply tool is included. Before installation, verify all `repository_inputs` preimages.
Preserve the six preimages under the maintained inventory's new
`_SNAPSHOTS/BEFORE_FINAL_THREE_2026-09-13/` directory. Then copy proposed module and tests
to their corresponding maintained paths and the four proposed inventory companions to
the existing inventory directory. Run the maintained inventory `--check` and focused
suite. Do not rerun `prepare.py` as an installer: it writes only this proposal and changes
its preparation time. No raw, intake ledger/report, registry, source QA or legacy coverage
edits are part of this proposal. Root owns acceptance and any actual installation.

The exact source-fidelity review judgments belong to the accepted QA packages. This
inventory validates identities, schemas and explicit links; it does not independently
repeat their image review or infer legal effect from review counts.
