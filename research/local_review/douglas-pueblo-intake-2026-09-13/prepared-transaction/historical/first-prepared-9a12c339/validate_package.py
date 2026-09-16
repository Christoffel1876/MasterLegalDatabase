"""Verify the closed prepared package offline; --live also performs a canonical dry-run."""
from pathlib import Path
import argparse,hashlib,json,sys
BASE=Path(__file__).resolve().parent
sys.dont_write_bytecode=True
sys.path.insert(0,str(BASE))
from package_models import Inventory,Validation

def verify(expected_manifest:str|None=None)->dict:
    manifest_path=BASE/'FINAL_MANIFEST.json'
    if any(p.is_symlink() for p in (BASE,*BASE.parents)):raise ValueError('Symlink package root')
    b=manifest_path.read_bytes()
    if expected_manifest and hashlib.sha256(b).hexdigest()!=expected_manifest:raise ValueError('External manifest pin differs')
    manifest=Inventory.model_validate_json(b)
    expected={x.path for x in manifest.files}|{'FINAL_MANIFEST.json','FINAL_MANIFEST.schema.json'}
    if len(expected)!=len(manifest.files)+2:raise ValueError('Duplicate manifest member')
    actual=set()
    for p in BASE.rglob('*'):
        relative=p.relative_to(BASE).as_posix()
        if any(x.is_symlink() for x in (p,*p.parents)):raise ValueError('Symlink package member')
        if not p.is_file() and not p.is_dir():raise ValueError('Nonordinary package member')
        if relative=='execution' or relative.startswith('execution/'):
            # Application state is a separately validated, explicitly excluded future output.
            continue
        if p.is_file():actual.add(relative)
    if actual!=expected:raise ValueError('Closed package membership differs')
    for item in manifest.files:
        path=Path(item.path)
        if path.is_absolute() or '..' in path.parts:raise ValueError('Manifest escape')
        body=(BASE/path).read_bytes()
        if len(body)!=item.size_bytes or hashlib.sha256(body).hexdigest()!=item.sha256:raise ValueError('Inventory mismatch: '+item.path)
    validation=Validation.model_validate_json((BASE/'VALIDATION.json').read_bytes())
    from validate_preparation import verify as verify_preparation
    result=verify_preparation()
    result.update(package_files=len(manifest.files)+2,manifest_sha256=hashlib.sha256(b).hexdigest(),tests_recorded=validation.tests_passed,execution_excluded='execution',portable_verification='custody_and_preparation_only; no claim of completed intake')
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--expected-manifest');p.add_argument('--live',action='store_true');p.add_argument('--root',type=Path);a=p.parse_args();result=verify(a.expected_manifest)
    if a.live:
        import transaction as tx
        root=a.root.absolute() if a.root else tx.DEFAULT_ROOT
        result['live_read_only']=tx.execute(tx.load_plan(root),root,BASE/'execution')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
