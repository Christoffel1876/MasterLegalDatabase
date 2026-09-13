"""Install only a separately reviewed, pinned six-file inventory proposal."""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from pydantic import BaseModel,ConfigDict
from jsonschema import Draft202012Validator

RUN=Path(__file__).resolve().parent
ROOT=RUN.parents[1]/'MasterLegalDatabase'
PREP=RUN/'extended-run/final-three-review-inventory'
OUT=ROOT/'research/local_review/final-three-review-inventory-install-2026-09-13'
PACKAGE=Path('research/local_review/manual-source-review-inventory-2026-09-11')

class Asset(BaseModel):
    """Exact ordinary-file identity."""
    model_config=ConfigDict(extra='forbid',strict=True)
    path:str
    sha256:str
    size_bytes:int

class Receipt(BaseModel):
    """Measured installation, without modification of canonical custody or source QA."""
    model_config=ConfigDict(extra='forbid',strict=True)
    status:Literal['installed_verified_inventory']
    installed_at:datetime
    proposal_manifest_sha256:str
    independent_review_manifest_sha256:str
    installed:list[Asset]
    preserved_preimages:list[Asset]
    unchanged_guards:dict[str,str]
    sources:Literal[64]
    mapped:Literal[27]
    unmapped:Literal[37]
    old_authorities_preserved:Literal[63]
    old_reviews_preserved:Literal[24]
    legal_currentness:Literal['not_verified']
    answer_safe:Literal[False]
    next_check:Literal['full_installed_suite_required']

def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()

def asset(root:Path,p:Path)->Asset:
    assert p.is_file() and not any(x.is_symlink() for x in [p,*p.parents])
    return Asset(path=p.relative_to(root).as_posix(),sha256=sha(p),size_bytes=p.stat().st_size)

def main()->None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--proposal-manifest',required=True)
    parser.add_argument('--independent-folder',type=Path,required=True)
    parser.add_argument('--independent-manifest',required=True)
    args=parser.parse_args()
    assert not OUT.exists()
    assert sha(PREP/'FINAL_MANIFEST.json')==args.proposal_manifest
    im=args.independent_folder/'FINAL_MANIFEST.json'
    assert sha(im)==args.independent_manifest
    proposal=json.loads((PREP/'FINAL_MANIFEST.json').read_bytes())
    Draft202012Validator(json.loads((PREP/'FINAL_MANIFEST.schema.json').read_bytes())).validate(proposal)
    listed={r['path']:r for r in proposal['files']}
    assert {p.relative_to(PREP).as_posix() for p in PREP.rglob('*') if p.is_file()}==set(listed)|{'FINAL_MANIFEST.json'}
    for name,r in listed.items():assert asset(PREP,PREP/name).model_dump()==r
    for r in proposal['repository_inputs']:assert asset(ROOT,ROOT/r['path']).model_dump()==r
    names={'manual_review_inventory.py':Path('geode/pipeline/manual_review_inventory.py'),
           'test_manual_review_inventory.py':Path('tests/test_manual_review_inventory.py'),
           **{name:PACKAGE/name for name in ['join-plan.json','inventory.json','inventory.schema.json','README.md']}}
    for name,dest in names.items():assert (ROOT/dest).read_bytes()==(PREP/'preimages'/name).read_bytes()
    guard_names=['_RAW_ARCHIVE/manual_intake/manual_source_intake_manifest.jsonl',
        '_CONTROL_PLANE/MANUAL_SOURCE_INTAKE_LEDGER.jsonl','_CONTROL_PLANE/MANUAL_SOURCE_INTAKE_REPORT.json',
        '_CONTROL_PLANE/LOCAL_COVERAGE_LEDGER.json','scripts/research_source_lookup.py']
    guards={n:sha(ROOT/n) for n in guard_names}
    old=json.loads((ROOT/PACKAGE/'inventory.json').read_bytes())
    new=json.loads((PREP/'proposed/inventory.json').read_bytes())
    old_plan=json.loads((ROOT/PACKAGE/'join-plan.json').read_bytes())
    new_plan=json.loads((PREP/'proposed/join-plan.json').read_bytes())
    assert new_plan['authorities'][:63]==old_plan['authorities'] and new_plan['reviews'][:24]==old_plan['reviews']
    for a,b in zip(new['sources'][:63],old['sources'],strict=True):
        if a['record_id'] in ['larimer-equity-fee-memo-sd007-05','el-paso-boh-bylaws-sd011']:
            a={**a,'reviews':None,'review_status':'metadata_only_review_unknown'}
        assert a==b
    assert (len(new['sources']),new['rows_with_review'],new['rows_without_review'])==(64,27,37)
    assert all(r['legal_currentness']=='not_verified' and r['answer_safe'] is False for r in new['sources'])
    shutil.copytree(PREP,OUT/'proposal')
    shutil.copytree(args.independent_folder,OUT/'independent-review')
    shutil.copy2(__file__,OUT/'install_final_inventory.py')
    snapshots=ROOT/PACKAGE/'_SNAPSHOTS/BEFORE_FINAL_THREE_2026-09-13'
    assert not snapshots.exists();shutil.copytree(PREP/'preimages',snapshots)
    sys.path.insert(0,str(ROOT))
    from geode.utils.file_io import atomic_write_text
    for name,dest in names.items():
        atomic_write_text(ROOT/dest,(PREP/'proposed'/name).read_text(),ROOT)
        assert (ROOT/dest).read_bytes()==(PREP/'proposed'/name).read_bytes()
    check=subprocess.run([sys.executable,'-B','-m','geode.pipeline.manual_review_inventory',
        '--root',str(ROOT),'--check'],cwd=ROOT,capture_output=True)
    (OUT/'installed-check.log').write_bytes(check.stdout+check.stderr)
    assert check.returncode==0,(check.stdout+check.stderr).decode()
    assert guards=={n:sha(ROOT/n) for n in guards}
    receipt=Receipt(status='installed_verified_inventory',installed_at=datetime.now(timezone.utc),
        proposal_manifest_sha256=args.proposal_manifest,independent_review_manifest_sha256=args.independent_manifest,
        installed=[asset(ROOT,ROOT/d) for d in names.values()],
        preserved_preimages=[asset(ROOT,snapshots/n) for n in names],unchanged_guards=guards,
        sources=64,mapped=27,unmapped=37,old_authorities_preserved=63,old_reviews_preserved=24,
        legal_currentness='not_verified',answer_safe=False,next_check='full_installed_suite_required')
    (OUT/'INSTALLATION.schema.json').write_text(json.dumps(Receipt.model_json_schema(),indent=2)+'\n')
    (OUT/'INSTALLATION.json').write_text(receipt.model_dump_json(indent=2)+'\n')
    (OUT/'README.md').write_text('# Three reviewed sources linked in the manual inventory\n\n'
        'One newly preserved Pueblo County source and three accepted source-fidelity reviews are now linked:64originals,27withreviews,37without. '
        'The original63authorityjoins and24reviewjoins remain exact. Only the two existing memo/bylaws rows gained review links. '
        'All legalcurrentness remains unverified. Proposal and independent reviews are preserved unchanged; INSTALLATION.json records the later actual install. '
        'The required final installed suite is recorded separately at docs/audits/FOUR_HOUR_RUN_2026-09-12/VERIFICATION_CATCHUP_INTEGRATION/.\n')
    print(receipt.model_dump_json(indent=2))

if __name__=='__main__':main()
