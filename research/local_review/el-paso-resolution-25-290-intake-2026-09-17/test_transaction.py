"""Offline exact-prefix, custody and interruption probes; no source network."""
import io
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pymupdf
import pytest
import transaction as tx
from models import Asset, Baseline, Preparation


def snapshot(root: Path) -> dict[str, bytes]:
    """Capture ordinary fixture files without following links."""
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*')
            if p.is_file() and not p.is_symlink()}


def ref(base: Path, path: Path) -> Asset:
    """Bind one temporary fixture file."""
    raw = path.read_bytes()
    return Asset(path=path.relative_to(base).as_posix(), sha256=tx.digest(raw), size_bytes=len(raw))


@pytest.fixture
def fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path, Any]:
    """Build an independent corpus with exact selected source evidence and synthetic history."""
    root = tmp_path / 'corpus'; root.mkdir()
    base = tmp_path / 'packet'; base.mkdir()
    shutil.copytree(tx.BASE / 'inputs', base / 'inputs')
    plan = tx.load_plan()
    with pymupdf.open() as doc:
        doc.new_page().insert_text((72, 72), 'Synthetic prior original.')
        raw = doc.tobytes()
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
        p.write_text(json.dumps(old.model_dump(mode='json'), separators=(', ', ': ')) + '\n')
    tx.mi.reconcile_manual_source_intake(root, dry_run=False)
    (base / 'preimages').mkdir(); baseline = []
    for item in plan.baseline:
        p = root / item.repository_path
        saved = base / 'preimages' / p.name; saved.write_bytes(p.read_bytes())
        baseline.append(Baseline(repository_path=item.repository_path, preserved=ref(base, saved),
                                 records=1 if p.suffix == '.jsonl' else None))
    legacy = root / plan.legacy_guard.path; legacy.write_bytes(b'{"fixture":true}\n')
    parent = root / plan.parent_packet_manifest.path
    parent.parent.mkdir(parents=True); parent.write_bytes(
        (tx.RUNTIME_ROOT / plan.parent_packet_manifest.path).read_bytes())
    data = plan.model_dump(mode='json')
    data.update(baseline=[b.model_dump(mode='json') for b in baseline], raw_before=1,
                ledger_before=1, raw_after=2, ledger_after=2)
    data['legacy_guard'] = ref(root, legacy).model_dump()
    changed = Preparation.model_validate_json(json.dumps(data))
    monkeypatch.setattr(tx, 'load_plan', lambda base=tx.BASE: changed)
    return root, base, changed


def test_exact_prefix_timestamp_and_idempotence(fixture: Any, monkeypatch: Any) -> None:
    """Actual intake uses a new clock; replay changes no bytes and never uses generic append."""
    root, base, plan = fixture
    before = snapshot(root)
    monkeypatch.setattr(tx.mi, 'reconcile_manual_source_intake',
                        lambda *a, **k: pytest.fail('generic reconciliation called'))
    assert tx.run(root, base=base)['actual_repository_received_at'] is None
    assert snapshot(root) == before and not (base / 'execution').exists()
    done = tx.run(root, base=base, apply=True)
    intent = tx.Intent.model_validate_json((base / 'execution/INTENT.json').read_bytes())
    record = intent.records[0]
    assert record.received_at > plan.provenance[0].recorded_http_completed_at
    assert record.original_filename == 'original.pdf'
    assert record.acquisition_method == 'manual_official_download'
    assert record.official_source_url == plan.templates[0].official_source_url
    assert (root / record.archive_path).read_bytes() == (base / 'inputs/original.pdf').read_bytes()
    suffix = (record.model_dump_json() + '\n').encode()
    for name in [tx.RAW, tx.LEDGER]:
        assert (root / name).read_bytes() == before[name] + suffix
    after = snapshot(root)
    assert tx.run(root, base=base, apply=True) == done
    assert tx.run(root, base=base, verify=True) == done
    assert snapshot(root) == after


@pytest.mark.parametrize('stage', ['intent', 'original_1', 'raw', 'ledger', 'reconciled'])
def test_interruption_recovery(fixture: Any, stage: str) -> None:
    """Every write boundary resumes the exact original timestamp and record."""
    root, base, _ = fixture
    def fault(current: str) -> None:
        if current == stage:
            raise RuntimeError('interrupted')
    with pytest.raises(RuntimeError):
        tx.run(root, base=base, apply=True, fault=fault)
    old_intent = (base / 'execution/INTENT.json').read_bytes()
    result = tx.run(root, base=base, apply=True)
    assert (base / 'execution/INTENT.json').read_bytes() == old_intent
    assert tx.run(root, base=base, verify=True) == result


@pytest.mark.parametrize('stage', ['original_1', 'raw', 'ledger', 'reconciled'])
def test_foreign_arrival_never_reconciled(fixture: Any, stage: str) -> None:
    """An unrelated suffix is refused without publishing it to the ledger or report."""
    root, base, _ = fixture; observed = {}
    def fault(current: str) -> None:
        if current == stage:
            raw = (root / tx.RAW).read_bytes()
            row = json.loads(next(io.BytesIO(raw)))
            row.update(intake_id='MSI-foreign', record_id='foreign')
            (root / tx.RAW).write_bytes(raw + (json.dumps(row) + '\n').encode())
            observed.update(snapshot(root))
    with pytest.raises(ValueError, match='unrecognized canonical prefix'):
        tx.run(root, base=base, apply=True, fault=fault)
    for name in [tx.RAW, tx.LEDGER, tx.REPORT]:
        assert (root / name).read_bytes() == observed[name]
    assert b'MSI-foreign' not in observed[tx.LEDGER]
    assert b'MSI-foreign' not in observed[tx.REPORT]


@pytest.mark.parametrize('name', ['inputs/original.pdf', 'inputs/curl-event-04.json',
                                  'inputs/referring-homepage.html',
                                  'preimages/' + Path(tx.RAW).name])
def test_changed_pinned_input_refused_before_mutation(fixture: Any, name: str) -> None:
    """Changed source, acquisition, referral or historical bytes prevent all writes."""
    root, base, _ = fixture; before = snapshot(root)
    with (base / name).open('ab') as handle:
        handle.write(b'changed')
    with pytest.raises(ValueError, match='input changed'):
        tx.run(root, base=base, apply=True)
    assert snapshot(root) == before and not (base / 'execution').exists()


def test_bad_intent_report_refused(fixture: Any) -> None:
    """A changed report projection cannot be blessed on resume."""
    root, base, _ = fixture
    def fault(stage: str) -> None:
        if stage == 'intent':
            raise RuntimeError('interrupted')
    with pytest.raises(RuntimeError):
        tx.run(root, base=base, apply=True, fault=fault)
    path = base / 'execution/INTENT.json'
    data = json.loads(path.read_bytes()); data['expected_report']['records'] += 1
    path.write_text(json.dumps(data)); before = snapshot(root)
    with pytest.raises(ValueError, match='intent report differs'):
        tx.run(root, base=base, apply=True)
    assert snapshot(root) == before


def test_symlink_source_refused(fixture: Any) -> None:
    """An alias to the same exact bytes is still refused."""
    root, base, _ = fixture; p = base / 'inputs/original.pdf'
    p.rename(p.with_name('other.pdf')); p.symlink_to(p.with_name('other.pdf'))
    before = snapshot(root)
    with pytest.raises(ValueError, match='symlink'):
        tx.run(root, base=base, apply=True)
    assert snapshot(root) == before
