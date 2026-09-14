# PDF source-fidelity review

Use this method when preparing or reviewing a PDF transcription, fee table or other
research extraction. It supplements the [reviewer SOP](GEODE_REVIEWER_SOP.md). It
does not activate a queued assignment or authorize a canonical apply operation.

## Keep three questions separate

1. **Custody:** Which exact original was acquired, from which observed official
   referral and URL, and when? Record response completion separately from repository
   receipt. A parser opening a file does not prove that an earlier HTTP transfer
   completed correctly.
2. **Source fidelity:** Does the extraction preserve the original's text, layout
   relationships, notes, markup and uncertainty?
3. **Legal currentness:** Was the document adopted, effective, superseded or applicable
   to the question? Source-fidelity review alone does not answer this question.

Keep issuer, collecting agency, county, municipality and related district roles
distinct. A source's title, printed year, filename or successful download is not a
currentness decision. Retain `legal_currentness: not_verified` unless a separate
documented currentness review supports another status.

## Freeze the independent first pass

The assignment must name the source hash, physical page count, permitted files,
candidate type, stop conditions and delivery location. Review every physical page,
including covers, margins, footers and signature areas.

For a source-first pass, open only the original and its exact rendered pages before
freezing the transcript. Do not consult candidate OCR/native text, earlier
corrections or another review first. Save the frozen report, its SHA256 and a
separate receipt before opening the candidate. Preserve that first report unchanged.
Artifact timestamps record availability; they are not independent proof of when a
model saw information.

State the actual viewing method. Direct page-image inspection, caption-mediated
tools and assistance from another model are different methods. Disclose prior
exposure. A reviewer using the same model or an existing correction can provide
useful verification, but should not describe it as an independent blind pass.

## Compare the candidate to the visible source

Keep uncorrected native extraction or OCR bytes unchanged. Native text can lose
reading order, table associations, graphic text and visible markup even when its
words appear accurate. Page markers and candidate packaging are not source text.

Record each finding against a physical page and a specific source region, including
the candidate text, supported correction or uncertainty, and why it matters. Review
the following together:

- A fee's row and column, units, tier, year, exception and relevant note. Keep nested
  conditions and multiple amounts in the same cell distinct. A blank cell is not zero.
- Cross-page table continuations, group headings and definitions. Do not carry a
  classification into another row merely because its wording seems similar.
- Visible strikes, additions, highlights, redactions, handwriting and signatures.
  Describe what is visible; do not infer legal effect from markup or identify a
  handwritten signatory from an adjacent printed name.
- Negation, conditions, dates, citations, decimals and limits. Do not silently repair
  source typos, contradictory figures, missing subsections or inconsistent dates.

Treat absence claims as findings that need evidence. If a full-page display seems
to omit text present in a candidate, inspect a focused crop of the exact rendered
region before calling the candidate text invented or invisible. Check headers and
footers on each physical page, including repeated ones. Record crop page, pixel
bounds, image hash, renderer and any scaling. Do not substitute one page's crop for
another without checking the actual pixels.

Where needed, inspect the PDF text geometry, color or clipping and an additional
rendering. These can explain a discrepancy; native text alone cannot prove
visibility. Conversely, an overlooked footer in an initial visual pass is a
reviewer correction, not automatically a PDF defect. Do not invent an explanation
for a tool's display behavior.

Exact Unicode punctuation, superscripts and stylized initials may remain uncertain.
Distinguish normalized display text from exact source/candidate bytes rather than
claiming a particular code point solely from a small raster image.

## Record corrections without rewriting history

Use an additive errata record for errors in the frozen first pass or an earlier
review. State which claim is withdrawn or qualified and what new source inspection
supports the change. Do not relabel feedback-based work as a renewed blind pass.

A completed review should retain:

- Original PDF and physical page images, with exact hashes and page counts.
- Frozen first pass and its receipt; unchanged candidate and extraction settings.
- Page coverage, individual findings, unresolved regions, source anomalies and errata.
- Reviewed row/context relationships, where a structured table is supplied.
- A closed inventory and an offline verifier that checks custody and relationships.

The verifier should reject altered page identities, incorrect row/column bindings,
unlisted evidence and changed originals. Report what it actually replays: checking
hashes is different from regenerating native text, rendering pages or visually
reading them. Keep test fixtures, simulated clocks and actual public acquisitions
clearly labeled.

## Accept only the reviewed scope

Atlas reviews the returned evidence and records a scoped disposition. Partial
review can be preserved with explicit unchecked pages; it must not become a claim
that the full document was verified. Discovery, source review, canonical intake,
research lookup and recurring monitoring are separate transitions.

Before exposing a numeric research result, bind it to the exact accepted original
and reviewed page/row/context. Preserve unresolved wording and associated
conditions in the result. Do not calculate a project's charge or promote current
legal applicability through a source-fidelity acceptance.
