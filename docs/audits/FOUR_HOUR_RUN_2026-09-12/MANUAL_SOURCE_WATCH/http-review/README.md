---
title: Maintained manual-watch HTTP independent review
status: frozen_helper_and_focused_tests
review_scope: offline_transport_and_adapter_findings
---

The helper now enforces total parser-operation deadlines across repeated header or trailer reads, retaining an independent socket descriptor so Connection: close cannot disable interruption. Timers are cancelled and joined, descriptors are released, partial source bytes stay preserved, and late completion is classified as timeout.

The combined helper and deadline suite passed 94 tests with 94.9025487% branch-inclusive coverage. Root's rejection of conflicting Transfer-Encoding and Content-Length is retained. The exact copied helper, tests, code preimages, local socket-pair reproductions, coverage and test output are bound by the receipt and manifest.

The adapter findings were delivered separately to its owner; this receipt does not certify later adapter edits. No public requests, canonical source changes, legal-currentness claims, or full-suite run were made. Run `python validate_evidence.py` here to verify these closed evidence bytes; this does not rerun tests or open any source URL.
