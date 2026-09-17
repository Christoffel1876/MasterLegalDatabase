---
status: complete_candidate_aware_source_fidelity_review_pending_atlas_acceptance
source_id: el-paso-boh-admin-regulations-sd011
review_kind: checked_passages
reviewer: Plato
legal_currentness: not_verified
answer_safe: false
---
# El Paso Board of Health administrative regulations: direct source review

Plato directly viewed all seven complete 300 dpi page images with `view_image`,
then read the unchanged native candidate and compared every substantive passage.
Four exact-pixel crops confirmed selected anomalies and the final paragraph's
scope. This is a candidate-aware internal review by the packet preparer, not a
blind review or independent model-family experiment. No Ebenezer output, new
Sherlock source findings, or Atlas reading notes were consulted. The external
review is not part of this artifact or its acceptance.

The source is the retained seven-page PDF with SHA256
`64d72ce1f7783dcf7fb5a3f6956e8ba4845c4839318613a1dee09d99716625d7`.
Issuer: El Paso County Board of Health; the cover also names El Paso County Public
Health. That board is distinct from the Board of County Commissioners. The review
covers the cover and Sections 2.1–2.11, all lettered and nested numbered items,
the unlettered final paragraph, heading markup and seven repeated footer dates.
There are no tables. All 78 checked passages and 894 raw native lines are recorded;
all 19,118 native bytes and the 19,272-byte packaged candidate remain unchanged.

No substantive candidate correction was identified. The reviewed transcript
normalizes whitespace only; raw native text and half-open byte spans remain
separately auditable. Source anomalies are deliberately preserved:

- Section 2.4A says **general and permanent affect**.
- Definition 2.7F says **EXECITOVE DIRECTOR**.
- Section 2.10F says **said real property in compliance**.
- The final emergency paragraph has no printed letter Q and is separate from P.

The repeal statement retains its “except as provided below” qualification and
following saved-action clause. The certificate provisions distinguish thirty (30)
calendar days prior from thirty (30) days after notice, and preserve “may, but is
not required.” All administrative-procedure exclusions, hearing-notice periods,
conditional effective-language, “if feasible,” and emergency conditions/three-month
limit remain attached to their full paragraphs. No deadline arithmetic or legal
interpretation is supplied.

The repeated **5/23/2012** footer is unlabelled. **January 21, 2009** is printed in
the prior-regulation cutoff clause, with its exceptions. Neither is certified as
this document's adoption/effective date. The document's operative status,
subsequent amendments, current cited statutes and present applicability remain
unverified. Source-fidelity acceptance would not make it answer-safe current law.

`SOURCE_QA.json` and its strict exported schema are the primary machine-readable
review. `REVIEWED_TRANSCRIPT.md` is the complete readable whitespace-normalized
transcript. `INSPECTION.json` records actual image use and its limits;
`INSPECTION_WORKING.md` is an earlier note whose “crops pending” statement is
superseded by the final inspection. The failed initial crop constructor produced
no image and is disclosed there; successful exact pixel-slice recipes are retained.

Original acquisition remains a received-review-package claim. Actual repository
intake is receipt-bound to 2026-09-12T22:59:48.795762Z. Historical supplied URLs,
HTTP times and pre-intake null statements are not rewritten or promoted. Only
selected custody inputs are copied; this is not a complete upstream packet audit.
The source PDF, seven images and seven per-page native files are self-contained;
no external handoff is needed for normal verification.

Run the read-only validator from any directory:

```sh
PYTHONDONTWRITEBYTECODE=1 "/Users/mcoors/Documents/Project Geode/.geode-venv/bin/python" -B "/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-16/plato-direct-review/verify_review.py"
```

Add `--rerender` to reproduce all seven Poppler PNGs in an automatically removed
temporary directory. This optional check requires the same recorded renderer
binary, with `--pdftoppm` available for an explicit path. Normal validation needs
Pydantic 2, jsonschema and PyMuPDF only. Builders must not be rerun over this frozen
review. The 12 focused tests reject content/exception/anomaly changes, missing
footers, wrong paragraph nesting, candidate/image changes and legal-date or HTTP
provenance promotion. Mechanical checks cannot independently authenticate the
reviewer's visual attestation or prove legal validity.
