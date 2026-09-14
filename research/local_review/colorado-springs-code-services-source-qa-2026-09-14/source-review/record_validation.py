"""Capture final focused checks and seal the compact portable review once."""
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, ConfigDict
from build_review import ROOT, asset
from review_models import Asset, Seal


class Run(BaseModel):
    """Actual local validation command and retained result."""
    model_config=ConfigDict(extra='forbid',strict=True)
    argv: list[str]
    started_at: str
    finished_at: str
    exit_code: int
    output: Asset


class Validation(BaseModel):
    """Bounded validation receipt, distinct from source/currentness claims."""
    model_config=ConfigDict(extra='forbid',strict=True)
    status: Literal['focused_checks_passed_before_seal']
    qa: Asset
    schema_asset: Asset
    tests: Run
    structural_verification: Run
    scope: str
    limitations: list[str]


def now() -> str:
    """Return actual UTC time."""
    return datetime.now(timezone.utc).isoformat()


def write(path: Path, raw: bytes) -> None:
    """Publish a new file without replacement."""
    assert not path.exists()
    temp=path.with_suffix(path.suffix+'.tmp')
    with temp.open('xb') as stream:stream.write(raw)
    temp.rename(path)


def run(argv: list[str], name: str) -> Run:
    """Execute one local check and retain its complete ordinary output."""
    start=now()
    result=subprocess.run(argv,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                          check=False)
    end=now()
    write(ROOT/name,result.stdout)
    return Run(argv=argv,started_at=start,finished_at=end,exit_code=result.returncode,
               output=asset(ROOT/name,ROOT))


def main() -> None:
    """Freeze final checks and closed inventory after passing results."""
    import sys
    write(ROOT/'VERIFICATION.schema.json',
          (json.dumps(Validation.model_json_schema(),indent=2)+'\n').encode())
    tests=run([sys.executable,'-B','-m','pytest','-p','no:cacheprovider',
               str(ROOT/'test_review.py'),'-q'],'tests-final.log')
    checked=run([sys.executable,'-B',str(ROOT/'verify_review.py'),'--unsealed'],
                'verify-before-seal.log')
    assert tests.exit_code==checked.exit_code==0
    record=Validation(status='focused_checks_passed_before_seal',
        qa=asset(ROOT/'SOURCE_QA.json',ROOT),schema_asset=asset(ROOT/'SOURCE_QA.schema.json',ROOT),
        tests=tests,structural_verification=checked,
        scope='7 source pages, 18343 unchanged native bytes, 197 fee associations, '
              '53 two-column rows, 15 contexts, 10 definitions, 14 pixel crops; 33 tests.',
        limitations=['No new HTTP, OCR or canonical writes. No maintained suite repeated.',
                     'Five SWIG warnings plus a shutdown warning; source currentness unverified.',
                     'A separate read-only closed-seal invocation is required after publication.'])
    write(ROOT/'VERIFICATION.json',(record.model_dump_json(indent=2)+'\n').encode())
    write(ROOT/'FINAL_MANIFEST.schema.json',
          (json.dumps(Seal.model_json_schema(),indent=2)+'\n').encode())
    seal=Seal(files=[asset(p,ROOT) for p in sorted(ROOT.rglob('*')) if p.is_file()])
    write(ROOT/'FINAL_MANIFEST.json',(seal.model_dump_json(indent=2)+'\n').encode())


if __name__=='__main__':
    main()
