---
title: Sherlock005 retained package structural audit
assignment_id: geode-source-discovery-005
audited_at_utc: "2026-09-11T17:30:06.061002+00:00"
status: structural_audit_completed_pending_source_review
legal_currentness: not_verified
coverage_promoted: false
archive_sha256: 34ff40001ce67434ddab4f8f1450f9e711296e6b557753622e6f0f41f19c27ee
audit_json_sha256: 7deb695f8dd7925dafab238bc6450db05597bfecfa91ccd6bb97b47ed6b6c3ad
---

# Sherlock005 retained package audit

The archive and retained delivery copies passed byte-integrity checks, with delivery-scope and source-type qualifications. No sources were imported into the repository.

- Archive: **193,493,914 bytes**, SHA-256 `34ff40001ce67434ddab4f8f1450f9e711296e6b557753622e6f0f41f19c27ee`.
- Tar: **69 regular files**, **4 directories**, **204,233,754 uncompressed file bytes**.
- Inventory: **40 loose files**, all hash/size/absolute-path bindings verified; **33** present in tar and **7 Mac retry captures** outside it.
- PDFs: **19 unique files**, **203,976,733 bytes**, **2,575 pages**. Of these, two meeting packets contribute **1,705 pages** and 17 other PDF candidates contribute **870 pages**.
- All 69 `box_extract/` file copies match tar members exactly. All 19 PDF member page trees parse, with no repair/password/encryption and terminal EOF markers.
- Blocking artifact-integrity discrepancies: **0**. Legal review and source currentness remain unverified.

## Findings

1. The compressed archive hash and byte count match the supplied claim; concatenation of partaa through partae reproduces the same hash and byte count.
2. No traversal, absolute member paths, links, special members, or duplicate member names found. All regular member bytes were streamed and hashed without extraction.
3. The supplied artifact inventory describes 40 loose artifacts, not a complete archive manifest. 7 inventory entries are outside the tar: the seven mac_* retry HTML captures. All inventory-to-loose hash/size/path bindings match.
4. The tar contains 69 files in four directories. All 69 box_extract copies match their tar member hashes and sizes. Later loose logs differ from the frozen archive; collector.py and supplement.py exist only in tar/box_extract, not the top-level attempt folder.
5. The 19 structurally parseable PDFs are 17 code/amendment candidates plus two meeting packets. This is not a count of certified adopted ordinances or reviewed legal rules. The two packet SHA-256 values differ from one another.
6. Four WebFetch texts occur twice each at raw/ and exports/ paths. These are four derived text artifacts, not eight originals. WebFetch exports are not publisher-original HTML bytes and were not validated against live pages.
7. Both OrdRes retry HTML files are byte-identical Laserfiche Error pages saying cookies must be enabled to sign in. They are not certified ordinance PDFs and should be labeled error pages rather than a successful document viewer capture.
8. The failed Article 7 .pdf.html body is a Page Not Found page, not legal text. The separately retained Article 7 PDF has different original bytes and parses as 64 pages.
9. PDF internal title fields contain stale-looking labels (for example IRC metadata says 2012 International Residential Code and several code amendments say Annual Report). Those metadata titles are not reliable evidence of document version; this audit did not transcribe or visually inspect document pages.
10. Package labels, supplied request/final URLs, source/HTML status codes, and fetched_at timestamps are reporter provenance claims. Bytes establish received-artifact identity only; no new HTTP requests were made. File/tar mtimes and internal PDF dates do not authenticate original acquisition or legal effective dates.

## PDF inventory

Page counts are structural; titles below are filenames, not certified document titles.

