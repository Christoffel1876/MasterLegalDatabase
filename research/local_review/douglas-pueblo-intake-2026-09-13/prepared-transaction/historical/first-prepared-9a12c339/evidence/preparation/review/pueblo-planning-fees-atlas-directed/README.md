---
title: Pueblo City planning fee schedule source QA
status: frozen_candidate_aware_source_review
source_sha256: 0ba13c07bede5bf07c24dd8bbbe604c61745e8a73be773a7987e26dfa601414b
legal_currentness: not_verified
---

This package preserves one four-page City of Pueblo planning fee schedule and a candidate-aware Atlas source review. It contains 44 physical application rows, 43 nested entries, and all 4,923 native UTF-8 bytes across 243 lines. The rows retain their paired Applications/Fees cells, source geometry, source-page hashes and nested category relationships. Rezoning has 11 paired categories; Commercial Site Plan has six complete fee bullets. These counts describe this table, not all municipal laws or legal requirements.

Read SOURCE_QA.md for the full reviewed table and SOURCE_QA.json for exact line, byte, geometry and evidence bindings. The original PASS1_frozen.json is unchanged. Additive errata correct both remodel clauses to “nor site improvements” and withdraw the original header/date omissions: all four pages show the letterhead, Applications/Fees header and printed 2-13-26. Targeted crops and identical repeated-region pixels support that correction. The cause of the initial omission was not established.

The CCN/RCN fee has a separate low horizontal graphic between $150 and +. Native text omits that graphic; the reviewed underscore-like notation is explicitly qualified. No numeric operator or arithmetic repair is inferred. Annexation-waiver, hourly legal-review, Vacation exception and common “fees per plat” notes remain attached to their source rows or nested entries.

The copied public custody subset contains E002 (official parent HTML), E004 (explicit redirect) and E005 (the PDF), plus their reservations and observed links. E005 body.bin and original.pdf are duplicate custody copies of the same document. Other discovery events and the county access failure remain in the separate discovery package. No new public request or canonical intake was performed for this QA. The filename, printed date and actual HTTP receipt times are distinct evidence; no adoption or legal currentness was verified.

Run this read-only verifier from any working directory with Python, Pydantic 2, PyMuPDF 1.28.2 and Beautiful Soup available:

```sh
python /absolute/path/to/pueblo-planning-fee-source-qa/validate_qa.py --rerender
```

The verifier rejects altered native text, swapped row/category/fee bindings, lost notes, wrong source/custody identities, unsafe paths, extra files and inconsistent source pixels. It does not execute the frozen builders or contact any URL. Rendering replay requires the declared compatible PyMuPDF runtime; ordinary hash verification does not claim portable rendering byte equality across library versions.

66 focused tests passed with at least 90% branch-inclusive coverage for each module. VERIFICATION.json identifies the final test log and coverage file. Earlier test logs and pre-freeze-snapshots are retained development history and are not the accepted QA. All 16 original inputs are individually bound by PRESERVED_INPUTS.json. Root's two original crops are retained without inventing their creation settings or timestamps; the six independent crops have exact replayable source settings.

The first Poppler attempt was stopped after configuration errors. A second local render with an explicit font configuration succeeded; only its four full-page images are used as supplemental review evidence. Poppler cache files are outside this package and are not required by the read-only verifier. No lookup, monitoring enrollment, current-law mode or semantic promotion is provided.
