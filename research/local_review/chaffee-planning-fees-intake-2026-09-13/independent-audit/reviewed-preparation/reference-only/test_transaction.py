"""Temporary-fixture tests only; no canonical apply or network."""
import io
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
import pymupdf
import pytest
import transaction as tx
from models import Asset, Baseline, Preparation


def snapshot(root):
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
    shutil.copytree(tx.BASE / 'sources', base / 'sources')
    plan = tx.load_plan()
    doc = pymupdf.open(); doc.new_page().insert_text((72, 72), 'Synthetic historical source.')
    raw = doc.tobytes(); doc.close()
    old_path = '_RAW_ARCHIVE/manual_intake/08_County_Authorities/fixture-old/original.pdf'
    path = root / old_path; path.parent.mkdir(parents=True); path.write_bytes(raw)
    old = tx.mi.ManualSourceIntakeRecord(
        intake_id='MSI-fixture-old', record_id='fixture-old', layer_id='08_County_Authorities',
        official_source_name='Synthetic fixture', official_source_url=None,
        acquisition_method='received_review_package', received_from='fixture',
        reviewer_name='fixture', reviewer_email=None, custody_note='Synthetic fixture only.',
        original_filename='original.pdf', archive_path=old_path, sha256=tx.digest(raw),
        size_bytes=len(raw), source_format='pdf',
        received_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        status='archived_pending_pipeline', blocked_queue_match=False, boundary='fixture only')
    for name in [tx.RAW, tx.LEDGER]:
        p = root / name; p.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(old.model_dump(mode='json'), separators=(', ', ': ')) + '\n'
        p.write_bytes(line.encode())
    tx.mi.reconcile_manual_source_intake(root, dry_run=False)
    (base / 'preimages').mkdir(); baseline = []
    for item in plan.baseline:
        p = root / item.repository_path
        if item.repository_path not in [tx.RAW, tx.LEDGER, tx.REPORT]:
            p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(b'{"fixture":true}\n')
        saved = base / 'preimages' / p.name; saved.write_bytes(p.read_bytes())
        baseline.append(Baseline(repository_path=item.repository_path, preserved=ref(base, saved),
                                 records=1 if p.suffix == '.jsonl' else None))
    legacy = root / plan.legacy_guard.path; legacy.write_bytes(b'{"fixture":true}\n')
    data = plan.model_dump(mode='json')
    data.update(baseline=[b.model_dump(mode='json') for b in baseline], raw_before=1,
                ledger_before=1, raw_after=3, ledger_after=3)
    data['legacy_guard'] = {'path': plan.legacy_guard.path,
                            'sha256': tx.digest(legacy.read_bytes()),
                            'size_bytes': legacy.stat().st_size}
    changed = Preparation.model_validate_json(json.dumps(data))
    monkeypatch.setattr(tx, 'load_plan', lambda base=tx.BASE: changed)
    return root, base, changed


def interrupt(root, base, stage):
    def stop(here):
        if here == stage:
            raise RuntimeError('simulated interruption')
    with pytest.raises(RuntimeError):
        tx.run(root, base=base, apply=True, fault=stop)


def test_dry_run_prefixes_and_idempotence(fixture, monkeypatch):
    root, base, plan = fixture; before = snapshot(root)
    # No generic reconciliation, including its mutating mode, is used by the transaction.
    monkeypatch.setattr(tx.mi, 'reconcile_manual_source_intake',
                        lambda *a, **k: pytest.fail('generic reconciliation called'))
    result = tx.run(root, base=base)
    assert result['actual_repository_received_at'] is None
    assert snapshot(root) == before and not (base / 'execution').exists()
    done = tx.run(root, base=base, apply=True)
    intent_raw = (base / 'execution/INTENT.json').read_bytes()
    intent = tx.Intent.model_validate_json(intent_raw)
    assert len(intent.records) == 2
    assert len({r.received_at for r in intent.records}) == 1
    for record, template, provenance in zip(intent.records, plan.templates, plan.provenance):
        assert record.received_at != provenance.http_completed_at
        assert record.original_filename == Path(template.source.path).name
        assert record.acquisition_method == 'manual_official_download'
        assert record.official_source_url == provenance.requested_url
        expected = (base / template.source.path).read_bytes()
        assert (root / record.archive_path).read_bytes() == expected
    suffix = b''.join((r.model_dump_json() + '\n').encode() for r in intent.records)
    for name in [tx.RAW, tx.LEDGER]:
        assert (root / name).read_bytes() == before[name] + suffix
    after = snapshot(root); execution = snapshot(base / 'execution')
    assert tx.run(root, base=base, apply=True) == done
    assert tx.run(root, base=base, verify=True) == done
    assert snapshot(root) == after
    assert snapshot(base / 'execution') == execution
    assert (base / 'execution/INTENT.json').read_bytes() == intent_raw


