"""Independent cases recorded before draft inspection; all subprocess I/O is injected."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import socket
import sys

import pytest

ROOT = Path(__file__).resolve().parent
FIXTURE = ROOT / 'final/tests/test_manual_source_watch_ci.py'
SPEC = importlib.util.spec_from_file_location('reviewed_fixture_helpers', FIXTURE)
f = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = f
SPEC.loader.exec_module(f)
w = f.w


@pytest.fixture()
def packet(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple:
    """Reuse setup only; assertions and mixed results are independently specified."""
    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError('Network forbidden in independent fixture')
    monkeypatch.setattr(socket, 'create_connection', forbidden)
    return f.packet.__wrapped__(tmp_path, monkeypatch)


def report_path(root: Path, argv: list[str]) -> Path:
    """Locate only the per-pair fixture report chosen by actual wrapper arguments."""
    mode = '--run-name' if '--execute' in argv else '--verify-run'
    runtime = ('manual_source_watch_batches' if '--batch' in argv else 'manual_source_watch')
    return root / '.geode_runtime' / runtime / argv[argv.index(mode) + 1] / 'report.json'


@pytest.mark.parametrize('status', ['unchanged', 'changed'])
def test_valid_stopped_complete_is_incomplete(packet: tuple, status: str) -> None:
    """Complete comparisons survive a valid non-null stop reason and exit 2."""
    root, plan = packet
    process = f.Process(root, plan, status=status)
    calls = []

    def stopped(argv: list[str], **kwargs: object) -> object:
        calls.append(argv)
        result = process(argv, **kwargs)
        if '--execute' in argv or '--verify-run' in argv:
            path = report_path(root, argv)
            report = json.loads(path.read_bytes())
            report['status'] = 'stopped'
            report['stop_reason'] = 'Fixture interruption after retained complete comparisons'
            path.write_text(json.dumps(report))
            result.stdout = path.read_bytes()
            result.returncode = 2
        return result

    result = w.run_ci(root, 'stopped-complete', True, 'workflow_dispatch', None, stopped)
    assert result.status == 'incomplete'
    assert all(pair.status == 'incomplete' and pair.reason is None for pair in result.pairs)
    assert all(source.status == status for pair in result.pairs for source in pair.sources)
    assert len(calls) == 12
    assert not any('--execute' in args for args in calls[:4])


@pytest.mark.parametrize('status', ['access_denied', 'not_found', 'invalid_response',
                                    'refused', 'not_checked', 'transport_error'])
def test_actual_stopped_source_failures_are_retained(packet: tuple, status: str) -> None:
    """Actual producer failure semantics remain stopped/exit2, never false success."""
    root, plan = packet
    process = f.Process(root, plan, status=status)
    result = w.run_ci(root, 'failed-source', True, 'workflow_dispatch', None, process)
    assert result.status == 'incomplete'
    assert all(pair.status == 'incomplete' for pair in result.pairs)
    assert all(source.status == status for pair in result.pairs for source in pair.sources)
    assert all(pair.execute_exit == pair.verify_exit == 2 for pair in result.pairs)


@pytest.mark.parametrize('changed_pair', [None, 'county-fees-v1'])
def test_no_change_and_mixed_change(packet: tuple, changed_pair: str | None) -> None:
    """A change in one pair does not erase unchanged results in the other pairs."""
    root, plan = packet
    normal = f.Process(root, plan)
    changed = f.Process(root, plan, status='changed')

    def mixed(argv: list[str], **kwargs: object) -> object:
        batch = argv[argv.index('--batch') + 1] if '--batch' in argv else 'springs'
        return (changed if batch == changed_pair else normal)(argv, **kwargs)

    result = w.run_ci(root, 'mixed-results', True, 'schedule', None, mixed)
    assert result.status == ('changed' if changed_pair else 'unchanged')
    assert all(pair.status == 'verified' for pair in result.pairs)
    assert sum(s.status == 'changed' for p in result.pairs for s in p.sources) == (
        2 if changed_pair else 0)
    assert not result.baseline_updated and result.legal_currentness == 'not_verified'


@pytest.mark.parametrize('bad_index', range(4))
def test_each_individual_preflight_failure_blocks_all_http(packet: tuple, bad_index: int) -> None:
    """Every pair preflight completes before any execute subprocess may be attempted."""
    root, plan = packet
    process = f.Process(root, plan)

    def fail_one(argv: list[str], **kwargs: object) -> object:
        value = process(argv, **kwargs)
        if len(process.calls) - 1 == bad_index:
            value.returncode = 2
        return value

    result = w.run_ci(root, 'preflight-failure', True, 'schedule', None, fail_one)
    assert result.status == 'setup_failed'
    assert len(process.calls) == 4
    assert not any('--execute' in args for args in process.calls)


@pytest.mark.parametrize('lie', ['completed-denial', 'verify-exit', 'stop-status'])
def test_genuine_report_exit_disagreements_reject(packet: tuple, lie: str) -> None:
    """Do not promote the withdrawn impossible completed-denial premise as valid."""
    root, plan = packet
    process = f.Process(root, plan, status='access_denied' if lie == 'completed-denial'
                        else 'unchanged')

    def forged(argv: list[str], **kwargs: object) -> object:
        result = process(argv, **kwargs)
        if '--execute' in argv or '--verify-run' in argv:
            path = report_path(root, argv)
            report = json.loads(path.read_bytes())
            if lie == 'completed-denial':
                report['status'] = 'completed'
                result.returncode = 0
            elif lie == 'stop-status':
                report['stop_reason'] = 'non-null stop conflicts with completed status'
            elif '--verify-run' in argv:
                result.returncode = 2
            path.write_text(json.dumps(report))
            result.stdout = path.read_bytes()
        return result

    result = w.run_ci(root, 'disagreement', True, 'schedule', None, forged)
    assert result.status == 'incomplete'
    assert all(pair.status == 'verification_failed' for pair in result.pairs)


def test_partial_stdout_timeout_has_exact_receipt_and_no_retry(packet: tuple) -> None:
    """Timeout partial output remains immutable while subsequent pairs stay bounded."""
    root, plan = packet
    process = f.Process(root, plan, fail='timeout')
    result = w.run_ci(root, 'timeout', True, 'schedule', None, process)
    out = root / w.RUNTIME / 'timeout'
    receipt = w.ProcessReceipt.model_validate_json((out / 'springs-execute.process.json').read_bytes())
    assert receipt.exit_code == 124 and not receipt.retried
    assert w.check_ref(out, receipt.stdout) == b'partial stdout'
    assert w.check_ref(out, receipt.stderr) == b'partial'
    assert result.status == 'incomplete'
    assert len([args for args in process.calls if '--execute' in args]) == 4


def test_source_status_schema_is_closed() -> None:
    """Published typed summary limits match runtime outcomes, not arbitrary strings."""
    schema = w.SourceResult.model_json_schema()
    assert set(schema['properties']['status']['enum']) == w.STATUSES


def test_final_code_identity_unchanged() -> None:
    """Independent execution stays bound to the reviewed frozen runner."""
    path = ROOT / 'final/scripts/manual_source_watch_ci.py'
    assert hashlib.sha256(path.read_bytes()).hexdigest() == (
        '09fc26756c7432af64c65b48ad8b08080c0cf1d5353456b587062386c65135df')
