"""Offline agency capture tests using wholly synthetic source fixtures."""
from __future__ import annotations
import copy
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

import pymupdf as fitz
import pytest
from pydantic import ValidationError
from geode.pipeline import ccr_agency_capture as module

BASE = json.loads(r'''
{
  "schema_version": "ccr16-agency-capture-plan-1",
  "status": "prepared_not_activated_not_acquired",
  "prepared_at": "2026-09-23T20:31:00.969096Z",
  "checkpoint_commit_claim": "da3ba811be1599c77ad25fc1c135f3bd6108294d",
  "checkpoint_basis": "root-provided commit; actual working input hashes independently pinned",
  "department_id": "16",
  "department_name": "1000 Department of Public Health and Environment",
  "selected_agency_ids": [
    "137",
    "138",
    "140"
  ],
  "department_catalog_agencies": [],
  "targets": [],
  "frozen_inputs": [],
  "historical_rule_count": 20,
  "historical_url_associations": 65,
  "historical_distinct_urls": 65,
  "historical_received_body_bytes": 1,
  "historical_bytes_are_future_guarantee": false,
  "shared_discovery_associations": 2,
  "shared_discovery_bytes": 1,
  "caps": {
    "status": "proposed_not_active",
    "actual_http_events": 80,
    "distinct_requested_urls": 80,
    "response_bytes": 15000000,
    "aggregate_received_body_bytes": 50000000,
    "automatic_retries": 0,
    "automatic_redirects": 0,
    "timeout_seconds_per_event": 30,
    "overall_elapsed_seconds": 900,
    "activation_at": null,
    "public_stop_at": null,
    "reservation_before_request": true
  },
  "accounting_policy": [
    "Synthetic fixture; no public request or evidence claim."
  ],
  "success_criteria": [
    "Synthetic fixture; no public request or evidence claim."
  ],
  "failure_criteria": [
    "Synthetic fixture; no public request or evidence claim."
  ],
  "limitations": [
    "Synthetic fixture; no public request or evidence claim."
  ],
  "full_department_discovery": false,
  "existing_department_publisher_admissible": false,
  "department16_complete": false,
  "review_required": true,
  "legal_currentness": "not_verified",
  "answer_safe": false,
  "new_public_requests": 0
}
''')


