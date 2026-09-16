"""Read-only replay of the audit receipt and optional accepted-package byte comparisons."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import jsonschema
from audit_packages import Audit,Ref,check,ref,safe,HERE
from finish_audit import Scope,Manifest

def main()->None:
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--repository',type=Path)
 args=parser.parse_args()
 m=Manifest.model_validate_json((HERE/'FINAL_MANIFEST.json').read_bytes())
 actual={str(p.relative_to(HERE)) for p in HERE.rglob('*') if p.is_file()}
 names={x.path for x in m.files}
 if len(names)!=len(m.files) or actual!=names|{'FINAL_MANIFEST.json','FINAL_MANIFEST.schema.json'}:
  raise ValueError('Closed audit file set differs')
 for item in m.files:check(HERE,item)
 a=Audit.model_validate_json((HERE/'AUDIT.json').read_bytes())
 s=Scope.model_validate_json((HERE/'SCOPE_CHECK.json').read_bytes())
 for name in ['AUDIT','SCOPE_CHECK','FINAL_MANIFEST']:
  jsonschema.validate(json.loads((HERE/(name+'.json')).read_bytes()),
                      json.loads((HERE/(name+'.schema.json')).read_bytes()))
 if a.status!='PASS' or a.issues or s.scope_issues or not a.canonical_guards_unchanged:
  raise ValueError('Audit contains unresolved issues')
 if (a.current_raw_records,a.current_ledger_records)!=(64,65):raise ValueError('Count differs')
 for item in a.validators:
  check(HERE,item.stdout);check(HERE,item.stderr)
  if item.exit_code!=0:raise ValueError('Failed validator')
 for item in a.packages:
  n=Path(item.package).name
  copied=ref(HERE,HERE/'received'/n/'ROOT_ACCEPTANCE.json')
  if copied.sha256!=item.root_acceptance.sha256:raise ValueError('Acceptance copy differs')
  if args.repository:
   package=args.repository/item.package
   names={f.path for f in item.all_package_files}
   actual={str(p.relative_to(package)) for p in package.rglob('*') if p.is_file()}
   if actual!=names:raise ValueError('Accepted package set changed')
   for f in item.all_package_files:check(package,f)
 print(json.dumps({'status':'PASS','audit_payloads':len(m.files),'accepted_packages':3,
   'root_package_bytes_rechecked':args.repository is not None,'public_requests':0,
   'canonical_mutations':0,'visual_review_repeated':False},indent=2))
if __name__=='__main__':main()
