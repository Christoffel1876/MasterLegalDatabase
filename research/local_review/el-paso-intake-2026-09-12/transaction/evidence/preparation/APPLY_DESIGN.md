---
title: Unexecuted exact-prefix intake design
status: design_only_no_apply_command
production_mutations: 0
legal_currentness: not_verified
---

# Review gate

Accept or revise the 13 proposed county records by exact ID, SHA-256, issuer and document role. Keep the school-district sheet and CGS guide outside this county transaction. Preserve the Board of Health issuer and separate bilingual artifacts. Do not clear the upstream cap violation, two absent earlier bodies, unverified acquisition claims or LDC referral gap.

# Preflight at authorized execution

1. Run the portable verifier and current-repository preflight against the accepted frozen package. Recompute the complete manual-stream identity/digest checks and ordinary raw-size screen. Reject changed preimages, collisions, unsafe paths or unaccounted pending transactions before writing anything.
2. Record a new actual UTC repository receipt time. Derive unique `MSI-...` intake IDs and write-once raw destinations under `_RAW_ARCHIVE/manual_intake/08_County_Authorities/<record_id>/`. Keep the proposed source IDs distinct from all inherited registry aliases. Do not use this preparation's timestamp as the later receipt time.
3. Construct all 13 final `ManualSourceIntakeRecord` objects before any write. Use `received_review_package`; preserve actual source-request and final-URL claims, event IDs, issuer qualifications, legal-currentness limits and exact PDF hashes. Validate strict typed records and the existing schema. The final status may be `archived_pending_pipeline`, never “current” or “answer safe.”
4. Preserve exact preimages of the raw manifest, manual ledger and report under a named snapshot. Bind old and proposed new hashes and byte counts in a typed transaction receipt. Also preserve the old report's missing ledger-only history.

# Exact-prefix transaction

Write each new PDF once with exclusive creation, checking the source hash immediately before and the destination hash after the write. Do not replace existing raw files. Prepare one UTF-8 JSONL suffix containing the 13 newly validated records. The new raw manifest must satisfy exact byte equality `after == before + new_suffix` and preserve every old line byte, order and final newline. Use an atomic temporary-file replacement only after all source destinations and record values are known and checked.

The generic `_append_jsonl_raw` implementation reserializes prior records; **do not call it for this transaction**. Existing ordinary manual-intake CLI also misstates acquisition method for a received review package. Follow the established explicit-record custody transaction instead.

Append the missing exact validated raw-manifest records into the control ledger with the existing reconciliation workflow only after reviewing its current implementation and preserving its preimage. Preserve the original ledger prefix exactly, retain the ledger-only historical record, and update the derived report without legal promotion. An interrupted transaction must be diagnosed from its recorded preimages, raw destinations and suffix; rerun must not invent a second receipt or duplicate sources.

# Post-transaction checks, not yet run

Verify all 13 destination hashes/sizes/PDF page counts, both exact-prefix equations, record schema/identity joins, and a no-change reconciliation replay. If the baseline remains 46 raw / 47 ledger and all 13 are new, expected counts become 59 raw / 60 ledger; these are **conditional projected counts**, not this preparation's results. Full corpus validation remains required after actual intake, with inherited failures disclosed separately. No source registry, canonical layer index, coverage ledger, semantic review queue, normal retrieval or currentness record is part of this transaction.

The eventual receipt must record actual start/end times, validated source and record hashes, all written paths, snapshot hashes, exact before/after counts and validation outputs. This document does not claim that any of these apply or post-transaction steps occurred.
