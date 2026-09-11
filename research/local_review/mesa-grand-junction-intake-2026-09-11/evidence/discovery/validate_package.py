"""Read-only portable validator for the finite Atlas discovery package."""
from __future__ import annotations
import hashlib
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
import jsonschema
import pymupdf
from audit_models import Custody, Extract, Inputs, PDF, Report, Validation
from capture import Event, Parsed

BASE=Path(__file__).resolve().parent
def digest(path: Path) -> str:
    """Hash a file without loading large evidence inventories into memory."""
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()
def safe(path: str) -> Path:
    """Reject escaping paths and symlinks before reading package evidence."""
    rel=Path(path)
    if rel.is_absolute() or '..' in rel.parts:raise ValueError('unsafe inventory path')
    p=BASE/rel
    for ancestor in (p,*p.parents):
        if ancestor.is_symlink():raise ValueError('symlink evidence')
        if ancestor==BASE:break
    if not p.is_file():raise ValueError(f'missing evidence {path}')
    return p

def validate() -> Validation:
    """Validate exact custody, referrals, limits and all native page bindings."""
    manifest=Custody.model_validate_json((BASE/'CUSTODY.json').read_text())
    rows={r.path:r for r in manifest.files}
    if len(rows)!=len(manifest.files):raise ValueError('duplicate custody path')
    for r in manifest.files:
        p=safe(r.path)
        if p.stat().st_size!=r.bytes or digest(p)!=r.sha256:
            raise ValueError(f'custody mismatch {r.path}')
    actual={str(p.relative_to(BASE)) for p in BASE.rglob('*') if p.is_file()
            and '__pycache__' not in p.parts}
    if actual-set(manifest.excludes)!=set(rows):raise ValueError('unbound package file')
    report=Report.model_validate_json(safe('REPORT.json').read_text())
    jsonschema.validate(json.loads(safe('REPORT.json').read_text()),
                        json.loads(safe('REPORT.schema.json').read_text()))
    jsonschema.validate(json.loads(safe('CUSTODY.json').read_text()),
                        json.loads(safe('CUSTODY.schema.json').read_text()))
    inputs=Inputs.model_validate_json(safe('INPUTS.json').read_text())
    assert report.input_commit==inputs.commit
    for i in inputs.files:
        x=Extract.model_validate_json(safe(i.extract_path).read_text())
        assert x.input_path==i.path and x.sha256==i.sha256
        assert len(x.rows)==i.matching_rows
    evs={p.parent.name:Event.model_validate_json(p.read_text())
         for p in sorted((BASE/'events').glob('*/event.json'))}
    assert list(evs)==[f'E{i:03d}' for i in range(1,len(evs)+1)]
    for e in evs.values():
        assert e.started_at.tzinfo and e.completed_at.tzinfo
        assert e.started_at<=e.completed_at<=report.stop_at
        assert e.requested_url.startswith('https://')
        assert e.final_url==e.requested_url
        m=json.loads(safe(e.metadata_path).read_text())
        assert m.get('num_redirects')==0 and m.get('url_effective')==e.final_url
        assert (m.get('http_code') or None)==e.http_status
        if e.body_path:
            p=safe(e.body_path)
            assert p.stat().st_size==e.body_bytes and digest(p)==e.body_sha256
        else:assert e.body_bytes==0 and e.body_sha256 is None and e.http_status is None
        for path in [e.headers_path,e.stderr_path]:safe(path)
    s=report.summary
    assert len(evs)==s.public_events<=20
    assert len({e.requested_url for e in evs.values()})==s.distinct_requested_urls<=12
    assert sum(e.http_status==200 for e in evs.values())==s.http_200
    assert sum(e.http_status==301 for e in evs.values())==s.http_301
    assert sum(e.http_status is None for e in evs.values())==s.transport_failures
    assert sum(e.body_bytes for e in evs.values())==s.response_body_bytes
    assert sum(e.body_bytes for e in evs.values() if e.http_status==200)==s.accepted_200_bytes
    assert report.stop_at<datetime(2026,9,11,20,25,tzinfo=timezone.utc)
    for p in report.priorities:
        for basis in p.basis:
            if basis.event_id:
                parsed=Parsed.model_validate_json(safe(f'events/{basis.event_id}/parsed.json').read_text())
                assert any(x.url==p.url and x.label==basis.label for x in parsed.links)
        if p.source_event_id:
            e=evs[p.source_event_id];assert e.requested_url==p.url
            if p.acquisition_status=='source_preserved':
                assert e.http_status==200 and e.body_path
            if p.acquisition_status=='redirect_only':
                assert e.http_status==301
                from urllib.parse import urljoin
                headers=safe(e.headers_path).read_text().splitlines()
                loc=[x.split(':',1)[1].strip() for x in headers if x.lower().startswith('location:')]
                assert len(loc)==1 and urljoin(e.requested_url,loc[0])==p.unfollowed_redirect_url
                assert p.unfollowed_redirect_url not in {x.requested_url for x in evs.values()}
        else:assert p.acquisition_status=='linked_unopened'
    pdf_pages=0;viewed=0
    for scope in report.pdf_review:
        info=PDF.model_validate_json(safe(f'pdf-inspection/{scope.event_id}/STRUCTURE.json').read_text())
        e=evs[scope.event_id];assert e.content_type=='application/pdf'
        assert info.pdf_sha256==e.body_sha256
        doc=pymupdf.open(safe(e.body_path));assert len(doc)==info.pages==scope.source_pages
        assert not doc.is_repaired and not doc.is_encrypted
        assert len(info.native_pages)==len(doc)
        for i,record in enumerate(info.native_pages):
            assert record.physical_page==i+1
            native=doc[i].get_text('text',flags=info.native_flags,sort=info.native_sort).encode('utf-8')
            assert safe(record.native_path).read_bytes()==native
            assert len(native)==record.native_bytes
            assert hashlib.sha256(native).hexdigest()==record.native_sha256
        assert len(scope.full_pages_viewed)==len(scope.render_paths)
        assert len(set(scope.full_pages_viewed))==len(scope.full_pages_viewed)
        for page,path in zip(scope.full_pages_viewed,scope.render_paths):
            assert 1<=page<=len(doc) and f'view-{page:04d}.png' in path
            assert safe(path).read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
        pdf_pages+=len(doc);viewed+=len(scope.full_pages_viewed)
    assert pdf_pages==s.pdf_structural_pages and viewed==s.full_pages_visually_checked
    assert len(report.pdf_review)==s.pdf_count and len(report.priorities)==s.priority_count
    compare=json.loads(safe('LEGACY_COMPARISON.json').read_text())
    jsonschema.validate(compare,json.loads(safe('LEGACY_COMPARISON.schema.json').read_text()))
    legacy_input=next(i for i in inputs.files if i.path.endswith('LOCAL_DOWNLOAD_MANIFEST.jsonl'))
    assert compare['input_sha256']==legacy_input.sha256
    assert compare['priorities']==[p.model_dump(mode='json') for p in report.priorities]
    return Validation(task_id=report.task_id,validated_at=datetime.now(timezone.utc),passed=True,
        checked_files=len(rows),event_count=len(evs),distinct_targets=s.distinct_requested_urls,
        priority_count=s.priority_count,checklist_rows=len(report.checklist),pdf_count=s.pdf_count,
        pdf_pages=pdf_pages,viewed_pages=viewed,
        note='Offline schema/hash/referral/limit/native checks passed. Visual scope is a human inspection record, not a computed legal-currentness result.')
if __name__=='__main__':
    logging.warning(validate().model_dump_json(indent=2))