| Member | Bytes | Pages | SHA-256 |
|---|---:|---:|---|
| `raw/005_www.fortcollins.gov_24-ibc-final-amendments.pdf` | 618,034 | 34 | `405c319be443d472e348eac121fec78e1057a8fc1894c800fbefe4ac4d61d5b8` |
| `raw/006_www.fortcollins.gov_24-irc-final-amendments.pdf` | 919,990 | 52 | `88f183426f4ac7995753df423b949342a4ba68e2e9c05dee1a580289d3c983a2` |
| `raw/007_www.fortcollins.gov_24-iecc-final-amendments.pdf` | 1,771,758 | 91 | `561320ff6504708e2719626aaa29b663525a571736b1477d7d41e5a0d14b6e9d` |
| `raw/008_www.fortcollins.gov_24-imc-final-amendments.pdf` | 481,147 | 13 | `b8b7ef5a549e71788683c4d67bce6c13f8e75aa70b4fc10f277bce9e5dba4dd3` |
| `raw/009_www.fortcollins.gov_2025-colorado-wildfire-resiliency-code-final-for-brc.pdf` | 169,449 | 8 | `00e7446d7deac3499b86c4b8f15a5d802cc0c14dc2621409845ec13525cb01d2` |
| `raw/010_www.fortcollins.gov_article-1-general-purpose-and-provisions.pdf` | 340,287 | 7 | `555a05553af57619c818c5b9ab90d1b751e161a307d8bb65fc73141991a73d2a` |
| `raw/011_www.fortcollins.gov_article-2-zone-districts.pdf` | 15,221,919 | 91 | `1ec5deac82b2511d2ae82ee928f887b006db689553181ed1bb717c7c7a421e36` |
| `raw/012_www.fortcollins.gov_article-3-buildingtypes.pdf` | 22,584,310 | 33 | `b12f6031046c354307685563901bf8981c21554342dd5c39424809cb89654ea6` |
| `raw/013_www.fortcollins.gov_article-4-use-standards.pdf` | 14,252,023 | 53 | `c46f095d1be1e8ba65d1d5fe325daafcec0f4482bb89846f97a039c80449e757` |
| `raw/014_www.fortcollins.gov_article_5_general_development_and_site_design.pdf` | 6,306,165 | 188 | `b3e4eb6e9a3f3354f63035430a2c9e4e2ccfbd0fa1c39303b96442da913c0364` |
| `raw/019_www.fortcollins.gov_24-ifgc-final-amendments.pdf` | 483,615 | 13 | `dbcfe030e1643892964a6261127f242c16017bc88ac91116c6cb868952fe28ac` |
| `raw/020_www.fortcollins.gov_24-ipc-final-amendments.pdf` | 953,468 | 38 | `0bd99bf7b3b1d5bb7c0792c8a791db5a80a3224c7a2c58bfef2a50cb182333ea` |
| `raw/021_www.fortcollins.gov_24-ispsc-final-amendments.pdf` | 549,485 | 23 | `6704ba29209f86268df1a2ea9b20aba74652fda6b62a9f5d820d1099dab8c900` |
| `raw/022_www.fortcollins.gov_24-iebc-final-amendments.pdf` | 504,193 | 13 | `07313c0b4be74f59d4db72703dbd89b53852166b3f0cfc0ad947e7044adfaf5e` |
| `raw/023_www.fortcollins.gov_24-ipmc-final-amendments.pdf` | 557,620 | 22 | `69a0d3e946866cd72311b0364cd1a97a8ef6c47758be5cf81fee1f61914266b6` |
| `raw/024_www.fortcollins.gov_article-6-administration-and-procedures.pdf` | 1,529,063 | 127 | `fb096c95cbb04a5da339d0e534496ca26df9fb854116ea81cf73281dd3b25b24` |
| `raw/026_www.fortcollins.gov_article-7-rules-of-measurement-and-definitions.pdf` | 3,332,684 | 64 | `646ebd678a89dd24e8f8c9cc487ecc0e6776265f5f1b847a1ce3e5e3d3cde79f` |
| `raw/027_mccmeetings.blob.core.usgovcloudapi.net_MEET-Packet-9909c32063cd463990a30436cf0d9096.pdf` | 42,636,309 | 529 | `95de1b7b623aba3ea062ba1b1e19d10bbb1f32618cde17097db2eab15496e2ad` |
| `raw/028_mccmeetings.blob.core.usgovcloudapi.net_MEET-Packet-98ce54e66b3d4da38059730c71b0f1c6.pdf` | 90,765,214 | 1,176 | `412acf2984ea86b792dea6b88880ebcd4fb0cd21969b7c0a61672ce65da2bae2` |

