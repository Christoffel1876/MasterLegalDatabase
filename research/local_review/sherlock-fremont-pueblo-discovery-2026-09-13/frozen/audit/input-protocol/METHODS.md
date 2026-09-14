---
title: SH-EXT-001 preparation and comparison method
status: PREPARED_NOT_DISPATCHED
legal_currentness: not_verified
---

This packet performed zero public-source opens. Local preparation read the current repository and pinned commit `2f2b450d8ecb3eff5258598d7be27189bc5e4cff`, plus the already accepted Pueblo discovery record. `COMPARISON.json` records actual capture time, current HEAD and separate byte hashes for working and committed inputs. A later commit or intake does not rewrite this historical capture.

The full pinned and working `LOCAL_DOWNLOAD_MANIFEST.jsonl` streams each contained 48,390 parsed rows. Each selected export contains 1,415 exact original lines. Selection was: authority ID equals CO-COUNTY-PUEBLO or CO-COUNTY-FREMONT, **or** the joined source_url/requested_url/final_url/url string contains `county.pueblo.org`, `pueblocounty.gov` or `fremontcounty`, case-insensitively. Original one-based line numbers are retained. Selected records may be duplicate attempts or carry inherited ownership errors; they are not 1,415 distinct sources. The portable packet does not include the full stream and cannot reproduce the full-stream hashes without the pinned repository.

The 29 selected registry objects retain their original JSON pointers and unmodified field values. Registry source categories and old URLs remain unverified leads. The modern Pueblo blocked seed comes from the separate retained Atlas E003 record, not an invented URL or inferred fee filename. The selected public HTTP403 body is an earlier error response, not a county fee original.

The snapshot inventory contained 61 originals and 22 mapped reviews. The separate Douglas/City-of-Pueblo intake was pending; the intended 63-original future inventory is neither county completeness nor a completed state at capture. Its working-file hashes and Git commit identity are distinct facts.

`RETRIEVAL_CATALOG.jsonl`, `LOCAL_REVIEW_QUEUE.jsonl` and county `_index.jsonl` are copied LFS pointer evidence only. `LOCAL_REVIEW_SUMMARY.json` is an ordinary 498-byte historical summary and is stored separately. The pre-freeze files preserve an earlier mistaken pointer description and older return instructions; only the current INSTRUCTIONS.md and COMPARISON.json are authoritative for this assignment.

The action schemas validate visible reserved tool actions, references and finite action/URL counters. They do not intercept tools, guarantee byte caps, authenticate clock history or measure browser/CDN wire traffic. The 20 MB per-body and 80 MB cumulative body limits are explicit procedural constraints. Preserve any actual overrun honestly and stop further body acquisition. The eight synthetic template tests made no public requests.

Run `python -B verify_packet.py` to verify the frozen prepared payloads. Run `python -B validate_templates.py` for initial reporting templates. The separate `deliveries/` tree is reserved for later results and excluded from the prepared-file inventory; never alter the prepared instructions, comparison exports or templates. No dispatch is performed by either validator.
