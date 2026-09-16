"""Seal this prepared package without applying any canonical changes."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,sys
BASE=Path(__file__).resolve().parent
sys.dont_write_bytecode=True
sys.path.insert(0,str(BASE))
from package_models import File,Inventory,Validation
from preparation_models import Preparation

def ref(p:Path)->File:
 b=p.read_bytes();return File(path=p.relative_to(BASE).as_posix(),sha256=hashlib.sha256(b).hexdigest(),size_bytes=len(b))
def put(name,data):
 p=BASE/name
 with p.open('xb') as f:f.write(data)
def enc(value):return (json.dumps(value.model_dump(mode='json') if hasattr(value,'model_dump') else value,indent=2)+'\n').encode()
prep=Preparation.model_validate_json((BASE/'evidence/preparation/PREPARATION.json').read_bytes())
coverage=json.loads((BASE/'validation/final-focused/coverage.json').read_bytes())
assert not (BASE/'execution').exists()
# Existing test-prefix snapshot reconstructed from exact retained bytes; not claimed as an earlier-time capture.
test=(BASE/'test_transaction.py').read_bytes();marker=b"\n\n@pytest.mark.parametrize('swap', ['url', 'authority_and_layer'])"
prior=test[:test.index(marker)];snap=BASE/'preparation-history'/'generated-test-prefix-observed-after-addition';snap.mkdir(exist_ok=True)
(snap/'test_transaction.py').write_bytes(prior)
(snap/'README.txt').write_text('Exact prefix of the current test file before three added mixed-owner regressions, retained after addition. This does not claim an earlier capture timestamp. The original reviewed Springs test file is separately preserved unchanged.\n')
from transaction import NewRecord,Intent,Receipt
for name,model in [('NewRecord',NewRecord),('INTENT',Intent),('RECEIPT',Receipt)]:put(name+'.schema.json',enc(model.model_json_schema()))
record=Validation(schema_version=1,checked_at=datetime.now(timezone.utc),status='ready_for_root_review_not_applied',tests_passed=59,branch_inclusive_coverage_percent=float(coverage['totals']['percent_covered']),transaction=ref(BASE/'transaction.py'),tests=ref(BASE/'test_transaction.py'),preparation=ref(BASE/'evidence/preparation/PREPARATION.json'),source_provenance=ref(BASE/'evidence/preparation/source-provenance.jsonl'),preserved_prefixes=[ref(BASE/'evidence/preparation'/b.preserved.path) for b in prep.baseline if b.records is not None],command_receipts=[ref(BASE/'validation'/name/'ATTEMPT.json') for name in ['final-focused','actual-read-only','actual-cli-dry-run']],raw_before=61,ledger_before=62,raw_after_if_applied=63,ledger_after_if_applied=64,current_intake_time=None,legal_currentness='not_verified',qualifications=['Initial host rejection preserved; root subsequently authorized only the verified www.douglasco.gov host with tests.','First pytest invocation from project root used importlib mode and failed collection because transaction was not on import path; no tests ran in that attempt. Correct package-directory invocation passed56, then59 after mixed-authority additions.','Accepted source QA metadata and root acceptances are copied subsets; the complete QA image/test packages remain separately preserved in the repository. No new visual review was performed.','Execution directory is absent. Source acquisition times are actual prior recorded HTTP intervals; future repository receipt remains unknown.','Current61raw/62ledger prefixes unchanged; one historical ledger-only missing original remains missing.'],canonical_writes=0,public_requests=0)
put('VALIDATION.json',enc(record));put('VALIDATION.schema.json',enc(Validation.model_json_schema()))
files=[]
for p in sorted(BASE.rglob('*')):
 if p.is_symlink():raise ValueError('Symlink in closed package')
 if p.is_file():files.append(ref(p))
manifest=Inventory(schema_version=1,status='PREPARED_NOT_APPLIED',prepared_at=datetime.now(timezone.utc),files=files,mutable_execution_directory='execution',execution_directory_present_at_freeze=False,sources=2,physical_pages=5,original_bytes=377549,legal_currentness='not_verified',preparation_canonical_writes=0,public_requests=0)
put('FINAL_MANIFEST.json',enc(manifest));put('FINAL_MANIFEST.schema.json',enc(Inventory.model_json_schema()))
print('FROZEN',len(files)+2,'files',sum(x.size_bytes for x in files)+(BASE/'FINAL_MANIFEST.json').stat().st_size+(BASE/'FINAL_MANIFEST.schema.json').stat().st_size,'bytes')
for name in ['FINAL_MANIFEST.json','VALIDATION.json','transaction.py','test_transaction.py','validate_preparation.py','validate_package.py','evidence/preparation/PREPARATION.json','evidence/preparation/source-provenance.jsonl']:
 print(name,ref(BASE/name).sha256)
