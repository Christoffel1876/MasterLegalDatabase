---
title: EB-PDF-006 validation scope
checked: 2026-09-10
status: scoped_checks_passed_full_corpus_blocked
legal_currentness: not_verified
---

# Validation

The strict Pydantic table model, exported JSON Schema, all referenced artifact
hashes, exact native-text replay, and both manual-intake manifests passed.
The table contains 36 ordered fee rows and nine context blocks. Each page was
checked directly against its image, then independently compared with the final
records. The unchanged reports retain the reviewer's caption-mediated method
and stated limitations.

The required `python -m geode.validate --layer all` check was run and returned
two existing errors. The county `_index.jsonl` is still a Git LFS pointer rather
than the referenced data. The local-review summary check encounters the same
problem when reading `LOCAL_REVIEW_QUEUE.jsonl`; the summary JSON itself is
readable. These files were not changed in this intake. No full-corpus validation
success is claimed, and these errors do not establish that this table is current
law or ready for production retrieval.

No production code changed. The table remains a source-bound research artifact
and the unchanged PDF remains `archived_pending_pipeline`.