@pytest.fixture
def packet(tmp_path: Path) -> tuple[Path, str, dict[str, Any]]:
    """Generate18catalog agencies and20rules with65 serial synthetic response bindings."""
    plan = copy.deepcopy(BASE)
    bodies: dict[str, bytes] = {}
    targets = []
    origin = 'https://www.sos.state.co.us'
    start = datetime(2026, 9, 23, 18, tzinfo=timezone.utc)
    with fitz.open() as pdf:
        pdf.new_page().insert_text((30, 30), 'SYNTHETIC FIXTURE ONLY')
        pdf_body = pdf.tobytes()
    word_body = b'\xd0\xcf\x11\xe0' + b'SYNTHETIC SIGNATURE ONLY'

    def add(role: str, url: str, body: bytes, parent: dict[str, Any] | None = None,
            attr: str | None = None, aid: str | None = None, rule: str | None = None,
            citation: str | None = None, version: str | None = None) -> dict[str, Any]:
        """Create exact fixture bytes and ordered public-field projections."""
        if role not in ('pdf', 'word'):
            body = b'<html><body>' + body + b'</body></html>'
        seq = len(targets) + 1
        ref = {'path': 'bodies/' + module.sha(body) + '.bin',
               'sha256': module.sha(body), 'bytes': len(body)}
        bodies[ref['path']] = body
        target = {
            'sequence': seq, 'target_id': f'CCR16-P{seq:03}', 'role': role,
            'department_id': '16', 'agency_id': aid, 'rule_id': rule,
            'source_citation': citation, 'version_id': version,
            'source_designation': 'current' if role in ('pdf', 'word') else None,
            'requested_url': url, 'parent_target_id': parent['target_id'] if parent else None,
            'observed_attribute': attr,
            'attribute_kind': 'historically_requested_seed' if not parent else (
                'onclick' if role in ('pdf', 'word') else 'href'),
            'resolution_method': 'synthetic exact fixture join', 'source_label_claim': None,
            'historical': {
                'original_receipt_path_claim': '/FIXTURE/PRIVATE/receipt.json',
                'original_receipt_sha256': '0' * 64, 'original_receipt_bytes': 10,
                'historical_sequence': seq if seq < 3 else seq + 130,
                'requested_url': url,
                'recorded_started_at': (start + timedelta(seconds=seq)).isoformat(),
                'recorded_finished_at':
                    (start + timedelta(seconds=seq, milliseconds=1)).isoformat(),
                'recorded_http_status': 200, 'recorded_result': 'returned',
                'content_type': 'application/pdf' if role == 'pdf' else 'fixture',
                'body': ref, 'recorded_charged_bytes': len(body), 'private_headers_copied': False,
                'projection': 'only explicit nonsecret URL/time/status/body/'
                              'content-type fields retained'}}
        targets.append(target)
        return target

    welcome = add('welcome', origin + '/CCR/Welcome.do',
                  b'<a href="/CCR/NumericalDeptList.do">Catalog</a>')
    agencies = []
    for aid in sorted(module.EXPECTED_IDS, key=int):
        href = f'/CCR/NumericalCCRDocList.do?deptID=16&agencyID={aid}&agencyName=Agency{aid}'
        agencies.append({'agency_id': aid, 'name': 'Agency' + aid, 'original_href': href,
                         'observed_url': origin + href, 'selected': aid in ('137', '138', '140'),
                         'expected_rule_count': {'137': 7, '138': 7, '140': 6}.get(aid)})
    html = '<table><tr><td><a name="1000"></a>Department of Public Health and Environment</td></tr>'
    html += ''.join('<tr><td><a href="' + a['original_href'] + '">' + a['name']
                    + '</a></td><td>x</td></tr>' for a in agencies) + '</table>'
    catalog = add('catalog', origin + '/CCR/NumericalDeptList.do', html.encode(), welcome,
                  '/CCR/NumericalDeptList.do')
    for agency in agencies:
        agency['catalog'] = catalog['historical']['body']
        if not agency['selected']:
            continue
        aid = agency['agency_id']
        rows = []
        for number in range(agency['expected_rule_count']):
            rule = aid + str(number)
            citation = f'1 CCR {aid}-{number + 1}'
            href = (f'/CCR/DisplayRule.do?deptID=16&agencyID={aid}'
                    f'&ruleId={rule}&action=ruleinfo&seriesNum=')
            href += quote(citation)
            rows.append((rule, citation, href))
        listing_body = ('<table><tr><th>CCR#</th><th>Title</th></tr>' +
                        ''.join(f'<tr><td><a href="{href}">{citation}</a></td>'
                                '<td>Synthetic rule</td></tr>'
                                for _, citation, href in rows) + '</table>').encode()
        listing = add('agency_listing', agency['observed_url'], listing_body, catalog,
                      agency['original_href'], aid)
        for rule, citation, href in rows:
            pdf_handler = f"OpenRuleWindow('{rule}', '{citation}')"
            word_handler = f"OpenRuleWordVersion('{rule}', '{citation}')"
            history = (f'<p class="pagehead5">{citation} Synthetic</p><b>Current Version</b>'
                       '<table><tr><th>Effective Date</th><th>Filing Type</th>'
                       '<th>Adopted Date</th><th>Colorado Register Publication Date</th>'
                       '<th>Rulemaking Details (eDocket Tracking #)</th>'
                       '<th>Download Word Version</th></tr><tr><td><a onclick="'
                       + pdf_handler + '">01/01/2020 (PDF)</a></td>'
                       '<td>Permanent Rule</td><td>12/01/2019</td><td>12/15/2019</td>'
                       '<td>Fixture</td><td><a onclick="' + word_handler
                       + '">01/01/2020 (DOCX)</a></td></tr></table>'
                       '<b>Archived Versions</b>').encode()
            target = add('rule_history', origin + href, history, listing, href, aid, rule, citation)
            for role, handler, body in [('pdf', pdf_handler, pdf_body),
                                         ('word', word_handler, word_body)]:
                version, url = module.document_target(target['requested_url'], handler)
                child = add(role, url, body, target, handler, aid, rule, citation, version)
                child['source_label_claim'] = (
                    '01/01/2020 (PDF) Permanent Rule 12/01/2019 12/15/2019 Fixture '
                    '01/01/2020 (DOCX)')
    plan['department_catalog_agencies'] = agencies
    plan['targets'] = targets
    plan['historical_received_body_bytes'] = sum(t['historical']['body']['bytes'] for t in targets)
    plan['shared_discovery_bytes'] = sum(t['historical']['body']['bytes'] for t in targets[:2])
    module.Plan.model_validate_json(json.dumps(plan))
    for path, body in bodies.items():
        destination = tmp_path / 'input' / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(body)
    data = (json.dumps(plan, indent=2) + '\n').encode()
    (tmp_path / 'input/PLAN.json').write_bytes(data)
    return tmp_path / 'input', module.sha(data), plan


