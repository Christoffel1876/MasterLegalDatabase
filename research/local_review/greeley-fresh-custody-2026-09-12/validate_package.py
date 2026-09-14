"""Read-only portable verification; never open an origin URL or run acquisition code."""
from __future__ import annotations
import hashlib
import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

import jsonschema
import pymupdf
from bs4 import BeautifulSoup

sys.dont_write_bytecode=True
BASE=Path(__file__).absolute().parent
sys.path.insert(0,str(BASE))
from models import Asset,Manifest,Preservation,HttpCandidate

IDS=['SD008-06','SD008-07','SD008-08']
EXPECTED={
 'SD008-06':('greeley-building-fees-sd008-06','fa8a90dae00525c2dcb62ef4d69aeb84b7032a0fd2dc64f45c1685981e9becd4',1),
 'SD008-07':('greeley-development-impact-fee-memo-sd008-07','9effbd15196898c16105913ee21032db52ad1e259f4f9def0586804726f78709',3),
 'SD008-08':('greeley-water-sewer-proposed-pif-notice-sd008-08','edfd4eecc57657bec922b8e0e63597fbf2fc957936d8f26a1a457b195dac145c',2)}
PARENT='https://greeleyco.gov/business/construction-and-growth/building-permits-and-inspections/'
PUBLIC={'content-type','content-length','last-modified','date','etag','cache-control','location'}


def safe(root:Path,relative:str)->Path:
    """Reject escapes and every symlink ancestor before reading evidence."""
    rel=Path(relative)
    if rel.is_absolute() or '..' in rel.parts:raise ValueError('Unsafe relative path')
    path=root/rel
    if any(p.is_symlink() for p in (path,*path.parents)):
        raise ValueError('Symlink evidence path')
    if not path.is_file():raise ValueError('Missing ordinary file')
    return path


def hashed(root:Path,ref:Asset)->bytes:
    """Require exact ordinary bytes and size."""
    path=safe(root,ref.path)
    with path.open('rb') as stream:sha=hashlib.file_digest(stream,'sha256').hexdigest()
    if sha!=ref.sha256 or path.stat().st_size!=ref.size_bytes:
        raise ValueError('Evidence hash/size mismatch: '+ref.path)
    return path.read_bytes()


def pointer(value:dict,ptr:str)->object:
    """Resolve explicit JSON pointers only; no expressions or arbitrary code."""
    if not ptr.startswith('/'):raise ValueError('Invalid JSON pointer')
    for token in ptr[1:].split('/'):
        key=token.replace('~1','/').replace('~0','~')
        value=value[int(key)] if isinstance(value,list) else value[key]
    return value


def selected(root:Path,binding)->dict:
    """Stream exact selected JSONL rows, retaining the original line-ending hash."""
    path=safe(root,binding.selected_document.path)
    with path.open('rb') as stream:
        if hashlib.file_digest(stream,'sha256').hexdigest()!=binding.selected_document.sha256:
            raise ValueError('Selected JSONL hash mismatch')
    if path.stat().st_size!=binding.selected_document.size_bytes:
        raise ValueError('Selected JSONL size mismatch')
    with path.open('rb') as stream:
        for index,line in enumerate(stream):
            if index==binding.selected_zero_based_row:
                if (hashlib.sha256(line).hexdigest()!=binding.exact_line_sha256
                        or len(line)!=binding.exact_line_size_bytes):
                    raise ValueError('Exact historical row mismatch')
                return json.loads(line)
    raise ValueError('Selected row absent')


