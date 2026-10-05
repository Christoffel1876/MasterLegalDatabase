"""Prepare this new handoff only from fixed tracked inputs and retained web derivatives."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from models import Candidate, Comparison, Event, Manifest, Pin, Queue, Report

BASE = Path(__file__).resolve().parent
REPO = Path('/Users/mcoors/Documents/Project Geode/MasterLegalDatabase')
COMMIT = '06504e53ca64734b05eb2362bd48d04b1f223078'
CONTROLS = [
    'AGENTS.md', '_CONTROL_PLANE/SESSION_START_FRESHNESS.md',
    '_CONTROL_PLANE/MASTER_MANIFEST.json', '_CONTROL_PLANE/SOURCE_FRESHNESS_REPORT.json',
    '_CONTROL_PLANE/FRESHNESS_VERIFICATION_QUEUE.json',
    '_CONTROL_PLANE/FRESHNESS_PRIORITIES.json',
    '_CONTROL_PLANE/SESSION_FRESHNESS_REPORT.schema.json',
    '_CONTROL_PLANE/SOURCE_REGISTRY.json', '_CONTROL_PLANE/LOCAL_SOURCE_REGISTRY.json',
    '_CONTROL_PLANE/MUNICIPAL_SOURCE_REGISTRY.json',
    '_CONTROL_PLANE/REGISTER_REFRESH_STATE.json',
]


def pin(path: str, data: bytes) -> Pin:
    """Bind exact bytes."""
    return Pin(path=path, sha256=hashlib.sha256(data).hexdigest(), size_bytes=len(data))


def read(path: str) -> bytes:
    """Read the pinned tracked blob without using unrelated workspace files."""
    return subprocess.check_output(['git', 'show', f'{COMMIT}:{path}'], cwd=REPO)


def write(path: str, obj: object) -> None:
    """Write a new handoff artifact, refusing replacement."""
    target = BASE / path
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('x', encoding='utf-8') as handle:
        handle.write(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')


def main() -> None:
    """Build the fixed four-action report; no public requests are made here."""
    for name, model in [('REPORT', Report), ('CANDIDATE_QUEUE', Queue),
                        ('FINAL_MANIFEST', Manifest)]:
        write(name + '.schema.json', model.model_json_schema())
    controls = [pin(path, read(path)) for path in CONTROLS]
    policy = json.loads(read(CONTROLS[6]))
    write('policy-contract.json', policy)
    state = json.loads(read('_CONTROL_PLANE/REGISTER_REFRESH_STATE.json'))
    issue_url, issue = next((k, v) for k, v in state['issues'].items()
                           if v['publication_date'] == '2026-09-10')
    issue_ids = set(issue['notice_ids'])
    comparisons = []
    inputs = [
        '_CONTROL_PLANE/LOCAL_DOWNLOAD_MANIFEST.jsonl',
        '_RAW_ARCHIVE/manual_intake/manual_source_intake_manifest.jsonl',
        '_CONTROL_PLANE/MANUAL_SOURCE_INTAKE_LEDGER.jsonl',
        '10_Municipal_Authorities/_index.jsonl', '04_Rulemaking/_index.jsonl',
    ]
    for path in inputs:
        proc = subprocess.Popen(['git', 'show', f'{COMMIT}:{path}'], cwd=REPO,
                                stdout=subprocess.PIPE)
        digest = hashlib.sha256()
        total = 0
        count = 0
        matches = {'el_paso_subject': [], 'arvada_subject': [],
                   'register_issue_ids': [], 'authority_arvada': []}
        assert proc.stdout is not None
        for line in proc.stdout:
            digest.update(line)
            total += len(line)
            if not line.strip():
                continue
            count += 1
            row = json.loads(line)
            rid = str(row.get('id', row.get('record_id', row.get('source_id', count))))
            # Search explicit metadata fields only; random hash fragments are not title matches.
            text = ' '.join(str(row.get(k, '')) for k in (
                'id', 'record_id', 'source_id', 'title', 'official_source_name',
                'source_url', 'requested_url', 'final_url', 'original_filename'))
            authority = row.get('authority_id')
            if re.search(r'(?<!\d)26[-_ ]54(?!\d)|graffiti', text, re.I):
                matches['el_paso_subject'].append(f'{count}:{rid}:{authority}')
            if re.search(r'CB\s*26[-_ ]029|data[-_ ]?cent', text, re.I):
                matches['arvada_subject'].append(f'{count}:{rid}:{authority}')
            if rid in issue_ids:
                matches['register_issue_ids'].append(f'{count}:{rid}')
            if authority == 'CO-MUNICIPAL-ARVADA':
                matches['authority_arvada'].append(f'{count}:{rid}')
        assert proc.wait() == 0
        comparisons.append(Comparison(
            input=Pin(path=path, sha256=digest.hexdigest(), size_bytes=total),
            row_count=count, representation='jsonl_records', matches=matches,
            qualification='Metadata-field search only; authority and catalog records are not '
                          'document matches. Other-authority thematic matches are not duplicates. '
                          'Underlying local bodies and LFS objects were not reopened.'))
    for path in ['08_County_Authorities/_index.jsonl',
                 '_CONTROL_PLANE/LOCAL_REVIEW_QUEUE.jsonl']:
        body = read(path)
        assert body.startswith(b'version https://git-lfs.github.com/spec/v1')
        comparisons.append(Comparison(
            input=pin(path, body), row_count=0, representation='lfs_pointer', matches={},
            qualification='Tracked blob is an LFS pointer, not readable index/review records. '
                          'Zero parsed rows does not mean zero underlying records. ' + body.decode()))
    inv_path = 'research/local_review/manual-source-review-inventory-2026-09-11/inventory.json'
    inv_bytes = read(inv_path)
    inv = json.loads(inv_bytes)
    comparisons.append(Comparison(
        input=pin(inv_path, inv_bytes), row_count=len(inv['sources']),
        representation='json_document', matches={
            'el_paso_ids': [r['record_id'] for r in inv['sources']
                            if r['authority_id'] == 'CO-COUNTY-EL_PASO'],
            'arvada_ids': [r['record_id'] for r in inv['sources']
                           if r['authority_id'] == 'CO-MUNICIPAL-ARVADA']},
        qualification=f"Custody inventory only: {inv['rows_with_review']} scoped review links; "
                      f"{inv['rows_without_review']} unmapped. No source bodies reopened."))
    ledger_path = '_CONTROL_PLANE/LOCAL_COVERAGE_LEDGER.json'
    ledger_bytes = read(ledger_path)
    ledger = json.loads(ledger_bytes)
    comparisons.append(Comparison(
        input=pin(ledger_path, ledger_bytes), row_count=len(ledger['authorities']),
        representation='json_document', matches={},
        qualification='September 10 checklist snapshot; category labels do not certify '
                      'a current complete corpus. No category status was promoted.'))
    urls = [
        'https://www.sos.state.co.us/CCR/RegisterHome.do',
        'https://clerkandrecorder.elpasoco.com/clerk-to-the-board/ordinances/',
        'https://www.arvadaco.gov/245/Meetings-and-Other-Legal-Notices',
        'https://www.sos.state.co.us/CCR/RegisterContents.do?Month=9&Volume=49&Year=2026'
        '&publicationDay=09%2F10%2F2026&yearPublishNumber=17',
    ]
    events = []
    for n, url in enumerate(urls, 1):
        evidence_path = 'evidence/web-first.json' if n < 4 else 'evidence/web-second.json'
        evidence = (BASE / evidence_path).read_bytes()
        observed = json.loads(evidence)
        events.append(Event(
            event_id=f'E{n:03}', operation='click' if n == 4 else 'open',
            requested_url=url, reported_final_url=url.replace('%2F', '/') if n == 4 else url,
            interval_start=observed['start']['current_time'],
            interval_end=observed['end']['current_time'],
            interval_role='tool_batch_wall_clock_not_http_timing',
            representation='web_tool_parsed_page', evidence=pin(evidence_path, evidence)))
    candidates = []
    for cid, owner, authority, label, url, event, layer in [
        ('FRESH-20260917-EPC-26-54', 'El Paso County Clerk and Recorder',
         'CO-COUNTY-EL_PASO', 'Resolution No. 26-54 Control and Prevention of Graffiti',
         urls[1], 'E002', '08_County_Authorities'),
        ('FRESH-20260917-ARVADA-CB26-029', 'City of Arvada', 'CO-MUNICIPAL-ARVADA',
         'CB26-029 Data Centers', urls[2], 'E003', '10_Municipal_Authorities')]:
        candidates.append(Candidate(
            candidate_id=cid, source_owner=owner, source_url=url, possible_layer=layer,
            discovered_date='2026-09-17', change_type='unknown', status='needs_validation',
            confidence=0.9, confidence_scope='catalog_identity_only_not_legal_effect',
            authority_id=authority, observed_label=label, event_ids=[event],
            reason_for_review='Official catalog displays this labeled lead; operative text '
                              'and legal dates were not opened or established.',
            local_comparison='No same-authority exact subject identity found in scanned '
                             'manual/legacy metadata; no candidate body hash is available. '
                             'This is not proof that related law or another alias is absent.',
            next_step='If separately authorized, retain the exact observed linked document '
                      'and adoption/notice context, then compare bytes and subject identity.'))
    candidates.append(Candidate(
        candidate_id='FRESH-20260917-REGISTER-49-17', source_owner='Colorado Secretary of State',
        source_url=urls[3], possible_layer='04_Rulemaking', discovered_date='2026-09-17',
        change_type='unknown', status='duplicate', confidence=1.0,
        confidence_scope='catalog_identity_only_not_legal_effect', authority_id='CO-STATE-SOS',
        observed_label='September 10, 2026, 49 CR 17', event_ids=['E001', 'E004'],
        reason_for_review='High-priority Register check; displayed issue already represented.',
        local_comparison=f'Issue identity matches REGISTER_REFRESH_STATE with '
                         f'{len(issue_ids)} notice IDs and recorded source SHA '
                         f"{issue['source_sha256']}; all IDs compared to rulemaking index. "
                         'Query ordering/URL encoding differs; no new byte-equality claim.',
        next_step='No duplicate intake. Preserve future effective-date distinctions; '
                  'no new collector activation follows from this report.'))
    report = Report(
        report_id='PTOLEMY-FRESHNESS-2026-09-17', session_date='2026-09-17',
        prepared_at=datetime.now(timezone.utc).isoformat(), baseline_commit=COMMIT,
        sources_checked=events, candidates=candidates, controls=controls,
        comparisons=comparisons, public_action_count=len(events),
        findings=[
            'The saved freshness report was generated August 11 without network refresh; '
            'its fresh/age-zero labels are historical, not September 17 verification.',
            'Register September 10 issue is already indexed; the parsed contents list future '
            'effective dates including September 30, October 1 and December 31, 2026. '
            'Those are publisher claims, not independently reviewed operative dates.',
            'Two county/municipal catalog leads require document-level validation. '
            'Arvada municipal ownership remains separate from Jefferson and Adams Counties.',
            'No official original was downloaded, no candidate text was treated as current '
            'law, and no old queue or automation was activated.',
        ],
        unchecked_scope=[
            'Linked local document bodies, adoption/execution instruments and complete histories.',
            'All other state, county, municipal and district sources.',
            'Unmerged branches, prior external handoffs and working assignments.',
            'Underlying LFS bodies and original Windows-path archives.',
        ],
        limitations=[
            'Four deliberate public actions across three subjects; no broad crawl.',
            'Retained evidence is parsed web-tool output with cached crawl labels today/yesterday. '
            'Tool batch times are not HTTP request times; status, response headers and source '
            'body hashes are unavailable. No fresh exact-body identity is asserted.',
            'Metadata nonmatch is not source absence, completeness or legal novelty.',
            'The repository report-schema file is a field/enumeration policy descriptor. '
            'This packet supplies actual strict Pydantic-generated JSON Schemas and checks '
            'the descriptor required fields/enums explicitly.',
            'Candidates are a handoff-only proposal, not canonical queue entries or tasks.',
        ])
    assert set(policy['required_fields']) <= report.model_dump().keys()
    for candidate in candidates:
        assert set(policy['candidate_required_fields']) <= candidate.model_dump().keys()
        assert candidate.status in policy['allowed_statuses']
        assert candidate.change_type in policy['allowed_change_types']
    write('REPORT.json', report.model_dump())
    write('CANDIDATE_QUEUE.json', Queue(candidates=candidates[:2]).model_dump())


if __name__ == '__main__':
    main()
