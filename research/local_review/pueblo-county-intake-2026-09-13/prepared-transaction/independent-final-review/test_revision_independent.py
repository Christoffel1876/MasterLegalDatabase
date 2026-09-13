"""Independent temporary-fixture checks of the fixed-source intake writer."""
from __future__ import annotations
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

REVISION = Path(__file__).resolve().parent.parent / 'pueblo-county-fees-intake-revision'
sys.path.insert(0, str(REVISION))
import transaction as tx
spec = importlib.util.spec_from_file_location('revision_fixture', REVISION / 'test_transaction.py')
fixture_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture_module)


@pytest.fixture
def package(tmp_path, monkeypatch):
    """Reuse setup only; independent assertions and injected races follow."""
    root, base, plan = fixture_module.fixture.__wrapped__(tmp_path, monkeypatch)
    original = tx.mi.reconcile_manual_source_intake
    calls = []
    def readonly(*args, **kwargs):
        assert kwargs.get('dry_run', True) is True, 'Generic mutation API called'
        calls.append(True)
        return original(*args, **kwargs)
    monkeypatch.setattr(tx.mi, 'reconcile_manual_source_intake', readonly)
    return root, base, plan, calls, original


def rows(path):
    """Read JSONL records individually."""
    with path.open('rb') as handle:
        return [json.loads(line) for line in handle]


def foreign_arrival(root):
    """Represent another writer's new valid record; do not add it to the ledger."""
    old = tx.mi.ManualSourceIntakeRecord.model_validate(rows(root / tx.RAW)[0])
    path = root / '_RAW_ARCHIVE/manual_intake/08_County_Authorities/foreign/original.pdf'
    path.parent.mkdir(parents=True)
    path.write_bytes((root / old.archive_path).read_bytes())
    record = old.model_copy(update={
        'record_id': 'foreign', 'intake_id': 'MSI-foreign',
        'archive_path': path.relative_to(root).as_posix(),
        'received_at': datetime(2025, 2, 1, tzinfo=timezone.utc),
    })
    with (root / tx.RAW).open('ab') as handle:
        handle.write((record.model_dump_json() + '\n').encode())
    return (root / tx.RAW).read_bytes()


@pytest.mark.parametrize('boundary', ['raw', 'ledger', 'reconciled'])
def test_foreign_raw_never_enters_ledger_or_report(package, boundary):
    root, base, _, calls, _ = package
    arrived = []
    def inject(stage):
        if stage == boundary:
            arrived.append(foreign_arrival(root))
    with pytest.raises(ValueError, match='unrecognized canonical prefix/state'):
        tx.run(root, base=base, apply=True, fault=inject)
    assert (root / tx.RAW).read_bytes() == arrived[0]
    assert 'MSI-foreign' not in [r['intake_id'] for r in rows(root / tx.LEDGER)]
    report = json.loads((root / tx.REPORT).read_bytes())
    assert report['records'] == (2 if boundary == 'reconciled' else 1)
    assert 'MSI-foreign' not in report['archive_verification']['verified_intake_ids']
    assert not (base / 'execution/RECEIPT.json').exists()
    before = fixture_module.snap(root)
    with pytest.raises(ValueError):
        tx.run(root, base=base, apply=True)
    assert fixture_module.snap(root) == before
    assert calls


