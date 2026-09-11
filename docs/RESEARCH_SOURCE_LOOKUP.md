---
title: Checked source lookup
created: 2026-09-11
scope: one_frozen_source_table
legal_currentness: not_verified
---

# Checked source lookup

Use this command to find and cite rows in the reviewed Grand Junction
fire-prevention fee snapshot. It checks the source PDF, review, page text and
row associations before returning results. It supports this one 57-row table;
the broad search pipeline and other preserved sources are separate work.

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

The default output is Markdown. JSON also supplies exact native byte offsets,
span hashes and page references for heading, label and fee. A page-two row keeps
its explicitly qualified reference to the page-one heading; that heading is not
invented as printed page-two text. The historical review alias
`grand-junction-fire-fees-mg-07` and the canonical source ID are bound by the same
PDF hash and remain separately named.

Every result has `legal_currentness: not_verified`, `answer_safe: false` and null
adoption, effective and edition dates. Acquisition and review timestamps are
separate evidence events. An empty result means only that this snapshot has no
matching row; it does not establish that a service is free or unregulated.

Current-law/applicability questions and `--mode current-law` return a refusal
with no rows. Exit status 0 means the source lookup completed, 1 means invalid
request/evidence, and 2 means the current-law/question request was refused.
Successful lookup is never permission to treat a fee as presently applicable.

The command performs no network calls and writes no source, index or ledger.
It verifies fixed file hashes before executing the pinned offline package
validator with assertions enabled, then rechecks the package. Missing, changed
or misbound evidence produces no source result. Use `--root PATH` to select a
repository checkout; evidence symlinks and parent-traversal paths are rejected.

Read the [source review](../research/local_review/grand-junction-fire-fees-atlas-source-review-2026-09-11/README.md)
for inspection scope and the [earlier readiness assessment](../research/local_review/project-readiness-2026-09-11/README.md)
for the broader query and coverage blockers. This lookup is an additive
implementation after that timed assessment; it does not alter frozen reports,
claim coverage of the other 45 manual originals, or repair the missing catalog.
