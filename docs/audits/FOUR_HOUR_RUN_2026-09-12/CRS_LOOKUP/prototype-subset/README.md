---
title: Bounded 2026 CRS source-passage lookup
prepared: 2026-09-12
status: prepared_research_prototype_not_integrated
research_only: true
legal_currentness: not_verified
---

# Three reviewed section selections

This offline prototype returns the complete reviewed source selection for exactly **CRS-1-1-101, CRS-1-1-102 or CRS-1-1-103** from the preserved 2026 Title 1 PDF. It is prepared for review before selective production integration. No production code, catalog, index, ledger, original or older research package is changed.

The response contains a section heading, complete statutory paragraphs, and separately classified source-history notes, editor's notes, cross-references, annotation heading and case annotation wherever present. It preserves all **six paragraphs and 19 native regions** across the three selections. Section 102(1) includes both its page 4 and page 5 fragments; section 103 includes its page 6 editor's note and complete two-column annotation. Notes are always included with the section; there is no optional filter that silently drops them.

Each fragment carries its physical and printed page, unchanged native file hash, half-open UTF-8 byte offsets, exact text and hash, image hash, visible location and the source review's qualification. Paragraph text concatenates its ordered fragments **without inserting, normalizing or correcting any bytes**. Native line wrapping and spacing remain. The annotation's case commentary is not recast as statutory language or an independently checked holding.

## Use

Run one source-only query:

```bash
PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-status-venv/bin/python -I -B "/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-12/crs-2026-passage-lookup/lookup.py" --section CRS-1-1-102
```

`--section` requires the exact selected ID. `--mode source_only` is the default. Any other mode, including `current_law` or `calculate`, returns a typed `refused_mode` response without passages and exits 2. An unselected ID returns `outside_scope` and exits 2; this describes the prototype boundary, not the existence or absence of law. There is no free-text search, partial paragraph match, formula or interpretation.

The Python API is `lookup(source_packet: Path, section_id: str, *, mode="source_only") -> Result`. An integrity or semantic-verification failure raises `ValueError` and returns no passages. Use this entry point, not the private adapter. JSON output validates as `Result`; `RESULT.schema.json` is its exported schema. The Pydantic model also enforces the exact section/paragraph/note associations that JSON Schema alone cannot express.

By default the handoff uses its `source/` copy. The same lookup has been checked against the repository's intended integration source packet:

```bash
PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-status-venv/bin/python -I -B "/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-12/crs-2026-passage-lookup/lookup.py" --source "/Users/mcoors/Documents/Project Geode/MasterLegalDatabase/research/local_review/crs-2026-title1-source-review-2026-09-12" --section CRS-1-1-103
```

Both packets bind source PDF SHA256 `1c6b021e612929ca8024bebf1022ba45f57aa99712d080c404da8f7f7e90cd1d`, source-review SHA256 `555aefd0cac5b99e74d3bb37937d0f36b1943979202aa3f7d96a4cc55f1109e0`, and source manifest SHA256 `ea43aa1d1d2ae4d28a8833642230d22babb18c615a1604b913b52459d181175d`. The 39 copied handoff source files are unchanged. No additional production copy is needed.

## Evidence boundaries

The official URL is `https://olls.info/crs/crs2026-title-01.pdf`, supported by the retained Office of Legislative Legal Services referral. The direct HTTP receipt records acquisition start **2026-09-12T22:13:16.539063Z** and completion **2026-09-12T22:13:17.603959Z**, HTTP 200, verified TLS and a complete response. These are acquisition measurements, separate from review preparation, the printed 2026 edition, PDF creation/modification metadata and historical dates quoted in source notes. **No legal effective date or current-law status is assigned.** The catalog's session statement is returned explicitly as a source claim.

The accepted review directly inspected physical pages 1–6 with native-text context; it was candidate-aware, not blind. Pages 1–4 contain contextual contents listings; those listings cannot become section hits. The native section 104 tail on page 6 is retained only as source custody and is not admitted. The complete PDF has 1,008 pages; neither that structural count nor preserving its bytes establishes a review of the whole title. Exact character encoding comes from native bytes, not visual Unicode certification. The lookup creates no new legal or visual review.

The prior 2025 metadata prototype remains distinct. Its inherited data and unresolved original-source custody remain unchanged; the new 2026 PDF is not represented as a recovered 2025 original. The copied older metadata is present only because the original frozen verifier checks its mechanical comparison, not because this lookup admits it as answer evidence.

## Verification

Before each admitted response, the helper validates the closed source inventory, all exact hashes and sizes, paths and selected IDs, then runs the pinned original semantic verifier. Its two local code dependencies are checked before execution and compiled from the verified bytes in an isolated child. The child prohibits network, subprocess activity and filesystem writes. Source files are checked again after semantic verification and after adaptation. Symlinks, path escapes, extra files, replaced source bytes, changed native offsets, missing continuations, missing notes and changed role associations are refused. No public request is made.

Replay the portable handoff, including all three saved examples:

```bash
PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-status-venv/bin/python -I -B "/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-12/crs-2026-passage-lookup/verify_handoff.py"
```

The focused tests use local copies or injected failures. They cover continuations, notes, custody/date separation, role swaps, path escapes, changed code/evidence, pre/post checks, current-law refusal, child network/write prohibitions and schema invariants. `VALIDATION.json` binds the exact test log and examples. Running tests does not revisit any public source or establish legal currentness.
