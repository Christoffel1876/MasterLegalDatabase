---
title: Count-neutral inventory wording clarification
status: prepared_not_installed
legal_currentness: not_verified
---

Only the inherited first limitation changes from “All 61 rows…” to “Every row…”.
The historical inventory `prepared_at` stays unchanged. The separate clarification
receipt records when this wording proposal was prepared.

All 64 complete SourceRows remain typed-equivalent and their serialized JSON array
is byte-identical. All authority and review join arrays are byte-identical. Inventory
changes are only its plan identity and first limitation; README changes only that
limitation line. Inventory schema is unchanged. The proposed visual changes only the
`data-inventory-sha256` attribute; all display text, metadata, CSS and JavaScript remain
byte-identical. Metadata QA checks all 64 IDs, authority IDs and review kinds. Previous
four-viewport UI QA remains historical; no new browser run is claimed or needed for
this nonvisual attribute-only change.

Run `python -B verify.py` from any directory for portable read-only verification.

Root may install only after the current full suite finishes: preserve current plan,
inventory, schema, README and visual, then copy the four proposed inventory companions
and proposed visual to their existing paths. No module, test, raw, ledger or QA file is
part of this replacement. Run the unchanged maintained inventory `--check` afterward.
The preimages, input pins and prepared proposal stay frozen in this separate handoff.
