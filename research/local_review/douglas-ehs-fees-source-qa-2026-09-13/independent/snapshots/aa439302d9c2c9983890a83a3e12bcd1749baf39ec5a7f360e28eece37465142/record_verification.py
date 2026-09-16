"""Capture focused tests and read-only replay; never modify source or earlier QA."""
from pathlib import Path
from datetime import datetime,timezone
from typing import Literal
import hashlib,json,os,subprocess,sys
from pydantic import BaseModel,ConfigDict
BASE=Path(__file__).absolute().parent
sys.dont_write_bytecode=True
sys.path.insert(0,str(BASE))
from independent_models import Asset,Verification


class RenderMethod(BaseModel):
    """Separate originally observed settings from later exact-byte reproduction."""
    model_config=ConfigDict(extra='forbid',strict=True)
    source:Asset
    output:Asset
    command_template:list[str]
    observed_version:Literal['pdftoppm version 26.05.0']
    originally_executed:Literal[True]
    original_invocation_timestamp:None
    physical_page:Literal[1]
    dpi:Literal[150]
    evidence_scope:str


def asset(name:str)->Asset:
    p=BASE/name;data=p.read_bytes()
    return Asset(path=name,sha256=hashlib.sha256(data).hexdigest(),size_bytes=len(data))


def new(name:str,data:bytes)->Asset:
    """Write new capture files exactly once."""
    p=BASE/name;p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as out:out.write(data)
    return asset(name)


def freeze()->None:
    """Rebuild the inventory, preserving its exact predecessor."""
    subprocess.run([sys.executable,'-I','-B',str(BASE/'freeze_package.py')],
                   capture_output=True,check=True,timeout=15)


def main()->None:
    """Record only this source's local tests and complete render replay."""
    started=datetime.now(timezone.utc)
    env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1',
         'COVERAGE_FILE':'/private/tmp/douglas-source-qa-recorded.coverage'}
    test=subprocess.run([sys.executable,'-B','-m','pytest',str(BASE/'test_package.py'),'-q',
        '-p','no:cacheprovider','--basetemp=/private/tmp/douglas-source-qa-recorded-tests',
        '--cov=validate_package','--cov-branch','--cov-report=term-missing',
        '--cov-report=json:/private/tmp/douglas-source-qa-recorded-coverage.json'],
        cwd='/private/tmp',env=env,capture_output=True,timeout=90)
    tests_stdout=new('independent/tests.stdout.txt',test.stdout)
    tests_stderr=new('independent/tests.stderr.txt',test.stderr)
    assert test.returncode==0 and b'30 passed' in test.stdout,test.stdout.decode()
    cov=Path('/private/tmp/douglas-source-qa-recorded-coverage.json').read_bytes()
    coverage=new('independent/coverage.json',cov)
    render=RenderMethod(source=asset('original.pdf'),output=asset('independent/poppler-page-0001.png'),
        command_template=['pdftoppm','-r','150','-f','1','-l','1','-singlefile','-png',
                          '<package>/original.pdf','<output-prefix>'],
        observed_version='pdftoppm version 26.05.0',originally_executed=True,
        original_invocation_timestamp=None,physical_page=1,dpi=150,
        evidence_scope='The command and version were observed in this task. No independent per-command start timestamp was retained; the later verifier repeats the exact output in temporary storage.')
    new('independent/RENDER_METHOD.json',(render.model_dump_json(indent=2)+'\n').encode())
    new('independent/RENDER_METHOD.schema.json',
        (json.dumps(RenderMethod.model_json_schema(),indent=2)+'\n').encode())
    freeze()
    validation=subprocess.run([sys.executable,'-I','-B',str(BASE/'validate_package.py'),'--rerender'],
        cwd='/private/tmp',env=env,capture_output=True,timeout=60)
    validation_stdout=new('independent/validation.stdout.txt',validation.stdout)
    validation_stderr=new('independent/validation.stderr.txt',validation.stderr)
    assert validation.returncode==0,validation.stderr.decode()
    outcome=json.loads(validation.stderr)
    assert outcome['poppler_replayed'] is True and outcome['crops_replayed']==5
    assert asset('SOURCE_QA.json').sha256=='69f962f1caa58f9fcf90970aed1a05d7ccdbba6bb39b69f78ff0f15012896df4'
    assert asset('PASS1_frozen.json').sha256=='e9db13cf88f77d2ad9bf2c4d0d3975eb162d58eff2afc8a0e85a4911eeb76a6f'
    assert asset('original.pdf').sha256=='35e90b9c3b73b414155ed965898c8c270757f1c367cbe50d7645956039dbb687'
    receipt=Verification(status='passed',started_at=started,completed_at=datetime.now(timezone.utc),
        test_count=30,tests_stdout=tests_stdout,tests_stderr=tests_stderr,
        validation_stdout=validation_stdout,validation_stderr=validation_stderr,
        source_qa_unchanged=True,frozen_pass1_unchanged=True,source_unchanged=True,
        branch_inclusive_coverage=json.loads(cov)['totals']['percent_covered'],coverage=coverage,
        native_replayed=True,original_full_png_replayed=True,five_crops_replayed=True,
        independent_poppler_replayed=True,limitations=[
            'Tests mutate only isolated fixture copies. No canonical or source writes occur.',
            'Thirty focused tests plus direct source review do not establish legal status or applicability.',
            'Rendering checks reproduce bytes under the installed tools; original creation times remain unclaimed.'])
    new('VERIFICATION.json',(receipt.model_dump_json(indent=2)+'\n').encode())
    new('VERIFICATION.schema.json',(json.dumps(Verification.model_json_schema(),indent=2)+'\n').encode())
    freeze()


if __name__=='__main__':main()
