"""Prepare the final local checkpoint only after the final installed suite passed."""
from datetime import datetime,timezone
from pathlib import Path
from typing import Literal
import hashlib,json,re,shutil,subprocess
from pydantic import BaseModel,ConfigDict

RUN=Path(__file__).resolve().parent
ROOT=RUN.parents[1]/'MasterLegalDatabase'
OUT=ROOT/'docs/audits/FOUR_HOUR_RUN_2026-09-12/VERIFICATION_CATCHUP_CHECKPOINT'

class Asset(BaseModel):
    """Recorded input bytes of this checkpoint."""
    model_config=ConfigDict(extra='forbid',strict=True)
    path:str
    sha256:str
    size_bytes:int

class Checkpoint(BaseModel):
    """Measured results, source limitations and the exact tree awaiting local commit."""
    model_config=ConfigDict(extra='forbid',strict=True)
    prepared_at:datetime
    status:Literal['verified_ready_for_local_commit']
    parent_commit:str
    branch:str
    tests_passed:int
    warnings:int
    test_seconds:float
    changed_module_coverage:dict[str,float]
    manual_originals:Literal[64]
    manual_ledger_records:Literal[65]
    linked_reviews:Literal[27]
    unmapped_reviews:Literal[37]
    authorities:Literal[12]
    code_stable_during_suite:Literal[True]
    corpus_errors:list[str]
    evidence:list[Asset]
    conclusions:list[str]
    pending:list[str]
    public_push:Literal[False]
    legal_currentness:Literal['not_verified']

def asset(p:Path)->Asset:
    raw=p.read_bytes();return Asset(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(raw).hexdigest(),size_bytes=len(raw))

