"""Offline fixture-only refusal, prefix and replay checks."""
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
import pymupdf
import pytest
import transaction as tx
from models import Asset, Baseline, Preparation


def snap(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*')
            if p.is_file() and not p.is_symlink()}


def ref(base, path):
    raw = path.read_bytes()
    return Asset(path=path.relative_to(base).as_posix(), sha256=tx.digest(raw), size_bytes=len(raw))


@pytest.fixture
def fixture(tmp_path, monkeypatch):
    root = tmp_path / 'corpus'; root.mkdir()
    base = tmp_path / 'packet'; base.mkdir()
    shutil.copytree(tx.BASE / 'inputs', base / 'inputs')
    plan = tx.load_plan()
    document = pymupdf.open(); page = document.new_page()
    page.insert_text((72, 72), 'Synthetic historical fixture; no legal claim.')
    raw = document.tobytes(); document.close()
    old_path = '_RAW_ARCHIVE/manual_intake/08_County_Authorities/fixture-old/original.pdf'
    dest = root / old_path; dest.parent.mkdir(parents=True); dest.write_bytes(raw)
    old = tx.mi.ManualSourceIntakeRecord(intake_id='MSI-fixture-old', record_id='fixture-old',
        layer_id='08_County_Authorities', official_source_name='Synthetic fixture',
        official_source_url=None, acquisition_method='received_review_package',
        received_from='fixture', reviewer_name='fixture', reviewer_email=None,
        custody_note='Synthetic historical record, not actual acquisition.',
        original_filename='original.pdf', archive_path=old_path, sha256=tx.digest(raw),
        size_bytes=len(raw), source_format='pdf',
        received_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        status='archived_pending_pipeline', blocked_queue_match=False, boundary='fixture only')
    for name in [tx.RAW, tx.LEDGER]:
        p = root / name; p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(old.model_dump(mode='json'), separators=(', ', ': ')) + '\n')
    tx.mi.reconcile_manual_source_intake(root, dry_run=False)
    (base / 'preimages').mkdir(); baseline = []
    for item in plan.baseline:
        p = root / item.repository_path
        if item.repository_path not in [tx.RAW, tx.LEDGER, tx.REPORT]:
            p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(b'{"fixture": true}\n')
        saved = base / 'preimages' / p.name; saved.write_bytes(p.read_bytes())
        baseline.append(Baseline(repository_path=item.repository_path, preserved=ref(base, saved),
                                 records=1 if p.suffix == '.jsonl' else None))
    legacy = root / plan.legacy_guard.path
    legacy.write_bytes(b'{"fixture_legacy_stream": true}\n')
    d = plan.model_dump(mode='json')
    d['legacy_guard'] = {'path': plan.legacy_guard.path,
        'sha256': tx.digest(legacy.read_bytes()), 'size_bytes': legacy.stat().st_size}
    d.update(baseline=[b.model_dump(mode='json') for b in baseline], raw_before=1,
             ledger_before=1, raw_after=2, ledger_after=2)
    changed = Preparation.model_validate_json(json.dumps(d))
    monkeypatch.setattr(tx, 'load_plan', lambda base=tx.BASE: changed)
    return root, base, changed


def test_dry_run_prefix_replay(fixture):
    root, base, plan = fixture; before = snap(root)
    assert tx.run(root, base=base)['actual_repository_received_at'] is None
    assert snap(root) == before and not (base / 'execution').exists()
    result = tx.run(root, base=base, apply=True)
    intent = tx.Intent.model_validate_json((base / 'execution/INTENT.json').read_bytes())
    assert intent.record.received_at != plan.provenance.reported_finished_at
    assert intent.record.acquisition_method == 'received_review_package'
    assert intent.record.official_source_url is None
    suffix = (intent.record.model_dump_json() + '\n').encode()
    for name in [tx.RAW, tx.LEDGER]:
        assert (root / name).read_bytes() == before[name] + suffix
    after = snap(root)
    assert tx.run(root, base=base, apply=True) == result
    assert tx.run(root, base=base, verify=True) == result
    assert snap(root) == after
    assert (base / 'execution/preimages' / Path(tx.RAW).name).read_bytes() == before[tx.RAW]


@pytest.mark.parametrize('stage', ['intent', 'original', 'raw', 'reconciled'])
def test_interruption(fixture, stage):
    root, base, _ = fixture
    def stop(here):
        if here == stage: raise RuntimeError('fixture interruption')
    with pytest.raises(RuntimeError): tx.run(root, base=base, apply=True, fault=stop)
    intent = (base / 'execution/INTENT.json').read_bytes()
    out = tx.run(root, base=base, apply=True)
    assert (base / 'execution/INTENT.json').read_bytes() == intent
    assert tx.run(root, base=base, verify=True) == out


@pytest.mark.parametrize('kind', ['source', 'qa', 'approval', 'raw', 'ledger', 'report',
                                  'guard', 'symlink', 'snapshot_parent'])
