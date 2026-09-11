"""Read-only portable custody and transaction checks; no network or external handoff reads."""
from __future__ import annotations
import argparse,hashlib,json,sys
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin,urlparse
from html.parser import HTMLParser
sys.dont_write_bytecode=True
import jsonschema,pymupdf
from intake_models import Asset,Preparation,Receipt,Record
BASE=Path(__file__).resolve().parent

class Anchors(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.href=None;self.parts=[];self.links=[]
    def handle_starttag(self,tag,attrs):
        if tag.lower()=='a':self.href=dict(attrs).get('href');self.parts=[]
    def handle_data(self,data):
        if self.href is not None:self.parts.append(data)
    def handle_endtag(self,tag):
        if tag.lower()=='a' and self.href is not None:
            self.links.append((self.href,' '.join(' '.join(self.parts).split())))
            self.href=None;self.parts=[]

def check(base:Path,item:Asset)->bytes:
    rel=Path(item.path)
    assert rel.parts and not rel.is_absolute() and '..' not in rel.parts,item.path
    p=base/rel
    assert not any(x.is_symlink() for x in (p,*p.parents)),item.path
    assert p.is_file() and p.resolve().is_relative_to(base.resolve()),item.path
    b=p.read_bytes();assert len(b)==item.size_bytes and hashlib.sha256(b).hexdigest()==item.sha256,item.path
    return b

def schema(data:bytes,definition:bytes):
    s=json.loads(definition);jsonschema.Draft202012Validator.check_schema(s)
    jsonschema.Draft202012Validator(s).validate(json.loads(data))

def validate(repo_root:Path|None=None,preparation_only:bool=False)->dict:
    prep=Preparation.model_validate_json((BASE/'PREPARATION.json').read_bytes())
    schema((BASE/'PREPARATION.json').read_bytes(),(BASE/'PREPARATION.schema.json').read_bytes())
    copies={c.original.path:c for c in prep.copied_discovery_files}
    assert len(copies)==len(prep.copied_discovery_files)==356
    def read(rel):
        return check(BASE,copies[rel].preserved)
    for c in copies.values():
        b=check(BASE,c.preserved)
        assert c.preserved.path.startswith('evidence/discovery/')
        if c.method=='exact_copy':
            assert c.original.sha256==c.preserved.sha256 and c.original.size_bytes==c.preserved.size_bytes and c.omitted_lines==0
        else:
            assert c.original.path.endswith('/headers.txt')
            assert c.preserved.path=='evidence/discovery/'+c.original.path.replace('/headers.txt','/headers.public.txt')
            assert c.omitted_lines==3
            assert not any(l.lower().startswith(b'set-cookie:') for l in b.splitlines())
    assert sum(c.method=='set_cookie_lines_omitted' for c in copies.values())==6
    for manifestname in ['CUSTODY.json','FINAL_MANIFEST.json']:
        m=json.loads(read(manifestname));schema(read(manifestname),read('CUSTODY.schema.json'))
        assert len({x['path'] for x in m['files']})==len(m['files'])
        assert {x['path'] for x in m['files']}==set(copies)-set(m['excludes'])
        for x in m['files']:
            c=copies[x['path']]
            assert c.original.sha256==x['sha256'] and c.original.size_bytes==x['bytes']
    for name in ['REPORT','INPUTS','LEGACY_COMPARISON','VALIDATION']:
        schema(read(name+'.json'),read(name+'.schema.json'))
    report=json.loads(read('REPORT.json'));inputs=json.loads(read('INPUTS.json'))
    assert report['input_commit']==inputs['commit']=='f160dec2792a2efbcbfee8d37fd3c72477e83cb1'
    for x in inputs['files']:
        extract=json.loads(read(x['extract_path']));schema(read(x['extract_path']),read('INPUT_EXTRACT.schema.json'))
        assert extract['input_path']==x['path'] and extract['sha256']==x['sha256'] and len(extract['rows'])==x['matching_rows']
    events={}
    for n in range(1,14):
        eid=f'E{n:03d}';path=f'events/{eid}/event.json';raw=read(path)
        schema(raw,read('EVENT.schema.json'));e=json.loads(raw);events[eid]=e
        m=json.loads(read(e['metadata_path']))
        assert e['event_id']==eid and e['requested_url']==e['final_url']==m['url_effective']
        assert m['num_redirects']==0 and (m['http_code'] or None)==e['http_status']
        if e['body_path']:
            b=read(e['body_path']);assert len(b)==e['body_bytes'] and hashlib.sha256(b).hexdigest()==e['body_sha256']
        else:assert e['body_bytes']==0 and e['body_sha256'] is None
        if e['http_status']==200:assert m['ssl_verify_result']==0
    assert len({e['requested_url'] for e in events.values()})==12
    assert sum(e['http_status']==200 for e in events.values())==10
    assert sum(e['http_status']==301 for e in events.values())==2
    for s in prep.sources:
        e=events[s.event_id]
        assert s.exact_requested_url==s.exact_final_url==e['requested_url']
        assert datetime.fromisoformat(e['started_at'].replace('Z','+00:00'))==s.http_started_at
        assert datetime.fromisoformat(e['completed_at'].replace('Z','+00:00'))==s.http_completed_at
        body=check(BASE,s.staged_original);assert body==read(e['body_path'])
        assert e['http_status']==200 and e['content_type']=='application/pdf' and e['curl_exit']==0
        p=next(p for p in report['priorities'] if p['priority_id']==s.priority_id)
        assert p['authority_id']==s.authority_id and p['source_event_id']==s.event_id
        assert p['url']==s.exact_requested_url and p['acquisition_status']=='source_preserved'
        assert p['existing_registry_source_ids']==s.legacy_registry_source_ids
        assert p['legacy']['preserved_digest_equal_records']==s.historical_digest_match_records
        for basis in p['basis']:
            if basis['event_id']:
                parent=events[basis['event_id']]
                parsed=json.loads(read(f"events/{basis['event_id']}/parsed.json"))
                schema(read(f"events/{basis['event_id']}/parsed.json"),read('HTML_EXTRACT.schema.json'))
                assert any(a['url']==p['url'] and a['label']==basis['label'] for a in parsed['links'])
                anchors=Anchors();anchors.feed(read(parent['body_path']).decode('utf-8'))
                assert any(urljoin(parent['final_url'],href)==p['url'] and label==' '.join(basis['label'].split()) for href,label in anchors.links)
        host=urlparse(s.exact_requested_url).hostname
        assert host==('www.mesacounty.us' if s.authority_id=='CO-COUNTY-MESA' else 'www.gjcity.org')
        info=json.loads(read(f'pdf-inspection/{s.event_id}/STRUCTURE.json'))
        schema(read(f'pdf-inspection/{s.event_id}/STRUCTURE.json'),read('PDF_STRUCTURE.schema.json'))
        assert info['pdf_sha256']==s.staged_original.sha256 and info['native_flags']==195 and info['native_sort'] is False
        scope=next(x for x in report['pdf_review'] if x['event_id']==s.event_id)
        assert scope['full_pages_viewed']==s.discovery_visually_reviewed_pages
        with pymupdf.open(stream=body,filetype='pdf') as pdf:
            assert len(pdf)==s.physical_pages==info['pages']==len(info['native_pages'])
            assert not pdf.is_repaired and not pdf.is_encrypted
            total=0
            for i,r in enumerate(info['native_pages']):
                assert r['physical_page']==i+1
                native=pdf[i].get_text('text',flags=195,sort=False).encode()
                assert native==read(r['native_path']) and len(native)==r['native_bytes']
                assert hashlib.sha256(native).hexdigest()==r['native_sha256'];total+=len(native)
            assert total==s.native_utf8_bytes
        for r in scope['render_paths']:assert read(r).startswith(b'\x89PNG\r\n\x1a\n')
    assert [s.historical_digest_match_records for s in prep.sources]==[41,0,0]
    assert [s.physical_pages for s in prep.sources]==[219,29,2]
    assert len(prep.sources[-1].dates)==0
    for req in prep.requests:schema(check(BASE,req),check(BASE,prep.request_schema))
    assert not prep.dedupe.matching_size_files and not prep.dedupe.raw_manifest_matches and not prep.dedupe.ledger_matches and not prep.dedupe.source_id_collisions
    if preparation_only:
        assert repo_root is not None
        check(repo_root,prep.dedupe.raw_manifest);check(repo_root,prep.dedupe.manual_ledger)
        return {'status':'passed_preparation','sources':3,'pages':250,'copies':356}
    r=Receipt.model_validate_json((BASE/'INTAKE_RECEIPT.json').read_bytes())
    schema((BASE/'INTAKE_RECEIPT.json').read_bytes(),(BASE/'INTAKE_RECEIPT.schema.json').read_bytes())
    assert check(BASE,r.preparation)==(BASE/'PREPARATION.json').read_bytes()
    assert r.sources==prep.sources
    records=check(BASE,r.records);provenance=check(BASE,r.provenance)
    assert provenance==b''.join((s.model_dump_json()+'\n').encode() for s in r.sources)
    record_schema=check(BASE,r.record_schema)
    rows=[Record.model_validate_json(line) for line in records.splitlines()]
    assert len(rows)==3
    for line in records.splitlines():schema(line,record_schema)
    for row,s,raw in zip(rows,r.sources,r.canonical_originals,strict=True):
        assert row.record_id==s.source_id and row.layer_id==s.layer_id
        assert row.sha256==raw.sha256==s.staged_original.sha256
        assert row.archive_path==raw.path and row.size_bytes==raw.size_bytes==s.staged_original.size_bytes
        assert raw.path.startswith(f'_RAW_ARCHIVE/manual_intake/{s.layer_id}/{s.source_id}/')
        assert row.official_source_url==s.exact_requested_url and row.received_at==r.actual_repository_received_at
        assert s.http_completed_at<row.received_at<r.completed_at
        assert row.acquisition_method=='manual_official_download' and row.source_format=='pdf'
        if repo_root is not None:assert check(repo_root,raw)==check(BASE,s.staged_original)
    wanted=['_RAW_ARCHIVE/manual_intake/manual_source_intake_manifest.jsonl','_CONTROL_PLANE/MANUAL_SOURCE_INTAKE_LEDGER.jsonl','_CONTROL_PLANE/MANUAL_SOURCE_INTAKE_REPORT.json']
    assert [t.repository_path for t in r.transactions]==wanted
    for n,t in enumerate(r.transactions):
        before=check(BASE,t.before);after=check(BASE,t.after)
        assert t.snapshot.sha256==t.before.sha256 and t.snapshot.size_bytes==t.before.size_bytes
        assert t.snapshot.path.startswith('_SNAPSHOTS/snapshot_') and t.snapshot.path.endswith('/'+t.repository_path)
        if n<2:
            assert after==before+records and before.endswith(b'\n')
            assert len(before.splitlines())==[40,41][n] and len(after.splitlines())==[43,44][n]
        else:
            b,a=json.loads(before),json.loads(after)
            assert (b['records'],a['records'])==(41,44)
            assert (b['archive_verification']['manifest_records'],a['archive_verification']['manifest_records'])==(40,43)
            key='missing_ledger_only_intake_ids'
            assert b['archive_verification'][key]==a['archive_verification'][key] and len(a['archive_verification'][key])==1
        if repo_root is not None:
            check(repo_root,t.snapshot)
            check(repo_root,Asset(path=t.repository_path,sha256=t.after.sha256,size_bytes=t.after.size_bytes))
    actual={p.relative_to(BASE).as_posix() for p in BASE.rglob('*') if p.is_file() and p.name not in {'INTAKE_RECEIPT.json','INTAKE_RECEIPT.schema.json'}}
    assert len({a.path for a in r.files})==len(r.files) and actual=={a.path for a in r.files}
    for f in r.files:check(BASE,f)
    stdout=check(BASE,r.full_corpus.stdout);stderr=check(BASE,r.full_corpus.stderr)
    assert r.full_corpus.exit_code==1 and not r.full_corpus.unexpected_issues
    assert r.full_corpus.inherited_issue_paths==['_CONTROL_PLANE/LOCAL_REVIEW_SUMMARY.json','08_County_Authorities/_index.jsonl']
    assert b'Validation failed for all with 2 issue(s)' in stdout+stderr
    for path in r.full_corpus.inherited_issue_paths:assert path.encode() in stdout+stderr
    return {'status':'passed','mode':'live_repository' if repo_root else 'portable','raw_records':43,'ledger_records':44,'sources':3,'pdf_pages':250,'native_bytes':sum(s.native_utf8_bytes for s in r.sources),'discovery_visual_pages':8,'all_pages_semantically_reviewed':False,'cookie_header_derivatives':6,'full_corpus_status':'two_inherited_errors','legal_currentness':'not_verified'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo-root',type=Path);p.add_argument('--preparation-only',action='store_true')
    a=p.parse_args();print(json.dumps(validate(a.repo_root.resolve() if a.repo_root else None,a.preparation_only),indent=2))
