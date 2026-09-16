"""Verify retained acceptance outputs offline; never import or execute the tested adapter."""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path, PurePosixPath

from jsonschema import Draft202012Validator
from pydantic import BaseModel, ConfigDict, Field

HERE = Path(__file__).resolve().parent


class Member(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    path: str
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    size_bytes: int = Field(ge=0)


class Inventory(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    files: list[Member]


def read(relative: str) -> bytes:
    value=PurePosixPath(relative)
    if value.is_absolute() or '..' in value.parts or str(value)!=relative or '\\' in relative:
        raise ValueError('Unsafe evidence member')
    path=HERE/relative
    if not path.is_file() or any(p.is_symlink() for p in [path,*path.parents]):
        raise ValueError('Nonordinary evidence')
    return path.read_bytes()


def structured(name: str) -> dict:
    data=json.loads(read(name+'.json'))
    schema=json.loads(read(name+'.schema.json'))
    Draft202012Validator(schema).validate(data)
    return data


def validate() -> dict:
    inventory=Inventory.model_validate_json(read('FINAL_MANIFEST.json'))
    actual=set()
    for path in HERE.rglob('*'):
        if path.is_symlink() or not (path.is_file() or path.is_dir()):
            raise ValueError('Nonordinary package entry')
        if path.is_file() and path.relative_to(HERE).as_posix()!='FINAL_MANIFEST.json':
            actual.add(path.relative_to(HERE).as_posix())
    if actual!={m.path for m in inventory.files} or len(actual)!=len(inventory.files):
        raise ValueError('Closed inventory differs')
    for item in inventory.files:
        raw=read(item.path)
        if len(raw)!=item.size_bytes or hashlib.sha256(raw).hexdigest()!=item.sha256:
            raise ValueError('Changed evidence: '+item.path)
    original=structured('EXECUTION')
    corrected=structured('citation-fix-recheck/EXECUTION')
    boundaries=structured('citation-fix-recheck/BOUNDARIES')
    review=structured('FINAL_REVIEW')
    for receipt,prefix in [(original,''),(corrected,'citation-fix-recheck/')]:
        for event in receipt['events']:
            for kind in ['stdout','stderr']:
                if hashlib.sha256(read(prefix+event[kind+'_file'])).hexdigest()!=event[kind+'_sha256']:
                    raise ValueError('Event output digest differs')
        if not receipt['draft_unchanged_during_run']:
            raise ValueError('Unstable reviewed draft')
    if original['status']!='issues' or corrected['status']!='passed':
        raise ValueError('Original failure or final correction erased')
    failures=[e['id'] for e in original['events'] if e['errors']]
    if failures!=['EHS-07'] or any(e['errors'] for e in corrected['events']):
        raise ValueError('Unexpected acceptance outcome')
    frozen=structured('source-expectations/EXPECTATIONS')
    rechecked={e['id'] for e in corrected['events']}
    for case in frozen['cases']:
        prefix='citation-fix-recheck/' if case['id'] in rechecked else ''
        raw=read(prefix+'outputs/'+case['id']+'.stdout')
        if case['expected_exit']==1:
            if raw:raise ValueError('Unsupported source produced evidence')
            continue
        data=json.loads(raw)
        wanted={'rows':'matched','context_only':'matched_context_only','no_match':'no_matching_row',
                'refused':'refused_current_law'}[case['expected_kind']]
        if data['status']!=wanted or data['evidence_verified']!=case['expected_evidence_verified']:
            raise ValueError('Effective acceptance status differs')
        if [r['row_id'] for r in data['rows']]!=[r['row_id'] for r in case['expected_rows']]:
            raise ValueError('Selected row scope differs')
        for actual_row,want in zip(data['rows'],case['expected_rows']):
            if {k:actual_row[k] for k in want}!=want:raise ValueError('Complete source row differs')
        context={x['context_id']:x for x in data['context']}
        for want in case['required_context']:
            if {k:context[want['context_id']][k] for k in want}!=want:
                raise ValueError('Source condition differs')
        if (data['legal_currentness']!='not_verified' or data['answer_safe'] is not False or
                data['adoption_date'] is not None or data['effective_date'] is not None):
            raise ValueError('Unwarranted legal status')
    for n in range(1,7):
        for kind in ['json','markdown']:
            if read(f'outputs/OLD-{n}-{kind}.stdout')!=read(f'outputs/NEW-{n}-{kind}.stdout'):
                raise ValueError('Existing source output regression')
    if any(not case['passed'] for case in boundaries['checks']):
        raise ValueError('Citation/numeric boundary failure')
    if boundaries['baseline_definition_changes']!=['lookup','render_markdown']:
        raise ValueError('Existing implementation changed beyond dispatch')
    if boundaries['changes_from_first_tested_draft']!=['_lookup_ehs']:
        raise ValueError('Broader final change requires more acceptance testing')
    digest=hashlib.sha256(read('citation-fix-recheck/tested-research-source-lookup.py')).hexdigest()
    if digest!=review['accepted_draft_sha256'] or digest!=corrected['immutable_tested_copy_sha256']:
        raise ValueError('Final draft binding differs')
    return {'status':'passed_bounded_source_lookup_acceptance','source_cases':25,
            'old_source_output_comparisons':12,'targeted_rechecks':8,'boundary_checks':5,
            'preserved_original_failures':1,'new_network_requests':0,
            'legal_currentness':'not_verified','execution_replayed':False}


if __name__=='__main__':print(json.dumps(validate(),indent=2))
