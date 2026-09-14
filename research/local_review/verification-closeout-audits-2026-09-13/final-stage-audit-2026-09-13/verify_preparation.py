"""Verify this closed preparation. Optional live comparison is read-only and scoped."""
from __future__ import annotations
import argparse,hashlib,json,sys
from pathlib import Path,PurePosixPath
import jsonschema
from audit_staging import Audit
from finalize_audit import Manifest,Review
from smoke_check import RunReceipt,NATIVE
HERE=Path(__file__).resolve().parent

def digest(path:Path)->str:
    with path.open('rb') as handle:
        return hashlib.file_digest(handle,'sha256').hexdigest()
def ordinary(path:Path)->None:
    if not path.is_file() or any(p.is_symlink() for p in [path,*path.parents]):
        raise ValueError('Nonordinary file: '+str(path))
def relative(name:str)->Path:
    p=PurePosixPath(name)
    if p.is_absolute() or '..' in p.parts or str(p)!=name:
        raise ValueError('Unsafe manifest path')
    return Path(name)
def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository',type=Path)
    args=parser.parse_args()
    manifest=Manifest.model_validate_json((HERE/'FINAL_MANIFEST.json').read_bytes())
    expected={r.path for r in manifest.files}
    actual={str(p.relative_to(HERE)) for p in HERE.rglob('*') if p.is_file() and
            '__pycache__' not in p.parts and p.name not in
            {'FINAL_MANIFEST.json','FINAL_MANIFEST.schema.json'}}
    if len(expected)!=len(manifest.files) or expected!=actual:
        raise ValueError('Closed preparation file set differs')
    for r in manifest.files:
        p=HERE/relative(r.path);ordinary(p)
        if p.stat().st_size!=r.size_bytes or digest(p)!=r.sha256:
            raise ValueError('Preparation bytes differ: '+r.path)
    audit=Audit.model_validate_json((HERE/'STAGING_AUDIT.json').read_bytes())
    review=Review.model_validate_json((HERE/'REVIEW.json').read_bytes())
    for name in ['STAGING_AUDIT','REVIEW','SMOKE_PREPARATION','FINAL_MANIFEST']:
        jsonschema.validate(json.loads((HERE/(name+'.json')).read_bytes()),
                            json.loads((HERE/(name+'.schema.json')).read_bytes()))
    if json.loads((HERE/'RUN_RECEIPT.schema.json').read_bytes())!=RunReceipt.model_json_schema():
        raise ValueError('Run receipt schema differs from prepared harness')
    preparation=json.loads((HERE/'SMOKE_PREPARATION.json').read_bytes())
    if (preparation['prepared_harness_sha256']!=digest(HERE/'smoke_check.py') or
        preparation['previous_harness_sha256']!=digest(HERE/'previous-smoke_check.py') or
        preparation['native_sources']!=[list(x) for x in NATIVE] or
        preparation['expected_check_count']!=19 or len(NATIVE)!=9):
        raise ValueError('Smoke preparation binding differs')
    paths=[x.path for x in audit.candidates]
    if len(paths)!=len(set(paths)) or set(paths)&set(audit.excluded_user_paths):
        raise ValueError('Duplicate or excluded path selected')
    normal=[x.path for x in audit.candidates if x.tracked or not x.ignored_rule]
    force=[x.path for x in audit.candidates if not x.tracked and x.ignored_rule]
    for name,group in [('candidate-pathspecs',normal),('force-add-ignored-pathspecs',force)]:
        if ((HERE/(name+'.nul')).read_bytes()!=('\0'.join(group)+'\0').encode() or
            (HERE/(name+'.txt')).read_text()!='\n'.join(group)+'\n'):
            raise ValueError('Pathspec differs from typed selection')
    if review.candidates!=len(paths) or review.force_add_pathspecs!=len(force):
        raise ValueError('Summary counts differ')
    changes=[]
    if args.repository:
        root=args.repository.absolute()
        for r in audit.candidates:
            p=root/relative(r.path)
            try:
                ordinary(p)
                if p.stat().st_size!=r.size_bytes or digest(p)!=r.sha256:
                    changes.append(r.path)
            except (OSError,ValueError):changes.append(r.path)
    print(json.dumps({'status':'PASS' if not changes else 'LIVE_SELECTION_CHANGED',
          'payloads_verified':len(expected),'candidate_files':len(paths),
          'force_add_paths':len(force),'prepared_native_sources':len(NATIVE),
          'archive_executions':0,'public_requests':0,'canonical_mutations':0,
          'live_changed_paths':changes,
          'limit':'A historical preliminary selection; new final package paths are not discovered.'},indent=2))
    return 1 if changes else 0
if __name__=='__main__':raise SystemExit(main())
