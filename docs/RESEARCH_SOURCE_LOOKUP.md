---
title: Checked source lookup
created: 2026-09-11
updated: 2026-09-12
scope: three_fixed_source_reviews
legal_currentness: not_verified
---

# Checked source lookup

Use this command to find and cite evidence in three preserved fee sources:
Grand Junction's 57-row fire-prevention table, Greeley's 19-entry building fee
schedule, and Weld County's 137-row environmental-health schedule. Each has a separate output structure that preserves its source wording
and associations. These are transcription scopes, not counts of legal requirements
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
rechecks the package. Greeley's wrapper validates the entire retained package,
but only its building fee source is exposed by this lookup; the other packaged
Greeley documents are unsupported source IDs. Weld checks the complete closed
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
from reviewed scopes. It does not expand this command's three-source allowlist.

The [earlier readiness assessment](../research/local_review/project-readiness-2026-09-11/README.md)
records broader query and coverage blockers. This lookup is an additive
implementation after that timed assessment. It does not alter frozen reports,
repair the missing retrieval catalog, enable broad source search or certify the
remaining manual originals.
