---
title: Additional fixed manual source watch batches
status: prepared_for_review_not_installed_or_executed
prepared_date: 2026-09-13
legal_currentness: not_verified
---
# Additional fixed manual source watch batches

This proposed command compares six preserved PDFs at their exact approved URLs, two at a time.
It does not discover new editions elsewhere, update baselines, install a schedule, publish changes,
or determine whether law is current. Preparation performed no public requests.

The existing [Springs watch](MANUAL_SOURCE_WATCH.md), its configuration, and its saved-run replay
remain unchanged. This additional command uses ordinary maintained modules
`manual_source_watch_batches.py` and `manual_watch_http_v2.py`. Version 2 retains the earlier
transport behavior and adds an explicit five-host policy for these six sources. The old helper
remains available because historical runs bind its exact implementation hash.

## Select one reviewed pair

| Batch | Sources | Preserved baseline |
|---|---|---|
| `county-fees-v1` | `arapahoe-planning-fees-sd002-14`; `weld-ehs-fees-2026-atlas-directed` | 2 + 3 pages; 395,049 bytes |
| `western-fees-v1` | `grand-junction-fire-fees-atlas-directed`; `mesa-building-fees-exhibit-a-atlas-directed` | 2 + 5 pages; 993,264 bytes |
| `greeley-fees-v1` | `greeley-building-fees-sd008-06`; `greeley-development-impact-fee-memo-sd008-07` | 1 + 3 pages; 803,173 bytes |

Each invocation permits at most four HTTP requests and four distinct URLs, including redirects.
It permits at most one redirect per source, on that source's exact hostname, 2,000,000 response-body
bytes per source, 4,000,000 per invocation, 30 seconds per request and 300 seconds per invocation.
There are no automatic retries. Access denials stop the batch. Every attempted request is durably
reserved first. Partial bodies and interrupted reservations consume the bounded budget; they
cannot prove unchanged bytes. Limits may be narrowed in a separately reviewed plan.

After reviewed installation, readiness is read-only:

```bash
python -m geode.pipeline.manual_source_watch_batches --root /path/to/MasterLegalDatabase \
  --batch county-fees-v1
python -m geode.pipeline.manual_source_watch_batches --root /path/to/MasterLegalDatabase \
  --batch western-fees-v1
python -m geode.pipeline.manual_source_watch_batches --root /path/to/MasterLegalDatabase \
  --batch greeley-fees-v1
```

Readiness counts currently preserved originals and separately reports the two selected IDs.
`prior_watch_execution: not_asserted` makes no claim that these newly prepared batches have run.
The default batch is `county-fees-v1`; specify `--batch` to make the operator's choice explicit.

An operator may run one pair only after reviewing that installed selection's exact hash:

```bash
python -m geode.pipeline.manual_source_watch_batches --root /path/to/MasterLegalDatabase \
  --batch county-fees-v1 --execute --run-name county-fees-YYYYMMDDTHHMMSSZ \
  --reviewed-selection-sha256 THE_REVIEWED_CONFIG_SHA256
```

The file for this example is `config/manual_source_watch_county_fees_v1.json`. The other two files
are `manual_source_watch_western_fees_v1.json` and `manual_source_watch_greeley_fees_v1.json`.
No command accepts an arbitrary URL or new source ID. Changing the six-source catalog requires
an explicitly reviewed code/catalog revision; recomputing a local config hash cannot admit a
new source. A repeated run name replays its original pair and dispatch. It cannot be reused for
a different batch or rewritten to accept a different implementation.

```bash
python -m geode.pipeline.manual_source_watch_batches --root /path/to/MasterLegalDatabase \
  --batch county-fees-v1 --verify-run county-fees-YYYYMMDDTHHMMSSZ
```

Runs stay under `.geode_runtime/manual_source_watch_batches/<run-name>`. The exact config and raw
manifest preimage, invocation receipt, each request/body/public-header receipt, report, and closed
inventory are retained. Replay validates them without making a public request. It also enforces the original source
hostname, the selected redirect-hop ceiling and the exact per-request deadline; rehashing a
forged file inventory cannot bypass these policy checks.

## Custody and interpretation limits

Every observation retains its full `source` binding: original authority and layer, intake receipt,
old acquisition method and URL, later HTTP evidence where present, parent-link limits, declared
review scope, source-date claims and unresolved questions. Convenience fields are checked against
that binding. An inconsistent owner, URL, baseline, date, path, or omitted qualification fails
preflight before a request can be reserved.

`baseline_recorded_http_time` must be read with `baseline_http_time_role`. For Arapahoe it is the
receipt's recorded observation time; the request start remains null. For Greeley it is the later
September 12 verified reacquisition, not the original Sherlock transfer or repository receipt.
The earlier Greeley `received_review_package` method and null raw official URL remain unchanged.
The exact two CDN links require their preserved city-page anchors, including byte bounds and
visible-text association; the CDN hostname alone does not establish government ownership.

Arapahoe and Weld's parent-link gaps stay explicit. Grand Junction is a city source; Mesa and
Weld are county sources. An issuer or collector relationship does not merge their jurisdictions.
The Greeley development-impact document is a memorandum, not an independently verified adopting
ordinance. Source titles, upload paths, revision dates, metadata and receipt times are not assigned
legal effect. The catalog retains the recorded table gaps, ambiguous source labels and conditional
fees from each bounded review. Watching bytes does not expand those reviews.

Results distinguish `unchanged`, `changed`, access denial, missing source, invalid response,
transport failure, refusal and not checked. `unchanged` means exact PDF byte equality with the
pinned baseline. `changed` means different complete PDF bytes requiring review. Neither outcome
establishes legal currentness, adoption, repeal or a newly applicable fee. Existing unresolved
source issues remain even when `review_needed` is false because no new byte difference was found.
