---
title: Independent EB025–026 reconciliation audit
date: 2026-09-13
reviewer: Popper
status: no_actionable_issue_in_recorded_scope
---

All 16 root dispositions are supported within the checked scope. The three
externally reported critical findings are distinct from zero accepted critical
errors. The fee-word split is a formatting defect, the clipped footer year stays
unresolved, and the food-license continuation retains both physical rows. Both
proposed continuous bylaws citation numbers would change the printed source.

`AUDIT.json` records the 16 checks and the 11 image assets directly viewed in this
candidate-aware, post-report pass. It preserves the distinction between displayed
pixels, native character encoding, and historical tool-execution claims. This is
not a fresh blind review, a complete retranscription, translation certification,
or a current-law determination. All originals remain unchanged.

The `repository/` tree is a portable evidence subset. It includes the entire
canonical reconciliation and its complete historical delivery-audit subpackage,
plus the exact cited source-QA records, schemas, acceptances, images and crops.
It intentionally excludes other assets and validators from the two larger source
review packages. Those packages are not claimed to have been fully replayed here.

Run the read-only check from any directory with Python, Pydantic 2, jsonschema and
PyMuPDF available:

```sh
python -B /absolute/path/popper-reconciliation-audit/verify_audit.py
```

It verifies closed membership, all hashes, schemas, original report joins,
source/candidate identities, retained footer/currentness limits and the 124
historical delivery bindings. It does not judge images or prove historical review
order. `test_audit.py` uses temporary fixtures for refusal probes; the recorded
`tests.log` reports the actual run. No public activity is performed.
