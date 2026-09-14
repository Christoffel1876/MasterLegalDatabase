"""Seal the tested handoff, preserving the historical preliminary state unchanged."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import jsonschema
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2] / "MasterLegalDatabase"
TX = Path("research/local_review/douglas-pueblo-intake-2026-09-13/prepared-transaction")
sys.path.insert(0, str(ROOT))
from geode.pipeline.manual_source_intake import ManualSourceIntakeRecord


class Strict(BaseModel):
    """Reject unknown fields and implicit type conversion."""
    model_config = ConfigDict(extra="forbid", strict=True)


class Asset(Strict):
    """An exact local file, relative to its declared root."""
    path: str
    sha256: str = Field(pattern="^[a-f0-9]{64}$")
    size_bytes: int = Field(ge=0)


class ActualBinding(Strict):
    """Typed rendering of the two already completed canonical intakes."""
    status: Literal["prepared_not_installed"]
    sources: Literal[63]
    reviewed: Literal[24]
    unknown: Literal[39]
    actual_intakes: list[ManualSourceIntakeRecord] = Field(min_length=2, max_length=2)


class Final(Strict):
    """Completed metadata proposal without claiming installation or current law."""
    status: Literal["prepared_tested_not_installed"]
    prepared_at: AwareDatetime
    actual_repository_received_at: AwareDatetime
    intake_completed_at: AwareDatetime
    original_sources: Literal[63]
    review_mappings: Literal[24]
    unmapped: Literal[39]
    old_source_rows_preserved: Literal[61]
    old_review_joins_preserved: Literal[22]
    test_cases_passed: Literal[79]
    branch_inclusive_coverage_percent: float = Field(ge=90, le=100)
    canonical_receipt: Asset
    repository_bindings: list[Asset]
    source_record_ids: list[str] = Field(min_length=2, max_length=2)
    production_changes_by_preparation: Literal[False]
    legal_currentness: Literal["not_verified"]
    answer_safe: Literal[False]
    limitations: list[str]


class Manifest(Strict):
    """Closed handoff payload inventory, excluding its own two manifest files."""
    status: Literal["frozen_prepared_not_installed"]
    prepared_at: AwareDatetime
    files: list[Asset]


def asset(base: Path, relative: str) -> Asset:
    """Hash an ordinary file in one explicit root."""
    path = base / relative
    if path.is_symlink() or not path.is_file():
        raise ValueError("Not an ordinary file: " + relative)
    with path.open("rb") as handle:
        digest = hashlib.file_digest(handle, "sha256").hexdigest()
    return Asset(path=relative, sha256=digest, size_bytes=path.stat().st_size)


def put(path: Path, body: bytes) -> None:
    """Require a new output or byte-equal previous output."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != body:
            raise ValueError("Refusing changed existing output: " + str(path))
    else:
        with path.open("xb") as handle:
            handle.write(body)


def write_model(path: Path, model: BaseModel) -> None:
    """Validate strict serialized content before durable writing."""
    body = model.model_dump_json(indent=2) + "\n"
    type(model).model_validate_json(body)
    put(path, body.encode())
    schema = json.dumps(type(model).model_json_schema(), indent=2) + "\n"
    put(path.with_suffix(".schema.json"), schema.encode())


