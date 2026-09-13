"""Read-only verification of the closed two-source lookup preparation."""
from __future__ import annotations

import ast
import hashlib
import json
import sys
from pathlib import Path

import jsonschema

HERE = Path(__file__).resolve().parent


def read(name: str) -> bytes:
    """Read an ordinary confined handoff file without executing its contents."""
    relative = Path(name)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("Unsafe handoff path")
    path = HERE / relative
    if not path.is_file() or any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError("Missing or symlinked handoff input")
    return path.read_bytes()


def verify() -> dict:
    """Check every payload, schemas, original declarations and complete example scopes."""
    manifest = json.loads(read("FINAL_MANIFEST.json"))
    jsonschema.validate(manifest, json.loads(read("FINAL_MANIFEST.schema.json")))
    assets = manifest["files"]
    names = {a["path"] for a in assets}
    actual = {p.relative_to(HERE).as_posix() for p in HERE.rglob("*") if p.is_file()}
    if len(names) != len(assets) or actual != names | {
            "FINAL_MANIFEST.json", "FINAL_MANIFEST.schema.json"}:
        raise ValueError("Closed handoff inventory differs")
    for item in assets:
        raw = read(item["path"])
        if len(raw) != item["size_bytes"] or hashlib.sha256(raw).hexdigest() != item["sha256"]:
            raise ValueError("Changed handoff input: " + item["path"])
    for name in ("BASELINES", "PRESERVATION", "VERIFICATION"):
        jsonschema.validate(json.loads(read(name + ".json")),
                            json.loads(read(name + ".schema.json")))
    baseline = ast.parse(read("preimages/research_source_lookup.py"))
    proposed = ast.parse(read("proposed/research_source_lookup.py"))
    declarations = {n.name: n for n in proposed.body if isinstance(n, (ast.ClassDef, ast.FunctionDef))}
    for node in baseline.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef)) and node.name not in {
                "lookup", "render_markdown"}:
            if ast.dump(node) != ast.dump(declarations[node.name]):
                raise ValueError("An earlier source implementation changed: " + node.name)
    examples = {}
    for source in ["douglas-ehs-fees-atlas-directed", "pueblo-planning-fees-atlas-directed"]:
        data = json.loads(read("examples/" + source + ".json"))
        jsonschema.validate(data, json.loads(read("examples/result.schema.json")))
        if (len(data["rows"]) != 44 or data["legal_currentness"] != "not_verified" or
                data["answer_safe"] or data["adoption_date"] is not None or
                data["effective_date"] is not None):
            raise ValueError("Example scope or currentness differs")
        examples[source] = data
    county = examples["douglas-ehs-fees-atlas-directed"]
    city = examples["pueblo-planning-fees-atlas-directed"]
    if (len(county["context"]) != 7 or len(city["context"]) != 4 or
            sum(len(r["nested"]) for r in city["rows"]) != 43 or
            sum(c["native_text"] is None for r in county["rows"] for c in r["cells"]) != 2):
        raise ValueError("Blank, context or nested association scope differs")
    return {"status": "verified_prepared_not_installed", "payloads": len(assets),
            "old_declarations_preserved": 69, "source_rows": [44, 44],
            "legal_currentness": "not_verified", "public_requests": 0}


if __name__ == "__main__":
    sys.stdout.write(json.dumps(verify(), indent=2) + "\n")
