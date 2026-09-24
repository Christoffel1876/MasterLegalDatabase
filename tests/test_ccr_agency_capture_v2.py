"""Synthetic offline scope and adversarial tests; these tests never perform HTTP."""
from __future__ import annotations

import copy
import json
import os
import shutil
from pathlib import Path
from typing import Any
from urllib.parse import quote

import pymupdf as fitz
import pytest
from pydantic import ValidationError

from geode.pipeline import ccr_agency_capture_v2 as m

Fixture = tuple[Path, dict[str, Any], dict[str, bytes]]
ORIGIN = 'https://www.sos.state.co.us/CCR/'
HEADERS = ('<tr><th>Effective date</th><th>Filing type</th><th>Adopted date</th>'
           '<th>Colorado register publication date</th>'
           '<th>Rulemaking details (edocket tracking #)</th>'
           '<th>Download word version</th></tr>')


def _version(number: str, citation: str) -> str:
    return (f'<table>{HEADERS}<tr><td><a onclick="OpenRuleWindow(\'{number}\', '
            f"'{citation}')\">09/01/2026 (PDF)</a></td><td>Permanent Rule</td>"
            '<td>08/01/2026</td><td>08/10/2026</td><td></td>'
            f'<td><a onclick="OpenRuleWordVersion(\'{number}\', \'{citation}\')">'
            '09/01/2026 (DOCX)</a></td></tr></table>')


def _wrap(text: str) -> bytes:
    return ('<html><body>' + text + '</body></html>').encode()


