"""Freeze supplied originals and render all pages for bounded document-role review."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Literal

import fitz
from pydantic import BaseModel, ConfigDict

ROOT = Path(__file__).resolve().parent
WORK = ROOT.parents[2]
DELIVERY = WORK / 'handoffs/hour-2026-09-16-2135/sherlock-delivery/20260916T214414Z'
AUDIT = WORK / 'handoffs/hour-2026-09-16-2135/ptolemy-sherlock-intake/AUDIT.json'
POPPLER = Path('/Users/mcoors/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/override/pdftoppm')

class Asset(BaseModel):
    """Exact retained local bytes."""
    model_config = ConfigDict(extra='forbid', strict=True)
    path: str
    sha256: str
    size_bytes: int

class Source(BaseModel):
    """Supplied identity and actual local preparation."""
    model_config = ConfigDict(extra='forbid', strict=True)
    priority: str
    action_id: str
    authority: str
    source: Asset
    supplied_attempt: Asset
    page_count: int
    native_page_bytes: list[int]
    render_started_at: str
    render_finished_at: str
    render_command: list[str]
    render_exit_code: int
    images: list[Asset]

class Inputs(BaseModel):
    """Frozen originals, preparation and honest receipt-only provenance."""
    model_config = ConfigDict(extra='forbid', strict=True)
    started_at: str
    finished_at: str
    custody: Literal['received_review_package']
    official_http_independently_verified: Literal[False]
    supplied_times_independently_verified: Literal[False]
    public_requests: Literal[0]
    renderer: Asset
    render_dpi: Literal[200]
    supporting_inputs: list[Asset]
    sources: list[Source]

def now() -> str:
    """Get actual UTC preparation time."""
    return datetime.now(timezone.utc).isoformat()

def asset(path: Path) -> Asset:
    """Bind exact bytes, with local path relative to this package."""
    raw=path.read_bytes()
    return Asset(path=path.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(raw).hexdigest(),size_bytes=len(raw))

def main() -> None:
    """Prepare only new files and retain every full physical page."""
    if (ROOT/'INPUTS.json').exists():
        raise ValueError('Already prepared')
    start=now(); (ROOT/'inputs').mkdir()
    supports=[]
    for original,name in [(AUDIT,'prior-AUDIT.json'),(DELIVERY/'derived/mac_copy_receipt.json','supplied-copy-receipt.json')]:
        target=ROOT/'inputs'/name; shutil.copyfile(original,target); supports.append(asset(target))
    sources=[]
    for priority,aid,pages,sha,authority in [
        ('P04','SHDISC002-A010',2,'3e846e6e0e112bb0e46eb77e8292604e722ec719e325050525ebaff995eebe9d','CO-COUNTY-JEFFERSON'),
        ('P07','SHDISC002-A023',2,'f8c2183427c8fe1169c6891aee288c7d63b643ae6219fd51dc86adde03e21561','CO-MUNICIPAL-ARVADA'),
        ('P08','SHDISC002-A026',24,'921d5e6854a740aea608ed15bef3ea0a9c4fc8da09e29ef45e3a932ffeacfbcc','CO-MUNICIPAL-ARVADA')]:
        directory=ROOT/'inputs'/priority; directory.mkdir()
        original=DELIVERY/'raw'/f'{aid}.body'; raw=original.read_bytes()
        assert hashlib.sha256(raw).hexdigest()==sha
        source=directory/'original.pdf'; source.write_bytes(raw)
        attempt=directory/'supplied-attempt.json'; shutil.copyfile(DELIVERY/'attempts'/f'{aid}.json',attempt)
        with fitz.open(source) as pdf:
            assert len(pdf)==pages
            lengths=[len(p.get_text('text',flags=195,sort=False).encode()) for p in pdf]
        renders=ROOT/'renders'/priority; renders.mkdir(parents=True)
        command=[str(POPPLER),'-r','200','-png',str(source),str(renders/'page')]
        rs=now(); completed=subprocess.run(command,capture_output=True,check=False); rf=now()
        assert completed.returncode==0,completed.stderr
        images=sorted(renders.glob('*.png')); assert len(images)==pages
        sources.append(Source(priority=priority,action_id=aid,authority=authority,
            source=asset(source),supplied_attempt=asset(attempt),page_count=pages,
            native_page_bytes=lengths,render_started_at=rs,render_finished_at=rf,
            render_command=command,render_exit_code=completed.returncode,images=[asset(p) for p in images]))
    renderer=Asset(path=str(POPPLER),sha256=hashlib.sha256(POPPLER.read_bytes()).hexdigest(),size_bytes=POPPLER.stat().st_size)
    data=Inputs(started_at=start,finished_at=now(),custody='received_review_package',
        official_http_independently_verified=False,supplied_times_independently_verified=False,
        public_requests=0,renderer=renderer,render_dpi=200,supporting_inputs=supports,sources=sources)
    (ROOT/'INPUTS.schema.json').write_text(json.dumps(Inputs.model_json_schema(),indent=2)+'\n')
    (ROOT/'INPUTS.json').write_text(data.model_dump_json(indent=2)+'\n')
    sys.stdout.write(data.model_dump_json(indent=2)+'\n')
if __name__=='__main__':main()
