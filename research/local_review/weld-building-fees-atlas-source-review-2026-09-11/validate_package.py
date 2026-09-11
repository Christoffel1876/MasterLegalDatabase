#!/usr/bin/env python3
"""Verify copied custody bytes, then invoke the unchanged source-review validator."""

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import jsonschema

from package_models import Asset, Inventory, PackageStatus


def require(condition: bool, message: str) -> None:
    """Fail closed on an invalid package binding."""
    if not condition:
        raise ValueError(message)


def ordinary(root: Path, relative: str) -> Path:
    """Resolve only ordinary files inside the selected package root."""
    Asset(path=relative, sha256="0" * 64, size_bytes=0)
    path = root.absolute() / relative
    require(not any(p.is_symlink() for p in [path, *path.parents]), "symlink forbidden")
    require(path.is_file(), f"missing ordinary file: {relative}")
    return path


def read_asset(root: Path, asset: Asset) -> bytes:
    """Verify exact size and SHA-256 before returning retained bytes."""
    data = ordinary(root, asset.path).read_bytes()
    require(len(data) == asset.size_bytes, f"size mismatch: {asset.path}")
    require(hashlib.sha256(data).hexdigest() == asset.sha256, f"hash mismatch: {asset.path}")
    return data


def validate(root: Path) -> dict[str, Any]:
    """Check the wrapper inventory and delegate all source semantics unchanged."""
    inventory = Inventory.model_validate_json(ordinary(root, "evidence-manifest.json").read_bytes())
    status_bytes = ordinary(root, "package-status.json").read_bytes()
    status = PackageStatus.model_validate_json(status_bytes)
    for name, value in [("package-status", json.loads(status_bytes)),
                        ("evidence-manifest", inventory.model_dump(mode="json"))]:
        schema = json.loads(ordinary(root, f"{name}.schema.json").read_bytes())
        jsonschema.Draft202012Validator(schema).validate(value)
    actual = set()
    for path in root.rglob("*"):
        require(not path.is_symlink(), f"symlink forbidden: {path}")
        if path.is_file():
            actual.add(path.relative_to(root).as_posix())
    expected = {asset.path for asset in inventory.files} | {"evidence-manifest.json"}
    require(actual == expected, "missing or extra package files")
    for asset in inventory.files:
        read_asset(root, asset)
    frozen = [asset for asset in inventory.files if asset.path.startswith("frozen/")]
    require(len(frozen) == status.frozen_file_count, "frozen file count mismatch")
    require(sum(a.size_bytes for a in frozen) == status.frozen_total_bytes, "frozen size mismatch")
    require(status.frozen_inventory.path == "frozen/evidence-manifest.json", "inventory path")
    require(status.frozen_review.path == "frozen/SOURCE_REVIEW.json", "source review path")
    require(status.frozen_inventory.sha256 ==
            "797f6fc00384409d2c171380ed0a76fc863d49c0df5d2dcc3db5e869c5f76d78",
            "frozen handoff inventory identity mismatch")
    read_asset(root, status.frozen_inventory)
    read_asset(root, status.frozen_review)
    result = subprocess.run(
        [sys.executable, str(ordinary(root, "frozen/validate_review.py")),
         "--root", str(root / "frozen")],
        cwd=root, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        capture_output=True, text=True, check=True,
    )
    return {
        "validation_passed": True,
        "package_id": status.package_id,
        "frozen_files_preserved": len(frozen),
        "frozen_bytes_preserved": status.frozen_total_bytes,
        "source_review_validator": json.loads(result.stdout),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).absolute().parent)
    arguments = parser.parse_args()
    sys.stdout.write(json.dumps(validate(arguments.root.absolute()), indent=2) + "\n")