def test_roundtrip_and_publisher_refusal(packet: tuple, tmp_path: Path) -> None:
    """Actual portable scope is complete only for selected source associations."""
    root, pin, _ = packet
    output = tmp_path / 'output'
    manifest = module.build(root, output, pin)
    result = module.verify(output, module.sha((output / 'MANIFEST.json').read_bytes()))
    assert result.department_complete is False
    assert len(result.unselected_agency_ids) == 15
    assert len(result.plan.department_catalog_agencies) == 18
    assert len(result.plan.targets) == 65
    assert len(result.document_checks) == 40
    assert all(not t.historical.original_receipt_path_claim for t in result.plan.targets)
    assert result.input_plan_sha256 == pin
    assert result.classification_cutoff is None
    assert all(b'/FIXTURE/PRIVATE' not in (output / ref.path).read_bytes()
               for ref in manifest.files)
    from scripts.publish_ccr_current import validate_payload
    with pytest.raises(ValidationError):
        validate_payload(lambda _: (output / 'CAPTURE.json').read_bytes(), '16')
    with pytest.raises(ValueError, match='exists'):
        module.build(root, output, pin)


@pytest.mark.parametrize('mutation', ['pin', 'body', 'missing', 'symlink', 'fifo'])
def test_input_refusals(packet: tuple, tmp_path: Path, mutation: str) -> None:
    """Wrong identities, missing files, symlinks and FIFOs cannot become capture inputs."""
    import os
    root, pin, plan = packet
    body = root / plan['targets'][0]['historical']['body']['path']
    if mutation == 'pin':
        pin = 'f' * 64
    elif mutation == 'body':
        body.write_bytes(b'Changed')
    else:
        body.unlink()
        if mutation == 'symlink':
            body.symlink_to(root / 'PLAN.json')
        elif mutation == 'fifo':
            os.mkfifo(body)
    with pytest.raises((ValueError, FileNotFoundError)):
        module.build(root, tmp_path / 'output', pin)
    assert not (tmp_path / 'output').exists()


@pytest.mark.parametrize('mutation', ['roster', 'selected', 'sequence', 'duplicate', 'receipt',
                                     'time', 'host', 'parent', 'attribute', 'agency',
                                     'rule', 'version', 'citation', 'bytes', 'shared', 'overlap'])
def test_semantic_refusals(packet: tuple, mutation: str) -> None:
    """Re-pinning metadata cannot invent source/agency/version/time/byte associations."""
    root, pin, data = packet
    plan, captured = module.load_inputs(root, pin)
    changed = copy.deepcopy(data)
    rows = changed['targets']
    if mutation == 'roster':
        changed['department_catalog_agencies'][0]['name'] = 'Invented'
    elif mutation == 'selected':
        changed['department_catalog_agencies'][0]['selected'] = True
    elif mutation == 'sequence':
        rows[2]['sequence'] = 4
    elif mutation == 'duplicate':
        rows[2]['target_id'] = rows[1]['target_id']
    elif mutation == 'receipt':
        rows[3]['historical']['requested_url'] += '&false=1'
    elif mutation == 'time':
        rows[3]['historical']['recorded_started_at'] = '2027-01-01T00:00:00Z'
    elif mutation == 'host':
        rows[3]['requested_url'] = rows[3]['requested_url'].replace('www.sos', 'evil.sos')
        rows[3]['historical']['requested_url'] = rows[3]['requested_url']
    elif mutation == 'parent':
        rows[3]['parent_target_id'] = rows[4]['target_id']
    elif mutation == 'attribute':
        rows[3]['observed_attribute'] += 'invented'
    elif mutation == 'agency':
        rows[3]['agency_id'] = '138'
    elif mutation == 'rule':
        rows[3]['rule_id'] += '0'
    elif mutation == 'version':
        rows[4]['version_id'] += '0'
    elif mutation == 'citation':
        rows[4]['source_citation'] += ' suffix'
    elif mutation == 'bytes':
        changed['historical_received_body_bytes'] += 1
    elif mutation == 'shared':
        changed['shared_discovery_bytes'] += 1
    elif mutation == 'overlap':
        rows[3]['historical']['recorded_started_at'] = rows[2]['historical']['recorded_started_at']
    with pytest.raises(ValueError):
        revised = module.Plan.model_validate_json(json.dumps(changed))
        module.derive(revised, captured, pin)


@pytest.mark.parametrize('body,expected', [(b'<html>no PDF</html>', 'PDF'),
                                         (b'%PDF-1.4\ncorrupt', None)])
