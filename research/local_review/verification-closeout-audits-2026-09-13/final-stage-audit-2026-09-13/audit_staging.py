"""Read-only, preliminary selection audit. Writes only its own new receipt files."""
from __future__ import annotations
import hashlib, json, os, re, stat, subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
ROOT = Path('/Users/mcoors/Documents/Project Geode/MasterLegalDatabase')
OUT = Path(__file__).resolve().parent
EXCLUDED = {'docs/audits/PROJECT_STATUS_2026-09-09.md', 'geode/schemas/models 2.py'}
class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
class File(Strict):
    path: str
    sha256: str = Field(pattern='^[a-f0-9]{64}$')
    size_bytes: int = Field(ge=0)
    selection_reason: str
    tracked: bool
    ignored_rule: str | None
    lfs_filter: str | None
    changed_during_read: bool
class Match(Strict):
    path: str
    line: int
    kind: str
    classification: str
class Audit(Strict):
    status: Literal['PRELIMINARY_NOT_STAGED']
    started_at: str
    finished_at: str
    repository: str
    head: str
    status_capture_sha256: str
    source_counts: dict[str,int]
    excluded_user_paths: list[str]
    candidates: list[File]
    excluded_generated_paths: list[str]
    older_untracked_snapshots_not_selected: list[str]
    secret_scan: list[Match]
    blockers: list[str]
    scope: list[str]
def git(*args: str, data: bytes | None = None) -> bytes:
    return subprocess.run(['git',*args],cwd=ROOT,input=data,check=True,
                          stdout=subprocess.PIPE,stderr=subprocess.PIPE).stdout
def write(name: str, raw: bytes) -> None:
    p=OUT/name
    if p.exists(): raise ValueError('Output exists: '+name)
    t=p.with_name(p.name+'.tmp')
    with t.open('xb') as f: f.write(raw)
    os.replace(t,p)
def sha(p: Path) -> tuple[str,int,bool]:
    before=p.stat()
    with p.open('rb') as f: h=hashlib.file_digest(f,'sha256').hexdigest()
    after=p.stat()
    return h,after.st_size,(before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns)
def junk(p: Path) -> bool:
    return any(x in {'__pycache__','.pytest_cache','.mypy_cache','.ruff_cache'} for x in p.parts) or p.name in {'.DS_Store','.coverage'} or p.suffix in {'.pyc','.pyo'}
