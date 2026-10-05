"""Record final bounded checks, validate receipts and seal a new review once."""
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

from review_models import Manifest, Revision, RunReceipt, Validation

ROOT=Path(__file__).resolve().parent


def now() -> str:
    """Return the actual UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


def asset(path: Path) -> dict:
    """Bind one exact local payload."""
    raw=path.read_bytes()
    return {'path':path.relative_to(ROOT).as_posix(),
            'sha256':sha256(raw).hexdigest(),'size_bytes':len(raw)}


def save(name: str, model: type, data: dict) -> None:
    """Export schema and validate before atomic final writes."""
    schema=ROOT/(name+'.schema.json')
    schema.write_text(json.dumps(model.model_json_schema(),indent=2)+'\n')
    result=model.model_validate_json(json.dumps(data))
    temp=ROOT/(name+'.json.tmp');temp.write_text(result.model_dump_json(indent=2)+'\n')
    os.replace(temp,ROOT/(name+'.json'))


def main() -> None:
    """Run only finite local checks, then freeze every existing payload."""
    if (ROOT/'FINAL_MANIFEST.json').exists():
        raise ValueError('Already frozen')
    revisions=[asset(p) for folder in ('revision-preimages','revision-preimages-2','revision-preimages-3')
               for p in sorted((ROOT/folder).iterdir()) if p.is_file()]
    save('REVISION',Revision,{'recorded_at':now(),
        'status':'draft_annotation_corrections_before_freeze','preimages':revisions,
        'changes':[
            'Atlas flagged the initial regular page-one title incorrectly marked bold. Plato directly reopened page one and changed title markup to regular; source headers are bold blue and section headings bold.',
            'Plato corrected his own additive finding from 30-day notice periods to the actual submission/comment periods. Raw source/transcript wording had been exact.',
            'Atlas flagged terminal periods in printed labels 2.2.2., 2.2.3., 2.2.4. Their logical IDs remain unpunctuated; the labels now retain the periods and verifier enforces complete first-token equality. 2.2.1 remains without a terminal period.',
            'At Atlas request the schema restricts the sole DateStatement literal and role to the exact source effective-date assertion; schema-only inventory validation cannot reclassify it as adoption.',
            'The normalized transcript gained descriptive YAML frontmatter; no source words changed. Prior drafts and the initial corrected verifier syntax attempt are preserved separately.'
        ],'source_and_candidate_unchanged':True,'independent_model_family_review':False})
    runs=[]
    commands=[('tests',[sys.executable,'-B','-m','pytest','-q','-p','no:cacheprovider',str(ROOT/'test_review.py')]),
              ('verify-rerender',[sys.executable,'-B',str(ROOT/'verify_review.py'),'--unsealed','--rerender'])]
    env=dict(os.environ);env['PYTHONDONTWRITEBYTECODE']='1'
    for name,argv in commands:
        started=now()
        result=subprocess.run(argv,capture_output=True,timeout=180,check=False,env=env)
        finished=now()
        stdout=ROOT/(name+'.stdout.log');stderr=ROOT/(name+'.stderr.log')
        stdout.write_bytes(result.stdout);stderr.write_bytes(result.stderr)
        runs.append({'argv':argv,'started_at':started,'finished_at':finished,
                     'exit_code':result.returncode,'stdout':asset(stdout),'stderr':asset(stderr)})
        if result.returncode:
            sys.stdout.write(result.stdout.decode(errors='replace'))
            sys.stderr.write(result.stderr.decode(errors='replace'))
            raise ValueError('Final check failed: '+name)
    save('RUNS',RunReceipt,{'recorded_at':now(),'python_version':platform.python_version(),
        'network_requests':0,'runs':runs,'prior_checks':[
            'Initial unsealed native/crop verification plus seven-page rerender passed after one corrected syntax error, preserved in attempts/.',
            'Initial 13-case in-memory integrity suite passed. Final recorded run below includes a fourteenth printed-label punctuation case after Atlas feedback.'
        ]})
    save('VALIDATION',Validation,{'recorded_at':now(),'status':'passed','pages':7,
        'native_bytes':16366,'candidate_bytes':16520,'passages':119,'native_lines':302,
        'crop_count':7,'tests_run':14,'checks':[
            'All copied packet inputs match the independently pinned original packet manifest.',
            '119 checked records cover every native line/byte, exact printed label, parent and candidate span.',
            'Seven native extractions, seven full Poppler rerenders and seven exact pixel crops reproduce.',
            'Five page-crossing links and visual footer/body ordering reproduce.',
            'Printed effective-date role, received-package acquisition limits and selected intake bindings validate.',
            'Fourteen meaningful positive/negative integrity cases passed; exact actual commands/times/exits/logs in RUNS.json.'
        ],'limitations':[
            'Mechanical verification validates bindings and declared structure; direct image review is a same-Codex-family reviewer attestation.',
            'No currentness, operative effect, complete original HTTP custody, source referral or independent-family review is certified.'
        ]})
    (ROOT/'FINAL_MANIFEST.schema.json').write_text(json.dumps(Manifest.model_json_schema(),indent=2)+'\n')
    files=[asset(p) for p in sorted(ROOT.rglob('*')) if p.is_file()]
    m=Manifest.model_validate_json(json.dumps({'schema_version':1,
        'status':'frozen_source_fidelity_review_not_current_law','created_at':now(),'files':files}))
    temporary=ROOT/'FINAL_MANIFEST.json.tmp';temporary.write_text(m.model_dump_json(indent=2)+'\n')
    os.replace(temporary,ROOT/'FINAL_MANIFEST.json')
    sys.stdout.write(json.dumps({'files':len(files),'manifest':asset(ROOT/'FINAL_MANIFEST.json')},indent=2)+'\n')


if __name__=='__main__':
    main()
