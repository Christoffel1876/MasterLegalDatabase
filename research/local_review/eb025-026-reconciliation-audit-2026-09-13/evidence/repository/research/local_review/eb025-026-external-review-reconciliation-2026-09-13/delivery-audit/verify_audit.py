"""Portable read-only delivery bindings. It cannot establish historical tool execution."""
import hashlib
import json
import os
import re
import stat
from pathlib import Path

import jsonschema
import pymupdf
from models import Asset, Audit, Binding, Custody, FindingClaim, Manifest

HERE = Path(__file__).absolute().parent
PACKET_SHA = 'ace3738bac6375b17f01ae0c4390350d5aeeacb1b9473838c57832dcd09427f5'
QA_SHA = '2372e6bde1fa544c56dbaed1a808a7389bf943006f8d2d4c65dd5fa10a8ad46f'


def need(value, message):
    if not value:
        raise ValueError(message)


def read(root, name):
    part = Path(name)
    need(not part.is_absolute() and '..' not in part.parts and '\\' not in name
         and part.as_posix() == name, 'unsafe path')
    path = root / part
    need(not any(p.is_symlink() for p in (path, *path.parents)), 'linked evidence')
    need(stat.S_ISREG(path.stat().st_mode), 'nonordinary evidence')
    return path.read_bytes()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def check_asset(root, item):
    raw = read(root, item.path)
    need(sha(raw) == item.sha256 and len(raw) == item.size_bytes, 'asset mismatch: ' + item.path)
    return raw


def typed(root, name, model):
    raw = read(root, name + '.json')
    schema = json.loads(read(root, name + '.schema.json'))
    need(schema == model.model_json_schema(), 'schema/model mismatch')
    jsonschema.validate(json.loads(raw), schema)
    return model.model_validate_json(raw)


def finding_claims(raw):
    claims, kind = [], None
    for line in raw.decode().splitlines():
        if line.startswith('### Critical'):
            kind = 'critical'
        elif line.startswith('### Minor'):
            kind = 'minor'
        match = re.match(r'^\| (EB0(?:25|26)-P2-\d{3}) \| (.*?) \| (.*?) \|$', line)
        if match:
            need(kind is not None, 'finding has no declared classification')
            claims.append(FindingClaim(
                finding_id=match[1], claimed_classification=kind,
                claimed_summary=match[2] + ': ' + match[3], source_meaning_assessed=False))
    need(len({c.finding_id for c in claims}) == len(claims), 'duplicate finding')
    return claims


