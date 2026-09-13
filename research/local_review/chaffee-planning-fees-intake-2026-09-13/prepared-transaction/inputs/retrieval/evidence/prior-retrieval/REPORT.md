---
title: Chaffee directed response custody
reviewer: Ptolemy
prepared: 2026-09-13
authority_id: CO-COUNTY-CHAFFEE
status: three_authorized_actions_complete
answer_safe: false
legal_currentness: not_verified
---

Two observed Revize URLs returned complete PDF response bodies. The application-fee county
URL returned a complete 302 HTML notice. Its new Location was retained without being followed:
all three authorized actions were used. There were no retries, automatic redirects, searches,
authentication, cookies or browser impersonation in these requests.

| Action | Retained response | Bytes | Structural pages | SHA-256 |
| --- | --- | ---: | ---: | --- |
| A001 / CHAFFEE-D001 | HTTP 200 PDF at the observed CWRC ordinance lead | 1,146,747 | 14 | `0688818dfd4d7726f1eb84b5b57c47580d01b094297a92d4ce88c600ccfe7eba` |
| A002 / CHAFFEE-D002 | HTTP 200 PDF at the observed electric-amendment lead | 529,100 | 7 | `c0bfb6e8d4adb846fd62ec7dabbdd824286f7432be6a82b6b2d2264d4553cdf6` |
| A003 / CHAFFEE-D003 | HTTP 302 HTML notice at the application-fee link | 279 | none | `05eeea1749f7850885878184362ae70b502b30d6305129f36a303695b1abec6e` |

The total is **3 deliberate GETs / 3 distinct requested URLs / 1,676,126 response-body bytes**.
Two PDF bodies have **21 structural physical pages; zero pages were source reviewed** in this
task. The labels above identify the prior leads and do not certify document subject, adoption,
legal effect, source text accuracy or current law. No native-text extraction, page rendering,
canonical intake or review-inventory promotion was performed here.

The exact target plan was frozen at **2026-09-13T16:08:09.711809Z**, before every invocation,
with PLAN SHA `4b9168c1b391fd9d4e39fedaa8c68de0e86609329e057e349fc268acf5015256`.
Six copied evidence members bind the literal county anchors, first HTML base, supplied earlier
redirect notices and received header summaries. Spaces were percent-encoded once; observed
ampersands, existing escapes and query values were preserved. The first county label remains
literally “2025 BOCC Ordinance 2026-02”; it was not silently reconciled with its filename.

Each `events/A00N/` contains a write-once reservation with the exact argv and shell rendering,
actual local UTC start/completion, monotonic elapsed time, process exit, raw curl JSON stdout,
stderr, exact body and public response header subset. `/usr/bin/curl` 8.7.1 used ordinary TLS,
no proxy, no `.curlrc`, an honest Geode user agent, explicit GET, retry 0 and no `--location`.
Each invocation had a 15-second connect timeout, 60-second total curl timeout and at most
20,000,000 bytes, also limited by the 50,000,000-byte remaining batch balance. All returned
well inside these limits with curl exit 0, no followed redirects and TLS verify result 0.
PDF magic and physical page counts were parsed with PyMuPDF 1.28.2; structural parsing is not
visual or legal review.

Original response header bytes were held transiently, SHA-256-bound, filtered to an explicit
public allowlist as **exact original lines**, then deleted. The omitted-field names and counts
are preserved. No Cookie, Set-Cookie or authorization fields appeared in these responses.
The omitted originals cannot be regenerated from the public subset. Raw curl writeout includes
public TLS certificates and connection metadata; its certificate dates are not document dates.
Earlier SH004 received headers remain summaries, and this later direct retrieval does not
retroactively authenticate their original transport or timestamps.

The new application-fee Location, independently consistent between the original 302 header
and notice anchor, is:

`https://cms2.revize.com/revize/chaffeecounty/Documents/Departments/Planning & Zoning/Application Forms & Fees/app_fee_schedule.pdf?t=202503011142110`

Its literal spaces need the same documented encoding for any separately authorized request.
It was **not requested** in this batch. No date meaning is assigned to the query digits or
publisher Last-Modified values. The concrete remaining gap is the exact fee-PDF body behind
this now-observed Location; another request requires a separately authorized action budget.

Run only the portable read-only validator:

```sh
/private/tmp/geode-status-venv/bin/python -B /absolute/path/to/packet/verify_packet.py
```

The verifier checks closed membership, typed schemas, fixed plan and referral proofs, exact
commands, serial action/time/byte accounting, response framing, original byte hashes and PDF
page counts. It cannot reconstruct excluded headers, independently recreate historical TLS
events, or establish source fidelity or currentness. `prepare.py`, `retrieve.py` and `seal.py`
are frozen historical execution tools, not validation entry points; do not rerun them.
