"""Seal already validated proposed bytes and immutable repository input identities."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from prepare import HERE, ROOT, PACKAGE, PROPOSED, BASELINE, ACCEPTANCES, asset
from verify_preparation import Manifest, FileIdentity, verify
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal

class TestResult(BaseModel):
    """Exact focused-test outcome and proposed file bindings."""
    model_config = ConfigDict(extra="forbid", strict=True)
    status: Literal["prepared_not_installed"]
    focused_tests: Literal[92]
    coverage_percent: float = Field(ge=90, le=100)
    coverage_statements: int
    coverage_branches: int
    source_count: Literal[64]
    mapped: Literal[27]
    unmapped: Literal[37]
    historical_attempts: str
    proposed_files: list[FileIdentity]

def seal() -> None:
    """Write a strictly validated one-time manifest; never install proposed files."""
    if (HERE/'FINAL_MANIFEST.json').exists():
        raise ValueError('Already sealed')
    coverage=json.loads((HERE/'coverage.json').read_bytes())['totals']
    assert coverage['percent_covered']>=90
    assert '92 passed' in (HERE/'focused-tests.log').read_text()
    acceptance_paths=list(ACCEPTANCES)
    current_paths=[str(PACKAGE/n) for n in
        ['join-plan.json','inventory.json','inventory.schema.json','README.md']]
    current_paths+=['geode/pipeline/manual_review_inventory.py',
      'tests/test_manual_review_inventory.py',
      '_RAW_ARCHIVE/manual_intake/manual_source_intake_manifest.jsonl',
      '_CONTROL_PLANE/MANUAL_SOURCE_INTAKE_LEDGER.jsonl',
      '_CONTROL_PLANE/MANUAL_SOURCE_INTAKE_REPORT.json',
      '_CONTROL_PLANE/LOCAL_COVERAGE_LEDGER.json']
    # Canonical ledger/report names are observed from the completed receipt/preparation.
    for path in current_paths:
        if not (ROOT/path).is_file():
            raise ValueError('missing expected current input '+path)
    plans=json.loads((PROPOSED/'join-plan.json').read_bytes())
    evidence=[r[k]['path'] for r in plans['reviews'][-3:] for k in ['review','review_schema']]
    evidence.append(plans['authorities'][-1]['provenance']['artifact']['path'])
    evidence.append('research/local_review/pueblo-county-intake-2026-09-13/prepared-transaction/execution/RECEIPT.json')
    inputs=[asset(ROOT/p) for p in sorted(set(acceptance_paths+current_paths+evidence))]
    summary={
      'status':'prepared_not_installed','focused_tests':92,
      'coverage_percent':coverage['percent_covered'],
      'coverage_statements':coverage['num_statements'],
      'coverage_branches':coverage['num_branches'],
      'source_count':64,'mapped':27,'unmapped':37,
      'historical_attempts':'A temporary test collection import-order error and initial import-omitting coverage measurement are retained. Final Coverage.start precedes proposed module import; no source/model lines excluded.',
      'proposed_files':[asset(f,f.relative_to(HERE).as_posix()) for f in sorted(PROPOSED.iterdir())],
    }
    checked_result=TestResult.model_validate_json(json.dumps(summary))
    (HERE/'TEST_RESULT.json').write_text(checked_result.model_dump_json(indent=2)+'\n')
    (HERE/'TEST_RESULT.schema.json').write_text(json.dumps(TestResult.model_json_schema(),indent=2)+'\n')
    (HERE/'FINAL_MANIFEST.schema.json').write_text(json.dumps(Manifest.model_json_schema(),indent=2)+'\n')
    payloads=[asset(p,p.relative_to(HERE).as_posix()) for p in sorted(HERE.rglob('*'))
              if p.is_file() and p.name!='FINAL_MANIFEST.json']
    record=Manifest.model_validate_json(json.dumps(dict(
      schema_version='final-three-inventory-preparation-1',status='prepared_not_installed',
      created_at=datetime.now(timezone.utc).isoformat().replace('+00:00','Z'),
      files=payloads,repository_inputs=inputs,source_count=64,mapped_count=27,unmapped_count=37,
      changed_existing_review_ids=['larimer-equity-fee-memo-sd007-05','el-paso-boh-bylaws-sd011'],
      new_source_id='pueblo-county-planning-fees-sh-ext-002',
      original_metadata_unchanged_except_two_reviews=True,
      prior_authority_joins_unchanged=63,prior_review_joins_unchanged=24,
      legal_currentness='not_verified',answer_safe=False,
      limitations=['Prepared only; maintained files were not written.',
       'Read-only schema/hash joins do not independently repeat image QA or certify legal effect.',
       'Current raw/ledger pins reflect root completed County Pueblo intake; earlier custody remains received_review_package.',
       'Repository replay requires exact original path/evidence. Portable mode verifies closed preparation bytes only.',
       'No independent HTTP start/end time is promoted from supplied reservation/result claims.'])))
    (HERE/'FINAL_MANIFEST.json').write_text(record.model_dump_json(indent=2)+'\n')
    verify(repository=True)

if __name__=='__main__':
    seal()
