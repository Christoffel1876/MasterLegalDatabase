"""Run one authorized exact-object LFS dry-run, retaining output privately."""
from __future__ import annotations

import hashlib
import json
import os
import re
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2] / 'MasterLegalDatabase'
COMMIT = '512684a65ae3c4eb51509b23520cfe41823ca0b9'
EXEC_PATH = '/Users/mcoors/.cache/codex-runtimes/codex-primary-runtime/'
EXEC_PATH += 'dependencies/native/git/libexec/git-core'
TARGETS = {
    '_CONTROL_PLANE/LOCAL_REVIEW_QUEUE.jsonl': (
        'c65a0f190fd5d5dca7810c47afc7e6843cd78520242add1fe6951545fe92ad00', 72395471),
    '08_County_Authorities/_index.jsonl': (
        'e896fc157617cfd9cd9839bf2bf955d893b66d7de514107e8b3c98dc4795c806', 172131787),
}

class Strict(BaseModel):
    """Refuse unmodeled receipt fields."""
    model_config = ConfigDict(extra='forbid', strict=True)

class Target(Strict):
    """Identify requested content without implying its availability."""
    path: str
    object_sha256: str
    object_size_bytes: int
    pointer_sha256: str

class Output(Strict):
    """Hash a privately retained child stream without exposing its body."""
    path: str
    sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    size_bytes: int
    visibility: Literal['private_unreviewed_cli_output_not_public_payload']

class Receipt(Strict):
    """Keep actual execution timing distinct from unavailable protocol details."""
    schema_version: Literal['lfs-origin-escalated-dry-run-1']
    started_at: str
    finished_at: str
    elapsed_seconds: float
    environment: Literal['require_escalated_authorized_sandbox_route_retry']
    command: list[str]
    environment_overrides: dict[str, str]
    requested_commit: str
    targets: list[Target]
    process_exit_code: int
    timed_out: bool
    status: Literal['cli_success_requires_availability_review',
                    'failed_requires_sanitized_error_review']
    outputs: list[Output]
    retained_storage_file_count: int
    retained_storage_bytes: int
    canonical_pointer_bytes_unchanged: bool
    repository_config_bytes_unchanged: bool
    logical_cli_invocations: Literal[1]
    independent_object_downloads_attempted: Literal[0]
    publisher_http_status: None
    object_availability: Literal['not_inferred_from_cli_exit_alone']
    limitations: list[str]


def now() -> str:
    """Read the actual UTC instant for this process."""
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def private_write(path: Path, data: bytes) -> Output:
    """Create one private stream file, without echoing content."""
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, 'wb') as target:
        target.write(data)
    return Output(path=path.relative_to(HERE).as_posix(), size_bytes=len(data),
                  sha256=hashlib.sha256(data).hexdigest(),
                  visibility='private_unreviewed_cli_output_not_public_payload')


