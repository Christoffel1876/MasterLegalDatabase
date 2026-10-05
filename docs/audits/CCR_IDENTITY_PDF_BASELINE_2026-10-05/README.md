# Retained CCR catalog identity-to-PDF baseline — October 5, 2026

The exact retained catalog identity set has **1,156 identities across all 25 listed departments**. Each identity is bound to an original PDF and a native physical-page ledger. The exact PDF union contains **1,156 PDFs and 39,460 physical pages**. Of these identities, **1,155 have both PDF and Word sources**. These are whole publisher rule identities, not normalized legal sections or a claim that every identity is operative law.

| Retained source basis | Identities with PDFs | Identities with PDF/Word pairs |
|---|---:|---:|
| Prior 23 departmental inventories | 876 | 876 |
| Public Health source listings | 238 | 238 |
| Transportation source listings | 42 | 41 |
| Total | 1,156 | 1,155 |

`IDENTITIES.jsonl` binds every department/agency/rule selector to its literal source-history URL, selected source-version ID, original document URL, exact bytes and SHA-256, and physical-page count. Each row pins its source inventory or capsule manifest. The source cutoff claims are mixed: August 13 and August 29, 2026. Transportation's separately observed partial PDF has no independently assigned cutoff claim.

The only remaining PDF/Word pair gap is **Transportation / agency 124 / rule 3475 / version 12137, 2 CCR 601-27**. Its exact official PDF parses to 10 pages. The official Word handler returned HTML; the source-documented alternate route returned an empty Word body. A different eDocket part is not a substitute.

The verifier replays the earlier source-coverage audit, independently strengthens department 12 through the maintained publisher's complete source-byte validator, and proves that the original 20-rule Public Health V1 capsule and its V2 native bridge preserve the exact URL-to-body mappings. It reconstructs the source identity set, rejects duplicate/missing/foreign selectors, compares every declared binding with source metadata, hashes every retained PDF and Word original, checks Word signatures, and parses every PDF to compare physical-page counts. The PDF SHA-256 set must exactly equal the union of the seven pinned native ledgers; matching totals alone cannot pass.

The identity verifier does not re-extract all native text. Native page sequences and text hashes come from the pinned ledgers and their separate package verification. Native extraction remains unreviewed. This audit does not establish source-fidelity review, current legal effect, cross-reference completeness, incorporated material coverage, all historical versions, or all state authority layers. It does not change the existing 23/25 department publisher-completion flags, and both `answer_safe` and `whole_state_complete` remain false.

From the repository root, after copying the proposed files unchanged:

```sh
PYTHONPATH=. python -B scripts/verify_ccr_identity_pdf_baseline.py \
  --root . \
  --index docs/audits/CCR_IDENTITY_PDF_BASELINE_2026-10-05/INDEX.json \
  --index-sha256 27f7856e772dd9cbd1c54c95a5092efd9b6d73570011d2363f2395d29ad8c19c
python -B -m pytest -q -p no:cacheprovider tests/test_ccr_identity_pdf_baseline.py
```

The local replay passed with exactly 1,156 identities, 1,155 paired identities, 1,156 distinct PDFs and 39,460 pages. All 22 targeted tests passed. Verification is offline and read-only.
