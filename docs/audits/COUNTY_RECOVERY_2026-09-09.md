# County recovery findings — September 9, 2026

The six latest large-file objects remain unavailable. Four earlier files were
recovered from ordinary Git history into local evidence storage. **Historical
metadata recovery does not establish current county-law coverage.**

The recovery check ran at `2026-09-09T23:51:22.688981+00:00` against checkout
`09d6984424dbe99266b9b5aab7cc73037127319e`. No current corpus files, tracked
pointers, or manifests were replaced. No recovered bulk files were committed.

## Latest files: unresolved

Authenticated read-only Git LFS batch requests succeeded against both repositories:

- `Christoffel1876/MasterLegalDatabase`
- `GEODE77/MasterLegalDatabase`

Every requested object returned its own **404, “Object does not exist on the
server”**, with no download action. This is missing-object evidence, rather than
a failed login or transport request. The requests used the standard
`https://github.com/<repository>.git/info/lfs/objects/batch` endpoint and the
exact current pointer identifiers below. No tokens or signed URLs were retained.

| Current path | Declared bytes | Expected SHA256 / LFS object identifier |
| --- | ---: | --- |
| `08_County_Authorities/_index.jsonl` | 172,131,787 | `e896fc157617cfd9cd9839bf2bf955d893b66d7de514107e8b3c98dc4795c806` |
| `08_County_Authorities/_meta/local_rule_units.jsonl` | 198,510,809 | `063adb35f7899f839ec402f3bec1b679fc5874c035ced43305620b1af43e1870` |
| `08_County_Authorities/_meta/local_rules.jsonl` | 132,816,054 | `614fee8c3cb327853b66f2c2999aac56092a8e1fb205f75f3cbc6137796a4323` |
| `_CONTROL_PLANE/LOCAL_PROMOTION_QUEUE.jsonl` | 121,250,878 | `192ae7b9a63c284f6acfee7843aab6fd50e1c9e1c3093989326108828282ab4e` |
| `_CONTROL_PLANE/LOCAL_REVIEW_QUEUE.jsonl` | 72,395,471 | `c65a0f190fd5d5dca7810c47afc7e6843cd78520242add1fe6951545fe92ad00` |
| `_CONTROL_PLANE/RETRIEVAL_CATALOG.jsonl` | 225,796,201 | `e12d942b4c8098281d86a8e0db7a76b22512a8a75d050ff590a8e876c7b840b4` |

Total missing latest-object bytes: **922,901,200**. The local `.git/lfs` cache and
inherited `_RAW_ARCHIVE` were absent. The owner confirmed that an original backup
or original-machine path is unavailable. No broader personal-folder search was
performed.

All locally available recorded versions of the county index and county rule-unit
file were also LFS pointers; no earlier ordinary Git blob was found for either.
These findings do not establish that no copy exists anywhere, but they exhaust
the identified local and repository recovery sources for the latest objects.

## Earlier files: recovered as historical evidence

The following ordinary Git blobs were restored without changing their bytes.
Each was checked against its Git blob identifier, exact length, and an independent
SHA256. All records parse as JSONL.

`A` is commit `0f5e34ea6c1583ea206f6c4fbcdb0422cec37ff8`, dated July 15, 2026.
`B` is commit `505687b98a59d14f6d08e15dc9e8fe8e59e75902`, dated July 14, 2026.

| Historical path | Commit | Bytes | JSONL rows | Recovered SHA256 |
| --- | --- | ---: | ---: | --- |
| `08_County_Authorities/_meta/local_rules.jsonl` | A | 45,640,720 | 1,055 | `10b0df7b264d9204d15bb6a14ecb3b293717646747fda33fc89173f8acfbd806` |
| `_CONTROL_PLANE/LOCAL_REVIEW_QUEUE.jsonl` | A | 25,498,875 | 42,925 | `24ba0ea6417a3ab8331989af49303b88a0d635d5f38129bc4d7228205996c472` |
| `_CONTROL_PLANE/LOCAL_PROMOTION_QUEUE.jsonl` | A | 42,807,895 | 42,115 | `6fc3604e9371a83a10740827f2292203eefe2fcd699cc12a79f652a4f1fc0f39` |
| `_CONTROL_PLANE/RETRIEVAL_CATALOG.jsonl` | B | 35,098,198 | 57,155 | `4230fda4ba836194bd865d7f2ce9adf0f7de77a4831823e7a5241ba4938bf80c` |