@pytest.mark.parametrize('stage', ['intent', 'original_1', 'original_2',
                                  'raw', 'ledger', 'reconciled'])
def test_interruption_recovers_same_intent(fixture, stage):
    root, base, _ = fixture; interrupt(root, base, stage)
    raw = (base / 'execution/INTENT.json').read_bytes()
    result = tx.run(root, base=base, apply=True)
    assert (base / 'execution/INTENT.json').read_bytes() == raw
    assert tx.run(root, base=base, verify=True) == result


@pytest.mark.parametrize('stage', ['original_1', 'raw', 'ledger', 'reconciled'])
def test_foreign_raw_never_promoted(fixture, stage):
    root, base, _ = fixture
    before_ledger = (root / tx.LEDGER).read_bytes()
    before_report = (root / tx.REPORT).read_bytes()
    observed = {}
    def arrival(here):
        if here == stage:
            row = json.loads(next(io.BytesIO((root / tx.RAW).read_bytes())))
            row.update(intake_id='MSI-foreign', record_id='foreign')
            observed['raw'] = (root / tx.RAW).read_bytes() + (json.dumps(row) + '\n').encode()
            (root / tx.RAW).write_bytes(observed['raw'])
            observed['ledger'] = (root / tx.LEDGER).read_bytes()
            observed['report'] = (root / tx.REPORT).read_bytes()
    with pytest.raises(ValueError, match='unrecognized canonical prefix'):
        tx.run(root, base=base, apply=True, fault=arrival)
    assert (root / tx.RAW).read_bytes() == observed['raw']
    assert (root / tx.LEDGER).read_bytes() == observed['ledger']
    assert (root / tx.REPORT).read_bytes() == observed['report']
    assert b'MSI-foreign' not in observed['ledger'] and b'MSI-foreign' not in observed['report']
    assert not (base / 'execution/RECEIPT.json').exists()
    if stage in {'original_1', 'raw'}:
        assert observed['ledger'] == before_ledger and observed['report'] == before_report


@pytest.mark.parametrize('kind', ['source', 'parent', 'result', 'retrieval_plan', 'raw',
                                  'ledger', 'report', 'policy', 'legacy', 'source_symlink',
                                  'snapshot_parent', 'runtime_source_missing'])
def test_prewrite_refusal(fixture, kind):
    root, base, plan = fixture
    if kind in {'source', 'parent', 'result', 'retrieval_plan', 'source_symlink'}:
        a = {'source': plan.templates[1].source, 'source_symlink': plan.templates[0].source,
             'parent': plan.provenance[0].parent, 'result': plan.provenance[1].result,
             'retrieval_plan': plan.retrieval_plan}[kind]
        p = base / a.path
        if kind == 'source_symlink':
            moved = p.with_suffix('.saved'); p.rename(moved); p.symlink_to(moved)
        else:
            p.write_bytes(p.read_bytes() + b'corruption')
    elif kind == 'snapshot_parent':
        p = root / '_SNAPSHOTS'
        if p.exists(): shutil.rmtree(p)
        p.write_bytes(b'not a directory')
    elif kind == 'runtime_source_missing':
        row = json.loads(next(io.BytesIO((root / tx.RAW).read_bytes())))
        (root / row['archive_path']).unlink()
    else:
        name = {'raw': tx.RAW, 'ledger': tx.LEDGER, 'report': tx.REPORT,
                'policy': '_CONTROL_PLANE/MANUAL_SOURCE_INTAKE_POLICY.json',
                'legacy': plan.legacy_guard.path}[kind]
        p = root / name; p.write_bytes(p.read_bytes() + b' ')
    before = snapshot(root)
    with pytest.raises((ValueError, OSError)):
        tx.run(root, base=base, apply=True)
    assert snapshot(root) == before and not (base / 'execution').exists()


