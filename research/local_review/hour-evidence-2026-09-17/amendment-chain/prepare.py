"""Historical local preparation only; no collected code or public requests execute."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup
import jsonschema
import pymupdf

from models import Asset, Audit, Counts, Evidence, Link, Manifest, Source

ROOT = Path(__file__).resolve().parent
SESSION = ROOT.parent
DELIVERY = SESSION / 'sherlock-delivery/SH-CHAIN-2026-09-17-01-20260917T204333Z'
CURL_FIELDS = ['response_code', 'http_code', 'exitcode', 'url_effective', 'num_redirects',
               'ssl_verify_result', 'size_download', 'content_type', 'redirect_url', 'time_total']


def pin(path: str, body: bytes) -> Asset:
    """Record an exact byte identity."""
    return Asset(path=path, sha256=hashlib.sha256(body).hexdigest(), size_bytes=len(body))


def put(path: str, body: bytes) -> Asset:
    """Create one new audit file, refusing overwrite."""
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('xb') as handle:
        handle.write(body)
    return pin(path, body)


def encode(obj: object) -> bytes:
    """Serialize review metadata with stable human-readable formatting."""
    return (json.dumps(obj, ensure_ascii=False, indent=2) + '\n').encode()


def public_copy(path: Path, destination: str) -> Evidence:
    """Preserve hashes while excluding cookies and unnecessary curl address metadata."""
    body = path.read_bytes()
    original = pin(path.relative_to(SESSION).as_posix(), body)
    mode = 'exact'
    transformation = 'Exact unchanged bytes.'
    if 'headers' in path.name:
        lines = body.splitlines(keepends=True)
        kept = []
        removed = 0
        skip_continuation = False
        for line in lines:
            private = bool(re.match(
                rb'(?i)^(set-cookie|cookie|authorization|proxy-authorization):', line))
            if private or (skip_continuation and line[:1] in (b' ', b'\t')):
                removed += 1
                skip_continuation = True
                continue
            skip_continuation = False
            kept.append(line)
        if removed:
            body = b''.join(kept)
            destination = destination.replace('headers.txt', 'headers.public.txt')
            mode = 'public_derivative'
            transformation = ('Removed complete Set-Cookie/Cookie/Authorization/'
                              f'Proxy-Authorization lines and folded continuations: {removed}. '
                              'Other header bytes unchanged; original hash retained only.')
    elif path.name == 'curl.stdout.json':
        metadata = json.loads(body)
        body = encode({key: metadata.get(key) for key in CURL_FIELDS})
        destination = destination.replace('curl.stdout.json', 'curl.public.json')
        mode = 'public_derivative'
        transformation = 'Whitelist curl outcome fields; omit local/remote addresses, ports, '
        transformation += 'certificate material and other unnecessary runtime metadata.'
    return Evidence(original=original, retained=put(destination, body), mode=mode,
                    transformation=transformation)


def main() -> None:
    """Replay delivered evidence and write the finite audit proposal."""
    put('AUDIT.schema.json', encode(Audit.model_json_schema()))
    put('MANIFEST.schema.json', encode(Manifest.model_json_schema()))
    evidence = []
    for file in sorted(DELIVERY.rglob('*')):
        if file.is_file():
            assert not file.is_symlink()
            evidence.append(public_copy(file, 'received/' + file.relative_to(DELIVERY).as_posix()))
    fresh = SESSION / 'atlas-chain-downloads'
    for file in sorted(fresh.rglob('*')):
        if file.is_file():
            assert not file.is_symlink()
            evidence.append(public_copy(file, 'atlas/' + file.relative_to(fresh).as_posix()))
    evidence.append(public_copy(SESSION / 'fetch_chain_documents.py', 'inputs/fetch_chain_documents.py'))
    evidence.append(public_copy(SESSION / 'sherlock-packet/START_HERE.md', 'inputs/START_HERE.md'))
    packet = next(e.retained for e in evidence if e.retained.path == 'inputs/START_HERE.md')
    activation = json.loads((DELIVERY / 'ACTIVATION.json').read_bytes())
    assert activation['packet_start_here_sha256'] == packet.sha256
    inv = json.loads((DELIVERY / 'INVENTORY.json').read_bytes())
    assert inv['excludes'] == ['INVENTORY.json', 'SHA256SUMS.txt']
    actual = {p.relative_to(DELIVERY).as_posix() for p in DELIVERY.rglob('*') if p.is_file()}
    assert actual == {x['path'] for x in inv['files']} | set(inv['excludes'])
    assert len(actual) == 102 and len(inv['files']) == inv['file_count'] == 100
    for item in inv['files']:
        data = (DELIVERY / item['path']).read_bytes()
        assert len(data) == item['bytes'] and hashlib.sha256(data).hexdigest() == item['sha256']
    assert sum(x['bytes'] for x in inv['files']) == inv['total_bytes_inventoried']
    checksums = (DELIVERY / 'SHA256SUMS.txt').read_text().splitlines()
    assert len(checksums) == 100
    for line in checksums:
        sha, path = line.split(None, 1)
        assert hashlib.sha256((DELIVERY / path.lstrip('*')).read_bytes()).hexdigest() == sha
    events = [json.loads((DELIVERY / f'events/A{i:03}.json').read_bytes()) for i in range(1, 21)]
    reduced = [json.loads(line) for line in (DELIVERY / 'logs/attempted_urls.jsonl')
               .read_bytes().splitlines()]
    attempted = json.loads((DELIVERY / 'ATTEMPTED_URLS.json').read_bytes())
    assert len(reduced) == len(attempted) == len(events) == 20
    total = 0
    previous = None
    anchored = []
    by_url = {e['url']: e for e in events}
    for i, event in enumerate(events):
        reserve = json.loads((DELIVERY / f'events/A{i + 1:03}.reserved.json').read_bytes())
        assert reserve['caps_snapshot'] == dict(actions_before=i, targets_before=i,
                                                total_bytes_before=total)
        assert reserve['url'] == event['url'] and reserve['action_id'] == event['action_id']
        assert reserve['reserved_utc'] <= event['start_utc'] <= event['end_utc']
        assert event['end_utc'] < activation['public_stop_utc']
        assert previous is None or previous <= reserve['reserved_utc']
        previous = event['end_utc']
        body = (DELIVERY / event['body_path']).read_bytes()
        assert len(body) == event['retained_bytes'] <= 10_000_000
        assert hashlib.sha256(body).hexdigest() == event['sha256']
        assert event['http_code'] == '200' and event['curl_exit_code'] == 0
        assert not event['truncated'] and not event['followed_redirects']
        assert event['url_effective'] == event['url'] and not event['location_header']
        assert '-L' not in event['curl_argv'] and '--insecure' not in event['curl_argv']
        assert event['curl_argv'][-1] == event['url']
        assert all(event[k] == v for k, v in reduced[i].items())
        assert all(event[k] == attempted[i][k] for k in (
            'action_id', 'url', 'http_code', 'curl_exit_code', 'retained_bytes', 'sha256',
            'start_utc', 'end_utc', 'location_header', 'referrer', 'reason'))
        total += len(body)
        assert total <= 30_000_000
        if event['referrer'] in by_url:
            parent = by_url[event['referrer']]
            soup = BeautifulSoup((DELIVERY / parent['body_path']).read_bytes(), 'html.parser')
            if any(urljoin(parent['url'], a['href']).split('#')[0] == event['url']
                   for a in soup.find_all('a', href=True)):
                anchored.append(event['action_id'])
    assert len(by_url) == 20 and total == 15_776_357
    assert events[2]['sha256'] == activation['pinned_comparison']['25-290_sha256']
    catalog_path = 'bodies/A019.body'
    catalog = (DELIVERY / catalog_path).read_bytes()
    soup = BeautifulSoup(catalog, 'html.parser')
    links = []
    for row in soup.find_all('tr'):
        text = row.get_text(' ', strip=True)
        if re.match(r'^Resolutions (22-401|25-291|26-8)\b', text):
            for anchor in row.find_all('a', href=True):
                links.append(Link(parent_path='received/' + catalog_path,
                                  parent_sha256=hashlib.sha256(catalog).hexdigest(),
                                  raw_href=anchor['href'],
                                  resolved_url=urljoin(events[18]['url'], anchor['href']),
                                  anchor_text=anchor.get_text(' ', strip=True), row_text=text))
    assert len(links) == 3
    assert len(re.findall(rb'25-291', catalog, re.I)) == 1
    assert not re.search(rb'25-291\s+Amended|225096848', catalog, re.I)
    documents = []
    details = [
        ('resolution-22-401', '2022-11-15', '2022-11-16', '222141805',
         'Page1 adopts 2022 Board of Adjustment Bylaws amendments attached as Exhibit A; '
         'recites BOA hearing October26,2022. Page2 is Exhibit A cover only.'),
        ('resolution-25-291', '2025-10-28', '2025-10-29', '225094064',
         'Page1 adds VIII.F Board of Adjustment and X.D order of items; adopts attached '
         'Exhibit A and repeals former rules only to extent inconsistent. Page2 execution '
         'blocks. This is not the different25-291 Amended cited by26-8.'),
        ('resolution-26-8', '2026-01-13', '2026-01-13', '226002910',
         'Page1 cites25-291 Amended reception225096848 on November6,2025, then amends '
         'XI.C absence and XII.D reconsider/rescind. Page2 execution blocks. The cited '
         'amended-version source has not been retrieved or reviewed.'),
    ]
    schema = json.loads((fresh / 'RECEIPT.schema.json').read_bytes())
    for key, execution, recording, reception, observation in details:
        directory = fresh / key
        receipt = json.loads((directory / 'RECEIPT.json').read_bytes())
        jsonschema.Draft202012Validator(schema).validate(receipt)
        metadata = json.loads((directory / 'curl.stdout.json').read_bytes())
        body = (directory / 'response.bin').read_bytes()
        assert body.startswith(b'%PDF-') and len(body) == receipt['body_size_bytes']
        assert hashlib.sha256(body).hexdigest() == receipt['body_sha256']
        assert metadata['response_code'] == receipt['http_status'] == 200
        assert metadata['exitcode'] == receipt['returncode'] == 0
        assert metadata['num_redirects'] == metadata['ssl_verify_result'] == 0
        assert metadata['url_effective'] == receipt['requested_url']
        assert int(metadata['size_download']) == len(body)
        assert receipt['requested_url'] in [x.resolved_url for x in links]
        doc = pymupdf.open(stream=body, filetype='pdf')
        assert len(doc) == receipt['pdf_pages']
        assert all(page.get_text() == '' for page in doc)
        expected = ''.join(f'=== PHYSICAL PAGE {i} ===\n' for i in range(1, len(doc) + 1))
        assert (directory / 'native-all.txt').read_text() == expected
        images = sorted((directory / 'pages').glob('*.png'))
        assert len(images) == 2
        documents.append(Source(
            source_key=key, source=pin('atlas/' + key + '/response.bin', body),
            receipt=pin('atlas/' + key + '/RECEIPT.json', (directory / 'RECEIPT.json').read_bytes()),
            requested_url=receipt['requested_url'],
            root_recorded_started_at=receipt['started_at'],
            root_recorded_completed_at=receipt['completed_at'], http_status=200,
            curl_exit_code=0, redirects=0, reported_ssl_verify_result=0,
            physical_pages=len(doc), native_characters_all_pages=0,
            visually_inspected_pages=[1, 2], unread_pages=list(range(3, len(doc) + 1)),
            inspected_images=[pin('atlas/' + key + '/pages/' + p.name, p.read_bytes())
                              for p in images],
            printed_execution_date=execution, printed_recording_date=recording,
            reception_number=reception, identity_observation=observation,
            signature_qualification='Printed roles and signature graphics observed; identities '
                                    'and legal authentication not certified.'))
    audit = Audit(
        prepared_at=datetime.now(timezone.utc).isoformat(),
        scope='Offline delivered-run audit plus first2pages of each3root-downloaded PDFs only.',
        packet=packet, sherlock_inventory=pin('received/INVENTORY.json',
                                             (DELIVERY / 'INVENTORY.json').read_bytes()),
        evidence=evidence,
        counts=Counts(events=20, distinct_urls=20, retained_response_bytes=total,
                      maximum_response_bytes=max(e['retained_bytes'] for e in events),
                      redirects=0, http_200=20, curl_exit_zero=20,
                      delivered_payloads=102, inventory_listed_payloads=100,
                      valid_inventory_entries=100, valid_checksums=100,
                      deliberate_exclusions=inv['excludes'],
                      first_request_start_claim=events[0]['start_utc'],
                      last_request_end_claim=events[-1]['end_utc'],
                      reservation_replay='pass', shared_log_fields_replay='pass'),
        anchored_event_ids=anchored, search_actions=['A009','A010','A011','A012','A020'],
        catalog_links=links, amended_label_occurrences=0, amended_reception_occurrences=0,
        ordinary_25_291_occurrences=1, sources=documents,
        findings=[
            'All100declared payload hashes/sizes and100checksum entries pass; exact102-file '
            'delivery closure has only the two deliberate self/checksum exclusions.',
            'All20serial reservations, detailed events and shared reduced-log fields agree. '
            'Reported run stayed within30actions/20targets/30MBtotal/10MBresponse caps.',
            'A003 equals pinned25-290 digest. This is exact-byte equality only, not currency. '
            'No new ChapterTwo document was established; older ChapterTwo comparison was '
            'not performed here. Off-chain PDF labels are not content QA.',
            'Fourteen follow-link events have exact observed parent anchors. Four WordPress '
            'search requests are documented searches. A020 base search link is observed but '
            '?searchText=22-401 returns an empty SearchFilters.SearchString form; execution '
            'of that full-text query is not evidenced and no negative-result inference is safe.',
            'Only one25-291label occurs in A019, linking50986. No amended25-291label or '
            'reception225096848 occurs. Unrelated November6date strings are not that source.',
            'Root three receipts bind HTTP200/no redirects/exits0/TLS verify-result0 to exact '
            'retained PDFs:9/32/32pages, all native text empty. Only6of73physical pages viewed.',
            '26-8 cites a different amended25-291record; ordinary50986 PDF is reception225094064, '
            'not225096848. Keep that gap open; no complete amendment-chain conclusion.',
        ],
        limitations=[
            'Sherlock argv/status/time/host details are supplied recorded evidence; Ptolemy '
            'did not witness original execution. They are not relabeled as Atlas downloads.',
            'Atlas receipts are root-run transport evidence separately recorded20:50:15–20Z. '
            'This auditor performed no public requests. No raw archive or canonical intake.',
            'Captured run satisfies actual caps; supplied collector is historical, not approved '
            'reusable guard code. Its truncation path and fixed request caps are not certified.',
            'Raw cookie-bearing headers remain only in original handoffs. Public derivatives '
            'remove private header lines; original hashes/sizes preserve omission provenance. '
            'Curl public summaries omit local/remote addresses and unrelated runtime metadata.',
            'No schema was delivered for Sherlock logs; JSON parse and independently typed '
            'audit/recount checks do not retroactively supply a pre-execution schema.',
            'Printed dates and reception stamps are source assertions.67remaining pages are '
            'unread; empty native text is not empty legal content. No OCR or full73page QA.',
            'Source/caption/context-aware identity check, not blind. No signature authentication, '
            'full legal effect, municipal applicability or current-law certification.',
            'Mac locked and follow-up not sent, according to parent. Last observed standing '
            'down is not an independently verified continuing agent state.',
        ], sherlock_status_basis='parent_reports_last_observed_standing_down')
    put('AUDIT.json', encode(audit.model_dump()))


if __name__ == '__main__':
    main()
