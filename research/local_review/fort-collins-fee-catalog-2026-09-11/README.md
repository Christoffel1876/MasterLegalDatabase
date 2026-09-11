---
title: Fort Collins fee catalog — preserved page structure
created: 2026-09-11
source_id: fort-collins-fee-catalog-atlas-sd004-14
status: source_snapshot_structured_pending_semantic_review
legal_currentness: not_verified
---

# Fort Collins fee catalog — preserved page structure

This package structures the complete `#main-content` region of the City of Fort
Collins Fee Schedules HTML captured by Atlas on **2026-09-10 at
22:06:37.843075 UTC**. It is a source snapshot, not a new retrieval or a verified
statement of current fees. The original HTML and the exact earlier HTTP receipt
are preserved in `source/`. Their original capture identifier is `SD004-14`; this
package's source ID is a research identifier, not a source-ledger registration.

The source URL is
[City of Fort Collins Fee Schedules](https://www.fortcollins.gov/Business/Building-and-Development/Fee-Schedules).
The HTML SHA-256 is
`a10bcc173cd8e20bbfa83dd06292203c6c4ddd4720a58338c6f2b5f1eaeceb55`.
The preserved receipt's earlier `inspection_scope: not_yet_inspected` remains
unchanged; the separate extraction status describes this package's work.

## Contents and boundaries

`extraction.json` contains 337 ordered content blocks, including 213 list-item
fragments and nine tables with 76 source rows (headers included) and 238 cells.
All 674 nonblank text fragments within the selected region have exactly one
content owner. The record also preserves 1,015 elements, 1,752 text fragments and
48 anchors. These are structural counts, not counts of unique fees or legal
requirements. Some fees repeat in multiple source presentations.

The source's eight panels are kept distinct: Payment Methods, Where to Pay,
Building Permit Fees, Development Review Fees, Utilities Fees, Poudre Fire
Authority Fees, Capital Expansion Fees (including Transportation Capital
Expansion Fees), and Contact Us. Their prose and nested lists remain in source
order, including payment charges, service areas, exceptions, additional charges,
water supply requirements, water and wastewater units, city capital expansion
fees and the separately headed Larimer County transportation fee lists.

The printed `Jan. 1, 2024` phrase stays with Development Review Fees, `in 2022`
with Utilities Fees, and `January 1, 2026` with Capital Expansion Fees. The
`printed_date_mentions` field is a convenience index of the explicitly supported
date-phrase patterns, not a general date/event parser. All remaining date or
relative-time text stays in the complete content. No date is converted to an
adoption, revision or effective event, or copied to a neighboring component.

The two excluded byte ranges identify everything before and after
`#main-content`: document head, scripts/styles, site header/navigation,
breadcrumbs, back-to-top controls and site footer. Those bytes remain in the
original HTML. Page-specific contact details are included. HTML comments and
markup are preserved in the original and source envelopes, but are not projected
as visible text. Image attributes and alternative text are retained as metadata;
no external image, stylesheet, script or linked resource was retrieved or run.

## Text and provenance contract

`elements` stores source-tree locators, ordered decoded attributes and exact byte
ranges for element envelopes and tags. Locators use tag sibling indices from
Python's source parser; they are not claims about a browser's repaired DOM.
Every text/entity token has an exact half-open UTF-8 byte range and SHA-256.

`dom_text` concatenates unchanged character data and explicitly decoded HTML
entities. A source `<br>` is projected as a line feed. `normalized_text` collapses
Unicode whitespace to one ASCII space and trims ends. No Unicode composition,
spelling, punctuation, numerical or substantive correction is performed.

Blocks reference their fragments. Table text lives only in cells; parent list
blocks contain their own label/prose, while nested items are separate. Ancestor
list locators preserve hierarchy. Element envelopes, anchor labels and heading
context are provenance metadata and may overlap; they must not be counted as
additional content transcripts. A split list block's envelope can include
nested children, so use its `fragment_ids` to identify the text it owns.

Anchors preserve observed `href`, resolved URL, label, title and content owners.
URL resolution performs no request. For example, the printed email's source href
`/utilityfees@fortcollins.gov` remains a website-relative path; it is not silently
changed to `mailto:`. Source tier wording such as `Over 3,601` is unchanged.
Components describe source panels, not a determination of government ownership,
PFA's legal form or a fee's applicability.

## Offline verification

Use Python with Pydantic 2. The extraction was prepared and checked with
Python 3.14.3 and Pydantic 2.13.5. Tests also use pytest, pytest-cov and jsonschema.
From this directory:

```bash
python extract_catalog.py --verify
python -m pytest test_extract_catalog.py -q --cov=extract_catalog --cov-branch
```

The first command rebuilds the record from the exact HTML/receipt, validates it
through the strict Pydantic model, and requires byte-identical output and an
identical exported schema. This is stronger than JSON Schema validation alone.
The extractor refuses to replace an existing output. To reproduce new output,
copy `extract_catalog.py` and `source/` into an empty separate directory, then run
that copy without `--verify`; do not remove or overwrite this package's evidence.

The tests independently check every one of 5,144 source byte ranges and hashes,
entity decoding, text normalization, DOM order, unique fragment ownership, all
anchors, table dimensions, fee prose, printed-date binding, source/output/schema
tampering, invalid model records and refusal to overwrite. Final test and file
identities are recorded in `verification-receipt.json`. Earlier development
versions are preserved in `_SNAPSHOTS/` and are not the released extraction.

## Remaining review

Structural completeness applies only to this preserved page's selected content.
Linked PDFs, code provisions, adopting instruments and amendment chains are not
included merely because the page links to them. No fee totals, operative rule
units, ownership decisions, coverage promotions or ledger entries are produced.
The result remains **source_snapshot_structured_pending_semantic_review**, with
legal currentness **not_verified**.
