"""Read-only verification of the frozen expectation set; does not execute a lookup."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath

from jsonschema import Draft202012Validator

from expectation_models import Expectations, Inventory

HERE = Path(__file__).resolve().parent
EXPECTED_SHA = "48ad71c545306aacf1be757862da8eb4cbc9d6c11e8f813dc01b9dc00d50e155"


def read(path: Path) -> bytes:
    """Reject symlinks and read an ordinary evidence file."""
    if not path.is_file() or any(p.is_symlink() for p in [path, *path.parents]):
        raise ValueError("Nonordinary evidence")
    return path.read_bytes()


def validate() -> dict:
    """Check closed hashes and every expected row and context against frozen source QA."""
    manifest = Inventory.model_validate_json(read(HERE / "EXPECTATIONS_MANIFEST.json"))
    actual = set()
    for path in HERE.rglob("*"):
        if path.is_symlink() or not (path.is_file() or path.is_dir()):
            raise ValueError("Nonordinary closed package")
        if path.is_file() and path.name != "EXPECTATIONS_MANIFEST.json":
            actual.add(path.relative_to(HERE).as_posix())
    if actual != {item.path for item in manifest.files}:
        raise ValueError("Closed expectation inventory differs")
    for item in manifest.files:
        relative = PurePosixPath(item.path)
        if relative.is_absolute() or ".." in relative.parts or str(relative) != item.path:
            raise ValueError("Unsafe expectation member")
        raw = read(HERE / item.path)
        if len(raw) != item.size_bytes or hashlib.sha256(raw).hexdigest() != item.sha256:
            raise ValueError("Expectation evidence changed: " + item.path)
    raw = read(HERE / "EXPECTATIONS.json")
    if hashlib.sha256(raw).hexdigest() != EXPECTED_SHA:
        raise ValueError("Frozen pre-adapter expectations changed")
    values = Expectations.model_validate_json(raw)
    Draft202012Validator(json.loads(read(HERE / "EXPECTATIONS.schema.json"))).validate(
        json.loads(raw)
    )
    qa = json.loads(read(HERE / "frozen-inputs/SOURCE_QA.json"))
    Draft202012Validator(json.loads(read(HERE / "frozen-inputs/SOURCE_QA.schema.json"))).validate(qa)
    rows = {row["row_id"]: row for row in qa["rows"]}
    contexts = {value["context_id"]: value for value in qa["contexts"]}
    if len(values.cases) != 25 or [c.id for c in values.cases] != [f"EHS-{n:02d}" for n in range(1, 26)]:
        raise ValueError("Finite case scope changed")
    for case in values.cases:
        for row in case.expected_rows:
            if row.model_dump() != rows[row.row_id]:
                raise ValueError("Expected row differs from accepted source QA")
        for context in case.required_context:
            if context.model_dump() != contexts[context.context_id]:
                raise ValueError("Expected context differs from accepted source QA")
        available = {context.context_id for context in case.required_context}
        for row in case.expected_rows:
            if not set(row.linked_context) <= available:
                raise ValueError("Expected row loses its complete linked conditions")
    if len(values.cases[20].expected_rows) != 65 or len(values.cases[20].required_context) != 37:
        raise ValueError("Full-list scope changed")
    if qa["source"]["sha256"] != values.source_sha256:
        raise ValueError("Source identity differs")
    return {"status": "source_expectations_verified", "cases": 25,
            "new_adapter_read_or_executed_when_frozen": False,
            "source_qa_retranscribed": False, "public_requests": 0}


if __name__ == "__main__":
    print(json.dumps(validate(), indent=2))
