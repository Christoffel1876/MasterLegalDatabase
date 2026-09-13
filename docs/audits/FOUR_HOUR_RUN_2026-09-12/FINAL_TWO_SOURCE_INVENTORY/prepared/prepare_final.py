"""Prepare the final inventory only after the actual guarded two-source intake exists."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import jsonschema

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2] / "MasterLegalDatabase"
TRANSACTION = Path("research/local_review/douglas-pueblo-intake-2026-09-13/prepared-transaction")
PREPARATION = TRANSACTION / "evidence/preparation"


def main() -> int:
    """Bind actual records and preserve all earlier joins; write only into this handoff."""
    sys.path.insert(0, str(ROOT))
    spec = importlib.util.spec_from_file_location(
        "prepared_final_inventory", HERE / "proposed/manual_review_inventory.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    from geode.pipeline.manual_source_intake import ManualSourceIntakeRecord

    def identity(relative: str) -> module.Artifact:
        """Hash an ordinary existing repository input without treating missing files as evidence."""
        path = ROOT / relative
        if path.is_symlink() or not path.is_file():
            raise ValueError("Missing or nonordinary actual input: " + relative)
        with path.open("rb") as handle:
            digest = hashlib.file_digest(handle, "sha256").hexdigest()
        return module.Artifact(path=relative, sha256=digest, size_bytes=path.stat().st_size)

    def put(path: Path, content: bytes) -> None:
        """Write once or require exact equality; never overwrite a previous draft."""
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            if path.read_bytes() != content:
                raise ValueError("Existing prepared output differs: " + str(path))
        else:
            with path.open("xb") as handle:
                handle.write(content)

    preliminary = json.loads((HERE / "PRELIMINARY.json").read_bytes())
    jsonschema.validate(preliminary, json.loads((HERE / "PRELIMINARY.schema.json").read_bytes()))
    old = module.JoinPlan.model_validate_json((HERE / "preimages/join-plan.json").read_bytes())
    expected = {item["canonical_id"]: item for item in preliminary["selections"]}
    original_rows = []
    for relative, old_name, prior_count, expected_count in [
        ("_RAW_ARCHIVE/manual_intake/manual_source_intake_manifest.jsonl",
         "manual_source_intake_manifest.jsonl", 61, 63),
        ("_CONTROL_PLANE/MANUAL_SOURCE_INTAKE_LEDGER.jsonl",
         "MANUAL_SOURCE_INTAKE_LEDGER.jsonl", 62, 64),
    ]:
        before = (HERE / "preimages" / old_name).read_bytes()
        path = ROOT / relative
        with path.open("rb") as handle:
            if handle.read(len(before)) != before:
                raise ValueError("Prior stream prefix changed: " + relative)
        with path.open("rb") as handle:
            records = [ManualSourceIntakeRecord.model_validate_json(line) for line in handle]
        if (len(records) != expected_count or
                {r.record_id for r in records[prior_count:]} != set(expected)):
            raise ValueError("Actual intake count or selected IDs differ")
        for row in records[prior_count:]:
            selected = expected[row.record_id]
            if row.sha256 != selected["source_sha256"] or row.layer_id != selected["layer_id"]:
                raise ValueError("Actual intake source/owner differs")
            if row.status != "archived_pending_pipeline":
                raise ValueError("Unexpected promoted intake status")
        if relative.startswith("_RAW_ARCHIVE"):
            original_rows = records[prior_count:]
    prep = json.loads((ROOT / PREPARATION / "PREPARATION.json").read_bytes())
    schema = json.loads((ROOT / PREPARATION / "PREPARATION.schema.json").read_bytes())
    jsonschema.validate(prep, schema)
    provenance_path = (PREPARATION / "source-provenance.jsonl").as_posix()
    provenance = identity(provenance_path)
    with (ROOT / provenance_path).open("rb") as handle:
        sources = [json.loads(line) for line in handle]
    if sources != prep["sources"] or {s["proposed_record_id"] for s in sources} != set(expected):
        raise ValueError("Prepared provenance does not exactly match approved sources")
    authorities = []
    for index, source in enumerate(sources):
        selected = expected[source["proposed_record_id"]]
        if (source["authority_id"] != selected["authority_id"] or
                source["original"]["sha256"] != selected["source_sha256"] or
                source["legal_currentness"] != "not_verified"):
            raise ValueError("Source provenance identity or scope differs")
        event = "E017" if source["authority_id"] == "CO-COUNTY-DOUGLAS" else "E005"
        event_path = (PREPARATION / "custody" / source["proposed_record_id"] /
                      event / "event.json").as_posix()
        http = identity(event_path)
        authorities.append(module.AuthorityJoin(
            record_id=source["proposed_record_id"], authority_id=source["authority_id"],
            provenance=module.Document(artifact=provenance, jsonl_row=index),
            sha_pointer="/original/sha256", source_id_pointer="/proposed_record_id",
            authority_pointer="/authority_id",
            reported_acquisition_pointers=["/request_started_at", "/response_completed_at"],
            role_pointers=["/issuer", "/physical_pages", "/source_date_claims", "/review_scope"],
            qualification_pointers=["/qualifications", "/legal_currentness",
                                    "/actual_repository_received_at"],
            verified_http=module.HttpBinding(document=module.Document(artifact=http),
                sha_pointer="/body/sha256", status_pointer="/http_status",
                time_pointer="/completed_at")))
    reviews = [module.ReviewJoin.model_validate_json(json.dumps(x))
               for x in preliminary["review_joins"]]
    current_manifest = identity(old.manual_manifest.path)
    plan = module.JoinPlan.model_validate_json(old.model_copy(update={
        "prepared_at": datetime.now(timezone.utc), "manual_manifest": current_manifest,
        "authorities": [*old.authorities, *authorities], "reviews": [*old.reviews, *reviews],
    }).model_dump_json())
    put(HERE / "proposed/join-plan.json", (plan.model_dump_json(indent=2) + "\n").encode())
    prior_safe = module.safe_path
    module.safe_path = lambda root, relative: (
        HERE / "proposed/join-plan.json" if root == ROOT and relative == module.PLAN.as_posix()
        else prior_safe(root, relative))
    inventory = module.build_inventory(ROOT)
    previous = module.Inventory.model_validate_json(
        (HERE / "preimages/inventory.json").read_bytes())
    if (len(inventory.sources) != 63 or inventory.rows_with_review != 24 or
            inventory.rows_without_review != 39 or inventory.sources[:61] != previous.sources):
        raise ValueError("Prepared inventory changed earlier source metadata or counts")
    for name, body in module._render_outputs(inventory).items():
        put(HERE / "proposed/inventory" / name, body.encode())
    sys.stdout.write(json.dumps({"status": "prepared_not_installed", "sources": 63,
        "reviewed": 24, "unknown": 39,
        "actual_intakes": [r.model_dump(mode="json") for r in original_rows]}, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