@pytest.mark.parametrize('field,value', [('official_source_url', 'https://gunnisoncounty.org/'),
                                       ('acquisition_method', 'received_review_package'),
                                       ('layer_id', '10_Municipal_Authorities'),
                                       ('original_filename', 'invented.pdf')])
def test_template_claims_refused(fixture, field, value):
    _, _, plan = fixture; data = plan.model_dump(mode='json')
    data['templates'][0][field] = value
    with pytest.raises(ValueError): Preparation.model_validate_json(json.dumps(data))


@pytest.mark.parametrize('kind', ['report', 'record', 'timestamp', 'order', 'plan_pin'])
def test_intent_tampering_refused(fixture, kind):
    root, base, _ = fixture; interrupt(root, base, 'intent')
    path = base / 'execution/INTENT.json'; data = json.loads(path.read_bytes())
    if kind == 'report': data['expected_report']['records'] += 100
    elif kind == 'record': data['records'][1]['custody_note'] = 'Changed custody claim.'
    elif kind == 'timestamp': data['actual_repository_received_at'] = '2025-01-01T00:00:00Z'
    elif kind == 'order': data['records'] = list(reversed(data['records']))
    else: data['preparation_sha256'] = '0' * 64
    path.write_text(json.dumps(data)); before = snapshot(root)
    with pytest.raises(ValueError): tx.run(root, base=base, apply=True)
    assert snapshot(root) == before


@pytest.mark.parametrize('mode', ['ledger_ahead', 'report_ahead', 'partial_suffix',
                                  'second_original_only', 'wrong_destination'])
def test_unrecognized_partial_states(fixture, mode):
    root, base, plan = fixture; interrupt(root, base, 'intent')
    intent = tx.Intent.model_validate_json((base / 'execution/INTENT.json').read_bytes())
    suffix = b''.join((r.model_dump_json() + '\n').encode() for r in intent.records)
    if mode == 'ledger_ahead':
        (root / tx.LEDGER).write_bytes((root / tx.LEDGER).read_bytes() + suffix)
    elif mode == 'report_ahead':
        (root / tx.REPORT).write_bytes(tx.report_bytes(intent))
    elif mode == 'partial_suffix':
        (root / tx.RAW).write_bytes((root / tx.RAW).read_bytes() + suffix[:20])
    else:
        i = 1 if mode == 'second_original_only' else 0
        p = root / intent.records[i].archive_path; p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes((base / plan.templates[i].source.path).read_bytes()
                      if mode == 'second_original_only' else b'foreign')
    before = snapshot(root)
    with pytest.raises(ValueError): tx.run(root, base=base, apply=True)
    assert snapshot(root) == before


@pytest.mark.parametrize('name', [tx.RAW, tx.LEDGER, tx.REPORT])
def test_write_failure_replay(fixture, monkeypatch, name):
    root, base, _ = fixture; original = tx.atomic_replace
    def fail(path, before, after):
        if path == root / name: raise OSError('synthetic write failure')
        original(path, before, after)
    monkeypatch.setattr(tx, 'atomic_replace', fail)
    with pytest.raises(OSError): tx.run(root, base=base, apply=True)
    intent = (base / 'execution/INTENT.json').read_bytes()
    monkeypatch.setattr(tx, 'atomic_replace', original)
    tx.run(root, base=base, apply=True)
    assert (base / 'execution/INTENT.json').read_bytes() == intent
    assert tx.run(root, base=base, verify=True)['raw_records'] == 3


def test_input_changes_after_first_original(fixture):
    root, base, plan = fixture
    def change(stage):
        if stage == 'original_1':
            p = base / plan.templates[1].source.path; p.write_bytes(p.read_bytes()[:-1])
    before_raw = (root / tx.RAW).read_bytes(); before_ledger = (root / tx.LEDGER).read_bytes()
    with pytest.raises(ValueError, match='input changed'):
        tx.run(root, base=base, apply=True, fault=change)
    assert (root / tx.RAW).read_bytes() == before_raw
    assert (root / tx.LEDGER).read_bytes() == before_ledger
    intent = tx.Intent.model_validate_json((base / 'execution/INTENT.json').read_bytes())
    assert (root / intent.records[0].archive_path).exists()
    assert not (root / intent.records[1].archive_path).exists()


