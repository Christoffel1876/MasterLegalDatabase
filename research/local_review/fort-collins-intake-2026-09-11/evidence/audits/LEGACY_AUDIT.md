---
title: Sherlock005 full-manifest historical comparison
prepared_at: 2026-09-11T17:31:54.593066+00:00
assignment: geode-source-discovery-005
comparison_commit: be73a9c2bbc00c81f73392d847f8dc8c6234735c
compared_head_commit: 12b05e8be98c5861ed5a3c98d54a6209801b8125
status: historical_metadata_comparison_complete_content_pending
legal_currentness: not_verified
---

# Historical comparison audit

All ten reported PDF digest matches are confirmed against the full pinned manifest. The other nine of the nineteen delivered PDFs have no exact URL or matching digest anywhere in that manifest. None of the priority “new versus directed sample” claims is contradicted by this broader check; absence remains scoped to one manifest and commit.

## Scope and integrity

- Streamed **48,390 rows** across all owners: 39,050 downloaded and 9,340 failed records. Manifest SHA-256: `dce2b392bc3e81bbb21e31f2a837fdb498d5aa9a79f5b034942a777a82041c51`.
- Verified actual hashes and sizes for **all 40 inventory files**, including all nineteen PDFs. This measures delivered local bytes; it does not independently witness HTTP acquisition.
- The supplied 45-row Fort Collins extract exactly matches the entire Fort Collins subset. This review also searched every other owner and compared all nineteen PDF digests globally. No matching row outside the Fort Collins authority tag was found.
- Exact current requested/final URLs were compared without normalization. Historical rows have requested_url but no final_url field; source_url is parent-source context, not an alternate PDF download URL.
- Named control-plane Git blobs are unchanged between the pinned commit and recorded HEAD `12b05e8be98c5861ed5a3c98d54a6209801b8125`: download manifest, local source registry, municipal source registry, coverage ledger and ownership corrections.

## Confirmed historical recovery

The ten distinct PDFs map to fourteen downloaded rows because Articles 1–4 each have two historical source records for the same city. Matching a stored digest is not a direct comparison with old Windows files and does not prove current legal force.

| Delivered PDF | Historical manifest lines | SHA-256 |
|---|---|---|
| 005_www.fortcollins.gov_24-ibc-final-amendments.pdf | 17897 | `405c319be443d472e348eac121fec78e1057a8fc1894c800fbefe4ac4d61d5b8` |
| 006_www.fortcollins.gov_24-irc-final-amendments.pdf | 17898 | `88f183426f4ac7995753df423b949342a4ba68e2e9c05dee1a580289d3c983a2` |
| 007_www.fortcollins.gov_24-iecc-final-amendments.pdf | 17899 | `561320ff6504708e2719626aaa29b663525a571736b1477d7d41e5a0d14b6e9d` |
| 008_www.fortcollins.gov_24-imc-final-amendments.pdf | 17901 | `b8b7ef5a549e71788683c4d67bce6c13f8e75aa70b4fc10f277bce9e5dba4dd3` |
| 009_www.fortcollins.gov_2025-colorado-wildfire-resiliency-code-final-for-brc.pdf | 17900 | `00e7446d7deac3499b86c4b8f15a5d802cc0c14dc2621409845ec13525cb01d2` |
| 010_www.fortcollins.gov_article-1-general-purpose-and-provisions.pdf | 17905, 18052 | `555a05553af57619c818c5b9ab90d1b751e161a307d8bb65fc73141991a73d2a` |
| 011_www.fortcollins.gov_article-2-zone-districts.pdf | 17906, 18053 | `1ec5deac82b2511d2ae82ee928f887b006db689553181ed1bb717c7c7a421e36` |
| 012_www.fortcollins.gov_article-3-buildingtypes.pdf | 17907, 18054 | `b12f6031046c354307685563901bf8981c21554342dd5c39424809cb89654ea6` |
| 013_www.fortcollins.gov_article-4-use-standards.pdf | 17908, 18055 | `c46f095d1be1e8ba65d1d5fe325daafcec0f4482bb89846f97a039c80449e757` |
| 014_www.fortcollins.gov_article_5_general_development_and_site_design.pdf | 17909 | `b3e4eb6e9a3f3354f63035430a2c9e4e2ccfbd0fa1c39303b96442da913c0364` |

