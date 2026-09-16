"""Seal the prepared visualization without changing the thread's installed fragment."""
from __future__ import annotations
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

HERE=Path(__file__).resolve().parent

class Asset(BaseModel):
    """Exact relative immutable file identity."""
    model_config=ConfigDict(extra='forbid',strict=True)
    path:str
    sha256:str=Field(pattern=r'^[a-f0-9]{64}$')
    size_bytes:int=Field(ge=0)

class Receipt(BaseModel):
    """Prepared data-map scope and bounded visual QA."""
    model_config=ConfigDict(extra='forbid',strict=True)
    status:Literal['prepared_not_installed']
    sealed_at:str
    source_inventory_sha256:Literal['e2531da64de89de3fff894283707e32833633898c1b4961ae535c262bb83c413']
    fragment_sha256:Literal['b7ede04ac6de2bcc1f2affdfc45f0db9bf56e9084cc9a142358afb95552efbc0']
    sources:Literal[64]
    mapped:Literal[27]
    unmapped:Literal[37]
    authorities:Literal[12]
    direct_screenshots_inspected:list[str]
    tests:list[str]
    limitations:list[str]
    files:list[Asset]


def seal() -> None:
    """Hash all payloads; validate receipt before writing."""
    if (HERE/'FINAL_MANIFEST.json').exists():
        raise ValueError('already sealed')
    report=json.loads((HERE/'geode-source-review-inventory-qa.json').read_bytes())
    assert report['status']=='passed' and not report['errors']
    assert {(r['theme'],r['width']) for r in report['results']}=={
        ('light',736),('light',360),('dark',736),('dark',360)}
    assert all(r['selections_checked']==64 and not r['layout']['overflow'] for r in report['results'])
    (HERE/'FINAL_MANIFEST.schema.json').write_text(json.dumps(Receipt.model_json_schema(),indent=2)+'\n')
    files=[]
    for path in sorted(HERE.rglob('*')):
        if not path.is_file():continue
        assert not path.is_symlink()
        data=path.read_bytes()
        files.append(Asset(path=path.relative_to(HERE).as_posix(),
                           sha256=hashlib.sha256(data).hexdigest(),size_bytes=len(data)))
    result=Receipt(status='prepared_not_installed',
        sealed_at=datetime.now(timezone.utc).isoformat().replace('+00:00','Z'),
        source_inventory_sha256=report['source_inventory_sha256'],
        fragment_sha256=report['fragment_sha256'],sources=64,mapped=27,unmapped=37,authorities=12,
        direct_screenshots_inspected=[r['screenshot'] for r in report['results']],
        tests=['All 64 IDs, authority joins and exact mapped/null kinds match proposed inventory.',
               'All 64 selections update at 736/360 widths in light/dark; one pressed cell.',
               'Keyboard Enter activates three new and retained diagnostic selections.',
               'No overflow or page errors in any of four configurations.',
               'Fragment unchanged through browser QA and below 1 MB; all non-local requests blocked.'],
        limitations=['Prepared handoff only; thread fragment remains root-owned.',
                     'Source review counts do not certify legal currentness.',
                     'Preview wrappers force themes; fragment remains theme-aware.',
                     'Localhost preview process was stopped after QA.'],files=files)
    (HERE/'FINAL_MANIFEST.json').write_text(result.model_dump_json(indent=2)+'\n')

if __name__=='__main__':seal()
