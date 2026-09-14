"""Read-only validation of reporting schemas and optional delivered tool-action accounting."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import jsonschema

from models import ActionLog, ArtifactInventory, Backlog, Checklist, Priorities

MODELS = {"ACTION_LOG": ActionLog, "CHECKLIST": Checklist, "PRIORITIES": Priorities,
          "BACKLOG": Backlog, "ARTIFACT_INVENTORY": ArtifactInventory}


def main() -> int:
    """Validate only recorded actions and bytes; do not perform or claim network enforcement."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--delivery", type=Path)
    args = parser.parse_args()
    packet = Path(__file__).resolve().parent
    for name, model in MODELS.items():
        schema = json.loads((packet / "schemas" / (name + ".schema.json")).read_bytes())
        if schema != model.model_json_schema():
            raise ValueError("Exported schema differs: " + name)
        initial = packet / "templates" / (name + ".json")
        if initial.exists():
            value = json.loads(initial.read_bytes())
            jsonschema.validate(value, schema)
            model.model_validate_json(json.dumps(value))
    if args.delivery is None:
        sys.stdout.write('{"status":"templates_valid","public_actions_performed":0}\n')
        return 0
    root = args.delivery.resolve()
    data = {name: model.model_validate_json((root / (name + ".json")).read_bytes())
            for name, model in MODELS.items()}
    log = data["ACTION_LOG"]
    ids = {item.action_id for item in log.reservations}
    candidates = {item.candidate_id for item in data["PRIORITIES"].priorities}
    for row in data["CHECKLIST"].rows:
        if set(row.action_ids) - ids or set(row.candidate_ids) - candidates:
            raise ValueError("Checklist references missing actions or priorities")
    for row in data["PRIORITIES"].priorities:
        if set(row.action_ids) - ids:
            raise ValueError("Priority references an unreserved action")
    for ref in data["ARTIFACT_INVENTORY"].files:
        relative = Path(ref.path)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Unsafe retained path")
        path = root / relative
        if path.is_symlink() or not path.is_file():
            raise ValueError("Missing or symlinked artifact")
        with path.open("rb") as handle:
            digest = hashlib.file_digest(handle, "sha256").hexdigest()
        if digest != ref.sha256 or path.stat().st_size != ref.size_bytes:
            raise ValueError("Artifact hash/size differs")
    sys.stdout.write(json.dumps({"status": "recorded_delivery_valid",
        "reserved_actions": len(log.reservations), "recorded_results": len(log.results),
        "distinct_requested_urls": len({r.requested_url for r in log.reservations
                                        if r.requested_url}),
        "per_authority": {a: sum(r.authority_id == a for r in log.reservations)
                          for a in ["CO-COUNTY-PUEBLO", "CO-COUNTY-FREMONT"]},
        "hidden_network_requests_measured": False,
        "legal_currentness": "not_verified"}, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
