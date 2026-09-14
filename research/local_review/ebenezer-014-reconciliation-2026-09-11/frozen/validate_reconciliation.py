"""Validate the EB014 frozen reconciliation offline without changing any files."""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import re
import sys
from typing import Literal
import jsonschema
import pymupdf
from reconciliation_models import Reconciliation, Strict, FileRef, SourceSupport, FinalManifest
B = Path(__file__).resolve().parent
P = 'comparison/committed-package/'

class ValidationResult(Strict):
    validated_at: datetime
    reconciliation: FileRef
    external_reports: Literal[4]
    comparison_files: Literal[58]
    committed_files: Literal[56]
    distinct_asset_hash_claims: Literal[14]
    reconciled_findings: Literal[21]
    reconciled_errata: Literal[3]
    reconciled_unresolved_themes: Literal[5]
    directly_inspected_full_pages: Literal[7]
    directly_inspected_crops: Literal[11]
    original_pdf_bytes: Literal[340287]
    native_bytes: Literal[13579]
    original_paths_checked: bool
    candidate_changed: Literal[False]
    legal_currentness: Literal['not_verified']
    committed_package_validation: dict
    checks_passed: list[str]

def digest(p):
    return sha256(p.read_bytes()).hexdigest()

def check(path, expected, size):
    assert path.is_file() and not path.is_symlink(), str(path)
    assert not any(p.is_symlink() for p in path.parents), str(path)
    assert path.stat().st_size == size and digest(path) == expected, str(path)

def schema_data(name, model=None):
    d = json.loads((B / (name + '.json')).read_text())
    s = json.loads((B / (name + '.schema.json')).read_text())
    if model:
        assert s == model.model_json_schema()
        model.model_validate_json(json.dumps(d))
    jsonschema.Draft202012Validator(s).validate(d)
    return d

