# Colorado Springs completed source intake

Two immutable City of Colorado Springs Fire Department PDFs were received into the municipal raw archive at **2026-09-12 23:56:16.492216 UTC**. The available originals increased from 59 to 61; the ledger increased from 60 to 62 and retains one separately identified missing historical file. Original prefixes remain byte-for-byte intact.

`ACCEPTANCE.json` records Atlas's review and actual application/verification. `prepared-transaction/` preserves the frozen preparation and actual execution receipts; `completed-canonical/` preserves the exact resulting records, raw originals and old preimages. The empty advisory lock file is omitted. There are no changes to legal currentness, source registration or daily monitoring.

The safe, portable, read-only entrypoint is `validate_package.py`. Run it with the reviewed Python environment, for example `python -I -B /absolute/path/to/this/package/validate_package.py`. It verifies exact files, schemas, receipt/intent/source bindings, prefix/suffix preservation, and the missing historical ledger entry. It does not need the repository. Historical transaction/build scripts contain their original path assumptions and are retained as evidence only: do not run them from this copy.

The older 2015-titled schedule has structural and selected-context review. The modern construction schedule has a separate accepted 128-row extraction review. Source-printed dates and references between schedules do not establish adoption, supersession or legal currentness. No fee calculation is certified.
