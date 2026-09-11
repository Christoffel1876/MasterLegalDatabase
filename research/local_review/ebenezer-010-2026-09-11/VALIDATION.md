---
title: EB010 scoped validation and reproduction
date: 2026-09-11
status: bounded_evidence_validation
legal_currentness: not_verified
full_corpus_validation: not_run_by_this_bounded_intake
---

# Validation scope

The preparation checks verify the seven-page PDF digest and size against the existing pending manual intake, all seven PNG/native-evidence bindings, the exact candidate offsets, and all seven native streams reproduced with PyMuPDF 1.28.2 (`sort=False`, `flags=195`). The preserved old 12-record raw manifest and exact physical line 8 resolve the packet's historical custody binding even though later unrelated intake appended to the active manifest.

The strict review model reconstructs each original native page from an exhaustive partition of unchanged UTF-8 intervals; it rejects gaps, overlaps, duplicates and changed text. It then verifies each reordered page and the complete source-order candidate, including unchanged packaging. Separate annotations describe visual associations without adding characters to the source text.

The four delivered external files are exact copies. All 23 named hash claims across the receipts resolve to preserved assets. The two dollar-prefix defects are rejected as receipt-summary fee literals while the full report remains unchanged. The copied prior Atlas JSON audits validate against their original schemas. The final inventory covers every package file except its own manifest; the source PDF is separately hash-bound in the raw archive.

Use validate_package.py for a machine-readable result. It performs no network access, raw modification, control-plane update, coverage promotion or semantic promotion. It checks bytes and review structure, not whether the law is current or the source is legally operative. No full-corpus suite or source crawl was performed for this bounded integration.
