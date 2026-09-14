---
title: Boulder source ownership correction
reviewed: 2026-09-10
status: active_registry_corrected_historical_repair_pending
legal_currentness: not_verified
publication_scope: local_only
---

# Boulder source ownership correction

Atlas verified Sherlock's three ownership proposals against the official
[City building-code catalog](https://bouldercolorado.gov/services/building-codes-and-regulations)
and [City appointment page](https://bouldercolorado.gov/building-codes-regulations-appointment-bookings).
These are City of Boulder publications. The appointment page offers help and
booking; it is not an administrative-rules manual. The
[County homepage](https://bouldercounty.gov/) and
[County building-code page](https://bouldercounty.gov/property-and-land/land-use/building/building-code-amendments/)
identify the separate county government and its sources.

## Changes and preserved history

- Retired `county_boulder_code` and
  `county_boulder_county_codes_3890a99a2483` from active county registration.
  Their City catalog URL already has the municipal entry
  `municipal_boulder_building_codes`; no duplicate municipal source was added.
- Retired `county_boulder_administrative_rule_manuals_484ef287b62c` from active
  county registration. The booking page was not added as legal text.
- Added the distinct identity/discovery source `county_boulder_homepage` at the
  official County homepage. All 64 county identities remain registered.
- Corrected only Boulder County's ordinary authority metadata row. Removed ten
  source-ID memberships from seven legacy county-coverage cells. Other sources
  and category statuses remain historical claims awaiting review.
- Stored the old entries, exact affected IDs and input hashes in
  `_CONTROL_PLANE/LOCAL_SOURCE_OWNERSHIP_CORRECTIONS.json`. Prior versions of
  each changed file were snapshotted. No original source, historical download
  record, source hash, OCR text or reviewed legal excerpt was rewritten.

The 27 historical download rows carrying these IDs remain preserved. They do
not prove that the underlying pages are County law. The affected review queue
has 86 pending candidates from 17 parent records. Four have mappings and
automated decisions; all four decisions are `auto_quarantined`. No scoped
candidate is accepted as current law by this correction.

## Required downstream repair before regeneration

This is a data correction, not an implemented pipeline exclusion. The existing
legacy ingestion, coverage-building and promotion code does not enforce the
retirement audit. Before rerunning those paths, implement and test an exclusion
for the retired source IDs and affected parent/review IDs, then re-review source
ownership using actual bytes. An automatic County-to-City relabeling of their
extracted duties would be unsound.

The County index and rule metadata are missing Git LFS objects in this checkout.
Their pointer files were left unchanged. Recover those objects before repairing
the inherited index, dependent rule units, mappings and retrieval outputs.
The historical freshness report and semantic queues also remain unchanged;
they are not evidence that these source attributions have been repaired
throughout the system. Entire-corpus attribution safety is not certified.

## Verification and discovery boundary

All changed registry identity/URL fields, coverage structures, authority records
and the correction audit were validated with Pydantic before writing. Only the
Boulder authority metadata line changed. Historical files' hashes were checked
again after the writes. This change adds no legal text or accepted coverage.

Official City pages were available through parsed web-page access. Separate
direct HTTP attempts returned 403; those retained responses are error pages,
not legal-source bytes. The County building-amendments referral returned 200
and was retained with a hash outside the repository. No fresh City byte equality
or full document transcription review is claimed.

Sherlock's 003 package contains 24 checklist rows and 20 priority leads. Seven
priority URLs have exact historical download-manifest matches; ledger absence
does not make them newly discovered sources. Complete code text, exact fee and
adoption instruments, amendment chains, inspection scope and legal currentness
still need intake. The County's
[land-use update notice](https://bouldercounty.gov/property-and-land/land-use/planning/land-use-code/)
specifically describes phased incorporation of later amendments; the linked
code PDF alone does not establish a fully updated code.

Local handoff audits and the unchanged bot reports are under
`handoffs/atlas-reviews/sherlock-source-discovery-003/` in the parent Project Geode
workspace. Sherlock has received the next bounded assignment, discovery 004,
covering Larimer County and City of Fort Collins separately.
