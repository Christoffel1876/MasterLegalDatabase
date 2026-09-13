"""Offline fixture probe: an unrelated record arrives after the planned raw append."""
from pathlib import Path
from datetime import datetime, timezone
import importlib.util
import json
import sys
import tempfile
import pytest

BASE = Path('/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-12/extended-run')
PROPOSAL = BASE / 'pueblo-county-fees-intake-proposal'
sys.path.insert(0, str(PROPOSAL))
import transaction as tx
spec = importlib.util.spec_from_file_location('frozen_fixture', PROPOSAL / 'test_transaction.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

with tempfile.TemporaryDirectory(prefix='pueblo-intake-independent-') as name:
    mp = pytest.MonkeyPatch()
    root, base, plan = module.fixture.__wrapped__(Path(name), mp)
    foreign = None
    def simultaneous_writer(stage):
        global foreign
        if stage != 'raw':
            return
        with (root / tx.RAW).open('rb') as handle:
            old = tx.mi.ManualSourceIntakeRecord.model_validate_json(next(handle))
        target = root / '_RAW_ARCHIVE/manual_intake/08_County_Authorities/foreign/original.pdf'
        target.parent.mkdir(parents=True)
        target.write_bytes((root / old.archive_path).read_bytes())
        row = old.model_copy(update={
            'intake_id': 'MSI-foreign', 'record_id': 'foreign',
            'archive_path': target.relative_to(root).as_posix(),
            'received_at': datetime(2025, 2, 1, tzinfo=timezone.utc),
        })
        foreign = row.intake_id
        with (root / tx.RAW).open('ab') as handle:
            handle.write((row.model_dump_json() + '\n').encode())
    result = {'network_requests': 0, 'temporary_fixture_only': True}
    try:
        tx.run(root, base=base, apply=True, fault=simultaneous_writer)
        result['returned'] = 'success'
    except Exception as exc:
        result['returned'] = type(exc).__name__
        result['error'] = str(exc)
    for label, relative in [('raw', tx.RAW), ('ledger', tx.LEDGER)]:
        with (root / relative).open('rb') as handle:
            result[label + '_ids'] = [json.loads(line)['intake_id'] for line in handle]
    result['unrelated_record_promoted_to_ledger'] = foreign in result['ledger_ids']
    result['report_records'] = json.loads((root / tx.REPORT).read_bytes())['records']
    mp.undo()
    sys.stdout.write(json.dumps(result, indent=2) + '\n')
