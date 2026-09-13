"""Select exact reviewed run outputs only after the final installed regression succeeds."""
from pathlib import Path
from datetime import datetime,timezone
from hashlib import sha256
from typing import Literal
import json,re,shutil,subprocess
from pydantic import BaseModel,ConfigDict,Field
BASE=Path('/Users/mcoors/Documents/Project Geode')
REPO=BASE/'MasterLegalDatabase'
RUN=BASE/'handoffs/run-2026-09-12'
PREFIX='docs/audits/FOUR_HOUR_RUN_2026-09-12'
OUT=REPO/PREFIX/'FINAL_RUN_CHECKPOINT'
class Asset(BaseModel):
 model_config=ConfigDict(extra='forbid',strict=True)
 path:str
 sha256:str=Field(pattern=r'^[0-9a-f]{64}$')
 size_bytes:int=Field(ge=0)
class Preparation(BaseModel):
 model_config=ConfigDict(extra='forbid',strict=True)
 checked_at:str
 status:Literal['tested_local_checkpoint_prepared_shutdown_pending']
 authorized_start_utc:str
 authorized_end_utc:str
 parent_commit:str
 starting_commit:str
 full_suite_result:str
 changed_module_coverage:dict[str,float]
 files:list[Asset]
 conclusions:list[str]
 public_push:Literal[False]=False
 legal_currentness:Literal['not_verified']='not_verified'
def ref(p):
 assert p.is_file() and not p.is_symlink()
 raw=p.read_bytes()
 return Asset(path=p.relative_to(REPO).as_posix(),sha256=sha256(raw).hexdigest(),size_bytes=len(raw))