def validate_content(root:Path,audit:Preservation,indexed:dict[str,Asset])->dict:
    """Replay custody, HTML associations, structural PDF checks and unchanged prior bindings."""
    def data(name:str)->dict:
        return json.loads(safe(root,name).read_bytes())
    def schema(name:str,schema_name:str)->None:
        jsonschema.Draft202012Validator(data(schema_name),
            format_checker=jsonschema.FormatChecker()).validate(data(name))
    if [s.event_id for s in audit.sources]!=IDS:raise ValueError('Changed source selection')
    if audit.fresh_parent.sha256!=audit.historical_parent.sha256:
        raise ValueError('Parent byte comparison mismatch')
    parent=hashed(root,audit.fresh_parent)
    if parent!=hashed(root,audit.historical_parent):raise ValueError('Parent bytes changed')
    if b'</html>' not in parent.lower():raise ValueError('Incomplete parent HTML')
    for copy in audit.original_copies:
        if indexed.get(copy.copied.path)!=copy.copied:
            raise ValueError('Original copy is not bound to the package inventory')
    plan=data('fresh/plan.json');summary=data('fresh/summary.json')
    schema('fresh/plan.json','fresh/plan.schema.json')
    schema('fresh/summary.json','fresh/summary.schema.json')
    event_ids=['GREELEY-PARENT',*IDS]
    if ([t['source_id'] for t in plan['targets']]!=event_ids
            or [r['source_id'] for r in summary['receipts']]!=event_ids
            or summary['public_requests']!=4 or summary['redirects_followed']!=0
            or summary['canonical_writes']!=0):raise ValueError('Event sequence/counters changed')
    previous_end=None
    for target,receipt in zip(plan['targets'],summary['receipts'],strict=True):
        event=receipt['source_id'];folder='fresh/'+event+'/'
        schema(folder+'receipt.json','fresh/receipt.schema.json')
        schema(folder+'reservation.json','fresh/reservation.schema.json')
        reservation=data(folder+'reservation.json')
        body=safe(root,folder+'body.bin').read_bytes()
        if receipt!=data(folder+'receipt.json'):raise ValueError('Summary/receipt mismatch')
        url=receipt['requested_url'];split=urlsplit(url)
        if split.scheme!='https' or split.username or split.password or split.fragment:
            raise ValueError('Nonpublic or unsafe source URL')
        if event=='GREELEY-PARENT':
            if url!=PARENT:raise ValueError('Wrong parent URL')
        elif split.netloc!='cogy-p-001.sitecorecontenthub.cloud':
            raise ValueError('Wrong document host')
        if (receipt['http_status']!=200 or receipt['returncode']!=0 or not receipt['body_complete']
                or receipt['effective_url']!=url or url!=target['url']
                or receipt['source_body']!='body.bin' or receipt['error_text']
                or reservation['requested_url']!=url or reservation['started_at']!=receipt['started_at']
                or receipt['size_bytes']!=len(body)
                or receipt['sha256']!=hashlib.sha256(body).hexdigest()
                or target['expected_historical_sha256']!=receipt['sha256']
                or receipt['historical_digest_match'] is not True):
            raise ValueError('Recorded acquisition/body binding mismatch')
        headers=receipt['headers']
        if set(headers)-PUBLIC or any('\r' in v or '\n' in v for v in headers.values()):
            raise ValueError('Nonpublic or unsafe retained header')
        if int(headers['content-length'])!=len(body):raise ValueError('Content-Length mismatch')
        if headers['content-type']!=receipt['content_type']:raise ValueError('Type mismatch')
        start=datetime.fromisoformat(receipt['started_at'].replace('Z','+00:00'))
        end=datetime.fromisoformat(receipt['finished_at'].replace('Z','+00:00'))
        if start.tzinfo is None or end.tzinfo is None or start>end or (
                previous_end is not None and start<previous_end):
            raise ValueError('Recorded acquisition order mismatch')
        previous_end=end
    for source in audit.sources:
        sid,sha,pages=EXPECTED[source.event_id]
        if source.record_id!=sid or source.body.sha256!=sha or source.pages!=pages:
            raise ValueError('Source identity/digest/pages changed')
        receipt=data(source.receipt.path)
        if source.reservation.path!='fresh/'+source.event_id+'/reservation.json':
            raise ValueError('Source reservation swap')
        hashed(root,source.reservation)
        if receipt!=data('fresh/'+source.event_id+'/receipt.json'):
            raise ValueError('Source receipt swap')
        body=hashed(root,source.body)
        if not body.startswith(b'%PDF-') or b'%%EOF' not in body[-1024:]:
            raise ValueError('Missing PDF framing')
        with pymupdf.open(stream=body,filetype='pdf') as document:
            if (document.is_repaired or document.is_encrypted or len(document)!=pages
                    or any(page.rect.is_empty for page in document)):
                raise ValueError('Invalid PDF structure')
        for existing in [source.archived_source,source.prior_qa_original]:
            if (existing.sha256!=sha or existing.size_bytes!=len(body)
                    or existing.represented_by!=source.body):
                raise ValueError('Archived byte comparison binding mismatch')
        row=selected(root,source.canonical_record)
        prov=selected(root,source.prior_provenance)
        schema_path=safe(root,'prior/canonical-record.schema.json')
        jsonschema.Draft202012Validator(json.loads(schema_path.read_bytes())).validate(row)
        jsonschema.Draft202012Validator(data('prior/source-provenance.schema.json')).validate(prov)
        if (row['record_id']!=sid or row['sha256']!=sha or row['size_bytes']!=len(body)
                or row['archive_path']!=source.archived_source.repository_path
                or row['layer_id']!=source.layer_id or row['official_source_url'] is not None
                or row['acquisition_method']!='received_review_package'
                or row['status']!='archived_pending_pipeline'
                or datetime.fromisoformat(row['received_at'].replace('Z','+00:00'))
                    !=source.prior_repository_received_at
                or prov['source_id']!=sid or prov['authority_id']!=source.authority_id
                or prov['canonical_original']['sha256']!=sha
                or prov['source_role']!=source.source_role):
            raise ValueError('Prior source/custody identity mismatch')
        qa=json.loads(hashed(root,source.prior_qa))
        jsonschema.Draft202012Validator(json.loads(hashed(root,source.prior_qa_schema))).validate(qa)
        if pointer(qa,source.prior_qa_source_sha_pointer)!=sha or qa['source_id']!=sid:
            raise ValueError('Prior QA source identity mismatch')
        anchor=source.anchor
        raw=parent[anchor.exact_source_start_byte:anchor.exact_source_end_byte]
        if (anchor.parent!=audit.fresh_parent or anchor.parent_url!=PARENT
                or raw!=anchor.exact_anchor_html.encode()
                or hashlib.sha256(raw).hexdigest()!=anchor.anchor_html_sha256
                or anchor.href!=receipt['requested_url']):
            raise ValueError('Exact HTML anchor bytes mismatch')
        soup=BeautifulSoup(parent,'html.parser')
        matches=[a for a in soup.find_all('a',href=True) if a['href']==anchor.href]
        if len(matches)!=1 or ' '.join(matches[0].get_text(' ',strip=True).split())!=anchor.normalized_dom_text:
            raise ValueError('Fresh parent anchor association mismatch')
    scan=audit.privacy_scan
    if set(scan.public_header_names)!=PUBLIC or scan.rejected_header_keys_found:
        raise ValueError('Public header scan mismatch')
    expected_scans=[]
    for path in sorted((root/'fresh').rglob('*')):
        if path.is_file() and (path.suffix in {'.json','.py'} or path==root/audit.fresh_parent.path):
            expected_scans.append(path.relative_to(root).as_posix())
    if scan.scanned_text_assets!=expected_scans:raise ValueError('Privacy scan membership changed')
    for name in expected_scans:
        text=safe(root,name).read_text()
        if any(re.search(pattern,text) for pattern in scan.credential_patterns):
            raise ValueError('Potential private token/header requires review')
    bindings=[]
    with safe(root,'http-bindings.jsonl').open('rb') as stream:
        for line in stream:
            item=HttpCandidate.model_validate_json(line)
            jsonschema.Draft202012Validator(data('http-binding.schema.json')).validate(json.loads(line))
            bindings.append(item)
    if [b.record_id for b in bindings]!=[s.record_id for s in audit.sources]:
        raise ValueError('HTTP binding source list mismatch')
    for binding,source in zip(bindings,audit.sources,strict=True):
        h=binding.verified_http
        receipt=json.loads(hashed(root,h.document.artifact))
        if (h.document.artifact!=source.receipt or h.document.jsonl_row is not None
                or h.sha_pointer!='/sha256' or h.status_pointer!='/http_status'
                or h.time_pointer!='/finished_at' or pointer(receipt,h.sha_pointer)!=source.body.sha256
                or pointer(receipt,h.status_pointer)!=200
                or pointer(receipt,h.time_pointer)!=data(source.receipt.path)['finished_at']):
            raise ValueError('HTTP binding pointer mismatch')
    if sum(s.pages for s in audit.sources)!=6 or sum(s.body.size_bytes for s in audit.sources)!=877639:
        raise ValueError('PDF totals mismatch')
    return {'status':'verified_public_custody_preservation','recorded_gets':4,'pdf_sources':3,
            'pdf_pages':6,'pdf_bytes':877639,'canonical_writes':0,'new_public_requests':0,
            'prior_full_qa_replayed':False,'legal_currentness':'not_verified'}


