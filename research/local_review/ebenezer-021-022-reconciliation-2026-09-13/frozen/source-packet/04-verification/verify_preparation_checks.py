from pathlib import Path
from datetime import datetime,timezone
import sys,json,shutil,tempfile,hashlib,subprocess,os
from pydantic import BaseModel,ConfigDict
base=Path('/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-12/extended-run/ebenezer-021-022')
sys.dont_write_bytecode=True;sys.path.insert(0,str(base/'04-verification'))
from validate_packet import validate
from models import Identities
start=datetime.now(timezone.utc)
expected=hashlib.sha256((base/'manifest.json').read_bytes()).hexdigest()
initial=validate(base,expected)
# Read-only deterministic check from an unrelated working directory.
p=subprocess.run([sys.executable,'-B',str(base/'04-verification/validate_packet.py'),'--expected-manifest',expected],cwd='/private/tmp',env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),capture_output=True,timeout=60)
assert p.returncode==0,p.stderr
cases=[]
with tempfile.TemporaryDirectory(prefix='eb021-022-',dir='/private/tmp') as temporary:
 for case in ['pdf_tamper','candidate_tamper','missing_page','extra_member','symlink']:
  copy=Path(temporary)/case;shutil.copytree(base,copy)
  if case=='pdf_tamper':
   path=copy/'01-source-only/douglas-ehs-fees-atlas-directed/original.pdf';path.write_bytes(path.read_bytes()+b'changed')
  elif case=='candidate_tamper':
   path=copy/'02-candidate-text/pueblo-planning-fees-atlas-directed/candidate.txt';path.write_bytes(path.read_bytes().replace(b'$50',b'$51',1))
  elif case=='missing_page':(copy/'01-source-only/pueblo-planning-fees-atlas-directed/page-0004.png').unlink()
  elif case=='extra_member':(copy/'unexpected.txt').write_bytes(b'not allowed')
  else:
   path=copy/'01-source-only/douglas-ehs-fees-atlas-directed/original.pdf';path.unlink();path.symlink_to(base/'01-source-only/douglas-ehs-fees-atlas-directed/original.pdf')
  try:validate(copy,expected)
  except ValueError as error:
   assert str(error) != 'Symlink root'
   cases.append({'case':case,'result':'rejected','reason':str(error)})
  else:raise AssertionError('Accepted bad packet '+case)
ids=json.loads((base/'SOURCE_ONLY_IDENTITIES.json').read_bytes())
for case in ['wrong_authority','duplicate_page']:
 changed=json.loads(json.dumps(ids))
 if case=='wrong_authority':changed['documents'][0]['authority_id']='CO-MUNICIPAL-PUEBLO'
 else:changed['documents'][1]['pages'][1]['physical_page']=1
 try:Identities.model_validate_json(json.dumps(changed))
 except ValueError:cases.append({'case':case,'result':'rejected','reason':'typed identity invariant'})
 else:raise AssertionError('Accepted bad identity '+case)
text=(base/'START_HERE.md').read_text()
assert not any(s in text for s in ['You reported','EB018','EB019','EB020','44 rows','43 nested','Initial Inspection','Intial Inspection','two blank'])
assert '03:55:00Z' in text and '04:15:00Z' in text
assert 'EB-PDF-023 is assigned' in text and 'No EB-PDF-023 is assigned' in text
assert '01a08848-5f8e-7c51-9b66-fd82eff860fe' in text
result={'started_at':start.isoformat(),'completed_at':datetime.now(timezone.utc).isoformat(),'initial_manifest_sha256':expected,'status':'passed','portable_cli_exit':p.returncode,'portable_stdout':p.stdout.decode(),'portable_stderr':p.stderr.decode(),'tamper_checks':cases,'packet_check':initial,'all_five_full_images_directly_viewed_for_render_completeness':True,'review_scope':'Technical rendering and packaging only; no new full numerical source QA claimed.','initial_local_setup_failures':['PIL unavailable; PNG dimensions read directly from IHDR instead.','First builder redirection used wrong working directory and wrote no builder; corrected before successful build.','Initial temporary tamper fixtures used a symlinked default temp root and therefore did not reach intended tamper checks; rerun with explicit /private/tmp.'],'source_or_repository_writes':0,'public_requests':0}
Path('/private/tmp/eb021-022-validation-result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
