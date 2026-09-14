---
title: Greeley impact-fee and proposed PIF lookup extension
status: ready_for_independent_review
legal_currentness: not_verified
---

The three production files are frozen for independent review. The two new source
IDs return the complete reviewed 30-row impact-fee grid and separate seven-plus-one
PIF tables, retaining native/candidate bindings, source columns, merged cells,
blanks, dates and qualifications. The other three adapters return byte-identical
complete JSON and Markdown compared with the pre-change snapshot.

The final lookup-module run passed 187 tests. Coverage including branches is
96.53%; statements 97.75%; branches 92.42%. One subsequent test-only formatting
adjustment was checked by rerunning the affected test. No full suite ran here.

`impact-police-row.json` and `pif-single-family-row.json` are Pydantic-validated
example results; their Markdown views and result schema are supplied beside them.
Every PIF example retains “assuming they are adopted” and the Greeley-issuer/Weld-
addressee distinction. The accepted superseding title disposition remains attached;
the withdrawn not-visible claims never replace the original source-grid flags.

`IMPLEMENTATION_RECEIPT.json` records exact final/preimage hashes, commands, tests
and limits. `final-code/` holds exact copies for independent review. The documented
production command remains in `docs/RESEARCH_SOURCE_LOOKUP.md`. Both frozen evidence
packages must remain available; the command makes no network calls or source writes.
No source originals, reviews, raw manifests, indexes or control records were changed.
