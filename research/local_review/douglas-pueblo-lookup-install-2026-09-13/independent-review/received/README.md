---
title: Douglas County and City of Pueblo lookup — captured-evidence revision
status: prepared_pending_independent_acceptance_and_root_installation
legal_currentness: not_verified
---

This separate revision fixes a confirmed integrity defect in the earlier sealed proposal. A temporary file change after its second package check could previously replace reviewed display text while the result still said `evidence_verified=true`. The predecessor remains unchanged at `../douglas-pueblo-lookups/`; its copied manifest and historical test receipt under `predecessor/` describe that earlier version and are not acceptance of its runtime behavior.

The revised two-source adapter captures and checks exact bytes for the complete closed review package and root acceptance before running the isolated retained verifier. A second capture must match the first. All subsequent source, native-text, context, annotation, image and receipt references come from captured buffers. Fixed intake receipts, intent, exact selected canonical lines, provenance and HTTP events are individually captured and hash-checked before parsing. Current canonical JSONL is still streamed, and the selected exact line must match the frozen transaction; original PDF bytes are separately captured and checked. Later reads cannot inject altered display text or change a returned asset digest. This does not promise that a file will remain unchanged after the command returns: output paths identify the preserved bytes by their reported hashes.

Douglas retains all 44 five-column rows, seven contexts and two null fee cells. County issuer and state-caption rows remain distinct. Pueblo is the **City of Pueblo**, with 44 physical rows and 43 nested associations (15 paired subcategories and 28 fee bullets), four page contexts and all six source-review annotations. Every verified result, including no matches, keeps full context and qualifications. No fee arithmetic, adoption determination, current-law output, raw-source change or monitor enrollment is added.

The installation inputs remain the proposed script, new tests, documentation and seven-source fixtures. The fixtures are complete frozen JSON/Markdown outputs, with only the repository absolute prefix normalized to `__REPOSITORY__`. All 69 prior class/function declarations except the two dispatch functions remain AST-identical. `examples/` contains unchanged examples copied from the predecessor; regression tests replay and compare actual results against exact source evidence. They are not fresh public acquisitions.

Thirteen added regression cases exercise late review/context/native/image swaps, all five fixed custody inputs, a late acceptance swap plus ABA restoration, a substituted read buffer, and a finite byte cap. The final measured counts and combined branch-inclusive coverage are recorded in `VERIFICATION.json`. The focused runner measures the proposed module without installation; its temporary `__file__` adjustment models the installed default root for existing in-process CLI tests, while the new subprocess test runs the actual proposed script with explicit `--root`.

Root may install these exact files only after independent review:

- `proposed/research_source_lookup.py` → `scripts/research_source_lookup.py`
- `proposed/test_douglas_pueblo_native_lookup.py` → `tests/test_douglas_pueblo_native_lookup.py`
- `proposed/RESEARCH_SOURCE_LOOKUP.md` → `docs/RESEARCH_SOURCE_LOOKUP.md`
- `fixtures/seven-native-sources/` → `tests/fixtures/douglas_pueblo_native_lookup/seven-native-sources/`

Read-only packet verification uses the project Python environment:

```sh
PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-status-venv/bin/python -B \
  '/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-12/extended-run/douglas-pueblo-lookups-revision-1/verify_handoff.py'
```

No production files, source evidence, original sealed handoff, public endpoint or Git state was changed by this preparation. Full-suite execution, installation and independent acceptance are separate root decisions. The correction applies to these two new adapters; it does not claim a new concurrency audit of the unchanged seven earlier adapters.