def document_bindings(root, directory):
    """Compare every delivered receipt hash and retained source/candidate file with packet pins."""
    prefix = 'received/' + directory + '/'
    complete = json.loads(read(root, prefix + 'COMPLETION_RECEIPT.json'))
    freeze = json.loads(read(root, prefix + 'PASS1_FREEZE_RECEIPT.json'))
    sid = complete['source_id']
    manifest_raw = read(root, 'packet/MANIFEST.json')
    need(sha(manifest_raw) == PACKET_SHA, 'unexpected original packet manifest')
    pins = {x['path']: Asset.model_validate(x) for x in json.loads(manifest_raw)['files']}
    bindings = []

    def bind(label, claimed, observed, paths):
        bindings.append(Binding(label=label, claimed=str(claimed) if claimed is not None else None,
                                observed=str(observed), matches=claimed == observed,
                                evidence_paths=paths))

    for label, target in [
        ('packet_manifest_sha256', 'packet/MANIFEST.json'),
        ('start_here_instruction_sha256', 'packet/START_HERE.md'),
        ('pass1_frozen_sha256', prefix + 'PASS1_frozen.md'),
        ('pass1_freeze_receipt_sha256', prefix + 'PASS1_FREEZE_RECEIPT.json'),
        ('candidate_sha256', prefix + 'candidate/candidate.txt'),
        ('pass2_review_sha256', prefix + 'PASS2_REVIEW.md'),
        ('original_pdf_sha256', prefix + 'source/original.pdf'),
    ]:
        observed = sha(read(root, target))
        bind('completion.' + label, complete[label], observed,
             [prefix + 'COMPLETION_RECEIPT.json', target])
        if label in freeze:
            bind('freeze.' + label, freeze[label], observed,
                 [prefix + 'PASS1_FREEZE_RECEIPT.json', target])
    prompt = prefix + 'prompts/PASS1_TASK_PROMPT.txt'
    prompt_claim = (freeze.get('pass1_task_prompt_sha256') or
                    freeze.get('assistance', {}).get('task_prompt_retained_sha256'))
    bind('freeze.pass1_task_prompt_sha256', prompt_claim, sha(read(root, prompt)),
         [prefix + 'PASS1_FREEZE_RECEIPT.json', prompt])
    for local_sub, packet_sub in [('source', '01-source-only'),
                                  ('candidate', '02-candidate-text')]:
        for item in sorted((root / prefix / local_sub).iterdir()):
            local = prefix + local_sub + '/' + item.name
            pin = pins[packet_sub + '/' + sid + '/' + item.name]
            body = read(root, local)
            bind('packet.' + local_sub + '/' + item.name + '.sha256', pin.sha256, sha(body),
                 ['packet/MANIFEST.json', local])
            bind('packet.' + local_sub + '/' + item.name + '.size_bytes', pin.size_bytes, len(body),
                 ['packet/MANIFEST.json', local])
    for n in range(1, 7):
        name = f'page-{n:04}.png'
        path = prefix + 'source/' + name
        observed = sha(read(root, path))
        bind('completion.page.' + str(n), complete['page_image_sha256'][name], observed,
             [prefix + 'COMPLETION_RECEIPT.json', path])
        if 'page_image_sha256' in freeze:
            claimed = freeze['page_image_sha256'][name]
        else:
            claimed = next(x['sha256'] for x in freeze['page_images'] if x['physical_page'] == n)
        bind('freeze.page.' + str(n), claimed, observed,
             [prefix + 'PASS1_FREEZE_RECEIPT.json', path])
    with pymupdf.open(stream=read(root, prefix + 'source/original.pdf'), filetype='pdf') as pdf:
        pages = pdf.page_count
    bind('source.pdf_page_count', 6, pages, [prefix + 'source/original.pdf'])
    release = read(root, prefix + 'CANDIDATE_RELEASE_UTC.txt').decode().strip()
    bind('completion.utc_candidate_release', complete['utc_candidate_release'], release,
         [prefix + 'COMPLETION_RECEIPT.json', prefix + 'CANDIDATE_RELEASE_UTC.txt'])
    claims = finding_claims(read(root, prefix + 'PASS2_REVIEW.md'))
    for kind in ['critical', 'minor']:
        bind('completion.findings.' + kind, complete['findings'][kind],
             sum(c.claimed_classification == kind for c in claims),
             [prefix + 'COMPLETION_RECEIPT.json', prefix + 'PASS2_REVIEW.md'])
    canonical = 'packet/03-custody/' + sid + '/canonical-record.jsonl'
    with (root / canonical).open('rb') as handle:
        rows = [json.loads(line) for line in handle]
    need(len(rows) == 1, 'canonical row count')
    bind('canonical.source_id', sid, rows[0]['record_id'], [canonical])
    bind('canonical.source_sha256', complete['original_pdf_sha256'], rows[0]['sha256'], [canonical])
    known_hashes = {b.observed for b in bindings if re.fullmatch(r'[a-f0-9]{64}', b.observed)}
    for name in ['PASS1_frozen.md', 'PASS2_REVIEW.md']:
        mentioned = set(re.findall(r'\b[a-f0-9]{64}\b', read(root, prefix + name).decode()))
        need(mentioned <= known_hashes, 'report mentions a hash outside checked evidence')
    return bindings, claims


def verify(root=HERE):
    manifest = typed(root, 'FINAL_MANIFEST', Manifest)
    actual = set()
    for top, dirs, files in os.walk(root, followlinks=False):
        for name in dirs + files:
            need(not (Path(top) / name).is_symlink(), 'linked package member')
        for name in files:
            actual.add((Path(top) / name).relative_to(root).as_posix())
    expected = {a.path for a in manifest.files} | {'FINAL_MANIFEST.json'}
    need(actual == expected and len(expected) == len(manifest.files) + 1, 'closed membership')
    for item in manifest.files:
        check_asset(root, item)
    custody = typed(root, 'CUSTODY', Custody)
    need(custody.source_review_pin.sha256 == QA_SHA, 'pre-report source QA identity differs')
    for copy in custody.copies:
        check_asset(root, copy.retained)
    audit = typed(root, 'AUDIT', Audit)
    need(audit.custody_sha256 == sha(read(root, 'CUSTODY.json')), 'audit custody pin')
    need([d.assignment for d in audit.documents] == ['EB-PDF-025', 'EB-PDF-026'], 'document scope')
    for document in audit.documents:
        bindings, claims = document_bindings(root, document.report_directory)
        need(bindings == document.bindings and claims == document.claimed_findings,
             'recorded observations differ from retained artifacts')
        need(all(b.matches for b in bindings), 'delivered hash/count discrepancy')
    return {
        'status': 'passed_artifact_bindings_only', 'documents': 2, 'source_pages': 12,
        'claimed_findings': [len(d.claimed_findings) for d in audit.documents],
        'checked_bindings': sum(len(d.bindings) for d in audit.documents),
        'historical_execution_order_established': False,
        'caption_process_independence_established': False,
        'substantive_findings_accepted': 0, 'public_requests': 0,
    }


if __name__ == '__main__':
    print(json.dumps(verify(), indent=2))
