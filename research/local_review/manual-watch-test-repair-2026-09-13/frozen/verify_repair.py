"""Read-only portable verification of a test-only installation repair receipt."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Strict(BaseModel):
    """Reject undeclared fields and scalar coercion."""

    model_config = ConfigDict(extra='forbid', strict=True)


class Asset(Strict):
    """Bind an exact ordinary local payload."""

    path: str
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    size_bytes: int = Field(ge=0)


class Change(Strict):
    """A repository test adaptation and its unchanged exact preimage."""

    repository_path: str
    before: Asset
    after: Asset
    repository_snapshot: Asset


class Command(Strict):
    """An actual executed command, preserving unsuccessful collection separately."""

    argv: list[str]
    cwd: str
    exit_code: int
    log: Asset
    description: str


class Predecessor(Strict):
    """The earlier frozen package was checked in place but not duplicated in this repair."""

    path_at_verification: str
    manifest: Asset
    verified_payload_count: int
    all_payload_hashes_verified: Literal[True]
    payloads_excluded_from_this_receipt_package: Literal[True]


class Receipt(Strict):
    """An additive compatibility correction; no runtime policy or source bytes changed."""

    status: Literal['installed_focused_tests_passed']
    verified_at: str
    changes: list[Change]
    unchanged_repository_files: list[Asset]
    commands: list[Command]
    tests_passed: Literal[205]
    combined_branch_coverage_percent: float
    coverage: Asset
    predecessors: list[Predecessor]
    public_requests: Literal[0]
    runtime_config_changes: Literal[0]
    repository_full_suite_run: Literal[False]
    limits: list[str]


class Manifest(Strict):
    """Closed additive evidence membership, independent of the original checkout."""

    status: Literal['frozen']
    files: list[Asset]


def verify_asset(root: Path, ref: Asset) -> None:
    """Verify exact bytes without following symlinks or escaping the declared root."""
    relative = Path(ref.path)
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('Unsafe evidence path')
    path = root / relative
    if any(item.is_symlink() for item in [path, *path.parents]) or not path.is_file():
        raise ValueError('Nonordinary evidence')
    with path.open('rb') as handle:
        digest = hashlib.file_digest(handle, 'sha256').hexdigest()
    if digest != ref.sha256 or path.stat().st_size != ref.size_bytes:
        raise ValueError('Evidence bytes differ: ' + ref.path)


def main() -> int:
    """Verify portable receipt; optional --root additionally checks installed current files."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path)
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    manifest = Manifest.model_validate_json((here / 'FINAL_MANIFEST.json').read_bytes())
    expected = {ref.path for ref in manifest.files} | {'FINAL_MANIFEST.json'}
    if len(expected) != len(manifest.files) + 1:
        raise ValueError('Duplicate manifest member')
    actual = set()
    for path in here.rglob('*'):
        if path.is_symlink() or not (path.is_file() or path.is_dir()):
            raise ValueError('Nonordinary closed member')
        if path.is_file():
            actual.add(path.relative_to(here).as_posix())
    if actual != expected:
        raise ValueError('Closed package membership differs')
    for ref in manifest.files:
        verify_asset(here, ref)
    for name, model in [('RECEIPT', Receipt), ('FINAL_MANIFEST', Manifest)]:
        schema = json.loads((here / (name + '.schema.json')).read_bytes())
        if schema != model.model_json_schema():
            raise ValueError('Exported schema differs')
    receipt = Receipt.model_validate_json((here / 'RECEIPT.json').read_bytes())
    if len(receipt.changes) != 3 or receipt.combined_branch_coverage_percent < 90:
        raise ValueError('Repair scope or test evidence differs')
    coverage = json.loads((here / receipt.coverage.path).read_bytes())
    if coverage['totals']['percent_covered'] != receipt.combined_branch_coverage_percent:
        raise ValueError('Coverage summary differs')
    for change in receipt.changes:
        verify_asset(here, change.before)
        verify_asset(here, change.after)
        if change.before.sha256 != change.repository_snapshot.sha256:
            raise ValueError('Snapshot does not preserve exact preimage')
    for command in receipt.commands:
        verify_asset(here, command.log)
    if args.root:
        for change in receipt.changes:
            current = Asset(path=change.repository_path, sha256=change.after.sha256,
                            size_bytes=change.after.size_bytes)
            verify_asset(args.root, current)
            verify_asset(args.root, change.repository_snapshot)
        for ref in receipt.unchanged_repository_files:
            verify_asset(args.root, ref)
    print(json.dumps({'status': 'passed', 'test_files_changed': 3, 'tests_passed': 205,
                      'public_requests': 0, 'runtime_config_changes': 0,
                      'current_repository_checked': args.root is not None,
                      'predecessor_payloads_recomputed_portably': False}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
