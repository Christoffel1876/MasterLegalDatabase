---
title: Checked source lookup
created: 2026-09-11
updated: 2026-09-12
scope: seven_fixed_source_reviews
legal_currentness: not_verified
---

# Checked source lookup

Use this command to find and cite evidence in seven preserved fee sources:
Grand Junction's 57-row fire-prevention table, Greeley's 19-entry building schedule,
Weld County's 137-row environmental-health schedule, Greeley's 30-row impact-fee
memorandum, Greeley's separate seven-plus-one-row proposed water/sewer notice, Colorado
Springs' seven-page 128-row Construction Services schedule, and the El Paso County Board
of Health's five-page, 65-row English EHS schedule.
Each output structure preserves its source wording and associations. These are transcription scopes, not counts of legal requirements
or complete jurisdictional fee coverage.

From the repository root, using the project's Python environment:

```sh
python scripts/research_source_lookup.py \
  --source-id grand-junction-fire-fees-atlas-directed \
  --query "system modification"
```

This returns two separate source rows for alarm and sprinkler modifications.
The complete source fee wording stays attached to each row's heading and label.
A result includes the physical page, row ID, original PDF link, official URL,
source and review hashes, and the review's qualifications.

Use keyword phrases, not questions. Matching ignores case and normalizes
whitespace and Unicode for search only. Returned JSON retains the original text.
It does not interpret synonyms, calculate an amount or decide applicability.

```sh
python scripts/research_source_lookup.py \
  --source-id grand-junction-fire-fees-atlas-directed \
  --query "mobile food preparation" --format json

python scripts/research_source_lookup.py \
  --source-id grand-junction-fire-fees-atlas-directed --list-rows
```

Grand Junction returns `rows`. JSON supplies exact native byte offsets, span
hashes and page references for heading, label and fee. A page-two row keeps its
explicitly qualified reference to the page-one heading; that heading is not
invented as printed page-two text. The historical review alias
`grand-junction-fire-fees-mg-07` and the canonical source ID are bound by the same
PDF hash and remain separately named. Its authority context is
`CO-MUNICIPAL-GRAND_JUNCTION`, separate from those document identities.

For Greeley's one-page building fee schedule:

```sh
python scripts/research_source_lookup.py \
  --source-id greeley-building-fees-sd008-06 \
  --query "inspections outside" --format json

python scripts/research_source_lookup.py \
  --source-id greeley-building-fees-sd008-06 --query "sales tax"

python scripts/research_source_lookup.py \
  --source-id greeley-building-fees-sd008-06 --list-rows
```

Greeley returns `entries`, not Grand Junction's `rows` structure. The 19 entries
are eight valuation clauses, nine other-fee items, sales tax and temporary
electrical inspection. Each entry retains a complete `statement`, its source
`headings`, linked `footnotes` and page image. For example, the outside-hours
inspection entry keeps both its two-hour minimum and the footnote allowing the
greater total hourly cost. The tax entry keeps both branches and their conditions.
Amounts and formulas remain source text; there is no computed numeric-fee field.

Greeley's 19 statement spans and ten `context` spans account for all 3,236 native
UTF-8 bytes. Its candidate file has a 56-byte page marker before those bytes.
Each block declares its byte basis and both candidate and native offsets; the
marker is not printed source text. The displaced tax and electrical headings
remain bound to their own bodies. The authority context is
`CO-MUNICIPAL-GREELEY`, separate from `greeley-building-fees-sd008-06`.

Greeley's `date_statements` preserve the 2024 title, `Effective -2024` heading
and unlabeled `8/18/2026` footer separately. None becomes a verified adoption,
effective or edition date. Its original acquisition time and canonical official
source URL remain null. The output distinguishes the official referral page,
reported Sitecore download URL and acquisition-time claim, actual repository
receipt, and source-review timestamp. Receipt is not acquisition. Custody remains
`received_review_package` and `archived_pending_pipeline`; this adapter does not
change the source-host allowlist. The cited review is candidate-aware Atlas QA,
not a blind pass, and its external-review status remains `pending_not_intaken`.