Total historical bytes recovered: **149,045,688**. The 1,055 county records span
45 authority labels and all pass the current `geode.schemas.local.LocalRule`
Pydantic model. Every one is marked `source_preservation_only`, with legal status
`unknown`. The historical review queue contains 42,925 pending entries. The
recovered retrieval catalog contains state-layer records only.

These counts measure stored records and queue entries, not verified obligations,
unique current documents, or completed jurisdictions. Structural validation does
not establish source accuracy, legal currency, applicability, or completeness.
The older records were not promoted or substituted for the missing latest data.

Local evidence is retained under the ignored directory
`.geode_runtime/recovery-2026-09-09/`:

- `recovery-report.json`: sanitized repository responses, identifiers, lengths,
  validation counts, and historical Git blob identifiers.
- `pointer-preimages/<original-path>`: all six exact pointer preimages.
- `historical/<full-commit>/<original-path>`: the four recovered files.
- `prioritized-reacquisition.json`: initial official-source collection plan.

The historical files remain reproducible from the commits above with
`git show <commit>:<path>`. The ignored recovery directory is local evidence,
not a remotely published archive or a backup service.

## Initial official-source reacquisition

The inherited download manifest retains source URLs and hashes, which can guide
new acquisition. Its 48,390 rows are download attempts across counties,
municipalities, and districts; they do not prove that original bytes survived.

Four official catalog entry points were inspected for a bounded county pilot:

| Candidate county | Catalog inspected | First collection target |
| --- | --- | --- |
| Jefferson | [Zoning Resolution](https://www.jeffco.us/2460/Zoning-Resolution) | Complete published zoning document and separately identified later adopted changes. |
| Jefferson | [Land Use & Planning](https://www.jeffco.us/303/Land-Use-Planning) | Separate fee, permit, policy, and ordinance documents. |
| Clear Creek | [Codes & Regulations](https://www.clearcreekcounty.us/196/Codes-Regulations) | Publisher lists for building, zoning, subdivision, health, roads, and taxes. The inherited `/960/Codes-Regulations` URL redirected here. |
| Clear Creek | [County Ordinances](https://www.clearcreekcounty.us/339/County-Ordinances) | Linked enacted documents together with the publisher's repeal and replacement labels. |

These are **inspected official catalogs, not fetched and verified current law**.
The web tool's source crawl dates vary. This inspection did not preserve original
source bytes or establish a new successful raw-source check. No mass download
occurred during recovery.

The proposed first acquisition batch is limited to these four catalogs, at most
30 explicitly linked documents, and 100,000,000 total bytes, without automatic
recursive crawling. Those limits bound the trial; they do not define complete
county coverage. Stop and report any catalog or required document that exceeds
the batch, fails access, or requires additional discovery.

Preserve each new original by content hash and actual retrieval time. If new
bytes match an inherited SHA256, record exact historical-source recovery.
Otherwise retain them as a newly retrieved version and keep the historical
original marked missing. Reconcile authoritative document lists, jurisdiction,
adoption/effective/repeal status, and subsequent amendments before publishing
validated derived records for review.

The inherited registry explicitly flags a City of Boulder website attributed
to a Boulder County source. That jurisdiction mismatch requires correction from
official county evidence; historical authority labels and source categories
cannot be accepted solely because their records parse.

## Planned local expansion

The next local pilot remains a planned **two counties, two municipalities, and
two districts**. Jefferson and Clear Creek are initial county candidates; the
municipalities and districts still require selection against the coverage map,
publishing systems, and service-area boundaries. Include different access formats
and a fire or water/sanitation district.

Complete and reconcile the agreed category checklist for each pilot, then run
change, no-change, missing-source, and failure cases before expanding. Capture
codes, uncodified adopted changes, zoning, building/fire amendments, permits,
fees, and applicable district requirements from their separate publishers.
Publish reviewable batches, preserve unresolved gaps, and demonstrate scheduled
checks. The four catalog inspections and historical recovery do not complete
that six-jurisdiction pilot or activate its monitoring.
