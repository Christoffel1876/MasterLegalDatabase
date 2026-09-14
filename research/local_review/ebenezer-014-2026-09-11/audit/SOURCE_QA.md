---
title: "EB014 seven-page source and candidate QA"
reviewed_at: "2026-09-11T19:16:34.268333Z"
source_id: "fort-collins-land-use-article-1-sd005-07"
assignment_id: "EB-PDF-014"
status: "seven_page_candidate_aware_source_qa_complete_pending_parent_integration"
review_mode: "candidate_aware_not_blind"
external_review_consulted: false
legal_currentness: "not_verified"
---

# EB014 seven-page source and candidate QA

All seven complete page images and ten focused source crops were inspected against the frozen native candidate. No substantive word or number correction was identified. All 13,579 native UTF-8 bytes are preserved unchanged in `SOURCE_QA.json` and seven `page-NNNN.original-native.txt` files. This is candidate-aware Atlas QA: the reviewer prepared the packet and had previously seen its source images. No external EB014 report was consulted.

The strict typed review contains 29 observations, 36 exact native/candidate byte spans, 27 exhaustive native chunks, ten crop identities and all twelve actual PDF link annotations. It distinguishes visible wording, non-visible extracted text, image-only words, layout and source anomalies. No candidate, original PDF, packet, repository record or legal text was edited.

## Physical and printed pages

| Physical page | Visible role | Visible printed page label | Extracted label |
|---|---|---|---|
| 1 | Cover | None visible | 1-0, not visible |
| 2 | Accessibility instructions and artwork | None visible | None |
| 3 | Table of contents | None visible | 1-1, not visible |
| 4 | Division 1.1 organization | 1-1 | 1-1 |
| 5 | Division 1.2; purpose A–L | 1-2 | 1-2 |
| 6 | Purpose M–N; authority; applicability | 1-3 | 1-3 |
| 7 | Applicability continuation; minimum standards; Division 1.3 | 1-4 | 1-4 |

The cover's article banner is visible; its extracted footer is not. On the contents page, neither the extracted recurring banner nor footer is visible. Full images and targeted crops confirm these distinctions. The review preserves those bytes but excludes them from its separate visible-order references. On substantive pages, the native stream places the footer before the header and body; visible order is header, body, footer. The cover also extracts General Purpose and Provisions before the large ARTICLE 1, reversing their visible order.

## Findings and qualifications

- The City of Fort Collins wordmarks on pages 1 and 2 are image content, not independently extracted logo text. Their wording is recorded separately with source-image hashes and regions. The accessibility symbol, border and photograph are separate graphic observations; no caption, photograph date, building identity or person identity was invented.
- All accessibility instructions, phone numbers, email and displayed link labels match. The PDF contains three actual URI annotations and nine internal contents links. Their targets are preserved as annotation metadata, distinct from printed wording; none was opened. No clickable destinations were invented for the final two contents entries.
- Contents entries and body section numbering match. Article 7's title uses the singular **Definition**. The seven-article inventory does not mean those other articles were reviewed.
- Purpose items A–L continue with M–N on physical page 6. M has no terminal period in the source. Preserve the following qualification: purpose statements are generally not binding standards, subject to the source's explicit-reference and contextual limits, including Sections 1.2.4, 6.8.2 and 6.14.4. Do not detach the list from that qualification.
- Physical page 6 visibly prints **“interpretation - 4 - and application”** inside a sentence. The token is an actual source anomaly, not solely a footer displaced by extraction. It was not deleted.
- The applicability material retains municipal boundaries, express exemptions, the Chapter 14 landmarks example, prior-approval language, purpose/policy qualifications, all listed conformance actions and the plan/permit distinctions. Its ongoing-use paragraph continues at the top of physical page 7 before section 1.2.5.
- Physical page 7 visibly reads **“Articles 2, 3, or 4 a standard”** without a conjunction. The same page uses lowercase **“it”** after **“the City.”** Both are preserved without editorial repair. Conflict subsections A and B, their conditions and the full severability paragraph remain intact.

No visible edition, adoption or effective date was identified in these seven pages. Adoption-by-reference and other legal statements are preserved as source wording, not independently established facts. This review does not establish currentness, adoption, applicability or complete amendment history. Exact typographic Unicode identity, design intent and an exhaustive font-style inventory are not certified.

## Verification

Strict Pydantic and exported JSON Schema validation passed before the record was written. A read-only verifier checked 35 file identities; source/candidate hashes and sizes against the frozen packet; exact equality with the canonical raw PDF; seven fresh native re-extractions; all page, chunk and observation byte bindings; complete disjoint native partitions; and reproduction of all ten crop images. All twelve PDF links reproduce from the original's annotations. These outputs reference existing local packet/canonical paths and are not a standalone bundle of upstream custody evidence.

- Source SHA256: `555a05553af57619c818c5b9ab90d1b751e161a307d8bb65fc73141991a73d2a`
- Candidate SHA256: `a31bfdec7d300e43690236b7fdacd9dd89c9f431fc48fe9077e9ae09c13a1105`
- Typed review SHA256: `29a0370d6e7a0f968b75140740ca8856d936f15eeab445e87d9e125db494ae84`

Revalidate without changing outputs:

```sh
PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-register-ci-venv/bin/python \
  handoffs/atlas-reviews/fort-collins-land-use-article-1-sd005-07/pre-review-2026-09-11/build_review.py --verify
```
