"""Serial public verified-TLS GETs with explicit finite bounds and no auto redirects."""
from datetime import datetime,timezone
from hashlib import sha256
import json
from pathlib import Path
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request

from models import Access,Event

ROOT=Path(__file__).resolve().parent
URLS=['https://planningdevelopment.elpasoco.com/',
'https://epc-assets.elpasoco.com/wp-content/uploads/sites/12/Misc/25-290.pdf']
CAP=10485760

class NoRedirect(urllib.request.HTTPRedirectHandler):
    """Expose redirects as separately counted events."""
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        return None

def now():
    return datetime.now(timezone.utc).isoformat()

def asset(path):
    raw=path.read_bytes()
    return {'path':path.relative_to(ROOT).as_posix(),'sha256':sha256(raw).hexdigest(),'size_bytes':len(raw)}

def main():
    if (ROOT/'ACCESS.json').exists(): raise ValueError('Attempt already frozen')
    for cls,name in [(Access,'ACCESS'),(Event,'EVENT')]:
        (ROOT/(name+'.schema.json')).write_text(json.dumps(cls.model_json_schema(),indent=2)+'\n')
    opener=urllib.request.build_opener(NoRedirect(),urllib.request.HTTPSHandler(context=ssl.create_default_context()))
    events=[];targets=set();total=0;stop=False
    for initial in URLS:
        url=initial
        while True:
            if len(events)>=7 or len(targets|{url})>6 or total>=2*CAP: stop=True;break
            seq=len(events)+1;reserved=now();targets.add(url)
            (ROOT/f'event-{seq:02}.reserved.txt').write_text(reserved+'\n'+url+'\n')
            event={'sequence':seq,'requested_url':url,'returned_url':None,'reserved_at':reserved,
                'started_at':now(),'finished_at':now(),'status':None,'outcome':'failed','body':None,
                'headers':{},'omitted_header_names':[],'redirect_location':None,'error':None,'complete':False}
            try:
                try: response=opener.open(url,timeout=25)
                except urllib.error.HTTPError as e: response=e
                with response:
                    event['status']=response.status;event['returned_url']=response.geturl()
                    safe={'content-type','content-length','content-disposition','last-modified','date','etag','location','server'}
                    event['headers']={k:v for k,v in response.headers.items() if k.lower() in safe}
                    event['omitted_header_names']=sorted({k for k in response.headers.keys() if k.lower() not in safe})
                    location=response.headers.get('Location')
                    event['redirect_location']=location
                    bound=min(CAP,2*CAP-total)
                    length=response.headers.get('Content-Length')
                    if length is not None and int(length)>bound:
                        event['outcome']='limit_refusal';event['error']='Declared body exceeds remaining cap';stop=True
                    else:
                        chunks=[];count=0
                        while count<bound:
                            part=response.read(min(65536,bound-count))
                            if not part: event['complete']=True;break
                            chunks.append(part);count+=len(part)
                        raw=b''.join(chunks);total+=len(raw)
                        path=ROOT/f'event-{seq:02}.body';path.write_bytes(raw);event['body']=asset(path)
                        if not event['complete']:
                            event['outcome']='limit_refusal';event['error']='Read cap reached without certified EOF';stop=True
                        elif response.status in (301,302,303,307,308): event['outcome']='redirect'
                        elif response.status in (401,403): event['outcome']='denied';stop=True
                        else: event['outcome']='received'
            except Exception as e:
                event['error']=type(e).__name__+': '+str(e);stop=True
            event['finished_at']=now();typed=Event.model_validate_json(json.dumps(event))
            (ROOT/f'event-{seq:02}.json').write_text(typed.model_dump_json(indent=2)+'\n');events.append(event)
            if stop or event['outcome']!='redirect': break
            candidate=urllib.parse.urljoin(url,event['redirect_location'] or '')
            parsed=urllib.parse.urlsplit(candidate)
            if parsed.scheme!='https' or parsed.hostname not in {'planningdevelopment.elpasoco.com','epc-assets.elpasoco.com'}:
                stop=True;break
            url=candidate
        if stop: break
    receipt={'recorded_at':now(),'request_cap':8,'distinct_target_cap':6,
        'per_response_byte_cap':CAP,'aggregate_byte_cap':2*CAP,'deliberate_attempts':len(events),
        'distinct_targets':len(targets),'retained_body_bytes':total,'tls_verification':True,
        'cookies_or_authentication_used':False,'events':events,
        'limitations':['Counts deliberate urllib requests including explicit redirects, not hidden DNS/TLS/wire packets.',
            'Only a selected public response-header derivative is retained; omitted header names are recorded, values are not saved.',
            'Normal verified TLS; no authentication, cookie jar, denial bypass or retries. No legal-currentness certification.']}
    typed=Access.model_validate_json(json.dumps(receipt));(ROOT/'ACCESS.json').write_text(typed.model_dump_json(indent=2)+'\n')
    sys.stdout.write(json.dumps({'events':[(e['sequence'],e['status'],e['outcome'],e['body']) for e in events]},indent=2)+'\n')

if __name__=='__main__':main()