def main():
 log=RUN/'final-ehs-full-suite/pytest.log'
 matches=re.findall(r'(2600 passed, 49 warnings in [0-9.]+s)',log.read_text())
 assert len(matches)==1,'Wait for exact complete final2600-test success'
 assert not subprocess.check_output(['git','diff','--cached','--name-only'],cwd=REPO).strip(),'Preexisting index changes must be reviewed separately'
 OUT.mkdir()
 shutil.copyfile(log,OUT/'pytest.log')
 shutil.copyfile('/private/tmp/geode-final-ehs-full-coverage.json',OUT/'full-coverage.json')
 shutil.copyfile(__file__,OUT/'prepare_checkpoint.py')
 for p in [Path('/private/tmp/install_el_paso_ehs.py'),Path('/private/tmp/geode_final_ehs_cli.py'),Path('/private/tmp/preserve_watch_closure.py'),Path('/private/tmp/preserve_geode_closing_packets.py'),Path('/private/tmp/preserve_maintained_watch.py')]:
  shutil.copyfile(p,OUT/p.name)
 allowed_audits=['COLORADO_SPRINGS_INTAKE','COLORADO_SPRINGS_LOOKUP','DOUGLAS_CASTLE_ROCK_DISCOVERY','DOUGLAS_EHS_SOURCE_QA','EL_PASO_EHS_SOURCE_QA','EL_PASO_EHS_LOOKUP','GREELEY_FRESH_CUSTODY','MANUAL_SOURCE_WATCH','PUEBLO_DISCOVERY','PUEBLO_SOURCE_QA','CLOSEOUT_DOC_REVIEW','FINAL_RUN_CHECKPOINT']
 packages=['colorado-springs-intake-2026-09-12','douglas-castle-rock-discovery-2026-09-12','douglas-ehs-fees-source-qa-2026-09-13','el-paso-ehs-fees-source-qa-2026-09-13','greeley-fresh-custody-2026-09-12','manual-source-review-inventory-2026-09-11','manual-source-watch-live-2026-09-13','manual-source-watch-prototype-2026-09-13','manual-watch-next-selection-2026-09-13','pueblo-fee-discovery-2026-09-13','pueblo-planning-fees-source-qa-2026-09-13']
 files=['README.md','_CONTROL_PLANE/MANUAL_SOURCE_INTAKE_LEDGER.jsonl','_CONTROL_PLANE/MANUAL_SOURCE_INTAKE_REPORT.json','_RAW_ARCHIVE/manual_intake/manual_source_intake_manifest.jsonl','docs/GEODE_REVIEWER_SOP.md','docs/RESEARCH_SOURCE_LOOKUP.md','docs/MANUAL_SOURCE_WATCH.md','docs/PDF_SOURCE_REVIEW.md','docs/FOUR_HOUR_RUN_2026-09-12.md','geode/pipeline/manual_review_inventory.py','geode/pipeline/manual_source_watch.py','geode/pipeline/manual_watch_http.py','scripts/research_source_lookup.py','tests/test_manual_review_inventory.py','tests/test_el_paso_ehs_native_lookup.py','tests/test_colorado_springs_native_lookup.py','tests/test_manual_source_watch.py','tests/test_manual_watch_http.py','tests/test_manual_watch_http_deadlines.py','tests/fixtures/research_source_lookup_before_springs.json','config/manual_source_watch.json','config/manual_source_watch.schema.json']
 selected={REPO/f for f in files}
 folders=[REPO/PREFIX/a for a in allowed_audits]
 folders +=[REPO/'research/local_review'/p for p in packages]
 folders +=[REPO/'tests/fixtures/el_paso_ehs_native_lookup']
 folders +=[REPO/'_SNAPSHOTS/colorado-springs-sd014-20260912T235616492216Z']
 folders += sorted((REPO/'_SNAPSHOTS').glob('snapshot_2026-09-13T*'))
 for folder in folders:
  assert folder.is_dir() and not folder.is_symlink()
  for p in folder.rglob('*'):
   assert not p.is_symlink() and '__pycache__' not in p.parts and '.DS_Store' not in p.parts
   if p.is_file():selected.add(p)
 with (REPO/'_RAW_ARCHIVE/manual_intake/manual_source_intake_manifest.jsonl').open() as h:
  for line in h:
   row=json.loads(line)
   if row['record_id'] in ['colorado-springs-code-services-fees-2015-atlas-directed','colorado-springs-construction-fees-atlas-directed']:
    p=REPO/row['archive_path'];assert ref(p).sha256==row['sha256'];selected.add(p)
 assert all(p.is_file() and not p.is_symlink() for p in selected)
 assert not any(p.name in ['models 2.py','PROJECT_STATUS_2026-09-09.md'] for p in selected)
 coverage=json.loads((OUT/'full-coverage.json').read_bytes())
 modules=['geode/pipeline/manual_source_watch.py','geode/pipeline/manual_watch_http.py','geode/pipeline/manual_review_inventory.py','scripts/research_source_lookup.py']
 cov={m:coverage['files'][m]['summary']['percent_covered'] for m in modules}
 assert all(v>=90 for v in cov.values()),cov
 record=Preparation(checked_at=datetime.now(timezone.utc).isoformat(),status='tested_local_checkpoint_prepared_shutdown_pending',authorized_start_utc='2026-09-12T21:55:00Z',authorized_end_utc='2026-09-13T01:55:00Z',parent_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO).decode().strip(),starting_commit=subprocess.check_output(['git','rev-parse','0a3ba27a'],cwd=REPO).decode().strip(),full_suite_result=matches[0],changed_module_coverage=cov,files=[ref(p) for p in sorted(selected)],conclusions=[
'Run baseline46manual originals19review joins; current61originals22review joins39unmapped. Fifteen new originals, explicit county/municipal ownership, no statewide completeness claim.',
'Final native source lookup has seven fixed sources, with source-specific complete notes and dates; scanned ElPaso104rows and CRS three-section tools remain separate.',
'Two actual finite Springs checks (prototype and maintained) each fetched the same two PDFs unchanged. No scheduled manual watch or automatic baseline promotion.',
'Greeley later exact-byte reacquisition preserved independently from original received-package custody. Douglas/CastleRock and Pueblo discovery/QA remain outside canonical intake.',
'Ebenezer018 and Sherlock012-A deliveries retained. Grokusage limit stopped external work around22:46UTC; no019/020delivery, no purchase/reset/restart.',
'Root read implemented changes, independently verified portable packages, installedCLIconditions and visual61source mapping. Local fullsuite and changed-modulecoverage passed.',
'No GitHub push, official contacts, forms, signups, purchases, security changes or unavailablealways-onMac deployment. Final shutdown and archive smoke check recorded separately after this preparation.',
'Original reports/failed tests/errata remain unchanged with additive superseding records. Existing two missingLFS errors and separate retrievalcatalog gap are not repaired here.',
'Exactselectedfiles exclude unrelated preexisting untrackedprojectstatus and models2.py; indexblobs mustmatch these bytes before localcommit.'
 ])
 for name,value in [('PREPARATION.schema.json',Preparation.model_json_schema()),('PREPARATION.json',record.model_dump())]:
  path=OUT/name;path.write_text(json.dumps(value,indent=2)+'\n');selected.add(path)
 paths=RUN/'final-checkpoint-pathspec.nul';assert not paths.exists()
 paths.write_bytes(b'\0'.join(p.relative_to(REPO).as_posix().encode() for p in sorted(selected))+b'\0')
 print(json.dumps({'selected_files':len(selected),'selected_bytes':sum(p.stat().st_size for p in selected),'preparation_sha256':ref(OUT/'PREPARATION.json').sha256,'coverage':cov,'pathspec':str(paths)},indent=2))
if __name__=='__main__':main()
