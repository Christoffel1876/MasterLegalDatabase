---
title: One origin LFS availability retry
status: exact_objects_reported_missing_at_origin_no_recovery
date: 2026-09-13
---

The explicitly authorized retry ran outside the network-restricted sandbox from **2026-09-13T15:37:48.781849Z** to **15:37:49.775559Z**. The pinned, origin-only Git LFS dry run exited 2 and reported both requested object IDs as **404: Object does not exist on the server**. It retained zero object bytes and made no checkout changes. This is a fresh client-reported object result; the earlier sandbox DNS failure remains separate.

The review queue object expects 72,395,471 bytes (`c65a0f190fd5d5dca7810c47afc7e6843cd78520242add1fe6951545fe92ad00`). The county index expects 172,131,787 bytes (`e896fc157617cfd9cd9839bf2bf955d893b66d7de514107e8b3c98dc4795c806`). Neither was recovered. Both working pointers and `.git/config` remain byte-identical. No further request or download was made.

The complete four-line error output was compared against exact safe templates, then copied unchanged to `stderr.public.txt`; it contains the known commit, two OIDs, fixed error wording and known origin endpoint. Private original streams remain outside this public subset with restricted filesystem permissions. This does not claim HTTP header redaction: raw HTTP headers/body were never captured. HTTP batch status and wire-level request count remain unknown.

`DISPOSITION.json` is the final interpretation. The copied `ATTEMPT.json` retains the earlier pre-interpretation status and exact execution metadata unchanged. Its private-path references are identity records only, not portable files to open. `run_attempt.py` is preserved method evidence and must not be rerun into the closed execution directory. `validate_public.py` verifies only frozen public files, schemas and target/error bindings, with no network or writes.

No restoration is proposed. Older queues, other OIDs or reconstructed data are not the requested original objects. Another recovery location would require a separate authorized check. This package is a public subset, not the entire execution directory.
