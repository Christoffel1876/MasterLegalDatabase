"""Create new exact-copy preapply audit; never alter the received preparation."""
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import jsonschema
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

PARENT = Path('/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-13')
SOURCE = PARENT / 'ptolemy-chaffee-fee-intake-preparation'
DEST = PARENT / 'plato-chaffee-fee-intake-audit'
OLD = PARENT / 'plato-chaffee-intake-audit'
PIN = '8033006a57280b2ea897baa3bb3121e195edd3885ea9fa84c55af5998f83b2b1'

class Asset(BaseModel):
    """A hash-bound ordinary copied file."""
    model_config = ConfigDict(strict=True, extra='forbid')
    path: str
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    size_bytes: int = Field(ge=0)

class Receipt(BaseModel):
    """Actual copying custody, not execution or source-content approval."""
    model_config = ConfigDict(strict=True, extra='forbid')
    reviewer: Literal['Plato']
    source_directory: str
    copied_at: AwareDatetime
    source_manifest_sha256: str
    copied_files: Literal[253]
    copy_method: Literal['exact captured bytes, write-once destination']
    canonical_apply: Literal[False]
    public_requests: Literal[0]
    files: list[Asset]


def digest(raw: bytes) -> str:
    """Return an exact byte digest."""
    return hashlib.sha256(raw).hexdigest()

assert not DEST.exists(), 'Do not overwrite an existing audit'
assert not (SOURCE / 'execution').exists()
manifest_raw = (SOURCE / 'FINAL_MANIFEST.json').read_bytes()
assert digest(manifest_raw) == PIN
manifest = json.loads(manifest_raw)
jsonschema.validate(manifest, json.loads((SOURCE / 'FINAL_MANIFEST.schema.json').read_bytes()))
expected = {x['path'] for x in manifest['files']} | {'FINAL_MANIFEST.json'}
assert len(manifest['files']) == 252 and len(expected) == 253
actual = set()
buffers = {}
for path in sorted(SOURCE.rglob('*')):
    assert not path.is_symlink()
    if path.is_file():
        name = path.relative_to(SOURCE).as_posix()
        actual.add(name)
        buffers[name] = path.read_bytes()
assert actual == expected
for ref in manifest['files']:
    raw = buffers[ref['path']]
    assert digest(raw) == ref['sha256'] and len(raw) == ref['size_bytes']
DEST.mkdir()
for name, raw in buffers.items():
    path = DEST / 'reviewed-preparation' / name
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as handle:
        handle.write(raw)
refs = [Asset(path='reviewed-preparation/' + name, sha256=digest(raw), size_bytes=len(raw))
        for name, raw in sorted(buffers.items())]
receipt = Receipt(reviewer='Plato', source_directory=str(SOURCE),
    copied_at=datetime.now(timezone.utc), source_manifest_sha256=PIN, copied_files=253,
    copy_method='exact captured bytes, write-once destination', canonical_apply=False,
    public_requests=0, files=refs)
for name, value in [('COPY_RECEIPT', receipt)]:
    schema = type(value).model_json_schema()
    raw = value.model_dump_json(indent=2) + '\n'
    jsonschema.validate(json.loads(raw), schema)
    (DEST / (name + '.json')).write_text(raw)
    (DEST / (name + '.schema.json')).write_text(json.dumps(schema, indent=2) + '\n')
for name in ['independent_probes.py', 'run_checks.py', 'audit_models.py', 'verify_audit.py']:
    text = (OLD / name).read_text()
    if name == 'independent_probes.py':
        text = text.replace('exact two received PDF bodies', 'exact one received PDF body')
        text = text.replace('== 3', '== 2').replace('len(intent.records) == 2', 'len(intent.records) == 1')
        text = text.replace('exact_two_source_prefix', 'exact_one_source_prefix')
        text = text.replace('plato-chaffee-probe-', 'plato-chaffee-fee-probe-')
    if name == 'run_checks.py':
        text = text.replace("'popper-chaffee-intake-preparation'", "'ptolemy-chaffee-fee-intake-preparation'")
    if name == 'audit_models.py':
        text = text.replace('fixed_two_source_preapply', 'fixed_one_source_preapply')
        text = text.replace('min_length=2, max_length=2', 'min_length=1, max_length=1')
        text = text.replace('Literal[67]', 'Literal[69]').replace('Literal[68]', 'Literal[70]')
        text = text.replace('proposed_raw_records: Literal[69]', 'proposed_raw_records: Literal[70]')
        text = text.replace('proposed_ledger_records: Literal[70]', 'proposed_ledger_records: Literal[71]')
    if name == 'verify_audit.py':
        text = text.replace('a8f768ff4c00bf55ba2db4712d67183f8c739e8e59777fa9bfed77f1bd12ef4b',
            'a25b2071c9275af9b7299edf198b96870a79ba5ac8e0c412f6b8647774d683ca')
        text = text.replace('f6ba9314dbfb9c8fd546be3111485603bef5acdd544d6706bf3cd2bf6aca23fb',
            'd4342c76031ebcebb7948a137f96bf0f563be72d24ec76e0a5b7718074e127ef')
        text = text.replace('a27a0932e382605d4213ea0e2645725504b97539ba306668b2408d09e7ab0f86', PIN)
        text = text.replace('== 106', '== 253').replace('(67, 68, 69, 70)', '(69, 70, 70, 71)')
        text = text.replace("'sources': 2", "'sources': 1").replace("'physical_pages': 21", "'physical_pages': 2")
    (DEST / name).write_text(text)
shutil.copyfile(__file__, DEST / 'prepare_audit.py')
sys.stdout.write(str(DEST) + '\n')
