# Colorado Register pilot implementation and validation

The first daily-source pilot is implemented on `codex/daily-register-refresh`.
It is **not active on the repository's default branch yet**. GitHub authentication
is configured for `Christoffel1876`, which has read-only access to
`GEODE77/MasterLegalDatabase`. The implementation is being submitted through an
account-owned fork for review. A repository maintainer must merge the implementation
and enable the required Actions settings before the initial run, data PR review,
and seven consecutive scheduled daily checks can be completed.

## Live source validation

The completed live check started at 2026-09-09T23:02:18Z and used an isolated copy
of the existing rulemaking corpus. It collected directly from the Colorado
Secretary of State with standard verified HTTPS requests.

| Result | Verified value |
| --- | ---: |
| Publications checked | 4: July 10, July 25, August 10, August 25, 2026 |
| Distinct source URLs checked | 203 |
| Downloaded source bytes | 65,256,601 |
| Unique immutable original files | 201 |
| New notices | 124 |
| Proposed / adopted / emergency / terminated | 59 / 52 / 10 / 3 |
| Historical notice records preserved without changing their values | 7,955 |
| Resulting notice count in the isolated candidate | 8,079 |
| Existing notices updated | 0 |

Every preserved original matched its SHA-256 hash. The candidate passed the
publisher's path allowlist. Its index, metadata, dataset, and quarterly files
agreed. All 124 new records passed both Pydantic validation and the control-plane
JSON Schema. Replaying all captured sources returned `no_change`, with every existing
file byte unchanged. This replay is an offline repeatability test, not evidence
of another live or scheduled daily check.

The live test's data remains separate from the working corpus under the ignored
directory `.geode_runtime/register-pilot-validation-2026-09-09/`. It contains the
originals, snapshots, complete candidate data, `verification.json`, first-run and
replay reports, source logs, test logs, JUnit results, and coverage report. The live
trial's candidate data is not included in the implementation PR.

## Code and test results

- Restored the missing completeness and faithfulness verification stages.
- Corrected local freshness reporting to calculate elapsed time and identify
  missing or invalid check dates as unknown.
- Added incremental Register parsing and validated, atomic updates with immutable
  originals, prior-version snapshots, history checks, and rollback on failure.
- Added a daily 12:23 UTC workflow and a separate publisher that proposes a review
  PR. It never directly updates `main`, force-pushes, approves, or merges a PR.
- Froze the small pilot dependency set and added CI coverage gates.
- Reconciled the notice JSON Schema with the existing Pydantic evidence fields,
  terminated notices, and explicitly unknown agency codes and routing outcomes.
- Final full repository and orchestration test run: **683 passed**, five existing
  dependency deprecation warnings.
- Clean minimal-environment pilot CI run: **135 passed**. Coverage gates passed
  individually: pipeline 94%, parser 90%, publisher 94%.
- Code diff whitespace checks passed. The factual HTML fixtures intentionally
  retain the source website's original whitespace.

Tests include real source excerpts, unchanged and changed responses, document-only
changes, strict character decoding, generic-MIME Word downloads, blocked sources,
HTML error attachments, disappearing records, corrupt archives, rollback after
disk failure, safe temporary files, and pending-PR preservation.

Full-corpus validation still fails on the two pre-existing Git LFS pointer files:
`_CONTROL_PLANE/LOCAL_REVIEW_SUMMARY.json` and
`08_County_Authorities/_index.jsonl`. This pilot does not certify the statewide or
county corpus. Historical Register records and current CCR legal status remain
unverified; registry agency codes are null when not established by source evidence.

## Deployment and next evidence

See [the operating guide](../DAILY_REGISTER_PILOT.md) for installation, exact
scope, collection limits, activation, recovery, and the seven-day acceptance
criteria. After opening the implementation PR, a repository maintainer must
merge the reviewed workflow into `main`, verify Actions permissions, dispatch the
first collection, and review its source-backed data PR. Record seven actual
successful scheduled runs before declaring the daily monitoring milestone met.