def test_untracked_duplicate_body_refused(fixture):
    root, base, plan = fixture
    p = root / '_RAW_ARCHIVE/untracked-copy.pdf'
    p.write_bytes((base / plan.templates[0].source.path).read_bytes())
    before = snapshot(root)
    with pytest.raises(ValueError, match='elsewhere in raw archive'):
        tx.run(root, base=base, apply=True)
    assert snapshot(root) == before and not (base / 'execution').exists()


@pytest.mark.parametrize('kind', ['unknown_file', 'unknown_dir', 'symlink', 'lock'])
def test_execution_refusal(fixture, kind):
    root, base, _ = fixture; execution = base / 'execution'; execution.mkdir()
    if kind == 'unknown_file': (execution / 'unrelated').write_bytes(b'x')
    elif kind == 'unknown_dir': (execution / 'unrelated').mkdir()
    elif kind == 'symlink': (execution / 'INTENT.json').symlink_to(base / 'absent')
    else:
        import fcntl
        with (execution / 'LOCK').open('a+b') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            before = snapshot(root)
            with pytest.raises(BlockingIOError): tx.run(root, base=base, apply=True)
            assert snapshot(root) == before
        return
    before = snapshot(root)
    with pytest.raises(ValueError): tx.run(root, base=base, apply=True)
    assert snapshot(root) == before


def test_missing_execution_and_mutual_modes(fixture):
    root, base, _ = fixture
    with pytest.raises(ValueError, match='no completed execution'):
        tx.run(root, base=base, verify=True)
    with pytest.raises(ValueError, match='select one'):
        tx.run(root, base=base, apply=True, verify=True)


def test_receipt_snapshot_tampering(fixture):
    root, base, _ = fixture; tx.run(root, base=base, apply=True)
    p = base / 'execution/RECEIPT.json'; original = p.read_bytes(); data = json.loads(original)
    data['source_id_to_sha256'][next(iter(tx.SELECTED))] = '0' * 64
    p.write_text(json.dumps(data)); before = snapshot(root)
    with pytest.raises(ValueError, match='receipt/state'): tx.run(root, base=base, verify=True)
    assert snapshot(root) == before; p.write_bytes(original)
    pre = base / 'execution/preimages' / Path(tx.RAW).name; pre.write_bytes(b'altered preimage')
    with pytest.raises(ValueError, match='preimage differs'): tx.run(root, base=base, verify=True)


def test_checked_buffer_plan_is_parsed_once(tmp_path, monkeypatch):
    raw = (tx.BASE / 'PREPARATION.json').read_bytes()
    (tmp_path / 'PREPARATION.json').write_bytes(raw)
    original = Path.read_bytes; calls = []
    def read(path):
        if path == tmp_path / 'PREPARATION.json':
            calls.append(path)
            if len(calls) > 1:
                data = json.loads(raw); data['templates'][0]['official_source_name'] = 'changed'
                return json.dumps(data).encode()
        return original(path)
    monkeypatch.setattr(Path, 'read_bytes', read)
    plan = tx.load_plan(tmp_path)
    assert len(calls) == 1 and plan.templates[0].official_source_name != 'changed'


def test_real_plan_pins_and_bad_pin(tmp_path):
    plan = tx.load_plan()
    counts = (plan.raw_before, plan.ledger_before, plan.raw_after, plan.ledger_after)
    assert counts == (67, 68, 69, 70)
    assert list(tx.SELECTED) == [s.record_id for s in plan.templates]
    (tmp_path / 'PREPARATION.json').write_bytes((tx.BASE / 'PREPARATION.json').read_bytes() + b' ')
    with pytest.raises(ValueError, match='preparation pin'): tx.load_plan(tmp_path)


def test_runtime_pin_refusal(monkeypatch, tmp_path):
    original = tx.ordinary; p = tmp_path / 'changed.py'; p.write_bytes(b'changed')
    def changed(root, name, missing=False):
        if root == tx.RUNTIME_ROOT: return p
        return original(root, name, missing)
    monkeypatch.setattr(tx, 'ordinary', changed)
    with pytest.raises(ValueError, match='reviewed runtime'): tx.load_plan()


