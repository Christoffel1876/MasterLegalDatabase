---
status: accepted_bounded_source_lookup_behavior_not_current_law
source_id: el-paso-boh-ehs-fees-sd011
legal_currentness: not_verified
---
# Independent El Paso English EHS lookup acceptance

Twenty-five source-derived cases were frozen before the new adapter was read. The first
immutable draft passed 24 and failed the exact phrase `Section 2`: a numeric boundary
rejected the comma after the citation. `EXECUTION.json` and its raw outputs preserve that
failure. The implementation owner added an EHS-only citation matcher; eight targeted
source cases and five additional numeric/citation boundary cases then passed. The final
tested draft is SHA256 `3aeba887caf30e34b5041f8d85caff0a43e7e1f7c8f3e9f17221312f559f8fcf`.

The other six sources retain byte-identical full-list JSON and Markdown output. All 65
source rows and 37 complete contexts were compared with the accepted source QA, including
all years, explicit footnotes/definitions, no-fee investigation context, the unresolved
Section 2 exception and statutory-reference-only license fee. Current-law and Spanish
source requests are refused. No numeric fee is calculated or promoted to current law.

The first run and correction run each bind the actual draft before/after and an immutable
tested copy. Code did not change during either run. The final AST differs only in EHS
matching from the initially tested addition; all original source functions and the shared
matcher remain unchanged. The 49 initial CLI invocations, eight focused replay invocations,
five boundary invocations and one additional full-list Markdown capture are retained.

`source-expectations/` is a byte-exact copy of the closed original expectation package.
The source PDF is not duplicated; the accepted QA metadata identifies it and its existing
repository location. Prototype/test scripts contain historical absolute execution paths.
Only `verify_execution.py` is the portable verifier; it does not import or run those scripts.
The original received-review-package transport/time qualifications remain, and no new PDF
visual review, network request, production edit or legal-status assessment occurred here.

```sh
python -B /absolute/path/to/el-paso-ehs-lookup-independent-execution/verify_execution.py
```

The verifier checks closed hashes, typed receipts, retained output/source expectations,
resolved failure and unchanged old-source output comparisons. It does not rerun the
adapter or its accepted source verifier. Root decides production integration separately.
