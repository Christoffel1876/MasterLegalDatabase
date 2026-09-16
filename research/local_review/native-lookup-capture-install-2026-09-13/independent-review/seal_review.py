"""Preserve the bounded independent closeout review; no production or network writes."""
from __future__ import annotations

import difflib
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

HERE = Path(__file__).resolve().parent
PROPOSAL = HERE.parent / "native-lookup-captured-buffers"
FINAL = "1f4da2ec117996c21a2676bdd82226018ecf4ad0e583297c1f52ece43d1ffe55"


class Asset(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    path: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    size_bytes: int = Field(ge=0)


class Review(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    prepared_at: AwareDatetime
    status: Literal["scoped_acceptance_for_parent_integration_review"]
    final_script_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    proposal_manifest: Asset
    historical_injections_replayed: Literal[9]
    rejected: Literal[6]
    returned_without_injection: Literal[3]
    exact_normal_outputs: Literal[18]
    sources: Literal[9]
    unchanged_model_asts: Literal[44]
    unchanged_douglas_pueblo_helpers: Literal[9]
    independent_findings: list[str]
    limits: list[str]
    public_requests: Literal[0]
    production_writes: Literal[0]


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def write_once(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(raw)


def main() -> None:
    raw = (PROPOSAL / "proposed/research_source_lookup.py").read_bytes()
    if digest(raw) != FINAL:
        raise ValueError("Final reviewed implementation differs")
    manifest = (PROPOSAL / "FINAL_MANIFEST.json").read_bytes()
    release = (PROPOSAL / "tests-release.log").read_bytes()
    if b"430 passed" not in release or b"FAILED " in release:
        raise ValueError("Final combined run is not complete and passing")
    probes = json.loads((HERE / "PROBES_FINAL.json").read_bytes())
    assert probes["script_sha256"] == FINAL and probes["status"] == "PASS"
    assert len(probes["normal_outputs"]) == 18
    for name in ["proposed/research_source_lookup.py", "proposed/test_native_lookup_capture.py",
                 "preimages/research_source_lookup.py", "tests-final.log", "tests-release.log",
                 "tests-diagnostic-compatibility.log", "BASELINES.json", "README.md",
                 "FINAL_MANIFEST.json", "FINAL_MANIFEST.schema.json", "VERIFICATION.json",
                 "VERIFICATION.schema.json", "prior-audit/probe_family.py"]:
        write_once(HERE / "checked-inputs" / name, (PROPOSAL / name).read_bytes())
    before = (PROPOSAL / "preimages/research_source_lookup.py").read_text()
    patch = "".join(difflib.unified_diff(before.splitlines(True), raw.decode().splitlines(True),
                                      fromfile="installed-preimage", tofile="final-proposed"))
    write_once(HERE / "checked-final-diff.patch", patch.encode())
    review = Review(
        prepared_at=datetime.now(timezone.utc),
        status="scoped_acceptance_for_parent_integration_review",
        final_script_sha256=FINAL,
        proposal_manifest=Asset(path="checked-inputs/FINAL_MANIFEST.json",
                                sha256=digest(manifest), size_bytes=len(manifest)),
        historical_injections_replayed=9, rejected=6, returned_without_injection=3,
        exact_normal_outputs=18, sources=9, unchanged_model_asts=44,
        unchanged_douglas_pueblo_helpers=9,
        independent_findings=[
            "Reviewed the full preimage-to-proposal diff and final two diagnostic wrappers.",
            "Captured pinned buffers now supply QA/native wording, custody, and asset identities.",
            "Nine historical temporary-file substitutions did not inject returned evidence.",
            "All eighteen full JSON/Markdown outputs match preserved fixtures exactly, with only "
            "the repository prefix normalized; all forty-four result models are AST-identical.",
            "The prior 428-pass/two-failure attempt still refused both altered inputs. The final "
            "wrappers preserve those original diagnostic assertions without weakening checks.",
            "No remaining actionable consumed-evidence bypass found within the inspected repair.",
        ],
        limits=[
            "Independent testing covers nine preserved counterexamples and eighteen complete "
            "normal outputs; the author's final combined suite is separate evidence.",
            "BASELINES.json is a historical receipt for earlier 53d3fd02 code. It is not a "
            "final-code run; this independent final replay binds the final 1f4da2ec implementation.",
            "This accepts the prepared repair for parent integration review, not an installation "
            "or repository-wide regression claim.",
            "File references describe captured snapshot bytes; files may subsequently change. "
            "This is not a general guarantee against arbitrary concurrent filesystem attacks.",
            "Source-only scope, legal_currentness not_verified and answer_safe false remain; "
            "there was no new PDF review, source collection, or canonical intake.",
            "The Pueblo County intake proposal remains frozen and unapplied in this review.",
        ], public_requests=0, production_writes=0,
    )
    payload = review.model_dump_json(indent=2) + "\n"
    Review.model_validate_json(payload)
    write_once(HERE / "REVIEW.json", payload.encode())
    write_once(HERE / "REVIEW.schema.json",
               (json.dumps(Review.model_json_schema(), indent=2) + "\n").encode())
    text = """---
reviewer: Atlas independent closeout reviewer
status: scoped_acceptance_for_parent_integration_review
legal_currentness: not_verified
production_writes: 0
public_requests: 0
---

# Older native-adapter captured-buffer repair

The final prepared repair passes this bounded independent review. Its implementation is
`1f4da2ec117996c21a2676bdd82226018ecf4ad0e583297c1f52ece43d1ffe55`.
Parent integration and installed-path regression remain separate steps.

I read the complete implementation diff and final two diagnostic wrappers. The seven older
adapters now use hash-verified captured buffers for returned QA/native text, custody and asset
identities. Both newer Douglas/Pueblo adapters and all 44 result models are structurally unchanged.

Actual independent probes replayed all nine preserved temporal substitution cases in temporary
fixtures: six refused and three returned without the injected evidence. All 18 complete JSON and
Markdown outputs for nine sources were byte-identical to the frozen normal fixtures after only
repository-path normalization. No production files or source originals were modified.

The earlier combined run was **428 passed, two failed**, both diagnostic compatibility assertions;
the altered evidence was still refused. That log is retained. The final wrappers preserve both
assertions, the targeted two cases pass, and the separately retained author release log records
**430 passed**. I did not rerun the entire suite. `BASELINES.json` remains the historical earlier
53d3fd02 receipt; `PROBES_FINAL.json` is the independent final-code comparison.

This is a source-integrity repair, not new source review or legal promotion. Paths identify
captured bytes and do not promise files cannot change later. Broader hostile-filesystem assurance
and installed repository-wide regression are outside this bounded check. The pending Pueblo
County intake remains unapplied. `checked-inputs/` is a selective evidence copy, not a relocated
complete author package; its copied author manifest references additional original payloads.
Historical probe scripts contain external fixture paths;
`verify_review.py` validates this closed audit without executing any probe or network access.
"""
    write_once(HERE / "REVIEW.md", text.encode())
    assets = []
    for path in sorted(HERE.rglob("*")):
        if path.is_symlink():
            raise ValueError("Symlinked audit member")
        if path.is_file():
            body = path.read_bytes()
            assets.append(Asset(path=path.relative_to(HERE).as_posix(), sha256=digest(body),
                                size_bytes=len(body)).model_dump())
    write_once(HERE / "MANIFEST.json", (json.dumps(assets, indent=2) + "\n").encode())
    print(json.dumps({"review_sha256": digest(payload.encode()),
                      "manifest_sha256": digest((HERE / "MANIFEST.json").read_bytes()),
                      "payloads": len(assets)}, indent=2))


if __name__ == "__main__":
    main()
