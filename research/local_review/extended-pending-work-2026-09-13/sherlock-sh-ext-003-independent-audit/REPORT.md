---
title: SH-EXT-003 independent custody, budget and legacy audit
status: received_evidence_qualified_pending_intake
assignment_id: SH-EXT-003
legal_currentness: not_verified
public_requests_by_audit: 0
---

# Findings

All 343 supplied inventory entries match their original files. The delivery contains
346 files; its lock, inventory and hash-summary are the three additional files.
The portable copy includes every file, with explicitly redacted derivatives of four
curl logs that contained 12 Set-Cookie headers. Original hashes were recomputed at
capture; the original private values remain only in the untouched delivery. The
portable verifier cannot reconstruct those four unredacted hashes from derivatives.

The complete recorded action sequence is 30 reservations and 30 results: 20 Chaffee,
10 Gunnison, 30 distinct requested URLs, 18 nonempty response bodies totaling
1,600,233 bytes, and 12 no-body outcomes. The next input, A031, exists, but its
reservation was rejected at the URL cap. There is no actual A031 reservation or
unclosed action. Supplied times are serial and precede the 03:05 UTC research cutoff.
They are worker-provided records, not independently witnessed acquisition times.
The helper counts recorded visible actions, not hidden network requests.

`logs/final_status.json` is a stale 24-action snapshot. `tool_sequence.jsonl` contains
command sequences for only the first 24 actions. Later reservations/results and
headers are retained, but an equally complete original command history is not.
The first 24 commands use curl with a Chrome-like User-Agent; they are not browser
observations. No TLS-disable, automatic-follow or retry flag occurs in those recorded
commands. The audit did not replay HTTP requests.

# Three Gunnison PDFs

| Action | Received role from first-page inspection | Pages | Historical exact URL/digest records |
|---|---|---:|---:|
| A026 | County resolution 25-24 establishing building-permit fees | 3 | 4 / 4 |
| A027 | County resolution 23-22 adopting listed 2021 codes and amendments | 16 | 4 / 4 |
| A028 | County resolution 2022-33 adopting the 2021 IWUIC | 4 | 0 / 0 |

All three originals parse without repair and have terminal EOF markers. Only the
first physical page of each was directly viewed: three of 23 pages. These observations
support document roles and county ownership; they are not full extraction, signature
identity authentication, verification of every attachment or certification of current law.
The first-page fee resolution explicitly conditions effect on recordation. Its visible
adoption line and recorder stamp are separately described in AUDIT.json. They do not
establish that no subsequent change occurred. PPRBD, municipalities and districts are
not the issuers of these three county documents.

The full current and pinned legacy files each contain 48,390 rows and are byte-identical.
The audit retains that complete stream and reproduces all 1,462 matching rows, distinguishing
133 exact requested-URL matches, 1,451 parent/source-URL context matches and eight digest
matches (categories overlap). A026 and A027 each have four exact URL-plus-digest records.
The worker's sample-based `no_exact_url_match` qualifications cannot support a global
absence claim. A028 has neither an exact requested-URL nor digest match in either full
stream. This is metadata comparison, not proof of absent content everywhere.

All eight paths named by the digest-matched historical records are missing in the
current repository at those exact mapped locations. Their names end in `.html`, while
the received bytes are PDFs. Filename extensions must not substitute for byte inspection.
No whole-repository raw/LFS absence claim is made. None of the three PDF digests matches
the separately retained current manual-intake manifest snapshot.

# Chaffee correction and remaining gaps

The retained Chaffee pages declare `<base href="https://www.chaffeecounty.org/">`.
Ten follow-ups (A009–A014 and A021–A024) were resolved against the page directory instead
of that base, creating different URLs from the observed anchors. Additional raw spaces
caused curl preflight failures. Shared holiday, policy and other navigation links
consumed the county cap before the actual planning/building fee and adoption links.
Those attempted URL strings and failures remain unchanged. Zero Chaffee PDFs in this
batch is an access/discovery gap, not evidence that county regulations are absent.

`CHAFFEE_REPAIR_PROPOSAL.json` contains exactly four unopened priorities: planning fees,
building fees, the explicitly linked wildfire-code ordinance and electric-preferred
amendments. Each binds the parent HTML, literal href, HTML base, visible label and
correctly encoded URL. The wildfire anchor says “2025 BOCC Ordinance 2026-02”; both
parts are retained as a label anomaly. The electric amendment's href resolves directly
under the homepage base; an unobserved Documents path was not invented. No request is
executed or authorized merely by this proposal.

Gunnison's land-use source remains a redirect shell. A025/A030 name an unopened
March 5, 2026 amendment slug in Location; no LUR PDF was obtained. The A029 redirect
leads to a personal-data privacy policy, not a code adoption. The 24-row checklist and
45-item backlog are bounded worker reporting, not a complete legal source inventory.

# Intake recommendation and validation

The three verified PDF byte sequences qualify for a separate proposed
`received_review_package` preservation intake, pending normal exact-digest deduplication,
authority/layer validation and root approval. Source transport and time claims must
remain supplied custody claims. A026/A027 recover bytes corresponding to historical
metadata; they are not newly discovered laws. A028 is unmatched within these exact
full metadata comparisons, without a global novelty claim. Do not intake redirect
shells, no-body failures or cookie-bearing logs as legal originals.

Run the portable read-only verifier with Python containing Pydantic, jsonschema,
BeautifulSoup and PyMuPDF:

```sh
python -B validate_audit.py
```

The verifier recomputes the closed file inventory, schemas, every retained body binding,
serial action timings, full legacy comparisons, PDF structural counts, original source
anchors and proposed URL transformations. It does not perform public requests, reopen
the original workspace, certify source acquisition times or redo legal content review.