def main()->None:
    assert not OUT.exists()
    suite=ROOT/'docs/audits/FOUR_HOUR_RUN_2026-09-12/VERIFICATION_CATCHUP_INTEGRATION'
    result=json.loads((suite/'RESULT.json').read_bytes())
    assert result['status']=='passed' and result['exit_code']==0 and result['changed_during_run']==[]
    log=(suite/'pytest.log').read_text()
    assert asset(suite/'pytest.log').sha256==result['log_sha256']
    assert asset(suite/'coverage.json').sha256==result['coverage_sha256']
    match=re.search(r'(\d+) passed, (\d+) warnings in ([\d.]+)s',log)
    assert match,log[-1500:]
    coverage=json.loads((suite/'coverage.json').read_bytes())
    modules=['geode/constants.py','geode/pipeline/manual_review_inventory.py',
        'geode/pipeline/manual_source_watch_batches.py','geode/pipeline/manual_watch_http_v2.py',
        'scripts/research_source_lookup.py']
    measured={name:coverage['files'][name]['summary']['percent_covered'] for name in modules}
    assert all(value>=90 for value in measured.values()),measured
    inventory=ROOT/'research/local_review/manual-source-review-inventory-2026-09-11/inventory.json'
    data=json.loads(inventory.read_bytes());assert(len(data['sources']),data['rows_with_review'],data['rows_without_review'])==(64,27,37)
    subprocess.run(['/private/tmp/geode-status-venv/bin/python','-B','-m',
        'geode.pipeline.manual_review_inventory','--root',str(ROOT),'--check'],
        cwd=ROOT,check=True,capture_output=True)
    for relative,expected in {
        '_RAW_ARCHIVE/manual_intake/manual_source_intake_manifest.jsonl':'7b8f882ec45286f69713a023345d8c5ef7f5859ecdb5f8d4036c8d8900eb8570',
        '_CONTROL_PLANE/MANUAL_SOURCE_INTAKE_LEDGER.jsonl':'dc4dd0096e6eee5bed75b13b9f7990dc1735212b9835bbf645f390235be69f3c',
        '_CONTROL_PLANE/MANUAL_SOURCE_INTAKE_REPORT.json':'d59fe2a04ed9ad278d5d9a0313d3909a830dae1d43c0c46bfb5e68b96006d2c5',
    }.items(): assert asset(ROOT/relative).sha256==expected
    evidence=[asset(suite/'RESULT.json'),asset(suite/'pytest.log'),asset(suite/'coverage.json'),asset(inventory)]
    for name in ['pueblo-county-intake-2026-09-13','eb023-equity-memo-source-qa-2026-09-13','eb024-bylaws-source-qa-2026-09-13']:
        evidence.append(asset(ROOT/'research/local_review'/name/'ROOT_ACCEPTANCE.json'))
    evidence.extend([asset(ROOT/'research/local_review/final-three-review-inventory-install-2026-09-13/INSTALLATION.json'),
        asset(ROOT/'docs/audits/FOUR_HOUR_RUN_2026-09-12/PUEBLO_COUNTY_CORPUS_VALIDATION/RESULT.json'),
        asset(ROOT/'docs/audits/FOUR_HOUR_RUN_2026-09-12/FINAL_THREE_INVENTORY_VISUAL/INSTALLATION.json'),
        asset(ROOT/'research/local_review/inventory-wording-clarification-2026-09-13/INSTALLATION.json')])
    receipt=Checkpoint(prepared_at=datetime.now(timezone.utc),status='verified_ready_for_local_commit',
        parent_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip(),
        branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT).decode().strip(),
        tests_passed=int(match[1]),warnings=int(match[2]),test_seconds=float(match[3]),
        changed_module_coverage=measured,manual_originals=64,manual_ledger_records=65,linked_reviews=27,unmapped_reviews=37,
        authorities=len({r['authority_id'] for r in data['sources']}),code_stable_during_suite=True,
        corpus_errors=['_CONTROL_PLANE/LOCAL_REVIEW_QUEUE.jsonl: inherited missing Git LFS content',
            '08_County_Authorities/_index.jsonl: inherited missing Git LFS content'],evidence=evidence,
        conclusions=['Captured-buffer lookup repair prevents rereading unverified mutable artifacts across seven older adapters; nine native source families retained.',
            'Three newly preserved raw sources since parent commit: Douglas County EHS, City of Pueblo planning, Pueblo County planning. Exact old raw and ledger prefixes remain unchanged.',
            'County intake uses the separately reviewed fixed-source transaction; original race-prone proposal remains blocked historical evidence.',
            'Full four-page Larimer memo and five-page El Paso bylaws source-fidelity reviews accepted. Candidate/original/report bytes remain unchanged.',
            'Final inventory has 64 originals / 27 linked reviews / 37 unmapped, across 12 authorities. Prior 63 authority joins and 24 review joins remain exact.',
            'Six-source watch checks returned unchanged originals; no daily deployment or new-edition/currentness claim.',
            'All helpers and preview servers stopped; source discovery paused. Final clean-export receipt is produced after committing this exact tree.'],
        pending=['Review remaining 37 unmapped manual originals and retained source-discovery gaps in future bounded sessions.',
            'Recover two inherited missing Git LFS original contents if available.',
            'Keep source-text fidelity distinct from adoption, legal currency and complete local/statewide coverage.',
            'Deploy recurring checks only when the always-on Mac is available.'],public_push=False,legal_currentness='not_verified')
    OUT.mkdir()
    (OUT/'CHECKPOINT.schema.json').write_text(json.dumps(Checkpoint.model_json_schema(),indent=2)+'\n')
    (OUT/'CHECKPOINT.json').write_text(receipt.model_dump_json(indent=2)+'\n')
    shutil.copy2(__file__,OUT/Path(__file__).name)
    (OUT/'README.md').write_text('# Verification catch-up checkpoint\n\n'
        f'{receipt.tests_passed:,} tests passed ({receipt.warnings} warnings; {receipt.test_seconds:.2f} seconds). '
        'Code and test files stayed unchanged during the final suite. All five changed runtime modules exceed 90% combined statement/branch coverage.\n\n'
        'The manual PDF inventory now records 64 originals, 27 with linked source reviews and 37 awaiting review across 12 authorities. '
        'County and City of Pueblo remain separate. Source text reviews do not establish current legal effect or complete statewide coverage.\n\n'
        'The new County intake passed 44 targeted transaction checks and independent review; exact source bytes, previous JSONL prefixes, snapshots and repeated no-op execution were verified. '
        'The original rejected transaction and all original reports remain preserved. Complete Larimer memo and El Paso bylaws reviews are linked with their qualifications.\n\n'
        'The corpus validator still reports exactly two inherited unavailable Git LFS contents. Daily monitoring has not been deployed to the unavailable always-on Mac. '
        'All helpers are stopped. No public push was performed. This record precedes its local commit; the final handoff records the resulting commit and clean-export checks.\n')
    print(receipt.model_dump_json(indent=2,exclude={'evidence'}))

if __name__=='__main__':main()
