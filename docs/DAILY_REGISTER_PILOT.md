# Daily Colorado Register pilot

The pilot's working repository is
[Christoffel1876/MasterLegalDatabase](https://github.com/Christoffel1876/MasterLegalDatabase).
Use its [Actions page](https://github.com/Christoffel1876/MasterLegalDatabase/actions)
for run status and its pull requests for update review. The original repository is
retained as upstream history; activation does not depend on its owner's permissions.

The pilot checks four rulemaking sections in Colorado Register publications dated
July 1, 2026 onward: proposed rules, permanent rules adopted, emergency rules
adopted, and terminated rulemaking. It preserves official issue responses and
documents linked directly from their rulemaking rows, then updates factual records
through a reviewable pull request. The hearing calendar and miscellaneous notices
are outside this first collection scope. Hearing/eDocket detail pages are preserved
when needed to resolve a row's CCR citation; the pilot does not recursively collect
every link on those pages.

It does not interpret legal obligations or calculate burden. Preserving a document
linked by a notice does not establish that the document is the current, complete
Code of Colorado Regulations. Agency names are preserved exactly as source text;
an unverified registry `agency_code` remains `null`, rather than being invented from
the name. Additional source dates, including emergency expiration and termination
dates, remain in the per-notice provenance row even where the shared canonical
notice schema has no corresponding date field.

## What runs

`.github/workflows/register-daily.yml` runs daily at **12:23 UTC** (06:23 MDT / 05:23
MST) and supports **Run workflow** from the Actions page on `main`. Concurrent runs
wait rather than overlap. A source check finding no changes is a successful run.
A fetch, extraction, validation, merge, or publication failure is a failed run.

1. A job with read-only repository permissions starts from `main`, fetches the
   existing `codex/register-daily-update` branch if present, and verifies that its
   unmerged changes contain only pilot data. It merges current `main` into that
   branch; a conflict stops the run for review. Pending original downloads and
   source hashes survive between checks before a reviewer merges the PR.
2. Offline pilot regression tests run. The source checker fetches official pages,
   compares source hashes, parses factual notices, validates the changed records,
   archives prior canonical bytes, and applies the validated transaction.
3. The publishing harness stages only paths enumerated in `changes.json`. It
   independently rejects non-allowlisted paths, deletions, executable files,
   symlinks, modified archives, and archive filenames inconsistent with their
   SHA-256 content hashes. Ignored originals are explicitly included individually.
   A validated local commit is exported as a Git bundle.
4. A separate publishing job receives repository-content and pull-request write
   permissions. It rechecks the candidate, confirms that neither `main` nor the
   pending branch changed after validation, and pushes without force to the bot
   branch. It creates or updates one PR against `main`. It never merges that PR.

When neither the check nor an existing pending PR has data changes relative to
`main`, no commit or PR is created. A pending PR can remain open across no-change
checks. Daily success timestamps belong in the run reports, avoiding meaningless
daily corpus commits.

## Data and evidence

The publication allowlist is deliberately narrower than the complete repository:

| Path | Contents |
| --- | --- |
| `04_Rulemaking/YYYY/register_YYYY_QN.jsonl` | Touched quarterly notice records |
| `04_Rulemaking/_index.jsonl` | Retrieval index |
| `04_Rulemaking/_meta/rulemaking_notices_meta.jsonl` | Notice metadata |
| `04_Rulemaking/_dataset/rulemaking_notices.jsonl` and `.csv` | Derived notice views |
| `04_Rulemaking/_dataset/register_daily_sources.jsonl` | Per-notice source provenance |
| `_CROSSWALKS/rulemaking_to_regulation.jsonl` | Notice-to-regulation links |
| `_CONTROL_PLANE/MASTER_MANIFEST.json` | Relevant pilot/layer inventory changes |
| `_CONTROL_PLANE/REGISTER_REFRESH_STATE.json` | Source hashes and committed evidence references |
| `_RAW_ARCHIVE/register/daily/<sha256>.<extension>` | Immutable official HTML/PDF/DOCX/DOC/RTF bytes |
| `_SNAPSHOTS/register_daily/<sha256>.<json\|jsonl\|csv>` | Immutable prior canonical file bytes |

Only new source originals and snapshots are accepted. Existing archive files are
never overwritten or deleted. The broader historical `_RAW_ARCHIVE` and county
LFS archives are not required to run this bounded pilot.

Some SOS HTML includes a passive Cloudflare script containing values that change
on every request. Only the exact known wrapper is ignored when comparing HTML for
substantive changes. Original archived bytes and their SHA-256 integrity hashes
remain intact. If that wrapper is the only change, the check reuses the previously
archived original and avoids a new corpus commit. Legal text, links, whitespace,
other scripts, and an altered or extended wrapper remain significant. This does
not execute the script or solve an access challenge; blocked source responses still
fail the check.

Every collection job writes an Actions summary and retains a uniquely named
`register-report-<run-id>-<attempt>` artifact for 90 days (subject to repository
retention policy). Successful source checks contain:

- `report.json`: actual check time, success/failure, source and publication counts,
  added/updated notices, validation outcome, changed paths, and errors.
- `summary.md`: readable status and scope limitations.
- `changes.json`: exact transaction path list, empty when no changes were found.
- `tests.xml`: the offline regression results from that run.
- `coverage.xml`: coverage evidence for the three new pilot modules.

Setup failures can happen before the source checker starts; their job result and
fallback summary must not be interpreted as a successful source check. Publication
has a separate summary and retained candidate/PR metadata. A failed publication
does not become a successful scheduled run merely because source collection passed.
Candidate bundles are kept for 14 days; original source evidence remains in Git
on the pending branch and, after review, on `main`.

## Run locally

Use Python 3.11 or later in an isolated environment, from the repository root.
The official-source transport also requires `curl` with a trusted system CA store;
the Ubuntu 24.04 GitHub-hosted runner includes it. TLS verification remains enabled.
Requests and redirects are currently limited to HTTPS `/CCR/` paths on
`www.sos.state.co.us` and `sos.state.co.us`. HTML, PDF, DOCX, DOC, and RTF are supported
source formats. A different official hostname or an unsupported attachment format
stops the check for review; parser recognition alone does not authorize collection
from a new source location.

The source checker identifies DOCX files from their ZIP structure, including when
SOS serves a generic MIME type. A document link returning an HTML error page is
rejected. HTML decoding follows byte-order marks, HTTP charset declarations, then
early HTML declarations, in that order. Undeclared HTML uses valid UTF-8 or the
standard Windows-1252 HTML fallback. Unknown relevant encoding labels, conflicting
declarations at the same priority, or malformed encoded text stop the check instead
of silently replacing characters.

```bash
python -m venv .venv-register
source .venv-register/bin/activate
python -m pip install -r requirements-ci.txt
python -m pytest tests/test_register_daily*.py tests/test_publish_register_update.py tests/test_register_table_parser.py tests/test_register_pipeline.py -q
python -m geode.pipeline.register_daily --root . --since 2026-07-01 --report-dir .geode_runtime/register-refresh
```

The source-check command writes validated data locally. Inspect its report and Git
diff afterward. The publishing harness is designed for clean ephemeral CI checkouts;
do not run its `prepare` phase in a working checkout containing unrelated edits.
`requirements-register.txt` freezes the small source-check runtime;
`requirements-ci.txt` adds the frozen offline test dependencies. Neither installs
the full application, LLM clients, nor the optional document-extraction stack.

The pilot has hard limits of **15,000,000 bytes per source**, **150,000,000 downloaded
bytes per run**, and **500 distinct source URLs per run**. Its start date must be in
the current calendar year or either of the two preceding years. Reaching a limit
fails the run without publishing a partial update. Review the collection window,
limits, and state migration before a cap is reached; the fixed July 1, 2026 start
date requires a reviewed migration before 2029. These limits are deliberate pilot
boundaries, not an indefinitely expanding statewide collection schedule.

## Activation and review

Merge the reviewed implementation into `main` to make the schedule available.
Keep the repository's default workflow permissions read-only; the workflow grants
the publisher only its required write permissions. Under **Settings → Actions →
General**, Actions must be enabled and permitted to use the pinned GitHub-authored
actions. The setting **Allow GitHub Actions to create and approve pull requests**
must permit PR creation. The workflow uses that capability to create PRs only; it
does not approve them. Organization policy can restrict these settings.
See [GitHub's Actions settings documentation](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository).

Dispatch one initial run from `main`, inspect the full report and resulting PR,
then observe the actual daily schedule. A reviewer should compare added/changed
notices to the preserved official evidence and read validation errors before
merging. Unresolved source extraction errors stop publication rather than being
silently skipped.

`Register pilot checks` is read-only PR/main CI using the same offline pilot tests.
Its name and scope are intentional: it does **not** certify the pre-existing
historical or county corpus. CI retains coverage reports and requires at least 90%
coverage, including branches, separately for the new daily pipeline, source parser,
and publisher modules. The September 9, 2026 full-corpus validation still has two
pre-existing failures involving `_CONTROL_PLANE/LOCAL_REVIEW_SUMMARY.json` and
`08_County_Authorities/_index.jsonl` from the incomplete county/LFS handoff. Those
failures remain outside this pilot's validation claim.

Bot-token PR events can create workflows that require
maintainer approval; approve the checks shown by GitHub if needed. The collection
job already executes the regression checks before publishing the candidate.
See [GitHub's current token-event behavior](https://docs.github.com/en/actions/concepts/security/github_token).

## Seven-day milestone

The operational milestone requires evidence accumulated after activation:

1. Seven successful **scheduled** runs on seven consecutive UTC dates, with a
   successful official-source report for each date. Manual reruns are useful for
   recovery and testing but do not demonstrate that seven daily triggers occurred.
2. A known-change test and a no-change replay both pass; offline fixtures exercise
   these cases even if the live source is unchanged during the observation week.
3. A real source-backed update PR exists and passes the pilot checks, with original
   evidence and reviewable changed records.

List the actual schedule history with:

```bash
gh run list --workflow register-daily.yml --event schedule --limit 30 --json databaseId,createdAt,status,conclusion,url
```

Open each qualifying run and inspect its retained `report.json`; do not infer a
streak from commit dates, manual runs, or a successful setup step. Record the seven
run URLs and the reviewed data PR when declaring the milestone complete.

GitHub schedules are best-effort and can be delayed. Scheduled workflows run only
when their file exists on the default branch; public repositories can have their
schedule disabled after 60 days without repository activity. Check that a new run
exists each day during the pilot and inspect Actions for failures. No external
uptime monitor is included in this first implementation.
See [GitHub's scheduling limitations](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule).

## Recovering a stopped run

- **Source blocked, missing, or malformed:** inspect the source URL and retained
  report, repair the parser or source boundary with a fixture, then rerun. Do not
  mark a failed source as current to get a green run.
- **Main or the pending branch moved:** rerun; the harness deliberately refuses to
  replace work based on an old baseline.
- **Merge conflict:** review and resolve the data conflict on the pending branch,
  preserving the original evidence, then rerun. No force-push is necessary.
- **PR creation denied:** enable the repository setting permitted by organization
  policy, then rerun. The already-pushed bot branch preserves collected data.
- **Bot branch contains code or an invalid archive:** review the unexpected commit
  before restoring the branch. The harness will not execute or publish its changes.

No workflow uses `pull_request_target`, an unpinned action, a personal access token,
an LLM service, or automatic PR approval/merge.
