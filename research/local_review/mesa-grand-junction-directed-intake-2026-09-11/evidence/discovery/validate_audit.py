"""Read-only portable custody, page, slice and observed-referral validation."""
from __future__ import annotations
from pathlib import Path, PurePosixPath
from datetime import datetime, timezone
import hashlib
import json
import sys
import pymupdf
from pydantic import Field
from audit_models import Audit, File, Inventory, Strict
from capture import Event, Parsed, Parser
B=Path(__file__).resolve().parent

def digest(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def path(rel: str) -> Path:
    p=PurePosixPath(rel)
    if p.is_absolute() or any(x in ('..','.') for x in p.parts):
        raise ValueError('unsafe relative path')
    q=B.joinpath(*p.parts)
    for part in [q,*q.parents]:
        if part.is_symlink(): raise ValueError('symlink evidence')
    if not q.is_file(): raise ValueError(f'missing evidence: {rel}')
    return q

def check(f: File) -> bytes:
    b=path(f.path).read_bytes()
    if len(b)!=f.bytes or digest(b)!=f.sha256:raise ValueError(f'file mismatch: {f.path}')
    return b

class Result(Strict):
    validated_at: datetime
    passed: bool
    inventory_files: int
    public_events: int
    distinct_urls: int
    pdfs: int
    pdf_pages: int
    full_pages_viewed: int
    observations: int
    native_page_replays: int
    rendered_image_replays: int
    note: str

def main() -> None:
    inv=Inventory.model_validate_json((B/'FINAL_MANIFEST.json').read_text())
    expected={x.path for x in inv.files}|set(inv.exclusions)
    actual={p.relative_to(B).as_posix() for p in B.rglob('*') if p.is_file()}
    if expected!=actual:raise ValueError(f'inventory mismatch: {expected^actual}')
    for entry in inv.files:check(entry)
    a=Audit.model_validate_json((B/'ACCESS_AUDIT.json').read_text())
    if json.loads((B/'ACCESS_AUDIT.schema.json').read_text())!=Audit.model_json_schema():
        raise ValueError('schema drift')
    events=[Event.model_validate_json(p.read_text()) for p in sorted((B/'events').glob('*/event.json'))]
    es={e.event_id:e for e in events}
    if len(events)!=a.public_event_count or len({e.requested_url for e in events})!=a.distinct_requested_urls:
        raise ValueError('event count')
    if a.public_stop_at!=max(e.completed_at for e in events):raise ValueError('stop time')
    if a.public_stop_at>=datetime(2026,9,11,20,35,tzinfo=timezone.utc):raise ValueError('collection deadline')
    if sum(e.body_bytes for e in events)!=a.response_bytes:raise ValueError('body total')
    for e in events:
        b=check(File(path=e.body_path,sha256=e.body_sha256,bytes=e.body_bytes))
        m=json.loads(path(e.metadata_path).read_text())
        if e.http_status!=200 or m['http_code']!=200 or m['num_redirects']!=0 or m['ssl_verify_result']!=0 or e.curl_exit!=0:
            raise ValueError('response/TLS/redirect evidence')
        if m['url_effective']!=e.requested_url or m['size_download']!=len(b):raise ValueError('response binding')
        if any(m.get(k) for k in ['url.user','url.password','urle.user','urle.password']):raise ValueError('unexpected credential')
        if e.content_type and 'html' in e.content_type:
            observed=Parsed.model_validate_json((B/f'events/{e.event_id}/parsed.json').read_text())
            parser=Parser(e.requested_url);parser.feed(b.decode('utf-8',errors='replace'))
            text='\n'.join(x.strip() for x in ''.join(parser.text).splitlines() if x.strip())
            if text!=observed.text or parser.links!=observed.links:raise ValueError('HTML derivation mismatch')
    for basis in a.basis:
        if es[basis.event_id].requested_url!=basis.exact_url:raise ValueError('request/referral mismatch')
        obj=json.loads(path(basis.source_file).read_text())
        if basis.source_kind=='curl_redirect':
            if obj.get('redirect_url')!=basis.exact_url or obj.get('http_code')!=301:raise ValueError('redirect provenance')
        elif {'url':basis.exact_url,'label':basis.exact_label} not in obj['links']:
            raise ValueError('exact source anchor missing')
    for eid in ['E009','E010','E011','E013']:
        e=Event.model_validate_json((B/f'inputs/{eid}-event.json').read_text())
        b=path(f'inputs/{eid}-body.bin').read_bytes()
        if digest(b)!=e.body_sha256 or len(b)!=e.body_bytes:raise ValueError('seed-body binding')
    native_count=images=0
    for pdf in a.pdfs:
        doc=pymupdf.open(stream=check(pdf.source),filetype='pdf')
        if len(doc)!=pdf.pages or doc.is_repaired!=pdf.repaired or doc.is_encrypted!=pdf.encrypted:raise ValueError('PDF structure')
        if pdf.version!=pymupdf.VersionBind:raise ValueError('exact replay requires recorded PyMuPDF version')
        for pg in pdf.native_pages:
            native=doc[pg.page-1].get_text('text',flags=pdf.flags,sort=pdf.sort).encode()
            if check(pg.native)!=native:raise ValueError('native reproduction')
            native_count+=1
            if pg.image:
                image=doc[pg.page-1].get_pixmap(matrix=pymupdf.Matrix(1.5,1.5)).tobytes('png')
                if check(pg.image)!=image:raise ValueError('render reproduction')
                images+=1
    if sum(p.source.bytes for p in a.pdfs)!=a.acquired_pdf_bytes:raise ValueError('PDF byte total')
    for o in a.observations:
        if o.physical_page:
            pdf=next(x for x in a.pdfs if x.event_id==o.event_id)
            if o.physical_page not in [p.page for p in pdf.native_pages if p.visually_viewed]:raise ValueError('unviewed citation')
        for s in o.evidence:
            b=check(s.file)
            if s.end>s.file.bytes or b[s.start:s.end]!=s.excerpt.encode() or digest(s.excerpt.encode())!=s.excerpt_sha256:
                raise ValueError('excerpt bounds or bytes')
    rows=[json.loads(s) for s in check(a.legacy.manual_snapshot).splitlines()]
    if len(rows)!=a.legacy.manual_rows:raise ValueError('manual row count')
    for eid,n in a.legacy.manual_digest_matches.items():
        if sum(es[eid].body_sha256 in row.values() for row in rows)!=n:raise ValueError('manual digest comparison')
    for row in a.legacy.matched_rows:
        if digest(row.line_utf8.encode())!=row.line_sha256 or json.loads(row.line_utf8)!=row.row:raise ValueError('legacy original line binding')
    result=Result(validated_at=datetime.now(timezone.utc),passed=True,inventory_files=len(inv.files),public_events=len(events),distinct_urls=a.distinct_requested_urls,pdfs=len(a.pdfs),pdf_pages=sum(p.pages for p in a.pdfs),full_pages_viewed=sum(p.visually_viewed for pdf in a.pdfs for p in pdf.native_pages),observations=len(a.observations),native_page_replays=native_count,rendered_image_replays=images,note='Read-only integrity and derivation replay; visual truth and legal currentness are not certified. Full historical download manifest is not distributed, so its measured global absence comparison is not recomputed offline.')
    sys.stdout.write(result.model_dump_json(indent=2)+'\n')
if __name__=='__main__':main()
