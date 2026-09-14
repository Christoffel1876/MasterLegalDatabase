"""Offline regressions using all thirteen real approved templates and received source bytes."""
from __future__ import annotations

import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

import replay

tx = replay.transaction_module()
spec = importlib.util.spec_from_file_location(
    'frozen_transaction_tests', replay.TRANSACTION / 'test_transaction.py'
)
old_tests = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = old_tests
spec.loader.exec_module(old_tests)


@pytest.fixture
def actual_templates(tmp_path):
    """Reuse a synthetic old baseline but all real source/owner/URL/hash/template values."""
    fixture, root, state = old_tests.fixture.__wrapped__(tmp_path)
    approved = tx.load_plan(replay.ROOT)
    plan = tx.Plan(approved.preparation_sha256, approved.source_provenance_sha256,
                   approved.sources, approved.templates, approved.originals_root,
                   fixture.before, fixture.guards)
    assert len(plan.templates) == 13
    return plan, root, state


def stop_after_raw(name):
    """Simulate only process interruption at the actual observed transaction boundary."""
    if name == 'raw_manifest':
        raise KeyboardInterrupt('fixture stop after raw append')


def interrupted(fixture):
    """Create after/before/before using real templates in the isolated fixture root."""
    plan, root, state = fixture
    with pytest.raises(KeyboardInterrupt):
        tx.execute(plan, root, state, apply=True, checkpoint=stop_after_raw)
    intent = tx.Intent.model_validate_json((state / 'INTENT.json').read_bytes())
    assert len(tx.rows((root / tx.RAW).read_bytes())) == 59
    assert (root / tx.LEDGER).read_bytes() == plan.before[tx.LEDGER]
    assert (root / tx.REPORT).read_bytes() == plan.before[tx.REPORT]
    return plan, root, state, intent


def test_actual_unauthorized_host_fails_before_any_write(actual_templates, monkeypatch):
    """The exact previously missed asset host must fail before state, snapshots or originals."""
    import geode.schemas.validators as validators

    plan, root, state = actual_templates
    intent, _, _ = tx._derive(plan, root, datetime.now(timezone.utc))
    before = old_tests.membership(root)
    monkeypatch.setattr(validators, 'AUTHORIZED_SOURCE_HOSTS',
                        validators.AUTHORIZED_SOURCE_HOSTS - {'epc-assets.elpasoco.com'})
    with pytest.raises(ValueError, match='unauthorized source host: epc-assets.elpasoco.com'):
        replay.validated_replay(tx, plan, root, state, intent, mode='apply')
    assert old_tests.membership(root) == before and not state.exists()


def test_authorized_exact_interrupted_replay_preserves_time_originals_and_prefixes(actual_templates):
    """Finish from the actual order without another raw append, source rewrite or receipt time."""
    plan, root, state, intent = interrupted(actual_templates)
    raw_before = (root / tx.RAW).read_bytes()
    intent_before = (state / 'INTENT.json').read_bytes()
    sources_before = {r.archive_path: (root / r.archive_path).read_bytes() for r in intent.records}
    assert replay.validated_replay(tx, plan, root, state, intent, mode='dry-run')['sources'] == 13
    result = replay.validated_replay(tx, plan, root, state, intent, mode='apply')
    assert result['status'] == 'verified_complete'
    assert (root / tx.RAW).read_bytes() == raw_before
    assert (state / 'INTENT.json').read_bytes() == intent_before
    assert all((root / p).read_bytes() == b for p, b in sources_before.items())
    suffix = (state / 'records.jsonl').read_bytes()
    assert (root / tx.LEDGER).read_bytes() == plan.before[tx.LEDGER] + suffix
    receipt = tx.Receipt.model_validate_json((state / 'RECEIPT.json').read_bytes())
    assert receipt.actual_repository_received_at == intent.actual_repository_received_at
    before = old_tests.membership(root), old_tests.membership(state)
    replay.validated_replay(tx, plan, root, state, intent, mode='apply')
    assert before == (old_tests.membership(root), old_tests.membership(state))


def test_corrupt_promoted_source_stops_before_ledger_write(actual_templates):
    """A policy fix cannot bless unexpected bytes already present at a destination."""
    plan, root, state, intent = interrupted(actual_templates)
    (root / intent.records[0].archive_path).write_bytes(b'corrupt fixture original')
    before = old_tests.membership(root), old_tests.membership(state)
    with pytest.raises(ValueError, match='Hash/size mismatch'):
        replay.validated_replay(tx, plan, root, state, intent, mode='apply')
    assert before == (old_tests.membership(root), old_tests.membership(state))


def test_changed_intent_source_identity_stops_before_write(actual_templates):
    """The recovery validates deterministic record identity, not merely host membership."""
    plan, root, state, intent = interrupted(actual_templates)
    changed = intent.model_copy(update={'records': [
        intent.records[0].model_copy(update={'sha256': '0' * 64}), *intent.records[1:]
    ]})
    before = old_tests.membership(root), old_tests.membership(state)
    with pytest.raises(ValueError, match='Intent differs'):
        replay.validated_replay(tx, plan, root, state, changed, mode='apply')
    assert before == (old_tests.membership(root), old_tests.membership(state))


@pytest.mark.parametrize('kind', ['changed', 'symlink', 'directory', 'missing'])
def test_policy_and_intent_pin_refuses_unsafe_inputs(tmp_path, kind):
    """Frozen code, policy and intent pin checks reject altered or nonordinary files."""
    p = tmp_path / 'input'
    if kind == 'changed':
        p.write_bytes(b'changed')
    elif kind == 'symlink':
        other = tmp_path / 'actual'; other.write_bytes(b'unchanged'); p.symlink_to(other)
    elif kind == 'directory':
        p.mkdir()
    with pytest.raises(ValueError):
        replay.exact(p, tx.digest(b'unchanged'))
