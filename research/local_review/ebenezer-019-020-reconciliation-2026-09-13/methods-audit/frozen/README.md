---
title: EB019 and EB020 custody and methods audit
status: custody_verified_methods_qualified_pending_root_disposition
review_date: 2026-09-13
public_requests: 0
direct_visual_pages_reviewed: 0
legal_currentness: not_verified
---
# EB019 and EB020 custody and methods audit

The retained files pass the identity checks. Both original PDFs, all eight full-page PNGs and
both candidates match the unchanged source-packet manifest. All eight native page slices
reproduce exactly with PyMuPDF 1.28.2, `get_text("text", sort=False, flags=195)`. This establishes
current local byte identity and reproducibility, not the accuracy of the words, source layout,
historical worker access or legal currentness.

| Assignment | PDF SHA-256 | Pages | Candidate SHA-256 |
|---|---|---:|---|
| EB-PDF-019 | `2ba9073aa06420e41a5dce98fade56278df96729630f5d61d3ab1c910e839eb0` | 5 | `2ba00b91a33612e279a0553f5e573af795df27a11329d695ea307ea78ae2dfee` |
| EB-PDF-020 | `852801c5ad0056c7b0dde6300e66e86f2e4235ce0efc16471d5210d74aa17ed3` | 3 | `e54c8a008fe12cdb6704851c1009afab1c5d9186d6aff90c5fcc63e85b36f67a` |

All 150 files in Root's received-package receipt were rehashed successfully before this audit.
The methods tar contains seven ordinary files and one directory, with no traversal, duplicate
members, links or special files. All six content hashes listed in its inventory match; the
seventh file is the inventory itself. Its clarification is byte-identical to the loose delivery.
Five supplied Task-input JSON extracts are retained exactly, with separate hashes of each prompt
string and explicit attachment counts. No parent agent transcript was delivered in this subset.

## What the clarification resolves

The initial clarification says exact delegated prompts were unavailable as saved attempt files.
Its later addendum supplies five Task-input extracts located in an existing transcript. These
are an additive delivery; the earlier statement must remain visible. Their byte identities are
verified, while origin and extraction timing remain supplied claims.

The saved Task text contains instructions and attachment paths, not page-description prose.
The clarification attributes the executor's extra descriptions to attachment mediation and
Cursor Read, rather than Atlas-authored activation. The actual automatically supplied attachment
context is not reproduced in these Task extracts. Its unknown supplier and unseen contents
remain unknown.

The original PDFs were reported absent and unopened in both worker directories. The workers'
PDF hashes were declared from source identities, not local PDF rehashes. They reported using
page images through caption mediation. This audit's successful PDF check does not rewrite that
historical limitation.

## What remains qualified

Both Pass2 workers explicitly report that they did not open the full packet manifest. Their
Task prompts supplied expected candidate hashes computed by the coordinator. The activation
required a post-freeze manifest identity lookup. The candidates now match that manifest, but
this audit does not certify that the historical procedure was followed.

EB019 discloses an interrupted earlier source view and possible recollection. Its frozen first
pass includes paraphrased and unchecked spans. EB020's Pass2 prompt supplies spelling uncertainties
from Pass1. These are assisted, candidate-aware comparisons. They are not direct pixel inspection,
new blind passes, independent model-diversity evidence or complete verbatim source certifications.
EB020's two tool-output files are inventories of reported caption use; they are not full verbatim
caption-response transcripts. Delivered crop images do not alone prove what an executor saw.

Reported all-page coverage means every expected page was represented under the declared assisted
method. It does not establish that every region, glyph, exception or table relationship was
checked. Reported freeze/release times, filenames and filesystem timestamps do not independently
prove unseen chronology or the chat-hash release gate.

The activation's final paragraph says no bot delegation is authorized; the clarification reports
separate executor-subagent Tasks. Root should reconcile that wording with the internal executor
workflow. No separate exception is evidenced here, and this audit does not infer unseen permission.

## Visual disposition remains with Root

Root has independently rejected EB020-P2-001 through EB020-P2-004 because `Temproary`, the clipped
`if applicab`, `Transportion` and `Phenophthalein` are source print rather than candidate errors.
That decision was supplied to this audit by Root's task instruction. This audit does not repeat,
override or independently substantiate those pixel findings from text. The external report is
retained unchanged. No corrected source transcription, adoption finding, coverage promotion or
canonical review-status change is proposed here.

`METHODS_AUDIT.json` contains the bounded typed proposal, exact page/candidate/native bindings,
all prompt identities and nine separate custody/method/disposition observations. `received/`
contains immutable external report/caption/crop copies and the tar plus safely retained members.
`source-evidence/` contains only the two relevant source PDFs, page PNGs, candidates and native
receipts; the original manifest's EB018 source payload and unrelated custody are explicitly excluded.

```bash
/path/to/python -B validate_audit.py
```

The verifier is portable and read-only. It checks the closed inventory, safe tar structure,
report/source/page/candidate hashes, declared prompt bindings and native reproduction. It makes
no network request, imports no external reviewer code and does not inspect source wording visually.
