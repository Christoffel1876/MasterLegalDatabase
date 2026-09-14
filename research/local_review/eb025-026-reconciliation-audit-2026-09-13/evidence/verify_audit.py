"""Read-only portable hash, schema and exact finding-join verification.

The recorded visual observations are not regenerated or certified by this program.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import jsonschema
from models import Asset, Audit, Manifest

HERE = Path(__file__).absolute().parent
PACKAGE = 'research/local_review/eb025-026-external-review-reconciliation-2026-09-13'
RECON_SHA = 'f070adbd98d49debccd617a50f27dd07cd650ce81ce01c56906c332e867919fd'
DELIVERY_SHA = 'e17544720906c73349b914bdcb5641533d7a3ff2643ef3cdaf5658d1dd5f937a'


def need(condition: bool, message: str) -> None:
    """Raise on a broken binding."""
    if not condition:
        raise ValueError(message)


def read(root: Path, name: str) -> bytes:
    """Read ordinary files beneath an ordinary root without following symlinks."""
    Asset(path=name, sha256='0' * 64, size_bytes=0)
    root = root.absolute()
    for ancestor in (root, *root.parents):
        need(not ancestor.is_symlink(), 'linked root ancestor')
    path = root
    for part in name.split('/'):
        path /= part
        need(not path.is_symlink(), 'linked evidence')
    need(path.is_file(), 'missing ordinary evidence: ' + name)
    return path.read_bytes()


def sha(body: bytes) -> str:
    """Return SHA256 of retained bytes."""
    return hashlib.sha256(body).hexdigest()


def asset(root: Path, item: dict, prefix: str = '') -> bytes:
    """Check size and digest before consuming an evidence buffer."""
    pin = Asset.model_validate(item)
    body = read(root, prefix + pin.path)
    need(len(body) == pin.size_bytes and sha(body) == pin.sha256, 'asset mismatch: ' + pin.path)
    return body


def typed(root: Path, name: str, model: type):
    """Validate exact JSON using its preserved model and exported schema."""
    body = read(root, name + '.json')
    value = model.model_validate_json(body)
    jsonschema.validate(json.loads(body), json.loads(read(root, name + '.schema.json')))
    return value


def verify_joins(root: Path, rec: dict, audit: Audit) -> dict:
    """Check all sixteen joins and retained limitations, without judging pixels."""
    prefix = 'repository/'
    delivery = prefix + PACKAGE + '/delivery-audit/'
    original = json.loads(read(root, delivery + 'AUDIT.json'))
    claims = [f for d in original['documents'] for f in d['claimed_findings']]
    expected = [f'EB025-P2-{n:03}' for n in range(1, 8)]
    expected += [f'EB026-P2-{n:03}' for n in range(1, 10)]
    need([f['finding_id'] for f in claims] == expected, 'original finding scope')
    need([f['finding_id'] for f in rec['findings']] == expected, 'reconciliation finding scope')
    need([f.finding_id for f in audit.findings] == expected, 'audit finding scope')
    evidence = [rec['report_audit'], *rec['pre_report_qa']]
    for claim, finding, checked in zip(claims, rec['findings'], audit.findings, strict=True):
        need(finding['reported_classification'] == claim['claimed_classification'], 'severity join')
        need(finding['reported_summary'] == claim['claimed_summary'], 'report summary join')
        need(checked.reported_classification == finding['reported_classification'], 'audit severity')
        need(checked.disposition == finding['disposition'], 'audit disposition')
        need(finding['correction_applied'] is False, 'unapproved source correction')
        need(bool(finding['evidence']), 'empty evidence')
        evidence.extend(finding['evidence'])
    for item in evidence:
        asset(root, item, prefix)
    need(rec['critical_extraction_errors_accepted'] == 0, 'critical-count promotion')
    for key in ('answer_safe', 'translation_equivalence_verified',
                'independent_grok_review_established'):
        need(rec[key] is False, 'scope promotion: ' + key)
    need(rec['legal_currentness'] == 'not_verified', 'currentness promotion')
    qa = [json.loads(asset(root, item, prefix)) for item in rec['pre_report_qa'][:2]]
    for data, document in zip(qa, original['documents'], strict=True):
        base = delivery + 'received/' + document['report_directory'] + '/'
        for key, path in [('source', 'source/original.pdf'), ('candidate', 'candidate/candidate.txt')]:
            body = read(root, base + path)
            need(sha(body) == data[key]['sha256'], 'source QA ' + key + ' identity')
            need(len(body) == data[key]['size_bytes'], 'source QA ' + key + ' size')
        need(data['legal_currentness'] == 'not_verified' and data['answer_safe'] is False,
             'pre-report QA scope')
    need(qa[0]['external_reports_consulted'] is False, 'rewritten pre-report chronology')
    need(qa[0]['translation_equivalence_verified'] is False, 'translation promotion')
    need(len(qa[0]['footer_evidence']) == 6, 'footer scope')
    need(all(x['visually_certified_year'] is None for x in qa[0]['footer_evidence']),
         'footer year certification')
    return {'findings': 16, 'reported_critical': 3, 'accepted_critical': 0}


def verify(root: Path = HERE) -> dict:
    """Verify this closed package and the complete copied delivery subpackage."""
    manifest = typed(root, 'FINAL_MANIFEST', Manifest)
    actual = set()
    for top, dirs, files in os.walk(root, followlinks=False):
        for name in dirs + files:
            need(not (Path(top) / name).is_symlink(), 'linked member')
        actual.update((Path(top) / n).relative_to(root).as_posix() for n in files)
    wanted = {x.path for x in manifest.files} | {'FINAL_MANIFEST.json'}
    need(len(wanted) == len(manifest.files) + 1 and actual == wanted, 'closed membership')
    for item in manifest.files:
        asset(root, item.model_dump())
    audit = typed(root, 'AUDIT', Audit)
    rec_bytes = asset(root, audit.reconciliation.model_dump())
    need(sha(rec_bytes) == RECON_SHA, 'reconciliation pin')
    rec = json.loads(rec_bytes)
    prefix = 'repository/' + PACKAGE + '/'
    jsonschema.validate(rec, json.loads(read(root, prefix + 'RECONCILIATION.schema.json')))
    inv_body = asset(root, audit.reconciliation_inventory.model_dump())
    inv = json.loads(inv_body)
    jsonschema.validate(inv, json.loads(read(root, prefix + 'INVENTORY.schema.json')))
    for item in inv['files']:
        asset(root, item, 'repository/')
    need(sha(read(root, prefix + 'delivery-audit/FINAL_MANIFEST.json')) == DELIVERY_SHA,
         'original delivery audit pin')
    result = verify_joins(root, rec, audit)
    for item in audit.directly_viewed:
        asset(root, item.model_dump())
    process = subprocess.run(
        [sys.executable, '-B', str(root / prefix / 'delivery-audit/verify_audit.py')],
        cwd=root, capture_output=True, text=True, timeout=30, check=True,
    )
    replay = json.loads(process.stdout)
    need(replay['checked_bindings'] == 124, 'delivery binding count')
    result.update(status='passed_recorded_scope', delivery_bindings=124,
                  pixels_rejudged_by_validator=False, public_requests=0)
    return result


if __name__ == '__main__':
    print(json.dumps(verify(), indent=2))
