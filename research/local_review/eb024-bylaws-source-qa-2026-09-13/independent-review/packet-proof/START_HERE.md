---
status: prepared_not_dispatched
start_no_document_at_or_after_utc: 2026-09-13T04:25:00Z
hard_stop_utc: 2026-09-13T04:45:00Z
stop_after: EB-PDF-024
legal_currentness: not_verified
---
# Ebenezer: finite source-first queue EB023 and EB024

This packet is prepared, not dispatched. Start only after Atlas explicitly activates it
in your existing Grok conversation, after the earlier assigned queue is complete.
Start no document at or after 04:25 UTC on September 13, 2026. Stop all work by
04:45 UTC. Check actual UTC at each document boundary. Stop after EB-PDF-024, an
integrity failure, unavailable source representation or an Atlas stop instruction.
No EB-PDF-025 is assigned. Do not repeat earlier completed reviews. No public research.

The complete frozen data packet is this directory:
`/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-12/extended-run/ebenezer-023-024/`.
All original/image/candidate paths in its metadata are relative to this directory.
Before each source-first freeze, read only this START_HERE, the neutral
SOURCE_ONLY_IDENTITIES.json beside it, MANIFEST_SHA256.txt, and the current document's
original PDF and complete physical-page PNGs. Do not open the full manifest,
preparation receipt, candidate, custody or verification directories before that freeze.
The opaque digest file identifies the frozen data manifest without exposing its contents.

| Assignment | Source ID | Physical pages |
|---|---|---:|
| EB-PDF-023 | larimer-equity-fee-memo-sd007-05 | 4 |
| EB-PDF-024 | el-paso-boh-bylaws-sd011 | 5 |

Use the exact identities and source/image hashes from SOURCE_ONLY_IDENTITIES.json.
Bind every freeze and completion receipt to the manifest digest in MANIFEST_SHA256.txt
and the exact START_HERE instruction hash. The complete images are 300 dpi source-page
renders; inspect the full page before taking technical crops. Neither the source title
nor collection identity certifies adoption, applicability or current law. Preserve the
actual images/crops and tool outputs used; do not cite absent files. Every document has
its own complete pass-one freeze before that document's candidate may be released.

## Pass 1: independently read the complete source

Before this document's pass-1 freeze, you may access only these instructions, the neutral source identity file, opaque manifest digest, and that exact original PDF and its complete page images. Do not open the full custody-bearing packet manifest, `02-candidate-text`, `03-custody`, `04-verification`, the preparation receipt, packet inventory or validator, prior Atlas/Sherlock/Ebenezer analyses, repository transcripts, review inventory details or the source lookup. Those materials can expose candidate wording, prior interpretations or preparation findings. Folder separation is procedural; it does not enforce blindness technically.

**Declare one review method per pass and page.** Direct pixel review is preferred. If your tool exposes the actual source-page pixels, describe that access truthfully. If it exposes only a caption or mediated source-page description, a **CAPTION-MEDIATED SOURCE-FIRST** review is permitted: label the work assisted, name the tool and assistance supplier/model if known, preserve or identify the tool output, and distinguish what it reports from what you directly observed. Never call caption-mediated work direct pixel inspection or blind visual transcription. Unknown tool internals remain unknown; a caption may contain OCR/model interpretation and share errors with the later candidate.

Necessary internal execution and image tools are permitted for these two assigned sources, including an internal executor that reads the authorized source images, computes hashes/crops or writes outputs. Preserve each exact executor/tool prompt and available response, declare any caption or model mediation, and do not provide candidate/prior-review text to any assisting process before the relevant freeze. This permission does not authorize separate bots, external research, a new source or a silent claim of direct pixel access.

Do not deliberately run native PDF extraction, OCR or a second model as a substitute for the independent first-pass procedure, and do not open another existing transcript or prior review. In the permitted assisted route, use only the source-page output your available tool actually exposes. Keep the candidate and prior findings sealed through the same frozen report, receipt and chat-hash gate. Disclose preexisting exposure, previews, captions, alt text, summaries, assistance, tools, suppliers and their possible influence. If you previously saw candidate wording or relevant prior findings, say so; never label that pass blind.

