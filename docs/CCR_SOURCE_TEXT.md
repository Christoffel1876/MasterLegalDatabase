---
title: CCR collected-source native text research bridge
date: 2026-09-23
status: offline_research_tool
---

# CCR collected-source native text research bridge

`python -m geode.pipeline.ccr_source_text` creates and searches a **separate research
package** from explicitly pinned CCR collector states and inventories. It does not
collect sources, alter canonical text, reconcile amendments, or answer legal questions.
It reuses the collector's Pydantic models and checks department, rule, source, version,
document URL, hash and size associations before extracting any text.

Every result is `machine_extraction_unreviewed`, `answer_safe: false`, and
`currentness: not_verified`. Native extraction can retain deleted or struck text,
concatenate replacements, omit layout and visual markup, and return empty text from
scanned pages. Exact replay is a machine consistency check, **not visual source QA**.
Use the original PDF and physical page citation to inspect any substantive match.

## Prepare and build

Use a new output directory, preferably beneath a handoff or `.geode_runtime`.
Do not choose a canonical layer, raw archive, control-plane or snapshot directory;
those prefixes are refused. The finite input plan contains one entry per department:

```json
{
  "version": 1,
  "departments": [
    {
      "root": "/absolute/path/to/collector/evidence",
      "department_id": "15",
      "state_sha256": "<exact SHA256 of department-15-state.json>",
      "inventory_sha256": "<exact SHA256 of department-15.jsonl>"
    }
  ]
}
```

The two inputs live under `02_Regulations_CCR/_verification/current/` in that root.
The placeholder hashes above must be replaced with actual hashes. Emit the plan
schema with `InputPlan.model_json_schema()` and validate the plan with
`InputPlan.model_validate_json()` before retaining it. Build with:

```bash
python -m geode.pipeline.ccr_source_text build \
  --plan /absolute/path/input-plan.json --output /absolute/path/new-package
python -m geode.pipeline.ccr_source_text verify \
  --package /absolute/path/new-package --manifest-sha256 EXACT_MANIFEST_SHA256
```

The package preserves exact state/inventory bytes and all sources referenced by
each state, including catalog HTML and unsupported Word/RTF originals. It admits
document links for source-designated `current`, `future`, and `unknown` versions;
history metadata remains intact in the copied inventories and parent records but
history-only documents are not collected or expanded. A `source_repealed` record
retains that classification, rather than being relabeled current.

Each PDF is opened from the same captured byte buffer that passed its source hash
and size check. Extraction is PyMuPDF `get_text("text", sort=False)`, without OCR,
cleanup, Unicode normalization or inferred section structure. Each physical page's
UTF-8 bytes are retained unchanged. Empty native pages and wholly empty native PDFs
remain explicit; no claim is made that they are blank visually. DOC, DOCX and RTF
originals receive `unsupported_format` and zero extracted pages, not invented text
or a successful document-content validation.

## Source-only search

```bash
python -m geode.pipeline.ccr_source_text query \
  --package /absolute/path/new-package --text '8 CCR 1502-1' --mode citation --limit 2
python -m geode.pipeline.ccr_source_text query \
  --package /absolute/path/new-package --text 'retirement' --mode phrase --limit 2
```

Citation mode matches the entire recorded CCR citation, case-insensitively. Phrase
mode is a literal case-insensitive substring match inside each physical page; it
does not join page breaks, normalize whitespace, expand synonyms or apply legal
reasoning. An empty query is refused. The result includes complete matched pages,
their text hashes, original PDF hashes and portable paths, physical page numbers,
all recorded source/version/date metadata, match counts and an explicit truncation
flag. Unsupported and wholly empty native document counts remain visible even in
no-match results. An unmatched query does not establish absence of a requirement.
Source citation suffixes remain exact. Ordinary record IDs stay unchanged; a suffixed
series uses the collector's `<base_id>__rule_<SOS_rule_id>` evidence identity. The
full source citation must still match the retained document URL's filename argument;
searching the unsuffixed citation does not silently include a suffixed series.

## Portable verification and limits

Verification captures all package members once, checks the closed inventory and
schemas, revalidates all input joins, and re-extracts every PDF page from captured
original bytes. Queries perform this verification too; input provenance paths are
never reopened. Matching the supplied manifest hash binds an independently saved
package identity. Without that external pin, verification establishes only internal
consistency of the supplied package. The recorded PyMuPDF version must match the
verification runtime; there is no silent acceptance of a different renderer's output.

Limits are 30 departments, 1,000 sources per collector state, 25 MB per input file,
500 MB of captured input reads (including repeated aliases), 500 MB total package bytes, 4,000
package payload files, 1,000 document associations, 20,000 page associations, and
100 MB native text. Results allow at most 50 complete pages and 2 MB of native text;
the count and truncation flag expose omitted matches. Shared original PDFs/text
are stored once, but rule/version associations remain distinct. Manifest counts
separate association counts from unique original PDFs and physical pages. These
counts are not statewide coverage measures.
The collector's ordinary/default request limit remains 300; 1,000 is its explicitly
selected hard ceiling. The bridge's aggregate limits are unchanged, so a large
department may require its own package rather than combination with other departments.

Missing, LFS-pointer, hash-mismatched, symlinked or oversized inputs fail before
publication. PDF magic, parseability, encryption and parser-repair status are checked;
encrypted or repaired PDFs are refused for explicit follow-up. Output creation is
exclusive, with atomic member writes and the final manifest written last. Ordinary
write exceptions clean up the new package; process termination may leave an incomplete
directory that verification rejects. There is no overwrite, resume, network access,
or power-loss durability guarantee. A new package is required after any input change.

Focused offline tests:

```bash
python -m pytest tests/test_ccr_source_text.py \
  --cov=geode.pipeline.ccr_source_text --cov-branch --cov-fail-under=90
```
