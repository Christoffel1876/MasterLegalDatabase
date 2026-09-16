"""Offline CI orchestration counterexamples; never contact a publisher."""
from __future__ import annotations

import importlib.util
import json
import hashlib
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

MODULE = Path(__file__).resolve().parents[1] / 'scripts/manual_source_watch_ci.py'
spec = importlib.util.spec_from_file_location('scripts.manual_source_watch_ci', MODULE)
w = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = w
spec.loader.exec_module(w)


def ref(path: str, data: bytes) -> dict:
    return {'path': path, 'sha256': hashlib.sha256(data).hexdigest(), 'size_bytes': len(data)}


@pytest.fixture
def packet(tmp_path, monkeypatch):
    root = tmp_path / 'repository'
    root.mkdir()
    pairs = []
    refs = []
    for batch in w.BATCH_IDS:
        ids = [batch + '-first', batch + '-second']
        data = json.dumps({'targets': [{'canonical_source_id': s} for s in ids],
                          'limits': {'requests': 4, 'distinct_urls': 4, 'redirects_per_source': 1,
                                     'bytes_per_source': 2000000, 'total_bytes': 4000000,
                                     'request_seconds': 30}, 'max_run_seconds': 300}).encode()
        path = 'config/' + batch + '.json'
        (root / path).parent.mkdir(exist_ok=True)
        (root / path).write_bytes(data)
        selection = ref(path, data)
        refs.append(selection)
        pairs.append({'batch_id': batch, 'module': 'geode.pipeline.manual_source_watch' if
                      batch == 'springs' else 'geode.pipeline.manual_source_watch_batches',
                      'selection': selection, 'source_ids': ids})
    plan = {'schema_version': 'manual-watch-ci-v1', 'pairs': pairs, 'immutable_inputs': refs,
            'max_source_events': 16, 'max_source_body_bytes': 16000000,
            'max_source_seconds': 1200, 'legal_currentness': 'not_verified'}
    data = json.dumps(plan).encode()
    (root / w.CONFIG).write_bytes(data)
    monkeypatch.setattr(w, 'CONFIG_SHA', hashlib.sha256(data).hexdigest())
    raw = root / '_RAW_ARCHIVE/manual_intake/manual_source_intake_manifest.jsonl'
    raw.parent.mkdir(parents=True)
    raw.write_bytes(b'exact historical fixture prefix\n')
    return root, plan


class Process:
    """Fake only process I/O; exercise actual retained files and wrapper decisions."""
    def __init__(self, root, plan, status='unchanged', fail=None):
        self.root, self.plan, self.status, self.fail = root, plan, status, fail
        self.calls = []

    def __call__(self, argv, **kwargs):
        self.calls.append(argv)
        batch = argv[argv.index('--batch') + 1] if '--batch' in argv else 'springs'
        pair = next(p for p in self.plan['pairs'] if p['batch_id'] == batch)
        execute, verify = '--execute' in argv, '--verify-run' in argv
        if not execute and not verify:
            return SimpleNamespace(returncode=2 if self.fail == 'readiness' else 0,
                                   stdout=b'{}\n', stderr=b'readiness fixture')
        if execute and self.fail == 'timeout':
            raise subprocess.TimeoutExpired(argv, 330, output=b'partial stdout', stderr=b'partial')
        if execute and self.fail == 'oserror':
            raise OSError('fixture process unavailable')
        name = argv[argv.index('--run-name' if execute else '--verify-run') + 1]
        runtime = 'manual_source_watch' if batch == 'springs' else 'manual_source_watch_batches'
        path = self.root / '.geode_runtime' / runtime / name / 'report.json'
        if execute:
            path.parent.mkdir(parents=True)
            observations = []
            for source in pair['source_ids']:
                observations.append({'canonical_source_id': source, 'status': self.status,
                    'reason': 'fixture exact source outcome', 'requested_url': 'https://example.test/source',
                    'response_url': None, 'http_status': 200 if self.status in w.COMPLETE else 403,
                    'baseline': {'sha256': '0' * 64}, 'response_body': {'sha256': '1' * 64},
                    'request_started_at': None, 'response_finished_at': None,
                    'legal_currentness': 'not_verified'})
            report = {'plan_sha256': pair['selection']['sha256'], 'mode': 'live_http',
                      'legal_currentness': 'not_verified', 'baseline_updated': False,
                      'observations': observations}
            path.write_text(json.dumps(report))
        code = 0 if self.status in w.COMPLETE else 2
        if verify and self.fail == 'verify':
            return SimpleNamespace(returncode=2, stdout=b'', stderr=b'fixture verification failed')
        if verify and self.fail == 'substitute':
            report = json.loads(path.read_bytes())
            report['observations'][0]['status'] = 'changed'
            return SimpleNamespace(returncode=code, stdout=json.dumps(report).encode(), stderr=b'')
        if verify and self.fail == 'false-success':
            code = 0
        return SimpleNamespace(returncode=code, stdout=path.read_bytes(), stderr=b'')