For assisted work, record all expected page requests and which page outputs were actually available. Mark unrepresented/unchecked regions, uncertain letterforms and any tool omissions; do not fill them from context or assert that the source says what a summary merely suggests. The result remains **assisted and pending Atlas's actual image verification**. Missing page coverage, an unavailable source-page representation or an identity/integrity failure is partial or blocked. Availability of a caption does not authenticate complete transcription or exact glyphs.

For direct review, inspect **every complete physical page**. For the assisted route, process the tool-provided representation of **every expected physical page**, explicitly retaining unchecked regions and its representation limits. Transcribe the available printed-body reading with its declared evidentiary basis; preserve reported wording, capitalization, punctuation, numbers, units, dates, cross-references, conditions and exceptions without claiming pixel precision from captions. Include title/frontmatter, headings, tables, margins, footers, notes and execution areas. For tables, record the heading and every row/column association, per-unit basis, notes and any linked footnotes. Distinguish page layout and chosen reading order from the printed wording. Preserve source typos, apparent arithmetic anomalies, conflicting labels and uncertainty; do not silently normalize them.

Describe color, strike-through, underlining, insertions, deletions, blank fields and other marks separately from plain text, distinguishing directly visible features from tool-reported features. A directly viewed mark is a pixel observation, not proof of an enacted amendment; a caption-reported mark remains an assisted claim awaiting Atlas verification. Separate handwriting/signature presence from printed names; never infer the writer or signer from a nearby label. Give alternative readings or leave a glyph unresolved where warranted. Do not claim exact Unicode code points, typography, spaces or leader-dot counts from pixels.

List each expected physical page, any directly visible or tool-reported printed page label (distinguish them), the actual method, source-page representation received and all unresolved, unchecked or unviewed regions. Save `PASS1_frozen.md` in a **new unique attempt directory**, then hash its exact bytes. Save `PASS1_FREEZE_RECEIPT.json` binding assignment ID, source ID, this frozen packet-manifest hash, START_HERE instruction hash, original PDF and all page-image hashes, expected/inspected pages, actual UTC start and freeze times, reviewer/model if known, methods, prior exposure, captions/assistance and limitations. Unknown values remain null or explicitly unknown; filesystem mtime is not proof of review completion or blind order.

Record the unchanged pass-1 report SHA-256 in your Grok conversation. **Only after the frozen report, freeze receipt and chat hash all exist may you self-release this same document's candidate without waiting for another Atlas acknowledgment.** Never rewrite the frozen pass. Keep an append-only correction/addendum if later needed.

## Pass 2: compare source pixels with the candidate

After that document's frozen report, receipt and chat hash exist, verify the **complete packet manifest**, its opaque digest, all retained payload hashes and the exact original-copy/page-image bindings before comparison. You may now inspect the custody and verification metadata. Run `PYTHONDONTWRITEBYTECODE=1 python -B 04-verification/validate_packet.py` read-only if your available execution tools support it; retain its exact command/output. Otherwise verify the hashes through your available tool and state precisely what was not verified. Never skip source-copy verification merely because the candidate hash matches. A mismatch stops this queue.

Open only this document's `02-candidate-text/<source_id>/candidate.txt` and corresponding machine-page evidence; the next document's candidate remains sealed until its own pass-one freeze. EB023 is **machine_ocr_unreviewed**, generated by the existing on-device Apple Vision revision-three adapter from the four complete images. Exact engine observations, confidence/bounding boxes, settings, binary/source hashes and raw outputs are retained. Observation strings are joined by LF in engine order without correction; initial empty native extraction and a failed sandbox OCR attempt are separately retained. EB024 is **machine_native_text_unreviewed**, using PyMuPDF 1.28.2 `Page.get_text("text", sort=False, flags=195)`, preserving exact native bytes, order, Unicode and line breaks. The physical-page markers in either candidate are packaging, not source text. Neither method is presumed accurate or equivalent to the other. Preparation's hash, extraction or rendering checks are not a transcription verdict.

