"""Replay exact citation and amount boundaries on the retained source without mutation."""
from __future__ import annotations

import ast
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, ConfigDict

import run_cases


class Check(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    query: str
    expected_status: str
    expected_rows: list[str]
    passed: bool
    event: run_cases.Event


class Checks(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    recorded_at: str
    tested_script_sha256: str
    baseline_definition_changes: list[str]
    changes_from_first_tested_draft: list[str]
    checks: list[Check]
    public_requests: int = 0


def definitions(path: Path) -> dict[str, str]:
    tree=ast.parse(path.read_bytes())
    return {n.name:ast.dump(n,include_attributes=False) for n in tree.body
            if isinstance(n,(ast.FunctionDef,ast.ClassDef))}


def main() -> None:
    root=Path(__file__).resolve().parent;script=root/'tested-research-source-lookup.py'
    results=[]
    cases=[('211','no_matching_row',[]),('211.5','no_matching_row',[]),
           ('Section 25-4','no_matching_row',[]),
           ('Section 25-4-1607','matched',['R056']),('Section 2.1','no_matching_row',[])]
    for number,(query,status,rows) in enumerate(cases,1):
        event,raw=run_cases.run(f'BOUNDARY-{number}',script,
            ['--source-id','el-paso-boh-ehs-fees-sd011','--query',query,'--format','json'])
        data=json.loads(raw)
        passed=(event.exit_code==0 and data['status']==status and
                [r['row_id'] for r in data['rows']]==rows)
        if not passed:event.errors.append('Source citation/amount boundary differs')
        results.append(Check(query=query,expected_status=status,expected_rows=rows,
                             passed=passed,event=event))
    actual=definitions(script)
    baseline=definitions(root/'prior-six-source-lookup.py')
    first=definitions(root.parent/'tested-research-source-lookup.py')
    result=Checks(recorded_at=datetime.now(timezone.utc).isoformat(),
        tested_script_sha256=hashlib.sha256(script.read_bytes()).hexdigest(),
        baseline_definition_changes=[name for name in baseline if baseline[name]!=actual.get(name)],
        changes_from_first_tested_draft=[name for name in first if first[name]!=actual.get(name)],
        checks=results)
    raw=(result.model_dump_json(indent=2)+'\n').encode();Checks.model_validate_json(raw)
    run_cases.write(root/'BOUNDARIES.json',raw)
    run_cases.write(root/'BOUNDARIES.schema.json',(json.dumps(Checks.model_json_schema(),indent=2)+'\n').encode())
    print(result.model_dump_json(indent=2))


if __name__=='__main__':main()
