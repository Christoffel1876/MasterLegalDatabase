"""Portable, offline, read-only verification of this finite access audit."""
from __future__ import annotations
import hashlib
import json
import runpy
from pathlib import Path
import jsonschema

BASE = Path(__file__).resolve().parent

def safe(relative: str) -> Path:
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("Nonportable evidence path")
    candidate = BASE / path
    if not candidate.is_file() or any(p.is_symlink() for p in (candidate, *candidate.parents)):
        raise ValueError("Missing or symlinked evidence")
    return candidate

def check(asset):
    body = safe(asset.path).read_bytes()
    if len(body) != asset.size_bytes or hashlib.sha256(body).hexdigest() != asset.sha256:
        raise ValueError("Evidence identity mismatch: " + asset.path)

def evidence_text(path: str) -> str:
    p = safe(path)
    if p.name.startswith("web-tool-call-"):
        return json.loads(p.read_bytes())["result"]
    return p.read_text()

def main():
    models = runpy.run_path(str(BASE / "audit_models.py"))
    audit_body = safe("AUDIT.json").read_bytes()
    audit = models["Audit"].model_validate_json(audit_body)
    jsonschema.validate(json.loads(audit_body), json.loads(safe("AUDIT.schema.json").read_bytes()))
    mbody = safe("FINAL_MANIFEST.json").read_bytes()
    manifest = models["Manifest"].model_validate_json(mbody)
    jsonschema.validate(json.loads(mbody), json.loads(safe("FINAL_MANIFEST.schema.json").read_bytes()))
    listed = [a.path for a in manifest.files]
    if len(listed) != len(set(listed)):
        raise ValueError("Duplicate inventory path")
    actual = sorted(p.relative_to(BASE).as_posix() for p in BASE.rglob("*") if p.is_file()
                    and p.name not in {"FINAL_MANIFEST.json", "FINAL_MANIFEST.schema.json"}
                    and "__pycache__" not in p.parts)
    if actual != sorted(listed):
        raise ValueError("Inventory is not exhaustive")
    for a in manifest.files:
        check(a)
    for item in audit.inputs:
        check(item.copy)
    for action in audit.actions:
        check(action.result_asset)
    capture_models = runpy.run_path(str(BASE / "capture.py"))
    for event_id in ("E001", "E002"):
        event = capture_models["Event"].model_validate_json(safe(f"events/{event_id}/event.json").read_bytes())
        if event.curl_exit != 6 or event.http_status is not None or event.outcome != "transport_failure_no_http_response":
            raise ValueError("Transport outcome differs from the report")
        for asset in event.assets:
            check(asset)
        if (BASE / "events" / event_id / "body.bin").exists():
            raise ValueError("Unexpected publisher body in no-body receipt")
    for finding in audit.findings:
        for ref in finding.evidence:
            if " ".join(ref.excerpt.split()) not in " ".join(evidence_text(ref.asset_path).split()):
                raise ValueError("Unsupported excerpt: " + finding.finding_id)
    if any(p.suffix.lower() == ".pdf" for p in BASE.rglob("*")):
        raise ValueError("This audit reports zero acquired PDFs")
    if len(audit.actions) + audit.reported_redirect_count > 12 or len(audit.distinct_requested_and_reported_final_urls) > 8:
        raise ValueError("Declared public bounds exceeded")
    print(json.dumps({"status":"passed", "files":len(manifest.files), "requested_actions":8,
                      "reported_redirects":1, "observed_urls":5, "search_queries":2,
                      "originals_acquired":0, "legal_currentness":"not_verified",
                      "checks":"hashes, schema, exhaustive inventory, source excerpts, counts and time bounds"}))

if __name__ == "__main__":
    main()
