---
source_id: el-paso-boh-bylaws-spanish-sd011
source_sha256: 1b8367a5710b5159ea479ad588ee5dee9850e1e9451b0115d2770a2d4aae6c7f
authority_id: CO-COUNTY-EL_PASO
status: initial_direct_source_qa_pending_root_acceptance
legal_currentness: not_verified
answer_safe: false
---

# Spanish bylaws: initial direct source review

Ptolemy directly read all six complete source pages, then compared the unchanged machine-native
candidate. All six pages had earlier preparation exposure; this is **preparation/candidate-aware
direct-image review**, not a blinded review or Ebenezer's caption-mediated procedure. No external
Ebenezer report, prior source correction or English-version text was consulted. No translation
equivalence was assessed.

The review preserves **13,558 native UTF-8 bytes, 180 extracted lines (178 nonwhitespace), and
51 context segments**. Every byte, including extraction-only whitespace, belongs to exactly one
segment. All ten numbered section headings, cover wording, full paragraphs, conditions, negations,
citations and page continuations remain linked to exact page and candidate offsets. The whole
candidate remains unchanged at14,236 bytes including its explicit packaging markers.

Nine dense PDF detail crops and six exact-pixel crops of the original full-page PNG footers were
also individually inspected. All six full PNGs were displayed at1376×1780 from2550×3300 originals;
detail crops were separately displayed with their resize notices. This is a record of actual visual
judgment, not something that the byte validator can certify automatically.

The candidate wording matches the visible source within this complete six-page review. The19
observations in `SOURCE_QA.json` qualify **source-owned wording and layout**, rather than claim19
extraction errors. The source retains unusual citation spacing (`11-10.5-10 1`, `25-1-5 11`),
repeated words, an I-like citation glyph, grammar anomalies and a repeated amendment-notice sentence.
None is silently rewritten. Exact Unicode and spaces remain native-byte evidence; visually similar
glyphs do not independently prove a codepoint. Underlines are heading appearance, not inferred deletion.

Cross-page context is explicit: the president paragraph continues2→3, attendance/removal3→4, and
amendments5→6. The recurring September1 budget deadline is not a document adoption/effective date.
No date/footer number was observed on pages2–6 after full-page and exact-pixel footer inspection.
Page1 has the printed organization footer. No execution signature or handwritten entry was observed.
Source issue/adoption/effective dates and independently verified original HTTP time remain null.

`inputs/` preserves the selected original, all six full page images, each native file, unchanged
candidate, extraction/render records, selected canonical custody row, and historical packet proofs.
It does **not** copy the other source's payloads or claim its review. Historical paths and custody
notes remain historical; for example, the inherited custody note describes proposal timing, while
the canonical row records actual repository receipt2026-09-12T22:59:48.795762Z. Reported original
download timing remains unverified. No raw, index, ledger or other canonical file was written.

Run the portable read-only validator from any directory:

```sh
/private/tmp/geode-status-venv/bin/python -B /absolute/path/to/ptolemy-eb026-source-qa/verify_review.py
```

It captures and hashes each closed member once, validates the strict exported schema, verifies
the fixed source/candidate and selected packet custody, replays native extraction and PDF line
geometry, checks all paragraph/continuation/observation bindings, and regenerates all15 detail crops.
Add `--rerender` for six full-page Poppler byte comparisons; this requires the exact recorded local
Poppler binary. PyMuPDF1.28.2 was used and tested; different rendering/extraction implementations
may fail exact replay. The portable default opens no historical outside-package evidence path.

`build_review.py` is preserved as historical construction code; **do not rerun it**. The initial
pre-freeze verifier field-access failure is retained in `preparation-history/`; canonical records use
`record_id`/`archive_path`. It was a verifier-development error, not a source-text discrepancy.
The focused tests use temporary copies and do not alter source evidence. Final validation records
state only actual completed checks. Any later external-report reconciliation must be additive.
