---
status: reviewed_prepared_only
reviewed_at: 2026-09-13
scope: four_existing_pairs_eight_fixed_pdf_sources
public_source_requests: 0
linux_execution_verified: false
installed_or_enabled: false
legal_currentness: not_verified
---

# Independent review of the corrected 87-input CI proposal

The corrected proposal passed 64 offline tests (44 author cases and 20 independent cases), exact final schema checks, and four actual readiness subprocesses in a fresh temporary corpus containing only the 87 independently Git-tracked, non-LFS dependencies, the streamed tracked raw manifest, and final runner/configuration. The excluded user-owned file was absent. No public HTTP, installation, scheduler activation or source promotion occurred.

The final plan removes only the unrelated `geode/schemas/models 2.py` dependency from the earlier 88-input plan. Source IDs, custody, baseline PDFs, selections and all caps are unchanged. Runner syntax differs only in its configuration digest. Test behavior is unchanged after removing annotations and the annotation-only import; documentation adds frontmatter and reflects 87 inputs. The workflow is byte-identical to the reviewed version. The independent test copy changes only the fixture directory and final runner hash, while preserving its assertions.

## Explicit corrections to the retained historical review

The earlier 88-input ordinary-checkout conclusion is withdrawn. Its local sparse run copied an untracked, user-owned file inadvertently included by the preparation's schema glob. That local success could not establish a clean tracked checkout. Initial tracking checks covered 79 dependencies; the later nine additions were hash-checked but not all rechecked for tracking in that review. The corrected independent run checks every one of the final 87 dependencies, and no user-file content is carried here under any name. Two tracked policy files currently differ from index bytes; their approved versions must be committed before a GitHub checkout can satisfy the final pins.

A separate earlier reasoning error is also preserved and withdrawn: completed reports containing denied responses were incorrectly proposed as actual maintained-producer behavior. The pinned producer requires completed status only when all source observations are changed/unchanged and stop_reason is null. Actual denial produces stopped/exit 2. The meaningful narrower regression is a valid stopped report with otherwise complete observations and a non-null stop reason. The final wrapper uses the verified producer status, retains incomplete source outcomes, and rejects contradictory completed-denial fixtures.

`historical-audit/` is the exact prior audit except one declared user-content member, whose identity remains in REVIEW.json and the unchanged original manifest. It is an explicitly incomplete historical subset. Do not execute its copied historical verifiers or builders; their original full-closure assertion cannot pass after this required omission. The original full handoffs remain outside publication unchanged. Historical statements remain readable as history, with the corrections above governing this review.

`author-public-selected/` contains only six selected metadata artifacts from the separately verified 217-payload author public revision. Its full manifest is an external identity reference; this selected subset does not claim that all author payloads are copied here. The ten final installation files are separately preserved under `final/`. This audit installs none of them.

## Scope and residual gates

The fixed four pairs remain serial, with readiness for all four before execution, at most 16 source HTTP events, 16 MB bodies, and 1,200 seconds of source-run windows. A 40-minute GitHub job timeout includes separate dependency/test/verification work. The default is readiness only. Public execution requires the explicit workflow input or reviewed repository enable variable; there are no automatic baseline changes, enrollment, publication, retries or promised external notifications. Always-upload behavior is conditional on a surviving runner/upload step; cancellation, timeout or service failures can still prevent artifact retention.

Actual checks ran on macOS with the existing local Python environment. Linux/Python 3.11 execution, dependencies on a fresh cloud runner, remote deployment and a separately authorized live pilot remain unverified. Tracked baseline availability does not repair unrelated missing LFS indexes or establish legal currentness. The script and selected URL scope do not discover replacement editions automatically.

## Portable read-only verification

Run `python -B validate_public.py --root <copied-public-audit-directory>`. The verifier checks the closed public inventory, declared historical omission, exact final selection/pin metadata, typed readiness evidence and absence of the excluded content hash. It needs Pydantic and jsonschema, no original repository, credentials, network or historical-code execution. The retained original probe scripts describe executed local checks and are evidence, not portable entry points.
