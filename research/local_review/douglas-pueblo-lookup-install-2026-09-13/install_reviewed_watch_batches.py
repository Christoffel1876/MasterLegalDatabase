"""Install exact reviewed additive watch files and preserve the bounded review record."""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

BASE = Path('/Users/mcoors/Documents/Project Geode')
ROOT = BASE / 'MasterLegalDatabase'
HANDOFF = BASE / 'handoffs/run-2026-09-12/extended-run'
OUT = ROOT / 'research/local_review/manual-watch-batches-install-2026-09-13'
PIN = 'ef2d664301fa00935100307628ec5ac0317bfd622480dc79c0d92ce44b8b159f'
AUDIT_PIN = '633d3df6e55d5b202ab77886f50c2fcb2e36be9379dfc12b1559c2a4255fee13'


class Ref(BaseModel):
    """One exact relative file identity."""
    model_config = ConfigDict(extra='forbid')
    path: str
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    size_bytes: int = Field(ge=0)


class Receipt(BaseModel):
    """Root installation, with no implicit public execution or currentness claim."""
    model_config = ConfigDict(extra='forbid')
    status: Literal['installed_exact_reviewed_files']
    finished_at: str
    proposal_sha256: str
    review_sha256: str
    installed_files: list[Ref]
    preserved_files: list[Ref]
    unchanged_springs_inputs: list[Ref]
    public_requests: Literal[0] = 0
    legal_currentness: Literal['not_verified'] = 'not_verified'
    full_repository_suite: Literal['pending_after_remaining_code_integration']


def identity(path: str, data: bytes) -> Ref:
    """Describe the same in-memory bytes that will be consumed."""
    return Ref(path=path, sha256=hashlib.sha256(data).hexdigest(), size_bytes=len(data))


def read(path: Path) -> bytes:
    """Reject nonordinary files and aliases."""
    if not path.is_file() or any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError(f'Unsafe input {path}')
    return path.read_bytes()


def closed(path: Path, pin: str) -> tuple[dict, dict[str, bytes]]:
    """Capture a pinned closed package before making any destination changes."""
    manifest = read(path / 'FINAL_MANIFEST.json')
    if hashlib.sha256(manifest).hexdigest() != pin:
        raise ValueError('Manifest pin mismatch')
    value = json.loads(manifest)
    files = {'FINAL_MANIFEST.json': manifest}
    for item in value['files']:
        ref = Ref.model_validate(item)
        if Path(ref.path).is_absolute() or '..' in Path(ref.path).parts or ref.path in files:
            raise ValueError('Unsafe or duplicate member')
        data = read(path / ref.path)
        if identity(ref.path, data) != ref:
            raise ValueError('Payload identity mismatch: ' + ref.path)
        files[ref.path] = data
    actual = {p.relative_to(path).as_posix() for p in path.rglob('*') if p.is_file()}
    if actual != set(files) or any(p.is_symlink() for p in path.rglob('*')):
        raise ValueError('Package closure mismatch')
    return value, files


def new_file(path: Path, data: bytes) -> None:
    """Write a new file atomically, refusing any overwrite."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.tmp')
    if path.exists() or temp.exists():
        raise ValueError('Existing destination: ' + str(path))
    with temp.open('xb') as output:
        output.write(data)
        output.flush()
        os.fsync(output.fileno())
    os.replace(temp, path)


def main() -> None:
    """Freeze approval evidence and install only already reviewed new target paths."""
    if OUT.exists():
        raise ValueError('Installation receipt already exists')
    manifest, proposed = closed(HANDOFF / 'manual-watch-expansion-revision', PIN)
    _, audit = closed(HANDOFF / 'manual-watch-expansion-revision-independent-review', AUDIT_PIN)
    targets = {rel: proposed['proposed/' + rel] for rel in manifest['installation_files']}
    if len(targets) != 16 or any((ROOT / rel).exists() for rel in targets):
        raise ValueError('Installation is not the expected additive 16-file subset')
    validation = json.loads(proposed['VALIDATION.json'])
    old = [Ref.model_validate(v) for v in validation['old_springs_inputs']]
    for ref in old:
        if identity(ref.path, read(ROOT / ref.path)) != ref:
            raise ValueError('Retained Springs input changed')
    frozen = {f'prepared/{k}': v for k, v in proposed.items()}
    frozen.update({f'independent-review/{k}': v for k, v in audit.items()})
    frozen['install_reviewed_watch_batches.py'] = read(Path(__file__))
    for rel, data in frozen.items():
        new_file(OUT / rel, data)
    for rel, data in targets.items():
        new_file(ROOT / rel, data)
        if read(ROOT / rel) != data:
            raise ValueError('Installed file mismatch')
    for ref in old:
        if identity(ref.path, read(ROOT / ref.path)) != ref:
            raise ValueError('Retained Springs input changed during install')
    receipt = Receipt(
        status='installed_exact_reviewed_files',
        finished_at=datetime.now(timezone.utc).isoformat(),
        proposal_sha256=PIN, review_sha256=AUDIT_PIN,
        installed_files=[identity(k, v) for k, v in sorted(targets.items())],
        preserved_files=[identity(k, v) for k, v in sorted(frozen.items())],
        unchanged_springs_inputs=old,
        full_repository_suite='pending_after_remaining_code_integration',
    )
    new_file(OUT / 'RECEIPT.schema.json',
             (json.dumps(Receipt.model_json_schema(), indent=2) + '\n').encode())
    new_file(OUT / 'RECEIPT.json', (receipt.model_dump_json(indent=2) + '\n').encode())
    new_file(OUT / 'README.md', (
        '---\nstatus: installed_exact_reviewed_files\nlegal_currentness: not_verified\n---\n'
        '# Root installation receipt\n\n'
        'Atlas reviewed the original proposal, focused replay-policy changes, independent '
        'counterexamples and their passing recheck. Root verified both closed packages and '
        'all six canonical source bindings before installing these 16 new files.\n\n'
        'The prepared guide retains its preparation-time wording. This receipt records the '
        'later actual installation. No public request or schedule was started by installation. '
        'The original Springs implementation, configuration and historical run remain unchanged. '
        'A later execution receipt must establish any live comparison.\n'
    ).encode())
    print(receipt.model_dump_json(include={'status', 'finished_at', 'public_requests'}))


if __name__ == '__main__':
    main()
