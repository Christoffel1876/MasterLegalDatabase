# Land-use research studies

These files contain selected, cited observations for process comparison. They are
not canonical legal-rule units and must not be used as a complete checklist or
current-law certificate. Counts include different actors and are not burden scores.

The first study is [standard rezoning, September 10, 2026](rezoning-2026-09-10.json),
covering unincorporated Jefferson and Clear Creek Counties. Its
[comparison and county details](../../docs/research/REZONING_COMPARISON_2026-09-10.md)
explain scenario boundaries, source conflicts, exceptions, and remaining questions.

Each observation preserves its responsible actor, modality, conditions, fee/timing
qualifiers, source identity, physical PDF page, printed label, and exact excerpt.
Sources preserve retrieval time, URL, byte hash, archive path, and currentness notes.
`research_only` is always true and `legal_currentness` remains
`not_fully_reconciled`. Source-version consistency does not override that boundary.

With `requirements-county.txt` installed, check the study offline:

```bash
python -m geode.pipeline.land_use_study \
  --study research/land_use/rezoning-2026-09-10.json --root .
```

CI runs this check against the committed originals and tests malformed, mismatched,
missing, corrupted, or misplaced evidence. It validates exact excerpt presence;
substantive review must still assess whether a paraphrase retains the legal
conditions and whether the cited edition applies. Research sources are not added
to the daily collection manifest merely by appearing here.
