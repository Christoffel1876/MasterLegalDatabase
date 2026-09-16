"""Read-only audit closure and typed review validation; never execute a retained probe."""
from pathlib import Path
import hashlib
import json
import sys

from jsonschema import Draft202012Validator
from pydantic import TypeAdapter
from seal_review import Asset, Review


def main() -> None:
    root = Path(__file__).resolve().parent
    rows = TypeAdapter(list[Asset]).validate_json((root / "MANIFEST.json").read_bytes())
    names = {row.path for row in rows}
    if len(names) != len(rows):
        raise ValueError("Duplicate audit inventory member")
    actual = set()
    for path in root.rglob("*"):
        if path.is_symlink() or not (path.is_file() or path.is_dir()):
            raise ValueError("Nonordinary audit member")
        if path.is_file():
            actual.add(path.relative_to(root).as_posix())
    if actual != names | {"MANIFEST.json"}:
        raise ValueError("Closed audit membership differs")
    for row in rows:
        rel = Path(row.path)
        if rel.is_absolute() or ".." in rel.parts:
            raise ValueError("Audit path escapes")
        raw = (root / rel).read_bytes()
        if len(raw) != row.size_bytes or hashlib.sha256(raw).hexdigest() != row.sha256:
            raise ValueError("Audit member differs: " + row.path)
    raw = (root / "REVIEW.json").read_bytes()
    review = Review.model_validate_json(raw)
    Draft202012Validator(json.loads((root / "REVIEW.schema.json").read_bytes())).validate(
        json.loads(raw))
    code = (root / "checked-inputs/proposed/research_source_lookup.py").read_bytes()
    if hashlib.sha256(code).hexdigest() != review.final_script_sha256:
        raise ValueError("Reviewed script differs")
    sys.stdout.write(json.dumps({"status": "PASS", "payloads": len(rows),
                                 "script_sha256": review.final_script_sha256}) + "\n")


if __name__ == "__main__":
    main()