def test_document_failure(packet: tuple, body: bytes, expected: str | None) -> None:
    """HTML and structurally corrupt PDF bodies cannot be accepted through metadata changes."""
    root, pin, _ = packet
    plan, captured = module.load_inputs(root, pin)
    target = next(t for t in plan.targets if t.role == 'pdf')
    captured[target.historical.body.path] = body
    with pytest.raises(Exception):
        module.derive(plan, captured, pin)


@pytest.mark.parametrize('mutation',
                         ['extra', 'member', 'manifest_pin', 'private', 'record', 'schema'])
def test_output_tamper(packet: tuple, tmp_path: Path, mutation: str) -> None:
    """Closed identity and deterministic replay refuse tampering even after a reseal."""
    root, pin, _ = packet
    output = tmp_path / 'output'
    manifest = module.build(root, output, pin)
    if mutation == 'extra':
        (output / 'extra.txt').write_text('unbound')
    elif mutation == 'member':
        (output / 'PLAN.json').write_text('{}')
    elif mutation in ('private', 'record', 'schema'):
        name = 'PLAN.json' if mutation == 'private' else (
            'CAPTURE.json' if mutation == 'record' else 'Capture.schema.json')
        data = json.loads((output / name).read_bytes())
        if mutation == 'private':
            data['targets'][0]['historical']['original_receipt_path_claim'] = '/private/injected'
        elif mutation == 'record':
            data['unselected_agency_ids'] = []
        else:
            data['title'] = 'Changed'
        raw = json.dumps(data).encode()
        (output / name).write_bytes(raw)
        manifest = manifest.model_copy(update={'files': [
            module.Asset(path=ref.path, sha256=module.sha(raw), bytes=len(raw))
            if ref.path == name else ref for ref in manifest.files]})
        (output / 'MANIFEST.json').write_bytes(module.encoded(manifest))
    manifest_pin = module.sha((output / 'MANIFEST.json').read_bytes())
    if mutation == 'manifest_pin':
        manifest_pin = 'f' * 64
    with pytest.raises(ValueError):
        module.verify(output, manifest_pin)


@pytest.mark.parametrize('path', ['/absolute', '../escape', 'a/../b', 'a\\b', '', '.'])
def test_paths(path: str) -> None:
    """Model-level path safety blocks escaping references before reads."""
    with pytest.raises(ValueError):
        module.Asset(path=path, sha256='0' * 64, bytes=1)


