---
status: PREPARED_NOT_DISPATCHED
packet_id: ebenezer-025-026-2026-09-13
review_method: caption_mediated_source_first
activate_only_by_atlas: true
no_new_document_at_or_after_utc: 2026-09-13T17:45:00Z
hard_stop_utc: 2026-09-13T18:00:00Z
stop_after: EB-PDF-026
legal_currentness: not_verified
---
# Ebenezer: finite Spanish source-fidelity queue EB025 and EB026

This is a prepared packet, not an activation. Start only when Atlas explicitly activates
this exact packet in your existing Grok conversation and confirms the prior queue is
closed. Do not reopen earlier completed assignments. Check actual UTC before starting
and at each document boundary. Start no document at or after **17:45 UTC on September
13, 2026**; preserve your work and stop by **18:00 UTC on September 13, 2026**. An Atlas
stop instruction, identity failure or unavailable page stops this finite queue sooner.
**No EB-PDF-027 or other follow-on is assigned.**

Packet root:
`/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-13/ebenezer-preparation/`

| Assignment | Source ID | Complete physical pages |
| --- | --- | ---: |
| EB-PDF-025 | el-paso-boh-ehs-fees-spanish-sd011 | 6 |
| EB-PDF-026 | el-paso-boh-bylaws-spanish-sd011 | 6 |

Each original and every full-page image is bound in the neutral
`SOURCE_ONLY_IDENTITIES.json`. `MANIFEST_SHA256.txt` is the opaque identity of the
complete frozen data manifest. All metadata paths are relative to this packet.
Before each document's pass-1 freeze, read **only** these instructions, the neutral
source identity JSON, the opaque manifest digest, and that document's exact original PDF
and complete physical-page PNGs. Do not open the complete manifest, candidate,
custody, verifier, preparation records, earlier analyses, English versions, repository
transcripts, research lookups or review-inventory details before the freeze.
Directory separation is a procedural boundary; it does not technically enforce blindness.

## Scope and method

Review the **Spanish source itself**. Preserve Spanish wording, accents, ñ, punctuation,
capitalization, amounts, literal currency symbols, per-unit bases, decimal or thousands
separators, headings, conditions, exceptions, negations, cross-references, dates and
source anomalies. Do not translate it into an English substitute, consult an English
version, or claim translation equivalence. Your explanatory notes may be in English;
source quotations and proposed faithful wording must retain the original Spanish.
Do not calculate fees, correct arithmetic, select applicable tiers or infer legal effect.

The review method for this queue is **CAPTION-MEDIATED SOURCE-FIRST**. Disclose the actual
image/executor tool, assistance supplier/model if known, exact request and available
response for every page and crop. Retain those outputs when available. A caption or
model-generated description is not direct pixel inspection and may omit or reinterpret
text, share errors with a later candidate, or describe unavailable details. Never call
this work blind visual transcription or direct pixel review. Unknown tool internals,
unavailable page details and confidence remain explicitly unknown. Atlas will directly
check the source images separately before accepting content findings.

Internal execution and image tools are permitted only to read these assigned source
images, hash/crop them or save outputs. Preserve exact tool prompts and responses. Do
not send candidate text, prior findings or English versions to an assisting process
before this document's pass-1 freeze. Do not deliberately run native extraction, OCR or
another model as a replacement for the source-first procedure. Using the source-page
representation your available image tool actually exposes is permitted, with the
caption-mediation disclosure above. No public research, new source, separate bot,
contact, login or security change is authorized.

Disclose all preexisting exposure, previews, captions, alt text, summaries, tools and
assistance that could influence the review. Do not assert independence unsupported by
the actual history. If the permitted representation cannot show an expected page or
region, mark it unchecked or unavailable. Do not fill missing language from context.

## Pass 1: source-only reading and immutable freeze

Process the full representation of **all six physical pages** of the current document,
including covers, final pages, margins, page labels, footers, headings, tables, notes,
execution areas and any page continuations. Open each complete page before technical
crops. Preserve each page request and which output was actually available. Do not
claim to have read a page solely because its filename exists.

For tables, retain every row/column association, complete header, unit basis, note and
footnote link. Record a page continuation explicitly rather than guessing that a nearby
heading governs it. Separate layout/reading-order choices from literal wording. Keep
blank fields blank, truncated text uncertain, and conflicting/source-owned labels intact.
Describe color, strikes, underlines, insertions and other marks separately as tool-reported
observations awaiting direct image confirmation. Mark presence does not establish an
enacted change. Distinguish handwriting or signature marks from printed labels; never
infer identity or initials from proximity. Do not certify Unicode code points, whitespace
counts or exact typography based on a caption.

Save `PASS1_frozen.md` in a **new unique attempt directory**. Include each expected
physical page, any tool-reported printed label, the actual representation/method,
Spanish reading with its evidence basis, and all unresolved/unchecked regions. Freeze
its exact bytes; never replace it later.

