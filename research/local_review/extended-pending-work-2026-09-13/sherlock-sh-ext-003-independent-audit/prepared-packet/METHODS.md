---
assignment_id: SH-EXT-003
status: PREPARED_NOT_DISPATCHED
public_actions_during_preparation: 0
legal_currentness: not_verified
---
# Preparation and comparison limits

This packet used local files and Git object reads only. Both the pinned baseline and observed HEAD were `2f2b450d8ecb3eff5258598d7be27189bc5e4cff` at capture. COMPARISON.json records the actual capture time and exact separate file hashes. The current manual manifest and ledger include later intake absent from that commit; their bytes are preserved separately instead of being described as the committed state.

Each complete `_CONTROL_PLANE/LOCAL_DOWNLOAD_MANIFEST.jsonl` stream was read and parsed line by line: **48,390 rows** in the pinned copy and **48,390 rows** in the current copy. Selection matched either exact authority CO-COUNTY-CHAFFEE/CO-COUNTY-GUNNISON, source IDs beginning `county_chaffee_`/`county_gunnison_`, or an exact parsed hostname in source_url/requested_url/final_url/url equal to chaffeecounty.org, www.chaffeecounty.org, search.chaffeecounty.org, gunnisoncounty.org or www.gunnisoncounty.org. It was not a sample.

Each selected export contains **1,831 exact original lines**, with original one-based line numbers: **1,651 Chaffee** and **180 Gunnison** records. They contain **401 downloaded-status** and **1,430 failed-status** records, **172 distinct recorded URLs**, and **65 distinct recorded SHA256 values**. These are inherited attempt records, not 1,831 documents, 401 verified available originals, or current source availability. Repeated source categories and repeated download attempts remain visible. Statuses and timestamps are historical record claims.

No selected record's exact `_RAW_ARCHIVE/…` suffix path was present in this checkout. This was a scoped existence check inside the repository after mapping the inherited Windows path suffix; it did not search outside the repository, scan every content-addressed object, or prove the digest is absent globally. No historical source bytes were compared. Do not claim a current source matches a historical original based only on the manifest digest.

The complete registry snapshots are included, with **33 selected objects** and their unchanged JSON pointers. Eight exact URLs are the initial plan; duplicate category rows are not separate required opens. Initial source roles and category labels remain unverified leads. Current and pinned selected legacy bytes match, but the full 33.9 MB streams are intentionally excluded. The portable verifier can recompute selected-line summaries and registry bindings, not the omitted full-stream hash or the earlier filesystem availability check. Those full-stream claims are reproducible only against the specified repository commit/current capture.

The retrieval catalog, county index and local review queue are retained as their actual Git LFS pointer bytes; their named payloads are unavailable in this capture. LOCAL_REVIEW_SUMMARY.json is a small ordinary historical JSON file, not a missing-LFS pointer. Neither a pointer nor an old summary establishes usable current coverage.

The local accounting helper is an additive adaptation of the earlier SH-EXT-001 reporting models. It adds immutable serial reservations/results, visible redirect charges, per-response and aggregate retained-body checks, a denial retry refusal and a fixed cutoff. It makes no public requests and cannot enforce the behavior of another tool. Known automatic hops are counted explicitly; hidden network requests remain unmeasured. Unknown or partial body accounting prevents further reservations. A real result that violates a cap remains preserved even though aggregate validation then refuses continuation. Full-source QA, legal effect and coverage promotion are outside this discovery assignment.

`preparation-preimages/` contains earlier local draft files changed while preparing this packet; those are historical inputs, not the operative model or schema. Every operative file and these preserved preimages are bound by the final closed manifest. Future deliveries are separately mutable and excluded from the preparation manifest. A separate root dispatch receipt is required to activate work; this preparation never changes its own status to dispatched.
