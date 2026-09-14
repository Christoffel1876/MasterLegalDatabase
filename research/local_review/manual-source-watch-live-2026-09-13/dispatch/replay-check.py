"""Verify a sealed actual run after expiry with transport explicitly disabled."""
from contextlib import redirect_stdout
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import io
import json
import sys

REPO = Path('/Users/mcoors/Documents/Project Geode/MasterLegalDatabase')
sys.path.insert(0, str(REPO))
from geode.pipeline import manual_source_watch as watch
from pydantic import BaseModel, ConfigDict

NAME = 'atlas-maintained-20260913T004429Z'
OUTPUT = REPO / watch.RUNTIME / NAME
DEST = Path('/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-12/'
            'manual-watch-maintained-root-dispatch')


class Receipt(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    checked_at: str
    original_deadline: str
    check_occurred_after_original_deadline: bool
    transport_calls: int
    exit_code: int
    returned_original_report_bytes: bool
    all_run_bytes_unchanged: bool
    report_sha256: str
    helper_sha256: str
    adapter_sha256: str
    legal_currentness: str


def identities() -> dict[str, str]:
    return {p.relative_to(OUTPUT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in OUTPUT.rglob('*') if p.is_file()}


if __name__ == '__main__':
    now = datetime.now(timezone.utc)
    deadline = json.loads((OUTPUT / 'run.json').read_bytes())['deadline']
    assert now > datetime.fromisoformat(deadline.replace('Z', '+00:00')), 'Not expired yet'
    before = identities()
    calls = []

    def no_transport(*args, **kwargs):
        calls.append(True)
        raise AssertionError('Replay attempted transport')

    watch.g.transport = no_transport
    captured = io.StringIO()
    with redirect_stdout(captured):
        code = watch.main(['--root', str(REPO), '--execute', '--run-name', NAME,
            '--reviewed-selection-sha256',
            '91b4c46f7121de66d70b353405900f9d1ed3a3247718a9471ad2f1a9afa6dabb'])
    report = (OUTPUT / 'report.json').read_bytes()
    receipt = Receipt(checked_at=now.isoformat(), original_deadline=deadline,
        check_occurred_after_original_deadline=True, transport_calls=len(calls), exit_code=code,
        returned_original_report_bytes=captured.getvalue().encode() == report,
        all_run_bytes_unchanged=before == identities(), report_sha256=hashlib.sha256(report).hexdigest(),
        helper_sha256=watch.transport_identity(), adapter_sha256=watch.implementation_identity(),
        legal_currentness='not_verified')
    assert (code == 0 and not calls and receipt.returned_original_report_bytes
            and receipt.all_run_bytes_unchanged)
    with (DEST / 'EXPIRED_REPLAY.json').open('x') as handle:
        handle.write(receipt.model_dump_json(indent=2) + '\n')
    with (DEST / 'EXPIRED_REPLAY.schema.json').open('x') as handle:
        handle.write(json.dumps(Receipt.model_json_schema(), indent=2) + '\n')
    print(receipt.model_dump_json(indent=2))
