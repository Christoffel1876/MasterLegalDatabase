# Checkout-name assumption exposed by the full regression run

The local full run of commit `c1dd18aba79764a00cffa524c7c422921e281dc9` completed with 3,198 passing tests and one failure. The failing relative-root test hard-coded `MasterLegalDatabase`, so in the isolated `hour-2026-09-16-review` checkout it inspected the original sibling checkout instead. That sibling contains previously audited untracked research duplicates, which correctly fail the source package’s closed-membership check.

The test now uses `Path(REPO.name)` after changing to `REPO.parent`. It still exercises a relative root, the separate tilde path, and parent-traversal refusal, but targets the checkout actually under test. No lookup or source-validation code was weakened, and no original file was removed or changed. Its prior test file is retained under `preimages/tests/`.

The production captured-byte repair and all inventory/source evidence remain unchanged. The affected lookup test module is rerun locally; GitHub reruns the complete suite on the final commit. The first full-run failure is retained in the session handoff and is not relabeled as a passing run.
