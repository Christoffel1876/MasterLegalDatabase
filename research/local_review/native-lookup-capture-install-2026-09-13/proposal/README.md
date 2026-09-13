---
title: Prepared native-source lookup integrity repair
date: 2026-09-13
status: prepared_pending_independent_root_acceptance
legal_currentness: not_verified
---

# Prepared native-source lookup integrity repair

This is a prepared, uninstalled repair for the seven older native adapters. Douglas and Pueblo already use captured evidence and their implementation remains unchanged. The proposal preserves all nine public source lookup schemas and normal JSON/Markdown outputs. It makes no legal-currentness, applicability, completeness or monitoring claim.

The retained prior audit reproduced nine injected-evidence results across the seven older sources, with real isolated source verifiers. Those failures and the original script are preserved unchanged in `prior-audit/`. All mutations were confined to temporary fixtures; production source evidence was not changed.

The repair captures bounded input buffers, hashes the bytes actually consumed, verifies closed manifest references against pinned original/review/receipt identities, and constructs source wording and asset identities from those buffers. The original source verifiers remain isolated and unchanged. A reported path and digest describe the captured snapshot, not an assurance that its disk file cannot change afterward. No new executable evidence imports or public requests are introduced.

`VERIFICATION.json` records actual runs and their implementation hashes. The initial focused run had two test-harness timing failures; the first combined run had 428 passes and two rejection-message regressions. These attempts remain under `historical/` and in their original logs. The proposal then preserved both existing El Paso diagnostic assertions; the targeted rerun passed both. The final combined result is recorded separately, never substituted for the failed attempts.

The 18 fixtures cover full JSON and Markdown outputs for nine sources. Only the repository absolute prefix is normalized to `__REPOSITORY__`. `BASELINES.json` is the earlier measured comparison receipt and intentionally retains the earlier prepared implementation hash. The new regression tests compare final outputs to those same exact frozen fixtures. Existing result classes and Douglas/Pueblo helpers are additionally compared structurally by the portable validator.

Run the read-only custody verifier from any directory:

```sh
/private/tmp/geode-status-venv/bin/python -B /absolute/path/to/this/package/verify_handoff.py
```

Root may install only after independent acceptance: `proposed/research_source_lookup.py` to `scripts/research_source_lookup.py`; `proposed/test_native_lookup_capture.py` to `tests/test_native_lookup_capture.py`; the 18 files in `fixtures/nine-native-sources/` to `tests/fixtures/native_lookup_capture/nine-native-sources/`; and the proposed documentation to `docs/RESEARCH_SOURCE_LOOKUP.md`. The exact preimage script hash must still match. Existing test assertions are unchanged.

The prepared-only runner uses the surrounding repository's unchanged source evidence and existing tests, so it is not a standalone corpus snapshot. It can be rerun before closure by `python -B run_tests.py --combined`; do not run it against this frozen packet because it writes its coverage file. Installed tests have repository-relative fixture paths and no handoff dependencies. The portable custody verifier itself is read-only and requires only Python, Pydantic and jsonschema.
