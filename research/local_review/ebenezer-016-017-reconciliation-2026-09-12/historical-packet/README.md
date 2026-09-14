---
title: Atlas reconciliation of Ebenezer Greeley reviews 016 and 017
status: reconciled_with_qualifications
legal_currentness: not_verified
---

# Result

The two assisted reports are preserved and reconciled against five directly viewed
full-page images and the unchanged native candidates. The 33 claim dispositions
include source agreements, layout qualifications and uncertainty; they are not
33 confirmed extraction errors. All prior source reviews remain unchanged.

For **EB016**, the Police Retail/Restaurant row clearly reads **$1,004 / -2.09% /
$983**, with `1,000 Sq. Ft of Building`. The competing captions are unsupported.
Residential descriptions span two columns. The EAF grid and Transportation table
need their explicit row/column associations; raw native sequence alone is unreliable.
All 30 fee rows remain as printed, without arithmetic corrections.

A new check also found a mistake in both the external report and the older Atlas
baseline: the repeated title is present in native text on pages 2 and 3 but **is
not visible in the checked full-page renders**. The additive findings file binds
those exact native spans and qualifies the old visibility flags. Its cause is
unresolved. Neither the old records nor native text has been rewritten.

For **EB017**, all seven tap-size rows and the separate Single Family row agree
with the source. The logo, footer contact line and motto are omitted from native
text but preserved as image evidence. The footer phone is a different printed
number from the body phone. The City of Greeley is the issuer; Weld County
contractors are the recipients. The notice explicitly conditions its effective
date on adoption; this remains a proposed notice, not proof of current fees.

# Custody and limits

`RECONCILIATION.json` binds the two reports, completion receipts, original PDFs,
full page images and frozen baseline reviews. `ATLAS_ADDITIONAL_FINDINGS.json`
qualifies the old visibility error. `supplemental/` retains the actual supplied
EB016/017 crop files. Its original inventory also names EB015, which is outside
this packet's scope. No coordinate files or tool histories were supplied; crop
custody does not authenticate the reported sequence or caption contents.

The EB017 receipt claims a hash for `PASS1_NOTES.md`, but those bytes were not
supplied. They are recorded as missing, not reconstructed or marked verified.
Both source PDFs are present and hashed by Atlas, although Ebenezer reported the
EB017 PDF absent from its own work directory. All external timestamps remain
reported chronology. Atlas's review is candidate-aware, not blind.

The verifier checks the closed inventory before loading the frozen source-specific
semantic validators, replays native extraction and source table associations,
checks all report line references and supplied crop hashes, then rechecks bytes.
It uses package-relative copies and does not open historical absolute paths.
It validates custody and structure; it does not certify visual judgments by code.

```sh
PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-status-venv/bin/python -I -B \
  '/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-12/ebenezer016-017-atlas-reconciliation/validate_reconciliation.py'
```

No canonical record, old review, source PDF, candidate, ledger or raw archive was
changed. Currentness, later adoption and applicability remain unverified.
