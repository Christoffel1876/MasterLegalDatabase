"""Execute frozen source-derived acceptance cases against an immutable draft copy."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

BASE = Path('/Users/mcoors/Documents/Project Geode')
REPO = BASE/'MasterLegalDatabase'
EXPECTATIONS = BASE/'handoffs/run-2026-09-12/el-paso-ehs-lookup-independent'
DRAFT = BASE/'handoffs/run-2026-09-12/el-paso-ehs-lookup-integration/proposed/research_source_lookup.py'
OUT = Path(__file__).resolve().parent
PYTHON = '/private/tmp/geode-status-venv/bin/python'
sys.path.insert(0,str(EXPECTATIONS))
from expectation_models import Expectations


class Event(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    id: str
    command: list[str]
    started_at: str
    finished_at: str
    exit_code: int
    stdout_file: str
    stdout_sha256: str
    stderr_file: str
    stderr_sha256: str
    errors: list[str]


class Receipt(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    recorded_at: str
    status: Literal['passed','issues']
    expected_cases_sha256: str
    draft_start_sha256: str
    draft_finish_sha256: str
    immutable_tested_copy_sha256: str
    draft_unchanged_during_run: bool
    source_cases: int
    compatibility_comparisons: int
    compatibility_errors: list[str]
    events: list[Event]
    limitations: list[str]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write(path: Path, data: bytes) -> None:
    if path.exists():raise ValueError('Refuse overwriting execution evidence')
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_suffix(path.suffix+'.tmp')
    with temporary.open('xb') as h:h.write(data)
    os.replace(temporary,path)


def run(identifier: str, script: Path, args: list[str]) -> tuple[Event,bytes]:
    command=[PYTHON,'-I','-B',str(script),'--root',str(REPO),*args]
    start=datetime.now(timezone.utc).isoformat()
    process=subprocess.run(command,cwd='/private/tmp',capture_output=True,timeout=90,
                           env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
    end=datetime.now(timezone.utc).isoformat()
    stdout=identifier+'.stdout';stderr=identifier+'.stderr'
    write(OUT/'outputs'/stdout,process.stdout);write(OUT/'outputs'/stderr,process.stderr)
    return Event(id=identifier,command=command,started_at=start,finished_at=end,
        exit_code=process.returncode,stdout_file='outputs/'+stdout,stdout_sha256=sha(process.stdout),
        stderr_file='outputs/'+stderr,stderr_sha256=sha(process.stderr),errors=[]),process.stdout


def main() -> None:
    raw=(EXPECTATIONS/'EXPECTATIONS.json').read_bytes()
    expected=Expectations.model_validate_json(raw)
    before=DRAFT.read_bytes();draft_copy=OUT/'tested-research-source-lookup.py'
    write(draft_copy,before)
    baseline=OUT/'prior-six-source-lookup.py'
    write(baseline,(EXPECTATIONS/'frozen-inputs/existing-six-source-interface.py').read_bytes())
    qa=json.loads((EXPECTATIONS/'frozen-inputs/SOURCE_QA.json').read_bytes())
    source_context={x['context_id']:x for x in qa['contexts']}
    source_bindings={x['identity']:x for x in qa['bindings']}
    events=[]
    for case in [c for c in expected.cases if c.id in {'EHS-02','EHS-03','EHS-04','EHS-07','EHS-08','EHS-09','EHS-10','EHS-25'}]:
        args=['--source-id',case.source_id,'--format','json','--mode',case.mode]
        args += ['--list-rows'] if case.list_rows else ['--query',case.query]
        event,output=run(case.id,draft_copy,args)
        if event.exit_code!=case.expected_exit:event.errors.append('Unexpected exit status')
        if case.expected_exit!=1:
            try:
                data=json.loads(output)
                status={'rows':'matched','context_only':'matched_context_only',
                        'no_match':'no_matching_row','refused':'refused_current_law'}[case.expected_kind]
                if data['status']!=status:event.errors.append('Status differs')
                if data['evidence_verified']!=case.expected_evidence_verified:event.errors.append('Evidence flag differs')
                rows=data['rows'];contexts={c['context_id']:c for c in data['context']}
                if [r['row_id'] for r in rows]!=[r.row_id for r in case.expected_rows]:event.errors.append('Selected row identity/order differs')
                for actual,row in zip(rows,case.expected_rows):
                    if {k:actual[k] for k in row.model_dump()}!=row.model_dump():event.errors.append('Source row/links changed: '+row.row_id)
                    for field,index in [('label_native',0),('fee_native',1)]:
                        span=source_bindings[row.row_id]['spans'][index]
                        if any(actual[field][key]!=value for key,value in span.items()):event.errors.append('Native bytes/offsets changed: '+row.row_id)
                    for forbidden in case.forbidden_context_links.get(row.row_id,[]):
                        if forbidden in actual['linked_context']:event.errors.append('Unsupported inferred context link: '+row.row_id)
                for required in case.required_context:
                    actual=contexts.get(required.context_id,{})
                    if any(actual.get(key)!=value for key,value in required.model_dump().items()):event.errors.append('Missing/changed complete clause: '+required.context_id)
                if case.query is not None and not set(case.directly_matched_context_ids)<=set(data['matched_context_ids']):event.errors.append('Missing directly matched context')
                if data['legal_currentness']!='not_verified' or data['answer_safe'] is not False:event.errors.append('Unsupported legal promotion')
                if data['adoption_date'] is not None or data['effective_date'] is not None:event.errors.append('Source date promoted')
                if data['translation_equivalence']!='not_reviewed':event.errors.append('Translation promotion')
                if case.expected_kind!='refused':
                    if set(contexts)!=set(source_context):event.errors.append('Complete 37-context scope differs')
                    source=data['source']
                    want={'source_id':expected.source_id,'authority_id':expected.authority_id,
                          'issuer':expected.issuer,'administering_agency':expected.administering_agency,
                          'acquisition_method':'received_review_package','original_http_acquired_at':None,
                          'original_http_independently_verified':False,
                          'printed_approval_claim':'October 25, 2023','printed_effective_claim':'January 1, 2024',
                          'intake_received_at':'2026-09-12T22:59:48.795762Z'}
                    for key,value in want.items():
                        if source[key]!=value:event.errors.append('Custody/date/authority differs: '+key)
                    if source['pdf']['sha256']!=expected.source_sha256:event.errors.append('Source digest differs')
                    if source['candidate']['sha256']!=qa['candidate']['sha256']:event.errors.append('Candidate digest differs')
                elif data.get('source') is not None or rows or contexts:event.errors.append('Refusal exposes evidence')
            except (ValueError,KeyError,TypeError) as error:event.errors.append(type(error).__name__+': '+str(error))
        elif output.strip():event.errors.append('Unsupported Spanish source exposed stdout')
        events.append(event);print(case.id,'PASS' if not event.errors else event.errors,flush=True)

    compat=[]
    source_ids=[]
    for number,source_id in enumerate(source_ids,1):
        for fmt in ['json','markdown']:
            args=['--source-id',source_id,'--list-rows','--format',fmt]
            old,old_raw=run(f'OLD-{number}-{fmt}',baseline,args)
            new,new_raw=run(f'NEW-{number}-{fmt}',draft_copy,args)
            events += [old,new]
            if old.exit_code!=0 or new.exit_code!=0 or old_raw!=new_raw:
                compat.append(source_id+' '+fmt+' output/exit differs')
            print('compat',source_id,fmt,'same' if old_raw==new_raw else 'DIFF',flush=True)
    final=DRAFT.read_bytes()
    receipt=Receipt(recorded_at=datetime.now(timezone.utc).isoformat(),
        status='issues' if compat or any(e.errors for e in events) else 'passed',
        expected_cases_sha256=sha(raw),draft_start_sha256=sha(before),draft_finish_sha256=sha(final),
        immutable_tested_copy_sha256=sha(draft_copy.read_bytes()),draft_unchanged_during_run=before==final,
        source_cases=8,compatibility_comparisons=0,compatibility_errors=compat,events=events,
        limitations=['Candidate-aware source-based acceptance; no new independent visual PDF review.',
                     'No public HTTP or production changes; all CLIs use the actual repository as read-only evidence.',
                     'No legal currentness/adoption/translation-equivalence conclusion.',
                     'Final draft hash must match the tested copy or changed code needs a targeted recheck.'])
    encoded=(receipt.model_dump_json(indent=2)+'\n').encode();Receipt.model_validate_json(encoded)
    write(OUT/'EXECUTION.json',encoded)
    write(OUT/'EXECUTION.schema.json',(json.dumps(Receipt.model_json_schema(),indent=2)+'\n').encode())
    print('receipt',sha(encoded),'status',receipt.status,'draft_unchanged',before==final)


if __name__=='__main__':main()
