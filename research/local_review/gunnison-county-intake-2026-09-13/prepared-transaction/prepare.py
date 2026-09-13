"""New handoff-only builder. Never executes a historical transaction or edits canonical data."""
from __future__ import annotations
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from models import Asset, Baseline, Preparation

HERE = Path(__file__).absolute().parent
BASE = HERE.parents[2]
REPO = BASE / "MasterLegalDatabase"
AUDIT = HERE.parent / "popper-sh003"
AUDIT_PIN = "254f53e93784937b2d3fa632fce84d64a6beb77218f6052bdb82d9f7115c897d"
REFERENCE = BASE / (
    "handoffs/run-2026-09-12/extended-run/pueblo-county-fees-intake-revision"
)


def sha(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError("Refuse overwrite " + str(path))
        return
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("xb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def copied(source, destination):
    data = source.read_bytes()
    write(HERE / destination, data)
    return Asset(path=destination, sha256=hashlib.sha256(data).hexdigest(), size_bytes=len(data))


def main():
    if (HERE / "PREPARATION.json").exists():
        raise ValueError("Frozen preparation exists; do not rerun")
    if sha(AUDIT / "FINAL_MANIFEST.json") != AUDIT_PIN:
        raise ValueError("Recommendation manifest changed")
    pins = {a["path"]: a for a in json.loads((AUDIT / "FINAL_MANIFEST.json").read_bytes())["files"]}
    recommendation = json.loads((AUDIT / "RECOMMENDATION.json").read_bytes())
    subset = []
    def take(name):
        path = AUDIT / name
        expected = AUDIT_PIN if name == "FINAL_MANIFEST.json" else pins[name]["sha256"]
        if sha(path) != expected:
            raise ValueError("Audited input changed")
        result = copied(path, "inputs/audit/" + name)
        if result.path not in {a.path for a in subset}:
            subset.append(result)
        return result
    rec_ref = take("RECOMMENDATION.json")
    rec_manifest = take("FINAL_MANIFEST.json")
    for name in ["RECOMMENDATION.schema.json", "README.md", "RAW_ARCHIVE_SCAN.json",
                 "RAW_ARCHIVE_SCAN.schema.json", "evidence/prior/AUDIT.json",
                 "evidence/prior/AUDIT.schema.json", "evidence/prior/CUSTODY_RECEIPT.json",
                 "evidence/prior/FINAL_MANIFEST.json"]:
        take(name)
    templates, provenance = [], []
    for source in recommendation["sources"]:
        selected = take(source["source"]["path"])
        roles = source["prior_role_observations"]
        note = (
            "Received unchanged from Sherlock SH-EXT-003 package, not an independently "
            "witnessed official download. Supplied parent URL, HTTP200, and action26-28 times "
            "remain reported claims; the original equivalent tool commands are absent. "
            "Preserved audit shows only historical first-page role observations; no full "
            "source review, execution authentication, adoption/effect date, legal currentness "
            "or structured-rule promotion. This received_at is repository intake time only."
        )
        templates.append({
            "record_id": source["proposed_source_id"], "authority_id": source["authority_id"],
            "layer_id": source["layer_id"], "official_source_name": source["visible_label"],
            "official_source_url": None, "acquisition_method": "received_review_package",
            "source": selected, "original_filename": Path(selected.path).name,
            "custody_note": note, "actual_repository_received_at": None,
            "intake_id": None, "archive_path": None,
        })
        provenance.append({
            "source_id": source["proposed_source_id"], "action_id": source["action_id"],
            "authority_id": source["authority_id"], "source": selected,
            "physical_pages": source["physical_pages"], "parent": take(source["parent"]["path"]),
            "parent_url": source["parent_url"], "original_href": source["original_href"],
            "visible_label": source["visible_label"],
            "reservation": take(source["reservation"]["path"]),
            "result": take(source["result"]["path"]),
            "public_headers": take(source["public_headers"]["path"]),
            "requested_url_reported": source["reported_requested_url"],
            "final_url_reported": source["reported_final_url"], "http_status_reported": 200,
            "reported_reserved_at": source["reported_start"],
            "reported_finished_at": source["reported_finish"],
            "verified_original_acquired_at": None, "original_tool_command_retained": False,
            "prior_visually_reviewed_pages": [1], "new_visually_reviewed_pages": [],
            "prior_role_observations": roles,
            "historical_digest_lines": [m["line"] for m in source["legacy_matches"]],
            "legal_currentness": "not_verified", "limitations": source["limitations"],
        })
    previous = json.loads((REFERENCE / "PREPARATION.json").read_bytes())
    baseline = []
    for item in previous["baseline"]:
        name = item["repository_path"]
        p = REPO / name
        count = None
        if p.suffix == ".jsonl":
            count = 0
            with p.open("rb") as handle:
                for line in handle:
                    json.loads(line)
                    count += 1
        baseline.append(Baseline(repository_path=name,
                                 preserved=copied(p, "preimages/" + p.name), records=count))
    # Registry identity is guarded, but never edited by this transaction.
    registry = "_CONTROL_PLANE/LOCAL_SOURCE_REGISTRY.json"
    baseline.append(Baseline(repository_path=registry,
                             preserved=copied(
                                 REPO / registry, "preimages/LOCAL_SOURCE_REGISTRY.json"),
                             records=None))
    runtime = {}
    for name in previous["runtime_pins"]:
        runtime[name] = sha(REPO / name)
    for name in ["transaction.py", "models.py", "PREPARATION.json"]:
        copied(REFERENCE / name, "reference-only/" + name)
    legacy_path = "_CONTROL_PLANE/LOCAL_DOWNLOAD_MANIFEST.jsonl"
    legacy = Asset(path=legacy_path, sha256=sha(REPO / legacy_path),
                   size_bytes=(REPO / legacy_path).stat().st_size)
    data = {
        "schema_version": 1, "prepared_at": datetime.now(timezone.utc).isoformat(),
        "status": "PREPARED_NOT_APPLIED",
        "comparison_commit": recommendation["snapshot"]["repository_head"],
        "templates": templates, "provenance": provenance, "baseline": baseline,
        "runtime_pins": runtime, "custody_subset": subset,
        "recommendation": rec_ref, "recommendation_manifest": rec_manifest,
        "legacy_guard": legacy, "raw_before": 64, "ledger_before": 65,
        "raw_after": 67, "ledger_after": 68, "public_requests": 0,
        "canonical_mutations": 0, "legal_currentness": "not_verified", "answer_safe": False,
    }
    # JSON roundtrip preserves strict aware timestamps while accepting nested model records.
    def encode(value):
        return value.model_dump(mode="json")
    plan = Preparation.model_validate_json(json.dumps(data, default=encode))
    raw = plan.model_dump_json(indent=2).encode() + b"\n"
    Preparation.model_validate_json(raw)
    write(HERE / "PREPARATION.json", raw)
    write(HERE / "PREPARATION.schema.json",
          (json.dumps(Preparation.model_json_schema(), indent=2) + "\n").encode())
    print(hashlib.sha256(raw).hexdigest())


if __name__ == "__main__":
    main()
