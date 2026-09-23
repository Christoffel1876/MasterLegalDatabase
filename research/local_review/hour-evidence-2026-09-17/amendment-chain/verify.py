"""Portable, offline public-scope audit verifier; never executes received collectors."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup
import jsonschema
import pymupdf

from models import Asset, Audit, Manifest


def require(condition: bool, message: str) -> None:
    """Reject an inconsistent binding."""
    if not condition:
        raise ValueError(message)


def digest(data: bytes) -> str:
    """Calculate an exact source/evidence digest."""
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    """Check closure, delivered count equations, body and limited-source evidence."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--original-session', type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    manifest = Manifest.model_validate_json((root / 'MANIFEST.json').read_bytes())
    require(manifest.exclusions == ['MANIFEST.json'], 'Exclusion mismatch')
    paths = {a.path for a in manifest.files}
    require(len(paths) == len(manifest.files), 'Duplicate path')
    actual = set()
    for p in root.rglob('*'):
        require(not p.is_symlink(), 'Symlink refused')
        if p.is_file():
            actual.add(p.relative_to(root).as_posix())
    require(actual == paths | {'MANIFEST.json'}, 'Closed membership differs')
    captured = {}
    for ref in manifest.files:
        p = Path(ref.path)
        require(not p.is_absolute() and '..' not in p.parts, 'Unsafe path')
        data = (root / p).read_bytes()
        require(len(data) == ref.size_bytes and digest(data) == ref.sha256, 'Payload differs')
        captured[ref.path] = data
    audit = Audit.model_validate_json(captured['AUDIT.json'])
    for name, model in [('AUDIT', Audit), ('MANIFEST', Manifest)]:
        require(json.loads(captured[name + '.schema.json']) == model.model_json_schema(),
                'Schema companion differs')
    originals = {}
    for e in audit.evidence:
        data = captured[e.retained.path]
        require(len(data) == e.retained.size_bytes and digest(data) == e.retained.sha256,
                'Evidence derivative differs')
        originals[e.original.path] = e.original
        if e.mode == 'exact':
            require(len(data) == e.original.size_bytes and digest(data) == e.original.sha256,
                    'Exact evidence differs')
        if 'headers' in e.retained.path:
            require(not re.search(rb'(?im)^(set-cookie|cookie|authorization|proxy-authorization):',
                                  data), 'Private header retained')
        if args.original_session:
            original = args.original_session / e.original.path
            require(not original.is_symlink(), 'Original symlink')
            raw = original.read_bytes()
            require(len(raw) == e.original.size_bytes and digest(raw) == e.original.sha256,
                    'Original changed')
            if e.mode == 'public_derivative' and 'headers' in e.retained.path:
                lines = []
                skip = False
                for line in raw.splitlines(keepends=True):
                    private = bool(re.match(
                        rb'(?i)^(set-cookie|cookie|authorization|proxy-authorization):', line))
                    if private or (skip and line[:1] in (b' ', b'\t')):
                        skip = True
                        continue
                    skip = False
                    lines.append(line)
                require(b''.join(lines) == data, 'Header transformation differs')
            if e.mode == 'public_derivative' and 'curl.public' in e.retained.path:
                public = json.loads(data)
                full = json.loads(raw)
                require(all(full.get(k) == v for k, v in public.items()),
                        'Curl public fields differ')
    inventory = json.loads(captured['received/INVENTORY.json'])
    delivery_prefix = 'sherlock-delivery/SH-CHAIN-2026-09-17-01-20260917T204333Z/'
    require(inventory['excludes'] == ['INVENTORY.json', 'SHA256SUMS.txt'], 'Delivery exclusions')
    require(len(inventory['files']) == 100, 'Inventory count')
    for item in inventory['files']:
        ref = originals[delivery_prefix + item['path']]
        require(ref.sha256 == item['sha256'] and ref.size_bytes == item['bytes'],
                'Delivered inventory binding differs')
    checksum_lines = captured['received/SHA256SUMS.txt'].decode().splitlines()
    require(len(checksum_lines) == 100, 'Checksum count')
    for line in checksum_lines:
        sha, path = line.split(None, 1)
        require(originals[delivery_prefix + path.lstrip('*')].sha256 == sha,
                'Checksum differs from original binding')
    events = [json.loads(captured[f'received/events/A{i:03}.json']) for i in range(1, 21)]
    reduced = [json.loads(x) for x in captured['received/logs/attempted_urls.jsonl'].splitlines()]
    total = 0
    previous = None
    for i, event in enumerate(events):
        reserve = json.loads(captured[f'received/events/A{i + 1:03}.reserved.json'])
        require(reserve['caps_snapshot'] == dict(actions_before=i, targets_before=i,
                                                total_bytes_before=total), 'Reservation differs')
        require(reserve['reserved_utc'] <= event['start_utc'] <= event['end_utc']
                < '2026-09-17T21:10:00Z', 'Time ordering differs')
        require(previous is None or previous <= reserve['reserved_utc'], 'Serial order differs')
        previous = event['end_utc']
        body = captured['received/' + event['body_path']]
        require(len(body) == event['retained_bytes'] <= 10000000
                and digest(body) == event['sha256'], 'Response binding differs')
        total += len(body)
        require(total <= 30000000, 'Total cap')
        require(all(event[k] == v for k, v in reduced[i].items()), 'Reduced log differs')
    require(total == audit.counts.retained_response_bytes == 15776357, 'Byte count')
    require(len({e['url'] for e in events}) == audit.counts.distinct_urls == 20, 'Target count')
    require(max(e['retained_bytes'] for e in events) == audit.counts.maximum_response_bytes,
            'Maximum response')
    for link in audit.catalog_links:
        data = captured[link.parent_path]
        require(digest(data) == link.parent_sha256, 'Catalog hash')
        soup = BeautifulSoup(data, 'html.parser')
        require(any(r.get_text(' ', strip=True) == link.row_text
                    and any(a.get('href') == link.raw_href
                            for a in r.find_all('a', href=True)) for r in soup.find_all('tr')),
                'Catalog row/anchor missing')
        require(urljoin(events[18]['url'], link.raw_href) == link.resolved_url, 'URL resolution')
    catalog = captured['received/bodies/A019.body']
    require(len(re.findall(rb'25-291', catalog, re.I)) == 1, 'Ordinary label count')
    require(not re.search(rb'25-291\s+Amended|225096848', catalog, re.I), 'Amended-gap changed')
    for source in audit.sources:
        body = captured[source.source.path]
        require(digest(body) == source.source.sha256, 'Root source hash')
        doc = pymupdf.open(stream=body, filetype='pdf')
        require(len(doc) == source.physical_pages, 'Page count')
        require(all(p.get_text() == '' for p in doc), 'Native content changed')
        require(source.visually_inspected_pages == [1, 2]
                and source.unread_pages == list(range(3, len(doc) + 1)), 'Review scope')
        receipt = json.loads(captured[source.receipt.path])
        jsonschema.Draft202012Validator(
            json.loads(captured['atlas/RECEIPT.schema.json'])).validate(receipt)
        require(receipt['body_sha256'] == digest(body)
                and receipt['body_size_bytes'] == len(body), 'Receipt body differs')
        public = json.loads(captured[f'atlas/{source.source_key}/curl.public.json'])
        require(public['response_code'] == public['http_code'] == 200
                and public['exitcode'] == public['num_redirects']
                == public['ssl_verify_result'] == 0, 'Root curl result differs')
        require(public['url_effective'] == source.requested_url
                and int(public['size_download']) == len(body), 'Root curl source differs')
    require(sum(s.physical_pages for s in audit.sources) == 73, 'Physical scope')
    sys.stdout.write('PASS: public audit closure, 20-event caps, catalog links, three root '
                     'source receipts; six-page human scope and currentness limits preserved.\n')


if __name__ == '__main__':
    main()
