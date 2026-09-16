"""Preserve exact index/export/sandbox-smoke receipts from the completed checkpoint."""
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
import hashlib
import json
import jsonschema
from pydantic import BaseModel, ConfigDict

BASE = Path('/Users/mcoors/Documents/Project Geode')
RUN = BASE/'handoffs/run-2026-09-12'
REPO = BASE/'MasterLegalDatabase'
SMOKE = Path('/private/tmp/geode-clean-smoke-2f2b450-isolated')
OUT = REPO/'docs/audits/FOUR_HOUR_RUN_2026-09-12/CLEAN_ARCHIVE_2F2B450'


class Ref(BaseModel):
    model_config = ConfigDict(extra='forbid')
    path: str
    sha256: str
    size_bytes: int
    copied_from: str


class Preservation(BaseModel):
    model_config = ConfigDict(extra='forbid')
    preserved_at: datetime
    checkpoint_commit: str
    index_files_verified: int
    archive_files_verified: int
    smoke_checks_passed: int
    files: list[Ref]
    network_requested_during_preservation: Literal[False]
    scope: str
    legal_currentness: Literal['not_verified']


def main() -> None:
    receipt = json.loads((SMOKE/'RUN_RECEIPT.json').read_bytes())
    jsonschema.validate(receipt, json.loads((RUN/'clean-archive-smoke/'
                                           'RUN_RECEIPT.schema.json').read_bytes()))
    assert receipt['status'] == 'passed' and len(receipt['checks']) == 14
    assert all(check['passed'] and not check['errors'] for check in receipt['checks'])
    assert receipt['isolation'] == 'sandbox_exec'
    assert receipt['network_denied_for_child_processes'] is True
    for check in receipt['checks']:
        for name in ('stdout','stderr'):
            ref = check[name]
            data = (SMOKE/ref['path']).read_bytes()
            assert len(data) == ref['size_bytes']
            assert hashlib.sha256(data).hexdigest() == ref['sha256']
    export = json.loads((RUN/'clean-archive-export/ARCHIVE_RECEIPT.json').read_bytes())
    assert export['verified_files'] == 9322
    assert export['commit'] == receipt['commit_label']
    payloads = []
    for source, prefix in [(RUN/'clean-archive-export','export'),
                           (RUN/'clean-archive-smoke','harness'), (SMOKE,'execution')]:
        for path in sorted(source.rglob('*')):
            if path.is_symlink():
                raise ValueError(f'Symlink not allowed: {path}')
            if path.is_file():
                payloads.append((path, prefix+'/'+path.relative_to(source).as_posix()))
    for name in ('FINAL_INDEX_VERIFICATION.json','FINAL_INDEX_VERIFICATION.schema.json',
                 'verify_final_index.py','create_clean_git_archive.py'):
        payloads.append((RUN/name,'index-and-export/'+name))
    payloads.append((Path(__file__),'preserve_clean_checkpoint_proof.py'))
    refs = []
    OUT.mkdir()
    for source, target in payloads:
        data = source.read_bytes()
        item = Ref(path=target,sha256=hashlib.sha256(data).hexdigest(),
                   size_bytes=len(data),copied_from=str(source))
        destination = OUT/target
        destination.parent.mkdir(parents=True,exist_ok=True)
        with destination.open('xb') as stream:
            stream.write(data)
        assert destination.read_bytes() == source.read_bytes()
        refs.append(item)
    preservation = Preservation(
        preserved_at=datetime.now(timezone.utc),checkpoint_commit=export['commit'],
        index_files_verified=1819,archive_files_verified=9322,smoke_checks_passed=14,
        files=refs,network_requested_during_preservation=False,
        scope=('Historical proof for checkpoint2f2b450 and inventory61/22/39 only. '
               'No rerun is claimed during copying. The archive itself is not duplicated. '
               'Network and original workspace were denied for smoke child processes; '
               'external runtimes and unrelated temporary reads were allowed.'),
        legal_currentness='not_verified')
    (OUT/'MANIFEST.schema.json').write_text(
        json.dumps(Preservation.model_json_schema(),indent=2)+'\n')
    (OUT/'MANIFEST.json').write_text(preservation.model_dump_json(indent=2)+'\n')
    actual = {p.relative_to(OUT).as_posix() for p in OUT.rglob('*') if p.is_file()}
    assert actual == {r.path for r in refs}|{'MANIFEST.json','MANIFEST.schema.json'}
    print(json.dumps({'preserved_files':len(actual),'checks':14,'path':str(OUT)}))


if __name__ == '__main__':
    main()
