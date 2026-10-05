"""One root-authorized ordinary system-curl request, preserving default TLS checks."""
from datetime import datetime,timezone
from email.parser import BytesParser
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from models import Event
ROOT=Path(__file__).resolve().parent
URL='https://epc-assets.elpasoco.com/wp-content/uploads/sites/12/Misc/25-290.pdf'
def now():return datetime.now(timezone.utc).isoformat()
def main():
    if (ROOT/'curl-event-04.json').exists():raise ValueError('Already attempted')
    reserved=now();(ROOT/'curl-event-04.reserved.txt').write_text(reserved+'\n'+URL+'\n')
    dest=ROOT/'curl-event-04.body'
    argv=['/usr/bin/curl','--silent','--show-error','--proto','=https','--max-time','25',
          '--max-filesize','10485760','--max-redirs','0','--dump-header','-',
          '--output',str(dest),'--write-out','\nGEODE_HTTP:%{http_code}\n',URL]
    started=now();run=subprocess.run(argv,capture_output=True,timeout=30,check=False);finished=now()
    raw_headers,_,tail=run.stdout.partition(b'\nGEODE_HTTP:')
    status=int(tail.strip() or b'0') or None
    blocks=raw_headers.split(b'\r\n\r\n');last=next((b for b in reversed(blocks) if b.startswith(b'HTTP/')),b'')
    parsed=BytesParser().parsebytes(last.split(b'\r\n',1)[1] if b'\r\n' in last else b'')
    safe={'content-type','content-length','content-disposition','last-modified','date','etag','location','server'}
    headers={k:v for k,v in parsed.items() if k.lower() in safe}
    body=None
    if dest.exists():
        raw=dest.read_bytes();body={'path':dest.name,'sha256':sha256(raw).hexdigest(),'size_bytes':len(raw)}
    outcome='failed' if run.returncode else 'denied' if status in (401,403) else 'redirect' if status in (301,302,303,307,308) else 'received'
    event={'sequence':4,'requested_url':URL,'returned_url':URL if status else None,
           'reserved_at':reserved,'started_at':started,'finished_at':finished,'status':status,
           'outcome':outcome,'body':body,'headers':headers,
           'omitted_header_names':sorted({k for k in parsed.keys() if k.lower() not in safe}),
           'redirect_location':parsed.get('Location'),'error':run.stderr.decode(errors='replace') or None,
           'complete':run.returncode==0}
    valid=Event.model_validate_json(json.dumps(event))
    (ROOT/'curl-event-04.json').write_text(valid.model_dump_json(indent=2)+'\n')
    (ROOT/'curl-pdf.stderr.log').write_bytes(run.stderr)
    sys.stdout.write(json.dumps({'status':status,'outcome':outcome,'body':body,'exit_code':run.returncode},indent=2)+'\n')
if __name__=='__main__':main()