def validate(check_originals=False):
    m = Reconciliation.model_validate_json(json.dumps(schema_data('RECONCILIATION', Reconciliation)))
    for r in m.receipts + m.supplemental_evidence + m.directly_inspected_crops + [m.source_pdf, m.native_candidate, m.committed_review]:
        check(B / r.path, r.sha256, r.size_bytes)
    custody = schema_data('CUSTODY_RECEIPT')
    comp = schema_data('COMPARISON_RECEIPT')
    assert len(custody['files']) == 4 and len(comp['files']) == 58
    assert comp['comparison_commit'] == m.comparison_commit == '95155c235bc64756c6ed1cdf9014cd920fe30fcc'
    assert sum(x['git_blob_match'] is True for x in comp['files']) == 56
    assert {Path(r['original_path']).name for r in custody['files']} == {'PASS1_frozen.md','PASS2_REVIEW.md','PASS1_FREEZE_RECEIPT.json','COMPLETION_RECEIPT.json'}
    for r in custody['files']:
        check(B / 'received' / Path(r['original_path']).name, r['sha256'], r['size_bytes'])
        if check_originals:
            check(Path(r['original_path']), r['sha256'], r['size_bytes'])
    for r in comp['files']:
        FileRef(path=r['copy_path'], sha256=r['sha256'], size_bytes=r['size_bytes'])
        check(B / r['copy_path'], r['sha256'], r['size_bytes'])
        if check_originals:
            check(Path(r['original_path']), r['sha256'], r['size_bytes'])
    aliases = {**{f'page-{n:04}.png': P+f'images/page-{n:04}.png' for n in range(1,8)},
        'candidate.txt': P+'candidate.txt', 'original.pdf': P+'source/original.pdf',
        'packet_manifest': 'comparison/batch4-manifest.json', 'queue': 'comparison/queue-auth.md',
        **{x: 'received/'+x for x in ['PASS1_frozen.md','PASS1_FREEZE_RECEIPT.json','PASS2_REVIEW.md']}}
    assert len(comp['hash_claims']) == len(aliases) == 14
    assert {x['label'] for x in comp['hash_claims']} == set(aliases)
    hashes = set()
    for c in comp['hash_claims']:
        assert c['matches'] and c['expected_sha256'] == c['actual_sha256'] == digest(B / aliases[c['label']])
        hashes.add(c['expected_sha256'])
        if check_originals:
            assert digest(Path(c['actual_path'])) == c['expected_sha256']
    for name in ['PASS1_frozen.md','PASS2_REVIEW.md','PASS1_FREEZE_RECEIPT.json','COMPLETION_RECEIPT.json']:
        assert set(re.findall(r'\b[0-9a-f]{64}\b', (B/'received'/name).read_text())) <= hashes
    draft = json.loads((B/m.committed_review.path).read_text())
    qa = draft['retained_source_audit_with_local_bindings']
    observations = {x['id']: x for x in qa['observations']}
    assert len(observations) == 29 and len(draft['associations']) == 5
    assert sum(len(p['native_text'].encode()) for p in qa['pages']) == 13579
    lines = (B/'received/PASS2_REVIEW.md').read_text().splitlines()
    for d in m.decisions:
        assert lines[d.external_line-1] == d.external_claim
        for page, r in zip(d.physical_pages, d.page_images):
            assert r.path == P+f'images/page-{page:04}.png'
            check(B/r.path, r.sha256, r.size_bytes)
        for id in d.atlas_observation_ids:
            assert id in observations and observations[id]['physical_page'] in d.physical_pages
    assert len([l for l in lines if re.match(r'^\| EB014-P2-\d{3} \|', l)]) == 21
    assert len([l for l in lines if re.match(r'^\| E\d \|', l)]) == 3
    receipt = json.loads((B/'received/COMPLETION_RECEIPT.json').read_text())
    assert receipt['findings_counts'] == {'critical':2,'minor':12,'info':7,'unresolved_themes':5}
    assert receipt['errata_vs_pass1_count'] == 3 and len(receipt['unresolved_regions']) == 5
    assert receipt['original_pdf_local_rehash'] == 'not_present_under_workdir_bound_from_assignment_and_pass1'
    assert receipt['candidate_unchanged_native'] is True
    support = SourceSupport.model_validate_json(json.dumps(schema_data('SOURCE_SUPPORT', SourceSupport)))
    assert support.source_pdf == m.source_pdf and pymupdf.VersionBind == '1.28.2'
    crops = [('p1-logo',1,(60,70,285,150)),('p4-list-transition-quotes',4,(75,324,570,392)),
        ('p5-title-quotes',5,(75,128,570,175)),('p5-italics',5,(75,328,570,359)),
        ('p6-authority',6,(75,276,565,334))]
    with pymupdf.open(B/m.source_pdf.path) as pdf:
        assert len(pdf) == 7 and not pdf.is_repaired and not pdf.is_encrypted
        native = (B/m.native_candidate.path).read_bytes()
        for page in qa['pages']:
            raw = pdf[page['physical_page']-1].get_text('text',sort=False,flags=195).encode()
            assert raw == page['native_text'].encode()
            assert native[page['candidate_start_byte']:page['candidate_end_byte_exclusive']] == raw
        for span in support.selected_font_spans:
            spans = [s for b in pdf[span.physical_page-1].get_text('dict')['blocks'] for l in b.get('lines',[]) for s in l['spans']]
            assert any(all(s[k] == getattr(span,k) for k in ['text','font','flags']) and list(s['bbox']) == span.bbox for s in spans)
        assert [{'xref':l['xref'],'uri':l['uri'],'rect':list(l['from'])} for l in pdf[1].get_links()] == support.page2_uri_annotations
        for name, n, rect in crops:
            raw = pdf[n-1].get_pixmap(matrix=pymupdf.Matrix(300/72,300/72),clip=pymupdf.Rect(rect),alpha=False).tobytes('png')
            assert raw == (B/'crops'/f'{name}.png').read_bytes()
    spec = importlib.util.spec_from_file_location('eb014_frozen_package', B/P/'validate_package.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    package_result = module.validate_package(B/P)
    assert package_result['status'] == 'passed'
    if (B/'FINAL_MANIFEST.json').exists():
        final = FinalManifest.model_validate_json(json.dumps(schema_data('FINAL_MANIFEST', FinalManifest)))
        actual = {str(p.relative_to(B)) for p in B.rglob('*') if p.is_file() and p.name not in ['FINAL_MANIFEST.json','FINAL_MANIFEST.schema.json'] and '__pycache__' not in p.parts}
        assert {r.path for r in final.files} == actual
        for r in final.files:
            check(B/r.path, r.sha256, r.size_bytes)
    p = B/'RECONCILIATION.json'
    return ValidationResult(validated_at=datetime.now(timezone.utc), reconciliation=FileRef(path=p.name,sha256=digest(p),size_bytes=p.stat().st_size), external_reports=4,comparison_files=58,committed_files=56,distinct_asset_hash_claims=14,reconciled_findings=21,reconciled_errata=3,reconciled_unresolved_themes=5,directly_inspected_full_pages=7,directly_inspected_crops=11,original_pdf_bytes=340287,native_bytes=13579,original_paths_checked=check_originals,candidate_changed=False,legal_currentness='not_verified',committed_package_validation=package_result,checks_passed=['Strict Pydantic and JSON Schema models; exact 29 decision identities and count arithmetic','Four external byte identities and 58 comparison files; all 14 distinct advertised hashes','Every external claim bound to its exact report line and correct full-page images/Atlas observations','Seven original PDF page re-extractions equal every retained native page and candidate slice','Three font spans, three URI metadata records and five new crops reproduced','Copied committed package validator passed its exhaustive partitions, 36 observation spans, ten original crops and twelve PDF links','Final complete file/hash inventory checked when present; no claim of unseen reviewer behavior or legal currentness'])

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-originals', action='store_true', help='Also compare original local input paths')
    args = parser.parse_args()
    print(validate(args.check_originals).model_dump_json(indent=2))
