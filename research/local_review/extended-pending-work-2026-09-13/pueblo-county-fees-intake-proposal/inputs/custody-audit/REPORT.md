---
assignment_id: SH-EXT-002
status: custody_verified_with_qualifications_pending_intake
independent_source_visual_pages: 0
public_requests_by_auditor: 0
canonical_intakes_by_auditor: 0
legal_currentness: not_verified
answer_safe: false
---
# Pueblo County directed source custody audit

The received two-page fee PDF is suitable for a **preservation-only intake proposal**, with acquisition method `received_review_package`. It remains pending the approved transaction and separate source QA. This audit does not establish an adoption date, legal effect, current law or complete county coverage.

All **25 inventoried payloads** match their recorded hashes and byte lengths. The actual delivery has **27 files**; the inventory itself and hash-summary.txt are the two unlisted files. The `.bin` files exactly duplicate the PDF and error HTML respectively, so there are **two response bodies**, not four acquisitions.

| Recorded action | Received result | Exact bytes | SHA256 |
| --- | --- | ---: | --- |
| SHEXT002-A001 | Fee PDF; reported HTTP 200; structurally valid, unencrypted, unrepaired, 2 pages | 75,214 | 1c9fda2c8bacb414468947664d6edb6640845081fcb1a5366dccf0c58720a084 |
| SHEXT002-A002 | Reported HTTP 403; retained “Just a moment…” challenge HTML | 5,868 | d4074fa6d9f4ac22d763ea65b9419241dac025322e2f57b9393dfd2bf5b43854 |

The PDF length agrees with the retained Content-Length and supplied curl size. Both reported final URLs equal the requested URLs; no visible redirects are recorded. The two public-header JSON objects contain no Cookie, Set-Cookie, Authorization, Proxy-Authorization or X-API-Key fields. This is a scoped header-name check, not a claim that every embedded HTML token or every unretained transport artifact was audited.

## Exact authorization and ownership

Both URLs exactly match the root-authorized DIRECTED_PROPOSAL and the retained A031 links. The PDF href retains its original percent encoding. The parent title is **Application Information Page and Checklists | Pueblo County**, with the matching department page URL. Its fee anchor is labeled **Fee Schedule Adopted 5.8.25 - Revised (2).pdf**. The other anchor is **County Commissioners**.

A031 is **retained rendered browser DOM**, not original HTTP response bytes. It came from the earlier assignment's authorized browser alternate after an earlier denial. That historical alternate does not authorize a retry in SH-EXT-002. The county attribution rests on this documented parent identity and link chain. City of Pueblo is a different authority, and no source-face issuer wording is independently certified by this custody audit.

The commissioner's 403 body is not a successful catalog and cannot serve as the adopting instrument. No retry or additional public action is recorded. The final collector-state `stop` field is null, while the result notes and report say the source was stopped. That is a reporting limitation; the null field is not affirmative machine proof of stop enforcement.

## Timing and budgets

The two recorded reservations/results are serial: A001 is reserved at **01:57:19.462 UTC**, finishes at **01:57:20.393**, and A002 is reserved at **01:57:20.394**, finishing at **01:57:20.652**. The recorded totals are **2 actions, 2 URLs and 81,082 response bytes**, within the authorized 6 actions / 4 URLs / 10 MB per body / 20 MB total. The reported research finishes before the 02:15 cutoff.

The original curl command, complete transport log and independent request-level timing evidence are absent. TLS verification, unchanged identity, original acquisition times and reserve-before-tool execution therefore remain **reported claims**. Hidden wire requests were not measured. The reservation timestamp must not be relabeled as an independently witnessed HTTP start.

This auditor captured all 27 unchanged delivery files at the actual local audit time **2026-09-13T02:20:59.829990Z**, before the 02:25 report deadline. That establishes that these bytes were present by the audit capture, not the exact original delivery-completion time. The report's prepared_at 01:58:07 precedes its appended caption summary's generated_at 01:58:37; neither is used as independent final-completion proof. Filesystem mtimes are not acquisition certificates.

## Full legacy comparison

The pinned commit is **2f2b450d8ecb3eff5258598d7be27189bc5e4cff**. Both its complete legacy manifest and the current complete manifest were independently streamed and parsed, **48,390 rows each**, **33,903,546 bytes each**, SHA256 **dce2b392bc3e81bbb21e31f2a837fdb498d5aa9a79f5b034942a777a82041c51**.

Both scans found **zero exact recorded digest matches** for either response and **zero exact URL matches** in source_url, requested_url, final_url or url. Percent-decoding the compared URLs also produced zero matches. The proposed stable source ID is absent as well.

Sherlock compared only the previously selected **1,415 rows**, whose exact SHA is **755c44489adb15f1acc91aa7ea6ad21dc59bef1a0df36cb2be0b82f2c38050cd**. That limited no-match claim was correctly qualified. This audit adds the full-manifest metadata comparison without rewriting the worker's report. Neither result proves global novelty, absence of unrecorded originals, a legal change or lack of earlier equivalent content at another URL. No historical original bytes were compared. The full streams are omitted from the portable package; their optional replay requires the pinned repository/current exact file.

The complete current **63-row raw manual manifest** and **64-row manual ledger** also have no exact fee digest, official URL or proposed source-ID match. Exact copies and scan hashes are retained. These are a dated preflight input, not permission to ignore a later concurrent intake.

## Minimal intake recommendation

Use source ID **pueblo-county-planning-fees-sh-ext-002**, authority **CO-COUNTY-PUEBLO**, and layer **08_County_Authorities**. Preserve exactly one 75,214-byte PDF. With `received/raw/SHEXT002-A001.pdf` as the actual incoming file, its original_filename is **SHEXT002-A001.pdf**. If a transaction instead selects a separately copied original.pdf, the basename must truthfully follow that actual input.

Use `received_review_package`; preserve the supplied URL and reservation/result times separately as claims. The actual repository received_at and final archive path must remain unset until the approved transaction runs. The existing generic CLI request enum does not support this method; use the established typed manual-record transaction and validators without changing the enum or disguising the acquisition as a direct official download.

Immediately before any write, recheck exact current manifest/ledger prefixes, source bytes, URL/layer policy and duplicate ID/hash/URL state. Preserve snapshots and immutable raw bytes. Exclude the 403 HTML, duplicate .bin files, rendered DOM, rasters and derived text from the single-original intake. The expected status is **archived_pending_pipeline**. Do not enroll monitoring or promote coverage/currentness as part of this intake.

Sherlock's visual method is explicitly caption-mediated. This auditor inspected no source pages visually and makes no table, fee, signature or absence finding. Root/Ptolemy's separately bound source review remains separate evidence.

## Read-only verification

```bash
python -B validate_audit.py
```

To additionally replay both complete legacy metadata streams locally:

```bash
python -B validate_audit.py --repository /absolute/path/to/MasterLegalDatabase
```

Neither command opens public sources or performs canonical intake. Original delivery and earlier audit bytes remain unchanged; the final manifest binds this additive package and explicitly retained draft preimages.
