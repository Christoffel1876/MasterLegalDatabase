---
title: Checked-source lookup verification
verified: 2026-09-11
legal_currentness: not_verified
---

# Checked-source lookup verification

The standalone Grand Junction fire-fee lookup passed the full repository suite:
**1,814 tests passed, 32 warnings, 201.88 seconds**. The 36 new focused cases
cover source tampering, resealed wrong row associations, unknown dates, missing
services, current-law refusal, numeric matching, duplicate labels and read-only
execution. The lookup script has **96.46% combined line/branch coverage**; the
existing geode package remains at 77% full-suite coverage. Do not confuse these
two coverage measures with legal-source coverage.

Root executed actual CLI calls both inside and outside the repository, checked
returned source spans and reviewed Markdown output. Plato independently checked
all 57 rows and the final request/refusal boundaries. One search defect found
during review (zero matching a suffix of larger numbers) was fixed and covered
by regression cases before the final suite.

[Usage and limits](../../RESEARCH_SOURCE_LOOKUP.md) explains this one-source
command. It does not integrate the other 45 manual originals, alter canonical
indexes or restore broad retrieval. Every result remains source-only with
currentness unverified and legal dates unknown. Local search does not check for
newer government publications.

`VERIFICATION.json` records script/test hashes, the exact full-suite command,
scoped review results and copied output hashes. `full-tests.log` is the complete
root execution output. `lookup-coverage.json` is the focused run's measured
coverage, independently read by root. The two example outputs are exact CLI
stdout captures, preserved with their source qualifications.
