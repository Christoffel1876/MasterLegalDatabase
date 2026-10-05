---
title: Native-page research for partial CCR agency captures
status: implemented_local_research_only
updated: 2026-09-24
---

# Native-page research for partial agency captures

`geode.pipeline.ccr_agency_text` builds an isolated research package from an exact,
externally pinned v2 agency capture. It performs no requests and does not create a
departmental state, canonical legal text, or publication payload. The complete
original closed capture is embedded unchanged so verification works after relocation.

The adapter first captures and verifies every original manifest/member byte, then
replays the unchanged v2 models and source joins against those captured buffers.
It uses `ccr_source_text.extract_pdf_pages` for exact PyMuPDF `get_text('text',
sort=False)` extraction. Each record joins a physical page to the original hash,
source URL, agency/rule/citation, version/date/designation and historical receipt
claims. Every retained association remains visible, including content aliases, Word
files and explicitly unselected PDFs. It never reads verified files again to derive
text or source identities.

Native text is **machine_extraction_unreviewed**. It can contain struck/deleted text,
concatenate replacements, omit visual markup or be empty on scanned pages. No OCR,
visual-fidelity certification or PDF/Word equivalence is implied. Word remains
`unsupported_word`. A blank extracted page remains a bound empty page; it is not
silently discarded or replaced with invented text.

## Scope and caps

The existing native bridge ceilings remain unchanged: 25 MB per file, 500 MB total
including the manifest, 4,000 files including the manifest, 1,000 document
associations, 20,000 page associations and unique physical pages, and 100 MB unique
native text. The embedded v2 capture must also meet every original v2 cap. Metadata
and source bodies count toward the actual package limits. There is no override.

If a capture cannot fit, use an explicit sorted list of whole PDF SHA256 identities.
All capture originals, source rows and omitted associations remain embedded and
visible. Only the selected PDFs receive native pages. An unknown hash, empty list,
duplicate selector or page-range request is refused. Shared PDF bytes are extracted
once, but every source association and its page joins remain represented. Do not
sum alias page associations as unique physical pages.

## Offline commands

```bash
python -m geode.pipeline.ccr_agency_text build \
  --source /path/to/verified-v2-capture --capture-sha256 EXACT_V2_MANIFEST_SHA256 \
  --output /path/to/new/research-package
python -m geode.pipeline.ccr_agency_text verify \
  --root /path/to/research-package --manifest-sha256 EXACT_NATIVE_MANIFEST_SHA256
python -m geode.pipeline.ccr_agency_text query \
  --root /path/to/research-package --manifest-sha256 EXACT_NATIVE_MANIFEST_SHA256 \
  --mode citation --text '5 CCR 1002-11' --limit 2
```

For explicit whole-PDF selection, repeat `--select-pdf SHA256` in sorted order when
building. `phrase` mode performs a literal case-insensitive native-text match;
`citation` matches the exact source citation case-insensitively. Every hit returns
the complete physical page and its source metadata. Queries are bounded to 500
characters, 50 returned page associations, and 2 MB of returned native text. Total
matching associations and truncation remain explicit.

Every result carries the full extraction-scope counts, the unselected agency IDs
and listing rule identities, unsupported Word/empty-native counts, source cutoff
and recorded observation range. **No match does not establish legal absence** from
unselected PDFs, Word files, scans, unselected rules/agencies or Colorado law.
`answer_safe` and `department_complete` remain false; currentness is unverified.

Construction uses fresh directories, validated schemas before records, atomic member
writes and a final manifest completion marker. Interrupted directories remain
preserved and cannot be resumed or overwritten. Verification checks exact closed
membership, source identities, schemas, metadata and repeated extraction before
searching; it never executes embedded code or depends on old local input paths.