@pytest.mark.parametrize('status,expected', [('unchanged', 'unchanged'), ('changed', 'changed'),
    ('access_denied', 'incomplete'), ('not_found', 'incomplete'), ('transport_error', 'incomplete'),
    ('invalid_response', 'incomplete'), ('refused', 'incomplete'), ('not_checked', 'incomplete')])
def test_all_source_outcomes_retained(packet, status, expected):
    root, plan = packet
    before = (root / '_RAW_ARCHIVE/manual_intake/manual_source_intake_manifest.jsonl').read_bytes()
    proc = Process(root, plan, status)
    result = w.run_ci(root, 'fixture', True, 'workflow_dispatch', None, proc)
    assert result.status == expected
    assert len(result.pairs) == 4 and sum(len(p.sources) for p in result.pairs) == 8
    assert all(s.status == status for p in result.pairs for s in p.sources)
    assert len(proc.calls) == 12
    assert (root / '_RAW_ARCHIVE/manual_intake/manual_source_intake_manifest.jsonl').read_bytes() == before
    assert not result.baseline_updated and not result.schedule_activation_verified
    assert all(len(c) > 1 and isinstance(c, list) for c in proc.calls)


def test_readiness_failure_prevents_every_source_attempt(packet):
    root, plan = packet
    proc = Process(root, plan, fail='readiness')
    result = w.run_ci(root, 'setup', True, 'schedule', None, proc)
    assert result.status == 'setup_failed'
    assert len(proc.calls) == 4 and not any('--execute' in c for c in proc.calls)
    assert (root / w.RUNTIME / 'setup/summary.md').is_file()
    assert all(not p.sources for p in result.pairs)


@pytest.mark.parametrize('failure', ['timeout', 'oserror', 'verify', 'substitute', 'false-success'])
def test_incomplete_or_unverified_is_not_unchanged(packet, failure):
    root, plan = packet
    proc = Process(root, plan, 'access_denied' if failure == 'false-success' else 'unchanged', failure)
    result = w.run_ci(root, 'fail', True, 'schedule', None, proc)
    assert result.status == 'incomplete'
    assert all(p.status == 'verification_failed' for p in result.pairs)
    assert len([c for c in proc.calls if '--execute' in c]) == 4
    assert (root / w.RUNTIME / 'fail/springs-execute.process.json').exists()


def test_default_readiness_never_executes(packet):
    root, plan = packet
    proc = Process(root, plan)
    result = w.run_ci(root, 'offline', False, 'local_readiness', None, proc)
    assert result.status == 'ready' and len(proc.calls) == 4
    assert all('--execute' not in c and '--verify-run' not in c for c in proc.calls)


@pytest.mark.parametrize('name', ['../bad', '/tmp/escape', 'bad space', 'x' * 41])
def test_unsafe_output_refused_before_creation(packet, name):
    root, plan = packet
    with pytest.raises(ValueError):
        w.run_ci(root, name, False, 'local_readiness', None, Process(root, plan))
    assert not (root / w.RUNTIME).exists()