def test_refusal_before_writes(fixture, kind):
    root, base, plan = fixture
    if kind in {'source', 'qa', 'approval'}:
        a = {'source': plan.template.source, 'qa': plan.source_review,
             'approval': plan.root_source_qa_approval}[kind]
        p = base / a.path; p.write_bytes(p.read_bytes() + b'corrupt')
    elif kind in {'raw', 'ledger', 'report', 'guard'}:
        name = {'raw': tx.RAW, 'ledger': tx.LEDGER, 'report': tx.REPORT,
                'guard': '_CONTROL_PLANE/LOCAL_COVERAGE_LEDGER.json'}[kind]
        p = root / name; p.write_bytes(p.read_bytes() + b' ')
    elif kind == 'symlink':
        p = root / tx.RAW; saved = p.with_name('saved.jsonl'); p.rename(saved); p.symlink_to(saved)
    else:
        p = root / '_SNAPSHOTS'
        if p.exists(): shutil.rmtree(p)
        p.write_bytes(b'not a directory')
    before = snap(root)
    with pytest.raises((ValueError, OSError)): tx.run(root, base=base, apply=True)
    assert snap(root) == before and not (base / 'execution').exists()


def test_wrong_authority(fixture):
    _, _, plan = fixture; d = plan.model_dump(mode='json')
    d['template']['authority_id'] = 'CO-MUNICIPAL-PUEBLO'
    with pytest.raises(ValueError): Preparation.model_validate_json(json.dumps(d))


def test_bad_intent_and_destination(fixture):
    root, base, _ = fixture
    def stop(stage):
        if stage == 'intent': raise RuntimeError('stop')
    with pytest.raises(RuntimeError): tx.run(root, base=base, apply=True, fault=stop)
    p = base / 'execution/INTENT.json'; original = p.read_bytes(); d = json.loads(original)
    d['record']['acquisition_method'] = 'manual_official_download'; p.write_text(json.dumps(d))
    before = snap(root)
    with pytest.raises(ValueError): tx.run(root, base=base, apply=True)
    assert snap(root) == before; p.write_bytes(original)
    intent = tx.Intent.model_validate_json(original); target = root / intent.record.archive_path
    target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(b'foreign original')
    before = snap(root)
    with pytest.raises(ValueError): tx.run(root, base=base, apply=True)
    assert snap(root) == before


def test_report_failure_recovery(fixture, monkeypatch):
    root, base, _ = fixture; original = tx.mi.atomic_write_json
    def failure(*args, **kwargs): raise OSError('fixture report failure')
    monkeypatch.setattr(tx.mi, 'atomic_write_json', failure)
    with pytest.raises(OSError): tx.run(root, base=base, apply=True)
    assert len((root / tx.RAW).read_bytes().splitlines()) == 2
    assert len((root / tx.LEDGER).read_bytes().splitlines()) == 2
    monkeypatch.setattr(tx.mi, 'atomic_write_json', original)
    out = tx.run(root, base=base, apply=True)
    assert tx.run(root, base=base, verify=True) == out


def test_receipt_count_tamper(fixture):
    root, base, _ = fixture; tx.run(root, base=base, apply=True)
    p = base / 'execution/RECEIPT.json'; d = json.loads(p.read_bytes())
    d['raw_records'] = 999; p.write_text(json.dumps(d)); before = snap(root)
    with pytest.raises(ValueError): tx.run(root, base=base, verify=True)
    assert snap(root) == before


def test_missing_execution(fixture):
    root, base, _ = fixture
    with pytest.raises(ValueError, match='no completed execution'):
        tx.run(root, base=base, verify=True)


def test_real_pins(tmp_path):
    raw = (tx.BASE / 'PREPARATION.json').read_bytes(); assert tx.digest(raw) == tx.PLAN_SHA
    plan = tx.load_plan()
    assert (plan.raw_before, plan.ledger_before, plan.raw_after, plan.ledger_after) == (63,64,64,65)
    for path, expected in plan.runtime_pins.items():
        assert tx.digest((tx.RUNTIME_ROOT / path).read_bytes()) == expected
    (tmp_path / 'PREPARATION.json').write_bytes(raw + b' ')
    with pytest.raises(ValueError, match='preparation pin'): tx.load_plan(tmp_path)


def test_atomic_paths(tmp_path):
    p = tmp_path / 'immutable'; tx.atomic_once(p, b'a')
    with pytest.raises(ValueError): tx.atomic_once(p, b'b')
    with pytest.raises(ValueError): tx.atomic_replace(p, b'b', b'c')
    assert p.read_bytes() == b'a'
    for rel in ['../escape', '/absolute', 'dir\\file']:
        with pytest.raises(ValueError): tx.ordinary(tmp_path, rel, missing=True)


