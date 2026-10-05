"""Meaningful in-memory refusal checks; original evidence stays unchanged."""
import copy
from datetime import datetime, timezone
import json
import sys
from typing import Literal

from pydantic import BaseModel, ConfigDict
from prepare import ROOT, asset
from role_models import Review
from verify import verify_content

class Case(BaseModel):
    """One actually attempted corruption and rejection."""
    model_config=ConfigDict(extra='forbid',strict=True)
    name: str
    rejected: Literal[True]
    error_type: str

class Checks(BaseModel):
    """Recorded actual bounded validation result, not a full software test suite."""
    model_config=ConfigDict(extra='forbid',strict=True)
    recorded_at: str
    review_sha256: str
    verifier_sha256: str
    baseline_passed: Literal[True]
    exact_rerender_28_pages_previously_passed: Literal[True]
    rerender_tool_exit_code: Literal[0]
    cases: list[Case]
    original_review_unchanged: Literal[True]

def main() -> None:
    """Probe source-identity, coverage, qualification and evidence-association gates."""
    if (ROOT/'CHECKS.json').exists():raise ValueError('Checks already recorded')
    before=(ROOT/'ROLE_DECISIONS.json').read_bytes(); original=json.loads(before)
    verify_content(ROOT)
    mutations=[
        ('currentness promotion',lambda d:d['documents'][0].update(legal_currentness='verified')),
        ('legal effect certification',lambda d:d['documents'][1].update(legal_effect_certified=True)),
        ('missing page',lambda d:d['documents'][2]['pages'].pop()),
        ('wrong issuer',lambda d:d['documents'][2].update(authority_id='CO-COUNTY-JEFFERSON')),
        ('collapsed date',lambda d:d['documents'][2]['dates'][0].update(literal='April 1st, 2026')),
        ('lost prior-permit qualifier',lambda d:d['documents'][2]['observations'][3].update(visual_text='This code shall become effective on July 1, 2026.')),
        ('wrong crop page',lambda d:d['documents'][2]['observations'][7].update(crop_ids=['P08-identifiers'])),
        ('wrong native offset',lambda d:d['documents'][2]['observations'][7]['native_anchor'].update(start=0)),
        ('bill promoted to adopted-claim role',lambda d:d['documents'][1].update(assessed_role='ordinance_form_code_with_printed_adoption_claim')),
        ('wrong original hash',lambda d:d['documents'][0]['source'].update(sha256='0'*64)),
        ('dropped ordinance effective claim',lambda d:d['documents'][2]['dates'].pop(1)),
    ]
    cases=[]
    for name,mutate in mutations:
        value=copy.deepcopy(original); mutate(value)
        try:
            review=Review.model_validate_json(json.dumps(value)); verify_content(ROOT,review)
        except (ValueError,AssertionError) as exc:
            cases.append(Case(name=name,rejected=True,error_type=type(exc).__name__))
        else: raise AssertionError('Corruption accepted: '+name)
    assert before==(ROOT/'ROLE_DECISIONS.json').read_bytes()
    checks=Checks(recorded_at=datetime.now(timezone.utc).isoformat(),
        review_sha256=asset(ROOT/'ROLE_DECISIONS.json').sha256,
        verifier_sha256=asset(ROOT/'verify.py').sha256,baseline_passed=True,
        exact_rerender_28_pages_previously_passed=True,rerender_tool_exit_code=0,
        cases=cases,original_review_unchanged=True)
    (ROOT/'CHECKS.schema.json').write_text(json.dumps(Checks.model_json_schema(),indent=2)+'\n')
    (ROOT/'CHECKS.json').write_text(checks.model_dump_json(indent=2)+'\n')
    sys.stdout.write(f'PASS: {len(cases)} corruptions rejected; baseline unchanged.\n')
if __name__=='__main__':main()
