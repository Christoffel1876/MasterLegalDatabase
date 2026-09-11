---
title: Source inventory, reviewed lookup and missing-input diagnostics
created: 2026-09-11
scope: first_implementation_checkpoint_of_one_hour_continuation
legal_currentness: not_verified
---

# Source inventory, reviewed lookup and missing-input diagnostics

This checkpoint makes preserved evidence easier to locate and stops missing Git
LFS content from appearing ready for retrieval. It also expands the standalone
reviewed-source lookup from one municipal fee source to two. The original PDFs,
frozen reviews and canonical coverage ledger retain their separate identities.

## Result

- The [manual-source inventory](../../../research/local_review/manual-source-review-inventory-2026-09-11/README.md)
  maps 46 distinct preserved PDFs to their recorded authorities. Eighteen have
  explicit review links; 28 have no allowlisted review mapping. Each review keeps
  its scope and qualifications. These are snapshot counts, not legal coverage.
- The [lookup guide](../../RESEARCH_SOURCE_LOOKUP.md) covers the existing 57 Grand
  Junction fire-fee rows and 19 Greeley building-fee entries. Greeley's complete
  clauses, headings and footnotes stay associated, including displaced tax and
  electrical headings. All 29 source spans retain exact byte bindings.
- Readiness checks distinguish a Git LFS pointer from actual file content and
  validate JSONL through its final record. Runtime retrieval rejects an
  unhydrated catalog before attempting to use it. Local validation attributes
  dependency failures to the dependent file, preserving the valid summary JSON.
- A [bounded Larimer access check](../../../research/local_review/larimer-extension-access-session2-2026-09-11/REPORT.md)
  retained eight requested actions and one reported redirect. No signed extension
  or final July Board action was obtained; that result does not establish absence.

## Verification

The full implementation suite passed: **1,951 tests**, 136 warnings, 231.23
seconds. Overall `geode` line/branch coverage is 78%; this is below the project's
90% target and is not represented as full-package coverage compliance. Focused
coverage is 100% for the LFS/readiness modules, 99% for the inventory module and
95.77% for the expanded lookup module. The frozen log retains dependency,
runpy and SQLite resource warnings for inspection.

Independent read-only checks verified all 46 original identities, the 18 review
bindings and 92 referenced artifacts. A separate reviewer checked the lookup's
19 Greeley entries, footnotes, date qualifications, refusals, unsupported sibling
sources and retained Grand Junction behavior. No new visual transcription or
current-law certification is implied by those implementation checks.

[VERIFICATION.json](VERIFICATION.json) records commands, counts, implementation
hashes and evidence hashes, with its [schema](VERIFICATION.schema.json).
[full-tests.log](full-tests.log) is the actual complete run. The saved
[Greeley output](greeley-all-entries.json) is an actual CLI result from outside
the repository, validated against the lookup's result schema.

## Actual corpus condition

The [readiness report](readiness-report.json) passes 13 of 16 selected prerequisite
checks and returns `needs_review`. These three files still contain pointers to
unavailable original content:

| File | Declared original bytes |
|---|---:|
| `_CONTROL_PLANE/RETRIEVAL_CATALOG.jsonl` | 225,796,201 |
| `08_County_Authorities/_index.jsonl` | 172,131,787 |
| `_CONTROL_PLANE/LOCAL_REVIEW_QUEUE.jsonl` | 72,395,471 |

The actual `python -m geode.validate --layer all` command exits 1 with two
dependency issues: county index and review queue. Its [stderr log](corpus-validation.stderr.log)
is preserved; the command does not emit a JSON report to stdout. The readiness
report separately checks the missing catalog. Passing implementation tests and
this expected corpus failure are different observations.

The standalone lookup performs no fee calculations or current-law answering.
Its results remain `legal_currentness: not_verified`, `answer_safe: false`, with
unresolved legal dates. Greeley's original acquisition time and canonical official
source URL remain null; reported claims, repository receipt and review time remain
separate. No external EB015–017 completion is claimed.

This is an implementation checkpoint during the authorized continuation. Later
source reviews or plans, if completed, belong in separately dated supplements;
this audit does not certify work that had not finished when it was recorded.

## Next retrieval implementation

The [isolated-rebuild feasibility plan](RETRIEVAL_REBUILD_PLAN.md), prepared after
this implementation checkpoint, inspected the existing builder and reader. It
records 57,420 schema-valid index rows, source-path limitations, and a tiny fixture
that reproduced metadata fallback without a source body. Those rows are not
57,420 verified legal texts. A separate research catalog needs strict admission
receipts and a source-only reader before broader inputs are accepted. The plan
was preserved verbatim with SHA-256
`0f7515f061dbfd40da07f41842f371c4cec52d2cde5d6cd68cf184ebe6b1e193`;
no canonical catalog build was run.
