"""Read-only verification of three preserved directed-gap PDFs and their custody."""
from __future__ import annotations
import argparse,hashlib,importlib.util,json,sys
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse
sys.dont_write_bytecode=True
import jsonschema,pymupdf
from intake_models import Asset,Preparation,Receipt,Record
BASE=Path(__file__).resolve().parent

def check(base,item):
    rel=Path(item.path)
    assert rel.parts and not rel.is_absolute() and '..' not in rel.parts,item.path
    p=base/rel;assert not any(x.is_symlink() for x in (p,*p.parents)),item.path
    assert p.is_file() and p.resolve().is_relative_to(base.resolve()),item.path
    b=p.read_bytes();assert len(b)==item.size_bytes and hashlib.sha256(b).hexdigest()==item.sha256,item.path
    return b

def schema(b,s):
    s=json.loads(s);jsonschema.Draft202012Validator.check_schema(s);jsonschema.Draft202012Validator(s).validate(json.loads(b))

def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path);assert spec and spec.loader
    m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m

def validate(repo_root=None,preparation_only=False):
    prep=Preparation.model_validate_json((BASE/'PREPARATION.json').read_bytes())
    schema((BASE/'PREPARATION.json').read_bytes(),(BASE/'PREPARATION.schema.json').read_bytes())
    copies={c.original.path:c for c in prep.copied_discovery_files}
    assert len(copies)==len(prep.copied_discovery_files)==95
    def read(rel):return check(BASE,copies[rel].preserved)
    def original_check(f):
        c=copies[f.path];assert c.original.sha256==f.sha256 and c.original.size_bytes==f.bytes
        assert c.method=='exact_copy','Source derivative must be explicitly handled'
        return read(f.path)
    for c in copies.values():
        b=check(BASE,c.preserved)
        assert c.preserved.path.startswith('evidence/discovery/')
        if c.method=='exact_copy':assert c.original.sha256==c.preserved.sha256 and c.original.size_bytes==c.preserved.size_bytes and c.omitted_lines==0
        else:
            assert c.original.path=='events/E003/headers.txt' and c.preserved.path=='evidence/discovery/events/E003/headers.public.txt'
            assert c.omitted_lines==3 and not any(x.lower().startswith(b'set-cookie:') for x in b.splitlines())
    assert sum(c.method=='set_cookie_lines_omitted' for c in copies.values())==1
    assert copies['FINAL_MANIFEST.json'].original.sha256=='8b56e16999dac1c8da5cdf25956843d149b5cf39c2b2ebbe802e8e0d2517edde'
    audit_models=module(BASE/'evidence/discovery/audit_models.py','_directed_frozen_audit_models')
    capture_models=module(BASE/'evidence/discovery/capture.py','_directed_frozen_capture_models')
    inventory=audit_models.Inventory.model_validate_json(read('FINAL_MANIFEST.json'))
    assert {x.path for x in inventory.files}|set(inventory.exclusions)==set(copies)
    for x in inventory.files:
        c=copies[x.path];assert c.original.sha256==x.sha256 and c.original.size_bytes==x.bytes
    audit=audit_models.Audit.model_validate_json(read('ACCESS_AUDIT.json'))
    assert json.loads(read('ACCESS_AUDIT.schema.json'))==audit_models.Audit.model_json_schema()
    schema(read('ACCESS_AUDIT.json'),read('ACCESS_AUDIT.schema.json'))
    events={}
    for n in range(1,8):
        eid=f'E{n:03d}';e=capture_models.Event.model_validate_json(read(f'events/{eid}/event.json'));events[eid]=e
        assert e.event_id==eid
        b=original_check(audit_models.File(path=e.body_path,sha256=e.body_sha256,bytes=e.body_bytes))
        m=json.loads(read(e.metadata_path))
        assert e.http_status==m['http_code']==200 and m['num_redirects']==0 and m['ssl_verify_result']==0 and e.curl_exit==0
        assert m['url_effective']==e.requested_url==e.final_url and m['size_download']==len(b)
        assert not any(m.get(k) for k in ['url.user','url.password','urle.user','urle.password'])
        if 'html' in (e.content_type or ''):
            p=capture_models.Parser(e.requested_url);p.feed(b.decode('utf-8',errors='replace'))
            saved=capture_models.Parsed.model_validate_json(read(f'events/{eid}/parsed.json'))
            assert p.links==saved.links and '\n'.join(x.strip() for x in ''.join(p.text).splitlines() if x.strip())==saved.text
    assert len(events)==audit.public_event_count==7 and len({e.requested_url for e in events.values()})==7
    assert max(e.completed_at for e in events.values())==audit.public_stop_at
    assert sum(e.body_bytes for e in events.values())==audit.response_bytes==1911314
    for b in audit.basis:
        assert events[b.event_id].requested_url==b.exact_url
        obj=json.loads(read(b.source_file))
        if b.source_kind=='curl_redirect':assert obj['redirect_url']==b.exact_url and obj['http_code']==301
        else:assert {'url':b.exact_url,'label':b.exact_label} in obj['links']
    for eid in ['E009','E010','E011','E013']:
        e=capture_models.Event.model_validate_json(read(f'inputs/{eid}-event.json'));body=read(f'inputs/{eid}-body.bin')
        assert len(body)==e.body_bytes and hashlib.sha256(body).hexdigest()==e.body_sha256
    native_count=images=0
    for pdf in audit.pdfs:
        s=next(x for x in prep.sources if x.event_id==pdf.event_id);e=events[pdf.event_id]
        assert pdf.source.sha256==s.staged_original.sha256 and original_check(pdf.source)==check(BASE,s.staged_original)
        assert s.authority_id==audit.source_ownership[s.event_id]
        assert s.exact_requested_url==s.exact_final_url==e.requested_url
        assert s.http_started_at==e.started_at and s.http_completed_at==e.completed_at
        assert urlparse(s.exact_requested_url).hostname==('www.gjcity.org' if s.authority_id=='CO-MUNICIPAL-GRAND_JUNCTION' else 'www.mesacounty.us')
        assert s.physical_pages==pdf.pages and s.native_utf8_bytes==sum(x.native.bytes for x in pdf.native_pages)
        assert s.discovery_visually_reviewed_pages==[p.page for p in pdf.native_pages if p.visually_viewed]
        with pymupdf.open(stream=original_check(pdf.source),filetype='pdf') as doc:
            assert len(doc)==pdf.pages and not doc.is_repaired and not doc.is_encrypted
            assert pdf.version==pymupdf.VersionBind=='1.28.2' and pdf.flags==195 and pdf.sort is False
            for pg in pdf.native_pages:
                assert doc[pg.page-1].get_text('text',flags=195,sort=False).encode()==original_check(pg.native);native_count+=1
                if pg.image:
                    assert doc[pg.page-1].get_pixmap(matrix=pymupdf.Matrix(1.5,1.5)).tobytes('png')==original_check(pg.image);images+=1
    assert native_count==13 and images==11
    assert sum(p.visually_viewed for pdf in audit.pdfs for p in pdf.native_pages)==8
    assert len(audit.observations)==15
    for o in audit.observations:
        if o.physical_page:
            pdf=next(p for p in audit.pdfs if p.event_id==o.event_id)
            assert o.physical_page in [p.page for p in pdf.native_pages if p.visually_viewed]
        for span in o.evidence:
            body=original_check(span.file);assert span.end<=len(body) and body[span.start:span.end]==span.excerpt.encode()
            assert hashlib.sha256(span.excerpt.encode()).hexdigest()==span.excerpt_sha256
    manual=original_check(audit.legacy.manual_snapshot)
    assert len(manual.splitlines())==audit.legacy.manual_rows==43
    for eid,count in audit.legacy.manual_digest_matches.items():
        assert count==sum(events[eid].body_sha256 in json.loads(row).values() for row in manual.splitlines())==0
    assert audit.legacy.total_lines==48390 and audit.legacy.matched_rows==[]
    assert all(s.historical_digest_match_records==0 for s in prep.sources)
    city,planning,building=prep.sources
    assert [s.physical_pages for s in prep.sources]==[5,3,5]
    assert city.native_extraction_gap_pages==[2,3] and not planning.native_extraction_gap_pages and not building.native_extraction_gap_pages
    cp=next(p for p in audit.pdfs if p.event_id=='E003');assert cp.native_pages[1].native.bytes==0 and cp.native_pages[2].native.bytes==637
    assert [(d.value,d.role) for d in city.dates][-1]==('2026-10-05','future_effective_as_stated_at_receipt')
    assert datetime.fromisoformat('2026-10-05').date()>city.http_completed_at.date()
    assert [(d.value,d.role) for d in planning.dates]==[('2017 & 2018','historical_fee_schedule_label'),('2020-10-01','school_dedication_resolution_expiration_as_stated_in_pdf')]
    assert building.dates==[]
    for item in prep.requests:schema(check(BASE,item),check(BASE,prep.request_schema))
    assert not any([prep.dedupe.matching_size_files,prep.dedupe.raw_manifest_matches,prep.dedupe.ledger_matches,prep.dedupe.source_id_collisions])
    if preparation_only:
        assert repo_root;check(repo_root,prep.dedupe.raw_manifest);check(repo_root,prep.dedupe.manual_ledger)
        assert check(repo_root,prep.dedupe.raw_manifest)==manual
        return {'status':'passed_preparation','sources':3,'pages':13,'native_extraction_gaps_preserved':True}
    receipt=Receipt.model_validate_json((BASE/'INTAKE_RECEIPT.json').read_bytes())
    schema((BASE/'INTAKE_RECEIPT.json').read_bytes(),(BASE/'INTAKE_RECEIPT.schema.json').read_bytes())
    assert check(BASE,receipt.preparation)==(BASE/'PREPARATION.json').read_bytes() and receipt.sources==prep.sources
    rows_bytes=check(BASE,receipt.records);rows=[Record.model_validate_json(x) for x in rows_bytes.splitlines()]
    assert len(rows)==3
    for line in rows_bytes.splitlines():schema(line,check(BASE,receipt.record_schema))
    assert check(BASE,receipt.provenance)==b''.join((s.model_dump_json()+'\n').encode() for s in prep.sources)
    for r,s,raw in zip(rows,prep.sources,receipt.canonical_originals,strict=True):
        assert r.record_id==s.source_id and r.layer_id==s.layer_id and r.official_source_url==s.exact_requested_url
        assert r.archive_path==raw.path and r.sha256==raw.sha256==s.staged_original.sha256 and r.size_bytes==raw.size_bytes
        assert raw.path.startswith(f'_RAW_ARCHIVE/manual_intake/{s.layer_id}/{s.source_id}/')
        assert s.http_completed_at<r.received_at==receipt.actual_repository_received_at<receipt.completed_at
        assert r.acquisition_method=='manual_official_download' and r.source_format=='pdf'
        if repo_root:assert check(repo_root,raw)==check(BASE,s.staged_original)
    expected=['_RAW_ARCHIVE/manual_intake/manual_source_intake_manifest.jsonl','_CONTROL_PLANE/MANUAL_SOURCE_INTAKE_LEDGER.jsonl','_CONTROL_PLANE/MANUAL_SOURCE_INTAKE_REPORT.json']
    assert [t.repository_path for t in receipt.transactions]==expected
    for i,t in enumerate(receipt.transactions):
        before=check(BASE,t.before);after=check(BASE,t.after)
        assert t.snapshot.sha256==t.before.sha256 and t.snapshot.size_bytes==t.before.size_bytes
        assert t.snapshot.path.startswith('_SNAPSHOTS/snapshot_') and t.snapshot.path.endswith('/'+t.repository_path)
        if i<2:
            assert before.endswith(b'\n') and after==before+rows_bytes
            assert len(before.splitlines())==[43,44][i] and len(after.splitlines())==[46,47][i]
        else:
            b,a=json.loads(before),json.loads(after)
            assert (b['records'],a['records'])==(44,47) and (b['archive_verification']['manifest_records'],a['archive_verification']['manifest_records'])==(43,46)
            key='missing_ledger_only_intake_ids';assert b['archive_verification'][key]==a['archive_verification'][key] and len(a['archive_verification'][key])==1
        if repo_root:
            check(repo_root,t.snapshot);check(repo_root,Asset(path=t.repository_path,sha256=t.after.sha256,size_bytes=t.after.size_bytes))
    actual={p.relative_to(BASE).as_posix() for p in BASE.rglob('*') if p.is_file() and p.name not in {'INTAKE_RECEIPT.json','INTAKE_RECEIPT.schema.json'}}
    assert len({a.path for a in receipt.files})==len(receipt.files) and actual=={a.path for a in receipt.files}
    for x in receipt.files:check(BASE,x)
    stdout=check(BASE,receipt.full_corpus.stdout);stderr=check(BASE,receipt.full_corpus.stderr)
    assert receipt.full_corpus.exit_code==1 and not receipt.full_corpus.unexpected_issues
    assert receipt.full_corpus.inherited_issue_paths==['_CONTROL_PLANE/LOCAL_REVIEW_SUMMARY.json','08_County_Authorities/_index.jsonl']
    assert b'Validation failed for all with 2 issue(s)' in stdout+stderr
    for p in receipt.full_corpus.inherited_issue_paths:assert p.encode() in stdout+stderr
    return {'status':'passed','mode':'live_repository' if repo_root else 'portable','raw_records':46,'ledger_records':47,'sources':3,'pdf_pages':13,'native_bytes':sum(s.native_utf8_bytes for s in prep.sources),'discovery_visual_pages':8,'native_gap_pages':{'E003':[2,3]},'currentness':'not_verified','full_corpus_status':'two_inherited_errors'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--repo-root',type=Path);p.add_argument('--preparation-only',action='store_true')
    a=p.parse_args();print(json.dumps(validate(a.repo_root.resolve() if a.repo_root else None,a.preparation_only),indent=2))
