---
status: offline_agency_scope_contract
scope: retained_department_16_agencies_137_138_140
---

# Offline CCR agency capture

`geode.pipeline.ccr_agency_capture` replays a caller-pinned retained planning packet
into a fresh, portable research directory. It performs no HTTP requests, source
extraction, canonical installation or publication. It does not change the department
collector, schema, publisher or their limits. The departmental publisher rejects this
separate capture schema.

This first contract is deliberately fixed to department 16's retained 18-agency catalog,
agencies 137/138/140, their 7/7/6 rules and 65 response associations. It is not a general
agency collector. The full catalog remains present; all 15 other agencies are explicitly
`unknown_not_evaluated`, with no zero-rule or no-historical-collection claim.
`department_complete`, `canonical_installation`, publisher admissibility and `answer_safe`
are false. Legal currentness remains unverified.

## Input and source fidelity

The input's exact `PLAN.json` SHA256 is mandatory. Maintained parser code reads the
plan and all referenced files as bounded captured buffers, verifies their hashes/sizes,
and derives from those buffers. It never imports or executes Python files from the
input packet. Symlinked paths and nonregular files are refused. Each original response
body retains its exact bytes and hash; duplicates retain every URL/rule association.

The existing maintained strict HTML parser requires complete documents and validates
selected rule tables and full version rows. Source-label text must equal its exact
parsed version-row label; a re-pinned fabricated label or bare-anchor listing is refused.
Validation replays the full catalog, exact parent href/handler joins, department/agency/
rule/citation/version identities, complete selected listings, source current/future
labels, chronological recorded intervals and response byte accounting. All 65 requested
URLs remain exact source associations; supplied historical receipt fields do not prove
independently witnessed transport. No new cutoff is invented: `classification_cutoff`
is null, and historical source labels are not reclassified as current law.

The input plan and auxiliary provenance files remain unchanged locally. The output
contains a typed public projection of the plan: original receipt path claims are blank,
nonbody provenance files are omitted, and the original input plan SHA is an opaque pin.
The output verifies its public projection and source bodies; absent private originals
cannot be reconstructed or authenticated from that pin alone. Raw HTTP headers are
never copied by this importer. Original receipt hashes, source URLs, status, recorded
times, content type and body/hash/size accounting remain explicit.

PDFs must have the expected signature and parse without repair/encryption; physical
page counts are structural observations only. Word bodies receive
`word_signature_only_unparsed`, never a complete format-validation or PDF-equivalence
claim. No native/visual review or legal accuracy claim is made.

## Bounded creation and verification

Run from a repository Python environment with its normal Pydantic, BeautifulSoup and
PyMuPDF dependencies. INPUT is the retained preparation directory; OUTPUT must be a
new path outside INPUT. PIN is the exact input-plan hash reviewed before the command.

```sh
python -m geode.pipeline.ccr_agency_capture build \
  --input INPUT --plan-sha256 PIN --output OUTPUT
```

The command returns the exact new manifest hash. Verify after creation or relocation:

```sh
python -m geode.pipeline.ccr_agency_capture verify \
  --root OUTPUT --manifest-sha256 OUTPUT_MANIFEST_SHA256
```

The output includes the unchanged response bodies, projected `PLAN.json`, strict
`CAPTURE.json`, deterministic schemas and a closed `MANIFEST.json`. No absolute runtime
path is needed to replay it. Hash checking precedes semantic replay; a resealed record
still must agree with all captured associations and scopes.

Per-file reads are capped at 15MB, aggregate package bytes at 50MB, and members at 100.
The imported proposal's 80-event/80-URL, 30-second/900-second future ceilings remain
historical proposed metadata, not an activated run or a claim that the complete old
collection fit those limits. The selected historical response byte total counts each
response, while the portable file total counts shared bodies once. Both are bounded.
No existing departmental or native-text package cap is raised.

Schemas are written before records, each member uses a fresh temporary file followed
by atomic replacement, and the manifest is published last. Existing outputs are refused.
An interruption can leave a partial directory or `.tmp`; it is preserved and cannot be
resumed or represented as verified. Use a different output path after investigating.

Focused offline tests use synthetic fixtures, cover meaningful mutations, no-overwrite
and interruption behavior, and demonstrate explicit refusal by the existing publisher.
They do not contact source websites or substitute for legal/source review.
