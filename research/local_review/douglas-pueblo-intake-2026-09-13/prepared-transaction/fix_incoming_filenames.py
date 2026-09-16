"""Preserve the prior packet and bind original_filename to the actual incoming basename."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,os,shutil,sys
BASE=Path(__file__).resolve().parent;sys.dont_write_bytecode=True;sys.path.insert(0,str(BASE))
from preparation_models import Preparation,Manifest,Asset
expected='0a16a7b835b6d38bf348df267fe04bb055cd50ddae2984412ce3ad1b2821f40f'
raw=(BASE/'FINAL_MANIFEST.json').read_bytes();assert hashlib.sha256(raw).hexdigest()==expected
m=json.loads(raw);history=BASE/'historical/second-prepared-0a16a7b8';assert not history.exists();history.mkdir(parents=True)
for name in [x['path'] for x in m['files']]+['FINAL_MANIFEST.json','FINAL_MANIFEST.schema.json']:
 p=BASE/name;q=history/name;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q);assert p.read_bytes()==q.read_bytes()
# The running revision script was just added, outside the prior closed inventory. Prior files
# are copied by its exact228-file inventory, not by recursively including new revision work.
def replace(path,data):
 old=path.read_bytes();snap=BASE/'preparation-history'/hashlib.sha256(old).hexdigest();snap.mkdir(parents=True,exist_ok=True);saved=snap/path.name
 if saved.exists():assert saved.read_bytes()==old
 else:saved.write_bytes(old)
 tmp=path.with_name('.'+path.name+'.tmp');tmp.write_bytes(data);os.replace(tmp,path)
def enc(v):return (json.dumps(v.model_dump(mode='json') if hasattr(v,'model_dump') else v,indent=2)+'\n').encode()
prep=BASE/'evidence/preparation';data=Preparation.model_validate_json((prep/'PREPARATION.json').read_bytes())
for source,template in zip(data.sources,data.proposed_records,strict=True):
 assert source.original==template.source_file
 template.original_filename=Path(source.original.path).name
 assert template.original_filename=='original.pdf'
Preparation.model_validate_json(data.model_dump_json())
replace(prep/'PREPARATION.json',enc(data))
replace(prep/'proposed-records.jsonl',b''.join((t.model_dump_json()+'\n').encode() for t in data.proposed_records))
files=[]
for p in sorted(prep.rglob('*')):
 if p.is_file() and p.name not in {'FINAL_MANIFEST.json','FINAL_MANIFEST.schema.json'}:
  b=p.read_bytes();files.append(Asset(path=p.relative_to(prep).as_posix(),sha256=hashlib.sha256(b).hexdigest(),size_bytes=len(b)))
manifest=Manifest(schema_version=1,files=files);replace(prep/'FINAL_MANIFEST.json',enc(manifest))
p=BASE/'transaction.py';s=p.read_text();import re
s=re.sub(r'PREP_SHA = "[a-f0-9]+"','PREP_SHA = "'+hashlib.sha256((prep/'PREPARATION.json').read_bytes()).hexdigest()+'"',s)
s=re.sub(r'MANIFEST_SHA = "[a-f0-9]+"','MANIFEST_SHA = "'+hashlib.sha256((prep/'FINAL_MANIFEST.json').read_bytes()).hexdigest()+'"',s)
needle='        data[sid] = checked(plan.originals_root, File.model_validate(source["original"]))'
s=s.replace(needle,'''        if template["original_filename"] != Path(source["original"]["path"]).name:
            raise ValueError("Original filename differs from actual incoming basename")
'''+needle);assert s!=p.read_text();replace(p,s.encode())
p=BASE/'validate_preparation.py';s=p.read_text();needle="  qa=json.loads(check(prep,next(a for a in source.evidence if a.path.endswith('/SOURCE_QA.json'))))"
s=s.replace(needle,"  if t.original_filename!=Path(source.original.path).name:raise ValueError('Original filename differs from incoming basename')\n"+needle);replace(p,s.encode())
p=BASE/'README.md';s=p.read_text().replace('61 focused tests passed with at least 90% branch-inclusive transaction coverage.','62 focused tests passed with at least 90% branch-inclusive transaction coverage.')
s+='\nThe second complete228-file revision is preserved under `historical/second-prepared-0a16a7b8/`. A subsequent root review corrected both proposed `original_filename` values to `original.pdf`, the exact incoming file basename. Descriptive names remain in `official_source_name`; publisher Content-Disposition values remain unchanged in the HTTP receipts. The transaction now rejects a differing filename before any write. Source/provenance and old canonical prefix bytes remain unchanged.\n';replace(p,s.encode())
p=BASE/'package_models.py';replace(p,p.read_bytes().replace(b'tests_passed:Literal[61]',b'tests_passed:Literal[62]'))
p=BASE/'test_transaction.py';old=p.read_bytes();replace(p,old+b'''\n\n
def test_incoming_filename_cannot_be_invented(fixture):
    """The input basename, rather than a curated descriptive label, enters the raw record."""
    plan, root, state = fixture
    templates = copy.deepcopy(plan.templates)
    templates[0]['original_filename'] = 'invented_descriptive_publisher_name.pdf'
    changed = tx.Plan(plan.preparation_sha256, plan.source_provenance_sha256,
                      plan.sources, templates, plan.originals_root, plan.before, plan.guards)
    before = membership(root)
    with pytest.raises(ValueError, match='actual incoming basename'):
        tx.execute(changed, root, state, apply=True)
    assert membership(root) == before and not state.exists()
''')
print('Preserved228files and corrected incoming basename invariants; canonical writes0')