Recheck **every expected physical source page**, including regions where pass 1 and candidate agree, using the declared available method. Direct review reinspects the full pixels; assisted review rechecks the page representation and marks regions it cannot verify. Do not compare transcripts alone. Repeat the method/assistance disclosure in pass 2; do not silently upgrade caption access to direct image access. Check table associations, fee amounts and bases, footnotes, exceptions, dates, negations, deadlines, cross-references, omitted graphics and markup, margins and execution areas. Keep source anomalies and uncertain readings. Do not calculate, repair arithmetic, infer missing attachments, reconcile contradictory dates or decide legal interpretation.

Save `PASS2_REVIEW.md` with full page coverage and a discrepancy table. Each finding must identify assignment/source SHA-256, physical page, visible printed label if any, region, exact candidate wording, source-supported wording or unresolved alternatives, error category, materiality/severity and visual explanation. Distinguish a real wording/association error from harmless linearization, typography or an uncertain glyph. If a source-supported finding also changes pass 1, put the original and revised readings in a separate pass-1 errata table; preserve the frozen report.

Bind PASS2 to the original, all images, candidate and unchanged pass-1 hashes. Record any additional assistance or exposure. A title, filename, printed date, official referral, received metadata or successful extraction is not evidence that a document is adopted, effective, complete, applicable or current. All outputs retain `legal_currentness: not_verified`; no source-wide certification or repository status promotion is authorized.

Save `COMPLETION_RECEIPT.json` binding these instructions, this packet manifest, PDF, all images, candidate, PASS1 report, freeze receipt and PASS2 report by exact path/SHA-256/byte count. Include actual UTC start/freeze/candidate-release/completion times, both passes' page coverage and unresolved areas, reviewer/model, known time/cost or explicit unknowns, and the distinction between reported chronology and independently proved chronology. Use safe structured writing that preserves literal dollar amounts and punctuation; do not let a shell substitute report text.

## Return results here and stop at the queue boundary

If local file writing is available, use only a new folder beneath:

`/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-12/ebenezer/reviews/<assignment_id>_<source_id>_<actual_UTC>/`

Do not overwrite any previous packet, original, review, receipt or repository file. If that output route is unavailable, return complete reports and declared limitations in your Grok conversation for Atlas to preserve; do not invent local paths or file hashes.

Return each document's four files, hashes, exact output locations and short status to **the existing Codex task “Assess Colorado project status”, task ID `01a08848-5f8e-7c51-9b66-fd82eff860fe`**. The operational return route is your existing Grok Bot conversation with Atlas: Atlas will bring the delivery into that task. Do not start a new Codex task or contact another person. Report `completed_pending_atlas_verification` only when the **declared procedure** has covered every expected physical page in both passes; otherwise use truthful `partial` or `blocked`. For caption-mediated work, the status means only that the declared assisted procedure covered those pages. Also record `review_method: caption_mediated_source_first` and `visual_verification: pending_atlas_direct_image_review`; it does not mean all text, regions or glyphs were visually verified. List remaining unchecked regions and uncertain readings even when that assisted procedure is complete. An absent page or unresolved identity/integrity failure remains partial or blocked. A bot's completion report does not replace Atlas's actual image verification.

After returning a document, you may continue without acknowledgment to the next exact queued document if before the no-new-document cutoff. Keep every document's pass-1 freeze separate from its own candidate release. An unresolved integrity or source-access failure stops this finite queue; report it. Stop after EB-PDF-024, an applicable cutoff or an Atlas stop instruction. No new documents, network research, bot delegation, official contact, source/repository edits, scheduled continuation or follow-on task is authorized by this packet.
