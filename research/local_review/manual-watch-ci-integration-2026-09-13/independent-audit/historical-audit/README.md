---
title: Independent prepared manual-source watch CI audit
status: frozen_base_review_no_runtime_blocker
public_requests: 0
canonical_changes: false
---

# Independent CI audit

The frozen runner passed 44 author tests and 20 independent cases. Four actual
readiness subprocesses also passed in a temporary sparse corpus containing the
88 selected input files and the complete 70-row manual manifest. No source GET,
canonical write, scheduling or installation occurred.

The final wrapper preserves valid stopped reports with complete byte comparisons
as incomplete. It keeps denial, missing, invalid-response and unattempted source
states explicit, and refuses genuine report/exit mismatches. The initial reviewer
premise about completed-denial reports was wrong and is withdrawn in
`REVIEW_HISTORY.md`; it is not promoted as an observed producer behavior.

The workflow defaults to readiness, uses read-only repository API permissions,
serial concurrency, bounded source requests and a 40-minute job limit. It attempts
summary/artifact retention after failures; cancellation, runner loss, hard timeout
or service failure can still prevent upload. The source budgets cover 16 events,
16 MB body bytes and 20 minutes of source windows, not all setup and verification.

Local installation does not prove GitHub activation. Ubuntu 24.04/Python 3.11
execution and a separately authorized live pilot remain untested here. Fixed
source URLs do not discover new editions elsewhere, update baselines or certify
current law. No notification service is configured.

`received-preparation/` is the complete 154-payload author preparation. The final
companion schemas are preserved alongside the exact tested runner. Earlier copied
companions and the initial proposal remain separately retained. Root's later
two-file annotation/frontmatter revision is outside this frozen base and requires
an additive receipt. Do not execute historical copied builders or live examples.

Run `python -B validate_audit.py --root /absolute/path/to/this/packet` for read-only
portable closure/schema checks. The verifier does not execute the proposed runner
or contact sources. Independent fixtures can be rerun with pytest against
`test_independent.py`; dependencies are Pydantic 2 and pytest. Actual sparse-corpus
readiness receipts contain their original temporary paths as historical facts.