def main() -> int:
    """Bind final receipt and tests, copy custody, and close this preparation only."""
    binding = ActualBinding.model_validate_json((HERE / "ACTUAL_BINDING_RESULT.json").read_bytes())
    put(HERE / "ACTUAL_BINDING_RESULT.schema.json",
        (json.dumps(ActualBinding.model_json_schema(), indent=2) + "\n").encode())
    receipt_rel = (TX / "execution/RECEIPT.json").as_posix()
    receipt_asset = asset(ROOT, receipt_rel)
    if receipt_asset.sha256 != "7ba1d9fa2f6c58a504551692a1d6ebed3ac8e5fed8d0dcbe459f32ca3bacf620":
        raise ValueError("Actual root receipt differs")
    receipt = json.loads((ROOT / receipt_rel).read_bytes())
    jsonschema.validate(receipt, json.loads((ROOT / TX / "RECEIPT.schema.json").read_bytes()))
    if receipt["intent"]["records"] != [r.model_dump(mode="json") for r in binding.actual_intakes]:
        raise ValueError("Actual binding and root receipt differ")
    for name, relative in [
        ("RECEIPT.json", TX / "execution/RECEIPT.json"),
        ("RECEIPT.schema.json", TX / "RECEIPT.schema.json"),
        ("INTENT.json", TX / "execution/INTENT.json"),
        ("INTENT.schema.json", TX / "INTENT.schema.json"),
    ]:
        put(HERE / "custody" / name, (ROOT / relative).read_bytes())
    spec = importlib.util.spec_from_file_location("final_inventory_models",
                                                 HERE / "proposed/manual_review_inventory.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    plan = module.JoinPlan.model_validate_json((HERE / "proposed/join-plan.json").read_bytes())
    put(HERE / "proposed/join-plan.schema.json",
        (json.dumps(module.JoinPlan.model_json_schema(), indent=2) + "\n").encode())
    refs = {receipt_rel, (TX / "execution/INTENT.json").as_posix(), plan.manual_manifest.path,
            "_CONTROL_PLANE/MANUAL_SOURCE_INTAKE_LEDGER.jsonl"}
    for row in binding.actual_intakes:
        refs.add(row.archive_path)
    for authority in plan.authorities[61:]:
        refs.add(authority.provenance.artifact.path)
        refs.add(authority.verified_http.document.artifact.path)
    for review in plan.reviews[22:]:
        refs.update((review.review.path, review.review_schema.path))
    preliminary = json.loads((HERE / "PRELIMINARY.json").read_bytes())
    refs.update(s["acceptance"]["path"] for s in preliminary["selections"])
    coverage = json.loads((HERE / "coverage.json").read_bytes())["totals"]["percent_covered"]
    if "79 passed" not in (HERE / "TEST_RESULTS.log").read_text():
        raise ValueError("Missing successful prepared test run")
    final = Final.model_validate_json(json.dumps({
        "status": "prepared_tested_not_installed",
        "prepared_at": datetime.now(timezone.utc).isoformat(),
        "actual_repository_received_at": receipt["actual_repository_received_at"],
        "intake_completed_at": receipt["completed_at"], "original_sources": 63,
        "review_mappings": 24, "unmapped": 39, "old_source_rows_preserved": 61,
        "old_review_joins_preserved": 22, "test_cases_passed": 79,
        "branch_inclusive_coverage_percent": coverage,
        "canonical_receipt": receipt_asset.model_dump(),
        "repository_bindings": [asset(ROOT, p).model_dump() for p in sorted(refs)],
        "source_record_ids": [r.record_id for r in binding.actual_intakes],
        "production_changes_by_preparation": False, "legal_currentness": "not_verified",
        "answer_safe": False, "limitations": [
            "This handoff is an installation proposal; root alone installs production files.",
            "Accepted source QA is source fidelity, not legal currentness or complete coverage.",
            "Earlier pending-intake and monitoring statements remain historical review evidence.",
            "The first test run started coverage after import; that incomplete measure is retained.",
            "The final run starts coverage before import; no lookup or ordinary query is added.",
            "Corpus-wide validation and root installation are outside this preparation result.",
        ]}))
    write_model(HERE / "FINAL.json", final)
    files = [asset(HERE, p.relative_to(HERE).as_posix()) for p in sorted(HERE.rglob("*"))
             if p.is_file() and p.name not in ("FINAL_MANIFEST.json", "FINAL_MANIFEST.schema.json")]
    write_model(HERE / "FINAL_MANIFEST.json", Manifest(
        status="frozen_prepared_not_installed",
        prepared_at=datetime.now(timezone.utc), files=files))
    sys.stdout.write(final.model_dump_json(indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
