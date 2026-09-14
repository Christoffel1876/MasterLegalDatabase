---
title: Independent packaging scanner audit
reviewer: Plato
status: proposed_revision_validated_not_installed
scope: Local packaging identities only
---

The original scanner can restamp an altered wrapper payload after checking the wrapper's expected hash. The isolated reproduction changes only a synthetic source between its first check and final scan assembly. Its final record retains the basis `closed wrapper fixture-approved` while publishing a different hash. This demonstrates a scanner defect; it does not establish that any repository payload was corrupted.

The separately proposed scanner retains each declared hash and size from wrapper, prior packaging, raw-manifest, and installation evidence through final assembly. Conflicting pins, changed final bytes, unbound inventory additions, and unbound installation metadata fail. The original scanner and before-final-install scan are preserved unchanged. No root scanner, canonical source, Git index, or maintained file was modified by this audit.

The original recorded scan contains 17 wrappers, 2,441 payloads, 85 ignored/untracked files, and exactly six appended originals. The proposed scanner's actual local run contains 19 wrappers, 2,511 payloads, 192,561,764 bytes, 87 ignored/untracked files, and the same six selected originals. Its additional scope includes the final installed inventory and the publisher-test style receipt. These counts are snapshots, not a completeness or publication assertion.

The case-insensitive macOS glob reaches the tracked lowercase `inventory.json` through the uppercase pattern. The existing case-folded tracked-file exclusion handles that case; the actual lowercase file is separately selected by its maintained-change path. Both repository-relative and wrapper-relative manifest members are resolved, the exact two user exclusions are absent, and both NUL lists agree with the recorded selections.

Inventory snapshot files now have independent anchors: the frozen earlier `UNTRACKED_ORDINARY.json` inventory, the final installation receipt and its schema, and the final preimage receipt/schema. Unlisted new inventory files fail rather than becoming approved simply because Git calls them untracked. The exact six original IDs, paths, hashes, and sizes are enumerated; the historical raw prefix remains byte-equal.

The proposed optional CI-installation branch requires `research/local_review/manual-watch-ci-integration-2026-09-13/INSTALLATION.json` and `INSTALLATION.schema.json` to be members of a validated closed wrapper. It validates that schema and carries every target pin forward. No actual CI installation receipt existed in the successful scan, so this branch is not an end-to-end acceptance of that future receipt. Root must bind the final reviewed receipt/schema hashes and actual installed-file identities before using that branch. A receipt that has only an allowed name is insufficient.

Nine focused tests passed against the proposed scanner's actual admission, metadata-consumption and final-assembly functions: late drift, conflicting pins, agreeing pins, wrong admission hash, changed metadata, unbound installation, unbound inventory, and exclusions/case aliases. The synthetic reproduction and tests perform no source requests or Git operations. A full maintained test suite was not run for this handoff-only scanner proposal.

Run the closed audit verifier from any directory:

```sh
PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-status-venv/bin/python -B '/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-13/plato-packaging-scan-audit/verify_audit.py'
```

To rerun the isolated original exploit or focused tests, use the adjacent `replay_original_repro.py` or `test_expected_identities.py`; disable Python bytecode and pytest cache writes. The proposed real scanner deliberately retains this session's repository, HEAD and evidence anchors and writes only to this audit's `proposed-runs/<new-name>` directory. It is not a portable general-purpose packager.

The revision is a bounded proposal, not staging authorization. Wrapper inventories authenticate bytes, not the truth of all historical assertions. Maintained changes without a separate installed receipt retain an explicitly observed first-admission snapshot, not a new content approval. Root must run a fresh final scan after its remaining installations and recheck exact recorded bytes before staging. The scanner is not a general hostile-filesystem or authorization engine: ancestor symlink defenses and explicit wrapper-name allowlisting were not comprehensively expanded. No claim of independent model-family review is made.
