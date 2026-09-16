---
status: source_expectations_frozen_before_new_adapter_review
source_id: el-paso-boh-ehs-fees-sd011
authority_id: CO-COUNTY-EL_PASO
legal_currentness: not_verified
---
# Independent El Paso English EHS lookup acceptance cases

These 25 cases were recorded from the accepted five-page source QA before reading or
executing the new adapter. The existing six-source CLI was read only to retain its
selection, JSON output and refusal conventions. This is source-based acceptance planning,
not a new blind transcription or independent legal review. The full source QA verifier
passed at preparation: 65 service rows, 37 context records, 74 grid rows/148 cells and all
8,060 native bytes. No new rendering or visual review is claimed here.

`EXPECTATIONS.json` is immutable. It includes complete expected source rows and clauses,
not just selected numeric strings. Its SHA256 is
`48ad71c545306aacf1be757862da8eb4cbc9d6c11e8f813dc01b9dc00d50e155`.
The four frozen source metadata files and old six-source interface identify the inputs.
The original PDF remains in the accepted repository QA package; it is not duplicated here.
The expectation verifier checks the frozen metadata/relations. It does not claim to replay
the original PDF or execute an unprovided adapter. Later execution receipts must be additive.

The cases require:

- Both first-system sale amounts (`$211.50 in 2024 ($368 in 2025)`) and the separate
  additional-system `$281.00 in 2024`, with no extension to another year.
- Context-only no-fee investigation and Section 2/civil-penalty results. The latter keeps
  “not more than,” the exception and “until the fee is paid in full.” Neither becomes a
  synthetic service-fee row or a calculation.
- The Retail Food Establishment License's statutory reference, without a dollar amount.
- The new-permit asterisk, all explicit numbered definitions and source exceptions.
  Equal amounts must not merge written and operational HACCP definitions. Residential/day
  treatment retains no invented routine-inspection link.
- All stacked event amounts, complete global notes and exactly 65 rows in full-list mode.
  A general-context query does not turn all associated rows into direct matches.
- No-match qualification; explicit and query-based current-law refusal; Spanish-source
  refusal without English fallback or a translation-equivalence claim.

The issuer is the County Board of Health and administrator is County Public Health.
Repository receipt at 2026-09-12T22:59:48.795762Z is distinct from the original unwitnessed
Sherlock acquisition. Printed approval/effective dates and the URL's 2025/06 segment remain
source claims, not verified current law. Previous acquisition/budget qualifications remain.

The intended existing CLI form is:

```sh
python /absolute/path/to/MasterLegalDatabase/scripts/research_source_lookup.py \
  --source-id el-paso-boh-ehs-fees-sd011 --query 'Property Sale' --format json
```

These commands are expected cases, not a claim that this source was already enabled.
Output field names may differ in a distinct typed adapter; comparison must preserve the
full source semantics and references without forcing an unrelated source's data shape.
For full-list case EHS-21, `directly_matched_context_ids` enumerates the required complete
context set, not a requirement that a future API call those contexts keyword matches.

Run the bounded expectation verifier without writing bytecode:

```sh
python -B /absolute/path/to/el-paso-ehs-lookup-independent/verify_expectations.py
```
