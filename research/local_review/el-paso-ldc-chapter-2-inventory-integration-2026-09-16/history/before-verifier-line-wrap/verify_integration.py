"""Read-only closed receipt and exact repository metadata delta verification."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys

import jsonschema

from integration_models import Asset, Execution, Manifest

HERE = Path(__file__).resolve().parent
PACKAGE = Path("research/local_review/manual-source-review-inventory-2026-09-11")


def checked(root: Path, ref: Asset) -> bytes:
    """Read a safe ordinary file and compare its recorded exact identity."""
    relative = Path(ref.path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("Unsafe evidence path")
    path = root / relative
    if any(p.is_symlink() for p in (path, *path.parents)) or not path.is_file():
        raise ValueError("Nonordinary evidence file: " + ref.path)
    raw = path.read_bytes()
    if (sha256(raw).hexdigest(), len(raw)) != (ref.sha256, ref.size_bytes):
        raise ValueError("Evidence identity differs: " + ref.path)
    return raw


def main() -> None:
    """Check closure, accepted pins, prior joins and all unchanged custody fields."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=HERE.parents[2])
    root = parser.parse_args().root.resolve()
    manifest = Manifest.model_validate_json((HERE / "FINAL_MANIFEST.json").read_bytes())
    jsonschema.validate(manifest.model_dump(mode="json"),
                        json.loads((HERE / "FINAL_MANIFEST.schema.json").read_bytes()))
    expected = {a.path for a in manifest.files}
    if len(expected) != len(manifest.files):
        raise ValueError("Duplicate closure member")
    actual = {p.relative_to(root).as_posix() for p in HERE.rglob("*") if p.is_file()}
    if actual != expected | {(HERE / "FINAL_MANIFEST.json").relative_to(root).as_posix()}:
        raise ValueError("Integration package membership differs")
    for asset in manifest.files:
        checked(root, asset)
    receipt = Execution.model_validate_json((HERE / "EXECUTION.json").read_bytes())
    jsonschema.validate(receipt.model_dump(mode="json"),
                        json.loads((HERE / "EXECUTION.schema.json").read_bytes()))
    for asset in (receipt.preimages + receipt.installed_files + receipt.unchanged_inputs
                  + receipt.accepted_review_inputs):
        checked(root, asset)
    old_dir = root / receipt.snapshot_directory
    old_plan = json.loads((old_dir / "join-plan.json").read_bytes())
    plan = json.loads((root / PACKAGE / "join-plan.json").read_bytes())
    old = json.loads((old_dir / "inventory.json").read_bytes())
    new = json.loads((root / PACKAGE / "inventory.json").read_bytes())
    assert plan["authorities"] == old_plan["authorities"]
    assert len(plan["authorities"]) == 70
    assert plan["reviews"][:37] == old_plan["reviews"] and len(plan["reviews"]) == 38
    assert plan["reviews"][37]["record_id"] == receipt.source_id
    assert (len(new["sources"]), new["rows_with_review"], new["rows_without_review"]) == (70, 38, 32)
    for prior, current in zip(old["sources"], new["sources"], strict=True):
        normalized = dict(current)
        if current["record_id"] == receipt.source_id:
            normalized.update(reviews=None, review_status="metadata_only_review_unknown")
        assert normalized == prior, current["record_id"]
    for name in ("inventory.schema.json", "join-plan.schema.json"):
        assert (old_dir / name).read_bytes() == (root / PACKAGE / name).read_bytes()
    assert new["manual_manifest"] == old["manual_manifest"]
    assert new["unchanged_legacy_ledger"] == old["unchanged_legacy_ledger"]
    assert new["legal_currentness"] == "not_verified"
    assert not new["answer_safe"] and not new["coverage_promotion"]
    sys.stdout.write("PASS: closed integration, 70/38/32; 70 authority joins, 37 prior reviews, "
                     "69 other rows and exact custody/source inputs preserved.\n")


if __name__ == "__main__":
    main()
