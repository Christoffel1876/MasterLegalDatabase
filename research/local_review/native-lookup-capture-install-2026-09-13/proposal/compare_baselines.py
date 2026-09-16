"""Freeze and compare nine complete installed/proposed outputs without changing production."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from pydantic import AwareDatetime, BaseModel, ConfigDict

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3] / "MasterLegalDatabase"


class Asset(BaseModel):
    """Exact fixture bytes with only the repository prefix normalized."""
    model_config = ConfigDict(strict=True, extra="forbid")
    source_id: str
    path: str
    sha256: str
    size_bytes: int
    proposed_equal: bool


class Receipt(BaseModel):
    """Actual measured normal-output preservation."""
    model_config = ConfigDict(strict=True, extra="forbid")
    started_at: AwareDatetime
    completed_at: AwareDatetime
    original_script_sha256: str
    proposed_script_sha256: str
    assets: list[Asset]
    schema_equal: bool
    public_requests: int = 0
    production_writes: int = 0


def load(path: Path, name: str):
    """Import a chosen source file without external package or network calls."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main() -> None:
    """Write frozen fixtures once after validating typed identities."""
    started = datetime.now(timezone.utc)
    old_path, new_path = HERE / "preimages/research_source_lookup.py", (
        HERE / "proposed/research_source_lookup.py")
    old, new = load(old_path, "before_capture"), load(new_path, "after_capture")
    sources = [old.SOURCE_ID, old.GREELEY_SOURCE_ID, old.WELD_SOURCE_ID,
               *old.GRID_SOURCES, old.SPRINGS_SOURCE_ID, old.EHS_SOURCE_ID, *old.DP_SOURCES]
    folder = HERE / "fixtures/nine-native-sources"
    folder.mkdir(parents=True)
    assets, schemas_equal = [], True
    for source in sources:
        baseline = old.lookup(ROOT, source, list_rows=True)
        proposed = new.lookup(ROOT, source, list_rows=True)
        schemas_equal &= type(baseline).model_json_schema() == type(proposed).model_json_schema()
        for suffix, left, right in [
            ("json", baseline.model_dump_json(indent=2) + "\n",
             proposed.model_dump_json(indent=2) + "\n"),
            ("md", old.render_markdown(baseline), new.render_markdown(proposed)),
        ]:
            raw = left.replace(str(ROOT), "__REPOSITORY__").encode()
            other = right.replace(str(ROOT), "__REPOSITORY__").encode()
            asset = Asset(source_id=source,
                path="fixtures/nine-native-sources/" + source + "." + suffix,
                sha256=hashlib.sha256(raw).hexdigest(), size_bytes=len(raw), proposed_equal=raw == other)
            Asset.model_validate_json(asset.model_dump_json())
            with (HERE / asset.path).open("xb") as handle:
                handle.write(raw)
            assets.append(asset)
        sys.stdout.write(source + ": " + str(all(a.proposed_equal for a in assets[-2:])) + "\n")
        sys.stdout.flush()
    receipt = Receipt(started_at=started, completed_at=datetime.now(timezone.utc),
        original_script_sha256=hashlib.sha256(old_path.read_bytes()).hexdigest(),
        proposed_script_sha256=hashlib.sha256(new_path.read_bytes()).hexdigest(),
        assets=assets, schema_equal=schemas_equal)
    raw = receipt.model_dump_json(indent=2) + "\n"
    Receipt.model_validate_json(raw)
    with (HERE / "BASELINES.json").open("x") as handle:
        handle.write(raw)
    with (HERE / "BASELINES.schema.json").open("x") as handle:
        handle.write(json.dumps(Receipt.model_json_schema(), indent=2) + "\n")


if __name__ == "__main__":
    main()
