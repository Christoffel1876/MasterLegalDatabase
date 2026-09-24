---
title: Project Geode control plane
updated: 2026-09-10
---

# Project Geode Control Plane

The control plane contains the small, AI-readable files that describe Geode's
backend knowledge layer: corpus schema, sources, agencies, freshness,
timelines, manifests, reliance boundaries, and update history.

The orchestration engine reads these files before retrieving legal text. They
are part of hard orchestration: code uses them to decide what exists, what is
fresh, what is trusted, and what must be disclosed as missing. Prompts may
summarize these rules for an LLM, but the control-plane files and validation
code are authoritative.

Current operational handoff files:

- `QUALITY_STATUS.json` is the first-read quality map for the corpus. It shows each layer's
  current status, open review limits, and next quality actions.
- `DOWNLOAD_SAFETY_CHECKPOINT.json` records the safety state before the next major source download.
- `NEXT_DOWNLOAD_DASHBOARD.json` identifies the next recommended download area and current blockers.
- `../docs/PUBLICATION_CHECKLIST.md` must be completed before public-facing GitHub publication.

- `LOCAL_COVERAGE_LEDGER.json` separates preserved local source evidence from missing
  collection, legal-currentness and review work. It includes dated directory reconciliation
  and a full category checklist for each identified authority. See
  `../docs/LOCAL_COVERAGE_LEDGER.md` for its validation and collection process.

- `MUNICIPAL_EXPORTS_2026-09-10.json` binds two recovered municipal publications
  to official referrals, publisher identities, source hashes and linked images.
  Its explicitly derived endpoint/redaction summaries are distinct from exact
  original source files. See `../docs/LOCAL_TEXT_RECOVERY.md` for saved native text,
  OCR page receipts, checked excerpts and the fee reconciliation study.
