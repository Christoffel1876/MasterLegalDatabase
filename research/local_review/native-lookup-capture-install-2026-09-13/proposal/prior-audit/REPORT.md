---
title: Existing native lookup adapters — verified-byte consumption audit
status: confirmed_temporal_evidence_binding_failures
legal_currentness: not_verified
scope: nine offline reproductions across seven existing source adapters
---

All seven earlier source adapters returned injected evidence in bounded temporary-file mutation probes while still reporting `evidence_verified=true`. The production sources were not altered. The implementation inspected and executed was the exact installed nine-source script with SHA256 `4b3f084eb9bf9a20f3e5c7b7c0c25a3b1bbbfe0de05caff9b626100808dbad6f`; the newly corrected Douglas/Pueblo branches were outside these probes.

Each completed case ran the real existing package checker and pinned offline verifier. The harness changed only isolated copied files at an explicitly chosen read boundary, retained the returned result in `PROBES.json`, and restored the copied bytes. Some probes use an ABA sequence: change the file for the unchecked read, then restore it before the next successful file check. This demonstrates a binding defect; it is not evidence of an actual attack or corrupted historical source in the repository.

| Source family | Reproduced outcome | Relevant inspected implementation |
|---|---|---|
| Grand Junction fire fees | Changed fee span text returned; a separate late event change returned an invented 2099 retrieval timestamp | `_check_package`, `_load_verified`, `lookup` |
| Greeley building fees | Injected source-review observation returned after a temporary unchecked QA read | `_load_greeley_verified`, `_lookup_greeley` |
| Weld environmental-health fees | A different existing fee span was assigned to the first row; injected review observation returned | `_load_weld_verified`, `_lookup_weld` |
| Greeley impact-fee memo | Injected displayed fee text returned with unchanged contributing native spans | `_load_grid_verified`, `_lookup_grid` |
| Greeley proposed PIF notice | Injected displayed fee text returned with unchanged native spans | `_load_grid_verified`, `_lookup_grid` |
| Colorado Springs construction fees | First fee changed from `$258.00` to `$000.00` through a late QA/native swap; still verified | `_load_springs_verified`, `_lookup_springs` |
| El Paso English EHS | Injected fee text returned with the original native fee span; a separate case returned an unverified traversing image path | `_load_ehs_verified`, `_lookup_ehs` |

The fee/display distinctions in the strict models are intentional: reviewed display wording may differ from linear native text. Those models cannot substitute for binding the exact accepted review bytes. Likewise, a source hash in output cannot authenticate a separately reread event, acceptance, native page or image-path claim.

The minimum correction is to capture every consumed source/review/native/context/custody buffer under its authoritative pinned digest, validate the captured references, and parse/build results exclusively from those buffers. Returned asset digests and sizes must describe the consumed captured bytes. Preserve both existing package verification and complete context; a final file hash check alone does not defeat an ABA swap. Keep all nine normal-source outputs and public API contracts unchanged, including current-law refusals.

The audit's first runner completed the El Paso and Springs reproductions but stopped when a copied Weld file retained a read-only mode. That attempt's script and log remain under `initial-read-only-fixture-attempt/`. The final runner enables writing only on the specifically mutated temporary files; it does not change production modes or evidence. Both attempts and all final outcomes are retained rather than retroactively relabeled.

This is a bounded audit of nine selected boundaries, not proof that every possible race, verifier-import race or custody mutation has been enumerated. The current findings warrant a family-wide captured-buffer repair before expanding this adapter family further. No source-currentness, legal-effect, full repository test or production repair result is claimed here.

Read-only audit verification: `PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-status-venv/bin/python -B verify_audit.py` from this directory. `probe_family.py` is a reproduction harness that makes temporary copies; it is not the read-only validator.