Save `PASS1_FREEZE_RECEIPT.json` binding assignment/source ID, packet-manifest digest,
START_HERE hash, original PDF, every page image, exact frozen report path/SHA-256/size,
actual UTC start/freeze times, expected/processed pages, methods, assistance and prior
exposure. Unknowns stay null or explicitly unknown. Filesystem timestamps do not prove
review order. Record the unchanged pass-1 report hash in your Grok conversation.

Only after the frozen report, freeze receipt and chat hash all exist may you self-release
**this same document's** candidate without waiting for another Atlas acknowledgment.
The next document's candidate remains sealed until its own independent freeze. Preserve
any later pass-1 correction as an additive errata record.

## Pass 2: full-source recheck against unchanged candidate

After the freeze gate, verify the complete `MANIFEST.json`, its opaque digest, retained
payload hashes, copied canonical record, original PDF and page-image bindings. If your
execution tool supports it, run the packet's read-only validator and preserve the command
and output:

```text
PYTHONDONTWRITEBYTECODE=1 python -B 04-verification/validate_packet.py
```

If unavailable, verify hashes through available tools and state the exact unverified
scope. Do not skip original-copy checks because the candidate hash matches. A mismatch
stops this queue. Do not rerun the builder or modify packet files.

Open only `02-candidate-text/<current_source_id>/candidate.txt` and its corresponding
machine-page evidence. Both candidates are **machine_native_text_unreviewed**: PyMuPDF
1.28.2 `Page.get_text("text", flags=195, sort=False)`, exact UTF-8 bytes, native order,
Unicode and line breaks. Physical-page marker lines are packaging, not source text.
No corrected Atlas or English wording was substituted. Successful extraction and
hash/render verification are not transcription verdicts.

Recheck the available source-page representation of **every one of the six expected
pages**, including regions where pass 1 and candidate agree. Do not compare transcripts
alone. Repeat the caption-mediation/assistance disclosure and retain limitations; do not
upgrade the method label in pass 2. Check all Spanish wording, row/fee/column associations,
units, notes, exceptions, negations, cross-references, dates, margins, omitted graphics,
markup and execution areas. Preserve uncertainty and source anomalies without calculating,
reconciling dates, inventing attachments or determining applicability.

Save `PASS2_REVIEW.md` with complete page coverage and a discrepancy table. Each finding
must identify assignment/source SHA, physical page, tool-reported printed label if any,
region, exact candidate wording, source-supported Spanish wording or unresolved alternatives,
error category, materiality/severity and evidentiary explanation. Distinguish actual
wording/association discrepancies from harmless linearization, cosmetics, source typos
and uncertain glyphs. Caption-reported findings remain pending Atlas's direct source
verification. If the finding changes your pass 1, include its original and revised reading
in a separate errata table; keep the original frozen report unchanged.

A title, source filename, printed or metadata date, official referral or successful
extraction does not prove adoption, effectiveness, completeness, currentness or applicability.
All outputs retain `legal_currentness: not_verified`; no repository or source-review
status promotion is authorized by the bot's report.

Save `COMPLETION_RECEIPT.json` binding instructions, packet manifest, PDF, all images,
candidate, unchanged PASS1, freeze receipt and PASS2 by exact path/SHA-256/size. Include
actual start/freeze/candidate-release/completion UTC, both passes' actual page coverage,
remaining uncertainty, reviewer/model, assistance and known time/cost or explicit unknowns.
Distinguish recorded chronology from independently established chronology. Preserve literal
Spanish and dollar amounts safely; do not let a shell expand report text.

## Return each completed document and stop

If local writing is available, use only a new directory beneath:
`/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-13/ebenezer/reviews/<assignment_id>_<source_id>_<actual_UTC>/`

Return the four files, their exact hashes and paths, the page-coverage limitations and a
short status through the existing Grok Bot conversation with Atlas. Atlas will preserve
that delivery in the **current Codex task `01a08848-5f8e-7c51-9b66-fd82eff860fe`**.
Do not create another task or contact anyone. If local output is unavailable, return
complete reports in chat and disclose the limitation; never invent filenames or hashes.

Use `completed_pending_atlas_verification` only if the declared assisted procedure has
processed every expected page in both passes. Also record
`review_method: caption_mediated_source_first` and
`visual_verification: pending_atlas_direct_image_review`. This does not mean all regions,
text or glyphs were directly verified. List every unchecked area even when the assisted
procedure is complete. Missing pages or an identity/integrity failure mean `partial` or
`blocked`, not complete.

After a document's delivery you may proceed to the next exact queued document without
waiting, but only within the activation and cutoff rules above. Stop after EB-PDF-026,
the cutoff, an Atlas stop, or an integrity/source-access failure. No027, new research,
retries of old completed reviews, source edits, recurring continuation or other work is
assigned by this packet.
