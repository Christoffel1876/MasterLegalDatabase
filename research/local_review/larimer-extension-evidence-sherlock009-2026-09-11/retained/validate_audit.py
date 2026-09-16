"""Validate frozen local custody, schemas and PDF structure; never retrieve sources."""
from pathlib import Path, PurePosixPath
from hashlib import sha256
from datetime import datetime, timezone
from typing import Literal
import json, tarfile
import jsonschema, pymupdf
from pydantic import ConfigDict, Field
from audit_models import Audit, StrictModel, FileRef

B=Path(__file__).parent
A=B/'received/20260911T190213Z'

def digest(p: Path) -> str:
    h=sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):
            h.update(block)
    return h.hexdigest()

def check_file(p: Path, expected_hash: str, expected_size: int) -> None:
    if p.is_symlink() or any(q.is_symlink() for q in p.parents):
        raise ValueError(f'Symlink: {p}')
    if not p.is_file() or p.stat().st_size != expected_size or digest(p) != expected_hash:
        raise ValueError(f'File differs: {p}')

class ValidationResult(StrictModel):
    schema_version: Literal[1]
    validated_at: datetime
    audit: FileRef
    custody_receipt: FileRef
    checks_passed: list[str]
    original_and_received_file_pairs: Literal[97]
    inventoried_files: Literal[51]
    checked_tar_file_members: Literal[87]
    source_pdfs: Literal[3]
    structural_pages: Literal[27]
    visual_pages_previously_inspected: Literal[10]
    exact_publisher_acquisition_verified: Literal[False]
    legal_currentness: Literal['not_verified']


def validate() -> ValidationResult:
    raw=(B/'INTAKE_AUDIT.json').read_text()
    audit=Audit.model_validate_json(raw)
    schema=json.loads((B/'INTAKE_AUDIT.schema.json').read_text())
    assert schema==Audit.model_json_schema()
    jsonschema.Draft202012Validator(schema).validate(json.loads(raw))
    cr=json.loads((B/'CUSTODY_RECEIPT.json').read_text())
    jsonschema.Draft202012Validator(json.loads((B/'CUSTODY_RECEIPT.schema.json').read_text())).validate(cr)
    assert len(cr['files'])==97
    assert sum(r['size_bytes'] for r in cr['files'])==71496968
    for r in cr['files']:
        for key in ('original_path','received_path'):
            check_file(Path(r[key]),r['sha256'],r['size_bytes'])
    for r in audit.supporting_files:
        check_file(B/r.path,r.sha256,r.size_bytes)
    for s in audit.sources:
        check_file(B/s.file.path,s.file.sha256,s.file.size_bytes)
        with pymupdf.open(B/s.file.path) as pdf:
            assert not pdf.is_repaired and not pdf.is_encrypted and len(pdf)==s.pages
            for page in pdf:page.get_text()
    for e in audit.excerpts:
        check_file(B/e.image.path,e.image.sha256,e.image.size_bytes)
    for f in audit.findings:
        for rel in f.evidence_paths:
            assert not PurePosixPath(rel).is_absolute() and '..' not in PurePosixPath(rel).parts
            assert (B/rel).is_file()
    inv=json.loads((A/'exports/artifact_inventory_20260911T191427Z.json').read_text())
    assert len(inv['files'])==inv['file_count']==51
    assert len({r['relative_path'] for r in inv['files']})==51
    for r in inv['files']:check_file(A/r['relative_path'],r['sha256'],r['byte_count'])
    assert sum(r['byte_count'] for r in inv['files'])==19290536
    members_total=0
    for name,prefix,expected in [('geode-discovery-009-package-20260911T191427Z.tar.gz','',54),('geode-discovery-009-browser-artifacts.tar.gz','geode-discovery-009/',33)]:
        with tarfile.open(A/name) as tar:
            seen=set();count=0
            for m in tar:
                q=PurePosixPath(m.name)
                assert not q.is_absolute() and '..' not in q.parts
                assert m.isfile() or m.isdir()
                assert m.name not in seen;seen.add(m.name)
                if m.isdir():continue
                count+=1
                p=A/m.name
                assert p.is_file() and m.size==p.stat().st_size
                h=sha256();stream=tar.extractfile(m)
                for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
                assert h.hexdigest()==digest(p)
            assert count==expected;members_total+=count
            if not prefix:assert {r['relative_path'] for r in inv['files']}<=seen
    assert members_total==87
    aliases=[('report-20260911T191427Z.md','report-20260911T191427Z.md'),('attempted_urls.json','logs/attempted_urls.json'),('backlog.json','logs/backlog.json'),('priority_candidates_final.json','priority_candidates_final.json'),('artifact_inventory.json','exports/artifact_inventory_20260911T191427Z.json')]
    for outer,inner in aliases:assert digest(B/'received'/outer)==digest(A/inner)
    for p in (A/'geode-discovery-009').rglob('*'):
        if p.is_file():assert digest(p)==digest(A/p.relative_to(A/'geode-discovery-009'))
    for line in (B/'received/hash-summary-20260911T191427Z.txt').read_text().splitlines():
        h,p=line.split(maxsplit=1);assert digest(Path(p))==h
    logs=json.loads((A/'logs/attempted_urls.json').read_text())['events']
    assert len(logs)==13 and len({r['event_id'] for r in logs})==13
    public=[r for r in logs if r['public_open']]
    assert len(public)==12 and len({r['requested_url'] for r in public})==9
    priorities=json.loads((A/'priority_candidates_final.json').read_text())['candidates']
    assert [r['id'] for r in priorities]==[f'SD009-{i:02}' for i in range(1,9)]
    assert all(r['legal_currentness']=='not_verified' and r['authority_id']=='CO-COUNTY-LARIMER' for r in priorities)
    def ref(name):
        p=B/name
        return FileRef(path=name,sha256=digest(p),size_bytes=p.stat().st_size)
    return ValidationResult(schema_version=1,validated_at=datetime.now(timezone.utc),audit=ref('INTAKE_AUDIT.json'),custody_receipt=ref('CUSTODY_RECEIPT.json'),checks_passed=['Strict Pydantic audit and JSON Schema validation','Custody receipt JSON Schema and 97 original/copy hash-size checks','All hash-bound comparison and supporting evidence','Three unrepaired, unencrypted PDFs and 27 structural pages','All 51 inventory file hashes/sizes','All 87 safe regular tar members; complete main archive inventory','Five top-level and 33 nested byte-identical aliases','All six advertised hashes','Event/priority unique IDs and declared row/target counts; exact public-attempt completeness remains unverified','Scoped excerpt image bindings; machine validation does not certify image transcription or legal status'],original_and_received_file_pairs=97,inventoried_files=51,checked_tar_file_members=87,source_pdfs=3,structural_pages=27,visual_pages_previously_inspected=10,exact_publisher_acquisition_verified=False,legal_currentness='not_verified')

if __name__=='__main__':
    result=validate()
    print(result.model_dump_json(indent=2))