def test_duplicate_digest_refused_before_mutation(fixture, monkeypatch):
    root, base, plan = fixture
    # An already-present source under another record ID must not be recaptured as new.
    row = json.loads((root / tx.RAW).read_bytes())
    source = (base / plan.template.source.path).read_bytes()
    (root / row['archive_path']).write_bytes(source)
    row['sha256'] = tx.SOURCE_SHA; row['size_bytes'] = len(source)
    for name in [tx.RAW, tx.LEDGER]:
        (root / name).write_text(json.dumps(row) + '\n')
    revised = []
    for b in plan.baseline:
        if b.repository_path in [tx.RAW, tx.LEDGER]:
            p = base / b.preserved.path; p.write_bytes((root / b.repository_path).read_bytes())
            b = b.model_copy(update={'preserved': ref(base, p)})
        revised.append(b)
    plan = plan.model_copy(update={'baseline': revised})
    monkeypatch.setattr(tx, 'load_plan', lambda base=tx.BASE: plan)
    before = snap(root)
    with pytest.raises(ValueError, match='source already present'):
        tx.run(root, base=base, apply=True)
    assert snap(root) == before and not (base / 'execution').exists()


def test_changed_record_claims_in_valid_intent_refused(fixture):
    root, base, _ = fixture
    def stop(stage):
        if stage == 'intent': raise RuntimeError('stop')
    with pytest.raises(RuntimeError): tx.run(root, base=base, apply=True, fault=stop)
    p = base / 'execution/INTENT.json'; d = json.loads(p.read_bytes())
    d['record']['custody_note'] = 'False stronger acquisition claim.'
    p.write_text(json.dumps(d)); before = snap(root)
    with pytest.raises(ValueError, match='intent record differs'):
        tx.run(root, base=base, apply=True)
    assert snap(root) == before


def test_intent_time_mismatch_refused(fixture):
    root, base, _ = fixture
    def stop(stage):
        if stage == 'intent': raise RuntimeError('stop')
    with pytest.raises(RuntimeError): tx.run(root, base=base, apply=True, fault=stop)
    p = base / 'execution/INTENT.json'; d = json.loads(p.read_bytes())
    d['actual_repository_received_at'] = '2025-01-01T00:00:00Z'
    p.write_text(json.dumps(d)); before = snap(root)
    with pytest.raises(ValueError, match='intent identity differs'):
        tx.run(root, base=base, apply=True)
    assert snap(root) == before


def test_nonordinary_parent_and_missing_file(tmp_path):
    p = tmp_path / 'file'; p.write_text('not a directory')
    for name in ['missing', 'file/child']:
        with pytest.raises(ValueError): tx.ordinary(tmp_path, name)


def test_runtime_pin_refusal(tmp_path, monkeypatch):
    ordinary = tx.ordinary
    fake = tmp_path / 'bad-runtime.py'; fake.write_bytes(b'changed runtime')
    def substituted(root, name, missing=False):
        if root == tx.RUNTIME_ROOT: return fake
        return ordinary(root, name, missing)
    monkeypatch.setattr(tx, 'ordinary', substituted)
    with pytest.raises(ValueError, match='reviewed runtime changed'): tx.load_plan()


def test_cli_actual_readonly_and_refusal(monkeypatch, capsys):
    import runpy
    import sys
    monkeypatch.setattr(sys, 'argv', [str(tx.BASE / 'transaction.py'), '--dry-run'])
    runpy.run_path(str(tx.BASE / 'transaction.py'), run_name='__main__')
    assert json.loads(capsys.readouterr().out)['canonical_mutations'] == 0
    monkeypatch.setattr(sys, 'argv', [str(tx.BASE / 'transaction.py'), '--verify'])
    with pytest.raises(SystemExit) as caught:
        runpy.run_path(str(tx.BASE / 'transaction.py'), run_name='__main__')
    assert caught.value.code == 1
    assert 'no completed execution' in capsys.readouterr().err


def test_unrecognized_report_after_raw_is_refused(fixture):
    root, base, _ = fixture
    def stop(stage):
        if stage == 'raw': raise RuntimeError('stop')
    with pytest.raises(RuntimeError): tx.run(root, base=base, apply=True, fault=stop)
    p = root / tx.REPORT; d = json.loads(p.read_bytes()); d['records'] = 999
    p.write_text(json.dumps(d)); before = snap(root)
    with pytest.raises(ValueError, match='unrecognized changed report'):
        tx.run(root, base=base, apply=True)
    assert snap(root) == before


def test_changed_full_legacy_guard_refuses(fixture):
    root, base, plan = fixture
    (root / plan.legacy_guard.path).write_bytes(b'new unrelated legacy state')
    before = snap(root)
    with pytest.raises(ValueError, match='legacy comparison baseline changed'):
        tx.run(root, base=base, apply=True)
    assert snap(root) == before and not (base / 'execution').exists()


def test_nonoverlap_lock_refuses(fixture):
    import fcntl
    root, base, _ = fixture
    execution = base / 'execution'; execution.mkdir()
    with (execution / 'LOCK').open('a+b') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        before = snap(root)
        with pytest.raises(BlockingIOError): tx.run(root, base=base, apply=True)
        assert snap(root) == before and not (execution / 'INTENT.json').exists()