## No exact predecessor found

These are not “never collected” findings. Different URLs, alternate versions, other manifests or unrecorded files remain possible.

| Delivered PDF | SHA-256 |
|---|---|
| 019_www.fortcollins.gov_24-ifgc-final-amendments.pdf | `dbcfe030e1643892964a6261127f242c16017bc88ac91116c6cb868952fe28ac` |
| 020_www.fortcollins.gov_24-ipc-final-amendments.pdf | `0bd99bf7b3b1d5bb7c0792c8a791db5a80a3224c7a2c58bfef2a50cb182333ea` |
| 021_www.fortcollins.gov_24-ispsc-final-amendments.pdf | `6704ba29209f86268df1a2ea9b20aba74652fda6b62a9f5d820d1099dab8c900` |
| 022_www.fortcollins.gov_24-iebc-final-amendments.pdf | `07313c0b4be74f59d4db72703dbd89b53852166b3f0cfc0ad947e7044adfaf5e` |
| 023_www.fortcollins.gov_24-ipmc-final-amendments.pdf | `69a0d3e946866cd72311b0364cd1a97a8ef6c47758be5cf81fee1f61914266b6` |
| 024_www.fortcollins.gov_article-6-administration-and-procedures.pdf | `fb096c95cbb04a5da339d0e534496ca26df9fb854116ea81cf73281dd3b25b24` |
| 026_www.fortcollins.gov_article-7-rules-of-measurement-and-definitions.pdf | `646ebd678a89dd24e8f8c9cc487ecc0e6776265f5f1b847a1ce3e5e3d3cde79f` |
| 027_mccmeetings.blob.core.usgovcloudapi.net_MEET-Packet-9909c32063cd463990a30436cf0d9096.pdf | `95de1b7b623aba3ea062ba1b1e19d10bbb1f32618cde17097db2eab15496e2ad` |
| 028_mccmeetings.blob.core.usgovcloudapi.net_MEET-Packet-98ce54e66b3d4da38059730c71b0f1c6.pdf | `412acf2984ea86b792dea6b88880ebcd4fb0cd21969b7c0a61672ce65da2bae2` |

## Qualifications and remaining gaps

- **SD005-09 and SD005-11:** the two meeting-packet URLs and digests have no predecessor in the full pinned manifest, not merely the directed sample. They remain meeting-packet proxies. The specific Ordinance 055/166 PDFs were not obtained; viewer shells do not fill that gap.
- **SD005-10 and SD005-12:** the exact fee-page and public-notices URLs have no requested/final URL predecessor here. This is not a claim that no related fee or notice material exists in the corpus.
- **SD005-01 and SD005-06:** historical Building-Code and Land-Use-Code HTML captures exist. Current 403 bodies and WebFetch exports do not recover original publisher HTML. The Land-Use-Code URL has two different prior recorded digests at lines 17904 and 18051.
- **Single-value URL map:** the supplied helper map retains only one record per URL, hiding alternate prior hashes and duplicate source captures. The 45-row extract itself is accurate; this audit preserves all relevant historical rows.
- **Poudre Fire ownership:** line 17988 indexes the Poudre Fire page under the Fort Collins municipal tag. The municipal registry already identifies it as a related Poudre Fire Authority source and warns about jurisdiction/adoption relationships; Sherlock’s related-authority description is appropriate. Do not treat that inherited city tag as proof of city ownership or enactment. Current blocked responses do not recover the older HTML bytes.
- **Input paths:** artifact_inventory.json and backlog.json are in the delivery parent. Their attempt-folder copies under exports/ and logs/ are byte-identical. Exact consumed paths/hashes are in LEGACY_COMPARISON.json.

## Limits

Old Windows source paths were retained as historical metadata and were not opened. This review verifies newly computed local digests against recorded historical digests, not the past acquisition itself. It makes no finding about legal validity, effective dates, completeness, currentness or substantive changes. No network source was opened; no source or repository file was ingested, edited or committed.