For Weld County's three-page environmental-health schedule:

```sh
python scripts/research_source_lookup.py \
  --source-id weld-ehs-fees-2026-atlas-directed \
  --query "file review" --format json

python scripts/research_source_lookup.py \
  --source-id weld-ehs-fees-2026-atlas-directed --query "additional metals"

python scripts/research_source_lookup.py \
  --source-id weld-ehs-fees-2026-atlas-directed --query "contract approved"

python scripts/research_source_lookup.py \
  --source-id weld-ehs-fees-2026-atlas-directed --list-rows --format json
```

Weld returns `rows` with its own typed structure. Each row has a `group`, one or
more `labels`, an optional `fee`, `fee_cell_status`, linked row `notes` and a full
page image. These blocks retain exact native text, physical page, half-open UTF-8
byte offsets and hashes. All 137 rows in eleven groups remain separate; the
schedule covers environmental-health services beyond the URL's OWTS directory.
Its authority is `CO-COUNTY-WELD`.

File Review's visibly blank fee cell is `fee: null`, with
`fee_cell_status: visibly_blank`. It is distinct from the two source rows with
printed `$0.00` fees and their school/nonprofit/mobile conditions. The wrapped
Additional Metals label remains two spans associated with one `$23.00` fee.
Hourly rates, caps, minimums, `Market Rate`, the bacteriological three-times fee,
source spellings and the clipped coordinator condition remain unchanged text.
The command does not complete the clipped wording or compute an amount.

Every Weld evidence result includes all three `page_context` entries and all
twelve review qualifications. Context includes the market-rate paragraph and
Board-approved-contract exception on page 3; it does not assign those notes new
legal applicability. The excess-four-hours parenthetical remains attached only
to its reviewed Methamphetamine permit row. A query that matches page context
but no fee row returns `status: matched_context_only` and `matched_context_ids`.
A rowless result therefore need not mean no source context matched. All page
context is retained even when there is no match. The unfiltered rows plus context
retain all 313 native lines and 7,367 bytes; shared group references repeat the
same line identity rather than inventing additional text. `header_visible` is
true for page 1 and false for pages 2 and 3: the latter native headers were not
visible in the reviewed full-page images.

Weld's printed 2026 year is a source assertion only. HTTP retrieval at
`2026-09-11T19:49:19.040662Z`, review at `2026-09-11T19:55:05.808484Z` and repository
receipt at `2026-09-11T20:02:02.187060Z` have separate fields. The frozen receipts
record an Atlas-initiated ordinary verified-TLS curl download followed by curated
intake, not a human-browser transfer. Status remains `archived_pending_pipeline`.
No adopting resolution, later amendment, contract replacement amount or current
applicability has been verified. The earlier pending-intake label in the frozen
source-review package remains historical; the adapter cites the later immutable
intake receipt and final records. It does not read the mutable raw manifest.

For the two additional Greeley source grids:

```sh
python scripts/research_source_lookup.py \
  --source-id greeley-development-impact-fee-memo-sd008-07 \
  --query "police-fee-5" --format json

python scripts/research_source_lookup.py \
  --source-id greeley-development-impact-fee-memo-sd008-07 --list-rows --format json

python scripts/research_source_lookup.py \
  --source-id greeley-water-sewer-proposed-pif-notice-sd008-08 \
  --query "Single Family" --format json

python scripts/research_source_lookup.py \
  --source-id greeley-water-sewer-proposed-pif-notice-sd008-08 \
  --query "assuming they are adopted"
```

These adapters return `rows` with explicit source `cells`, `column_headers`,
`group_headers`, `table_headings` and `column_roles`. A cell preserves its reviewed
display text, column start and span, blank/printed status, and every contributing
native string with exact native/candidate UTF-8 offsets and hashes. Display text
expresses the reviewed cell association; the `native_spans` retain original line
breaks, spacing and prefixes. `native_pages` also retain every original native byte,
including whitespace and disclosed non-visible extraction artifacts.

