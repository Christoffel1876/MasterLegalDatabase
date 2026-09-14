---
title: Proposed next production boundary after independent review
status: proposal_only
legal_currentness: not_verified
---

# Narrow next step

First independently review this frozen prototype and, only after explicit root approval,
run one finite live cycle against the exact two reviewed destinations. Preserve its actual
result even if access is denied or the bytes differ. Offline fixture success is not a live
check and neither is a recurring monitoring history.

If that boundary is accepted, the proposed production change is limited to:

1. A new `geode/pipeline/manual_source_watch.py` CLI and `tests/test_manual_source_watch.py`.
   Move the reviewed adapter and necessary verified-TLS custody code into maintained,
   tested modules. Do not import executable code from a research packet at runtime.
   Preserve all existing Register, CCR, county and research-query defaults.
2. A separate, strict `config/manual_source_watch.json` selecting only these two source IDs.
   Bind their actual canonical originals/intake receipts, official URLs, issuer, old byte
   hashes and custody references. Use an explicit per-invocation elapsed-time/request budget;
   replacing the current session cutoff requires a reviewed configuration, not date guessing.
3. Keep each invocation's outputs under a separate runtime directory, with immutable bodies,
   failed responses, public-header records, per-source classifications and one closed report.
   The CLI returns complete/stopped status, source-only unknown-currentness labels and
   review-needed byte changes. No raw-manifest append, baseline promotion, OCR replacement,
   email, pull request or normal-query integration occurs automatically.
4. Add a read-only readiness report distinguishing preserved manual originals, explicitly
   selected sources, live checks attempted/completed and recurring deployment. Two configured
   sources do not change the existing three scheduled collectors or establish daily operation.
   Root reports canonical intake has since reached 61 raw / 62 ledger rows; this prototype's
   earlier baseline records remain historical. Recompute production counts from validated
   local inputs instead of hardcoding that checkpoint.
5. Independently verify focused failure cases and the real finite run, then perform the normal
   full regression suite. Scheduler/workflow installation and any publication remain a separate
   decision. New-URL discovery, wider municipal coverage and baseline acceptance are outside
   this two-source integration.

The main limitation is deliberate: the fixed old URLs can remain unchanged while a publisher
posts a newer schedule under a different URL. A future catalog/link watcher needs its own
bounded selection and review contract; it must not be implied by this prototype's success.
