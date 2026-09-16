"""Portable custody verification; optional full legacy replay is local and read-only."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
from urllib.parse import unquote, urljoin

from bs4 import BeautifulSoup
import jsonschema
import pymupdf

from audit_models import Asset, Audit, IntakeRecommendation, Manifest

ROOT = Path(__file__).resolve().parent


def asset_path(root: Path, ref: Asset) -> Path:
    """Reject escapes/symlinks and verify one immutable payload before consumption."""
    relative = Path(ref.path)
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('Unsafe evidence path')
    path = root / relative
    if any(p.is_symlink() for p in [path, *path.parents]) or not path.is_file():
        raise ValueError('Nonordinary evidence path')
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    if digest != ref.sha256 or path.stat().st_size != ref.size_bytes:
        raise ValueError('Changed evidence: ' + ref.path)
    return path


def validate(root: Path, check_manifest: bool = True, repository: Path | None = None) -> Audit:
    """Verify measured custody and metadata; never infer source content or legal status."""
    if check_manifest:
        manifest = Manifest.model_validate_json((root / 'FINAL_MANIFEST.json').read_bytes())
        expected = {a.path for a in manifest.files} | {'FINAL_MANIFEST.json'}
        actual = set()
        for path in root.rglob('*'):
            if path.is_symlink() or not (path.is_file() or path.is_dir()):
                raise ValueError('Nonordinary closed member')
            if path.is_file():
                actual.add(path.relative_to(root).as_posix())
        if actual != expected or len(expected) != len(manifest.files) + 1:
            raise ValueError('Closed audit membership differs')
        for item in manifest.files:
            asset_path(root, item)
    for name, model in [('AUDIT', Audit), ('INTAKE_RECOMMENDATION', IntakeRecommendation)]:
        if json.loads((root / (name + '.schema.json')).read_bytes()) != model.model_json_schema():
            raise ValueError('Exported schema differs')
    audit = Audit.model_validate_json((root / 'AUDIT.json').read_bytes())
    recommendation = IntakeRecommendation.model_validate_json(
        (root / 'INTAKE_RECOMMENDATION.json').read_bytes())
    custody = json.loads((root / 'CUSTODY_RECEIPT.json').read_bytes())
    jsonschema.validate(custody, json.loads((root / 'CUSTODY_RECEIPT.schema.json').read_bytes()))
    for row in custody['assets']:
        asset_path(root, Asset(path=row['preserved_path'], sha256=row['sha256'],
                               size_bytes=row['size_bytes']))
    inventory = json.loads((root / 'received/ARTIFACT_INVENTORY.json').read_bytes())
    if len(inventory['files']) != 25:
        raise ValueError('Original inventory scope differs')
    names = set()
    for row in inventory['files']:
        if row['path'] in names:
            raise ValueError('Duplicate original inventory path')
        names.add(row['path'])
        asset_path(root / 'received', Asset.model_validate(row))
    actual = {p.relative_to(root / 'received').as_posix()
              for p in (root / 'received').rglob('*') if p.is_file()}
    if actual - names != {'ARTIFACT_INVENTORY.json', 'hash-summary.txt'}:
        raise ValueError('Original inventory exclusions differ')
    activation = json.loads((root / 'received/ACTIVATION.json').read_bytes())
    for ref, key in [(audit.authorization, 'start_here_sha256'),
                     (audit.directed_proposal, 'directed_proposal_sha256'),
                     (audit.parent_manifest, 'audit_manifest_sha256')]:
        asset_path(root, ref)
        if ref.sha256 != activation[key]:
            raise ValueError('Authorization pin differs')
    proposal = json.loads(asset_path(root, audit.directed_proposal).read_bytes())
    if (proposal['max_public_actions'], proposal['max_distinct_urls'],
        proposal['max_source_bytes'], proposal['max_total_body_bytes']) != (
            6, 4, 10_000_000, 20_000_000):
        raise ValueError('Authorized budget differs')
    log = json.loads((root / 'received/ACTION_LOG.json').read_bytes())
    if len(audit.events) != 2 or len(log['reservations']) != 2 or len(log['results']) != 2:
        raise ValueError('Recorded action scope differs')
    total = 0
    previous_finish = None
    for event, reserve, result, target in zip(
            audit.events, log['reservations'], log['results'], proposal['targets']):
        if json.loads(asset_path(root, event.reservation).read_bytes()) != reserve:
            raise ValueError('Reservation differs from aggregate log')
        if json.loads(asset_path(root, event.result).read_bytes()) != result:
            raise ValueError('Result differs from aggregate log')
        if event.requested_url != target['url'] or event.requested_url != reserve['requested_url']:
            raise ValueError('Unapproved exact target')
        if (event.reported_http_status, event.reported_final_url, event.reported_visible_redirects,
            event.body.sha256, event.body.size_bytes) != (
                result['observed_http_status'], result['observed_final_url'],
                result['visible_redirect_urls'], result['body_sha256'], result['size_bytes']):
            raise ValueError('Reported event binding differs')
        start = datetime.fromisoformat(reserve['reserved_at'])
        finish = datetime.fromisoformat(result['finished_at'])
        if (start, finish) != (event.reported_reserved_at, event.reported_finished_at):
            raise ValueError('Reported event times differ')
        if start > finish or (previous_finish and previous_finish > start):
            raise ValueError('Recorded serial closure differs')
        previous_finish = finish
        if finish >= datetime(2026, 9, 13, 2, 15, tzinfo=timezone.utc):
            raise ValueError('Recorded research deadline exceeded')
        body = asset_path(root, event.body).read_bytes()
        if body != asset_path(root, event.byte_identical_duplicate).read_bytes():
            raise ValueError('Duplicate body is not identical')
        total += len(body)
        headers = json.loads(asset_path(root, event.headers).read_bytes())
        if (headers['requested_url'], headers['curl_meta']['final_url'],
            int(headers['curl_meta']['http_code']), int(headers['curl_meta']['size_download'])) != (
                event.requested_url, event.reported_final_url, event.reported_http_status, len(body)):
            raise ValueError('Supplied HTTP metadata differs')
        public = headers['headers']
        if sorted(public) != event.observed_header_names:
            raise ValueError('Header-name scope differs')
        if any(k.lower() in {'set-cookie', 'cookie', 'authorization', 'proxy-authorization',
                              'x-api-key'} for k in public):
            raise ValueError('Private header present')
        if 'content-length' in public and int(public['content-length']) != len(body):
            raise ValueError('Content length differs')
        if event.retained_role == 'received_pdf':
            if not body.startswith(b'%PDF-') or not body.rstrip().endswith(b'%%EOF'):
                raise ValueError('PDF envelope differs')
            with pymupdf.open(stream=body, filetype='pdf') as pdf:
                if pdf.page_count != 2 or pdf.is_encrypted or pdf.is_repaired:
                    raise ValueError('PDF structure differs')
            if event.structural_pdf_pages != 2 or event.reported_http_status != 200:
                raise ValueError('PDF role differs')
        else:
            soup = BeautifulSoup(body, 'html.parser')
            title = soup.title.get_text(' ', strip=True) if soup.title else None
            if title != event.html_title or event.reported_http_status != 403:
                raise ValueError('Denied-body role differs')
    if total != 81082 or audit.retained_response_body_bytes != total:
        raise ValueError('Retained body total differs')
    if audit.delivery_captured_at >= datetime(2026, 9, 13, 2, 25, tzinfo=timezone.utc):
        raise ValueError('Audit did not capture delivery by report cutoff')
    for referral, target in zip(audit.referrals, proposal['targets']):
        soup = BeautifulSoup(asset_path(root, referral.parent).read_bytes(), 'html.parser')
        matches = [a for a in soup.find_all('a', href=True)
                   if a['href'] == referral.exact_href and
                   ' '.join(a.get_text(' ', strip=True).split()) == referral.exact_label]
        if len(matches) != 1 or referral.anchor_match_count != 1:
            raise ValueError('Exact official-parent anchor differs')
        if urljoin(referral.parent_url, referral.exact_href) != target['url']:
            raise ValueError('Resolved official-parent URL differs')
        if referral.resolved_url != target['url']:
            raise ValueError('Referral target differs')
    rasters = json.loads((root / 'received/derived/SHEXT002-A001_rasters.json').read_bytes())
    if [p['page'] for p in rasters['pages']] != [1, 2]:
        raise ValueError('Declared raster page scope differs')
    for page in rasters['pages']:
        raw = root / 'received' / page['path']
        if hashlib.sha256(raw.read_bytes()).hexdigest() != page['sha256']:
            raise ValueError('Raster bytes differ')
        pix = pymupdf.Pixmap(str(raw))
        if (pix.width, pix.height) != (page['w'], page['h']):
            raise ValueError('Raster dimensions differ')
    for current in audit.current_intake:
        path = asset_path(root, current.file)
        count = hashes = urls = ids = 0
        with path.open('rb') as handle:
            for count, line in enumerate(handle, 1):
                row = json.loads(line)
                hashes += row.get('sha256') == audit.events[0].body.sha256
                urls += row.get('official_source_url') == audit.events[0].requested_url
                ids += row.get('record_id') == current.proposed_source_id
        if (count, hashes, urls, ids) != (current.rows, current.sha256_matches,
                                         current.exact_url_matches, current.proposed_id_matches):
            raise ValueError('Current intake summary differs')
    for legacy in audit.legacy:
        path = asset_path(root, legacy.matching_original_lines)
        if path.stat().st_size or legacy.original_line_numbers or any([
                legacy.exact_url_field_matches, legacy.digest_matches,
                legacy.decoded_url_matches, legacy.proposed_id_matches]):
            raise ValueError('Expected bounded no-match capture differs')
        if repository:
            process = None
            if legacy.pinned_commit:
                process = subprocess.Popen(['git', 'show', legacy.pinned_commit + ':' +
                                            legacy.repository_path], cwd=repository,
                                           stdout=subprocess.PIPE)
                handle = process.stdout
            else:
                handle = (repository / legacy.repository_path).open('rb')
            digest, size, rows, matches = hashlib.sha256(), 0, 0, 0
            for rows, line in enumerate(handle, 1):
                digest.update(line)
                size += len(line)
                row = json.loads(line)
                fields = [row.get(k) for k in ['source_url', 'requested_url', 'final_url', 'url']]
                matches += bool(str(row.get('sha256', '')).lower() in legacy.compared_sha256s or
                                any(isinstance(u, str) and unquote(u) in {
                                    unquote(v) for v in legacy.compared_urls} for u in fields) or
                                row.get('source_id') == recommendation.source_id)
            handle.close()
            if process and process.wait() != 0:
                raise ValueError('Pinned local Git stream unavailable')
            if (digest.hexdigest(), size, rows, matches) != (
                    legacy.full_file_sha256, legacy.full_file_bytes, legacy.full_rows, 0):
                raise ValueError('Full legacy stream changed or comparison differs')
    if recommendation.incoming_source != audit.events[0].body:
        raise ValueError('Intake source differs from measured fee PDF')
    if recommendation.original_filename != Path(recommendation.incoming_source.path).name:
        raise ValueError('Intake filename differs from actual incoming basename')
    return audit


def main() -> int:
    """Verify only local evidence; no public transport or canonical mutation is available."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', type=Path)
    args = parser.parse_args()
    audit = validate(ROOT, repository=args.repository)
    print(json.dumps({'status': 'passed', 'delivery_files': 27, 'responses': 2,
                      'body_bytes': 81082, 'pdf_pages_structural': 2,
                      'full_legacy_streams_replayed': args.repository is not None,
                      'source_visual_pages_by_auditor': 0, 'public_requests': 0,
                      'canonical_intakes': 0, 'legal_currentness': audit.legal_currentness}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
