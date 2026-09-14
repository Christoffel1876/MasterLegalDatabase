---
status: accepted_with_recorded_limits
checked_at: 2026-09-13
scope: local_manual_watch_ci_installation_and_new_wrapper_publication_boundary
source_requests: 0
canonical_writes: false
legal_currentness: not_verified
---

# Installed CI acceptance

All ten installed files match the reviewed final public proposal byte for byte. The root installation receipt matches SHA256 `5a9e25492d0fe21f1a2ff44a90d705550cb1eb7b8bd9733ea627fc9257819d5b`; its schema and the 494-payload canonical wrapper inventory validate. Both copied top-level public verifiers pass, including the proposal's optional current-repository check. All 87 selected runtime inputs match their hashes and remain Git-tracked, non-LFS files. No full suite or public HTTP was run by this audit.

The publication check covers the 22 wrapper roots enumerated in ACCEPTANCE.json, derived from staged additions plus remaining untracked paths at the check time. All 3,051 ordinary files were inspected for excluded basenames, then every file was hashed by streaming SHA256: 200,144,918 bytes, zero matches to the excluded personal file's exact digest. `HASHED_WRAPPER_FILES.jsonl` contains validated path/size/digest records. This is a bounded scan of new canonical wrappers, including their ignored children, not a claim about every historical repository file.

The original `geode/schemas/models 2.py` remains outside these wrappers with its prior 36,560-byte identity, SHA256 `24554bb0b1dd44a41e6dcb7db72e17e9f4a739a6b7d5ccd9fd59a4edd12aa411`, verified before and after the checks. Its contents were never copied into this audit. Matching present bytes does not certify an unwitnessed historical sequence. The user's other excluded document basename was also absent from the selected wrappers; no claim is made about its contents.

Staging occurred between initial discovery and the first audit scan, leaving only the two excluded personal files untracked. That initial zero-root attempt is retained under `preimages/before-staged-scope/` and explicitly withdrawn as publication evidence. The final check uses the union of staged additions and untracked paths, obtaining the same 22 wrapper roots seen initially. The final acceptance and full hash stream govern this audit.

The canonical wrapper preserves the public 87-input proposal and public independent audit exactly. Their historical subsets intentionally omit the personal file. Old full-packet verifiers remain historical evidence and were not executed. Preparation-stage document frontmatter is qualified by the later typed installation receipt; it does not assert deployment.

No runtime issue was found within this scope. Local installation does not establish a Linux run, remote deployment, scheduler activation, a successful live pilot, unconditional artifact retention, source currentness or legal effect. The parent task owns the separately running full suite and the eventual checkpoint. Approved policy bytes must be committed before a cloud checkout can satisfy their pins.

## Read-only verification

Run `python -B validate_acceptance.py --root <copied-audit-directory>` for portable metadata closure and scan-record verification. Add `--repository-root <repository>` to check the actual installed files, all 87 input hashes and every canonical wrapper payload again. The optional mode reads local files only and performs no process execution, tests or source requests. Pydantic and jsonschema are required.

The five copied files under `wrapper-metadata/` are a clearly scoped subset. Their full inventory identifies the external canonical wrapper; this audit does not duplicate all 494 wrapper payloads. `executed_check.py` records the actual audit procedure and is not the portable entry point.
