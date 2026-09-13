---
status: installed_focused_tests_passed
public_requests: 0
runtime_config_changes: 0
---
# Installed watch test compatibility repair

The installed repository treats tests as a package. Two copied prototype tests imported their sibling as a top-level module, causing collection to fail before those tests could run. Their imports now use `tests.test_manual_source_watch_batches`. The shared fixture now derives its source root directly from its installed repository location; the earlier handoff fallback and `PROPOSED` alias were removed. No assertions changed.

All three original files were preserved both here and in exact repository snapshots before atomic replacement. The original proposal, revised proposal and independent review packages remain unchanged. The installation receipt still truthfully describes the initial exact copy; RECEIPT.json supplies the later three test-file identities.

The actual installed command passed **205 tests** with **93.8184% combined branch-inclusive coverage** of the batch adapter and versioned HTTP helper. The earlier two collection errors and actual corrected command are preserved separately. Runtime code, configuration and the original Springs replay inputs were rehashed unchanged. No public HTTP, canonical data mutation or full-suite run occurred.

Portable receipt verification:

```bash
python -B verify_repair.py
```

Optionally verify the current installed tests, snapshots and unchanged runtime/configuration files as well:

```bash
python -B verify_repair.py --root /absolute/path/to/MasterLegalDatabase
```

The portable package validates its retained evidence. Its excluded predecessor payloads require their original folders to recompute; their observed successful rechecks are explicitly dated in the receipt.
