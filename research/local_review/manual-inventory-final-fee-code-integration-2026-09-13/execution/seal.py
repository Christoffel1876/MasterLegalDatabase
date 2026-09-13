"""Close exact execution evidence after the authorized inventory-only installation."""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import jsonschema
from pydantic import AwareDatetime

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE.parent))
from models import Asset, InstallReceipt, Strict


class ExecutionManifest(Strict):
    """Closed actual-install evidence, distinct from the earlier preparation."""
    recorded_at: AwareDatetime
    status: Literal['closed_inventory_installation_execution']
    files: list[Asset]
    exclusions: Literal['FINAL_MANIFEST.json, FINAL_MANIFEST.schema.json']


def seal() -> None:
    """Validate the actual receipt, then write a strict closed inventory once."""
    data = (BASE / 'RECEIPT.json').read_bytes()
    receipt = InstallReceipt.model_validate_json(data)
    schema = json.loads((BASE / 'RECEIPT.schema.json').read_bytes())
    assert schema == InstallReceipt.model_json_schema()
    jsonschema.validate(json.loads(data), schema)
    assert receipt.records == 70 and receipt.reviewed == receipt.unmapped == 35
    assert receipt.raw_manifest_before == receipt.raw_manifest_after
    files = []
    for path in sorted(BASE.rglob('*')):
        assert not path.is_symlink()
        if path.is_file():
            raw = path.read_bytes()
            files.append(Asset(path=path.relative_to(BASE).as_posix(),
                               sha256=hashlib.sha256(raw).hexdigest(), size_bytes=len(raw)))
    result = ExecutionManifest(recorded_at=datetime.now(timezone.utc),
        status='closed_inventory_installation_execution', files=files,
        exclusions='FINAL_MANIFEST.json, FINAL_MANIFEST.schema.json')
    raw = result.model_dump_json(indent=2) + '\n'
    schema = ExecutionManifest.model_json_schema()
    jsonschema.validate(json.loads(raw), schema)
    with (BASE / 'FINAL_MANIFEST.schema.json').open('x') as handle:
        handle.write(json.dumps(schema, indent=2) + '\n')
    with (BASE / 'FINAL_MANIFEST.json').open('x') as handle:
        handle.write(raw)
    sys.stdout.write('Execution evidence sealed.\n')


if __name__ == '__main__':
    seal()