def verify(root:Path=BASE)->dict:
    """Validate the closed package, then replay its bounded acquisition/source bindings."""
    manifest=Manifest.model_validate_json(safe(root,'FINAL_MANIFEST.json').read_bytes())
    names=[item.path for item in manifest.files]
    if names!=sorted(set(names)):raise ValueError('Duplicate or unordered inventory')
    actual=set()
    for path in root.rglob('*'):
        if path.is_symlink() or (not path.is_dir() and not path.is_file()):
            raise ValueError('Nonordinary package member')
        if path.is_file() and path.relative_to(root).as_posix()!='FINAL_MANIFEST.json':
            actual.add(path.relative_to(root).as_posix())
    if actual!=set(names):raise ValueError('Package membership changed')
    indexed={item.path:item for item in manifest.files}
    for item in manifest.files:hashed(root,item)
    audit=Preservation.model_validate_json(safe(root,'PRESERVATION.json').read_bytes())
    for name,model in [('PRESERVATION',Preservation),('FINAL_MANIFEST',Manifest)]:
        schema=json.loads(safe(root,name+'.schema.json').read_bytes())
        if schema!=model.model_json_schema():raise ValueError('Declared schema changed')
        jsonschema.Draft202012Validator(schema).validate(json.loads(safe(root,name+'.json').read_bytes()))
    return validate_content(root,audit,indexed)


if __name__=='__main__':
    logging.basicConfig(level=logging.INFO,format='%(message)s')
    logging.info('%s',json.dumps(verify(),indent=2))
