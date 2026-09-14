"""Freeze the exact observed planning-fee Location before any new GET."""
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from bs4 import BeautifulSoup

from models import Attempt, Manifest, Plan, PlanFreeze, Reservation, Target

ROOT=Path(__file__).resolve().parent
PRIOR_SHA='0ad7b970736921a175de778e05629db8b9191ba2394a692d3715c0a51421c95f'


def now() -> str:
    """Capture the actual UTC clock."""
    return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')


def put(path: Path,data: bytes) -> None:
    """Create an ordinary new payload atomically; never overwrite."""
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists() or path.is_symlink():
        raise ValueError('existing output')
    tmp=path.with_name(path.name+'.tmp')
    with tmp.open('xb') as stream:
        stream.write(data)
    os.replace(tmp,path)


def ref(path: Path):
    """Bind exact package-relative evidence bytes."""
    from models import FileRef
    data=path.read_bytes()
    return FileRef(path=path.relative_to(ROOT).as_posix(),
                   sha256=hashlib.sha256(data).hexdigest(),size_bytes=len(data))


def main() -> None:
    """Validate the exact retained Location and freeze a one-target initial admission."""
    prior=ROOT/'evidence/prior-retrieval'
    if ref(prior/'FINAL_MANIFEST.json').sha256 != PRIOR_SHA:
        raise ValueError('prior packet pin differs')
    original_manifest=Manifest.model_validate_json(
        (prior/'FINAL_MANIFEST.json').read_bytes().replace(
            b'chaffee-directed-public-custody-v1',b'chaffee-fee-directed-public-custody-v1'))
    for record in original_manifest.files:
        data=(prior/record.path).read_bytes()
        if len(data)!=record.size_bytes or hashlib.sha256(data).hexdigest()!=record.sha256:
            raise ValueError('prior payload differs')
    event=Attempt.model_validate_json((prior/'events/A003/RESULT.json').read_bytes())
    if event.http_status!=302 or not event.body_complete or event.partial_or_unknown:
        raise ValueError('prior response not a complete redirect')
    raw_headers=(prior/'events/A003/public-response.headers').read_bytes()
    locations=[x.split(b':',1)[1].strip().decode('utf-8') for x in raw_headers.splitlines()
               if x.lower().startswith(b'location:')]
    if len(locations)!=1 or locations[0]!=event.location:
        raise ValueError('ambiguous or mismatched Location')
    raw_location=locations[0]
    anchors=[a.get('href') for a in BeautifulSoup(
        (prior/'events/A003/response.body').read_bytes(),'html.parser').find_all('a',href=True)]
    if anchors != [raw_location]:
        raise ValueError('redirect body and Location disagree')
    encoded=raw_location.replace(' ','%20')
    parsed=urlsplit(encoded)
    if (parsed.scheme!='https' or parsed.netloc!='cms2.revize.com' or
        not parsed.path.startswith('/revize/chaffeecounty/')):
        raise ValueError('outside exact Chaffee tenant')
    target=Target(target_id='CHAFFEE-FEE-D001',authority_id='CO-COUNTY-CHAFFEE',layer_id='08',
        prior_request_url=event.requested_url,prior_response_body=ref(prior/'events/A003/response.body'),
        prior_public_headers=ref(prior/'events/A003/public-response.headers'),
        prior_actual_result=ref(prior/'events/A003/RESULT.json'),
        prior_frozen_manifest=ref(prior/'FINAL_MANIFEST.json'),raw_location=raw_location,
        request_url=encoded,
        encoding_rule='Preserve raw Location; replace literal spaces with %20 exactly once',
        evidence_limit='A003 is the actual previously captured ordinary-TLS county HTTP 302. '
        'Its exact public Location and redirect-body href agree. The original catalog anchor '
        'and earlier supplied discovery custody remain separately preserved and qualified. '
        'This new GET is not a retry of A003 and does not recover its omitted header fields.',
        anticipated_role='County planning Application Fee Schedule lead; body/edition/role '
        'unverified until actual response and source review.',legal_currentness='not_verified')
    plan=Plan(schema_version='chaffee-fee-directed-plan-v1',prepared_at=now(),
        status='PREPARED_NOT_EXECUTED',targets=[target],maximum_actions=3,maximum_distinct_urls=3,
        maximum_body_bytes=20000000,maximum_total_body_bytes=30000000,request_seconds=60,
        connect_seconds=15,no_start_after='2026-09-13T17:45:00Z',finish_by='2026-09-13T18:00:00Z',
        redirects=False,retries=0,request_user_agent='Geode/1.0 (public source preservation; read-only)',
        authorization='Atlas explicitly authorized this new exact-Location fee gap-fill under '
        'Michael\'s active public source work. Narrow ordinary network escalation is authorized '
        'after the established sandbox DNS limitation. No auth/cookies or denial bypass.',
        limitations=['Only this initial exact target is admitted by this plan. Any subsequent '
            'explicit same-Chaffee-tenant Location would require a separately frozen additive '
            'admission and deliberate GET; no automatic redirect, retry, search or link expansion.',
            'Maximum three deliberate events/three distinct URLs, 20MB per body/30MB total. '
            'Stop on partial/unknown/capped bodies, 401/403 or a security wall. Unused budget '
            'does not authorize new document discovery. No source QA or canonical intake here.'])
    put(ROOT/'PLAN.json',(plan.model_dump_json(indent=2)+'\n').encode())
    for name,model in [('PLAN',Plan),('PLAN_FREEZE',PlanFreeze),('ATTEMPT',Attempt),
                       ('RESERVATION',Reservation),('MANIFEST',Manifest)]:
        put(ROOT/(name+'.schema.json'),(json.dumps(model.model_json_schema(),indent=2)+'\n').encode())
    freeze=PlanFreeze(frozen_at=now(),plan=ref(ROOT/'PLAN.json'),
        schema_file=ref(ROOT/'PLAN.schema.json'),
        evidence=[ref(p) for p in sorted(prior.rglob('*')) if p.is_file()],
        public_actions_before_freeze=0)
    put(ROOT/'PLAN_FREEZE.json',(freeze.model_dump_json(indent=2)+'\n').encode())


if __name__=='__main__':
    main()
