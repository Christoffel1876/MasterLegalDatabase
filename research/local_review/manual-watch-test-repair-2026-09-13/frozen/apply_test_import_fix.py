"""Apply a reviewed test-only installation adaptation, preserving each exact preimage."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

from geode.utils.file_io import atomic_write_text

ROOT = Path.cwd()
OUT = ROOT.parent / 'handoffs/run-2026-09-12/extended-run/manual-watch-installed-test-repair'


class File(BaseModel):
    """Bind one ordinary local file."""

    model_config = ConfigDict(extra='forbid', strict=True)
    path: str
    sha256: str
    size_bytes: int


class Change(BaseModel):
    """The exact permitted before/after test adaptation."""

    model_config = ConfigDict(extra='forbid', strict=True)
    repository_path: str
    preimage: File
    before_sha256: str
    after_sha256: str


class Intent(BaseModel):
    """Record test-only scope before applying atomically snapshotted edits."""

    model_config = ConfigDict(extra='forbid', strict=True)
    prepared_at: str
    purpose: Literal['installed_test_import_and_fixture_root_compatibility']
    changes: list[Change]
    unchanged_runtime_config_and_other_installed_inputs: list[File]
    public_requests: Literal[0]


def digest(raw: bytes) -> str:
    """Return an exact byte fingerprint."""
    return hashlib.sha256(raw).hexdigest()


def main() -> None:
    """Require exact installed preimages, then adapt only the three reviewed test files."""
    names = ['tests/test_manual_source_watch_batches.py',
             'tests/test_manual_watch_batches_admission.py',
             'tests/test_manual_watch_batches_replay_policy.py']
    receipt = json.loads((ROOT / 'research/local_review/manual-watch-batches-install-2026-09-13'
                          / 'RECEIPT.json').read_bytes())
    expected = {f['path']: f for f in receipt['installed_files']}
    changes, content = [], {}
    for name in names:
        path = ROOT / name
        raw = path.read_bytes()
        if digest(raw) != expected[name]['sha256']:
            raise ValueError('Installed test changed before adaptation: ' + name)
        source = raw.decode('utf-8')
        if name.endswith('test_manual_source_watch_batches.py'):
            source = source.replace(
                "PROPOSED = Path(__file__).resolve().parents[1]\n"
                "SOURCE = (PROPOSED if (PROPOSED / 'AGENTS.md').exists() else\n"
                "          PROPOSED.parents[4] / 'MasterLegalDatabase')",
                'SOURCE = Path(__file__).resolve().parents[1]')
            source = source.replace('PROPOSED', 'SOURCE')
        else:
            source = source.replace('from test_manual_source_watch_batches import ',
                                    'from tests.test_manual_source_watch_batches import ')
            source = source.replace('NOW, PROPOSED, SOURCE, Response, packet',
                                    'NOW, SOURCE, Response, packet')
            source = source.replace('PROPOSED / w.SELECTION', 'SOURCE / w.SELECTION')
        changed = source.encode('utf-8')
        if changed == raw:
            raise ValueError('Expected adaptation was absent')
        preimage = OUT / 'preimages' / name
        preimage.parent.mkdir(parents=True, exist_ok=True)
        if preimage.exists():
            raise ValueError('Refuse replacing a prior preimage')
        temporary = preimage.with_suffix('.tmp')
        temporary.write_bytes(raw)
        temporary.replace(preimage)
        changes.append(Change(repository_path=name,
            preimage=File(path=preimage.relative_to(OUT).as_posix(),
                          sha256=digest(raw), size_bytes=len(raw)),
            before_sha256=digest(raw), after_sha256=digest(changed)))
        content[name] = source
    unchanged = []
    for name, entry in expected.items():
        if name in names:
            continue
        raw = (ROOT / name).read_bytes()
        if digest(raw) != entry['sha256']:
            raise ValueError('Other installed input changed: ' + name)
        unchanged.append(File.model_validate(entry))
    intent = Intent(prepared_at=datetime.now(timezone.utc).isoformat(),
                    purpose='installed_test_import_and_fixture_root_compatibility',
                    changes=changes,
                    unchanged_runtime_config_and_other_installed_inputs=unchanged,
                    public_requests=0)
    raw = intent.model_dump_json(indent=2) + '\n'
    Intent.model_validate_json(raw)
    if (OUT / 'INTENT.json').exists():
        raise ValueError('This adaptation has already been recorded')
    atomic_write_text(OUT / 'INTENT.json', raw, OUT)
    atomic_write_text(OUT / 'INTENT.schema.json',
                      json.dumps(Intent.model_json_schema(), indent=2) + '\n', OUT)
    before = set((ROOT / '_SNAPSHOTS').glob('snapshot_*/tests/test_manual*watch*.py'))
    for name, source in content.items():
        atomic_write_text(ROOT / name, source, ROOT)
    after = set((ROOT / '_SNAPSHOTS').glob('snapshot_*/tests/test_manual*watch*.py'))
    for snapshot in sorted(after - before):
        print(snapshot.relative_to(ROOT))


if __name__ == '__main__':
    main()
