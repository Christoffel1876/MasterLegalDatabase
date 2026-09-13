"""Source admission, custody distinctions and three independently selected finite batches."""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

import pytest
from geode.pipeline import manual_source_watch_batches as w
from test_manual_source_watch_batches import NOW, PROPOSED, SOURCE, Response, packet


def selected(root: Path, batch: str) -> tuple[Path, w.Plan]:
    """Load a named pair using the same production entry point as an operator."""
    path = root / w.SELECTIONS[batch]
    return path, w.load_plan(path)


@pytest.mark.parametrize('batch', list(w.BATCHES))
def test_each_batch_selects_only_its_two_approved_sources(packet: Path, batch: str) -> None:
    """Each explicit batch observes two sources and preserves whole custody records."""
    path, plan = selected(packet, batch)
    calls = []
    outputs = []
    for target in plan.targets:
        outputs.append((packet / target.baseline.path).read_bytes())
    def fetch(url: str, *args: Any) -> Response:
        calls.append(url)
        return Response(outputs[len(calls) - 1])
    report = w.run_watch(path, packet / w.RUNTIME / batch, NOW, w.g.sha(path),
                         clock=lambda: NOW, fetch=fetch)
    assert calls == [t.url for t in plan.targets]
    assert [o.source_id for o in report.observations] == list(w.BATCHES[batch])
    assert [o.source for o in report.observations] == [t.source for t in plan.targets]
    assert report.status == 'completed' and report.mode == 'offline_fixture'
    assert report.legal_currentness == 'not_verified' and not report.baseline_updated
    assert w.verify_run(path, packet / w.RUNTIME / batch) == report
    assert w.readiness(packet, path).batch_id == batch


def test_unknown_start_and_later_reacquisition_are_not_invented(packet: Path) -> None:
    """Receipt time is not source acquisition; a later GET does not rewrite old custody."""
    _, county = selected(packet, 'county-fees-v1')
    arapahoe = county.targets[0]
    assert arapahoe.baseline_request_started_at is None
    assert arapahoe.repository_received_at > arapahoe.baseline_recorded_http_time
    _, greeley = selected(packet, 'greeley-fees-v1')
    for target in greeley.targets:
        assert target.source.historical_raw_url is None
        assert target.source.historical_acquisition_method == 'received_review_package'
        assert target.repository_received_at < target.baseline_request_started_at
        assert 'later' in target.source.http_time_role.lower()
        assert target.source.legal_currentness == 'not_verified'


@pytest.mark.parametrize('batch', ['western-fees-v1', 'greeley-fees-v1'])
def test_cli_selectable_readiness_no_network(packet: Path, batch: str, capsys: Any) -> None:
    """Operators select reviewed files by name, not by editing source code or URLs."""
    assert w.main(['--root', str(packet), '--batch', batch]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data['configured_source_ids'] == list(w.BATCHES[batch])
    assert data['prior_watch_execution'] == 'not_asserted'


def test_batch_filename_swap_refused(packet: Path) -> None:
    """A valid different pair cannot hide under another batch filename."""
    paths = [packet / p for p in w.SELECTIONS.values()]
    shutil.copyfile(paths[1], paths[0])
    with pytest.raises(ValueError, match='filename'):
        w.load_plan(paths[0])


@pytest.mark.parametrize('field,value', [
    ('proposed_url', 'https://files.arapahoeco.gov/other.pdf'),
    ('authority_id', 'CO-MUNICIPAL-GREELEY'),
    ('http_started_at', '2026-09-10T21:28:00Z'),
    ('historical_acquisition_method', 'received_review_package'),
])
def test_coherent_target_substitution_still_fails_catalog_pin(
        packet: Path, field: str, value: str) -> None:
    """Updating redundant display fields does not authorize a changed source binding."""
    path, plan = selected(packet, 'county-fees-v1')
    source = plan.targets[0].source.model_dump(mode='json')
    source[field] = value
    changed = w.SourceBinding.model_validate_json(json.dumps(source))
    data = plan.model_dump(mode='json')
    data['targets'][0] = w.Target(**w.target_fields(changed), source=changed).model_dump(mode='json')
    path.write_text(w.Plan.model_validate_json(json.dumps(data)).model_dump_json())
    with pytest.raises(ValueError, match='substitution'):
        w.load_plan(path)
    assert not (packet / w.RUNTIME).exists()


def test_catalog_rehash_is_not_an_admission_mechanism(packet: Path) -> None:
    """Changing a data catalog requires a new reviewed code version, not only local JSON edits."""
    path = packet / w.CATALOG
    data = json.loads(path.read_bytes())
    data['sources'][0]['proposed_url'] = 'https://files.arapahoeco.gov/other.pdf'
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match='Approved source catalog'):
        w.load_plan(packet / w.SELECTION)