def test_existing_run_refused_without_overwrite(packet):
    root, plan = packet
    proc = Process(root, plan)
    w.run_ci(root, 'same', False, 'local_readiness', None, proc)
    before = {p: p.read_bytes() for p in (root / w.RUNTIME).rglob('*') if p.is_file()}
    with pytest.raises(ValueError):
        w.run_ci(root, 'same', True, 'schedule', None, proc)
    assert all(p.read_bytes() == b for p, b in before.items())


def test_changed_immutable_input_fails_before_any_process(packet):
    root, plan = packet
    (root / plan['immutable_inputs'][0]['path']).write_bytes(b'tampered')
    proc = Process(root, plan)
    result = w.run_ci(root, 'badpin', True, 'schedule', None, proc)
    assert result.status == 'setup_failed' and proc.calls == []


def test_unreviewed_config_fails_before_any_process(packet):
    root, plan = packet
    (root / w.CONFIG).write_bytes(b'{}')
    proc = Process(root, plan)
    assert w.run_ci(root, 'badplan', True, 'schedule', None, proc).status == 'setup_failed'
    assert proc.calls == []


def test_path_and_symlink_guards(packet, tmp_path):
    root, _ = packet
    for path in ['../escape', '/etc/passwd']:
        with pytest.raises(ValueError):
            w.check_ref(root, w.Ref(path=path, sha256='0' * 64, size_bytes=0))
    (root / 'link').symlink_to(root / w.CONFIG)
    with pytest.raises(ValueError):
        w.ordinary(root / 'link')
    (root / '.geode_runtime').symlink_to(tmp_path)
    with pytest.raises(ValueError):
        w.safe_output(root, 'safe')


def test_manifest_mutation_preserves_guard_failure(packet):
    root, plan = packet
    proc = Process(root, plan)
    def mutate(argv, **kwargs):
        value = proc(argv, **kwargs)
        if '--execute' in argv:
            raw = root / '_RAW_ARCHIVE/manual_intake/manual_source_intake_manifest.jsonl'
            raw.write_bytes(raw.read_bytes() + b'foreign\n')
        return value
    result = w.run_ci(root, 'foreign', True, 'schedule', None, mutate)
    assert result.status == 'setup_failed'


def test_cli_refusal_and_readiness(packet, monkeypatch, capsys):
    root, plan = packet
    monkeypatch.setattr(w, 'run_ci', lambda *a: w.Summary(created_at=w.utcnow(), event_context='local_readiness',
        run_name='cli', commit_claim=None, execution_requested=False, status='ready', pairs=[],
        plan_sha256=w.CONFIG_SHA))
    assert w.main(['--root', str(root), '--run-name', 'cli']) == 0
    assert json.loads(capsys.readouterr().out)['status'] == 'ready'
    monkeypatch.setattr(w, 'run_ci', lambda *a: (_ for _ in ()).throw(ValueError('fixture refusal')))
    assert w.main(['--run-name', 'cli']) == 2
    assert 'refusal' in capsys.readouterr().err


def test_python311_syntax_contract():
    import ast
    ast.parse(MODULE.read_text(), feature_version=(3, 11))


def test_mixed_change_and_denial_stays_incomplete_with_verified_siblings(packet):
    root, plan = packet
    normal = Process(root, plan)
    changed = Process(root, plan, 'changed')
    denied = Process(root, plan, 'access_denied')
    def mixed(argv, **kwargs):
        batch = argv[argv.index('--batch') + 1] if '--batch' in argv else 'springs'
        proc = changed if batch == 'springs' else denied if batch == 'county-fees-v1' else normal
        return proc(argv, **kwargs)
    result = w.run_ci(root, 'mixed', True, 'schedule', None, mixed)
    assert result.status == 'incomplete'
    assert result.pairs[0].sources[0].status == 'changed'
    assert result.pairs[1].sources[0].status == 'access_denied'
    assert result.pairs[2].sources[0].status == 'unchanged'
    text = w.markdown(result)
    assert 'springs-first' in text and 'county-fees-v1-first' in text
    assert 'Legal currentness is not verified' in text


