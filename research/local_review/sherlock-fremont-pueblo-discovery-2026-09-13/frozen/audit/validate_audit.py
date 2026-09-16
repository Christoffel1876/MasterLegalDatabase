"""Read-only portable checks; no network, historical script execution or visual QA replay."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path, PurePosixPath
import sys
from urllib.parse import urljoin


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def safe(root: Path, relative: str) -> Path:
    p = PurePosixPath(relative)
    require(not p.is_absolute() and '..' not in p.parts and '\\' not in relative, 'unsafe path')
    target = root.joinpath(*p.parts)
    require(not any(x.is_symlink() for x in [target, *target.parents]), 'symlink path')
    require(target.is_file(), 'not an ordinary file: ' + relative)
    return target


def verify_ref(root: Path, item: dict) -> bytes:
    data = safe(root, item['path']).read_bytes()
    require(len(data) == item['size_bytes'], 'size mismatch: ' + item['path'])
    require(hashlib.sha256(data).hexdigest() == item['sha256'], 'hash mismatch: ' + item['path'])
    return data


def validate(root: Path, expected_manifest: str) -> dict:
    root = root.expanduser().absolute()
    require(not any(x.is_symlink() for x in [root, *root.parents]), 'symlink root')
    manifest_bytes = safe(root, 'FINAL_MANIFEST.json').read_bytes()
    require(hashlib.sha256(manifest_bytes).hexdigest() == expected_manifest, 'manifest pin')
    manifest = json.loads(manifest_bytes)
    names = [x['path'] for x in manifest['files']]
    require(len(names) == len(set(names)), 'duplicate manifest member')
    actual = set()
    for p in root.rglob('*'):
        require(not p.is_symlink(), 'symlink member')
        if p.is_dir():
            require(any(p.iterdir()), 'unlisted empty directory')
        else:
            require(p.is_file(), 'special member')
            actual.add(p.relative_to(root).as_posix())
    require(actual == set(names) | {'FINAL_MANIFEST.json'}, 'closed inventory mismatch')
    for item in manifest['files']:
        verify_ref(root, item)
    # Imports follow the complete external-manifest check. Historical collection scripts never run.
    sys.path.insert(0, str(root))
    from audit_models import Audit, Proposal, Manifest
    from bs4 import BeautifulSoup
    import jsonschema
    import pymupdf
    Manifest.model_validate_json(manifest_bytes)
    for name, model in [('AUDIT', Audit), ('DIRECTED_PROPOSAL', Proposal)]:
        raw = safe(root, name + '.json').read_bytes()
        model.model_validate_json(raw)
        schema = json.loads(safe(root, name + '.schema.json').read_bytes())
        require(schema == model.model_json_schema(), name + ' schema differs')
        jsonschema.Draft202012Validator(schema).validate(json.loads(raw))
    audit = json.loads(safe(root, 'AUDIT.json').read_bytes())
    proposal = json.loads(safe(root, 'DIRECTED_PROPOSAL.json').read_bytes())
    for finding in audit['findings']:
        for item in finding['evidence']:
            verify_ref(root, item)
    custody = json.loads(verify_ref(root, audit['custody']))
    received = root / 'received'
    receipt_names = [x['path'] for x in custody['files']]
    require(len(receipt_names) == len(set(receipt_names)) == 170, 'custody count')
    require({p.relative_to(received).as_posix() for p in received.rglob('*') if p.is_file()}
            == set(receipt_names), 'received closure')
    for item in custody['files']:
        verify_ref(received, item)
    # Verify the unchanged prepared packet, kept separate from the later delivered acquisition.
    protocol = root / 'input-protocol'
    original_manifest = json.loads(safe(protocol, 'FINAL_MANIFEST.json').read_bytes())
    for item in original_manifest['files']:
        verify_ref(protocol, item)
    sys.path.insert(0, str(protocol))
    from models import ActionLog, Reservation, Result, Checklist, Priorities, Backlog, ArtifactInventory
    log = ActionLog.model_validate_json(safe(received, 'ACTION_LOG.json').read_bytes())
    checklist = Checklist.model_validate_json(safe(received, 'CHECKLIST.json').read_bytes())
    priorities = Priorities.model_validate_json(safe(received, 'PRIORITIES.json').read_bytes())
    backlog = Backlog.model_validate_json(safe(received, 'BACKLOG.json').read_bytes())
    inventory = ArtifactInventory.model_validate_json(safe(received, 'ARTIFACT_INVENTORY.json').read_bytes())
    for item in inventory.files:
        verify_ref(received, item.model_dump())
    require(len(inventory.files) == 166, 'received inventory count')
    action_ids = {x.action_id for x in log.reservations}
    require(len(log.reservations) == len(log.results) == 31, 'action count')
    body_total = 0
    largest = 0
    previous = None
    for reservation, result in zip(log.reservations, log.results, strict=True):
        require(Reservation.model_validate_json(safe(received, 'reservations/' + reservation.action_id + '.json').read_bytes()) == reservation, 'reservation copy')
        require(Result.model_validate_json(safe(received, 'results/' + result.action_id + '.json').read_bytes()) == result, 'result copy')
        require(reservation.action_id == result.action_id, 'paired actions')
        require(result.finished_at is not None and result.finished_at >= reservation.reserved_at, 'time order')
        require(previous is None or reservation.reserved_at >= previous, 'recorded overlap')
        previous = result.finished_at
        require(result.observed_final_url in {None, reservation.requested_url}, 'unexpected final URL')
        require(not result.visible_redirect_urls, 'unexpected recorded redirects')
        for item in result.retained_assets:
            verify_ref(received, item.model_dump())
        matching = [x for x in result.retained_assets if x.sha256 == result.body_sha256]
        if matching:
            body_total += matching[0].size_bytes
            largest = max(largest, matching[0].size_bytes)
            alias = received / 'raw' / (result.action_id + '.bin')
            if alias.exists():
                require(alias.read_bytes() == verify_ref(received, matching[0].model_dump()), 'body alias mismatch')
    require((body_total, largest) == (14821045, 10756377), 'body sums')
    require(len({x.requested_url for x in log.reservations}) == 30, 'distinct targets')
    require(Counter(x.authority_id for x in log.reservations) == {'CO-COUNTY-PUEBLO': 11, 'CO-COUNTY-FREMONT': 20}, 'authority counts')
    counts = Counter(x.body_role for x in log.results)
    require(counts == {'original_pdf': 4, 'original_html': 17, 'error_body': 8, 'no_body': 1, 'browser_derivative': 1}, 'body roles')
    require(len(priorities.priorities) == 12 and len({x.requested_url for x in priorities.priorities}) == 11, 'priority count')
    candidate_ids = {x.candidate_id for x in priorities.priorities}
    for row in checklist.rows:
        require(set(row.action_ids) <= action_ids and set(row.candidate_ids) <= candidate_ids, 'dangling checklist reference')
    for row in priorities.priorities:
        require(set(row.action_ids) <= action_ids, 'dangling priority action')
        for action in row.action_ids:
            source = next(x for x in log.reservations if x.action_id == action)
            require(source.authority_id == row.authority_id, 'priority authority mismatch')
    require(len(backlog.entries) == len({x.url for x in backlog.entries}) == 13, 'backlog count')
    require(not ({x.url for x in backlog.entries} & {x.requested_url for x in log.reservations}), 'backlog opened')
    pages = 0
    for observation in audit['pdf_observations']:
        data = verify_ref(root, observation['source'])
        verify_ref(root, observation['first_page_image'])
        require(data.startswith(b'%PDF-'), 'PDF magic')
        with pymupdf.open(stream=data, filetype='pdf') as doc:
            require(not doc.is_encrypted and not doc.is_repaired, 'PDF structural issue')
            require(len(doc) == observation['physical_pages'], 'PDF page count')
            pages += len(doc)
            require(observation['viewed_pages'] == [1], 'expanded visual claim')
            # Re-render pixel derivative, not the human visual findings.
            expected = doc[0].get_pixmap(dpi=130).tobytes('png')
            require(hashlib.sha256(expected).hexdigest() == observation['first_page_image']['sha256'], 'first-page render binding')
    require(pages == 749 and len(audit['pdf_observations']) == 4, 'PDF scope')
    for target in proposal['targets']:
        soup = BeautifulSoup(verify_ref(root, target['parent']), 'html.parser')
        matches = [x for x in soup.find_all('a', href=True)
                   if x['href'] == target['exact_href'] and ' '.join(x.get_text(' ', strip=True).split()) == target['exact_label']]
        require(bool(matches), 'exact proposal anchor missing')
        require(urljoin(target['parent_url'], target['exact_href']) == target['url'], 'proposal URL resolution')
    return {'status': 'PASS', 'payload_files': len(names), 'received_files': 170,
            'actions': 31, 'distinct_targets': 30, 'pdfs': 4, 'structural_pages': 749,
            'visual_scope': 'four first pages only', 'legal_currentness': 'not_verified',
            'network_actions': 0}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).parent)
    parser.add_argument('--manifest-sha256', required=True)
    args = parser.parse_args()
    try:
        result = validate(args.root, args.manifest_sha256)
    except Exception as error:
        sys.stderr.write(type(error).__name__ + ': ' + str(error) + '\n')
        return 1
    sys.stdout.write(json.dumps(result, indent=2) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