@pytest.mark.parametrize('field', ['authority_evidence', 'custody_evidence', 'review_evidence'])
def test_pinned_metadata_tamper_refused(packet: Path, field: str) -> None:
    """Even metadata-only input changes fail before any event reservation."""
    path, plan = selected(packet, 'county-fees-v1')
    artifact = packet / getattr(plan.targets[1].source, field).artifact.path
    artifact.write_bytes(artifact.read_bytes() + b' ')
    with pytest.raises(ValueError):
        w.load_plan(path)
    assert not (packet / w.RUNTIME).exists()


def test_city_referral_html_tamper_refused(packet: Path) -> None:
    """An unchanged CDN receipt does not excuse a corrupted exact city referral."""
    path, plan = selected(packet, 'greeley-fees-v1')
    source = plan.targets[0].source
    ref = next(e for e in source.referral_evidence if e.artifact.path.endswith('/PRESERVATION.json'))
    proof = json.loads((packet / ref.artifact.path).read_bytes())
    parent = (packet / ref.artifact.path).parent / proof['sources'][0]['anchor']['parent']['path']
    parent.write_bytes(parent.read_bytes() + b'changed')
    with pytest.raises(ValueError):
        w.load_plan(path)


def test_semantic_custody_guards_with_individually_rebound_test_data(
        packet: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Defense after the catalog pin still checks concrete receipt URL and owner claims."""
    _, plan = selected(packet, 'county-fees-v1')
    source = plan.targets[0].source
    records, hashes, _ = w.manual_records(packet)
    original = w.evidence_value
    for field, value, match in [('authority_id', 'wrong', 'authority'),
                                ('requested_url', 'wrong', 'request URL'),
                                ('status_code', 404, 'HTTP/source'),
                                ('error', 'failed', 'response failure')]:
        def fake(root: Path, evidence: w.Evidence) -> Any:
            data = original(root, evidence)
            if field in data:
                data[field] = value
            return data
        monkeypatch.setattr(w, 'evidence_value', fake)
        with pytest.raises(ValueError, match=match):
            w.validate_source(packet, source, records, hashes)
        monkeypatch.setattr(w, 'evidence_value', original)


@pytest.mark.parametrize('mutation', ['bound', 'href', 'text', 'node'])
def test_greeley_anchor_semantics(packet: Path, monkeypatch: pytest.MonkeyPatch,
                                  mutation: str) -> None:
    """Test all exact anchor associations independently of the earlier manifest hash gate."""
    _, plan = selected(packet, 'greeley-fees-v1')
    source = plan.targets[0].source
    original = w.evidence_value
    def fake(root: Path, evidence: w.Evidence) -> Any:
        value = original(root, evidence)
        if evidence.artifact.path.endswith('/PRESERVATION.json'):
            anchor = value['sources'][0]['anchor']
            if mutation == 'bound':
                anchor['exact_source_end_byte'] += 1
            elif mutation == 'href':
                anchor['href'] += 'wrong'
            elif mutation == 'text':
                anchor['normalized_dom_text'] += 'wrong'
            else:
                anchor['href'] = source.proposed_url
                anchor['normalized_dom_text'] = ''
        return value
    monkeypatch.setattr(w, 'evidence_value', fake)
    with pytest.raises(ValueError, match='Greeley'):
        w.greeley_anchor(packet, source)


@pytest.mark.parametrize('payload', [b'{}\n', b''])
def test_streamed_custody_row_requires_exact_file_and_row(packet: Path, payload: bytes) -> None:
    """Missing selected rows and JSONL hash mismatches cannot be accepted as custody."""
    _, plan = selected(packet, 'county-fees-v1')
    source = plan.targets[1].source
    evidence = source.custody_evidence
    (packet / evidence.artifact.path).write_bytes(payload)
    with pytest.raises(ValueError):
        w.evidence_value(packet, evidence)


def test_staged_preflight_uses_explicit_canonical_root(packet: Path) -> None:
    """Preparers can validate staged configs against canonical bytes without installing files."""
    staged = PROPOSED / w.SELECTION
    assert w.load_plan(staged, root=packet, catalog_path=packet / w.CATALOG).batch_id == (
        'county-fees-v1')
    with pytest.raises(ValueError, match='Unsafe repository'):
        w.load_plan(staged, root=packet / 'missing')


def test_pointer_paths_are_data_only() -> None:
    """Pointers resolve escaped object keys/arrays; no external JSON resolution is possible."""
    assert w.pointer({'a/b': [{'~': 3}]}, '/a~1b/0/~0') == 3
    with pytest.raises(ValueError):
        w.pointer({}, 'https://example.org/value')


def test_prior_springs_module_and_config_unchanged() -> None:
    """The new code does not replace the bytes required by existing Springs saved runs."""
    pins = {
        'geode/pipeline/manual_source_watch.py':
            'e1958b886a8b164b0cc4e7a890fa70c47679fdb5318c33423ac45254f60f06ea',
        'geode/pipeline/manual_watch_http.py':
            'c935ee6d74843e9214f27c5fef82d4470ec3c2b55ea5001eade594cc6a8de2ae',
        'config/manual_source_watch.json':
            '91b4c46f7121de66d70b353405900f9d1ed3a3247718a9471ad2f1a9afa6dabb',
    }
    for name, digest in pins.items():
        assert hashlib.sha256((SOURCE / name).read_bytes()).hexdigest() == digest


def test_cross_batch_run_name_cannot_reuse_or_overwrite_events(packet: Path) -> None:
    """Each invocation binds one selection digest even when an operator repeats a run name."""
    path, plan = selected(packet, 'county-fees-v1')
    items = [Response((packet / t.baseline.path).read_bytes()) for t in plan.targets]
    output = packet / w.RUNTIME / 'same-name'
    w.run_watch(path, output, NOW, w.g.sha(path), clock=lambda: NOW,
                fetch=lambda *args: items.pop(0))
    before = {p.relative_to(output): p.read_bytes() for p in output.rglob('*') if p.is_file()}
    other, _ = selected(packet, 'western-fees-v1')
    with pytest.raises(ValueError):
        w.run_watch(other, output, NOW, w.g.sha(other), clock=lambda: NOW,
                    fetch=lambda *args: pytest.fail('No cross-batch request is permitted'))
    assert before == {p.relative_to(output): p.read_bytes()
                      for p in output.rglob('*') if p.is_file()}


def test_v2_does_not_admit_other_urls_or_cross_host_redirects(packet: Path) -> None:
    """The five-host policy does not expand a pair or permit an otherwise approved new owner."""
    path, plan = selected(packet, 'county-fees-v1')
    calls = []
    def fetch(url: str, *args: Any) -> Response:
        calls.append(url)
        return Response(b'', 302, {'location': plan.targets[1].url})
    report = w.run_watch(path, packet / w.RUNTIME / 'cross-owner', NOW, w.g.sha(path),
                         clock=lambda: NOW, fetch=fetch)
    assert calls[0] == plan.targets[0].url
    assert len(calls) == 1  # The other host is refused before any redirect request.
    assert report.observations[0].status == 'refused'
    assert report.observations[0].events == [1]
    assert all(o.bytes_equal_to_baseline is None for o in report.observations)
