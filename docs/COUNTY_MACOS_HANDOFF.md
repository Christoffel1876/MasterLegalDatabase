---
title: County collector handoff for the always-on Mac
date: 2026-09-10
status: prepared_not_installed
---
# County collector handoff

The owner has an always-on macOS machine and will return to setup when it is
available. **No account, service, scheduler, or remote connection has been created.**
The repository contains a collection wrapper and an inactive
[launchd example](../deploy/macos/org.projectgeode.county-collector.plist.example).
The placeholder hashes deliberately prevent that example from running as supplied.

The wrapper runs the existing county collector with the same selected sources,
ordinary request identity, pacing, and access checks. It adds an exclusive run
lock, separate UTC run directories, code and manifest fingerprints, start and
completion receipts, and a 45-minute execution limit. It preserves child failure
status and does not call a publisher. A successful collection report is not proof
of legal currency, reviewed publication, or an actual scheduled invocation.

## Resume on the other Mac

1. Open this project in Codex on that Mac. Use the accepted repository revision,
   not a downloaded folder of unknown version. Record the exact commit being
   installed and review the source/manifest hashes before enabling anything.
2. Create a dedicated unprivileged collector account and an isolated directory
   layout. Keep reviewed code and its Python environment writable only by the
   maintainer. Give the collector write access to its corpus, reports, and logs.
   The example uses `/Users/Shared/GeodeCounty/{code,venv,corpus,reports,logs}`.
3. Install the frozen `requirements-county.txt` dependencies in the dedicated
   Python 3.11+ environment. Use no personal GitHub token, Git credential store,
   SSH agent, or account keychain. The wrapper's filtered child environment
   supplements these account permissions; it does not replace them.
4. Seed the corpus **once** from the reviewed county baseline: both
   `08_County_Authorities/_verification/reacquisition/jefferson-clear-creek-state.json`
   and `jefferson-clear-creek.jsonl`, plus every original referenced by the state's
   `sources` dictionary. Preserve their exact bytes and timestamps. Do not copy the
   unresolved historical LFS pointers as a substitute. Missing or inconsistent
   baseline evidence must fail before fetching.
5. Compute the installed source fingerprint using
   `geode.pipeline.county_scheduled_run.code_fingerprint(code_root)` and the SHA-256
   of the reviewed manifest. Replace both placeholders in a copy of the example.
   Record the commit, fingerprints, Python version, and dependency installation
   alongside deployment evidence. The source fingerprint covers executable source
   and dependency definitions; it does not attest to the entire operating system.
6. Run one ordinary manual collection on that machine and inspect its receipts,
   complete source counts, originals, and unchanged replay. Stop on HTTP 403 or
   another denial and record the failure; do not vary identity, credentials, or
   network routes to defeat it. Current evidence does not establish why the
   GitHub-hosted request was denied.
7. Only after that check, configure the system LaunchDaemon with the verified paths and
   schedule. The example specifies **07:17 in the Mac's local timezone**, not a
   fixed UTC hour. Record the actual timezone and daily slot, and coordinate the
   transition from hosted collection so two schedules do not run indefinitely.

The durable corpus is updated locally as sources change. Do not overwrite it each
day with the initial GitHub snapshot: doing that would erase continuity and pending
local evidence. Code or manifest upgrades require deliberate review and migration.
The exclusive lock belongs to the persistent corpus, so a second report destination
does not permit an overlapping collection of that corpus.

Apple recommends `launchd` for timed jobs. Its calendar jobs can run after waking
from sleep, but a job missed while powered off waits for the next scheduled slot.
The Mac must therefore remain available at the chosen time. See
[Apple's scheduling documentation](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/ScheduledJobs.html).

## What still needs implementation or operating evidence

Collection on this Mac does **not** automatically update GitHub. Initial publication
can be reviewed by an operator. A later automatic handoff must authenticate the
producer, verify originals and allowed paths, check the current repository baseline,
and keep repository write credentials on a separate trusted publisher.
Preserve cumulative unpublished changes: a later local no-change report can follow
an earlier changed run that has not yet been published. The latest report alone
does not establish whether GitHub has received every local update.

Choose an independent destination for run receipts and failure/missing-run alerts
when setup resumes. A monitor running only on the collector cannot detect that its
own machine is offline. No external alert or missing-run watchdog is installed.

Retain evidence of seven consecutive actual daily scheduled successes before
expanding the county pilot. No-change checks qualify when all selected sources and
validation checks succeed; manual runs, replays, partial runs, and setup tests do
not. Receipts alone are not proof of scheduler origin: retain the service's actual
invocation evidence and expected slot as well. Test a missing-run alert and recovery.

The current acquisition scope remains four catalogs and 30 selected PDFs from
Jefferson and Clear Creek. The new rezoning study contains additional research
sources; those are not silently added to the daily acquisition manifest. Widening
that manifest is a separate reviewed change after the operating pilot is reliable.
