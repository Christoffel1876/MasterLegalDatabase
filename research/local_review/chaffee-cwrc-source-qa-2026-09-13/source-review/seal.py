"""One-time closed seal after offline tests; never fetches or reruns OCR."""
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

from models import Manifest, Ref
from verify_source_review import verify_review

ROOT = Path(__file__).resolve().parent


class Validation(BaseModel):
    """Typed receipt of actual local structural replay and measured focused tests."""
    model_config = ConfigDict(strict=True, extra='forbid')
    schema_version: Literal['cwrc-validation-1']
    recorded_at: str
    source_qa: Ref
    verifier: Ref
    models: Ref
    tests: Ref
    test_log: Ref
    coverage: Ref
    passed_tests: Literal[63]
    measured_line_and_branch_coverage: float
    coverage_subjects: list[str]
    structural_result: dict[str, int | str | bool]
    limitation: str


def ref(path: Path) -> Ref:
    """Bind exact payload bytes relative to this package."""
    data=path.read_bytes()
    return Ref(path=path.relative_to(ROOT).as_posix(),
               sha256=hashlib.sha256(data).hexdigest(),size_bytes=len(data))


def put(path: Path, data: bytes) -> None:
    """Atomically write a new final file, refusing overwrite."""
    if path.exists() or path.is_symlink():
        raise ValueError('already sealed; preserve this packet unchanged')
    temp=path.with_name(path.name+'.tmp')
    with temp.open('xb') as stream:
        stream.write(data)
    os.replace(temp,path)


def main() -> None:
    """Validate the final typed source review and close every ordinary payload."""
    if (ROOT/'FINAL_MANIFEST.json').exists():
        raise ValueError('already sealed')
    buffers={p.relative_to(ROOT).as_posix():p.read_bytes()
             for p in ROOT.rglob('*') if p.is_file()}
    result=verify_review(buffers)
    coverage=json.loads(buffers['validation/coverage-seal.json'])['totals']['percent_covered']
    if coverage < 90 or b'63 passed' not in buffers['validation/focused-seal.log']:
        raise ValueError('required focused tests/coverage not satisfied')
    receipt=Validation(schema_version='cwrc-validation-1',
        recorded_at=datetime.now(timezone.utc).isoformat().replace('+00:00','Z'),
        source_qa=ref(ROOT/'SOURCE_QA.json'),verifier=ref(ROOT/'verify_source_review.py'),
        models=ref(ROOT/'models.py'),tests=ref(ROOT/'test_review.py'),
        test_log=ref(ROOT/'validation/focused-seal.log'),
        coverage=ref(ROOT/'validation/coverage-seal.json'),passed_tests=63,
        measured_line_and_branch_coverage=coverage,
        coverage_subjects=['models.py','verify_source_review.py'],structural_result=result,
        limitation='Tests are offline, use temporary/in-memory corruption fixtures and include '
        'all fourteen fresh Poppler render comparisons. Coverage excludes historical retrieval, '
        'OCR execution and one-time construction; neither tests nor hashes independently prove '
        'human visual fidelity or legal currentness. Root acceptance is separately recorded.')
    put(ROOT/'VALIDATION.json',(receipt.model_dump_json(indent=2)+'\n').encode())
    put(ROOT/'VALIDATION.schema.json',
        (json.dumps(Validation.model_json_schema(),indent=2)+'\n').encode())
    paths=sorted((p for p in ROOT.rglob('*') if p.is_file()),
                 key=lambda p:p.relative_to(ROOT).as_posix())
    if any(p.is_symlink() for p in ROOT.rglob('*')):
        raise ValueError('symlink in closure')
    manifest=Manifest(schema_version='cwrc-closed-payloads-1',
        created_at=datetime.now(timezone.utc).isoformat().replace('+00:00','Z'),
        files=[ref(p) for p in paths],payload_count=len(paths))
    put(ROOT/'FINAL_MANIFEST.json',(manifest.model_dump_json(indent=2)+'\n').encode())


if __name__=='__main__':
    main()
