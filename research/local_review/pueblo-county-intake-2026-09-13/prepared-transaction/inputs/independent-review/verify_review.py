"""Portable closed custody and scope check; no network or historical script execution."""
import argparse,hashlib,json,sys
from pathlib import Path,PurePosixPath
import jsonschema

def safe(root,name):
 p=PurePosixPath(name)
 if p.is_absolute() or '..' in p.parts or '\\' in name:raise ValueError('unsafe path')
 f=root.joinpath(*p.parts)
 if not f.is_file() or any(x.is_symlink() for x in [f,*f.parents]):raise ValueError('nonordinary path')
 return f

def checked(root,ref):
 raw=safe(root,ref['path']).read_bytes()
 if len(raw)!=ref['size_bytes'] or hashlib.sha256(raw).hexdigest()!=ref['sha256']:raise ValueError('changed '+ref['path'])
 return raw

def validate(root,pin):
 root=root.expanduser().absolute();raw=safe(root,'FINAL_MANIFEST.json').read_bytes()
 if hashlib.sha256(raw).hexdigest()!=pin:raise ValueError('manifest pin differs')
 manifest=json.loads(raw);names=[r['path'] for r in manifest['files']]
 for p in root.rglob('*'):
  if p.is_symlink() or not(p.is_file() or p.is_dir()):raise ValueError('nonordinary member')
 if len(names)!=len(set(names)) or {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}!=set(names)|{'FINAL_MANIFEST.json'}:raise ValueError('closed inventory differs')
 for ref in manifest['files']:checked(root,ref)
 for stem in ['REVIEW','FINAL_MANIFEST']:
  jsonschema.Draft202012Validator(json.loads(safe(root,stem+'.schema.json').read_bytes())).validate(json.loads(safe(root,stem+'.json').read_bytes()))
 review=json.loads(safe(root,'REVIEW.json').read_bytes())
 for field in ['source','source_qa','source_schema','structural_verifier','checks']:checked(root,review[field])
 qa=json.loads(checked(root,review['source_qa']));schema=json.loads(checked(root,review['source_schema']))
 jsonschema.Draft202012Validator(schema).validate(qa)
 if review['source']['sha256']!=qa['source']['sha256'] or review['direct_visual_pages']!=[1,2]:raise ValueError('source/scope mismatch')
 ids={r['row_id'] for p in qa['pages'] for r in p['rows']}
 if len(ids)!=88 or any(set(f['row_ids'])-ids for f in review['findings']):raise ValueError('row-reference mismatch')
 checks=json.loads(checked(root,review['checks']))
 if checks['status']!='PASS' or checks['source_qa_sha256']!=review['source_qa']['sha256']:raise ValueError('result binding differs')
 for ref in json.loads(safe(root,'received/discovery/RECEIPT.json').read_bytes())['files']:checked(root/'received/discovery/frozen',ref)
 return {'status':'PASS','payloads':len(names),'physical_pages_directly_reviewed':2,'physical_rows':88,'legal_currentness':'not_verified','public_requests':0,'historical_scripts_executed':False}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).parent);p.add_argument('--manifest-sha256',required=True);a=p.parse_args()
 try:r=validate(a.root,a.manifest_sha256)
 except Exception as e:sys.stderr.write(str(e)+'\n');raise SystemExit(1)
 sys.stdout.write(json.dumps(r,indent=2)+'\n')
