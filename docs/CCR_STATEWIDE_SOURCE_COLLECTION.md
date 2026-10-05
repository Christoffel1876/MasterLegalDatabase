---
title: Expanding CCR source collection beyond the initial department
date: 2026-09-23
status: reviewable_implementation
---

# CCR source collection across departments

The collector and review-candidate publisher support an explicitly selected SOS
department. Collection preserves the official catalog, agency listings, rule
version pages and linked source-designated current/future documents. It produces
typed evidence separately from canonical legal text. A completed traversal is
coverage of that observed department catalog, not a legal-currentness determination.

Use the SOS `deptID` from the official numerical catalog. Internal agency registry
codes and the numerical prefix in a CCR citation are different identifiers and
must not be substituted for it.

```bash
python -m geode.pipeline.ccr_current \
  --root /absolute/path/new-evidence \
  --department-id 15 \
  --report-dir /absolute/path/new-report
```

The default is 300 source objects per department. An operator can explicitly use
`--max-sources 1000` for a larger department. The hard ceilings remain 1,000 source
objects, 150 MB for the department and the existing 15 MB per response. A bound or
source-validation failure does not create a successful department inventory.
Every failed attempt should remain in its own report directory; use an explicit
new acquisition plan for a retry.

## Preserve separately published source series

Some SOS departments have repeated numerical catalog headings, and some CCR base
citations are published as several separate source series. The collector checks
every declared catalog-heading copy and requires complete agency agreement.
An explicit empty agency result is accepted only with the matching official
breadcrumb and complete observed empty-result structure. A missing table alone
never means empty, and a previously collected rule disappearing still stops the run.

For each series, the listing label must equal the URL's `seriesNum`, match the
displayed rule title, and agree with every PDF/Word handler filename. Labels are
bounded literal data; no source JavaScript is executed. For example:

| Source label | Evidence identity |
|---|---|
| `8 CCR 1502-1` | `8_CCR_1502-1` |
| `10 CCR 2505-10 8.000`, SOS rule 2917 | `10_CCR_2505-10__rule_2917` |
| `7 CCR 1101-3 Rules 1-17`, SOS rule 3102 | `7_CCR_1101-3__rule_3102` |

Ordinary identities are unchanged. The `__rule_` identity distinguishes the SOS
source series; it does not infer a new legal section identifier. The entire source
label, SOS rule ID and source URL remain in the record. Unsupported or disagreeing
labels stop the department instead of silently collapsing into the base citation.

## Review-candidate publication

The publisher's `prepare`, `build` and `publish` commands accept `--department-id`.
Omitting it retains department 12 and its existing branch. Other departments use
`codex/ccr-current-department-ID-update`, so proposals cannot overwrite each other.
The selected department is bound into preparation, candidate and exact report
metadata. Historical candidate artifacts without those bindings must be rebuilt.

Only the selected inventory/state, checked content-addressed originals, and
legitimate selected-state preimage snapshots are permitted. The publisher replays
the catalog and version metadata from preserved bytes before accepting a proposal.
Current/future/repealed labels, cutoff dates, adopted dates and effective dates
remain separate source observations. A proposal is never automatically merged.

The GitHub schedule remains limited to its existing department-12 configuration.
Supporting other departments does not claim that they are already scheduled or
healthy. Expand scheduled scope only after reviewing acquisition results and the
resulting proposal volume.

## Research text and search

The separate [CCR source-text bridge](CCR_SOURCE_TEXT.md) creates portable native
PDF page packages from pinned collector inventories. It provides literal phrase
and exact source-citation lookup, with complete physical pages and original hashes.
It labels all new text unreviewed and explicitly reports unsupported Word formats.
Native text can flatten redlines or lose layout, so source lookup never certifies
operative legal text, applicability or absence of a requirement.
