"""Verify the closed local diagnosis and replay its comparison without network."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Literal

import jsonschema
from pydantic import BaseModel, ConfigDict, Field

HERE = Path(__file__).resolve().parent


class Asset(BaseModel):
    """One closed ordinary-file payload."""

    model_config = ConfigDict(extra="forbid")
    path: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    bytes: int = Field(ge=0)
    visibility: Literal["ordinary_evidence", "local_only_raw_cookie_headers"]


class Manifest(BaseModel):
    """Complete fixed input/output inventory, excluding this manifest alone."""

    model_config = ConfigDict(extra="forbid")
    status: Literal["diagnosis_complete_source_status_unresolved"]
    assets: list[Asset]


def check_inventory(manifest: Manifest) -> None:
    """Reject unexpected, changed, linked or missing files before code replay."""

    names = [asset.path for asset in manifest.assets]
    assert len(names) == len(set(names))
    entries = list(HERE.rglob("*"))
    assert not any(path.is_symlink() for path in entries)
    found = {path.relative_to(HERE).as_posix() for path in entries if path.is_file()}
    assert found == set(names) | {"FINAL_MANIFEST.json"}
    expected_dirs = set()
    for name in names:
        expected_dirs.update(
            parent.as_posix() for parent in Path(name).parents if parent != Path(".")
        )
    assert {path.relative_to(HERE).as_posix() for path in entries if path.is_dir()} == expected_dirs
    for asset in manifest.assets:
        relative = Path(asset.path)
        assert not relative.is_absolute() and ".." not in relative.parts
        path = HERE / relative
        data = path.read_bytes()
        assert len(data) == asset.bytes
        assert hashlib.sha256(data).hexdigest() == asset.sha256


def main() -> None:
    """Validate schemas, raw bindings and both preserved offline checkpoints."""

    manifest = Manifest.model_validate_json((HERE / "FINAL_MANIFEST.json").read_bytes())
    check_inventory(manifest)
    for name, schema in [
        ("BASELINE_RECEIPT", "BASELINE_RECEIPT"),
        ("SUPPLEMENTAL_BASELINE_RECEIPT", "BASELINE_RECEIPT"),
        ("MISSING_NOTICE_ORIGINALS_RECEIPT", "BASELINE_RECEIPT"),
        ("FETCH_RECEIPT", "FETCH_RECEIPT"),
        ("authorized-route/FETCH_RECEIPT", "authorized-route/FETCH_RECEIPT"),
        ("ARCHIVED_REPLAY", "ARCHIVED_REPLAY"),
        ("FRESH_COMPARISON", "FRESH_COMPARISON"),
        ("REMOVED_ROW_FRAGMENTS", "REMOVED_ROW_FRAGMENTS"),
        ("PUBLIC_HEADER_DERIVATIVE", "PUBLIC_HEADER_DERIVATIVE"),
        ("DECISION_RECEIPT", "DECISION_RECEIPT"),
        ("FINAL_MANIFEST", "FINAL_MANIFEST"),
    ]:
        payload = json.loads((HERE / f"{name}.json").read_bytes())
        schema_value = json.loads((HERE / f"{schema}.schema.json").read_bytes())
        jsonschema.validate(payload, schema_value)
    for name in ["BASELINE_RECEIPT", "SUPPLEMENTAL_BASELINE_RECEIPT",
                 "MISSING_NOTICE_ORIGINALS_RECEIPT"]:
        receipt = json.loads((HERE / f"{name}.json").read_bytes())
        for asset in receipt["assets"]:
            body = (HERE / asset["path"]).read_bytes()
            assert len(body) == asset["bytes"]
            assert hashlib.sha256(body).hexdigest() == asset["sha256"]
    fragments = json.loads((HERE / "REMOVED_ROW_FRAGMENTS.json").read_bytes())
    for row in fragments["fragments"]:
        source = (HERE / row["source_path"]).read_bytes()
        body = (HERE / row["path"]).read_bytes()
        assert hashlib.sha256(source).hexdigest() == row["source_sha256"]
        assert body == source[row["byte_start"]:row["byte_end"]]
        assert len(body) == row["bytes"]
        assert hashlib.sha256(body).hexdigest() == row["sha256"]
        assert source[:row["byte_start"]].count(b"\n") + 1 == row["first_line"]
        assert source[:row["byte_end"]].count(b"\n") + 1 == row["last_line"]
    derivative = json.loads((HERE / "PUBLIC_HEADER_DERIVATIVE.json").read_bytes())
    raw = (HERE / derivative["original_path"]).read_bytes()
    public = (HERE / derivative["public_path"]).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == derivative["original_sha256"]
    assert hashlib.sha256(public).hexdigest() == derivative["public_sha256"]
    kept = []
    dropping = False
    for line in raw.splitlines(keepends=True):
        if line.startswith((b" ", b"\t")):
            if not dropping:
                kept.append(line)
            continue
        key = line.split(b":", 1)[0].strip().lower()
        dropping = key in {b"set-cookie", b"cookie", b"authorization", b"proxy-authorization"}
        if not dropping:
            kept.append(line)
    assert public == b"".join(kept)
    for script, record in [
        ("replay_offline.py", "ARCHIVED_REPLAY.json"),
        ("compare_fresh.py", "FRESH_COMPARISON.json"),
    ]:
        result = subprocess.run(
            [sys.executable, "-I", "-B", str(HERE / script)],
            cwd=HERE, capture_output=True, timeout=30,
        )
        assert result.returncode == 0, result.stderr.decode()
        assert json.loads(result.stdout) == json.loads((HERE / record).read_bytes())
    comparison = json.loads((HERE / "FRESH_COMPARISON.json").read_bytes())
    assert comparison["old_notice_count"] == 50 and comparison["fresh_notice_count"] == 48
    assert comparison["removal_gate_missing_ids"] == [
        "RM-2026-daily-6ae185cdffa4fdedd5bb", "RM-2026-daily-fe6fe04b708089735009",
    ]
    check_inventory(manifest)
    sys.stdout.write(json.dumps({
        "status": "verified_offline", "payload_files": len(manifest.assets),
        "archived_notices": 50, "fresh_notices": 48, "missing_ids": 2,
        "common_rows_identical_except_row_number": 48, "fragment_slices": 4,
        "legal_status": "not_verified", "collector_executed": False,
    }) + "\n")


if __name__ == "__main__":
    main()
