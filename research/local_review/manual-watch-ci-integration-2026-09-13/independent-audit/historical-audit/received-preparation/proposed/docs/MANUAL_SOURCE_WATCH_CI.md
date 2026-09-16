# Prepared daily manual PDF watch

This integration prepares daily fixed-URL comparisons for the existing eight reviewed sources. Local installation does not deploy GitHub Actions. Even after the workflow reaches the default branch, scheduled runs perform **readiness only** unless the repository variable `MANUAL_WATCH_DAILY_ENABLED` is explicitly set to `true`. Manual dispatch also defaults to readiness; its `execute` Boolean must be explicitly selected for public GETs.

Before enabling daily GETs, review the exact installed commit/configuration, pass the offline suite on Ubuntu 24.04/Python 3.11, run and review a separately authorized manual live pilot, then approve the repository enable variable. The preparation was tested on macOS/Python 3.14.3 and syntax-checked for Python 3.11. PyPI advertises a compatible CPython 3.10+ Linux x86-64 PyMuPDF wheel and Python-compatible BeautifulSoup/SoupSieve wheels; this is not an executed Linux test.

The workflow has read-only repository permissions, no persistent checkout credentials, no publisher, no source enrollment, and no automatic baseline changes. Its daily cron is `13:17 UTC`; scheduling does not establish actual execution or exact punctuality. The workflow records the actual checked-out commit and event context. The runner's `schedule_activation_verified=false` means that no cloud setting/authorization is independently certified by the local program. Existing producer `scheduler_installed=false` fields remain historical component claims, not evidence about the surrounding workflow's deployment.

## Fixed scope and limits

| Pair | Sources |
|---|---|
| Springs | 2015 code-services fees; construction-services fees |
| County | Arapahoe planning fees; Weld EHS fees |
| Western | Grand Junction fire fees; Mesa building fee Exhibit A |
| Greeley | Building permit fees; development impact fee memorandum |

All four run serially. Each has four request events/four distinct URLs, one same-host redirect per source, 2,000,000 bytes per source/4,000,000 per pair, 30 seconds per request and 300 seconds per source-run window. Aggregate maxima are **16 source HTTP events, 16 MB source bodies, and 20 minutes of source-run windows**. Dependency installation and offline verification are separate bounded job work; the job timeout is 40 minutes. No response failure is automatically retried. A failed pair does not erase its siblings' results.

`config/manual_source_watch_ci.json` pins all four reviewed selection digests and the exact code/configuration/custody/baseline dependencies. Its own digest is pinned by the runner. The 88 explicit pins include package startup/schema imports; third-party distribution identities remain the frozen requirements, not hashes of every installed library file. Every selected raw record and original remains checked by the existing maintained adapters. The complete raw manifest is read and bound per invocation, allowing reviewed unrelated append-only intake between runs. An unrelated missing original is informational in readiness; it is not permission to replace a selected original or bypass its custody.

## Commands after reviewed installation

From the repository root, readiness requires no public source requests:

```sh
python -B scripts/manual_source_watch_ci.py --root . --run-name local-readiness-001
```

After separate authorization, this performs the finite four-pair check:

```sh
python -B scripts/manual_source_watch_ci.py --root . --run-name approved-pilot-001 --execute --event workflow_dispatch
```

Always use a fresh safe run name (at most 40 ASCII letters/digits/underscore/hyphen, starting with a letter or digit). Existing CI output directories are refused. A later GitHub attempt has a new run-attempt identity; it does not silently resume or retry the original HTTP reservation. The underlying watcher supports precise recovery, but restoring a past invocation requires its exact evidence, producer code, selection and original deadline through a separate reviewed operation.

Schemas for summaries, process receipts and progress preimages are emitted before records. Before replacing a CI summary, both old JSON and Markdown are preserved with typed hash identities in bounded progress history (at most five prior versions). Source evidence and process logs remain write-once. This is process-interruption evidence, not a proven power-loss durability guarantee.

Output lives only under `.geode_runtime/manual_source_watch_ci/<run-name>` and the existing two dedicated watch runtime roots. It includes process argv/UTC intervals/exits, stdout/stderr, typed summary/schema, complete underlying source events and verified reports. Job artifacts retain these even after failure, with hidden closed-inventory lock members included. No raw archive, ledger, registry or legal record is written. Ordinary Git checkout with `GIT_LFS_SKIP_SMUDGE=1` and `lfs: false` is sufficient for the watched original bytes already committed as ordinary files; the two inherited missing county index LFS bodies are not watch inputs.

## Reading a result

- `unchanged`: every selected response was a complete valid PDF equal to its own fixed baseline.
- `changed`: all eight sources were verified, with at least one different complete PDF; legal effect is unknown.
- `incomplete`: at least one source/process/report could not establish a complete comparison. Verified changed/unchanged siblings remain listed.
- `setup_failed`: readiness, immutable pins, canonical immutability, or local preparation failed. A report is retained when the runner could start; the workflow has a separate setup-failure message if it could not.
- `ready`: offline readiness only; no source result is implied.

Every actual source status (including denial, missing URL, invalid response, transport error, refusal or unattempted source) stays explicit. `changed` needs human review and is not a current-law finding. Source dates and acquisition history are unchanged. Fixed edition URLs can stay unchanged when a new edition appears at a different URL; discovery is a separate bounded task.

The job summary and artifact provide results. No email, issue, webhook or other notification service is configured here, so this preparation does not promise Michael a change alert. No publisher credentials, login, cookie replay, proxy rotation or denial bypass is provided. Public cloud access may differ from the local pilot; preserve the actual response rather than changing identity or route.

The three existing official action commit identities and new package metadata are recorded in the preparation's primary-source receipt. Future workflow/pin updates need review. Do not run historical builders or frozen research tools during this workflow.