The impact-fee memo retains all 30 rows: seven Police, seven Fire, four Park,
four Trails, one Storm Drainage and seven Transportation. Its 2025 amount,
printed percent change and 2026 amount occupy distinct columns. Residential
labels span two columns; no unprinted per-dwelling unit is supplied. Page-three
Transportation rows carry an explicit page-two year/change header reference,
while their group heading and cells remain on page three. The source's
`1,000 Sq. Ft of Building` and `1,000 Square Feet of Building` forms are distinct.
The EAF grid and all source header/blank rows remain in `context_tables`, including
the blank final Weight cell. Blank means no printed value, not zero.

The repeated title is **visible on all three memo pages**. The accepted
[superseding disposition](../research/local_review/ebenezer-016-017-reconciliation-2026-09-12/SUPERSEDING_DISPOSITION.json)
withdraws the later mistaken not-visible claim; the adapter uses the original
correct source-grid visibility. The separate native `-A` artifact on page one
remains preserved and labeled not visible in the checked render. No source or
candidate bytes have been rewritten.

The proposed PIF notice has a seven-row tap-size table and a separate one-row
Single Family table. Equal amounts remain separate records. The right table's
blank first header remains null, and dollar signs appear only where the source
prints them. Every successful result, including a single-row query or a no-match
result, includes `mandatory_qualification`, complete source `context`, and
`date_statements`. **Greeley is the issuer; Weld County contractors are the
addressees.** The March 1, 2021 date is explicitly conditional on adoption:
“assuming they are adopted.” The page-two effective heading never overrides that
condition. This is a proposed notice, not proof of later adoption or current fees.
The source footer phone 350-9811 remains distinct from body phone 350-9801.

The memo's November 1, 2025 date, 2026 fee year and source-stated March 1, 2026
effective date are separate source assertions. Its prospective Water and Sewer
adoption “in December” supplies no explicit December year or rates and does not
establish adoption of the separate 2020 PIF notice. Neither adapter computes rates,
percentages, totals, inflation changes or applicability. All verified legal dates
remain null. Supplied HTTP acquisition claims, actual repository receipt,
source-review time, external reconciliation and superseding disposition each have
separate provenance fields. The canonical official source URL remains null; the
reported download URL and saved official referral remain separately labeled.

Both new adapters pin the complete 127-file accepted review package before
executing its verifier in an isolated `-I -B` subprocess, and recheck its bytes
afterward. The verifier includes title/native/image bindings, source-table checks
and external receipt bindings. The original frozen Greeley custody package is also
hash-checked. External captions and timestamps remain unauthenticated review
history; the missing EB017 `PASS1_NOTES.md` stays missing. The earlier building
adapter's historical `pending_not_intaken` output is unchanged by this extension.

A match in a source note or condition without a fee-row match returns
`matched_context_only`. Complete source context remains attached in all successful
cases; it is not converted into inferred row applicability. The lookup is offline
and separate from the normal query backend. From another working directory, use
the absolute script path and `--root` pointing to the repository checkout.

The default output is Markdown; `--format json` provides the typed evidence
bindings. Every result has `legal_currentness: not_verified`, `answer_safe: false`
and null verified adoption, effective and edition dates. An empty result means
only that this snapshot has no matching row or entry; it does not establish that
a service is free, exempt or unregulated.

Current-law/applicability questions and `--mode current-law` return a refusal
with no source rows or entries. Exit status 0 means the source lookup completed,
1 means invalid request/evidence, and 2 means the current-law/question request
was refused. A context-only match also uses exit status 0. Successful lookup is
never permission to treat a fee as presently applicable.

