---
title: Chaffee electric ordinance — Plato source-fidelity audit
date: 2026-09-13
reviewer: Plato
status: accepted_scoped_revision_pending_root_integration
legal_currentness: not_verified
---

The revised seven-page source review is suitable for scoped research evidence. Plato
directly inspected all seven full 300 dpi images, nine supplied crops and one additional
printed-name crop, then compared the complete transcript and marked tables. This was
candidate-aware review within the same model family as Atlas, not a blind review or an
independent model-family result. No external bot report was consulted.

Two findings were resolved in Atlas's separate `revision/` copy. The initial paragraph
parser omitted the final seal annotation from its structured blocks even though the text
was present in the transcript. The revised 98-block record includes it. A confidently
transcribed printed surname character is obscured by blue ink; the revised transcript
preserves `Gina Lu[editorial: obscured character, c/f uncertain]rezi, Chair`. No alternate
name was researched and no signature identity was certified.

`draft/` preserves all 70 initially received files. `revision/` preserves all 77 revised
files, including Atlas's five preimages and revision receipt. Neither copied tree was
edited. `AUDIT.json` binds the selected SOURCE_QA, schema, transcript and exact original
PDF, and adds byte-bound table cells. The initial parser failure is retained in
`ORIGINAL_GAP_PROOF.json`; it remains reproducible. `INSPECTION.json` records actual
completed image inspections retrospectively without inventing individual display times.

The accepted revision preserves 22 numbered amendment instructions, 98 paragraph/table/
annotation blocks, 85 visible markup spans, seven logical tables in eight physical
fragments, 12 data rows and six cross-page continuations. All 14,190 machine OCR bytes
remain unchanged. All seven native extractions remain empty; the reviewed transcript is
not native PDF text. Table headings, merged cells, superscripts and source exceptions
remain associated. Counts describe this evidence structure, not operative legal rules.

The R/I table's undefined local `b` footnote remains unresolved. Repeated replacement
numerals retain both strike and underline. Commercial and residential water-heater
exceptions differ and are not merged. The source's duplicate `2.2`, `and or`, and
R406.4 paragraph/R406.5 caption discrepancy remain literal. Small terminal-punctuation
markup extents and obscured handwriting remain qualified. No effective date is computed
from the 30-day clause. Recorder, introduction, adoption and publication statements are
separate source assertions, not verified currentness or execution authenticity.

The supplied HTTP evidence is a **selected subset** of an upstream acquisition packet.
Its retained manifest is not a claim that all upstream members are present here. The
original nonpublic header bytes were not retained upstream; the stated deletion/filtering
procedure cannot be independently replayed from this subset. Observed GET completion
is distinct from any later repository intake. Historical pre-intake/null fields remain
unchanged. No public request, OCR rerun, canonical intake or production edit occurred.

From this folder, with Python packages Pydantic 2, jsonschema and PyMuPDF installed:

```sh
PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-status-venv/bin/python -B verify_audit.py
PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-status-venv/bin/python -B verify_audit.py --rerender
PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-status-venv/bin/python -B -m pytest -q -p no:cacheprovider test_audit.py
```

The default verifier is offline and read-only. It captures checked buffers, validates
schemas, closed inventory, copy identities, every paragraph and markup span, exact table
cells, crop pixel recipes, source/OCR bindings and supplied acquisition references.
Optional rerendering uses temporary files and the recorded Poppler 26.05.0 wrapper; use
`--renderer /absolute/path/to/the/same/wrapper` after relocation. All seven rerendered PNGs
matched their retained bytes. The 23 tests cover omitted text/strikes, altered exception
qualifiers and cells, swapped table/cross-page associations, false native text, date
promotion, symlink paths and captured-buffer behavior. `CHECKS.json` binds actual results.

These mechanical checks support reproducibility; they do not replace image inspection
or establish current law. The closed `FINAL_MANIFEST.json` excludes only itself and its
schema. Root integration and any later acceptance are separate actions.
