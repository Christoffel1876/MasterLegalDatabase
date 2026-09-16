---
title: "Additive review of Douglas/Pueblo intake metadata loading"
status: see_typed_final_review
legal_currentness: not_verified
answer_safe: false
---

This packet supplements the unchanged `final-two-source-independent` review. That earlier packet records source/authority/custody checks and a read-only preflight against the original transaction. It is historical; this packet records the subsequently identified metadata reread boundary and the final revision reviewed before intake.

An in-memory `Path.read_bytes` replacement demonstrated the issue without changing any file: the original loader read `PREPARATION.json` three times. The first reads passed its pins, but a changed `official_source_name` returned only by the third read was accepted into the resulting plan. This was a reproduction of a possible concurrent modification, not evidence that any production metadata was actually changed. `REPRODUCER_EXECUTED.txt` records the command body with a historical-use comment; its former import path now contains the revised code. Do not execute it as a current reproduction.

The revised loader captures the independently pinned preparation and manifest once. Every manifest member is checked into a byte buffer; preparation fields, source-provenance digest and historical control prefixes are derived from those exact buffers. A final source check still rereads the PDF against its fixed hash before writes. The pinned closed metadata therefore carries the previously accepted custody evidence without executing the preparation-supplied verifier again. It does not itself discover or certify official provenance, repeat the visual review, or authenticate current law.

The final named-reviewer decision, code hashes and exact read-only command are in `REVIEW.json` and `FINAL_READ_ONLY_CHECK.json`. The original and revised transaction copies are historical code evidence only; this packet's validator does not import or execute them. The actual transaction and its execution are owned by root and remain separate.

All earlier qualifications remain: one county-issued Douglas schedule contains distinct county/state-legislation captions and two blank fee cells; Pueblo is municipal and has 44 physical application rows plus 43 nested associations; printed date claims are not verified adoption/effectiveness; existing QA receipt fields remain historical. No fee calculation, applicability, currentness, monitoring enrollment or coverage promotion follows.

Portable verification, using Pydantic 2:

```sh
python -B /absolute/path/to/final-two-source-independent-revision/validate_review.py
```

This command validates only the closed packet, hashes and typed review records. It does not run the historical reproducer, apply a transaction, contact sources or assert that current repository files still equal an earlier snapshot. Read-only preflight results are timestamped historical observations, not an enduring live-state claim. Interruption tests are not a power-loss durability guarantee.

Root subsequently identified two descriptive `original_filename` values that did not match the actual incoming basename. Both incoming preserved files are named `original.pdf`. The final proposal must retain that incoming name, while the publisher response filename, official title and archive path remain distinct metadata. A before-write basename invariant and a regression test are part of the final review. The earlier `READ_ONLY_CHECK.json` and its stdout describe the intermediate checked-buffer revision before this correction; only `FINAL_READ_ONLY_CHECK.json` is the final preparation check. Neither read-only result is a claim that intake occurred.
