---
title: Fixed inventory integration — 69 originals and 33 review links
reviewer: Plato
date: 2026-09-13
legal_currentness: not_verified
---

This metadata-only proposal preserves all 67 existing authority joins and 30 review
joins, adds two actual Chaffee County custody rows, and links exactly three accepted
source reviews: Gunnison IWUIC, Chaffee electric ordinance r1 and Chaffee CWRC ordinance.
The result is 69 sources, 33 with explicit review links and 36 without an allowlisted
review link. These counts do not certify statewide coverage, complete legal codes,
current law, or answer-safe research.

Only the three exact schema entries are added to `manual_review_inventory.py`.
All other module behavior is unchanged. Every prior source row remains exactly equal,
except that the existing Gunnison IWUIC row gains its one bounded review and review
status. The two Chaffee additions retain county authority, distinct successful GET
completion times and the actual repository receipt of 2026-09-13T16:44:04.840983Z.
The legacy ledger binding is unchanged.

The marked-source reviews are classified `checked_passages`, including the electric
document's table fragments. Full scope/exception/markup/date and uncertainty fields
are linked; no overlapping block, table or paragraph count becomes a legal-rule count.
Historic pre-intake and pending-independent-audit fields in the accepted QA remain
unchanged. Their separate root acceptance receipts are pinned in `PREPARATION.json`.
Gunnison supplier acquisition times remain unverified; the later review does not turn
them into independently observed HTTP evidence. Chaffee original-header omissions
and earlier referral-custody qualifications remain attached to its rows.

`preimages/` holds the seven exact original files before preparation. `proposed/`
holds the six intended changed files: module, tests, join plan, inventory JSON, schema
and README. The inventory schema itself remains byte-identical; it is retained as a
deterministic companion. Installation preserves a named package snapshot
`_SNAPSHOTS/BEFORE_CHAFFEE_IWUIC_2026-09-13/` and changes only those authorized targets.
Any actual installation is recorded separately under `execution/`; preparation alone
does not establish that it happened.

129 focused tests passed against a temporary copied corpus, with 99.2537% coverage
including branches. The tests preserve all earlier checks and add exact source/owner/
schema refusal, rehashed currentness-promotion refusal, separate receipt/GET times,
complete recorded scope, and every prior join/row preservation. The first launch lacked
an explicit import path and failed collection; that log is retained unchanged. The
corrected invocation used the staged corpus explicitly. No public request, source QA
rewrite, original/custody mutation, or lookup-adapter change is part of this update.

From this folder:

```sh
PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-status-venv/bin/python -B verify_preparation.py
PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-status-venv/bin/python -B verify_preparation.py --repository '/Users/mcoors/Documents/Project Geode/MasterLegalDatabase'
```

The default verifies the closed preparation offline using retained hashes, schemas,
AST comparison and exact metadata preservation. The optional repository check also
replays all current source/provenance/review joins through the captured proposed
module, redirecting only its plan to the retained proposal. It does not write inventory
outputs. Both require Pydantic 2 and jsonschema; repository replay uses the maintained
runtime dependencies. Final full-suite validation is root's separate release check.
