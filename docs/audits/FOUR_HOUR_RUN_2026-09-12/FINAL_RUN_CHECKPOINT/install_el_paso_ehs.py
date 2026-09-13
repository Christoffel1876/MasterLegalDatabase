"""Install the source-reviewed, independently checked EHS addition with preimages."""
import sys
sys.path.insert(0, '/private/tmp')
from preserve_geode_closing_packets import *
sys.path.insert(0,str(REPO))
from geode.pipeline.manual_review_inventory import Inventory, JoinPlan
from geode.utils.file_io import atomic_write_text
source=RUN/'el-paso-ehs-lookup-integration'
out=AUDIT/'EL_PASO_EHS_LOOKUP'
verify([PYTHON,'-I','-B',str(source/'verify_preparation.py'),'--check-production-preimages',str(REPO)],out/'pre-install-verification.json')
copy_closed(source,out/'prepared-integration','FINAL_MANIFEST.json')
Inventory.model_validate_json((source/'proposed/inventory/inventory.json').read_bytes())
JoinPlan.model_validate_json((source/'proposed/join-plan.json').read_bytes())
assert hashlib.sha256((source/'proposed/research_source_lookup.py').read_bytes()).hexdigest()=='3aeba887caf30e34b5041f8d85caff0a43e7e1f7c8f3e9f17221312f559f8fcf'
base='research/local_review/manual-source-review-inventory-2026-09-11/'
pairs={
'research_source_lookup.py':'scripts/research_source_lookup.py',
'manual_review_inventory.py':'geode/pipeline/manual_review_inventory.py',
'RESEARCH_SOURCE_LOOKUP.md':'docs/RESEARCH_SOURCE_LOOKUP.md',
'join-plan.json':base+'join-plan.json',
 'test_manual_review_inventory.py':'tests/test_manual_review_inventory.py',
 'test_el_paso_ehs_native_lookup.py':'tests/test_el_paso_ehs_native_lookup.py'}
for p in (source/'proposed/inventory').rglob('*'):
 if p.is_file():pairs[p.relative_to(source/'proposed').as_posix()]=base+p.relative_to(source/'proposed/inventory').as_posix()
for p in (source/'proposed/test-fixtures').rglob('*'):
 if p.is_file():pairs[p.relative_to(source/'proposed').as_posix()]='tests/fixtures/'+p.relative_to(source/'proposed/test-fixtures').as_posix()
records=[]
for a,b in pairs.items():
 src=source/'proposed'/a;target=REPO/b
 content=src.read_text()
 if target.exists() and target.read_bytes()==src.read_bytes():continue
 atomic_write_text(target,content,REPO)
 assert target.read_bytes()==src.read_bytes()
 records.append(ref(target,REPO))
readme=REPO/'README.md'
content=readme.read_text()
old='selected fee tables from Grand Junction, Greeley, Weld County and Colorado Springs.'
assert content.count(old)==1
content=content.replace(old,'selected fee tables from Grand Junction, Greeley, Weld County, Colorado Springs\n  and the El Paso County Board of Health English schedule.')
atomic_write_text(readme,content,REPO)
records.append(ref(readme,REPO))
write_acceptance(out,Acceptance(checked_at=datetime.now(timezone.utc).isoformat(),status='installed_independently_checked_source_addition_full_suite_pending',copied_originals=records,verification_artifacts=[ref(out/'pre-install-verification.json',out),ref(out/'independent-portable-verification.json',out)],findings=[
'Root reviewed entire additive EHS implementation, its citation correction, all new tests, one-schema inventory whitelist and preservation-test changes.',
'Independent25source cases found one citation punctuation issue; eight targeted final cases and five boundary checks passed after EHS-only correction; prior six sources JSON/Markdown unchanged.',
'Prepared52tests passed96.03percent combined new-block statement/branch coverage; four inventory tests passed.51lookupcases installed plus one newinventorycase.',
'Installed61source/22mapped-review/39unmapped inventory; all61canonical originals/authority/custody joins and21prior reviews preserved. Earlier61/21snapshot retained.',
'Full source context preserved:65service rows37contexts7groups8060nativebytes; original received-package HTTP uncertainty and Spanish not-reviewed status unchanged.',
'Installed legacy fixtures derive only repository-prefix normalization; frozen original fixtures remain exact in prepared-integration.',
'No canonical append, ordinary query promotion, scheduler, baseline change or public request. Root full regression follows installation.'
]))
print(json.dumps({'installed_files':len(records),'lookup_sha256':ref(REPO/'scripts/research_source_lookup.py',REPO).sha256,'inventory_sha256':ref(REPO/base/'inventory.json',REPO).sha256}))
