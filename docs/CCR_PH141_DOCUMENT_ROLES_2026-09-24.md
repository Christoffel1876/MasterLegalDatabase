---
title: PH141 document roles — September 24, 2026
status: scoped_documentary_observations
legal_currentness: not_verified
answer_safe: false
---

# Distinguishing retained files from substantive rule text

Eight complete PDFs in the [PH141 source package](CCR_PH141_RESEARCH_2026-09-24.md)
were read from their page images and compared with their unchanged native text.
The [document-role inventory](audits/CCR_PH141_DOCUMENT_ROLES_2026-09-24/ROLES.json)
records their documentary roles separately from collection and extraction status.

| Observed document role | Retained rule IDs | PDFs | Pages |
|---|---|---:|---:|
| Editorial navigation and/or history | 2404, 2405, 2406 | 3 | 10 |
| Editorial repeal notice | 2408 | 1 | 1 |
| Editorial recodification notices | 2937, 2938, 2939 | 3 | 3 |
| Substantive regulation text present | 2407 | 1 | 10 |
| Not yet reviewed for document role | 2930–2936, 2943, 2944 | 9 | 859 |

Seven reviewed PDFs therefore contain notices or history, totaling 14 pages.
One ten-page PDF contains substantive provisions. The remaining nine PDFs have
**unknown roles**, not assumed absence of substantive text. The 17 PDFs still
represent only selected documents within the agency's 53-row retained listing.

The observations apply to these exact PDF hashes and versions. An editorial
notice can point to separate substantive rule parts; a whole-file download does
not establish that all those parts were collected. “Substantive text present”
also does not mean all incorporated material is present or that the document
is currently applicable. A repeal or recodification notice is identified by its
content, without a new determination of legal effect.

## Evidence and limits

Ptolemy, Plato and Atlas reviewed complete source images before comparison with
native pages. Their separate records preserve source anomalies, uncertain glyphs,
layout differences and corrections to preliminary visual readings. No confirmed
substantive candidate error was identified in these scoped comparisons; that is
not a guarantee of perfect transcription. The native package remains
`machine_extraction_unreviewed`, and `answer_safe` remains false.

The inventory binds each PDF's original hash, physical page count, source citation,
listing/history title, version and URL to the existing public capture. Its schema
keeps unreviewed roles null. CI checks these source associations, exact role/page
totals and provenance pins. Automated verification checks bytes and associations;
it cannot reproduce the reviewers' visual judgments or establish current law.

The three files in `review-manifests/` are provenance-only copies identifying
separately retained review packages. Their listed payloads are not bundled here
and are not required at private filesystem paths. The existing public source
PDFs remain the authority. No originals, source indexes, native text, completion
flags or daily monitoring settings were altered for this inventory.

Inventory SHA-256:
`01803cee71f8eba8c31476d8569535c3351414c35594fbc7306cdc6cb55ab213`.
