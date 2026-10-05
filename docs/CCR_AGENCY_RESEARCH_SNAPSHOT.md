---
status: historical_partial_research_capture
legal_currentness: not_verified
answer_safe: false
---

# Public Health agency source research snapshot

The repository retains a separately scoped historical capture at
`02_Regulations_CCR/_verification/agency_scopes/2026-09-23/public-health-137-138-140/`.
Its manifest SHA256 is
`1d8807b9aff8f42f923dbe1e147fce0821c4580cde967808271c02b660816219`.

The capture binds 20 rule series from three agencies to 65 retained response
associations, including 20 PDF and 20 Word associations. The complete observed
18-agency department catalog is included; 15 agencies remain unexamined within this
capture. These are source associations, not a count of laws in force. The package
contains 70 files and 11,176,618 bytes including its manifest.

It reuses previously retained source responses. No new source requests were made
when building or installing this package. Each original body is unchanged, with
hashes, original URLs, source labels and recorded observation times bound to the
portable metadata. Projected receipt fields are claims from earlier collection;
they do not independently establish transport authenticity or legal currentness.
Private receipt paths and raw HTTP headers are excluded.

Verify it from a repository Python environment:

```sh
python -B -m geode.pipeline.ccr_agency_capture verify \
  --root 02_Regulations_CCR/_verification/agency_scopes/2026-09-23/public-health-137-138-140 \
  --manifest-sha256 1d8807b9aff8f42f923dbe1e147fce0821c4580cde967808271c02b660816219
```

The verifier checks closed membership, exact file identities, the complete catalog,
selected agency listings, rule/version associations and source-row labels. PDF parsing
checks structure; it does not certify visible text. Word checks are explicitly limited
to signatures. There is no PDF/Word equivalence determination or full text review.
The original input-plan digest is retained as an opaque provenance pin; that private
planning package is not necessary to replay the public capture.

Department 16 remains incomplete. This package does not change its canonical state,
the statewide coverage index, the departmental publisher or scheduled monitoring.
It is not part of the completed-department or native-search totals. The old publisher
rejects this distinct schema. See `docs/CCR_AGENCY_CAPTURE.md` for the bounded offline
contract, including its current restriction to these three agencies.

Keep the directory immutable. Its closed manifest disallows added files and detects
changed ones; future corrections or observations need a separate version. A scoped
Git attribute disables newline conversion so that committed source bytes remain exact.
