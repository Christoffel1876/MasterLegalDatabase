"""Verify the closed inventory proposal without importing or executing review packages."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import jsonschema

HERE = Path(__file__).resolve().parent


def document(path: Path) -> Any:
    """Read one ordinary JSON document, rejecting symlink traversal."""
    for ancestor in (path, *path.parents):
        if ancestor.is_symlink():
            raise ValueError("Symlink is not a verified payload: " + str(path))
    if not path.is_file():
        raise ValueError("Missing ordinary file: " + str(path))
    return json.loads(path.read_bytes())


def identity(path: Path, expected: dict[str, Any]) -> None:
    """Compare an ordinary payload to its recorded exact byte identity."""
    for ancestor in (path, *path.parents):
        if ancestor.is_symlink():
            raise ValueError("Symlink is not a verified payload: " + str(path))
    if not path.is_file() or path.stat().st_size != expected["size_bytes"]:
        raise ValueError("Missing or wrong-size payload: " + str(path))
    with path.open("rb") as handle:
        digest = hashlib.file_digest(handle, "sha256").hexdigest()
    if digest != expected["sha256"]:
        raise ValueError("Payload hash differs: " + str(path))


def confined(base: Path, relative: str) -> Path:
    """Resolve a nonempty relative inventory path with no traversal components."""
    path = Path(relative)
    if not relative or path.is_absolute() or any(p in ("..", ".") for p in path.parts):
        raise ValueError("Invalid relative inventory path")
    return base / path


def verify(root: Path | None = None) -> dict[str, Any]:
    """Check closed bytes, typed documents, prior joins and optional live reference hashes."""
    manifest = document(HERE / "FINAL_MANIFEST.json")
    jsonschema.validate(manifest, document(HERE / "FINAL_MANIFEST.schema.json"))
    files = manifest["files"]
    listed = {item["path"] for item in files}
    if len(listed) != len(files):
        raise ValueError("Duplicate manifest path")
    actual = {p.relative_to(HERE).as_posix() for p in HERE.rglob("*") if p.is_file()}
    if actual != listed | {"FINAL_MANIFEST.json", "FINAL_MANIFEST.schema.json"}:
        raise ValueError("Closed proposal inventory differs")
    for asset in files:
        identity(confined(HERE, asset["path"]), asset)
    for name in ("PRELIMINARY", "FINAL"):
        jsonschema.validate(document(HERE / f"{name}.json"),
                            document(HERE / f"{name}.schema.json"))
    inventory = document(HERE / "proposed/inventory/inventory.json")
    jsonschema.validate(inventory, document(HERE / "proposed/inventory/inventory.schema.json"))
    plan = document(HERE / "proposed/join-plan.json")
    jsonschema.validate(plan, document(HERE / "proposed/join-plan.schema.json"))
    old_inventory = document(HERE / "preimages/inventory.json")
    old_plan = document(HERE / "preimages/join-plan.json")
    if (len(inventory["sources"]), inventory["rows_with_review"],
            inventory["rows_without_review"]) != (63, 24, 39):
        raise ValueError("Incorrect proposed source/review counts")
    if inventory["sources"][:61] != old_inventory["sources"]:
        raise ValueError("An earlier source row changed")
    if (plan["authorities"][:61] != old_plan["authorities"] or
            plan["reviews"][:22] != old_plan["reviews"] or
            len(plan["authorities"]) != 63 or len(plan["reviews"]) != 24):
        raise ValueError("An earlier join changed or an unexpected join was added")
    expected = {item["canonical_id"]: item for item in document(HERE / "PRELIMINARY.json")[
        "selections"]}
    for row in inventory["sources"][61:]:
        selected = expected.pop(row["record_id"])
        if (row["authority_id"] != selected["authority_id"] or
                row["layer_id"] != selected["layer_id"] or
                row["source"]["sha256"] != selected["source_sha256"] or
                row["legal_currentness"] != "not_verified" or row["answer_safe"]):
            raise ValueError("New source identity, authority or research scope differs")
    if expected:
        raise ValueError("An expected source is missing")
    snapshot = HERE / "proposed/inventory/_SNAPSHOTS/BEFORE_FINAL_TWO_2026-09-13"
    for name in ("join-plan.json", "inventory.json", "inventory.schema.json", "README.md"):
        if (snapshot / name).read_bytes() != (HERE / "preimages" / name).read_bytes():
            raise ValueError("Installation snapshot differs from its exact preimage")
    checked = 0
    if root is not None:
        for asset in document(HERE / "FINAL.json")["repository_bindings"]:
            identity(confined(root, asset["path"]), asset)
            checked += 1
    return {"status": "verified_prepared_not_installed", "payloads": len(files),
            "sources": 63, "reviews": 24, "unmapped": 39,
            "live_repository_references_checked": checked,
            "legal_currentness": "not_verified"}


def main() -> int:
    """Return stable JSON verification results without modifying evidence."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path)
    arguments = parser.parse_args()
    sys.stdout.write(json.dumps(verify(arguments.root), indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