## Delivery differences

Inventory-listed files absent from tar (all available and hash-verified loose):

- `raw/mac_101_Building-Code.html`
- `raw/mac_102_Land-Use-Code.html`
- `raw/mac_103_Fee-Schedules.html`
- `raw/mac_104_Public-Notices.html`
- `raw/mac_105_poudre-fire-code-adoption.html`
- `raw/mac_106_OrdRes-19288428.html`
- `raw/mac_107_OrdRes-23389379.html`

Loose top-level members differing from or absent at the tar-relative location (the frozen copies remain verified in `box_extract/`):

- `logs/backlog.json`: **different**; archive SHA `e78f1928011ed79e78d5e12b3b91b32c791bf9263d24b6c1b2091a1a22242072`; loose SHA `fcbc97ed65fe1812a125fd9f6618803566a673b71c97f57d517298d85702b655`.
- `logs/attempted_urls.json`: **different**; archive SHA `6226808cbf8f22191bef172164d185a165cf5e02a77db6789d22bdc616daac75`; loose SHA `76bff20333643a83cc4971268afa0280bf5b412eac775924873befe257d74201`.
- `collector.py`: **missing**; archive SHA `c457191cfd7982aa2a9891b70b2e88567eeb5ccf24625e9a497436196189d671`.
- `supplement.py`: **missing**; archive SHA `1dbe27c8fc6a41bd38078dec871f0ee2e8e22ee9a7dfc1434c6379ce8f93749f`.

The final log declares 36 events / 27 distinct requested URLs; the tar log declares 29 events / 25 distinct requested URLs. Both counts were recomputed. Raw hash/size bindings and sidecar claims in those two selected JSON logs were checked. The separate earlier TLS-failure JSONL is qualified below. These counts reflect supplied logs, not independently observed network transactions. The final inventory and combined logs were added after the box archive and are not authenticated merely by its hash.

## Supplemental attempt-history qualification

The retained `logs/mac_retry_attempts.jsonl` contains **seven earlier urllib TLS certificate failures**; `logs/mac_retry_attempts.json` contains **seven later curl responses**. They are different event sets. The combined 36-event report omits the earlier failures, so the retained logs establish **43 supplied tool-attempt events**, not a complete 36-event history. They still refer to 27 distinct requested URL strings. HTTP transaction counts were not independently observed.

Earlier failure records claim zero-byte hashes at body paths later reused for curl responses. The current nonempty files match the later curl claims, not the earlier failure claims. This is a provenance limitation; it is not evidence of a corrupt retained PDF. Preserve both logs.

All seven Mac bodies plus seven headers are outside the tar. Their 14 copies in `raw_mac_retries/` exactly match `raw/`. Each last HTTP status in the corresponding header matches the later curl JSON claim. No Mac per-response metadata sidecars exist. Header/log correspondence is not proof of acquisition time.

## Limits

- Read-only structural audit of supplied files; no source-site opens, live HTTP replay, PDF text extraction, page image review, signature/adoption/effective-date validation, repository intake, or coverage/currentness promotion.
- Archive integrity does not establish that any supplied file was freshly downloaded from its claimed URL at its claimed timestamp.
- Unsafe-member checks were performed before reading member payloads; no supplied scripts executed. PDF page-tree checks are structural and do not certify rendered/text completeness or accuracy.
- The archive is an earlier box-only package; the final inventory, priorities, Mac captures/headers, and combined 36-event log must be retained alongside it to reproduce the full reported delivery.
- Meeting-packet status comes from MEET-Packet filenames and supplied source roles; without document review the audit does not certify which ordinance attachments, drafts, hearings, or final signed texts appear inside.
- Historical digest comparisons are a separate audit; this report does not verify source novelty or substantive legal changes.

## Machine-readable evidence

`PACKAGE_AUDIT.json` SHA-256: `7deb695f8dd7925dafab238bc6450db05597bfecfa91ccd6bb97b47ed6b6c3ad`. It records every tar member, input hash, copy/inventory/log binding, duplicate group, and extra loose path.
