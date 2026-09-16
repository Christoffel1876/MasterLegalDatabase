"""Freeze one bounded acquired-source packet after actual local verification."""
from datetime import datetime,timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
from models import Manifest,Verification
from verify import content
ROOT=Path(__file__).resolve().parent

def now():return datetime.now(timezone.utc).isoformat()
def asset(path):
    raw=path.read_bytes();return {'path':path.relative_to(ROOT).as_posix(),'sha256':sha256(raw).hexdigest(),'size_bytes':len(raw)}
def main():
    if (ROOT/'FINAL_MANIFEST.json').exists():raise ValueError('Already sealed')
    data={p.relative_to(ROOT).as_posix():p.read_bytes() for p in ROOT.rglob('*') if p.is_file()}
    failures=[]
    for label,path in [('altered_original','original.pdf'),('altered_referral','referring-homepage.html'),('nonempty_native','page-1.native.txt')]:
        modified=dict(data);modified[path]=modified[path]+b'altered'
        try:content(modified)
        except ValueError:failures.append(label)
        else:raise ValueError('Mutation accepted: '+label)
    modified=dict(data);r=json.loads(modified['SOURCE_REVIEW.json']);r['legal_currentness']='verified';modified['SOURCE_REVIEW.json']=json.dumps(r).encode()
    try:content(modified)
    except ValueError:failures.append('currentness_promotion')
    else:raise ValueError('Currentness promotion accepted')
    argv=[sys.executable,'-B',str(ROOT/'verify.py'),'--unsealed','--rerender','--repository',str(ROOT.parents[2]/'MasterLegalDatabase')]
    started=now();env=dict(os.environ);env['PYTHONDONTWRITEBYTECODE']='1'
    run=subprocess.run(argv,capture_output=True,check=False,timeout=120,env=env);finished=now()
    (ROOT/'verify.stdout.log').write_bytes(run.stdout);(ROOT/'verify.stderr.log').write_bytes(run.stderr)
    if run.returncode:raise ValueError('Final verifier failed')
    model={'started_at':started,'finished_at':finished,'argv':argv,'exit_code':0,
           'stdout':asset(ROOT/'verify.stdout.log'),'stderr':asset(ROOT/'verify.stderr.log'),
           'integrity_cases':failures,'source_review_limit':'Mechanical binding checks plus a same-Codex-family direct visual attestation, not adoption-chain/current-law certification.'}
    (ROOT/'VERIFICATION.schema.json').write_text(json.dumps(Verification.model_json_schema(),indent=2)+'\n')
    receipt=Verification.model_validate_json(json.dumps(model));(ROOT/'VERIFICATION.json').write_text(receipt.model_dump_json(indent=2)+'\n')
    (ROOT/'FINAL_MANIFEST.schema.json').write_text(json.dumps(Manifest.model_json_schema(),indent=2)+'\n')
    payloads=[asset(p) for p in sorted(ROOT.rglob('*')) if p.is_file()]
    obj=Manifest.model_validate_json(json.dumps({'recorded_at':now(),'status':'frozen_literal_source_review_not_current_law','files':payloads}))
    (ROOT/'FINAL_MANIFEST.json').write_text(obj.model_dump_json(indent=2)+'\n')
    sys.stdout.write(json.dumps({'payloads':len(payloads),'manifest':asset(ROOT/'FINAL_MANIFEST.json')},indent=2)+'\n')
if __name__=='__main__':main()