@pytest.mark.parametrize('change', ['order', 'duplicate-source', 'duplicate-ref', 'identity', 'caps'])
def test_even_resealed_fixture_plan_refuses_scope_errors(packet, monkeypatch, change):
    root, plan = packet
    if change == 'order':
        plan['pairs'].reverse()
    elif change == 'duplicate-source':
        plan['pairs'][0]['source_ids'][1] = plan['pairs'][0]['source_ids'][0]
    elif change == 'duplicate-ref':
        plan['immutable_inputs'].append(plan['immutable_inputs'][0])
    else:
        path = root / plan['pairs'][0]['selection']['path']
        selection = json.loads(path.read_bytes())
        if change == 'identity':
            selection['targets'][0]['canonical_source_id'] = 'wrong-source'
        else:
            selection['limits']['requests'] = 5
        data = json.dumps(selection).encode()
        path.write_bytes(data)
        newref = ref(plan['pairs'][0]['selection']['path'], data)
        plan['pairs'][0]['selection'] = newref
        plan['immutable_inputs'][0] = newref
    data = json.dumps(plan).encode()
    (root / w.CONFIG).write_bytes(data)
    monkeypatch.setattr(w, 'CONFIG_SHA', hashlib.sha256(data).hexdigest())
    with pytest.raises(ValueError):
        w.load_plan(root)


@pytest.mark.parametrize('field,value', [('mode', 'offline_fixture'), ('baseline_updated', True),
    ('observations', []), ('legal_currentness', 'current')])
def test_substituted_report_claims_never_admitted(packet, field, value):
    root, plan = packet
    proc = Process(root, plan)
    def forged(argv, **kwargs):
        result = proc(argv, **kwargs)
        if '--verify-run' in argv:
            batch = argv[argv.index('--batch') + 1] if '--batch' in argv else 'springs'
            runtime = 'manual_source_watch' if batch == 'springs' else 'manual_source_watch_batches'
            path = root / '.geode_runtime' / runtime / argv[argv.index('--verify-run')+1] / 'report.json'
            report = json.loads(path.read_bytes()); report[field] = value
            path.write_text(json.dumps(report))
            result.stdout = path.read_bytes()
        return result
    result = w.run_ci(root, 'forged', True, 'schedule', None, forged)
    assert result.status == 'incomplete'
    assert all(p.status == 'verification_failed' for p in result.pairs)


def test_immutable_change_between_readiness_and_execution_stops_all_requests(packet):
    root, plan = packet
    proc = Process(root, plan)
    def tamper(argv, **kwargs):
        result = proc(argv, **kwargs)
        if len(proc.calls) == 4:
            (root / plan['immutable_inputs'][0]['path']).write_bytes(b'late mutation')
        return result
    result = w.run_ci(root, 'late', True, 'schedule', None, tamper)
    assert result.status == 'setup_failed'
    assert not any('--execute' in c for c in proc.calls)


def test_summary_symlink_refused(packet, tmp_path):
    root, _ = packet
    out = root / 'summary-fixture'; out.mkdir()
    target = tmp_path / 'untouched'; target.write_bytes(b'untouched')
    (out / 'summary.json').symlink_to(target)
    summary = w.Summary(created_at=w.utcnow(), event_context='local_readiness', run_name='test',
        commit_claim=None, execution_requested=False, status='ready', pairs=[], plan_sha256=w.CONFIG_SHA)
    with pytest.raises(ValueError):
        w.save_summary(out, summary)
    assert target.read_bytes() == b'untouched'


def test_workflow_is_readiness_by_default_and_no_write_permission():
    workflow = (MODULE.parents[1] / '.github/workflows/manual-source-watch-daily.yml').read_text()
    assert 'default: false' in workflow
    assert "vars.MANUAL_WATCH_DAILY_ENABLED == 'true'" in workflow
    assert "github.event_name == 'workflow_dispatch' && inputs.execute == true" in workflow
    assert 'mode=()' in workflow and 'mode=(--execute)' in workflow
    assert 'persist-credentials: false' in workflow and 'lfs: false' in workflow
    assert 'contents: write' not in workflow and 'pull-requests:' not in workflow
    assert 'if: always()' in workflow and 'include-hidden-files: true' in workflow
    assert 'publish_register' not in workflow and 'GH_TOKEN:' not in workflow
