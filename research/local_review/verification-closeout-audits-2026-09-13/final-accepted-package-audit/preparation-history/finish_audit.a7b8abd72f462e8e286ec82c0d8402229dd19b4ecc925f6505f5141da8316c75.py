"""Freeze additive scope verification without modifying any accepted input."""
from pathlib import Path
import json,hashlib,os,sys
from typing import Literal
from datetime import datetime,timezone
from pydantic import BaseModel,ConfigDict
from audit_packages import Audit,Ref,ref,save,ROOT,HERE
class ScopeItem(BaseModel):
 model_config=ConfigDict(extra='forbid',strict=True)
 source_id:str
 authority_id:str
 source_sha256:str
 matching_canonical_layer:str
 accepted_scope:dict[str,int]
 measured_verifier_scope:dict[str,int]
 external_report_scope:str
class Scope(BaseModel):
 model_config=ConfigDict(extra='forbid',strict=True)
 observed_at:str
 items:list[ScopeItem]
 blocked_original_transaction_sha256:str
 accepted_revision_transaction_sha256:str
 original_remains_blocked:Literal[True]
 scope_issues:list[str]
class Manifest(BaseModel):
 model_config=ConfigDict(extra='forbid',strict=True)
 status:Literal['FROZEN_READ_ONLY_AUDIT']
 files:list[Ref]
 canonical_mutations:Literal[0]=0
 source_requests:Literal[0]=0
 repeated_visual_review:Literal[False]=False

def main()->None:
 a=Audit.model_validate_json((HERE/'AUDIT.json').read_bytes())
 with (ROOT/'_RAW_ARCHIVE/manual_intake/manual_source_intake_manifest.jsonl').open() as f:
  rows={r['record_id']:r for l in f if (r:=json.loads(l))}
 items=[]
 expected=[('larimer-equity-fee-memo-sd007-05','CO-COUNTY-LARIMER','08_County_Authorities'),
           ('el-paso-boh-bylaws-sd011','CO-COUNTY-EL_PASO','08_County_Authorities')]
 for p,c,(source_id,authority,layer) in zip(a.packages[1:],a.validators[1:],expected):
  package=ROOT/p.package
  accept=json.loads((package/'ROOT_ACCEPTANCE.json').read_bytes())
  measured=json.loads((HERE/c.stdout.path).read_bytes())
  qa=json.loads((package/'independent-review/SOURCE_QA.json').read_bytes())
  assert accept['source_id']==qa['source_id']==source_id
  assert accept['authority_id']==qa['authority_id']==authority
  source_sha=accept['source']['sha256']
  assert rows[source_id]['sha256']==source_sha and rows[source_id]['layer_id']==layer
  assert ref(ROOT,ROOT/rows[source_id]['archive_path']).sha256==source_sha
  for k,v in accept['validated_scope'].items():
   if k in measured:assert measured[k]==v
  if source_id.startswith('el-paso'):
   assert len(qa['sections'])==accept['validated_scope']['sections']
  items.append(ScopeItem(source_id=source_id,authority_id=authority,source_sha256=source_sha,
   matching_canonical_layer=layer,accepted_scope=accept['validated_scope'],
   measured_verifier_scope={k:v for k,v in measured.items() if type(v) is int},
   external_report_scope=('No external reports consulted or duplicated in EB023 independent source QA; external delivery status remains separate.'
    if source_id.startswith('larimer') else 'Complete received EB024 reports preserved and scoped reconciliation retained; caption-mediated chronology remains reported.')))
 blocked='ba0a1083641f99f6d06fe739bffc4b53d9615aad0eef83b9035b61cd741f009d'
 accepted='dcacd5e6de2cb8bc7b3e37a8dcc20b705f97c8e90747768227b4b8b8b478c5f2'
 cp=ROOT/a.packages[0].package
 assert ref(cp,cp/'prepared-transaction/transaction.py').sha256==accepted
 assert ref(cp,cp/'prepared-transaction/historical/before-fixed-scope-repair/transaction.py').sha256==blocked
 text=(cp/'README.md').read_text()
 assert 'original proposal remains blocked' in text.lower()
 save('received/COUNTY_REVISION_DISPOSITION.md',(ROOT/'research/local_review/extended-pending-work-2026-09-13/COUNTY_REVISION_DISPOSITION.md').read_bytes())
 scope=Scope(observed_at=datetime.now(timezone.utc).isoformat(),items=items,
  blocked_original_transaction_sha256=blocked,accepted_revision_transaction_sha256=accepted,
  original_remains_blocked=True,scope_issues=[])
 raw=(scope.model_dump_json(indent=2)+'\n').encode();Scope.model_validate_json(raw)
 save('SCOPE_CHECK.json',raw);save('SCOPE_CHECK.schema.json',(json.dumps(Scope.model_json_schema(),indent=2)+'\n').encode())
 print(scope.model_dump_json(indent=2))
if __name__=='__main__':main()