@pytest.mark.parametrize('boundary', ['intent', 'original', 'raw', 'ledger', 'reconciled'])
def test_exact_partial_recovery_and_repeat(package, boundary):
    root, base, plan, calls, _ = package
    original = {name: (root / name).read_bytes() for name in [tx.RAW, tx.LEDGER, tx.REPORT]}
    def interrupt(stage):
        if stage == boundary:
            raise RuntimeError('temporary interruption')
    with pytest.raises(RuntimeError):
        tx.run(root, base=base, apply=True, fault=interrupt)
    intent_bytes = (base / 'execution/INTENT.json').read_bytes()
    intent = tx.Intent.model_validate_json(intent_bytes)
    expected = tx.report_bytes(intent)
    first = tx.run(root, base=base, apply=True)
    assert (base / 'execution/INTENT.json').read_bytes() == intent_bytes
    assert (root / tx.REPORT).read_bytes() == expected
    suffix = (intent.record.model_dump_json() + '\n').encode()
    for name in [tx.RAW, tx.LEDGER]:
        assert (root / name).read_bytes() == original[name] + suffix
    for name, prior in original.items():
        assert (root / '_SNAPSHOTS' / intent.record.intake_id / name).read_bytes() == prior
    assert intent.expected_report.generated_at == intent.actual_repository_received_at
    assert intent.record.received_at != plan.provenance.reported_finished_at
    assert intent.record.acquisition_method == 'received_review_package'
    assert intent.record.official_source_url is None
    after = fixture_module.snap(root)
    assert tx.run(root, base=base, verify=True) == first
    assert tx.run(root, base=base, apply=True) == first
    assert fixture_module.snap(root) == after
    assert calls


@pytest.mark.parametrize('field', ['records', 'verified_ids', 'missing_ids', 'generated_at'])
def test_intent_report_tampering_refused_before_canonical_write(package, field):
    root, base, _, _, _ = package
    def interrupt(stage):
        if stage == 'intent':
            raise RuntimeError('temporary interruption')
    with pytest.raises(RuntimeError):
        tx.run(root, base=base, apply=True, fault=interrupt)
    path = base / 'execution/INTENT.json'
    data = json.loads(path.read_bytes())
    report = data['expected_report']
    if field == 'records':
        report['records'] = 99
    elif field == 'verified_ids':
        report['archive_verification']['verified_intake_ids'].append('MSI-foreign')
    elif field == 'missing_ids':
        report['archive_verification']['missing_ledger_only_intake_ids'].append('MSI-invented')
    else:
        report['generated_at'] = '2030-01-01T00:00:00Z'
    path.write_text(json.dumps(data))
    before = fixture_module.snap(root)
    with pytest.raises(ValueError, match='intent report differs'):
        tx.run(root, base=base, apply=True)
    assert fixture_module.snap(root) == before


def test_missing_ledger_only_original_stays_missing(package, monkeypatch):
    root, base, plan, _, original_reconcile = package
    old = tx.mi.ManualSourceIntakeRecord.model_validate(rows(root / tx.RAW)[0])
    missing = old.model_copy(update={
        'intake_id': 'MSI-missing-history', 'record_id': 'missing-history',
        'archive_path': '_RAW_ARCHIVE/manual_intake/05_Executive_Orders/missing-history/old.pdf',
        'layer_id': '05_Executive_Orders',
    })
    with (root / tx.LEDGER).open('ab') as handle:
        handle.write((missing.model_dump_json() + '\n').encode())
    original_reconcile(root, dry_run=False)  # Temporary fixture preparation only.
    data = plan.model_dump(mode='json')
    for item in data['baseline']:
        if item['repository_path'] in [tx.LEDGER, tx.REPORT]:
            saved = base / item['preserved']['path']
            saved.write_bytes((root / item['repository_path']).read_bytes())
            item['preserved'] = fixture_module.ref(base, saved).model_dump(mode='json')
    data['ledger_before'], data['ledger_after'] = 2, 3
    revised = tx.Preparation.model_validate_json(json.dumps(data))
    monkeypatch.setattr(tx, 'load_plan', lambda base=tx.BASE: revised)
    tx.run(root, base=base, apply=True)
    report = json.loads((root / tx.REPORT).read_bytes())
    verification = report['archive_verification']
    assert report['records'] == 3 and verification['manifest_records'] == 2
    assert verification['ledger_only_intake_ids'] == ['MSI-missing-history']
    assert verification['missing_ledger_only_intake_ids'] == ['MSI-missing-history']
    assert 'MSI-missing-history' not in verification['verified_intake_ids']
    assert rows(root / tx.LEDGER)[1] == missing.model_dump(mode='json')
    assert not (root / missing.archive_path).exists()