def test_atomic_paths_and_immutable_conflict(tmp_path):
    p = tmp_path / 'original'; tx.atomic_once(p, b'a'); tx.atomic_once(p, b'a')
    with pytest.raises(ValueError): tx.atomic_once(p, b'b')
    with pytest.raises(ValueError): tx.atomic_replace(p, b'b', b'c')
    assert p.read_bytes() == b'a'
    for path in ['../escape', '/absolute', 'a\\b', 'a//b']:
        with pytest.raises(ValueError): tx.ordinary(tmp_path, path, missing=True)
    (tmp_path / 'directory').mkdir()
    with pytest.raises(ValueError): tx.ordinary(tmp_path, 'directory')


def test_prefix_changes_at_second_compare(tmp_path, monkeypatch):
    p = tmp_path / 'file'; p.write_bytes(b'old'); original = Path.read_bytes; calls = []
    def read(path):
        if path == p:
            calls.append(1)
            if len(calls) == 2:
                p.write_bytes(b'foreign')
        return original(path)
    monkeypatch.setattr(Path, 'read_bytes', read)
    with pytest.raises(ValueError, match='during replacement'): tx.atomic_replace(p, b'old', b'new')
    assert p.read_bytes() == b'foreign'


def test_cli_live_dry_run_and_verify_refusal(monkeypatch, capsys):
    import runpy
    import sys
    monkeypatch.setattr(sys, 'argv', [str(tx.BASE / 'transaction.py'), '--dry-run',
                                    '--root', str(tx.RUNTIME_ROOT)])
    runpy.run_path(str(tx.BASE / 'transaction.py'), run_name='__main__')
    assert json.loads(capsys.readouterr().out)['canonical_mutations'] == 0
    monkeypatch.setattr(sys, 'argv', [str(tx.BASE / 'transaction.py'), '--verify',
                                    '--root', str(tx.RUNTIME_ROOT)])
    with pytest.raises(SystemExit) as caught:
        runpy.run_path(str(tx.BASE / 'transaction.py'), run_name='__main__')
    assert caught.value.code == 1
    assert 'no completed execution' in capsys.readouterr().err


@pytest.mark.parametrize('kind', ['id', 'digest', 'provenance_order', 'source_binding', 'count'])
def test_preparation_join_constraints(fixture, kind):
    _, _, plan = fixture; data = plan.model_dump(mode='json')
    if kind == 'id': data['templates'][1]['record_id'] = data['templates'][0]['record_id']
    elif kind == 'digest':
        data['templates'][1]['source']['sha256'] = data['templates'][0]['source']['sha256']
    elif kind == 'provenance_order': data['provenance'] = list(reversed(data['provenance']))
    elif kind == 'source_binding': data['provenance'][0]['source']['size_bytes'] += 1
    else: data['raw_after'] += 1
    with pytest.raises(ValueError): Preparation.model_validate_json(json.dumps(data))


def test_asset_path_validation():
    for path in ['/outside', '../outside', 'a\\b', 'a//b']:
        with pytest.raises(ValueError): Asset(path=path, sha256='0' * 64, size_bytes=0)


def test_untracked_raw_symlink_refusal(fixture, tmp_path):
    root, base, _ = fixture
    (root / '_RAW_ARCHIVE/link').symlink_to(tmp_path / 'absent')
    before = snapshot(root)
    with pytest.raises(ValueError, match='linked raw archive'): tx.run(root, base=base, apply=True)
    assert snapshot(root) == before


def test_snapshot_bytes_verified(fixture):
    root, base, _ = fixture; tx.run(root, base=base, apply=True)
    found = list((root / '_SNAPSHOTS').rglob(Path(tx.RAW).name))
    assert len(found) == 1; found[0].write_bytes(b'altered snapshot')
    with pytest.raises(ValueError, match='repository snapshot differs'):
        tx.run(root, base=base, verify=True)