The command performs no network calls and writes no source, index or ledger.
It verifies fixed evidence and code hashes before executing the pinned offline
package validator in an isolated Python process with assertions enabled, then
rechecks the package. The building-fee adapter retains its original source-review contract. The two
additional Greeley adapters validate the accepted reconciliation with its
superseding title disposition, as well as the original frozen custody package. Weld checks the complete closed
review-package inventory, but executes only its pinned EHS `build_review.py
--verify` in an isolated `-I -B` process, with assertions enabled. It also verifies
the frozen intake receipt, final records and used access evidence. The sibling
Weld ordinance is an unsupported source ID. Missing, changed or misbound
evidence produces no source result. Use `--root PATH` to select a repository
checkout; evidence symlinks and parent-traversal paths are rejected.

Read the [Grand Junction source review](../research/local_review/grand-junction-fire-fees-atlas-source-review-2026-09-11/README.md),
[Greeley source-review package](../research/local_review/greeley-fees-atlas-source-review-2026-09-11/README.md)
and [Greeley building review](../research/local_review/greeley-fees-atlas-source-review-2026-09-11/source-audits/EB-PDF-015/SOURCE_QA.md)
for inspection limits. The [Weld source-review package](../research/local_review/weld-directed-atlas-source-review-2026-09-11/README.md)
and [Weld intake receipt](../research/local_review/weld-directed-intake-2026-09-11/intake-receipt.json)
preserve the county source and its custody. The [manual source/review inventory](../research/local_review/manual-source-review-inventory-2026-09-11/README.md)
links other preserved evidence and explicitly distinguishes missing review joins
from reviewed scopes. It does not expand this command's seven-source allowlist.

The [earlier readiness assessment](../research/local_review/project-readiness-2026-09-11/README.md)
records broader query and coverage blockers. This lookup is an additive
implementation after that timed assessment. It does not alter frozen reports,
repair the missing retrieval catalog, enable broad source search or certify the
remaining manual originals.


## Colorado Springs Construction Services

## Immutable input and execution boundary

The fixed accepted package is
`research/local_review/colorado-springs-construction-fees-qa-2026-09-12/`.
Source PDF SHA256:
`e35de501a011fe55f03140bf91aef54226997d896fec0b6308a2eac9bd40909a`.
SOURCE_QA SHA256:
`cb27452624c2b1be332a4eb241bee03520046466f95f696dee3a59cd7e94dc70`.
Its final manifest, schemas, verifier, every file and the separate root acceptance are pinned.
Missing/extra files, unexpected directories, symlink ancestors, traversal and changed source,
review, geometry, executable or custody bytes cause failure before a result is generated.

The copied original offline verifier executes using `python -I -B`, without inherited
credentials, with a 90-second timeout. It explicitly requires **PyMuPDF 1.28.2**, plus Pydantic
2 and jsonschema. It replays native text/geometry and source-response custody, checks every
line's assignment and every table/context relationship, and reproduces the twelve retained
crops. The lookup rechecks file hashes after verification and its contributing native ranges
before mapping results. Neither stage runs the downloader, OCR, a browser or any network call.

## Exact cells and complete qualifications

JSON keeps the complete label and `fee_as_printed` cell, exact line breaks and trailing spaces,
physical page, native line IDs, zero-based half-open native UTF-8 ranges, text/file hashes,
PDF rectangles and corresponding image-pixel rectangles. No candidate-text offset or currency
field is invented. All 410 native lines and 14,423 native bytes remain reachable through the
full listing's rows and complete context; footer/whitespace records stay separate.

Every verified response includes the full global plan-review note, implementation statement,
other-schedule reference and technology-fee row. The plan-review note preserves its
`Unless otherwise noted` qualification and the possibility of additional reviews/trips/
re-inspections. The technology row states `$25.00`; this adapter does not add it to another fee.
All thirteen complete definitions and all three table notes remain in `context`; each fee row
retains its original explicit links. `DEF-REINSPECTION` retains **both physical pages 6 and 7**.
The rendering groups complete definitions and notes before matched rows so no page-one-only
or first-sentence substitute can silently replace a condition.

