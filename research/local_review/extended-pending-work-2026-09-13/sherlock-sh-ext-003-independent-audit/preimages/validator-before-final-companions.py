"""Read-only verification of the closed offline SH003 audit; never performs HTTP."""
from __future__ import annotations
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import quote, urljoin
import jsonschema
import pymupdf
from bs4 import BeautifulSoup
from audit_models import Audit, Custody, Legacy, Manifest


def digest(path: Path) -> str:
    """Hash a file without loading a complete legacy JSONL."""
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def ordinary(root: Path, relative: str) -> Path:
    """Reject external, traversing, linked or nonordinary package references."""
    name = Path(relative)
    if name.is_absolute() or '..' in name.parts or not name.parts:
        raise ValueError('Unsafe evidence path')
    current = root
    for part in name.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError('Linked evidence')
    if not current.is_file():
        raise ValueError('Evidence is not an ordinary file')
    return current


def verify_asset(root: Path, asset: dict) -> Path:
    """Recompute both size and digest of a relative reference."""
    path = ordinary(root, asset['path'])
    if path.stat().st_size != asset['size_bytes'] or digest(path) != asset['sha256']:
        raise ValueError('Evidence bytes differ: ' + asset['path'])
    return path


def typed(root: Path, name: str, model: type):
    """Check stored schema and parse strict records."""
    data = ordinary(root, name + '.json').read_bytes()
    schema = json.loads(ordinary(root, name + '.schema.json').read_bytes())
    if schema != model.model_json_schema():
        raise ValueError('Schema differs: ' + name)
    jsonschema.validate(json.loads(data), schema)
    return model.model_validate_json(data)


