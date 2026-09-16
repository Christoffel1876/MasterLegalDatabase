"""Offline portable custody replay of the frozen prototype and its one actual live check."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Literal

import jsonschema
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

HERE = Path(__file__).resolve().parent


class Strict(BaseModel):
    """Reject undocumented fields and coercion in custody records."""
    model_config = ConfigDict(extra='forbid', strict=True)


class Ref(Strict):
    """Exact relative file bytes, not an external path or active source URL."""
    path: str
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    size_bytes: int = Field(ge=0)


class Receipt(Strict):
    """Exact historical copy receipt; original absolute paths are recorded claims only."""
    captured_at: AwareDatetime
    status: Literal['accepted_finite_live_check_not_recurring_deployment']
    originals: dict[str, str]
    files: list[Ref]
    no_private_header_files: Literal[True]
    legal_currentness: Literal['not_verified']


class Inventory(Strict):
    """Closed package inventory excluding only its own final manifest."""
    files: list[Ref]

    @model_validator(mode='after')
    def unique(self) -> Inventory:
        """Refuse duplicate relative identities."""
        if len({r.path for r in self.files}) != len(self.files):
            raise ValueError('Duplicate file identity')
        return self


class Result(Strict):
    """Typed verification outcome, separate from legal currentness and deployment."""
    status: Literal['passed'] = 'passed'
    closed_files: int
    unchanged_copied_files: int
    actual_live_events: Literal[2] = 2
    actual_live_bytes: Literal[421075] = 421075
    actual_live_statuses: list[Literal['unchanged']]
    public_requests_by_verifier: Literal[0] = 0
    recurring_deployment: Literal['not_established_by_this_packet']
    legal_currentness: Literal['not_verified'] = 'not_verified'


def checked(ref: Ref) -> bytes:
    """Read only a regular local member whose size and hash match its receipt."""
    rel = Path(ref.path)
    if rel.is_absolute() or '..' in rel.parts:
        raise ValueError('Unsafe relative member')
    path = HERE / rel
    if not path.is_file() or any(p.is_symlink() for p in [path, *path.parents]):
        raise ValueError('Missing or symlinked member')
    data = path.read_bytes()
    if len(data) != ref.size_bytes or hashlib.sha256(data).hexdigest() != ref.sha256:
        raise ValueError('Member bytes differ: ' + ref.path)
    return data


def inventory() -> Inventory:
    """Validate the exact closed set before and after offline replay."""
    record = Inventory.model_validate_json((HERE / 'FINAL_MANIFEST.json').read_bytes())
    jsonschema.Draft202012Validator(json.loads(
        (HERE / 'FINAL_MANIFEST.schema.json').read_bytes())).validate(record.model_dump())
    actual = set()
    for path in HERE.rglob('*'):
        if path.is_symlink():
            raise ValueError('Symlink in package')
        if path.is_file() and path.name != 'FINAL_MANIFEST.json':
            actual.add(path.relative_to(HERE).as_posix())
    if actual != {r.path for r in record.files}:
        raise ValueError('Closed file inventory differs')
    for ref in record.files:
        checked(ref)
    return record


def verify() -> Result:
    """Replay only pinned offline verifiers after validating every copied payload."""
    before = inventory()
    receipt_data = (HERE / 'COPY_RECEIPT.json').read_bytes()
    receipt = Receipt.model_validate_json(receipt_data)
    jsonschema.Draft202012Validator(json.loads(
        (HERE / 'COPY_RECEIPT.schema.json').read_bytes())).validate(json.loads(receipt_data))
    if len(receipt.files) != 103 or len({r.path for r in receipt.files}) != 103:
        raise ValueError('Unexpected copied payload count')
    for ref in receipt.files:
        checked(ref)
        if 'private.headers' in ref.path:
            raise ValueError('Private header payload is not permitted')
    copied = {p.relative_to(HERE).as_posix() for name in ['prototype', 'dispatch']
              for p in (HERE / name).rglob('*') if p.is_file()}
    if copied != {r.path for r in receipt.files}:
        raise ValueError('Copied payload scope changed')
    expected = {
        'prototype/verify_preparation.py':
            '21f26cbc6212f4e58911455562d2930f0cfacbd841b70fee9a1e6d1c63a28112',
        'prototype/watch.py':
            '5772538f29e10e1acba965fc9589ed5a37e8a6b680d41dcbdac8c35f186763da',
    }
    if any(next(r.sha256 for r in receipt.files if r.path == path) != digest
           for path, digest in expected.items()):
        raise ValueError('Unexpected frozen offline verifier')
    commands = [
        [sys.executable, '-I', '-B', str(HERE / 'prototype/verify_preparation.py')],
        [sys.executable, '-I', '-B', str(HERE / 'prototype/watch.py'),
         '--verify-run', 'atlas-live-20260913T000559Z'],
    ]
    for command in commands:
        process = subprocess.run(command, cwd=HERE / 'prototype', capture_output=True,
                                 text=True, timeout=90, check=False)
        if process.returncode:
            raise ValueError('Frozen offline replay failed: ' + process.stderr[:2000])
    report_path = HERE / 'prototype/runs/atlas-live-20260913T000559Z/report.json'
    report = json.loads(report_path.read_bytes())
    auth = json.loads((HERE / 'dispatch/AUTHORIZATION.json').read_bytes())
    if (report['dispatch_at'] != auth['dispatch_at'] or
            report['plan_sha256'] != auth['pins']['WATCH_PLAN.json'] or
            report['mode'] != 'live_http' or report['clock_basis'] != 'actual_utc_clock' or
            report['state']['request_count'] != 2 or report['state']['charged_bytes'] != 421075 or
            (HERE / 'dispatch/stdout.json').read_bytes() != report_path.read_bytes()):
        raise ValueError('Actual dispatch/report binding differs')
    statuses = [row['status'] for row in report['observations']]
    if statuses != ['unchanged', 'unchanged'] or inventory() != before:
        raise ValueError('Actual byte outcomes or final inventory differ')
    return Result(closed_files=len(before.files), unchanged_copied_files=103,
                  actual_live_statuses=statuses,
                  recurring_deployment='not_established_by_this_packet')


if __name__ == '__main__':
    try:
        result = verify()
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        sys.stderr.write(type(error).__name__ + ': ' + str(error) + '\n')
        raise SystemExit(1)
    sys.stdout.write(result.model_dump_json(indent=2) + '\n')
