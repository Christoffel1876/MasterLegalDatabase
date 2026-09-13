---
title: Independent rerun of revised manual watch replay checks
status: replay_findings_resolved_scoped_review_passed
reviewer: Ptolemy, Atlas team
legal_currentness: not_verified
public_requests: 0
production_writes: 0
---

The two concrete replay findings are resolved in proposal manifest `ef2d664301fa00935100307628ec5ac0317bfd622480dc79c0d92ce44b8b159f`.

- The coherently resealed cross-host follow-up now rejects at the original-source hostname gate.
- The coherently resealed overlong request, with a complete response at 70 seconds under a 30-second limit, now rejects at the exact deadline gate.
- Normal and narrower-limit same-host redirects still complete with both exact baseline PDFs. Final-seal recovery is byte-identical and performs no fetch. Cross-batch run-name reuse rejects without changes.
- The revised closed preparation and all six actual canonical source/custody preflights pass. Original Springs code/config pins still match.

Only temporary fixture histories were changed. The original review and proposal remain frozen; a complete exact copy of this 94-payload revised proposal is under `received/`. The revised helper adds original-host and selected-hop checks; the adapter binds each deadline to the minimum of the run deadline and reservation time plus the configured request limit.

This is scoped resolution of the reproduced issues, not a public transport test, legal-currentness statement or deployment. Root retains installation and live-execution decisions. The author’s full205-case suite and prior Springs saved-run replay were not independently rerun here.

The portable `verify_review.py --root /absolute/review --manifest-sha256 DIGEST` checks saved hashes, closure and schema without executing probes, network requests or historical installation tools.
