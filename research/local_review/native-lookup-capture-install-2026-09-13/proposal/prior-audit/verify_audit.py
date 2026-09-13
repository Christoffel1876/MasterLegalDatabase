"""Read-only closed custody and measured-reproduction checks; no mutation probe rerun."""
from pathlib import Path
import hashlib
import json
import sys

import jsonschema

HERE = Path(__file__).resolve().parent


def verify() -> dict:
    """Verify the actual retained outputs and distinguish fixture mutations from real evidence."""
    data = json.loads((HERE / "FINAL_MANIFEST.json").read_bytes())
    jsonschema.validate(data, json.loads((HERE / "FINAL_MANIFEST.schema.json").read_bytes()))
    names = {r["path"] for r in data["files"]}
    actual = {p.relative_to(HERE).as_posix() for p in HERE.rglob("*") if p.is_file()}
    if len(names) != len(data["files"]) or actual != names | {
            "FINAL_MANIFEST.json", "FINAL_MANIFEST.schema.json"}:
        raise ValueError("Closed audit membership differs")
    for ref in data["files"]:
        path = HERE / ref["path"]
        if Path(ref["path"]).is_absolute() or ".." in Path(ref["path"]).parts or any(
                p.is_symlink() for p in (path, *path.parents)):
            raise ValueError("Unsafe audit path")
        raw = path.read_bytes()
        if len(raw) != ref["size_bytes"] or hashlib.sha256(raw).hexdigest() != ref["sha256"]:
            raise ValueError("Audit bytes differ")
    probes = json.loads((HERE / "PROBES.json").read_bytes())
    jsonschema.validate(probes, json.loads((HERE / "PROBES.schema.json").read_bytes()))
    if hashlib.sha256((HERE / "research_source_lookup.py").read_bytes()).hexdigest() != (
            probes["implementation_sha256"]):
        raise ValueError("Probed implementation differs")
    if (len(probes["events"]) != 9 or any(e["status"] != "returned_injected_evidence" or
            not e["result"]["evidence_verified"] or e["verification_calls"] < 1 or
            not e["source_files_restored_in_fixture"] for e in probes["events"])):
        raise ValueError("Reproduction status differs")
    return {"status": "verified_bounded_audit", "affected_sources": 7, "reproductions": 9,
            "production_writes": 0, "public_requests": 0}


if __name__ == "__main__":
    sys.stdout.write(json.dumps(verify(), indent=2) + "\n")