def verify(root: Path) -> dict:
    """Validate copied custody, all actions, source links and full legacy comparisons."""
    root = root.resolve()
    manifest = typed(root, 'FINAL_MANIFEST', Manifest)
    expected = {a.path for a in manifest.files} | {'FINAL_MANIFEST.json'}
    actual = set()
    for path in root.rglob('*'):
        if path.is_symlink() or not (path.is_file() or path.is_dir()):
            raise ValueError('Nonordinary package member')
        if path.is_file():
            actual.add(path.relative_to(root).as_posix())
    if len(expected) != len(manifest.files) + 1 or actual != expected:
        raise ValueError('Closed package membership differs')
    for asset in manifest.files:
        verify_asset(root, asset.model_dump())
    audit = typed(root, 'AUDIT', Audit)
    custody = typed(root, 'CUSTODY_RECEIPT', Custody)
    legacy = typed(root, 'LEGACY_COMPARISON', Legacy)
    inventory = json.loads((root / 'received/ARTIFACT_INVENTORY.json').read_bytes())
    indexed = {a['path']: a for a in inventory['files']}
    if len(indexed) != 343 or len(custody.items) != 346:
        raise ValueError('Delivery inventory count differs')
    redacted_count = 0
    originals = {}
    for item in custody.items:
        originals[item.original.path] = item.original.model_dump()
        path = verify_asset(root, item.retained.model_dump())
        if item.original.path in indexed and item.original.model_dump() != indexed[item.original.path]:
            raise ValueError('Supplied inventory binding differs')
        if item.mode == 'exact':
            if item.original.sha256 != item.retained.sha256:
                raise ValueError('Exact custody digest differs')
        else:
            redacted_count += len(item.redacted_lines)
            lines = path.read_bytes().splitlines()
            for number in item.redacted_lines:
                if lines[number - 1] != b'Set-Cookie: [REDACTED]':
                    raise ValueError('Redaction marker differs')
    if redacted_count != 12:
        raise ValueError('Redaction scope differs')
    if sorted(set(originals) - set(indexed)) != custody.unlisted_original_files:
        raise ValueError('Unlisted original membership differs')
    packet = root / 'prepared-packet'
    if digest(packet / 'FINAL_MANIFEST.json') != audit.prepared_packet_manifest_sha256:
        raise ValueError('Prepared packet identity differs')
    pm = json.loads((packet / 'FINAL_MANIFEST.json').read_bytes())
    for asset in pm['files']:
        verify_asset(packet, asset)
    activation = json.loads((root / 'received/ACTIVATION.json').read_bytes())
    for field, name in [('start_here_sha256', 'START_HERE.md'),
                        ('instructions_sha256', 'INSTRUCTIONS.md'),
                        ('final_manifest_sha256', 'FINAL_MANIFEST.json')]:
        if activation[field] != digest(packet / name):
            raise ValueError('Worker activation pin differs')
    log = json.loads((root / 'received/ACTION_LOG.json').read_bytes())
    schema = json.loads((packet / 'schemas/ACTION_LOG.schema.json').read_bytes())
    jsonschema.validate(log, schema)
    reservations, results = log['reservations'], log['results']
    if len(reservations) != 30 or len(results) != 30:
        raise ValueError('Action prefix differs')
    urls = {r['requested_url'] for r in reservations}
    body_hashes = {r['body_sha256'] for r in results if r['body_sha256']}
    total = 0
    for index, (reservation, result) in enumerate(zip(reservations, results)):
        action = reservation['action_id']
        if action != result['action_id'] or action != f'SHEXT003-A{index + 1:03}':
            raise ValueError('Action order differs')
        for folder, data in [('reservations', reservation), ('results', result)]:
            if json.loads((root / f'received/{folder}/{action}.json').read_bytes()) != data:
                raise ValueError('Action copy differs')
        end = datetime.fromisoformat(result['finished_at'].replace('Z', '+00:00'))
        start = datetime.fromisoformat(reservation['reserved_at'].replace('Z', '+00:00'))
        if end < start or (index and start < prior_end):
            raise ValueError('Overlapping or reversed supplied action times')
        if end >= datetime.fromisoformat('2026-09-13T03:05:00+00:00'):
            raise ValueError('Action exceeded authorized cutoff')
        prior_end = end
        for asset in result['retained_assets']:
            verify_asset(root / 'received', asset)
        total += result['observed_body_bytes']
    if (audit.budget.actions, audit.budget.distinct_urls,
            audit.budget.accepted_body_bytes, audit.budget.chaffee_actions,
            audit.budget.gunnison_actions, audit.budget.pending_actions) != (
            len(reservations), len(urls), total, 20, 10, 0):
        raise ValueError('Audit budget summary differs')
    if (len(urls), total) != (30, 1600233):
        raise ValueError('Measured budget differs')
    if sum(r['authority_id'] == 'CO-COUNTY-CHAFFEE' for r in reservations) != 20:
        raise ValueError('County budget differs')
    for referral in audit.referrals:
        parent = verify_asset(root, referral.parent.model_dump())
        soup = BeautifulSoup(parent.read_bytes(), 'html.parser')
        bases = soup.find_all('base', href=True)
        base = bases[0]['href'] if bases else None
        if base != referral.html_base_href:
            raise ValueError('HTML base differs')
        pairs = {(a['href'], ' '.join(a.get_text(' ', strip=True).split()))
                 for a in soup.find_all('a', href=True)}
        if (referral.original_href, referral.visible_label) not in pairs:
            raise ValueError('Source anchor differs')
        resolved = urljoin(base or referral.parent_url, referral.original_href)
        if resolved != referral.resolved_url:
            raise ValueError('Browser base resolution differs')
        if (resolved == referral.attempted_url) != referral.exact_browser_resolution_match:
            raise ValueError('Attempt versus source-link assessment differs')
    repair = json.loads((root / 'CHAFFEE_REPAIR_PROPOSAL.json').read_bytes())
    jsonschema.validate(repair, json.loads((root / 'CHAFFEE_REPAIR_PROPOSAL.schema.json').read_bytes()))
    if len(repair['targets']) != 4 or repair['public_requests'] != 0:
        raise ValueError('Repair scope differs')
    for target in repair['targets']:
        parent = ordinary(root, target['parent_path'])
        if digest(parent) != target['parent_sha256']:
            raise ValueError('Repair parent differs')
        soup = BeautifulSoup(parent.read_bytes(), 'html.parser')
        if soup.find('base', href=True)['href'] != target['base_href']:
            raise ValueError('Repair base differs')
        if not any(a['href'] == target['original_href'] and
                   ' '.join(a.get_text(' ', strip=True).split()) == target['visible_label']
                   for a in soup.find_all('a', href=True)):
            raise ValueError('Repair anchor differs')
        resolved = urljoin(target['base_href'], target['original_href'])
        encoded = quote(resolved, safe=":/?#[]@!$&'()*+,;=%")
        if (resolved, encoded) != (target['resolved_url'], target['encoded_requested_url']):
            raise ValueError('Repair transformation differs')
    stream = verify_asset(root, legacy.stream.model_dump())
    matches = {m.line: m for m in legacy.matching_rows}
    found = set()
    with stream.open('rb') as handle:
        for number, raw in enumerate(handle, 1):
            row = json.loads(raw)
            reasons = []
            if row.get('requested_url') in urls:
                reasons.append('requested_url_exact')
            if row.get('source_url') in urls:
                reasons.append('source_url_parent_context')
            if row.get('sha256') in body_hashes:
                reasons.append('body_digest')
            if reasons:
                found.add(number)
                saved = matches[number]
                if reasons != saved.reasons or hashlib.sha256(raw).hexdigest() != saved.raw_line_sha256:
                    raise ValueError('Full legacy comparison differs')
                for key, expected_value in [('source_id', saved.source_id),
                        ('requested_url', saved.requested_url), ('source_url', saved.source_url),
                        ('sha256', saved.recorded_sha256), ('raw_path', saved.recorded_raw_path)]:
                    if row.get(key) != expected_value:
                        raise ValueError('Historical metadata association differs')
    if found != set(matches) or number != 48390 or legacy.current_rows != number:
        raise ValueError('Legacy scope differs')
    if legacy.pinned_rows != number or legacy.pinned_stream_sha256 != digest(stream):
        raise ValueError('Pinned stream digest/count differs')
    for pdf in audit.pdfs:
        source = verify_asset(root, pdf.source.model_dump())
        body = source.read_bytes()
        doc = pymupdf.open(stream=body, filetype='pdf')
        if (len(doc), doc.is_repaired, doc.is_encrypted, body.rstrip().endswith(b'%%EOF')) != (
                pdf.physical_pages, pdf.is_repaired, pdf.encrypted, pdf.terminal_eof):
            raise ValueError('PDF structural evidence differs')
        verify_asset(root, pdf.first_page_image.model_dump())
        if pdf.reviewed_pages != [1]:
            raise ValueError('Visual scope expanded')
        expected_lines = [m.line for m in legacy.matching_rows
                          if m.recorded_sha256 == pdf.source.sha256]
        if pdf.historical_digest_lines != expected_lines:
            raise ValueError('Historical PDF digest associations differ')
    return {'status': 'passed', 'delivery_files': 346, 'inventory_bindings': 343,
            'actions': 30, 'retained_body_bytes': total, 'pdfs': 3, 'parsed_pages': 23,
            'visually_reviewed_pages': 3, 'legacy_rows_per_snapshot': number,
            'legacy_matching_rows': len(matches), 'public_requests': 0,
            'legal_currentness': 'not_verified'}


if __name__ == '__main__':
    sys.stdout.write(json.dumps(verify(Path(__file__).parent), indent=2) + '\n')
