"""Apply only the root-authorized fixed inventory targets with preserved preimages."""
import hashlib
import json
import os
import stat
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import jsonschema

BASE = Path(__file__).resolve().parents[1]
ROOT = BASE.parents[2] / 'MasterLegalDatabase'
sys.path.insert(0, str(BASE))
from models import Asset, InstallReceipt, Preparation
from verify_preparation import verify


def asset(path: Path, parent: Path) -> Asset:
    """Bind exact ordinary file bytes."""
    if any(p.is_symlink() for p in [path, *path.parents]):
        raise ValueError('Refuse symlinked target')
    data = path.read_bytes()
    return Asset(path=path.relative_to(parent).as_posix(),
                 sha256=hashlib.sha256(data).hexdigest(), size_bytes=len(data))


def replace(path: Path, before: bytes, after: bytes) -> None:
    """Atomically replace only a byte-equal reviewed predecessor."""
    if path.read_bytes() == after:
        return
    if path.read_bytes() != before or path.is_symlink():
        raise ValueError('Unexpected maintained predecessor: ' + str(path))
    mode = stat.S_IMODE(path.stat().st_mode)
    fd, temporary = tempfile.mkstemp(prefix='.plato-inventory-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(after)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, mode)
        if path.read_bytes() != before or path.is_symlink():
            raise ValueError('Maintained predecessor changed during installation')
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def run() -> None:
    """Install fixed code/data and record the actual maintained CLI verification."""
    started = datetime.now(timezone.utc)
    if (BASE / 'execution/RECEIPT.json').exists():
        raise ValueError('Installation receipt already exists; verify instead of rerunning')
    if hashlib.sha256((BASE / 'FINAL_MANIFEST.json').read_bytes()).hexdigest() != (
        '9412785bbdd67a8c9d4467a42f2ba7de91cc9d62bcedcba301c052c0b2e6a8a9'):
        raise ValueError('Authorized preparation manifest differs')
    verify(ROOT)
    raw = (BASE / 'PREPARATION.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != (
        '8f02c21994697fc3cbedc3ea58c27fc80a2937a4ffa07ff79c0c416547dd9030'):
        raise ValueError('Authorized preparation differs')
    prep = Preparation.model_validate_json(raw)
    raw_before = asset(ROOT / prep.raw_manifest.path, ROOT)
    if raw_before != prep.raw_manifest:
        raise ValueError('Actual intake baseline changed')
    before = {}
    after = {}
    for target in prep.targets:
        before[target.repository_path] = (BASE / target.before.path).read_bytes()
        after[target.repository_path] = (BASE / target.after.path).read_bytes()
        actual = (ROOT / target.repository_path).read_bytes()
        if actual != before[target.repository_path]:
            raise ValueError('Unexpected target before installation')
        asset(ROOT / target.repository_path, ROOT)
    snapshot = ROOT / (
        'research/local_review/manual-source-review-inventory-2026-09-11/'
        '_SNAPSHOTS/BEFORE_FINAL_FEE_CODE_2026-09-13')
    if any(p.is_symlink() for p in [snapshot, *snapshot.parents]):
        raise ValueError('Unsafe snapshot path')
    snapshot.mkdir(parents=True, exist_ok=False)
    for path in sorted((BASE / 'preimages').iterdir()):
        destination = snapshot / path.name
        data = path.read_bytes()
        if destination.exists():
            if destination.read_bytes() != data or destination.is_symlink():
                raise ValueError('Snapshot conflict')
        else:
            with destination.open('xb') as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
    for target in prep.targets:
        replace(ROOT / target.repository_path, before[target.repository_path],
                after[target.repository_path])
    completed = subprocess.run(
        [sys.executable, '-B', '-m', 'geode.pipeline.manual_review_inventory', '--root', '.', '--check'],
        cwd=ROOT, capture_output=True, timeout=120, check=False)
    for name, data in [('stdout.txt', completed.stdout), ('stderr.txt', completed.stderr)]:
        with (BASE / 'execution' / name).open('xb') as stream:
            stream.write(data)
    if completed.returncode != 0:
        raise ValueError('Installed read-only CLI verification failed; retain outputs and preimages')
    for target in prep.targets:
        installed = asset(ROOT / target.repository_path, ROOT)
        if (installed.sha256, installed.size_bytes) != (
                target.after.sha256, target.after.size_bytes):
            raise ValueError('Installed target identity differs')
    raw_after = asset(ROOT / prep.raw_manifest.path, ROOT)
    if raw_after != raw_before:
        raise ValueError('Raw manifest changed during inventory installation')
    receipt = InstallReceipt(
        started_at=started, completed_at=datetime.now(timezone.utc),
        status='installed_and_verified', preparation_sha256=hashlib.sha256(raw).hexdigest(),
        targets=prep.targets, snapshot_directory=snapshot.relative_to(ROOT).as_posix(),
        verifier_exit_code=0, verifier_stdout=asset(BASE / 'execution/stdout.txt', BASE),
        verifier_stderr=asset(BASE / 'execution/stderr.txt', BASE),
        raw_manifest_before=raw_before, raw_manifest_after=raw_after, source_files_changed=False,
        records=70, reviewed=35, unmapped=35)
    payload = receipt.model_dump_json(indent=2) + '\n'
    schema = receipt.model_json_schema()
    jsonschema.validate(json.loads(payload), schema)
    with (BASE / 'execution/RECEIPT.schema.json').open('x') as stream:
        stream.write(json.dumps(schema, indent=2) + '\n')
    with (BASE / 'execution/RECEIPT.json').open('x') as stream:
        stream.write(payload)
    sys.stdout.write('Installed and verified: 70 sources / 35 review links / 35 unmapped.\n')


if __name__ == '__main__':
    run()
