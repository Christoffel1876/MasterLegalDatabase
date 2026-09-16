---
title: Colorado Springs two-source watch prototype
status: PREPARED_NOT_DISPATCHED
legal_currentness: not_verified
scope: handoff only; no deployment or canonical changes
---

# Two preserved fee schedules, one finite check

This prototype compares two exact official PDF responses with their preserved originals.
It makes no public request by default. It has no scheduler, GitHub workflow, publication
step, canonical write, legal-effect detector or automatic baseline update. All tests and
three saved example runs use injected local responses and an explicitly labeled fixture
clock. They are not monitoring history or proof of a successful daily run.

| Discovery ID | Reserved canonical ID | Pinned original SHA256 |
|---|---|---|
| SD014-01 | colorado-springs-code-services-fees-2015-atlas-directed | 555570a62a5a557a824d1bcf3ecd2e60d57e48d19ea401f06a2e5b7ccb177e56 |
| SD014-02 | colorado-springs-construction-fees-atlas-directed | e35de501a011fe55f03140bf91aef54226997d896fec0b6308a2eac9bd40909a |

Both sources are issued by the City of Colorado Springs / Colorado Springs Fire
Department. PPRBD's described fee-collection role does not make it the issuer. The first
source's visible title is the 2015 Code Services schedule. The second states “Effective
07/01/2026”; that is a source assertion, not verified present applicability. The prototype
preserves these distinctions in every source result. It performs no fee calculations.

The exact proposed GET destinations are:

1. `https://coloradosprings.gov/system/files/feeschedule_codeservices_final_2015.pdf`
2. `https://coloradosprings.gov/system/files/2026-07/2026%20Fee%20Schedule%20Construction%20Services.pdf`

The `%20` sequences in the second URL are part of the observed exact URL. Each destination
is independently bound to the saved official parent iframe and its once-decoded viewer
argument. No viewer endpoint, guessed sibling filename, parent-page refresh or hidden API
is requested. Fixed URLs cannot discover a newer edition published elsewhere while the
old file remains accessible.

## Proposed request limits

Root must review `WATCH_PLAN.json` before any live execution. One invocation permits
at most four request events and four distinct URLs: two initial GETs and one same-host
redirect per source. Every hop is reserved before transport; a host change, including a
change to `www`, is refused. Limits are 2,000,000 body bytes per source across its hops,
4,000,000 total, 30 seconds per request, and 300 seconds per invocation. The original
files are 162,682 and 258,393 bytes, each seven physical pages.

The frozen SD014 guard supplies verified TLS, public-address checks, serial reservations,
exact complete or partial body preservation, selected public-header records and conservative
interruption accounting. There are no retries, cookies, authentication, access-denial
workarounds or automatic redirects. HTTP 401, 403 or 407 stops the entire batch. The second
source then remains `not_checked`, if not already attempted. Other failures retain earlier
results and their evidence. Cookie/authentication headers are never persisted by this guard;
the selected public headers are not a complete raw HTTP-header transcript.

The prepared plan is bounded by this session: no new source after 2026-09-13 01:25 UTC and
hard stop 01:55 UTC. Daily deployment requires a separately reviewed configuration and
scheduler. A later day cannot silently reuse this plan as continuing authorization.

## Results and custody

- `unchanged`: HTTP 200, complete permitted PDF, expected media type, exact old SHA256.
- `changed`: a complete permitted PDF has different bytes; review is needed. PDF metadata
  changes alone can produce this result. No legal change, new effective date or currentness
  is inferred.
- `access_denied` / `not_found`: actual publisher status, with no withdrawal or repeal claim.
- `transport_error`: no successful comparison; recorded HTTP status remains separate.
- `invalid_response` / `refused`: incomplete, invalid-format, corrupt, excessive or disallowed
  response/routing. Preserved prefixes are not called complete PDFs.
- `not_checked`: no request was reserved for that source; it is never treated as unchanged.

Each run is immutable under `runs/<simple-name>/`, with invocation, run, per-event reservation,
body, public-header and result records, then `report.json` and `RUN_MANIFEST.json`. Baseline
references in a report resolve from the prototype root; response references resolve from
that run's directory. The run receipt distinguishes actual UTC clocks from injected test
clocks and binds the plan, helper and implementation hashes. Operator-supplied dispatch
metadata is not independent proof of approval. Interrupted reservations are never retried
as a new source attempt. A failed final report write leaves earlier source evidence intact.

`evidence/custody/` is an explicitly selected 21-file subset of the accepted source-custody
package, including both complete PDFs and exact acquisition/referral receipts. Its copied
original manifest references additional images and review files not copied here; this
prototype does not claim to contain or rerun that whole source review. Original acquisition
intervals remain 2026-09-12 23:10:46.169682–23:10:46.652367 UTC and
23:10:46.676197–23:10:47.380038 UTC. Repository receipt times were unknown at preparation;
any later intake receipt needs an additive binding, not a rewritten acquisition timestamp.

## Offline commands

Python needs Pydantic 2, PyMuPDF 1.28.2, BeautifulSoup, jsonschema and the frozen guard's
ordinary HTTP dependencies. From any directory:

```bash
PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-status-venv/bin/python -I -B \
  "/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-12/manual-source-watch-prototype/verify_preparation.py"

PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-status-venv/bin/python -I -B \
  "/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-12/manual-source-watch-prototype/watch.py"
```

The first command verifies closed custody, all baseline/referral bindings, the typed test
receipt and three saved offline examples. The second validates the proposed plan without
requesting sources. `watch.py --verify-run offline-equality` replays one saved example.
Exit status is 0 for a complete successful byte comparison, 2 for a stopped or refused watch;
the preparation verifier returns 1 on failed verification.

After separate root review only, `watch.py --execute --run-name <new-name>
--dispatch-at <actual-aware-UTC> --reviewed-plan-sha256 <exact-reviewed-plan-hash>` is the
finite live interface. This is an interface description, not a dispatch command or approval.
No `--execute` invocation occurred during preparation. An existing run report can be read
again but is not refetched; use a new run name for a separately authorized check. The baseline
remains pinned until a distinct reviewed change explicitly replaces the watch selection.

## Testing boundaries

`test_watch.py` tests actual baseline byte equality, changed valid PDFs, missing/denied
sources, transport errors, media-type mismatch, truncation, malformed/encrypted/oversized-page
PDFs, redirect/request/byte budgets, interrupt recovery, no-change replay, report-write failure,
receipt tampering, source/issuer substitution and output confinement. Focused coverage covers
the new adapter's statements and branches; the byte-identical reused SD014 guard is excluded
from that percentage. Historical helper and preimage files are evidence, not commands to run.
