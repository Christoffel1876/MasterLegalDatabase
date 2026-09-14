"""Closed read-only review receipt validation; no probe or proposal execution."""
from pathlib import Path,PurePosixPath
import argparse,hashlib,json,sys
import jsonschema

def check(root,item):
 p=PurePosixPath(item['path'])
 if p.is_absolute() or '..' in p.parts or '\\' in item['path']:raise ValueError('unsafe reference')
 f=root.joinpath(*p.parts)
 if not f.is_file() or any(x.is_symlink() for x in [f,*f.parents]):raise ValueError('unsafe file')
 data=f.read_bytes()
 if len(data)!=item['size_bytes'] or hashlib.sha256(data).hexdigest()!=item['sha256']:raise ValueError('changed evidence')
 return data

def validate(root,expected):
 root=root.expanduser().absolute();p=root/'FINAL_MANIFEST.json'
 if any(x.is_symlink() for x in [p,*p.parents]):raise ValueError('symlink root')
 raw=p.read_bytes()
 if hashlib.sha256(raw).hexdigest()!=expected:raise ValueError('external pin')
 manifest=json.loads(raw);names=[x['path'] for x in manifest['files']];actual=set()
 for f in root.rglob('*'):
  if f.is_symlink():raise ValueError('symlink member')
  if f.is_file():actual.add(f.relative_to(root).as_posix())
  elif not f.is_dir():raise ValueError('special file')
 if len(names)!=len(set(names)) or actual!=set(names)|{'FINAL_MANIFEST.json'}:raise ValueError('closure')
 for item in manifest['files']:check(root,item)
 for name in ['REVIEW','FINAL_MANIFEST']:
  jsonschema.Draft202012Validator(json.loads((root/(name+'.schema.json')).read_bytes())).validate(json.loads((root/(name+'.json')).read_bytes()))
 review=json.loads((root/'REVIEW.json').read_bytes());old=check(root,review['input_manifest'])
 if hashlib.sha256(old).hexdigest()!='ef2d664301fa00935100307628ec5ac0317bfd622480dc79c0d92ce44b8b159f':raise ValueError('proposal pin')
 previous=json.loads(old);expected_names={x['path'] for x in previous['files']}|{'FINAL_MANIFEST.json'}
 if expected_names!={f.relative_to(root/'received').as_posix() for f in (root/'received').rglob('*') if f.is_file()}:raise ValueError('proposal closure')
 for item in previous['files']:check(root/'received',item)
 for item in review['evidence']:check(root,item)
 if review['results']['replay']!=json.loads((root/'REPLAY_RESULTS.json').read_bytes()) or review['results']['positive']!=json.loads((root/'POSITIVE_RESULTS.json').read_bytes()):raise ValueError('result consistency')
 return {'status':'PASS','review_payloads':len(names),'proposal_payloads':94,'disposition':review['status'],'public_requests':0,'probes_rerun':False}

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path(__file__).parent);p.add_argument('--manifest-sha256',required=True);a=p.parse_args()
 try:r=validate(a.root,a.manifest_sha256)
 except Exception as error:sys.stderr.write(type(error).__name__+': '+str(error)+'\n');raise SystemExit(1)
 sys.stdout.write(json.dumps(r,indent=2)+'\n')
