---
title: Offline whole-rule CCR agency selections (v2)
status: implemented_local_offline_contract
updated: 2026-09-24
---

# Offline whole-rule CCR agency selections

`geode.pipeline.ccr_agency_capture_v2` creates a portable evidence capture from
already retained response bodies. It makes no network requests. The existing v1
contract, departmental collector, publisher, state schema and their caps remain
unchanged. V2 output is a separate format that the departmental state model refuses.

The input is a caller-pinned strict `Plan`: one department ID, explicit agency/rule
selectors, opaque provenance hashes, and up to 80 historical response associations.
Each association identifies a role, parent, retained body hash/size/path, and a small
nonsecret receipt projection. No input module or packet script is imported.

The unchanged maintained CCR parsers replay the complete department section of the
retained catalog, each selected agency's complete listing table, and every selected
rule's history. Every nonarchived version must have its exact displayed PDF and Word
pair. Missing formats, unrelated adopted-part files, extra archive acquisitions,
foreign parents, contradictory citations, truncated HTML and unsupported HTML base
overrides are refused. Labels and dates come from captured source rows; a title
containing “repealed” or “reserved” is retained without changing its source designation.
Listing titles and history-page titles remain separate source observations.

Every catalog agency appears in the capture. Unselected agencies have unknown rule
counts. All rows of a selected listing appear, with unselected rules explicitly
marked `unknown_not_selected`. Archived history rows and their links remain visible,
but their bodies are not selected. This is a bounded selection, never department
completion, legal currentness, verified native text, or an answer-safe legal result.
A source label such as “current” is not a current-law determination.

## Bounds and historical claims

The existing limits are preserved: 15,000,000 bytes per body, 48,000,000 retained
input-body bytes, 50,000,000 total output bytes **including MANIFEST.json**, 100 actual
files including that manifest, and 80 response/URL associations. V2 additionally
limits a selection to 25 whole rules, metadata members to 1,000,000 bytes each, and
structural PDF page counts to 20,000 per package. Exceeding any bound refuses the
package; there is no override or automatic splitting. Shared source bodies may be
stored once, while every distinct URL association and its charged-byte claim remains
counted. The per-response charged-byte claims also total at most 50,000,000 bytes.

Receipt hashes and reported status, URL, interval, content type and byte charges are
supplied historical claims. They are not independent proof of TLS, original wire
completeness or witnessed acquisition. A missing observed final URL remains null;
if one is present, this contract requires exact equality with the requested URL.
Each interval must be ordered, but logical parent order does not invent a global
transport chronology across reused sources captured on different dates. The cutoff
is parsed from the retained welcome page and qualified as a source claim.

PDF checks require the original PDF signature and successful nonencrypted,
nonrepaired structural parsing. Word checks recognize OLE/ZIP signatures only:
`word_signature_only_unparsed` does not establish valid Word structure, readable
text, or PDF/Word equivalence. No native extraction or visual source review occurs.

## Offline commands

Run from the repository with its pinned Python dependencies:

```bash
python -m geode.pipeline.ccr_agency_capture_v2 build \
  --input-root /path/to/retained-input-root \
  --plan /path/to/reviewed/PLAN.json --plan-sha256 EXACT_PLAN_SHA256 \
  --output /path/to/new/capture
python -m geode.pipeline.ccr_agency_capture_v2 verify \
  --root /path/to/capture --manifest-sha256 EXACT_MANIFEST_SHA256
```

`build` reads each body into a bounded hash-verified buffer before deriving metadata.
It publishes schemas before records and copies unchanged body bytes into public
content-addressed paths. Private local receipt paths and raw HTTP headers have no
fields in this contract. Opaque hashes preserve provenance without copying those
private artifacts. Official source HTML and document bodies remain unchanged.

Fresh members are written through exclusive temporary files and atomic replacement;
the closed manifest is written last. An interrupted output is a preserved partial
directory, not a completed capture. Existing directories and interrupted outputs
cannot be overwritten or resumed. All path components must be free of symlinks and
inputs must be regular files. Verification requires an external manifest hash,
exact closed membership, deterministic schemas, every body binding, and a fresh
replay from the captured buffers. It never imports or executes package code.

For a multi-package selection, review the exact expected rule set separately and
prove disjoint selector sets plus exact union. Shared catalog/listing bodies must
retain the same identities. Do not add package rule counts without that proof or
infer a complete department from a union of selected agencies.
