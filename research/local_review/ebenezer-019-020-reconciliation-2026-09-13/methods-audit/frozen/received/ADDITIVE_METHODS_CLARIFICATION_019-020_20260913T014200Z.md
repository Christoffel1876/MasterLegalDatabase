# Additive methods clarification — EB-PDF-019 / EB-PDF-020

issued_utc: 2026-09-13T01:41:00Z (approx; before 01:55 UTC deadline)
author: Ebenezer (Grok Bot)
scope: additive clarification from existing receipts/notes/tool_outputs and known coordination steps only
status: not a renewed blind pass; originals unchanged
legal_currentness: not_verified

## (1) Which worker saw which inputs; activating vs delegated prompts

### Workers (019 and 020, same pattern)

| Role | Identity | What it saw |
|---|---|---|
| Coordinator | Ebenezer in this Grok chat | Atlas activation text (no source-image descriptions per Atlas); SOURCE_ONLY_IDENTITIES / START_HERE / MANIFEST_SHA256.txt; page PNG paths on the Mac packet; after Pass1 freeze, the on-disk `candidate.txt` bytes for hashing/copy; receipt/report delivery |
| Pass 1 executor | Grok Bot executor subagent (`reviewer`/`model` fields on receipts) | Parent Task text prompt + `file_attachments` of the page PNGs; Cursor **Read** caption-mediated outputs; wrote PASS1_frozen / freeze receipt / NOTES / tool_outputs captions |
| Pass 2 executor | Separate Grok Bot executor subagent | Parent Task text prompt including a supplied expected candidate SHA; frozen Pass1 files; page PNGs; released `candidate.txt`; wrote PASS2_REVIEW / COMPLETION_RECEIPT |

Receipt language (`COMPLETION_RECEIPT` prior_exposure.activating_user_message_image_descriptions = present_non_authoritative; PASS1_frozen.md prior-exposure table) refers to **image descriptions present in the delegated Pass1 Task context** when PNGs were attached as `file_attachments`, plus subsequent Cursor Read captions. **Atlas's activation message itself is stated by Atlas to contain no source-image descriptions**; that Atlas statement is accepted. The receipt label "activating user message" is therefore **over-broad / imprecise**: it should be read as "delegated Task / attachment-mediated image descriptions," not as content authored in Atlas's activation chat.

### Prompt byte preservation

- Preserved: PASS1/PASS2 reports, freeze/completion receipts, NOTES, `tool_outputs/*` caption and reinspect files (019), crops + inventories (020).
- **Not preserved in the attempt folder:** the exact parent Task / dispatch prompt bytes for Pass1 or Pass2.
- Agent transcript may log tool calls, but **this clarification does not reconstruct or paste missing prompt bytes**. If Atlas needs exact delegated prompts, they are unavailable as saved attempt artifacts.

Authoritative freeze wording for Pass1 remains the Cursor Read captions under `tool_outputs/` (019) / Read+crops procedure (020), as the frozen reports already state.

## (2) Expected candidate hash source (019) — manifest not opened

From `EB-PDF-019 …/COMPLETION_RECEIPT.json` bindings:

- `full_manifest_opened`: **false**
- `data_manifest_digest_opaque`: `b9e843e7…a112` (from `MANIFEST_SHA256.txt` only)
- `candidate_txt.sha256` = `candidate_txt.expected_sha256` = `2ba00b91a33612e279a0553f5e573af795df27a11329d695ea307ea78ae2dfee` with `sha_match_expected: true`

**Provenance of "expected" (honest reconstruction of coordination, not a new computation):**

1. After Pass1 freeze, the coordinator copied `02-candidate-text/…/candidate.txt` into the workdir and ran `sha256sum` on that file (Mac packet path / box copy).
2. That digests value was placed into the Pass2 Task prompt as `expected SHA`.
3. The Pass2 executor re-hashed the local `candidate.txt` and reported MATCH to that supplied expected value.

**What this is not:** an independent read of the sealed full packet `manifest.json` candidate-identity field. Opaque digest verification does **not** verify manifest contents. `SOURCE_ONLY_IDENTITIES.json` does **not** contain candidate SHAs.

**Equivalent for 020:** same pattern — `COMPLETION_RECEIPT` records candidate SHA `e54c8a00…f67a` with packet_manifest_sha256 as opaque digest; Pass1 freeze receipt lists full_manifest / 02-candidate-text as sealed until after freeze; expected value used at Pass2 was the coordinator-supplied hash of the released candidate file, not a full-manifest identity lookup.