def main() -> None:
    """Execute exactly once after checking both immutable checkpoint pointers."""
    if (HERE / 'ATTEMPT.json').exists() or (HERE / 'private').exists():
        raise ValueError('Existing attempt: refusing a retry or overwrite')
    before = {path: (ROOT / path).read_bytes() for path in TARGETS}
    config = (ROOT / '.git/config').read_bytes()
    targets = []
    for path, (oid, size) in TARGETS.items():
        checkpoint = subprocess.run(['git', 'show', f'{COMMIT}:{path}'], cwd=ROOT,
                                    capture_output=True, check=True, timeout=10).stdout
        expected = ('version https://git-lfs.github.com/spec/v1\n'
                    f'oid sha256:{oid}\nsize {size}\n').encode()
        if checkpoint != expected or before[path] != expected:
            raise ValueError('Checkpoint or working pointer changed')
        targets.append(Target(path=path, object_sha256=oid, object_size_bytes=size,
                              pointer_sha256=hashlib.sha256(expected).hexdigest()))
    storage = HERE / 'isolated-lfs-storage'
    command = ['/usr/bin/git', '--exec-path=' + EXEC_PATH,
        '-c', 'lfs.storage=' + str(storage), '-c', 'lfs.fetchrecentalways=false',
        '-c', 'lfs.fetchrecentrefsdays=0', '-c', 'lfs.fetchrecentcommitsdays=0',
        '-c', 'lfs.remote.searchall=false', '-c', 'lfs.remote.autodetect=false',
        '-c', 'lfs.concurrenttransfers=1', '-c', 'lfs.basictransfersonly=true',
        '-C', str(ROOT), 'lfs', 'fetch', '--dry-run', '--json',
        '--include=' + ','.join(TARGETS), '--exclude=', 'origin', COMMIT]
    overrides = {'GIT_OPTIONAL_LOCKS': '0', 'GIT_TERMINAL_PROMPT': '0'}
    env = dict(os.environ, **overrides)
    # Never enable HTTP traces; the normal existing credential helper stays private.
    for key in ['GIT_TRACE', 'GIT_TRACE_CURL', 'GIT_CURL_VERBOSE', 'GIT_TRANSFER_TRACE']:
        env.pop(key, None)
    (HERE / 'private').mkdir(mode=0o700)
    started_at = now()
    start = time.monotonic()
    process = subprocess.Popen(command, env=env, cwd=ROOT, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, start_new_session=True)
    timed_out = False
    try:
        stdout, stderr = process.communicate(timeout=90)
    except subprocess.TimeoutExpired:
        timed_out = True
        os.killpg(process.pid, signal.SIGKILL)
        stdout, stderr = process.communicate()
    finished_at = now()
    elapsed = time.monotonic() - start
    outputs = [private_write(HERE / 'private/stdout.bin', stdout),
               private_write(HERE / 'private/stderr.bin', stderr)]
    files = [p for p in storage.rglob('*') if p.is_file()] if storage.exists() else []
    receipt = Receipt(schema_version='lfs-origin-escalated-dry-run-1',
        started_at=started_at, finished_at=finished_at, elapsed_seconds=elapsed,
        environment='require_escalated_authorized_sandbox_route_retry', command=command,
        environment_overrides=overrides, requested_commit=COMMIT, targets=targets,
        process_exit_code=process.returncode, timed_out=timed_out,
        status='cli_success_requires_availability_review' if process.returncode == 0 else
               'failed_requires_sanitized_error_review', outputs=outputs,
        retained_storage_file_count=len(files),
        retained_storage_bytes=sum(p.stat().st_size for p in files),
        canonical_pointer_bytes_unchanged=all((ROOT / p).read_bytes() == b
                                            for p, b in before.items()),
        repository_config_bytes_unchanged=(ROOT / '.git/config').read_bytes() == config,
        logical_cli_invocations=1, independent_object_downloads_attempted=0,
        publisher_http_status=None, object_availability='not_inferred_from_cli_exit_alone',
        limitations=['The CLI dry run can contact the LFS batch endpoint. No separate '
                     'download action will be followed by Atlas in this attempt.',
                     'No raw child output is published here; private stream files require '
                     'explicit redaction and source-bound interpretation before sharing.',
                     'The exact low-level network request count is not observed by this '
                     'wrapper; one CLI invocation and its actual wall-clock interval are recorded.',
                     'No publisher status or object availability is inferred from process exit.'])
    body = receipt.model_dump_json(indent=2) + '\n'
    Receipt.model_validate_json(body)
    with (HERE / 'ATTEMPT.json').open('x') as target:
        target.write(body)
    with (HERE / 'ATTEMPT.schema.json').open('x') as target:
        target.write(json.dumps(Receipt.model_json_schema(), indent=2) + '\n')
    sys.stdout.write(json.dumps({'status':receipt.status, 'exit_code':process.returncode,
        'timed_out':timed_out, 'started_at':started_at, 'finished_at':finished_at,
        'private_stdout_bytes':len(stdout), 'private_stderr_bytes':len(stderr),
        'retained_storage_files':len(files), 'retained_storage_bytes':
        receipt.retained_storage_bytes, 'pointers_unchanged':
        receipt.canonical_pointer_bytes_unchanged,
        'config_unchanged':receipt.repository_config_bytes_unchanged}) + '\n')


if __name__ == '__main__':
    main()
