"""Verify closed portable repair evidence without executing tests or altering any file."""
from __future__ import annotations

import ast
import hashlib
import json
import sys
from pathlib import Path

import jsonschema

from package_models import Manifest, Verification

HERE = Path(__file__).resolve().parent


def checked(relative: str, sha256: str, size: int) -> bytes:
    """Read one confined payload and verify its consumed bytes."""
    relative_path = Path(relative)
    path = HERE / relative_path
    if relative_path.is_absolute() or ".." in relative_path.parts or any(
            item.is_symlink() for item in (path, *path.parents)) or not path.is_file():
        raise ValueError("Unsafe package path")
    raw = path.read_bytes()
    if len(raw) != size or hashlib.sha256(raw).hexdigest() != sha256:
        raise ValueError("Payload identity differs: " + relative)
    return raw


def nodes(raw: bytes) -> dict[str, ast.AST]:
    """Index top-level declarations for implementation-independent preservation checks."""
    return {node.name: node for node in ast.parse(raw).body if isinstance(
        node, (ast.FunctionDef, ast.ClassDef))}


def verify() -> dict[str, object]:
    """Replay custody, historical receipts and unchanged API declarations offline."""
    manifest_raw = (HERE / "FINAL_MANIFEST.json").read_bytes()
    manifest = Manifest.model_validate_json(manifest_raw)
    jsonschema.validate(json.loads(manifest_raw), json.loads(
        (HERE / "FINAL_MANIFEST.schema.json").read_bytes()))
    names = {asset.path for asset in manifest.files}
    actual = {p.relative_to(HERE).as_posix() for p in HERE.rglob("*") if p.is_file()}
    if len(names) != len(manifest.files) or actual != names | {
            "FINAL_MANIFEST.json", "FINAL_MANIFEST.schema.json"}:
        raise ValueError("Closed package membership differs")
    buffers = {asset.path: checked(asset.path, asset.sha256, asset.size_bytes)
               for asset in manifest.files}
    receipt = Verification.model_validate_json(buffers["VERIFICATION.json"])
    jsonschema.validate(json.loads(buffers["VERIFICATION.json"]), json.loads(
        buffers["VERIFICATION.schema.json"]))
    for asset in [receipt.preimage, receipt.proposed, receipt.tests, receipt.documentation,
                  receipt.historical_audit_manifest, receipt.coverage,
                  *(run.log for run in receipt.measured_runs)]:
        checked(asset.path, asset.sha256, asset.size_bytes)
    old, new = nodes(buffers[receipt.preimage.path]), nodes(buffers[receipt.proposed.path])
    classes = [name for name, node in old.items() if isinstance(node, ast.ClassDef)]
    preserved = [*classes, *receipt.douglas_pueblo_functions_unchanged, "main"]
    if len(classes) != receipt.original_classes_unchanged or any(
            ast.dump(old[name]) != ast.dump(new[name]) for name in preserved):
        raise ValueError("Existing schemas or preserved dispatch functions differ")
    baseline = json.loads(buffers["BASELINES.json"])
    jsonschema.validate(baseline, json.loads(buffers["BASELINES.schema.json"]))
    if len(baseline["assets"]) != 18 or not baseline["schema_equal"]:
        raise ValueError("Historical fixture comparison differs")
    for asset in baseline["assets"]:
        checked(asset["path"], asset["sha256"], asset["size_bytes"])
        if not asset["proposed_equal"]:
            raise ValueError("Historical baseline comparison failed")
    historical = json.loads(buffers["prior-audit/FINAL_MANIFEST.json"])
    for asset in historical["files"]:
        checked("prior-audit/" + asset["path"], asset["sha256"], asset["size_bytes"])
    for run in receipt.measured_runs:
        text = buffers[run.log.path].decode()
        if str(run.passed) + " passed" not in text or (
                run.failed and str(run.failed) + " failed" not in text):
            raise ValueError("Recorded test counts do not match retained output")
    return {"status": "verified_prepared_handoff", "files": len(manifest.files),
            "normal_output_fixtures": 18, "unchanged_classes": len(classes),
            "proposed_sha256": receipt.proposed.sha256,
            "public_requests": 0, "production_writes": 0,
            "legal_currentness": "not_verified"}


if __name__ == "__main__":
    sys.stdout.write(json.dumps(verify(), indent=2) + "\n")
