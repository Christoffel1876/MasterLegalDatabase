"""Prepare an additive scanner revision; preserve root scanner and earlier scan exactly."""
import hashlib
import json
import shutil
from pathlib import Path

R=Path('/Users/mcoors/Documents/Project Geode/MasterLegalDatabase')
B=R.parent/'handoffs/run-2026-09-13'
A=B/'plato-packaging-scan-audit'
assert not A.exists()
(A/'original').mkdir(parents=True)
(A/'proposed').mkdir()
shutil.copyfile('/private/tmp/geode_packaging_scan.py',A/'original/geode_packaging_scan.py')
shutil.copyfile('/private/tmp/plato-packaging-scanner-probe.py',A/'original_repro.py')
shutil.copytree(B/'atlas-final-packaging/before-final-install',A/'before-final-install')
t=(A/'original/geode_packaging_scan.py').read_text()
t=t.replace('import argparse, json, subprocess','import argparse, io, json, subprocess')
t=t.replace("dst=B/'atlas-final-packaging'/args.name", "dst=B/'plato-packaging-scan-audit'/'proposed-runs'/args.name")
t=t.replace('selected:dict[str,set[str]]={}', "selected:dict[str,set[str]]={}\nexpected_identities:dict[str,tuple[str,int]]={}\nBASELINE_HEAD='512684a65ae3c4eb51509b23520cfe41823ca0b9'\nif git('rev-parse','HEAD').decode().strip()!=BASELINE_HEAD:raise ValueError('reviewed HEAD changed')")
t=t.replace('def add(rel:str,basis:str)->None:', 'def add(rel:str,basis:str,expected:tuple[str,int])->None:')
t=t.replace(" selected.setdefault(rel,set()).add(basis)", """ if any(name.casefold()==rel.casefold() and name!=rel for name in selected):
  raise ValueError('case-aliased packaging member '+rel)
 if rel in expected_identities and expected_identities[rel]!=expected:
  raise ValueError('conflicting expected identity '+rel)
 if hashasset(R/rel)!=expected:raise ValueError('selected identity drift '+rel)
 expected_identities[rel]=expected
 selected.setdefault(rel,set()).add(basis)

def bound_json(rel:str)->dict:
 if rel not in expected_identities:raise ValueError('unbound metadata '+rel)
 p=R/rel;raw=p.read_bytes()
 if (sha256(raw).hexdigest(),len(raw))!=expected_identities[rel]:
  raise ValueError('metadata identity drift '+rel)
 return json.loads(raw)
""")
t=t.replace("root=inv.parent;obj=json.loads(inv.read_bytes());", "root=inv.parent;inv_raw=inv.read_bytes();obj=json.loads(inv_raw);")
t=t.replace("add(p.relative_to(R).as_posix(),'closed wrapper '+root.name)", "add(p.relative_to(R).as_posix(),'closed wrapper '+root.name,(a['sha256'],a['size_bytes']))")
t=t.replace("add(inv.relative_to(R).as_posix(),'closed wrapper inventory')", "add(inv.relative_to(R).as_posix(),'closed wrapper inventory',(sha256(inv_raw).hexdigest(),len(inv_raw)))")
t=t.replace("prior=json.loads((B/'ptolemy-inventory69-packaging-audit/NEEDED_FORCE_ADD.json').read_bytes())", """prior_raw=(B/'ptolemy-inventory69-packaging-audit/NEEDED_FORCE_ADD.json').read_bytes()
if sha256(prior_raw).hexdigest()!='94ce696f540b45cfa2aa5fb6fc792adce5422b971fc7f4960b3fa013852284c0':
 raise ValueError('independent ignored-payload proposal changed')
prior=json.loads(prior_raw)""")
t=t.replace("add(a['path'],'independent packaging audit pin')", "add(a['path'],'independent packaging audit pin',(a['sha256'],a['size_bytes']))")
t=t.replace("old=git('show','HEAD:'+manifest)", "old=git('show',BASELINE_HEAD+':'+manifest)")
t=t.replace("new=[json.loads(line) for line in now[len(old):].splitlines()]", """if not old.endswith(b'\\n'):raise ValueError('historical manifest missing newline')
with io.BytesIO(now[len(old):]) as stream:new=[json.loads(line) for line in stream]
APPROVED_RAW = """+repr({json.loads(line)['record_id']:(json.loads(line)['archive_path'],json.loads(line)['sha256'],json.loads(line)['size_bytes']) for line in (R/'_RAW_ARCHIVE/manual_intake/manual_source_intake_manifest.jsonl').read_bytes().splitlines()[-6:]})+"""
if len({a['record_id'] for a in new})!=6 or {a['record_id'] for a in new}!=set(APPROVED_RAW):
 raise ValueError('selected raw source IDs differ')
for a in new:
 if (a['archive_path'],a['sha256'],a['size_bytes'])!=APPROVED_RAW[a['record_id']]:
  raise ValueError('selected raw source identity differs')""")
