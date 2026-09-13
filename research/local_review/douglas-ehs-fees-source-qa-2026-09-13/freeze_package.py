"""Freeze additive package files while preserving any preceding inventory exactly."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,os,sys
BASE=Path(__file__).absolute().parent
sys.dont_write_bytecode=True
sys.path.insert(0,str(BASE))
from independent_models import Asset,Manifest


def main()->None:
    """Write one typed closed inventory; source/QA/pass1 originals are never modified."""
    path=BASE/'FINAL_MANIFEST.json'
    if path.exists():
        raw=path.read_bytes();old=BASE/'independent/snapshots'/hashlib.sha256(raw).hexdigest()/'prior-manifest.json'
        old.parent.mkdir(parents=True,exist_ok=True)
        if old.exists():assert old.read_bytes()==raw
        else:old.write_bytes(raw)
    files=[]
    for p in BASE.rglob('*'):
        if p.is_symlink():raise ValueError('Symlink package member')
        if p.is_dir():continue
        if not p.is_file():raise ValueError('Nonordinary package member')
        if p==path:continue
        raw=p.read_bytes();files.append(Asset(path=p.relative_to(BASE).as_posix(),
            sha256=hashlib.sha256(raw).hexdigest(),size_bytes=len(raw)))
    result=Manifest(schema_version=1,frozen_at=datetime.now(timezone.utc),
                    files=sorted(files,key=lambda item:item.path),self_excluded='FINAL_MANIFEST.json',
                    status='source_qa_portable_pending_intake',legal_currentness='not_verified')
    temp=path.with_suffix('.tmp');temp.write_text(result.model_dump_json(indent=2)+'\n');os.replace(temp,path)


if __name__=='__main__':main()
