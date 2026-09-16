# Gunnison and Spanish review inventory supplement

The maintained inventory now has 67 sources, 30 explicit review links and 37 unmapped sources.
All previous 64 authority joins and 27 review joins remain unchanged. The new Gunnison intake
adds three county originals; accepted source QA adds one Gunnison prose-fee review and the two
existing Spanish El Paso sources. Legal currentness and English equivalence remain unverified.

VALIDATION.json/schema bind the precise code, plan, generated outputs, seven baseline preimages,
accepted source-QA inputs and actual focused test/check results. The 112 focused tests passed
with 99.2537% branch-inclusive module coverage. Earlier checkpoint counts remain historical.

From the repository root, run:

```sh
python -B -m geode.pipeline.manual_review_inventory --root . --check
```

No raw originals, manual intake manifest/ledger or local coverage ledger were changed by this
inventory integration. Full-suite execution and committing are reserved to the root task.
