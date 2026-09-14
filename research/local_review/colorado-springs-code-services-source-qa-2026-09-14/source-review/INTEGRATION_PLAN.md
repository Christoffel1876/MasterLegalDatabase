---
status: proposed_only
reviewer: Plato
legal_currentness: not_verified
---
# One-source inventory integration

After Atlas accepts the complete source review, preserve this compact self-contained package unchanged under one new `research/local_review/` folder and publish a separate acceptance receipt. No recursive external handoff wrapper is required for its verifier. Keep the source original and seven images exact; the raw canonical original already exists and needs no intake or modification.

Use the existing `geode/pipeline/manual_review_inventory.py` `ReviewJoin` contract. Add the exact `SOURCE_QA.schema.json` SHA256 to `ALLOWED_REVIEW_SCHEMAS` as `checked_tables`, and one pinned review/schema join in `research/local_review/manual-source-review-inventory-2026-09-11/join-plan.json`:

- record ID and expected review source ID: `colorado-springs-code-services-fees-2015-atlas-directed`.
- `/source_sha256`: `555570a62a5a557a824d1bcf3ecd2e60d57e48d19ea401f06a2e5b7ccb177e56`.
- source ID pointer `/source_id`; authority pointer `/authority_id` must equal `CO-MUNICIPAL-COLORADO_SPRINGS`.
- scope pointers `/review_kind`, `/status`, `/full_pages_inspected`, `/method`, `/findings`.
- limitation pointers `/legal_currentness`, `/answer_safe`, `/source_year_as_printed`, `/adoption_date`, `/effective_date`, `/limitations`.
- note: complete source-fidelity review of the preserved seven-page 2015 schedule; no legal-currentness, operative-effect, cross-edition equivalence or fee calculation certification.

Preserve all 70 authority/custody joins and the existing 35 review mappings exactly. The bounded expected inventory becomes **70 originals / 36 mapped reviews / 34 unmapped**. Do not change source/acquisition timestamps. The raw-manifest and legacy-ledger pins should stay unchanged unless an independent authorized intake actually occurred.

Required checks: exact preimage/snapshot preservation; schema/source/authority identity; one new review only; byte equality of prior rows after excluding only this source's review/status fields; currentness remains `not_verified` and `answer_safe` remains false for every row; deterministic regeneration and maintained inventory `--check`. Run focused inventory tests before root's next maintained suite. No lookup support or promotion to normal legal-query evidence is implied by this metadata-only join.

Final exact QA/schema/manifest hashes are in the closed `FINAL_MANIFEST.json` and final delivery message. This file is a plan, not an execution claim.
