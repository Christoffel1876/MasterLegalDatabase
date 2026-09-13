---
status: source_visual_and_native_compared_pending_root_review
source_id: el-paso-boh-ehs-fees-sd011
legal_currentness: not_verified
translation_equivalence: not_reviewed
---
# English El Paso County Board of Health EHS fees

This is a source-text review of the five-page English Chapter 3, Fee Schedule and Civil
Penalties. It preserves the complete original PDF, five full 300 dpi Poppler page images,
65 service/fee rows in seven groups, all 74 physical grid rows and 148 cells (including
merged-cell nulls), 37 context records and 102 exact native bindings. All 8,060 native UTF-8
bytes remain unchanged. Every nonwhitespace native byte is covered by a row or context
binding; leading blank extraction lines remain in the original native files.

The source SHA256 is
`1b0529fb7514bcc50c0dd36c903ca361f6ab431712b4aebc48bca8e3f5373622` (151,508 bytes).
The exact copied canonical record and its schema preserve the official URL, source ID,
county ownership, received-review-package acquisition method, and actual repository receipt
at 2026-09-12T22:59:48.795762Z. The original Sherlock HTTP acquisition/time is a retained claim,
not independently witnessed by this review. Its historical batch-cap and custody limitations
remain disclosed. No public source request was made here and no canonical record was changed.

## Review sequence and evidence

All five full-page source images were directly inspected before native extraction was
created or opened. The manually entered `PASS1.json` and readable `PASS1.md` were frozen at
00:30:48.343489 UTC on September 13, with a separate `PASS1_FREEZE.json` before the native
step. `NATIVE_EXTRACTION.json` records the subsequent actual local extraction interval,
PyMuPDF version, flags 195, `sort=False`, and every page/candidate byte boundary. These local
receipts document the performed sequence; they are not independent chronology authentication
or a blind external review. No external transcription was consulted for the first pass.

`SOURCE_QA.json` and its schema contain the final additive comparison. `SOURCE_QA.md` is the
readable companion. Source-first inputs remain unchanged. Small first-pass packaging
qualifications concern whitespace, stacked event fee lines, and the removal of an implicit
routine-inspection link from the residential/day-treatment row. No monetary value was changed.
The complete native cell text and geometry remain separate from normalized display wording.

A focused pixel crop of page five's footer was also directly viewed after a visibility check
was requested. It plainly shows black text on white: “Approved by the Board of Health October
25, 2023.” `CROP_RECEIPT.json` binds the exact original PNG and rectangle
`[100, 2980, 2000, 3150]`; the verifier reproduces the crop's pixels without scaling or
image enhancement. APPROVAL5 is visible source text, not merely an invisible text-layer item.

## Source scope and exceptions

The issuer is the **El Paso County Board of Health**; **El Paso County Public Health** is the
administering agency. The document states approval October 25, 2023, effective January 1,
2024, and a 2024 fee schedule. These are printed source claims, not independent confirmation
of enactment, later amendments or current legal applicability. The source URL's 2025/06 and
accessibility-check filename do not establish an operative edition date.

Air Quality, Body Art, Child Care, OWTS, Recreational Water, Retail Food Establishments and
Administrative groups remain distinct. The OWTS group continues onto page three from page
two. Every row retains the general fee authority, failure-to-pay paragraph and all three
Other Notes, including no fees for complaint or communicable-disease investigation visits.
Definitions (1)–(7) and the new-permit asterisk retain explicit row links. Other child-care
inspection definitions remain contextual source statements without invented classification.

The record preserves the OWTS first-system sale row's `$211.50 in 2024 ($368 in 2025)`, the
additional-system row's `$281.00 in 2024`, hourly caps, six-month and two-year periods, and
the Retail Food Establishment License's statutory reference without inventing an amount.
The global per-visit note remains alongside those specific cell statements; no precedence
or fee arithmetic is supplied. Neither `$298.00 1 Event` nor the closing quote without an
opening quote in definition (7) is silently repaired. Paragraph B's exception referring to
“Section 2” is retained and unresolved by this five-page document.

The six-page Spanish source was not opened or merged. Translation equivalence remains
unreviewed. This packet performs no fee lookup integration, rule extraction, currentness,
answer-safety or coverage promotion. Root acceptance is a separate step.

## Portable read-only validation

Using Python with Pydantic, jsonschema and PyMuPDF 1.28.2:

```sh
/private/tmp/geode-status-venv/bin/python -I -B \
  /absolute/path/to/el-paso-ehs-source-qa/validate_review.py --rerender
```

`--rerender` additionally requires Poppler `pdftoppm` and compares every original full-page
PNG byte-for-byte in temporary storage. The captured renderer was Poppler 26.05.0. Omit the
flag when that exact renderer is unavailable; source/native/grid/crop verification still
runs. No verification mode makes a network request or rewrites evidence. A different
renderer version may produce different PNG encodings and must not be silently accepted as
an exact-byte reproduction.

The verifier checks the closed inventory, schemas, exact first-pass/source identities,
recorded sequence, native extraction, complete candidate packaging, all source row/context
associations, table geometry, explicit exception links, original receipt metadata, and the
footer pixel crop. The 15 focused offline tests include a real source replay and 14 deliberate
invalid cases: changed fees/groups/context, wrong repeated-value byte location, candidate
offsets, merged nulls, date/currentness promotion, source substitution and path escape.
Their log and strict receipt are retained. They are a bounded package test, not the repository
full suite. `_PREPARATION_PREIMAGES` preserves earlier validator preparation bytes; the
final manifest binds every final payload without modifying prior source evidence.
