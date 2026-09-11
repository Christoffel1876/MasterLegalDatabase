---
title: Local pilot index preservation repair
status: verified_locally
legal_currentness: not_verified
---

# Preserving existing local records during a rebuild

The pilot rebuild previously retained local_rule rows but dropped ordinary rule_unit and
other existing index records. It now merges registered authorities by ID, preserves unrelated
records and fields, and checks all three layers before writing any output. Existing ownership
exclusions still apply; this repair does not transfer a source to another jurisdiction.

An independent review found two orphan-reference cases involving ./ metadata aliases and a
reference to another local layer. Both meta_path and path now resolve against the planned
metadata sets using lexical repository-relative normalization. Duplicate IDs, incompatible
record types, malformed late-layer inputs and missing managed metadata fail before writes.
Each actual write remains atomic with a preimage snapshot; multi-file disk-failure rollback
is outside this change.

Validation: 1,778 tests passed across tests/ and orchestration tests. The minimal CI selection
passed 299 tests; the ownership policy, parent helper and local pilot modules have 100%
combined statement and branch coverage. Whole-repository branch coverage remains 77%.
CHECKPOINT.json binds the final files and preserved test logs. Earlier ownership-enforcement
audits remain historical receipts for their original code versions.

The two exact missing Git LFS payloads still block broad corpus regeneration. The retained
corpus validation log shows the same inherited queue/index failures. No new law, currentness
claim, source ownership transfer or public publication is produced by this repair.
