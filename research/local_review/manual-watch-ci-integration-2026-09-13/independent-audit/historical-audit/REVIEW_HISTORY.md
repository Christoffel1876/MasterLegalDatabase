---
title: Independent review history and corrected premise
status: intermediate_record_preserved_for_final_audit
public_requests: 0
---

# Review history

The initial expectations were recorded at 2026-09-13T17:11:47.424461Z before the
proposed runner and workflow were inspected. Atlas separately supplied prior
feedback about typed process receipts, schema creation before records, and exact
progress-summary preimages. Those points are not claimed as blind discoveries.

Popper initially read the CLI exit branches and incorrectly inferred that a
completed access-denied report would return exit 0. Ptolemy directed attention to
the producer's `compile_report` and `verify_run` invariants. Popper then read both
pinned adapters and withdrew the inference before running a counterexample.

The actual invariant is: report status is `completed` only when every source
observation is `changed` or `unchanged` **and** `stop_reason` is null; otherwise
status is `stopped`. Thus denied, not-found and invalid-response observations
produce stopped reports and exit 2. The original test fixtures' exit 2 for these
outcomes was consistent with the maintained producer. An impossible
completed-denial report must not be presented as a real producer case.

A narrower valid case remains: all observations can be complete while a non-null
stop reason makes the report stopped. The wrapper should bind subprocess exit
codes to the verified report status, preserve the source observations, and keep
that run incomplete. The final independent tests target this invariant and genuine
verifier disagreement. This refinement changes no source bytes or legal status.

The four exact earlier proposal files are retained in
`received-before-refinement/`; no historical proposal was overwritten by this audit.
