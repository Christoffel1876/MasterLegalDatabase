---
title: EB015 external-review reconciliation and local integrity audit
source_id: greeley-building-fees-sd008-06
assignment_id: EB-PDF-015
status: external_review_reconciled_with_qualifications
legal_currentness: not_verified
answer_safe: false
---

This package preserves the Greeley building-fee source, unchanged native candidate,
prior Atlas source review, and Ebenezer's two external reports. The original
`RECONCILIATION.json` records 19 dispositions: ten findings, three errata, and six
unresolved themes. They are **not 19 OCR errors**. The decisions and all 13 original
copied inputs remain unchanged.

The parent Atlas reviewer directly inspected the complete supplied page and an
existing major-review crop, with prior candidate and source-review knowledge.
Ebenezer describes a caption-mediated procedure. This package does not call either
review blind, authenticate the remote execution history, or turn captions into
source quotations. The additional validator performs byte and reference checks;
it does not repeat or replace the parent's visual judgments.

## What is preserved and checked

- `source/`: exact one-page PDF, complete 2550 × 3300 PNG, and 3,349-byte candidate.
- `baseline/`: unchanged source QA, exported schema, narrative and major-review crop.
- `reports/` and `authorization/`: exact reports, receipts and authorization context.
- `RECONCILIATION.json`: the parent's qualified decisions, linked to exact report
  lines including their original newline bytes and to named source spans.
- `provenance/`: additive exact packet-manifest and schema, native extraction record
  and schema, frozen raw manifest, intake receipt, source provenance, official
  referral HTML, and already-derived public response headers.
- `supplemental/`: three supplied notes/inventory files and only the 19 EB015 crops.
  `SUPPLEMENT_RECEIPT.json` records their actual local custody time and byte identities.
- `VALIDATION_RECEIPT.json`: the separate local integrity findings.
  `FINAL_MANIFEST.json` closes every regular file except itself, including its schema.

PyMuPDF **1.28.2**, `Page.get_text("text", flags=195, sort=False)`, reproduces the
3,236 UTF-8 native bytes exactly. These occupy candidate offsets **56:3292**; the
surrounding physical-page markers are packaging, not printed source text. All 29
contiguous source spans cover those bytes once. Source order remains a separate
permutation, preserving the displaced sales-tax and temporary-electrical headings
without rewriting native bytes. Items 1–4 link to footnote 1; item 5 links to
footnote 2. All five links and every decision's report-line hash are checked.

The source PDF SHA256 is
`fa8a90dae00525c2dcb62ef4d69aeb84b7032a0fd2dc64f45c1685981e9becd4`.
The candidate SHA256 is
`aec7efa7edbd9e26a8ce7bbd9685431c386043fc074567a1b3db334e9f528334`.
The unchanged native slice SHA256 is
`35f7b7448e487369c1874fc31ec7292fe6c9c4bc6210abcac4cac2face620dff`.

## Later crop receipt and remaining limits

The original reconciliation was recorded at **2026-09-12T22:17:02.912816Z** and
states that external crops had not yet been supplied. A later delivery includes
all nine reported Pass 1 crops and all ten reported new Pass 2 crops. They match
the supplied hash inventory and decode as images. This is an additive update to
that historical availability statement; the original decision record is unchanged.

The sender's **2026-09-12T22:21:11Z** supplemental creation time remains a supplied
claim. The receipt separately records the actual local copy time. The accompanying
notes report no separate coordinate or tool-log files found under the remote
work directories. No historical crop was recreated here. Exact crop-to-page
coordinates, remote creation chronology, caption outputs, and claimed tool actions
remain unauthenticated. This intake does not add a visual interpretation of the
new crops. Shared notes mention EB016/017, but their crops and review content are
outside this package's validation scope.

The local provenance copies resolve the selected EB015 manifest and receipt
bindings. Complete multi-record manifests are retained for custody, **not as a
claim that every contained source or row was validated**. Historical absolute paths,
including remote `/workspace` paths, are recorded claims and are never opened by
the portable validator. The existing 38-row raw-manifest snapshot and source
provenance are checked at their exact selected line numbers and line hashes.
Other documents, packet support files and rows remain outside this audit.

The source's 2024 title, “Effective -2024” heading, and unlabeled 8/18/2026 footer
retain their distinct roles. The footer is not newly characterized as an adoption,
effective or revision date. Original HTTP acquisition is not independently verified
here; the frozen provenance retains a null canonical official source URL, a
reported Sitecore URL, an official referral, and a separate repository receipt time.
No source update, legal applicability, amendment completeness, fee arithmetic or
current-law certification is made. The terminal horizontal mark and fine typography
remain qualified as recorded; no character was inserted into the candidate.

## Offline validation

Run with Python 3.11+ and installed Pydantic 2, jsonschema, and PyMuPDF 1.28.2:

```bash
PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-status-venv/bin/python -I -B \
  '/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-12/ebenezer015-atlas-reconciliation/validate_reconciliation.py'
```

After copying this entire directory, use the copied validator path and an equivalent
Python environment. No repository imports, network access or historical-path
resolution is required. Validation returns JSON and exit 0 on success, or a clear
error and exit 1 on failure. It writes no files, rejects symlinks and unexpected
files or directories, and checks the closed inventory before and after replay.
Its hashes detect changes against this frozen package; they are not a digital
signature or independent authentication of the sender.
