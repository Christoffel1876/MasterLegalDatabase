"""Read-only receipt verification; never execute retained lookup code or probes."""
import argparse,hashlib,json,sys
from pathlib import Path,PurePosixPath
import jsonschema

def safe(root,name):
 p=PurePosixPath(name)
 if p.is_absolute() or '..' in p.parts or '\\' in name:raise ValueError('unsafe path')
 f=root.joinpath(*p.parts)
 if not f.is_file() or any(x.is_symlink() for x in [f,*f.parents]):raise ValueError('unsafe file')
 return f

def check(root,ref):
 raw=safe(root,ref['path']).read_bytes()
 if len(raw)!=ref['size_bytes'] or hashlib.sha256(raw).hexdigest()!=ref['sha256']:raise ValueError('changed '+ref['path'])
 return raw

def validate(root,pin):
 root=root.expanduser().absolute();raw=safe(root,'FINAL_MANIFEST.json').read_bytes()
 if hashlib.sha256(raw).hexdigest()!=pin:raise ValueError('manifest pin mismatch')
 m=json.loads(raw);names=[r['path'] for r in m['files']]
 for p in root.rglob('*'):
  if p.is_symlink() or not(p.is_file() or p.is_dir()):raise ValueError('nonordinary member')
 actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
 if len(names)!=len(set(names)) or actual!=set(names)|{'FINAL_MANIFEST.json'}:raise ValueError('closed inventory mismatch')
 for r in m['files']:check(root,r)
 for stem in ['FINAL_MANIFEST','REVIEW']:
  jsonschema.Draft202012Validator(json.loads(safe(root,stem+'.schema.json').read_bytes())).validate(json.loads(safe(root,stem+'.json').read_bytes()))
 r=json.loads(safe(root,'REVIEW.json').read_bytes());received=check(root,r['proposal_manifest'])
 if hashlib.sha256(received).hexdigest()!='e7a292b0774d2c53585836267d97f36854c183f67c3cadd2fdc8bef6a35ebb18':raise ValueError('proposal pin differs')
 p=json.loads(received)
 for ref in p['files']:check(root/'received',ref)
 if {q.relative_to(root/'received').as_posix() for q in (root/'received').rglob('*') if q.is_file()}!={v['path'] for v in p['files']}|{'FINAL_MANIFEST.json','FINAL_MANIFEST.schema.json'}:raise ValueError('received closure differs')
 for ref in [r['proposed_code'],*r['checks'].values()]:check(root,ref)
 late=json.loads(check(root,r['checks']['late_qa']));aba=json.loads(check(root,r['checks']['aba']));positive=json.loads(check(root,r['checks']['positive']))
 if late['status']!='no_matching_row' or late['row_ids'] or late['expected_review_sha256']!=late['reported_review_sha256']:raise ValueError('late-read disposition differs')
 if aba['status']!='PASS' or len(aba['cases'])!=2 or positive['status']!='PASS' or len(positive['legacy_output_comparisons'])!=14:raise ValueError('probe receipt differs')
 return {'status':'PASS','payloads':len(names),'received_payloads':len(p['files']),'public_requests':0,'probes_rerun':False}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).parent);p.add_argument('--manifest-sha256',required=True);a=p.parse_args()
 try:result=validate(a.root,a.manifest_sha256)
 except Exception as e:sys.stderr.write(str(e)+'\n');raise SystemExit(1)
 sys.stdout.write(json.dumps(result,indent=2)+'\n')
