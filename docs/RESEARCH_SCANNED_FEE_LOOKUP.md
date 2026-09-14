---
title: El Paso scanned planning-fee research lookup
status: source_only_research
source_id: el-paso-planning-fees-sd011
legal_currentness: not_verified
answer_safe: false
---

# El Paso scanned planning-fee research lookup

This separate command searches the accepted five-page image review of one El Paso County
planning fee schedule. It returns exact reviewed visual wording, fee strings, source project
codes and their complete recorded context. It does not calculate a fee or determine whether a
row applies to a person, project or date. The normal retrieval backend remains separate.

```bash
python scripts/research_scanned_fee_lookup.py \
  --root . --source-id el-paso-planning-fees-sd011 \
  --query 'Erosion' --format markdown

python scripts/research_scanned_fee_lookup.py \
  --root . --source-id el-paso-planning-fees-sd011 \
  --list-rows --format json
```

The command needs Python 3.11+, Pydantic 2, jsonschema and PyMuPDF. The preserved
review was tested with PyMuPDF 1.28.2; use that recorded version for reproducible
replay. The verifier checks replayed evidence rather than enforcing a version string.
It makes no network requests and writes no data.
When calling it outside the checkout, use the script's full path and an explicit
repository `--root`.

## Evidence and output contract

The fixed source package is
`research/local_review/el-paso-planning-fees-source-review-2026-09-12/`.
Before returning results, the command verifies the pinned root acceptance, package manifest,
manifest schema, source PDF, SOURCE_QA, reviewed grid and verifier. It checks every inventoried
file and rejects symlink ancestors, escapes, missing files and unlisted content. The one empty
historical `render-cache` directory is permitted; it contains no evidence and may be absent.
The pinned package verifier runs in an isolated, non-optimized Python subprocess with a
90-second timeout and no inherited credentials, then package integrity is checked again.
That verifier checks the five source pages, empty native text, recorded image hashes/crop
pixels, manual transcript byte ranges, row/column/section/footnote associations, three visual
errata and custody. It does not rerun OCR or download anything.

Every JSON response carries strict source-only flags and exact source/review/acceptance hashes.
`mandatory_context` supplies both source headings, the three-column header, its global
footnote 1 and all three General Notes once, for **every** returned row. Each match includes
all three fee-row cells, the exact section heading and all row-specific superscript footnotes.
Context rows retain blank cells too. Markdown renders the complete mandatory context first
and repeats no inferred abbreviated version of a condition.

Each evidence block includes the physical PDF page, full image path/hash, cell pixel rectangle
and the reviewed visual transcript path/hash. Cell offsets are UTF-8 byte offsets in that
**separately authored manual visual transcript**, never PDF-native offsets. All five native
text layers are empty; native offsets remain null. The source grid was checked against images
after a separate, preserved OCR comparison. This tool neither extracts nor treats OCR as truth.

The one clipped label, `P3-ENG-14`, remains visibly flagged and ends at the source-visible
`submittal`; no closing parenthesis or unseen tail is reconstructed. Five blank project-type
cells stay blank. `TBD` stays literal and is never zero. Project letters are preserved without
decoding. Footnote 1 states the $37 technology fee is **included**; this tool adds no charge.
The two waiver/deviation requests, refund exception, Director discretion and expert-review
cost conditions remain in their complete notes. Source spellings `Commerical` and `preformed`
are preserved rather than repaired.

## Searching and limits

Search is a case-insensitive keyword phrase, with Unicode compatibility normalization used
only for matching. Original output strings remain unchanged. Word boundaries prevent numeric
fragments such as `0` or `000` from matching inside `5,000`. A phrase is searched within each
complete cell, its section heading and its row-specific footnotes; repeated matching rows
are all returned in source order. No synonyms, fee calculations or semantic inference occur.

A match only in global notes or titles returns `matched_context_only`, with no fabricated fee
row. An unmatched phrase returns `no_matching_row`; this does not establish that a service is
unregulated, exempt, free or absent elsewhere. `--list-rows` returns all 104 reviewed rows of
this particular snapshot. These are not 104 independently verified current legal requirements.

`--mode current-law` and obvious current-law, applicability or calculation questions return
exit 2 with no rows. This keyword guard is only an additional usability boundary: **all** source
mode responses already refuse legal conclusions and remain `answer_safe=false` and
`legal_currentness=not_verified`. Evidence or argument failures return exit 1; valid research
results, including no match, return exit 0. Neither matching nor this guard interprets legal effect.

The printed `May 1, 2026` date is a source claim, not a verified effective date. Verified adoption
and effective dates remain null. The supplied HTTP acquisition time (`22:01:39Z`) remains a claim,
with independently verified HTTP time null. Actual repository receipt was
`2026-09-12T22:59:48.795762Z`; that is custody, not adoption or legal currency. The original
Sherlock collection exceeded its distinct-target cap and lost two earlier non-PDF bodies.
The preserved review and successful local integrity checks do not repair those acquisition limits.

## Validation

```bash
pytest tests/test_research_scanned_fee_lookup.py -q \
  --cov=research_scanned_fee_lookup --cov-branch --cov-report=term-missing
```

Focused tests include the real pinned package verifier and all 104 exact row/cell comparisons,
missing/tampered source/review/pixel/custody files, unknown sources, path attacks, lost notes,
wrong section/column associations, clipped-label and blank/TBD preservation, context-only and
absent-service queries, date/currentness restrictions, numeric search boundaries, inert Markdown
input, isolated verifier execution and CLI refusal. This is integrity validation of an accepted
source review; it is not a fresh legal review or an independent recertification of every pixel.