def test_missing_new_original_with_metadata_refused(fixture):
    root, base, _ = fixture; tx.run(root, base=base, apply=True)
    intent = tx.Intent.model_validate_json((base / 'execution/INTENT.json').read_bytes())
    (root / intent.records[1].archive_path).unlink()
    before = snapshot(root)
    with pytest.raises(ValueError, match='metadata ahead'): tx.run(root, base=base, apply=True)
    assert snapshot(root) == before


@pytest.mark.parametrize('field,value', [
    ('authority_id', 'CO-MUNICIPAL-SALIDA'),
    ('http_status', 302), ('tls_verified', False), ('redirects_followed', 1),
    ('actual_repository_received_at', '2026-09-13T16:09:37Z'),
    ('source_content_reviewed_in_this_intake', True),
])
def test_no_custody_role_or_time_promotion(fixture, field, value):
    _, _, plan = fixture
    data = plan.model_dump(mode='json')
    data['provenance'][0][field] = value
    with pytest.raises(ValueError):
        Preparation.model_validate_json(json.dumps(data))


def test_exact_two_pdf_actions_exclude_fee_redirect(fixture):
    _, base, plan = fixture
    assert [p.action_id for p in plan.provenance] == ['A001', 'A002']
    assert sum(p.physical_pages for p in plan.provenance) == 21
    body = base / 'inputs/retrieval/events/A003/response.body'
    assert body.read_bytes().startswith(b'<') and not body.read_bytes().startswith(b'%PDF-')
    assert body not in [base / t.source.path for t in plan.templates]
    assert sum(t.source.size_bytes for t in plan.templates) == 1675847


def test_swapped_source_url_refused(fixture):
    _, _, plan = fixture
    data = plan.model_dump(mode='json')
    data['templates'][0]['official_source_url'] = data['templates'][1]['official_source_url']
    with pytest.raises(ValueError, match='source-specific official URL'):
        Preparation.model_validate_json(json.dumps(data))


def test_clock_order_refused(fixture):
    _, _, plan = fixture
    data = plan.model_dump(mode='json')
    data['provenance'][0]['http_completed_at'] = '2020-01-01T00:00:00Z'
    with pytest.raises(ValueError, match='chronology'):
        Preparation.model_validate_json(json.dumps(data))


def test_maintained_strict_host_gate_before_intent(fixture, monkeypatch):
    root, base, _ = fixture
    before = snapshot(root)
    def deny(url):
        raise ValueError('deliberate maintained URL rejection')
    monkeypatch.setattr(tx.mi, 'require_official_source_url', deny)
    with pytest.raises(ValueError, match='maintained URL rejection'):
        tx.run(root, base=base, apply=True)
    assert snapshot(root) == before and not (base / 'execution').exists()


def test_captured_source_aba_preserves_checked_bytes(fixture, monkeypatch):
    root, base, plan = fixture
    original = tx.atomic_once
    target = base / plan.templates[0].source.path
    checked = target.read_bytes()
    def change_then_write(path, raw):
        if path.suffix == '.pdf' and '_RAW_ARCHIVE' in str(path):
            target.write_bytes(b'foreign temporary source')
            try:
                original(path, raw)
            finally:
                target.write_bytes(checked)
        else:
            original(path, raw)
    monkeypatch.setattr(tx, 'atomic_once', change_then_write)
    done = tx.run(root, base=base, apply=True)
    assert (root / done['canonical_archive_paths'][0]).read_bytes() == checked
    assert tx.run(root, base=base, verify=True) == done


def test_coherently_backdated_intent_refused(fixture):
    root, base, plan = fixture
    interrupt(root, base, 'intent')
    path = base / 'execution/INTENT.json'
    earlier = datetime(2025, 1, 1, tzinfo=timezone.utc)
    records = [tx.record_for(t, earlier) for t in plan.templates]
    originals = {b.repository_path: (base / b.preserved.path).read_bytes()
                 for b in plan.baseline}
    changed = tx.Intent(
        preparation_sha256=tx.PLAN_SHA, actual_repository_received_at=earlier,
        records=records,
        expected_report=tx.expected_report(plan, originals, records, earlier),
    )
    path.write_text(changed.model_dump_json())
    before = snapshot(root)
    with pytest.raises(ValueError, match='receipt precedes observed acquisition'):
        tx.run(root, base=base, apply=True)
    assert snapshot(root) == before
