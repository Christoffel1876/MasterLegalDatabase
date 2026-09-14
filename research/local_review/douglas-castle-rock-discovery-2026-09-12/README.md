---
title: Douglas County and Castle Rock public preservation subset
status: public_preservation_only
legal_currentness: not_verified
answer_safe: false
private_header_originals_present: false
---

# Public preservation subset

This package preserves **686 original files exactly**: 685 public payloads and the original
manifest. **All 31 original `events/E*/private.headers` files are omitted**, including the
24 without recorded sensitive fields. The original local handoff remains unchanged.
`OMISSIONS.json` and `OMISSIONS.md` identify every omitted file by path, size and SHA256 and
bind its retained public-header derivative. Seven originals contained Set-Cookie fields.

Before omission, the preparer independently reconstructed every public-header derivative
from its local original and checked the recorded removed-field names. The distributable
package contains no private header bytes. Its portable verifier **cannot replay that
derivation**; it checks public hashes/fields and hash-bound omission claims instead.

The privacy scan found no exact retained occurrence of the seven excluded credential values
in any of the 686 copied files. All 31 public header files were checked for sensitive field
names. This is a bounded scan of known response credentials, not a guarantee against every
possible privacy concern. Exact public HTML, historical local paths and Windows custody-path
claims remain unmodified. Display HTML passively; do not execute embedded page scripts.

# Supported read-only verification

Run this entrypoint from any working directory:

```sh
python -I -B /absolute/package/verify_public.py --root /absolute/package
```

The recorded environment is Python 3.14.3, PyMuPDF 1.28.2, Pydantic 2, jsonschema and
BeautifulSoup. Verification requires the recorded PyMuPDF version to reproduce the native
text and 150-DPI image bytes. The entrypoint checks the closed public inventory before
importing pinned original read-only helpers. It verifies public schemas, event reservations,
retained response metadata, explicit redirect locations, HTML derivatives, all **403 native
pages** and all **18 saved full-page renders**, plus the frozen full legacy comparison.
It never calls capture/build functions, opens a network source or writes evidence files.

**Do not run `frozen/verify_discovery.py`, capture helpers, PDF inspection builders or other
historical tools.** They are preserved historical evidence, not public-package entrypoints.
The original full verifier expects the omitted private files and cannot pass here. Some
builders can write files or issue requests if explicitly invoked. Their historical defaults,
absolute paths, commands and cutoff times do not authorize any new activity.

# What the source discovery establishes

The historical discovery made 31 explicit events against 30 exact requested URLs. It retained
21 HTTP 200 responses, eight explicit 301 responses, one 403 and one local DNS failure, with
14,428,668 body bytes. Eight PDFs have 403 structural pages. All native page text is preserved
as **unreviewed machine text**. The package records only **14 directly viewed full pages**;
18 mechanical rerenders do not create additional visual reviews or certify all 403 pages.
This preservation task adds no visual or fee-table review.

`_build_preimages/` retains the first successful verification and wrapper/manifest revisions
before line wrapping and tightening the exact event-to-public-derivative binding. Its earlier
public file count predates those additive preimages;
the current `PUBLIC_MANIFEST.json` defines the final file set. Historical preimages are not
alternative entrypoints.

Douglas County and the Town of Castle Rock remain separate authorities. The 12 priorities,
24 category rows and 381 unopened leads are source-discovery records, not legal completeness
or authorization for bulk collection. The county's distinct fire instruments retain their
unsigned/blank-final-date or placeholder-draft qualifications. The provider 403, town code
application shell, mixed county/state health-fee authorities, older fee/manual dates and
unopened incorporated codes remain limitations. See the unchanged `frozen/REPORT.md` and
typed discovery for exact source statements and sample-page references.

# Historical custody limitations

The original report's `private_header_originals_present: true` describes its complete local
source folder, **not this public subset**. Original manifest entries and event receipts still
refer to missing private headers; the omission table explains those intentional exclusions.

`BASELINE_RECEIPT.json` records exact working-file hashes separately from observed Git refs.
No committed-blob equality is inferred. The historical 59/60 manual intake counts, 48,390-line
legacy input, unresolved LFS pointer bytes and local raw-size probe are retained claims at
their original times. This package does not update them to a later repository state or replay
the old local raw-size probe. No canonical intake, registry, raw archive, coverage, legal date
or currentness has been promoted by preservation.
