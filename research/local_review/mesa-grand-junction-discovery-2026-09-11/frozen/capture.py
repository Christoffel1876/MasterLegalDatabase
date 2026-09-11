"""Bounded ordinary-TLS capture with one receipt for every public attempt."""
from __future__ import annotations
import hashlib
import json
import logging
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from pydantic import BaseModel, ConfigDict, Field

BASE = Path(__file__).resolve().parent
class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid')
class Event(Strict):
    event_id: str
    requested_url: str
    basis: str
    started_at: datetime
    completed_at: datetime
    curl_exit: int
    http_status: int | None
    final_url: str | None
    content_type: str | None
    body_path: str | None
    body_sha256: str | None
    body_bytes: int
    headers_path: str
    metadata_path: str
    stderr_path: str
    outcome: str
class Link(Strict):
    url: str
    label: str
class Parsed(Strict):
    event_id: str
    text: str
    links: list[Link]
class Parser(HTMLParser):
    def __init__(self, base: str) -> None:
        super().__init__(); self.base=base; self.text=[]; self.links=[]
        self.href=None; self.label=[]; self.skip=0
    def handle_starttag(self, tag: str, attrs: list[tuple[str,str|None]]) -> None:
        a=dict(attrs)
        if tag in ('script','style'): self.skip+=1
        if tag=='a' and a.get('href'):
            self.href=urljoin(self.base,a['href']); self.label=[]
    def handle_endtag(self, tag: str) -> None:
        if tag in ('script','style'): self.skip=max(0,self.skip-1)
        if tag=='a' and self.href:
            self.links.append(Link(url=self.href,label=' '.join(' '.join(self.label).split())))
            self.href=None
        if tag in ('p','div','li','h1','h2','h3','tr'): self.text.append('\n')
    def handle_data(self, data: str) -> None:
        if not self.skip: self.text.append(data)
        if self.href: self.label.append(data)
def save(path: Path, value: Strict) -> None:
    """Save a validated new record atomically without overwriting evidence."""
    if path.exists(): raise FileExistsError(path)
    tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(value.model_dump_json(indent=2)+'\n',encoding='utf-8')
    os.replace(tmp,path)
def capture(url: str, basis: str) -> None:
    """Fetch one explicit public URL, without automatic retries or redirects."""
    events=sorted((BASE/'events').glob('E*/event.json'))
    old=[Event.model_validate_json(p.read_text()) for p in events]
    if len(old)>=20 or len({e.requested_url for e in old}|{url})>12:
        raise ValueError('public event/target limit')
    if datetime.now(timezone.utc)>=datetime(2026,9,11,20,25,tzinfo=timezone.utc):
        raise ValueError('discovery deadline reached')
    if urlparse(url).scheme!='https': raise ValueError('HTTPS only')
    if any(e.requested_url==url and e.http_status in (400,401,403,404,410) for e in old):
        raise ValueError('nonretryable route already stopped')
    eid=f'E{len(old)+1:03d}'; d=BASE/'events'/eid; d.mkdir(parents=True)
    start=datetime.now(timezone.utc)
    result=subprocess.run(['curl','--silent','--show-error','--proto','=https',
        '--connect-timeout','15','--max-time','40','--max-filesize','20000000',
        '--dump-header',str(d/'headers.txt'),'--output',str(d/'body.bin'),
        '--write-out','%{json}',url],capture_output=True)
    (d/'curl-metadata.json').write_bytes(result.stdout)
    (d/'stderr.txt').write_bytes(result.stderr)
    try: meta=json.loads(result.stdout)
    except ValueError: meta={}
    body=d/'body.bin'; blob=body.read_bytes() if body.exists() else b''
    status=meta.get('http_code') or None
    event=Event(event_id=eid,requested_url=url,basis=basis,started_at=start,
        completed_at=datetime.now(timezone.utc),curl_exit=result.returncode,
        http_status=status,final_url=meta.get('url_effective'),
        content_type=meta.get('content_type'),
        body_path=str(body.relative_to(BASE)) if body.exists() else None,
        body_sha256=hashlib.sha256(blob).hexdigest() if body.exists() else None,
        body_bytes=len(blob),headers_path=str((d/'headers.txt').relative_to(BASE)),
        metadata_path=str((d/'curl-metadata.json').relative_to(BASE)),
        stderr_path=str((d/'stderr.txt').relative_to(BASE)),
        outcome='http_response' if status is not None else 'transport_failure')
    save(d/'event.json',event)
    if status==200 and 'html' in (event.content_type or ''):
        p=Parser(url); p.feed(blob.decode('utf-8',errors='replace'))
        parsed=Parsed(event_id=eid,text='\n'.join(x.strip() for x in ''.join(p.text).splitlines() if x.strip()),links=p.links)
        save(d/'parsed.json',parsed)
    logging.warning(event.model_dump_json())
if __name__=='__main__': capture(sys.argv[1],sys.argv[2])