t=t.replace("add(a['archive_path'],'new raw original exact appended manifest')", "add(a['archive_path'],'new raw original exact appended manifest',(a['sha256'],a['size_bytes']))")
start=t.index('# Actual fee-intake snapshot')
end=t.index("allowed={'_CONTROL_PLANE",start)
t=t[:start]+'''# Bind snapshot contents to previously reviewed custody, not a directory crawl.
fee='research/local_review/chaffee-planning-fees-intake-2026-09-13/prepared-transaction/'
fee_plan=bound_json(fee+'PREPARATION.json')
if expected_identities[fee+'PREPARATION.json'][0]!='a25b2071c9275af9b7299edf198b96870a79ba5ac8e0c412f6b8647774d683ca':
 raise ValueError('fee preparation changed')
fee_snapshot='_SNAPSHOTS/CHAFFEE-20260913T170209370066Z/'
for a in fee_plan['baseline']:
 if a['repository_path'] in {manifest,'_CONTROL_PLANE/MANUAL_SOURCE_INTAKE_LEDGER.jsonl','_CONTROL_PLANE/MANUAL_SOURCE_INTAKE_REPORT.json'}:
  pin=a['preserved'];add(fee_snapshot+a['repository_path'],'actual fee-intake preimage snapshot',(pin['sha256'],pin['size_bytes']))
prefix='research/local_review/manual-source-review-inventory-2026-09-11/'
ordinary_raw=(B/'ptolemy-inventory69-packaging-audit/UNTRACKED_ORDINARY.json').read_bytes()
if sha256(ordinary_raw).hexdigest()!='caadb14d9eb61a67a1e81afa78265fd627aec626ffce464dcc30c8cff14ed7fe':
 raise ValueError('independent ordinary-payload proposal changed')
for a in json.loads(ordinary_raw)['files']:
 if a['path'].startswith(prefix):
  add(a['path'],'previous independent inventory packaging pin',(a['sha256'],a['size_bytes']))
installed='research/local_review/manual-inventory-final-fee-code-integration-2026-09-13/'
receipt=bound_json(installed+'execution/RECEIPT.json')
receipt_schema=bound_json(installed+'execution/RECEIPT.schema.json')
jsonschema.validate(receipt,receipt_schema)
if expected_identities[installed+'execution/RECEIPT.json'][0]!='dbc0aa616f217dca664cfbbc587d22d3ae2f5cb57289c99188391b74a8bd6cde':
 raise ValueError('final inventory installation differs')
for a in receipt['targets']:
 pin=a['after'];add(a['repository_path'],'root-reviewed final inventory installation',(pin['sha256'],pin['size_bytes']))
preimage=bound_json(installed+'preparation/PREIMAGE_RECEIPT.json')
jsonschema.validate(preimage,bound_json(installed+'preparation/PREIMAGE_RECEIPT.schema.json'))
for a in preimage['files']:
 add(receipt['snapshot_directory']+'/'+Path(a['repository_path']).name,'final inventory exact preimage',(a['sha256'],a['size_bytes']))
unknown_inventory=[]
for item in git('ls-files','--others','--exclude-standard','-z','--',prefix).split(b'\\0'):
 if item and item.decode() not in selected:unknown_inventory.append(item.decode())
if unknown_inventory:raise ValueError('unbound inventory files require review: '+repr(unknown_inventory))
# A future CI installation must itself be bound by its closed wrapper and exact schema.
ci_files=set()
ci='research/local_review/manual-watch-ci-integration-2026-09-13/INSTALLATION.json'
if (R/ci).exists():
 d=bound_json(ci);ci_schema=bound_json(ci.removesuffix('.json')+'.schema.json')
 jsonschema.validate(d,ci_schema)
 for a in d['installed_files']:
  if a['path'] in ci_files:raise ValueError('duplicate CI installed path')
  ci_files.add(a['path'])
  add(a['path'],'root-reviewed CI installation',(a['sha256'],a['size_bytes']))
''' +t[end:]
t=t.replace("if rel not in allowed:", "if rel not in allowed|ci_files:")
t=t.replace("add(rel,'reviewed maintained change')", "add(rel,'explicit maintained change snapshot',expected_identities.get(rel,hashasset(R/rel)))")
t=t.replace("add('tests/test_chaffee_source_path.py','reviewed publisher-path regression tests')", "add('tests/test_chaffee_source_path.py','reviewed publisher-path regression tests',('01088333afd68e8b9fe9d61156725cc0505bb7e9c59a7296c90a54d9d1248f6e',(R/'tests/test_chaffee_source_path.py').stat().st_size))")
start=t.index('# CI files are included only')
end=t.index('paths=sorted(selected)',start)
t=t[:start]+t[end:]
t=t.replace('h,n=hashasset(R/rel)\n if n>', "h,n=hashasset(R/rel)\n if (h,n)!=expected_identities[rel]:raise ValueError('final identity drift '+rel)\n if n>")
t=t.replace("scan=Scan(status=", "if git('rev-parse','HEAD').decode().strip()!=BASELINE_HEAD:raise ValueError('HEAD changed during scan')\nscan=Scan(status=")
(A/'proposed/geode_packaging_scan.py').write_text(t)
shutil.copyfile(__file__,A/'prepare_revision.py')
print(A)
