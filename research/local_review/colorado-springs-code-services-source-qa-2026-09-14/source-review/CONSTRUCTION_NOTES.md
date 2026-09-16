---
status: historical_construction_notes
reviewer: Plato
---
# Preserved construction attempts

These notes summarize tool outputs observed during preparation; they are not contemporaneous raw execution logs.

1. The first structural derivation stopped with `AssertionError: (6, 3)`: the bold page-6 SCHOOL INSPECTIONS label and its normal-font fee had slightly different top coordinates. The derivation now uses their centerline separation (under three PDF points). The initial source is `preimages/build_review.initial.py`.
2. The first unsealed validator stopped in `captured_inputs` on `assert a.path not in buffers`. The upstream manifest already listed its schema, and the preparation script had appended that schema twice. The predecessor QA/script is under `preimages/before_asset_dedup_*`. The final asset list is unique and checked against the exact upstream manifest.
3. The initial pixel crop called `p2-m-threshold` landed on neighboring R/S entries. It was preserved unchanged and is explicitly excluded as proof for the M threshold. The threshold finding comes from the directly inspected complete page. The initial bulk crop captured HP3/4/5 and the HP9 heading; a subsequent complete bulk crop shows its intended ranges.
4. A portable exact subset replaced the initial external-packet dependency before freeze. The initial proposed QA and builders are preserved under `preimages/before_portable_*`; no original packet or canonical source was changed.
5. Long Python lines were wrapped with an AST-equality assertion. Those preimages are `preimages/before_style_*`. No QA or source wording changed during the style pass.

The historical preimages are not authoritative final QA records. Final validation applies to the top-level `SOURCE_QA.json`, current models/verifier, and the exact `inputs/` subset. All predecessor files remain byte-bound by the final closed manifest.