The full Construction Plan Check Fee definition identifies PPRBD as collector through its
portal and preserves the conditional deduction wording. Colorado Springs remains the issuer.
The Accela statement applies to the separate fire-system plan-check definition as printed.
The lookup does not assign either role or condition to an actual project.

Two rate cells remain `0.04/sq. ft.` without an inserted dollar sign. The performance-based
label and definition retain the stated `$2,000` minimum separately. The additional-100-head
sprinkler row remains `$336.00`, with adjacent `$344.00` rows unchanged. Source tier boundaries,
`50, 000`, `R2`, `sq. Ft`, operators and grammar remain untouched. No total, extra charge,
classification, discount, rounding operation or IRS rate is computed.

## Matching, dates and custody

Queries are keyword phrases, not legal questions. Case/Unicode/whitespace normalization
affects matching only. A query searches each label, fee and table heading. Context is searched
separately; a definition-only hit returns `matched_context_only` without inventing a fee row.
Repeated labels are retained in source order. Missing matches do not mean free, exempt or
unregulated. Numeric boundary checks prevent partial-number matches such as `0` inside `500`;
use the complete printed amount, such as `$336.00`.

`--mode current-law` and obvious legal/applicability/calculation questions return exit 2
before reading evidence. Every source-mode result remains `answer_safe=false` and
`legal_currentness=not_verified` regardless of query wording. Evidence failure returns exit 1.

The source's `Effective 07/01/2026` remains a printed claim. Verified adoption and effective
dates remain null. Atlas's source request was reserved at `2026-09-12T23:10:46.676197Z` and its
complete HTTP 200 response finished at `2026-09-12T23:10:47.380038Z`, with no redirects.
Server Date and Last-Modified headers are not legal dates. The exact received PDF and body
copy are one document, not two sources.

`SD014-02` remains the historical review ID. The canonical intake ID is
`colorado-springs-construction-fees-atlas-directed`; the lookup keeps that identity separate from the source
review's historical alias. The accepted completed intake receipt now supplies the distinct
`intake_received_at=2026-09-12T23:56:16.492216Z` and `canonical_intake_verified=true`.
The immutable completed-intake package and its safe portable verifier are separately pinned;
the present canonical PDF must also match the received source hash. Acquisition completed at
23:10:47.380038Z, independently of the later intake time. Historical proposal text and SD014-02
remain unchanged; neither event establishes legal currentness.

## El Paso Board of Health English EHS schedule

The exact canonical source `el-paso-boh-ehs-fees-sd011` adds 65 service/fee rows from the
five-page English Chapter 3 schedule. Example from the repository:

```sh
/private/tmp/geode-status-venv/bin/python -B scripts/research_source_lookup.py \
  --source-id el-paso-boh-ehs-fees-sd011 --query 'OWTS New Permit' --format json
```

All 37 source contexts are returned, including definitions, the new-permit reinspection
asterisk, per-visit and no-fee-investigation notes, and the civil-penalty Section 2 exception.
The 23 OWTS rows include 14 on page 3 whose group heading is carried from page 2. Native cell bytes,
page images and table geometry remain bound separately from normalized display fields.

Printed approval October 25, 2023 and effective January 1, 2024 are source claims. Actual
repository receipt at 2026-09-12T22:59:48.795762Z is separate from the unverified original
Sherlock HTTP acquisition claim. No fee arithmetic, current applicability, or translation
equivalence is supplied. The six-page Spanish source is unsupported. All source exceptions
and definitions remain context; a context-only match returns no invented fee row.
No match does not establish free, exempt or unregulated activity.

Use `--list-rows` for all 65 rows. Queries such as `complaint investigations`, `100 per day`,
and `January 1, 2024` can return source context without a matching fee row. Current-law
mode/questions remain refused before evidence retrieval. No scheduler or baseline change
is part of this adapter. The manual review inventory receives one explicit checked-table
join with the source SHA and exact schema, preserving existing authority/custody joins.
