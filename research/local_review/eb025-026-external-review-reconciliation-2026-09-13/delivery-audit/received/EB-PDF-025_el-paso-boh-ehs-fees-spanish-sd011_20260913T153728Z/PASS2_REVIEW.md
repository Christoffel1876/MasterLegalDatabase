# PASS2_REVIEW — EB-PDF-025

assignment_id: EB-PDF-025
source_id: el-paso-boh-ehs-fees-spanish-sd011
authority_id: CO-COUNTY-EL_PASO (collection identity only)
language: Spanish
packet_manifest_sha256: ace3738bac6375b17f01ae0c4390350d5aeeacb1b9473838c57832dcd09427f5
start_here_instruction_sha256: 12524a2fbc521477374f665228e0b5371649d529ba51338d32bf003b4d7f5a5d
attempt_dir: EB-PDF-025_el-paso-boh-ehs-fees-spanish-sd011_20260913T153728Z
legal_currentness: not_verified
review_method: caption_mediated_source_first
scope: Spanish source fidelity — not an English translation comparison
utc_pass2: 2026-09-13T15:40:50Z

## Gate checks

| Check | Result |
|---|---|
| Pass1 freeze before candidate | PASS — freeze SHA `ee248e440c867a5ad34379ddef45f4b769727c02228b7482cb97b5d4f470691a` at 15:39:10Z; release 15:39:33Z |
| Manifest opaque match | PASS — `ace3738bac6375b17f01ae0c4390350d5aeeacb1b9473838c57832dcd09427f5` |
| Candidate identity (unchanged vs manifest) | PASS — `2f5afec19de94a36328fdaa6281724e02334dc69720a2af67bc29c7d60044fa0` |
| Source original.pdf / page SHAs | unchanged vs SOURCE_ONLY / Pass1 table |
| Every page re-opened in Pass2 | PASS — fresh Read captions on pages 1–6 after release (plus parallel Task reopen) |

## Pass2 method

- Re-opened all six source PNGs via Cursor `Read` after candidate release (caption-mediated).
- Compared frozen Pass1 associations and candidate.txt Spanish content to re-opened captions.
- Did **not** use English packet / translation comparison as the fidelity standard.
- Originals preserved; freeze not rewritten.

## Findings

### Critical (1)

| ID | Loc | Issue |
|---|---|---|
| EB025-P2-001 | p2 lead §A | Candidate garbles lead as `A p` / `artir del 1 de enero de 2024` (hard line break mid-word). Pass1 caption and Pass2 reopen expect continuous **A partir**. Treat as extraction/packaging defect in candidate. |

### Minor (6)

| ID | Loc | Issue |
|---|---|---|
| EB025-P2-002 | all footers | Candidate renders approval as `Aprobado… 25 de octubre` then lone `d` then `2023`. Pass1/Pass2 captions still show year **truncated/crop** at image bottom (`…20` / illegible). Candidate year digits come from native layer; caption-mediated Pass2 **cannot pixel-verify** full “de 2023”. Limitation + packaging split (`d`/`2023`), not a silent invent claim beyond native. |
| EB025-P2-003 | p3 OWTS sale rows | Soft hyphen U+00AD after `propiedad` / similar on p4 `especiales`. Cosmetic. |
| EB025-P2-004 | p3–p4 fee lines | Printed/mixed EN fragments in Spanish schedule appear in candidate and were flagged unresolved in Pass1 captions: `in 2024`, `per hour`, `Per Section 25-4-1607`, `1 Event`, `for Multiple Events`. **Source anomaly / bilingual print** under caption mediation — not scored as Spanish-to-English rewrite by extractor. |
| EB025-P2-005 | p4 start | Orphan token `de alimentos` before special-event block (page-break packaging remnant). |
| EB025-P2-006 | p4 def (4) | Spurious line break / period before `para mantener la seguridad alimentaria.` |
| EB025-P2-007 | p5 (7) | Leading quote asymmetry: `adicional”` without matching open quote in candidate. |

### Agreements (caption-mediated)

- Cover identity, Suite **2044**, Capítulo 3 / Lista de tarifas…, **Salud Publica** (no accent on cover) match Pass1.
- Fee tables pages 2–4: dollar amounts and Spanish service labels agree with Pass1 freeze within caption compression (OWTS, recreativa, RFE, admin, §B sanctions $100/día).
- **Cuido de niños** spelling preserved (not normalized to Cuidado) — Pass1 + Pass2 + candidate agree.
- Page 6 **Otras notas** 1–3 Spanish text agrees.
- No evidence candidate omitted whole fee sections vs Pass1 coverage.

### Counts

- critical: **1**
- minor: **6**
- source_anomaly_notes: bilingual EN fee fragments (P2-004); footer year crop vs native 2023 (P2-002)

## Disclosures

- caption_mediated_source_first; Atlas direct image verification still pending.
- legal_currentness: not_verified
- Spanish fidelity scope only; no 027; originals unchanged.
