"""One-time final inventory generation, with exact prior inventory snapshots on revision."""
from datetime import datetime,timezone
from pathlib import Path
import hashlib,json,os,sys
BASE=Path(__file__).absolute().parent
sys.dont_write_bytecode=True
sys.path.insert(0,str(BASE))
from models import Manifest,Asset

def main()->None:
    """Write the typed closed inventory without modifying any original evidence."""
    path=BASE/'FINAL_MANIFEST.json'
    if path.exists():
        raw=path.read_bytes();old=BASE/'_SNAPSHOTS'/hashlib.sha256(raw).hexdigest()/'prior-manifest.json'
        old.parent.mkdir(parents=True,exist_ok=True)
        if old.exists():assert old.read_bytes()==raw
        else:old.write_bytes(raw)
    files=[]
    for source in sorted(BASE.rglob('*')):
        if source.is_symlink():raise ValueError('Symlink')
        if not source.is_file():continue
        if source==path:continue
        raw=source.read_bytes()
        files.append(Asset(path=source.relative_to(BASE).as_posix(),
            sha256=hashlib.sha256(raw).hexdigest(),size_bytes=len(raw)))
    manifest=Manifest(schema_version=1,status='public_custody_preserved_no_canonical_change',
        prepared_at=datetime.now(timezone.utc),files=files,self_excluded='FINAL_MANIFEST.json',
        legal_currentness='not_verified')
    temporary=path.with_suffix('.tmp');temporary.write_text(manifest.model_dump_json(indent=2)+'\n')
    os.replace(temporary,path)

if __name__=='__main__':main()
