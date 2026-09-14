# EB025 independent structural validator

This closed package checks one retained Spanish El Paso County environmental health fee PDF,
`el-paso-boh-ehs-fees-spanish-sd011`. It preserves the complete current Atlas source QA and the
selected source-packet custody metadata. It makes no new visual judgment, translation-equivalence
claim, effective-date finding, current-law certification, or external-review disposition.

The six source pages contain 10,216 unchanged native UTF-8 bytes. The 10,894-byte candidate adds
explicit physical-page markers only. The verifier re-extracts the text with PyMuPDF 1.28.2,
`flags=195, sort=False`; replays all five physical table fragments, 75 rows and 65 fee rows;
checks 168 native byte spans, 27 complete passage bindings and 11 explicit links; distinguishes
one recorded blank fee cell from eight merged placeholders; and reproduces all 15 crops from
the retained full-page pixels. Sequential matching rejects a valid-looking fee copied from a
different occurrence. Row geometry and extracted cell strings must match the exact PDF.

The optional Poppler check also reproduces all six complete 300 dpi PNGs byte-for-byte. It
requires the exact recorded renderer binary, not merely a compatible version number. The ordinary
check verifies their frozen hashes and dimensions and replays the crops without invoking Poppler.

## Read-only verification

Use Python with Pydantic 2, jsonschema and PyMuPDF **1.28.2**. Run with `-B` so verification does not
create bytecode files inside the closed package. Replace the example path with this copied folder:

```sh
python -B /path/to/popper-eb025-validator/validate_eb025.py
python -B /path/to/popper-eb025-validator/validate_eb025.py --rerender
```

For the second command, put the recorded `pdftoppm` executable on PATH. Verification works from a
different working directory and uses only this package plus the declared Python/Poppler runtime.
It does not read the original repository, run retained builders, acquire a source, write to the
package, or require a live service. Verify the final manifest/code hashes from a trusted receipt
before executing code. The outer manifest detects all changed, missing or added files, including
otherwise cache-named files. Symlinks and path escapes are refused.

The 54 focused tests use only temporary fixtures. They exercise altered amounts, labels, source
PDFs, pages, native offsets and hashes, footnote and continuation links, blank/merged-cell changes,
crop substitutions, footer-year promotion and unsupported currentness/translation claims.
`validation/tests.log` and `validation/coverage.json` retain their actual results. Tests should be
run on a separate work copy because test and coverage outputs are not part of read-only validation.

## What remains qualified

Atlas's six-page visual review and recorded reading limitations are retained as the root review's
claims; Popper did not repeat that image review or consult external Ebenezer reports. Table and
native extraction replay establishes source-byte and geometry consistency, not what every pixel
means. All six footer records preserve a readable first native line and a separately qualified
native tail `d\n2023`; the visually certified year remains null. The printed 2024 fee wording is
not an independently verified adoption date or current legal status. Spanish and English document
equivalence has not been established. The original source and native text are unchanged.

The first root draft bound only `Aprobado` where its footer record described the complete first
line. Atlas corrected that discrepancy before this capture. The earlier bytes are retained under
`received/preparation-history/before-complete-footer-spans/`; they are historical evidence, not
current acceptance. A dedicated negative test rejects the historical one-word bindings.

`CUSTODY.json` records 50 exact file copies. The entire current root QA directory is included,
including historical preparation files. The shared source-packet manifest mentions EB026, but
only EB025 metadata, source, candidate and page assets are included here; EB026 source assets and
unrelated packet files are deliberately not included. Original paths in custody are historical
identifiers and are never opened by the portable verifier. Repository receipt time, supplied
historical HTTP claims and unknown original acquisition remain distinct. No raw manifest,
ledger, lookup, canonical review or legal promotion is performed.