@pytest.fixture
def packet(tmp_path: Path) -> Fixture:
    """Two complete catalog agencies, three listed rules, one selected complete pair."""
    root = tmp_path / 'input'
    root.mkdir()
    bodies: dict[str, bytes] = {}
    responses: list[dict[str, Any]] = []
    with fitz.open() as pdf:
        pdf.new_page().insert_text((30, 30), 'SYNTHETIC SOURCE ONLY')
        pdf_bytes = pdf.tobytes()

    def add(ident: str, role: str, url: str, body: bytes, parent: str | None) -> None:
        """Bind one nonsecret synthetic receipt to exact fixture source bytes."""
        ref = {'path': 'raw/' + m.sha(body) + '.bin', 'sha256': m.sha(body), 'bytes': len(body)}
        bodies[ref['path']] = body
        responses.append({
            'association_id': ident, 'role': role, 'parent_id': parent, 'body': ref,
            'claim': {'receipt_sha256': '0' * 64, 'requested_url': url,
                      'observed_final_url': url, 'started_at': '2026-09-23T18:00:00Z',
                      'finished_at': '2026-09-23T18:00:01Z', 'http_status': 200,
                      'content_type': 'application/pdf' if role == 'pdf' else 'text/html',
                      'charged_bytes': len(body)}})

    add('welcome', 'welcome', ORIGIN + 'Welcome.do', _wrap(
        'Rules effective on or before 09/23/2026 '
        '<a href="/CCR/NumericalDeptList.do">Catalog</a>'), None)
    agency_urls = {}
    catalog = '<table><tr><td><a name="1000"></a>Example Department</td></tr>'
    for aid in ('132', '133'):
        href = (f'/CCR/NumericalCCRDocList.do?deptID=16&agencyID={aid}'
                '&deptName=1000%20Example%20Department&agencyName=1002%20Agency' + aid)
        agency_urls[aid] = 'https://www.sos.state.co.us' + href
        catalog += f'<tr><td><a href="{href}">1002 Agency{aid}</a></td><td>x</td></tr>'
    add('catalog', 'catalog', ORIGIN + 'NumericalDeptList.do', _wrap(catalog + '</table>'),
        'welcome')
    listing = '<table><tr><th>CCR#</th><th>Title</th></tr>'
    histories = {}
    for number in range(1, 4):
        citation = f'5 CCR 1002-{number}'
        href = (f'/CCR/DisplayRule.do?deptID=16&agencyID=132&ruleId={number}'
                '&action=ruleinfo&seriesNum=' + quote(citation))
        histories[number] = 'https://www.sos.state.co.us' + href
        listing += (f'<tr><td><a href="{href}">{citation}</a></td>'
                    f'<td>Source title {number}</td></tr>')
    add('listing', 'listing', agency_urls['132'], _wrap(listing + '</table>'), 'catalog')
    citation = '5 CCR 1002-1'
    history = (f'<p class="pagehead5">{citation} Source title 1</p>'
               '<b>Current Version</b>' + _version('10', citation)
               + '<b>Archived Versions</b>' + _version('9', citation))
    add('history', 'history', histories[1], _wrap(history), 'listing')
    add('pdf', 'pdf', ORIGIN + 'GenerateRulePdf.do?ruleVersionId=10&fileName=' + quote(citation),
        pdf_bytes, 'history')
    add('word', 'word', ORIGIN + 'GenerateRulePdf.do?type=word&ruleVersionId=10&fileName='
        + quote(citation), b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1SYNTHETIC', 'history')
    plan = {'department_id': '16', 'provenance_sha256': ['1' * 64],
            'selections': [{'agency_id': '132', 'rule_id': '1'}], 'responses': responses}
    _save(root, plan, bodies)
    return root, plan, bodies


def _save(root: Path, plan: dict[str, Any], bodies: dict[str, bytes]) -> str:
    for name, raw in bodies.items():
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_bytes(raw)
    raw = m.encoded(m.Plan.model_validate_json(json.dumps(plan)))
    (root / 'PLAN.json').write_bytes(raw)
    return m.sha(raw)


def _replace(plan: dict[str, Any], bodies: dict[str, bytes], ident: str, raw: bytes) -> None:
    item = next(r for r in plan['responses'] if r['association_id'] == ident)
    ref = {'path': 'raw/' + m.sha(raw) + '.bin', 'sha256': m.sha(raw), 'bytes': len(raw)}
    item['body'] = ref
    item['claim']['charged_bytes'] = len(raw)
    bodies[ref['path']] = raw


def _raw(plan: dict[str, Any], bodies: dict[str, bytes], ident: str) -> bytes:
    response = next(r for r in plan['responses'] if r['association_id'] == ident)
    return bodies[response['body']['path']]


def _derive(plan: dict[str, Any], bodies: dict[str, bytes]) -> m.Capture:
    return m.derive(m.Plan.model_validate_json(json.dumps(plan)), bodies, 'a' * 64)


def _build(packet: Fixture, tmp_path: Path) -> tuple[Path, str]:
    root, plan, bodies = packet
    pin = _save(root, plan, bodies)
    output = tmp_path / 'output'
    manifest = m.build(root, root / 'PLAN.json', output, pin)
    return output, m.sha(m.encoded(manifest))


def _reseal(output: Path) -> str:
    files = [m.Asset(path=p.relative_to(output).as_posix(), bytes=p.stat().st_size,
                     sha256=m.sha(p.read_bytes())) for p in sorted(output.rglob('*'))
             if p.is_file() and p.name != 'MANIFEST.json']
    raw = m.encoded(m.Manifest(files=files))
    (output / 'MANIFEST.json').write_bytes(raw)
    return m.sha(raw)


def test_roundtrip_full_denominators_and_relocation(packet: Fixture, tmp_path: Path) -> None:
    """One rule does not promote two other rules or the unselected agency."""
    output, pin = _build(packet, tmp_path)
    moved = tmp_path / 'relocated'
    shutil.copytree(output, moved)
    record = m.verify(moved, pin)
    assert (record.catalog_agency_count, record.selected_rule_count) == (2, 1)
    assert len(record.agencies[0].rules) == 3
    assert sum(r.selected for r in record.agencies[0].rules) == 1
    assert record.agencies[1].listed_rule_count is None
    assert record.selected_rules[0].versions[1].omission == 'archived_not_selected'
    assert len(record.documents) == 2 and record.documents[0].pages == 1
    assert not record.department_complete and not record.answer_safe
    assert len(record.links) == 5
    public = json.loads((moved / 'PLAN.json').read_bytes())
    assert all(r['body']['path'].startswith('bodies/') for r in public['responses'])
    from geode.pipeline.ccr_current import CCRState
    with pytest.raises(ValidationError):
        CCRState.model_validate_json((moved / 'CAPTURE.json').read_bytes())


def test_future_pair_is_required_and_preserved(packet: Fixture) -> None:
    """Every nonarchived version travels with the whole rule, archive remains omitted."""
    _, plan, bodies = packet
    history = _raw(plan, bodies, 'history').decode().replace(
        '<b>Archived Versions</b>', '<b>Future Versions</b>' + _version('11', '5 CCR 1002-1')
        + '<b>Archived Versions</b>')
    _replace(plan, bodies, 'history', history.encode())
    with pytest.raises(ValueError, match='pair missing'):
        _derive(plan, bodies)
    for old in copy.deepcopy(plan['responses'][-2:]):
        old['association_id'] += '_future'
        for key in ['requested_url', 'observed_final_url']:
            old['claim'][key] = old['claim'][key].replace('ruleVersionId=10', 'ruleVersionId=11')
        plan['responses'].append(old)
    result = _derive(plan, bodies)
    assert len(result.documents) == 4
    assert result.distinct_body_count < result.response_associations
    assert result.selected_rules[0].versions[1].designation == 'future'


@pytest.mark.parametrize('field,value', [
    ('department_id', '99'), ('selections', [{'agency_id': '999', 'rule_id': '1'}]),
    ('selections', [{'agency_id': '132', 'rule_id': '999'}]),
    ('selections', [{'agency_id': '132', 'rule_id': '1'}] * 2),
    ('answer_safe', True), ('unexpected', 'private')])
def test_bad_plan_scope_refused(packet: Fixture, field: str, value: Any) -> None:
    """Unknown identities, duplicate selectors and unsafe promotion are not accepted."""
    _, plan, bodies = packet
    plan[field] = value
    with pytest.raises(ValueError):
        _derive(plan, bodies)


@pytest.mark.parametrize('role', ['catalog', 'listing', 'history', 'pdf', 'word'])
def test_missing_association_refused(packet: Fixture, role: str) -> None:
    """Neither missing discovery nor missing format pairs can certify a selection."""
    _, plan, bodies = packet
    plan['responses'] = [r for r in plan['responses'] if r['role'] != role]
    with pytest.raises(ValueError):
        _derive(plan, bodies)


@pytest.mark.parametrize('ident,replacement', [
    ('welcome', b'<html><body>No cutoff</body></html>'),
    ('listing', b'<html><body><a href="DisplayRule.do">bare anchor</a></body></html>'),
    ('history', b'<html><body>truncated'),
    ('pdf', b'<html>security wall</html>'),
    ('word', b'<html>200 not a Word document</html>')])
def test_rebound_bad_source_refused(packet: Fixture, ident: str, replacement: bytes) -> None:
    """A valid digest cannot make incomplete HTML or a substituted body format valid."""
    _, plan, bodies = packet
    _replace(plan, bodies, ident, replacement)
    with pytest.raises(ValueError):
        _derive(plan, bodies)


@pytest.mark.parametrize('mutation', ['parent', 'role', 'url', 'duplicate_url', 'duplicate_id',
                                     'duplicate_pin', 'interval', 'redirect', 'private_path'])
def test_identity_claim_mutations(packet: Fixture, mutation: str) -> None:
    """Strict role/link/claim admission rejects invented scope before output writes."""
    _, plan, bodies = packet
    item = plan['responses'][-1]
    if mutation == 'parent':
        item['parent_id'] = 'listing'
    elif mutation == 'role':
        item['role'] = 'pdf'
    elif mutation == 'url':
        for key in ['requested_url', 'observed_final_url']:
            item['claim'][key] = item['claim'][key].replace('ruleVersionId=10', 'ruleVersionId=99')
    elif mutation == 'duplicate_url':
        item['claim'] = copy.deepcopy(plan['responses'][-2]['claim'])
    elif mutation == 'duplicate_id':
        item['association_id'] = 'pdf'
    elif mutation == 'duplicate_pin':
        plan['provenance_sha256'] *= 2
    elif mutation == 'interval':
        item['claim']['finished_at'] = '2020-01-01T00:00:00Z'
    elif mutation == 'redirect':
        item['claim']['observed_final_url'] += '&changed=yes'
    else:
        item['claim']['original_path'] = '/private/secret'
    with pytest.raises(ValueError):
        _derive(plan, bodies)


@pytest.mark.parametrize('url', [
    'https://evil.example/CCR/Welcome.do', 'https://www.sos.state.co.us/CCR/Welcome.do#x',
    ORIGIN + 'Welcome.do?a=1&a=2', ORIGIN + 'Welcome.do?a=', ORIGIN + 'Welcome.do?x=a b',
    ORIGIN + 'Welcome.do?x=\\server', 'https://u:p@www.sos.state.co.us/CCR/Welcome.do'])
def test_url_ambiguity_refused(url: str) -> None:
    """URL parsers must not silently trim or reconcile ambiguous supplied claims."""
    with pytest.raises(ValueError):
        m.official_url(url)


def test_pair_missing_from_source_itself_refused(packet: Fixture) -> None:
    """This pair-only contract cannot substitute another adopted-part document."""
    _, plan, bodies = packet
    raw = _raw(plan, bodies, 'history')
    raw = raw.replace(b'<a onclick="OpenRuleWordVersion(\'10\', \'5 CCR 1002-1\')">'
                      b'09/01/2026 (DOCX)</a>', b'')
    _replace(plan, bodies, 'history', raw)
    plan['responses'].pop()
    with pytest.raises(ValueError, match='displayed PDF and Word pair'):
        _derive(plan, bodies)


@pytest.mark.parametrize('mutation', ['extra_archive', 'base', 'duplicate_link', 'parent_later',
                                     'wrong_listing_role', 'wrong_history_role'])
def test_rebound_source_scope_contradictions(packet: Fixture, mutation: str) -> None:
    """Extra associations, altered source resolution and hierarchy mismatches fail closed."""
    _, plan, bodies = packet
    if mutation == 'extra_archive':
        extra = copy.deepcopy(plan['responses'][-2])
        extra['association_id'] = 'archived_pdf'
        for key in ['requested_url', 'observed_final_url']:
            extra['claim'][key] = extra['claim'][key].replace('ruleVersionId=10', 'ruleVersionId=9')
        plan['responses'].append(extra)
    elif mutation == 'base':
        _replace(plan, bodies, 'history', _raw(plan, bodies, 'history').replace(
            b'<body>', b'<body><base href="https://www.sos.state.co.us/">'))
    elif mutation == 'duplicate_link':
        _replace(plan, bodies, 'welcome', _raw(plan, bodies, 'welcome').replace(
            b'</body>', b'<a href="/CCR/NumericalDeptList.do">Other label</a></body>'))
    elif mutation == 'parent_later':
        plan['responses'][1], plan['responses'][2] = plan['responses'][2], plan['responses'][1]
    elif mutation == 'wrong_listing_role':
        plan['responses'][2]['role'] = 'history'
    else:
        plan['responses'][3]['role'] = 'listing'
    with pytest.raises(ValueError):
        _derive(plan, bodies)


def test_input_bytes_pin_and_output_collision(packet: Fixture, tmp_path: Path) -> None:
    """A caller pin is required, buffers are bound, and existing outputs are immutable."""
    root, plan, _ = packet
    output = tmp_path / 'output'
    with pytest.raises(ValueError, match='Plan pin'):
        m.build(root, root / 'PLAN.json', output, 'f' * 64)
    pin = m.sha((root / 'PLAN.json').read_bytes())
    body_path = root / plan['responses'][-1]['body']['path']
    original = body_path.read_bytes()
    body_path.write_bytes(original[:-1] + b'X')
    with pytest.raises(ValueError, match='source identity'):
        m.build(root, root / 'PLAN.json', output, pin)
    body_path.write_bytes(original)
    _build(packet, tmp_path)
    with pytest.raises(ValueError, match='already exists'):
        m.build(root, root / 'PLAN.json', output, pin)


def test_build_uses_captured_buffers_after_read(packet: Fixture, tmp_path: Path,
                                              monkeypatch: pytest.MonkeyPatch) -> None:
    """Subsequent disk mutation cannot alter the bytes already accepted into the capture."""
    root, plan, _ = packet
    body_path = root / plan['responses'][-1]['body']['path']
    real = m.derive

    def mutate_after_capture(*args: Any, **kwargs: Any) -> m.Capture:
        body_path.write_bytes(b'SUBSTITUTED AFTER CAPTURE')
        return real(*args, **kwargs)

    monkeypatch.setattr(m, 'derive', mutate_after_capture)
    output, pin = _build(packet, tmp_path)
    assert m.verify(output, pin).selected_rule_count == 1


@pytest.mark.parametrize('kind', ['symlink', 'fifo', 'parent_symlink'])
def test_nonregular_input_refused(packet: Fixture, tmp_path: Path, kind: str) -> None:
    """FIFO refusal happens before an open can block; symlink parents are never followed."""
    root, plan, _ = packet
    path = root / plan['responses'][-1]['body']['path']
    if kind == 'parent_symlink':
        moved = tmp_path / 'moved'
        (root / 'raw').rename(moved)
        (root / 'raw').symlink_to(moved, target_is_directory=True)
    else:
        path.unlink()
        if kind == 'fifo':
            os.mkfifo(path)
        else:
            path.symlink_to(root / 'PLAN.json')
    with pytest.raises(ValueError):
        m.build(root, root / 'PLAN.json', tmp_path / 'out',
                m.sha((root / 'PLAN.json').read_bytes()))


def test_failed_atomic_build_is_not_resumable(packet: Fixture, tmp_path: Path,
                                             monkeypatch: pytest.MonkeyPatch) -> None:
    """An interruption leaves an incomplete directory and no final manifest."""
    root, _, _ = packet
    output = tmp_path / 'output'
    original = m.atomic_new
    calls = 0

    def fail(path: Path, body: bytes) -> None:
        nonlocal calls
        calls += 1
        if calls == 3:
            raise OSError('fixture interruption')
        original(path, body)

    monkeypatch.setattr(m, 'atomic_new', fail)
    pin = m.sha((root / 'PLAN.json').read_bytes())
    with pytest.raises(OSError):
        m.build(root, root / 'PLAN.json', output, pin)
    assert output.is_dir() and not (output / 'MANIFEST.json').exists()
    with pytest.raises(ValueError, match='already exists'):
        m.build(root, root / 'PLAN.json', output, pin)


@pytest.mark.parametrize('mutation', ['extra', 'missing', 'changed', 'schema', 'capture',
                                     'private', 'symlink', 'directory', 'fifo', 'plan_path'])
def test_closed_capture_mutation_refused(packet: Fixture, tmp_path: Path, mutation: str) -> None:
    """Even resealed dishonest claims or extra private members fail deterministic replay."""
    output, pin = _build(packet, tmp_path)
    if mutation == 'extra':
        (output / 'extra.txt').write_text('unexpected')
    elif mutation == 'missing':
        (output / 'CAPTURE.json').unlink()
    elif mutation == 'changed':
        (output / 'CAPTURE.json').write_text('{}')
    elif mutation == 'schema':
        (output / 'Capture.schema.json').write_text('{}')
        pin = _reseal(output)
    elif mutation == 'capture':
        record = json.loads((output / 'CAPTURE.json').read_bytes())
        record['selected_rule_count'] = 2
        (output / 'CAPTURE.json').write_text(json.dumps(record))
        pin = _reseal(output)
    elif mutation == 'private':
        (output / 'private.json').write_text('{}')
        pin = _reseal(output)
    elif mutation == 'symlink':
        (output / 'extra').symlink_to(output / 'PLAN.json')
    elif mutation == 'directory':
        (output / 'empty').mkdir()
    elif mutation == 'fifo':
        os.mkfifo(output / 'fifo')
    else:
        plan = json.loads((output / 'PLAN.json').read_bytes())
        old = plan['responses'][-1]['body']['path']
        new = 'bodies/renamed.bin'
        (output / old).rename(output / new)
        plan['responses'][-1]['body']['path'] = new
        (output / 'PLAN.json').write_text(json.dumps(plan))
        pin = _reseal(output)
    with pytest.raises((ValueError, FileNotFoundError)):
        m.verify(output, pin)


@pytest.mark.parametrize('cap', ['MAX_INPUT_BYTES', 'MAX_PACKAGE_BYTES', 'MAX_METADATA_BYTES',
                                'MAX_PDF_PAGES', 'MAX_MEMBERS'])
def test_caps_refuse_before_output(packet: Fixture, tmp_path: Path,
                                  monkeypatch: pytest.MonkeyPatch, cap: str) -> None:
    """Bounded inputs, actual closed bytes, pages and member budgets are independent."""
    root, _, _ = packet
    monkeypatch.setattr(m, cap, 0 if cap == 'MAX_PDF_PAGES' else 1)
    with pytest.raises(ValueError):
        m.build(root, root / 'PLAN.json', tmp_path / 'out',
                m.sha((root / 'PLAN.json').read_bytes()))
    assert not (tmp_path / 'out').exists()


def test_cli_json_and_manifest_pin(packet: Fixture, tmp_path: Path,
                                   capsys: pytest.CaptureFixture[str]) -> None:
    """Both CLI paths are offline and report the exact externally pinned closure."""
    root, _, _ = packet
    output = tmp_path / 'cli'
    pin = m.sha((root / 'PLAN.json').read_bytes())
    assert m.main(['build', '--input-root', str(root), '--plan', str(root / 'PLAN.json'),
                   '--output', str(output), '--plan-sha256', pin]) == 0
    result = json.loads(capsys.readouterr().out)
    assert m.main(['verify', '--root', str(output), '--manifest-sha256',
                   result['manifest_sha256']]) == 0
    assert json.loads(capsys.readouterr().out)['department_complete'] is False
    with pytest.raises(ValueError, match='Manifest pin'):
        m.verify(output, 'f' * 64)


def test_sources_reject_conflicting_missing_and_excessive_refs(
        packet: Fixture, monkeypatch: pytest.MonkeyPatch) -> None:
    """Internal replay rebinds every plan asset, independent of filesystem checks."""
    _, plan, bodies = packet
    model = m.Plan.model_validate_json(json.dumps(plan))
    with pytest.raises(ValueError, match='source identity'):
        m.derive(model, {}, 'a' * 64)
    plan['responses'][-1]['body']['path'] = plan['responses'][-2]['body']['path']
    with pytest.raises(ValueError, match='Conflicting'):
        _derive(plan, bodies)
    monkeypatch.setattr(m, 'MAX_INPUT_BYTES', 1)
    with pytest.raises(ValueError, match='budget'):
        m.derive(model, bodies, 'a' * 64)


def test_manifest_members_model_refusals() -> None:
    """Closure cannot self-list or silently ignore duplicate member identities."""
    item = {'path': 'a', 'sha256': '0' * 64, 'bytes': 1}
    with pytest.raises(ValueError):
        m.Manifest.model_validate({'files': [item, item]})
    item['path'] = 'MANIFEST.json'
    with pytest.raises(ValueError):
        m.Manifest.model_validate({'files': [item]})


@pytest.mark.parametrize('target,before,after', [
    ('history', '5 CCR 1002-1 Source title 1', '5 CCR 9999-1 Source title 1'),
    ('history', "OpenRuleWindow('10', '5 CCR 1002-1')", "OpenRuleWindow('10', '5 CCR 9999-1')"),
    ('listing', 'seriesNum=5%20CCR%201002-1', 'seriesNum=5%20CCR%209999-1'),
    ('listing', 'agencyID=132', 'agencyID=133'),
    ('listing', '<td>Source title 1</td>', '<td></td>')])
def test_source_title_citation_and_owner_mutations(
        packet: Fixture, target: str, before: str, after: str) -> None:
    """Rehashing incorrect source identity or incomplete rows cannot satisfy maintained parsers."""
    _, plan, bodies = packet
    raw = _raw(plan, bodies, target)
    assert before.encode() in raw
    _replace(plan, bodies, target, raw.replace(before.encode(), after.encode()))
    with pytest.raises(ValueError):
        _derive(plan, bodies)


def test_null_final_url_and_mixed_observation_dates(packet: Fixture) -> None:
    """Missing old receipt fields and mixed dates remain claims rather than fabricated order."""
    _, plan, bodies = packet
    plan['responses'][-1]['claim']['observed_final_url'] = None
    plan['responses'][-1]['claim']['started_at'] = '2026-09-22T15:00:00Z'
    plan['responses'][-1]['claim']['finished_at'] = '2026-09-22T15:00:01Z'
    record = _derive(plan, bodies)
    assert record.observed_start_claim.day == 22
    assert record.observed_finish_claim.day == 23


def test_resealed_package_total_includes_manifest(packet: Fixture, tmp_path: Path,
                                                  monkeypatch: pytest.MonkeyPatch) -> None:
    """Payloads fitting a cap do not excuse the bytes of the enclosing manifest."""
    output, pin = _build(packet, tmp_path)
    manifest = m.Manifest.model_validate_json((output / 'MANIFEST.json').read_bytes())
    payload_bytes = sum(ref.bytes for ref in manifest.files)
    monkeypatch.setattr(m, 'MAX_PACKAGE_BYTES', payload_bytes)
    with pytest.raises(ValueError, match='including manifest'):
        m.verify(output, pin)


def test_encrypted_pdf_refused(packet: Fixture) -> None:
    """A recognizable encrypted PDF is not a usable structurally parsed source."""
    _, plan, bodies = packet
    with fitz.open() as pdf:
        pdf.new_page()
        raw = pdf.tobytes(encryption=fitz.PDF_ENCRYPT_AES_256,
                          owner_pw='fixture-owner', user_pw='fixture-reader')
    _replace(plan, bodies, 'pdf', raw)
    with pytest.raises(ValueError, match='encrypted'):
        _derive(plan, bodies)


def test_department_identity_is_generic_not_citation_prefix(packet: Fixture) -> None:
    """The selected department follows source URLs, independent of the printed CCR prefix."""
    _, plan, bodies = packet
    plan['department_id'] = '21'
    for response in plan['responses']:
        for key in ['requested_url', 'observed_final_url']:
            response['claim'][key] = response['claim'][key].replace('deptID=16', 'deptID=21')
        if response['role'] in {'catalog', 'listing'}:
            raw = bodies[response['body']['path']].replace(b'deptID=16', b'deptID=21')
            _replace(plan, bodies, response['association_id'], raw)
    result = _derive(plan, bodies)
    assert result.department_id == '21'
    assert result.selected_rules[0].source_citation.startswith('5 CCR')


def test_resealed_undercharged_response_refused(packet: Fixture, tmp_path: Path) -> None:
    """An externally repinned input cannot undercount any retained association's bytes."""
    root, plan, _ = packet
    plan['responses'][-1]['claim']['charged_bytes'] = 1
    raw = (json.dumps(plan, indent=2) + '\n').encode()
    (root / 'PLAN.json').write_bytes(raw)
    with pytest.raises(ValueError, match='Charged bytes'):
        m.build(root, root / 'PLAN.json', tmp_path / 'out', m.sha(raw))
    assert not (tmp_path / 'out').exists()


def test_larger_conservative_charge_is_preserved(packet: Fixture) -> None:
    """A retained-body lower bound does not pretend to reconstruct original wire size."""
    _, plan, bodies = packet
    expected = sum(r['claim']['charged_bytes'] for r in plan['responses']) + 10
    plan['responses'][-1]['claim']['charged_bytes'] += 10
    assert _derive(plan, bodies).charged_response_bytes_claim == expected
