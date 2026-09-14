---
status: configured_not_scheduled
legal_currentness: not_verified
---
# Manual PDF source watch

The maintained command checks exactly two Colorado Springs Fire Department PDF URLs against
accepted canonical originals. It preserves response bytes and reports availability or byte
changes. It does not update the baseline, legal status, ordinary query results, raw manifest,
or source coverage. A changed PDF requires review. An unchanged PDF establishes only byte
equality at that URL and retrieval time.

The selected canonical IDs are:

- `colorado-springs-code-services-fees-2015-atlas-directed` — seven pages, SHA256
  `555570a62a5a557a824d1bcf3ecd2e60d57e48d19ea401f06a2e5b7ccb177e56`.
- `colorado-springs-construction-fees-atlas-directed` — seven pages, SHA256
  `e35de501a011fe55f03140bf91aef54226997d896fec0b6308a2eac9bd40909a`.

The city is the issuer. PPRBD's collection role remains distinct. The first PDF's visible
2015 title and the second PDF's stated July 1, 2026 effective date are source claims;
neither establishes current legal applicability. Existing structure-review limitations and
the unresolved Code Services edition cross-reference remain attached to each result.

## Readiness without HTTP

From the repository, using the environment that contains the project dependencies:

```sh
cd '/Users/mcoors/Documents/Project Geode/MasterLegalDatabase'
PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-status-venv/bin/python -B \
  -m geode.pipeline.manual_source_watch --root "$PWD"
```

Outside the repository, set module lookup explicitly:

```sh
PYTHONPATH='/Users/mcoors/Documents/Project Geode/MasterLegalDatabase' \
PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-status-venv/bin/python -B \
  -m geode.pipeline.manual_source_watch \
  --root '/Users/mcoors/Documents/Project Geode/MasterLegalDatabase'
```

Readiness validates the selected originals, accepted intake and source-custody receipts,
then streams the complete manual intake manifest and checks available PDF hashes. It reports
the actual counts; it does not assume a fixed corpus size. At preparation, there were 61
manual PDF records, all locally available by hash, with two selected and 59 unselected.
The accepted earlier finite prototype check made two actual requests, both unchanged, ending
2026-09-13 at 00:06:01.287236 UTC. That historical check is separately labeled; it is not a
production scheduling history or evidence of ongoing daily operation.

## Explicit finite execution

Review `config/manual_source_watch.json`, then supply its exact SHA256 and a simple new
run name. The default configuration is bounded to four serial request events and four
URLs, one same-host HTTPS redirect per source, 2 MB per source, 4 MB total, 30 seconds per
request and 300 seconds per invocation. Redirects consume events and bytes. There are no
retries, cookies, account sessions, or alternate routes after publisher denial.

The following is an execution example, not evidence that it was run:

```sh
PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-status-venv/bin/python -B \
  -m geode.pipeline.manual_source_watch --root "$PWD" \
  --execute --run-name springs-reviewed-check-001 \
  --reviewed-selection-sha256 91b4c46f7121de66d70b353405900f9d1ed3a3247718a9471ad2f1a9afa6dabb
```

Each invocation writes only `.geode_runtime/manual_source_watch/<run-name>/`. It keeps exact
selection and raw-manifest preimages, implementation hashes, dispatch time, reservations,
actual event times, original response bodies, allowlisted public-header derivatives,
`report.json`, and `RUN_MANIFEST.json`. Source acquisition at 23:10 UTC on September 12,
repository receipt at 23:56:16.492216 UTC, and subsequent check times are separate fields.
Output ancestors and evidence paths cannot be symlinks. Bodies must be complete, readable,
unrepaired and unencrypted PDFs before a byte comparison is allowed.

Use a new name for a new check. Reusing a name resumes that same immutable invocation:
completed or interrupted sources are never requested again. The CLI preserves its original
dispatch. A missing final inventory can be recovered only after all retained report and event
bindings pass. An expired run cannot acquire another source. Unrelated later append-only
manual intake records do not rewrite the old run's frozen manifest preimage. A damaged or
substituted input, incomplete temporary metadata file, or changed implementation is refused
for operator review; there is no automatic reset or overwrite.

## Read an existing run

```sh
PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-status-venv/bin/python -B \
  -m geode.pipeline.manual_source_watch --root "$PWD" \
  --verify-run springs-reviewed-check-001
```

Verification is offline. It checks the closed inventory, exact selected source records,
clock and deadline bindings, event budgets, raw body hashes, PDF structure and classifications.
It returns exit 0 for readiness or a completed comparison; exit 2 means a refused invocation,
verification error or stopped/incomplete comparison. A completed comparison can contain a
`changed` source and still needs human review. Report observations distinguish `unchanged`,
`changed`, `access_denied`, `not_found`, `transport_error`, `invalid_response`, `refused` and
`not_checked`. Missing or denied material is never interpreted as repeal or unchanged law.

## Completed finite validation

On September 13, 2026, the installed maintained command ran from 00:44:41.691307
UTC through 00:44:43.469133 UTC. Two HTTP 200 responses preserved 421,075 bytes;
both seven-page PDFs exactly matched their selected originals. The full repository
suite had passed 2,548 tests before this check. An offline verification returned
the same report. A replay after the original five-minute deadline, with transport
explicitly disabled, made zero requests and left every saved run byte unchanged.

The [saved live-check evidence](../research/local_review/manual-source-watch-live-2026-09-13/README.md)
includes exact implementation copies, actual event times and a portable read-only
verifier. This is one finite maintained run, separate from the earlier prototype.
Neither establishes daily operation. `review_needed: false` means the check found
no new byte discrepancy; it does not close existing extraction or currentness questions.

## Operational boundary

No scheduler, GitHub workflow, notification or publication is installed by this feature.
The Register, CCR and county collectors remain unchanged. Fixed URLs cannot discover a newer
edition published elsewhere or a changed parent-page link. The other manual originals are
not monitored by this selection. Broader discovery, reviewed baseline promotion and recurring
deployment each require a separate scoped integration.

The earlier prototype, authorization and actual finite check are preserved under
`research/local_review/manual-source-watch-prototype-2026-09-13/`; its portable validator is
read-only. Production imports only maintained project modules and validates research custody
as data. It never imports the historical packet's executable scripts.