def main() -> None:
    started=datetime.now(timezone.utc).isoformat()
    status=(OUT/'git-status.initial.nul').read_bytes()
    entries=[(x[:2].decode(),x[3:].decode()) for x in status.split(b'\0') if x]
    tracked=set(git('ls-files','-z').decode().split('\0'))
    selected={p:'modified or untracked path in preliminary Git status' for s,p in entries
              if p not in EXCLUDED}
    roots=set()
    for s,p in entries:
        parts=Path(p).parts
        if p.startswith('research/local_review/'):
            roots.add(Path(*parts[:3]))
        elif p.startswith('docs/audits/FOUR_HOUR_RUN_2026-09-12/') and len(parts)>4:
            roots.add(Path(*parts[:4]))
    generated=[]
    for parent in sorted(roots):
        for p in (ROOT/parent).rglob('*'):
            if not p.is_file() and not p.is_symlink(): continue
            relative=str(p.relative_to(ROOT))
            if junk(p): generated.append(relative);continue
            if relative not in tracked:
                selected[relative]='complete new evidence-package payload (including ignored files)'
    rawpath='_RAW_ARCHIVE/manual_intake/manual_source_intake_manifest.jsonl'
    baseline={json.loads(l)['record_id'] for l in git('show','HEAD:'+rawpath).splitlines()}
    with (ROOT/rawpath).open() as f: rows=[json.loads(l) for l in f]
    for row in rows:
        if row['record_id'] not in baseline:
            selected[row['archive_path']]='new current raw-manifest original since HEAD'
    # Matching exact HEAD preimages helps recover the actual predecessor independent of filenames.
    changed_hashes={hashlib.sha256(git('show','HEAD:'+p)).hexdigest() for s,p in entries
                    if p in tracked and s.strip()=='M'}
    older=[]
    for p in (ROOT/'_SNAPSHOTS').rglob('*'):
        relative=str(p.relative_to(ROOT))
        if not p.is_file() or relative in tracked: continue
        h,_,_=sha(p)
        if '2026-09-13' in relative or '20260913' in relative or h in changed_hashes:
            selected[relative]='current-session snapshot or exact modified-file HEAD preimage'
        else: older.append(relative)
    paths=sorted(selected)
    ignored={}
    check=subprocess.run(['git','check-ignore','--no-index','-z','-v','--stdin'],cwd=ROOT,
                         input=('\0'.join(paths)+'\0').encode(),stdout=subprocess.PIPE)
    parts=check.stdout.decode().split('\0')
    for i in range(0,len(parts)-3,4):
        ignored[parts[i+3]]=':'.join(parts[i:i+3])
    attrs=git('check-attr','-z','--stdin','filter',data=('\0'.join(paths)+'\0').encode()).decode().split('\0')
    filters={attrs[i]:attrs[i+2] for i in range(0,len(attrs)-2,3)}
    files=[];matches=[];blockers=[]
    token=re.compile(rb'(?:gh[pousr]_[A-Za-z0-9]{25,}|github_pat_[A-Za-z0-9_]{25,}|sk-(?:proj-|ant-|xai-)?[A-Za-z0-9_-]{30,}|xai-[A-Za-z0-9_-]{30,}|AKIA[A-Z0-9]{16})')
    header=re.compile(rb'^\s*(?:[<>]\s*)?(set-cookie|cookie|authorization|proxy-authorization)\s*:\s*(.*)$',re.I)
    json_header=re.compile(rb'"(set-cookie|cookie|authorization|proxy-authorization)"\s*:\s*"([^"\r\n]+)"',re.I)
    for relative in paths:
        p=ROOT/relative
        if any(x.is_symlink() for x in [p,*p.parents]):
            blockers.append('Nonordinary symlink path: '+relative);continue
        if not p.is_file(): blockers.append('Missing or nonordinary: '+relative);continue
        h,size,changed=sha(p)
        files.append(File(path=relative,sha256=h,size_bytes=size,
            selection_reason=selected[relative],tracked=relative in tracked,
            ignored_rule=ignored.get(relative),lfs_filter=filters.get(relative),
            changed_during_read=changed))
        if changed: blockers.append('Changed during read: '+relative)
        if size>=100_000_000: blockers.append('At least100MB: '+relative)
        with p.open('rb') as f:
            first=f.read(512)
            if first.startswith((b'%PDF-',b'\x89PNG',b'\x1f\x8b',b'PK\x03\x04')) or b'\0' in first: continue
            f.seek(0)
            for number,line in enumerate(f,1):
                if token.search(line): matches.append(Match(path=relative,line=number,
                    kind='credential-shaped token',classification='requires manual review; no value retained'))
                candidates=[]
                if (m:=header.match(line)): candidates.append((m.group(1),m.group(2)))
                candidates.extend((m.group(1),m.group(2)) for m in json_header.finditer(line))
                for name,value in candidates:
                    if any(marker in value.lower() for marker in
                           [b'redacted',b'example',b'placeholder',b'forbidden',b'[omitted',b'<omitted']):
                        classification='explicit redaction/example marker'
                    else: classification='potential actual header value; requires manual review'
                    matches.append(Match(path=relative,line=number,kind=name.decode().lower(),
                                         classification=classification))
    inv=json.loads((ROOT/'research/local_review/manual-source-review-inventory-2026-09-11/inventory.json').read_bytes())
    with (ROOT/'_CONTROL_PLANE/MANUAL_SOURCE_INTAKE_LEDGER.jsonl').open() as f: ledger=sum(1 for _ in f)
    audit=Audit(status='PRELIMINARY_NOT_STAGED',started_at=started,
        finished_at=datetime.now(timezone.utc).isoformat(),repository=str(ROOT),
        head=git('rev-parse','HEAD').decode().strip(),status_capture_sha256=hashlib.sha256(status).hexdigest(),
        source_counts={'raw_manifest':len(rows),'ledger':ledger,'inventory_sources':len(inv['sources']),
                       'with_review':inv['rows_with_review'],'without_review':inv['rows_without_review']},
        excluded_user_paths=sorted(EXCLUDED),candidates=files,
        excluded_generated_paths=sorted(set(generated)),older_untracked_snapshots_not_selected=sorted(older),
        secret_scan=matches,blockers=blockers,scope=[
          'Read-only Git status, attribute, tracked-file and current file-byte inspection; no staging.',
          'Initial status capture precedes possible County intake and EB023/024 additions; recompute final scope.',
          'Candidate list is a review proposal, not authorization to publish every path.',
          'All ignored ordinary payloads beneath selected new evidence-package roots are included.',
          'Snapshots selected by current-session date names or exact modified-file HEAD digest; older snapshots listed separately.',
          'Text-like files scanned for actual header-line shapes and common token formats; no guarantee of all secret forms.',
          'Binary documents were hashed but not content-reviewed or text-extracted for secret scanning.',
          'No secret/header values are copied into this audit.'])
    raw=(audit.model_dump_json(indent=2)+'\n').encode();Audit.model_validate_json(raw)
    write('STAGING_AUDIT.json',raw)
    write('STAGING_AUDIT.schema.json',(json.dumps(Audit.model_json_schema(),indent=2)+'\n').encode())
    ordinary=[f.path for f in files if f.tracked or not f.ignored_rule]
    forced=[f.path for f in files if not f.tracked and f.ignored_rule]
    write('candidate-pathspecs.nul',('\0'.join(ordinary)+'\0').encode())
    write('force-add-ignored-pathspecs.nul',('\0'.join(forced)+'\0').encode())
    write('candidate-pathspecs.txt',('\n'.join(ordinary)+'\n').encode())
    write('force-add-ignored-pathspecs.txt',('\n'.join(forced)+'\n').encode())
    print(json.dumps({'files':len(files),'bytes':sum(f.size_bytes for f in files),
        'force_add':len(forced),'max_bytes':max(f.size_bytes for f in files),
        'counts':audit.source_counts,'header_matches':len(matches),'blockers':blockers},indent=2))
if __name__=='__main__':main()
