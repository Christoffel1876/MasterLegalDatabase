---
title: Coverage and CCR implementation evidence
date: 2026-09-09
---
# Coverage and CCR implementation evidence

The first implementation package adds an actual coverage inventory and a bounded
daily CCR source check. It also records the failed latest-file recovery and
successful historical recovery. This is progress on the approved roadmap;
statewide and local current-source coverage remain incomplete.

## Local live CCR trial

The check began at `2026-09-09T23:58:59.181378Z` against the official Secretary
of State pages. It traversed department 12, Department of Local Affairs:

| Measure | Observed result |
| --- | ---: |
| Agencies discovered and checked | 7 |
| Rule pages checked | 26 |
| Original source URLs/files preserved | 87 |
| Downloaded bytes | 9,586,133 |
| Source-designated current records | 7 |
| Explicitly repealed records with unambiguous dates | 18 |
| Ambiguous records requiring review | 1 |
| Publisher's stated currency cutoff | August 13, 2026 |

The 87 sources comprise the welcome page, numerical catalog, seven agency pages,
26 rule pages, and their 52 PDF/Word documents. The current designation on a
version table does not override an explicit repeal in the rule title. The
ambiguous record, `8_CCR_1306-1`, has the source title “NON-RATED PUBLIC SECURITIES
REPORTING - Repealed eff. 12/02/02”; the abbreviated date is preserved as source
text and not expanded into an invented four-digit year.

All 26 pilot IDs match existing records in
`02_Regulations_CCR/_meta/ccr_rules_meta.jsonl`. That inherited file labels all
1,035 records `active`, including these 26. The 18 clear repeal designations
therefore identify concrete discrepancies for review. This comparison uses the
regulation metadata; acquisition metadata separately records download outcomes
such as `skipped_existing`.

An independent local check validated all 26 verification records, all 87 source
hashes and lengths, the agency/rule identities, and preservation of every linked
current/future document. Replaying the captured source bytes on a later check
date returned `no_change` and left every file byte unchanged. Regression tests
separately cover an effective-date rollover that changes classification even
when source bytes stay identical.

Local evidence remains under ignored `.geode_runtime/` directories:

- `ccr-current-validation-2026-09-09/`: complete trial originals and inventory.
- `ccr-current-live-report/`: source report, changed paths, independent integrity
  results, and `canonical-comparison.json` with the specific discrepancies.
- `ccr-current-replay-report/`: no-change replay result.

The trial does not publish replacements for canonical legal text. The daily
workflow repeats discovery independently and proposes its own evidence through
a data PR requiring review.

## Coverage and county findings

The [generated coverage baseline](COVERAGE_BASELINE_2026-09-09.md) recounts
64 county identities, 272 municipal identities in the registry, and two district
identities. The active municipal index contains 85 identities; directory counts
need reconciliation. These measures are repository inventory, not verified
current jurisdiction totals or complete legal collections.

The county index and two county metadata files are unresolved LFS pointers.
Municipal legal-rule and unit files are absent. District metadata contains 708
units, while its index exposes identities and two preserved-source declarations.
The dashboard distinguishes these states and does not convert local download age
into verified source currency.

Historical local downloads comprise 48,390 attempts for 34,471 distinct source
ID/URL pairs, including 13,919 repeats and 2,211 latest recorded failures. Their
referenced originals are absent from the baseline checkout. The dashboard also
flags 11 supplementary records whose claimed original points to derived JSONL.

The [county recovery audit](COUNTY_RECOVERY_2026-09-09.md) provides exact hashes,
sizes, Git commits, and repository responses. Six latest LFS objects totaling
922,901,200 bytes could not be obtained from either GitHub repository. Four
older ordinary Git blobs totaling 149,045,688 bytes were recovered as historical
evidence. The owner has no backup location. Reacquisition remains necessary.

## Review and operating limits

Independent code review reproduced and resolved two discovery defects before
activation: unrecognized agency rows could have been omitted on a first run,
and a rule link could have pointed to a different department/agency. Both cases
now fail before promotion. Tests cover incomplete discovery, missing sources,
malformed pages, corrupt evidence, transaction rollback, no-change behavior,
future dates, publication races, and allowed-path restrictions.

Whole-corpus schema validation retains two pre-existing failures: the local
review-summary check encounters the missing `LOCAL_REVIEW_QUEUE.jsonl` LFS
object, and `08_County_Authorities/_index.jsonl` is another unresolved pointer.
The checker reports the first failure under
`_CONTROL_PLANE/LOCAL_REVIEW_SUMMARY.json`, although the summary itself is valid
JSON. These inherited input failures are not repaired by a successful CCR
verification transaction.

The clean minimal-dependency pilot suite passes 147 tests. Combined line/branch
coverage is 92% for the CCR collector, 97% for the dashboard, and 98% for the
publisher. Workflow YAML parses successfully. Original HTML fixtures retain
their source bytes, including the publisher's whitespace.

The full-suite check also exposed a UTC/local-date mismatch in validation of
retrieval dates near midnight UTC. Retrieval dates use UTC; the targeted fix
compares them against the UTC calendar date and retains future-date rejection.

Collection is read-only; publication receives separate write permissions and
rechecks the candidate bundle and same-run validation report. The bot maintains
one department-12 data PR and never approves or merges it. Run reports retain
failed and no-change outcomes. Seven scheduled successes, missed-run monitoring,
archive restore exercises, canonical CCR reconciliation, and local pilot
collection remain subsequent acceptance work.
