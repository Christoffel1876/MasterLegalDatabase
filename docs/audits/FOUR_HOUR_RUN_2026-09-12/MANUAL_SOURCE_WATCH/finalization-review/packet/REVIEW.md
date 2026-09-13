---
title: Manual-source watch independent review and finalization fix
date: 2026-09-13
status: resolved_focused_checks_passed_full_suite_separate
public_requests: 0
legal_currentness: not_verified
---

# Disposition

One reproducible recovery defect was found and narrowly fixed. The maintained
adapter, HTTP helper, configuration and documentation were read against all eight
production hashes in `PRE_FIX_PREPARATION.json`; all matched before the fix.
No public requests were made. The review does not certify recurring operation,
new-edition discovery or legal currentness.

An otherwise complete HTTP response could finish just before its reserved
deadline, then cross the deadline while `finish()` hashed its reservation.
The helper saved `outcome: complete` with a late `finished_at`. The adapter
correctly returned `transport_error` and null byte equality, but its unchanged
strict verifier refused the late complete event. The resulting `report.json`
could not be sealed, and replay failed again without making another request.
This was a safe refusal and recoverability defect, not a false unchanged result.

The frozen original reproduction uses an injected fixture clock: close at
29.999 seconds, two milliseconds of simulated finalization hashing, and a receipt
at 30.001 seconds against a 30 second deadline. `REPRODUCTION.json`, its source script,
the generated fixture evidence and exact pre-fix source copies are retained.
These are not actual HTTP or wall-clock timings. The historical reproduction
asserts the old failure and should not be run against the corrected production.

## Narrow correction

Only `manual_watch_http.finish()` and its focused adapter tests were changed.
The helper now computes reservation/body/header references, captures one
`finished_at`, and converts an expired otherwise-complete result to
`timeout`, `partial_body: true`, with
`error_type: deadline_during_result_finalization` before saving it.
Exact retained response bytes, prior reservations, custody dates and baseline
originals stay intact. The report verifier's deadline checks were not weakened.

Two new regression cases cover equality with the deadline and one millisecond
beyond it. Both retain the original PDF bytes, produce null equality and a
verifiable stopped report, permit the separately bounded second source to remain
unchanged, and replay the same sealed run with zero additional fixture requests.

The complete focused watch set passed: 173 tests, 5 warnings, 23.96 seconds.
Coverage with branch measurement was 90.92% for the adapter and 94.97% for the
helper; combined 92.84%. Branch-only coverage is recorded separately in the
coverage file and must not be confused with branch-inclusive coverage.
The parent accepted the narrow diff and started repository-wide tests separately;
this packet makes no claim about their outcome.

## Reviewed boundaries

The reviewed configuration fixes exactly two source identities/URLs and canonical
PDF hashes. It is configured, not scheduled. Source-context dates remain claims.
Invocation selection and selected raw-manifest lines are pinned; the current
canonical originals and accepted prior custody are validated before requests.
Readiness's other-original count is a local hash-availability count, not a review
or monitoring count. No normal query or baseline promotion is introduced.

Reservations precede transport and consume bounded events/bytes. Same-host
redirects require recorded predecessor evidence and respect the hop cap. Publisher
denials stop the batch. Headers and body parser operations have shutdown-backed
deadlines; conflicting length rules fail closed. Only complete valid HTTP 200 PDFs
can establish byte equality. Missing, denied, partial, non-PDF and late responses
do not become unchanged sources or repeal conclusions.

Missing final seals can be recovered only after retained report/event bindings
validate. Interrupted reservations are not retried. Incomplete temporary metadata
or damaged source evidence requires operator review, as documented; this is not a
claim of recovery from every filesystem or power-loss failure.

## Safe portable check

`final/` contains exact final source, test, configuration and documentation copies;
`preimages/` contains the two changed files' exact prior bytes. `fixture/` is
explicitly offline evidence with injected clocks, not an executed live watch.

Run only the hash/schema verifier:

```sh
python -I -B /path/to/manual-watch-independent-review/verify_packet.py
```

It checks the closed inventory, ordinary paths, hashes and strict saved review
metadata. It never imports or runs the saved helper, watch, tests, fixtures,
reproduction or any network transport. The historical scripts and copied command
examples are audit evidence, not an authorization to execute a watch.
