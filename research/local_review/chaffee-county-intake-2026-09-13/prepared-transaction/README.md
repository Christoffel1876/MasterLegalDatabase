---
title: Chaffee County two-source intake preparation
date: 2026-09-13
reviewer: Popper
status: PREPARED_NOT_APPLIED
legal_currentness: not_verified
---

This fixed transaction proposes exactly two pending source records for Chaffee
County, layer `08_County_Authorities`. It has not changed canonical data.

| Source ID | Actual acquired PDF | Bytes | Physical pages | Observed GET completion |
| --- | --- | ---: | ---: | --- |
| `chaffee-cwrc-ordinance-2026-02-atlas-directed` | A001 | 1,146,747 | 14 | 2026-09-13T16:09:37.730305Z |
| `chaffee-electric-ordinance-2026-01-atlas-directed` | A002 | 529,100 | 7 | 2026-09-13T16:09:47.762418Z |

Both records use `manual_official_download` and the exact successful HTTPS Revize
URL. The entire public retrieval packet is retained unchanged at
`inputs/retrieval/`: literal county parent links and first HTML base, earlier
supplied redirect evidence, direct GET reservations/commands, curl writeout,
public headers, response bodies, typed results and its closed manifest. Its A003
fee-link response is a 302 HTML notice. It is retained as evidence and cannot
become one of the two selected PDF records.

Each incoming local file is the exact response-body copy at
`sources/<source-id>/original.pdf`. The final `original_filename` is its actual
basename, `original.pdf`; this does not claim a publisher filename. The supplied
county labels remain explicit, including “2025 BOCC Ordinance 2026-02”. No date
meaning is inferred from labels, filenames, query values or Last-Modified headers.

`PREPARATION.json` contains validated prospective fields and source-specific
provenance. The actual repository `received_at`, intake IDs and archive paths
remain unset until an explicitly approved application freezes one UTC timestamp
in `execution/INTENT.json`. That timestamp cannot precede the observed HTTP
completion. It is not substituted for original acquisition time. All final
records remain `archived_pending_pipeline`.

The maintained URL gate approves only HTTPS `cms2.revize.com` under the decoded
`/revize/chaffeecounty/` tenant path. It does not approve the shared host globally.
`POLICY_REVIEW.json` records the independent diff review and offline probes. The
root decision and code are copied as an explicitly partial policy subset; the
complete original retrieval evidence is retained separately. Strict maintained
request and reconciliation validation runs before canonical writes.

The exact current prefixes are **67 raw-manifest records / 68 ledger records**;
the sole proposed result is **69 / 70**. The existing ledger-only missing original
remains disclosed; 70 ledger rows must not be described as 70 available originals.
`COMPARISON.json` records the complete 48,390-row legacy metadata comparison,
current registry/coverage comparisons, and a size-first scan of 571 present raw
files. No exact selected IDs, digests or requested/county-referral URLs matched.
Absent LFS content and external research copies were outside that raw-file scan.

The transaction checks all selected identities, source bytes, owner/layer, URL,
request evidence and exact current prefixes. It captures the old raw/ledger/report
bytes and derives the expected report solely from that captured state plus these
two records. It never uses generic append or mutating reconciliation. Application
uses an exclusive packet lock, immutable intent and original writes, exact-prefix
replacements and preflight at each boundary. Original canonical bytes are saved
both under `execution/preimages/` and `_SNAPSHOTS/CHAFFEE-<actual-intake-time>/`.
Only recognized monotone partial states resume. Unrelated suffixes, source changes,
wrong paths, conflicting destinations and altered report projections are refused.
The packet lock is not a global lock against unrelated noncooperating writers.

The source bodies were structurally parsed to 21 pages. This intake preparation
performs no visual source review or full-text extraction and does not certify
adoption, signatures, effective dates, translation, legal currentness or rule
promotion. Separate source-QA work is not silently converted into intake status.

The new files were adapted from unchanged copies of today's Gunnison transaction
in `reference-only/`. Historical builders, collectors, results and existing
transactions were not rerun. `preparation-history/` preserves draft code, the
initial missing-fixture-source failure, and the later passing pre-clock-guard
checks. No network, blocked-queue, registry or coverage-ledger mutation is part
of this transaction.

Run only the read-only commands while reviewing, using the intended repository
root explicitly:

```sh
/private/tmp/geode-status-venv/bin/python -B /absolute/path/popper-chaffee-intake-preparation/validate_preparation.py
/private/tmp/geode-status-venv/bin/python -B /absolute/path/popper-chaffee-intake-preparation/transaction.py --dry-run --root /absolute/path/MasterLegalDatabase
```

The portable verifier requires Pydantic 2, jsonschema, PyMuPDF and BeautifulSoup.
It checks the closed preparation, full original retrieval and recorded validation;
it does not import the transaction, invoke a collector or validate a later apply.
The transaction additionally requires the exact reviewed repository runtime pins.

Only Atlas may use the separately reviewed application command after acceptance:

```sh
/private/tmp/geode-status-venv/bin/python -B /absolute/path/popper-chaffee-intake-preparation/transaction.py --apply --root /absolute/path/MasterLegalDatabase
/private/tmp/geode-status-venv/bin/python -B /absolute/path/popper-chaffee-intake-preparation/transaction.py --verify --root /absolute/path/MasterLegalDatabase
```

After an interruption, rerun the same `--apply` command against the same packet
and repository. Do not delete an intent or fabricate a new receipt time to recover.
