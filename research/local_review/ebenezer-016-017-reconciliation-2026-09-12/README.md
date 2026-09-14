---
title: Independent EB016–017 integration audit and superseding title disposition
status: accept_with_superseding_correction_attached
legal_currentness: not_verified
answer_safe: false
---

**The repeated EB016 title is visible on all three supplied page images.** The
historical root reconciliation incorrectly rejected its visibility on pages 2 and
3. The parent reviewer accepted this independent finding and withdrew that
correction before integration. This directory preserves the complete 116-file
historical packet unchanged and supplies a separate, explicit superseding decision.
Do not present the historical packet's visibility correction as accepted evidence.

`SUPERSEDING_DISPOSITION.json` withdraws the conclusion of `ATLAS-EB016-014`, the
not-visible assertions in `ATLAS_ADDITIONAL_FINDINGS.json`, and the corresponding
README paragraph. It retains the original baseline's visible title classification,
all native text, source images and source table associations. It does not silently
edit or delete the mistaken record.

## Evidence and scope

This was candidate-aware independent Atlas QA. All five full 300 dpi page PNGs
were directly inspected at the tool's displayed 1376 × 1780 size; the source files
remain 2550 × 3300. The repeated title was immediately visible at the upper right
of EB016 pages 2 and 3. The source tables were compared with their existing explicit
row and cell records. No external tool history or blind-review independence was
certified.

The three exact header crops supplied by the parent are preserved in
`header-crops/`. Each is reproduced by selecting RGB pixels from **[1450, 90,
2400, 270)** in the corresponding complete image. Each crop is 950 × 180 and has
SHA256 `9d4bcab6286a4da98c71cdee2261a498aa521e5ce1870b3295c1c86080b6325a`.
All three crops are byte-identical, with 7,602 pixels whose RGB sum is below 660.
The second crop was also directly viewed. Pixel identity supports the comparison;
the title reading is a human/model image observation, not an OCR or threshold
inference. This finding is about these exact supplied renders, without a claim
about every possible renderer.

The historical validator passed its 33 dispositions, 42 supplied crop hashes,
7,191 EB016 native bytes, 1,316 EB017 native bytes and existing table checks. That
success did not validate the mistaken visual judgment. The other 32 dispositions
remain supportable within their stated source and uncertainty limits:

- EB016 retains 30 fee rows: 7 Police, 7 Fire, 4 Park, 4 Trails, 1 Storm Drainage,
  and 7 Transportation rows. The Police Retail/Restaurant row is $1,004 / -2.09% /
  $983, with `1,000 Sq. Ft of Building`. Residential descriptions span the first
  two columns. Page 3 retains its own `1,000 Square Feet of Building` wording and
  references the page-2 year/change column headings; the running title is a
  separate, visible header. The EAF grid's last Weight cell stays blank. No
  percentage, rounding or fee calculation was recomputed.
- EB017 retains two separate tables, seven tap-size rows and one Single Family row,
  with all 24 data cells. Exactly four amount cells visibly carry dollar signs.
  Equal amounts in two separately labeled rows do not establish equal applicability.
  The body phone 350-9801 stays distinct from footer phone (970) 350-9811 and fax
  (970) 350-9805. The notice's March 1, 2021 effective language remains conditional
  on adoption. Greeley is the issuer; the Weld County contractors are addressees.

The EB017 receipts claim `PASS1_NOTES.md` SHA256
`7281e862de45bb81a816770e4cc363fbbda9ed09c739ff5c6d81bacf075c9e9e`.
Those bytes are absent from this packet and remain unverified. No replacement was
created. The external crops have supplied hash identities but no coordinate files
or tool histories. Their sequence, creation times and caption contents remain
reviewer claims. The new header crops are clearly disclosed later audit derivatives,
not reconstructed historical external-review crops.

## Validator improvement and reproduction

`verify_integration.py` is an additive, read-only wrapper. It pins the historical
manifest and checks its entire closed inventory **before** launching the frozen
validator in a separate `-I -B` Python process. Thus the wrapper preflights the
Python model file that the old validator imports before doing its own checks.
It also rejects unexpected empty directories and symlinks.

The old validator validates the Supplement schema and line anchors, but not the
`TitleArtifact` native/candidate/image relationships. In a temporary copy, changing
the first native start offset to -1 and updating only the inventory identity still
returned `passed`. The temporary copy was removed; no historical file was changed.
This is an internal consistency gap, independent of the mistaken visual judgment.

The wrapper requires exactly pages 2 and 3, replays native extraction with PyMuPDF
1.28.2 (`flags=195`, `sort=False`), checks valid byte bounds, the exact title and its
SHA256, candidate offsets relative to each page origin, and the correct full-page
image identity. Seven in-memory mutations of these fields are rejected. It also
resolves activation, source-only identity and page-image receipt bindings that the
old validator does not explicitly cross-check. None of these automated checks can
certify a visual judgment or authenticate external chronology.

```bash
PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-status-venv/bin/python -I -B \
  '/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-12/ebenezer016-017-integration-audit/verify_integration.py'
```

Copy this whole directory and use the copied script path for portable validation.
Dependencies are Python 3.11+, Pydantic 2, jsonschema (used by the frozen validator)
and PyMuPDF 1.28.2. Exit 0 means the historical integrity checks and additive
correction bindings pass; it does **not** reinstate the withdrawn claim. Errors
return exit 1. No repository imports, historical absolute-path opens, network
requests or evidence writes are performed.

Integrate only with this superseding disposition attached and discoverable before
the erroneous historical findings. Do not propagate the not-visible labels into
source lookup or rewrite the original baseline. No adoption, amendment-chain
completeness, operative fees, current law or coverage promotion is established.