## (3) Why original.pdf was absent locally

Pass1 freeze receipts (019 and 020):

- `original_pdf_present_in_workdir`: false / `local_workdir_presence`: false
- `hash_status` / note: **declared_from_SOURCE_ONLY_IDENTITIES_not_rehashed_locally**
- `opened`: false

Operational cause: only page PNGs + instruction/identity files were copied into `/workspace/geode-019b/` and `/workspace/geode-020/`; `original.pdf` was never copied into those workdirs. Retain **declared-only** PDF identity status; do **not** claim a local PDF rehash.

## (4) Page coverage vs complete independent transcription; packaging markers

### 019 (explicit in PASS1_frozen.md / PASS1_NOTES.md)

- **Page coverage under declared method:** captions obtained for physical pages 1–5; both passes report full expected-page coverage under `caption_mediated_source_first`.
- **Not the same as complete independent verbatim transcription:** Whereas/boilerplate marked `[caption-paraphrase]`; large A–E / "No change" spans and some subsection bodies marked `[unchecked — not quoted by caption]`; exact connector wording partially unchecked.
- Therefore: `both_passes_full_expected_coverage_under_declared_method` means **assisted page representation coverage**, not glyph-complete independent transcription of every recital/preamble/body span.
- Packaging / physical-page markers in the candidate are treated as packaging, not source-transcription errors, and are excluded from critical/minor source-error counts (consistent with START_HERE and Pass2 practice).

### 020 (equivalent disclosure)

- All 3 pages had caption (Pass1) and caption+crop (Pass2) representations; status `completed_pending_atlas_verification` under assisted method only.
- Glyph-level verification remains pending Atlas; Pass1 retained spelling alternatives (Antimony|Atimony, etc.) later resolved in Pass2 errata toward source-supported/candidate-matching forms where crops supported.
- Packaging markers excluded from error counts; fee-amount agreement checks are separate from packaging.
- `visual_verification: pending_atlas_direct_image_review` unchanged.

## Waiting

No new blind pass. No source/packet edits. Waiting for explicit activation of any 021–022 packet. All captions/crops/notes and prior originals retained as previously delivered.

## Addendum — delegated prompt byte survival (existing transcript extraction)

Exact Pass1/Pass2 **delegated Task prompt** bytes were located in the existing Grok agent transcript as `tool_use` / `task` input fields and copied here without modification:

- `019_pass1_interrupted_or_prior_transcript_line_1670.json` SHA-256 `285b5eb2cb55130a76b08abbf492cddc81750710d1b27758e64122b600dd3dc9` (prompt_chars=2291, attachments=5, desc='EB-PDF-019 caption-mediated Pass1')
- `019_pass1_fresh_019b_transcript_line_1734.json` SHA-256 `ac0633ed912447772e6192aa66792bed05dbec0b3e011b60d6fac7c684d6bfc1` (prompt_chars=2973, attachments=5, desc='EB-PDF-019b caption-mediated Pass1')
- `019_pass2_fresh_019b_transcript_line_1764.json` SHA-256 `3cd46ed2bed5d79862c9faa62b2204889630ac9acbadd7c93cde9df026794ff8` (prompt_chars=2197, attachments=5, desc='EB-PDF-019 Pass 2 compare')
- `020_pass1_020_transcript_line_1810.json` SHA-256 `79609775444f44a533d6970368f43e01aa84b7af4ab8b265ee0f78a9f278b9f3` (prompt_chars=2149, attachments=3, desc='EB-PDF-020 caption-mediated Pass1')
- `020_pass2_020_transcript_line_1833.json` SHA-256 `4266557e14adfd7463e5aa7ae9e1af8a254e136a05778bf76246bbdbc54e1948` (prompt_chars=2056, attachments=3, desc='EB-PDF-020 Pass 2 compare')

**Important distinction:** These are coordinator→executor Task prompts, **not** Atlas activation text. Atlas activation contained no source-image descriptions (Atlas statement accepted). Image descriptions seen by executors come from (a) Task `file_attachments` / Cursor attachment captioning in the delegated context and (b) subsequent Cursor Read captions saved under `tool_outputs/`. Receipt phrase `activating_user_message_image_descriptions` is imprecise for Atlas chat activation; it refers to delegated/attachment-mediated descriptions.

No missing prompt bytes were invented. If a prompt is not listed above, it was not found as a Task tool_use input in this transcript.
