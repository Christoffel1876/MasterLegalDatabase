---
title: Colorado Springs lookup and manual inventory integration
scope: existing accepted evidence only
legal_currentness: not_verified
answer_safe: false
---

# Additive integration

The sixth native-source adapter exposes the accepted Colorado Springs Construction
Services review: 128 fee rows, nine tables, 13 definitions, three table notes and
all 410 preserved native lines. Every evidence result retains all 80 context
blocks, the full plan-review note, implementation and other-schedule qualifications,
and the technology-fee row. The cross-page definition remains complete. The source's
`0.04/sq. ft.` strings remain without invented currency; the sprinkler tier retains
`$336.00`. No arithmetic or applicability decision is performed.

The canonical source ID is `colorado-springs-construction-fees-atlas-directed`;
the review's historical `SD014-02` alias remains separate. The installed adapter
validates the accepted source package, completed intake package and present
canonical PDF. It reports the actual intake time `2026-09-12T23:56:16.492216Z`
separately from the earlier HTTP response. Adoption and effective dates remain
unverified. The original frozen prototype's false/null intake fields describe its
earlier pending-intake state and were not rewritten.

The five earlier adapters retain exactly the same normalized all-row JSON and
Markdown outputs. Greeley's later reacquisition evidence is deliberately added
only to the manual inventory; it does not silently rewrite those historical
lookup outputs, raw null URLs, methods or receipt times.

The manual inventory now records 61 custody sources, 21 explicit scoped review
links and 40 unmapped reviews. These counts do not measure legal or geographic
completeness. All 20 prior review joins are unchanged. The two new municipal
authority joins are exact source/hash/provenance bindings; only the modern Springs
schedule has a reviewed-table mapping. The 2015 schedule remains metadata-only.
Exactly three existing Greeley authority joins gain verified HTTP bindings for
later September 12 exact-byte reacquisitions. The previous 59-row checkpoint and
legacy coverage ledger are preserved.

## Verification

The typed receipt binds code, tests, output schema, accepted evidence pins,
snapshots, examples and test logs. It retains the first failed installed run:
the strict directory check found the accepted intake's empty historical
`prepared-transaction/execution/.staging` directory. The installed check now
permits only that exact optional empty directory. Unknown directories or any
staging contents fail closed. No accepted package was changed to fit the adapter.

Run the read-only integration check from any directory:

```sh
/private/tmp/geode-status-venv/bin/python -I -B \
  '/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-12/colorado-springs-lookup-integration/verify_integration.py' \
  --root '/Users/mcoors/Documents/Project Geode/MasterLegalDatabase'
```

Use the installed command, for example:

```sh
python scripts/research_source_lookup.py \
  --source-id colorado-springs-construction-fees-atlas-directed \
  --query '0.04' --format json
python -m geode.pipeline.manual_review_inventory --root . --check
```

`examples/` contains actual installed CLI results produced from `/private/tmp`,
including current-law refusal and no-match. These are derived research outputs,
not fresh collection. The source files, canonical manifests, coverage ledger,
accepted reviews and frozen handoffs were not edited by this integration. There
was no network access, intake application, source collection or legal promotion.
This receipt covers focused checks; repository-wide testing and commit decisions
remain the parent agent's separate responsibility.