def test_cli(packet: tuple, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Both commands stay offline and print explicit scope, never completeness."""
    root, pin, _ = packet
    output = tmp_path / 'output'
    assert module.main(['build', '--input', str(root), '--plan-sha256', pin,
                        '--output', str(output)]) == 0
    manifest_pin = json.loads(capsys.readouterr().out)['manifest_sha256']
    assert module.main(['verify', '--root', str(output), '--manifest-sha256', manifest_pin]) == 0
    assert json.loads(capsys.readouterr().out)['department_complete'] is False


@pytest.mark.parametrize('html', [b'<html>no section</html>',
                                  b'<table><tr><td><a name="1000">Wrong</a></td></tr></table>',
                                  b'<table><tr><td><a name="1000"></a>Department of Public Health '
                                  b'and Environment</td></tr><tr><td>bad</td></tr></table>'])
def test_malformed_catalog(html: bytes) -> None:
    """A missing or incomplete catalog cannot define the denominator."""
    with pytest.raises(ValueError):
        module.roster(html, 'https://www.sos.state.co.us/CCR/NumericalDeptList.do')


def test_exact_url_and_anchor_guards() -> None:
    """Ambiguous IDs, handlers, external URLs and conflicting anchors fail closed."""
    with pytest.raises(ValueError):
        module.query('https://www.sos.state.co.us/CCR/x?deptID=16&deptID=17', 'deptID')
    with pytest.raises(ValueError):
        module.resolve('https://www.sos.state.co.us/CCR/x', 'https://evil.example/x')
    with pytest.raises(ValueError):
        module.document_target('https://www.sos.state.co.us/CCR/x', 'alert(1)')
    with pytest.raises(ValueError):
        module.observed_anchor(b'<a>missing</a><a onclick="unknown()">X</a>',
                               'https://www.sos.state.co.us/CCR/x',
                               'https://www.sos.state.co.us/CCR/y', 'onclick')


def test_closed_manifest_caps() -> None:
    """Oversized and duplicate member identities cannot be admitted."""
    asset = module.Asset(path='a', sha256='0' * 64, bytes=15_000_000)
    with pytest.raises(ValueError):
        module.ClosedManifest(files=[asset, asset])
    with pytest.raises(ValueError):
        module.ClosedManifest(files=[asset.model_copy(update={'path': chr(97 + number)})
                                     for number in range(4)])


def test_atomic_interruption_and_collisions(tmp_path: Path,
                                           monkeypatch: pytest.MonkeyPatch) -> None:
    """A failed rename preserves partial evidence and never replaces an existing member."""
    path = tmp_path / 'fresh'
    original = module.os.replace

    def fail(source: Path, destination: Path) -> None:
        """Inject interruption before the atomic publication step."""
        raise OSError('fixture interrupted')

    monkeypatch.setattr(module.os, 'replace', fail)
    with pytest.raises(OSError):
        module.atomic_new(path, b'captured')
    assert not path.exists()
    assert path.with_name('fresh.tmp').read_bytes() == b'captured'
    monkeypatch.setattr(module.os, 'replace', original)
    with pytest.raises(FileExistsError):
        module.atomic_new(path, b'different')
    path.write_bytes(b'original')
    with pytest.raises(ValueError):
        module.atomic_new(path, b'replacement')
    assert path.read_bytes() == b'original'


def test_partial_build_is_not_resumed(packet: tuple, tmp_path: Path,
                                     monkeypatch: pytest.MonkeyPatch) -> None:
    """A partially written directory cannot be overwritten or mistaken for a closed output."""
    root, pin, _ = packet
    output = tmp_path / 'partial'
    original = module.atomic_new
    count = 0

    def fail(path: Path, body: bytes) -> None:
        """Permit first schema then interrupt the next fresh write."""
        nonlocal count
        count += 1
        if count == 2:
            raise OSError('fixture interrupted')
        original(path, body)

    monkeypatch.setattr(module, 'atomic_new', fail)
    with pytest.raises(OSError):
        module.build(root, output, pin)
    assert output.exists() and not (output / 'MANIFEST.json').exists()
    with pytest.raises(ValueError, match='exists'):
        module.build(root, output, pin)


def test_output_cannot_mutate_input_membership(packet: tuple) -> None:
    """A new directory beneath the frozen input would invalidate its closure and is refused."""
    root, pin, _ = packet
    with pytest.raises(ValueError, match='immutable'):
        module.build(root, root / 'new', pin)
    assert not (root / 'new').exists()


@pytest.mark.parametrize('role,field,value', [('rule_history', 'version_id', '999999'),
                                             ('agency_listing', 'source_citation', '99 CCR 999-9'),
                                             ('welcome', 'source_designation', 'current')])
def test_unused_role_fields_refused(packet: tuple, role: str, field: str, value: str) -> None:
    """Irrelevant identifiers and status claims cannot enter public output under another role."""
    _, _, data = packet
    row = next(target for target in data['targets'] if target['role'] == role)
    row[field] = value
    with pytest.raises(ValueError, match='Source role'):
        module.Plan.model_validate_json(json.dumps(data))


@pytest.mark.parametrize('mutation', ['fabricated_label', 'bare_listing', 'wrapped_bare_listing'])
def test_source_structure_and_label(packet: tuple, tmp_path: Path, mutation: str) -> None:
    """Re-pinned fabricated source-row wording or stripped listings remain inadmissible."""
    from bs4 import BeautifulSoup
    root, _, data = packet
    if mutation == 'fabricated_label':
        row = next(target for target in data['targets'] if target['role'] == 'pdf')
        row['source_label_claim'] = 'FABRICATED CURRENT VERSION ADOPTED 2099-01-01'
    else:
        row = next(target for target in data['targets'] if target['role'] == 'agency_listing')
        old = row['historical']['body']
        body = (root / old['path']).read_bytes()
        anchors = BeautifulSoup(body, 'html.parser').find_all('a', href=True)
        replacement = ''.join(str(anchor) for anchor in anchors).encode()
        if mutation == 'wrapped_bare_listing':
            replacement = b'<html><body>' + replacement + b'</body></html>'
        ref = {'path': 'bodies/' + module.sha(replacement) + '.bin',
               'sha256': module.sha(replacement), 'bytes': len(replacement)}
        (root / ref['path']).write_bytes(replacement)
        row['historical']['body'] = ref
        row['historical']['recorded_charged_bytes'] = len(replacement)
        data['historical_received_body_bytes'] += len(replacement) - old['bytes']
    raw = json.dumps(data).encode()
    (root / 'PLAN.json').write_bytes(raw)
    with pytest.raises(ValueError):
        module.build(root, tmp_path / 'refused', module.sha(raw))
    assert not (tmp_path / 'refused').exists()
