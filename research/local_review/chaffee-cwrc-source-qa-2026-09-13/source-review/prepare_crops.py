"""Create exact half-page pixel crops for direct source inspection, once only."""
import hashlib
import os
from pathlib import Path
import pymupdf
from pydantic import BaseModel, ConfigDict

ROOT = Path(__file__).resolve().parent

class Crop(BaseModel):
    """Exact source-PNG crop identity; coordinates use top-left pixels."""
    model_config = ConfigDict(strict=True, extra='forbid')
    page: int
    source_path: str
    source_sha256: str
    rect: tuple[int, int, int, int]
    path: str
    sha256: str
    size_bytes: int
    method: str = 'Exact pixel copy from preserved full Poppler 300dpi PNG'

def main() -> None:
    """Write the two complete halves of every page and typed crop records."""
    rows = []
    for n in range(1, 15):
        source = ROOT / f'pages/page-{n:02d}.png'
        pix = pymupdf.Pixmap(source)
        for half, rect in [('top',(0,0,pix.width,1650)),
                           ('bottom',(0,1650,pix.width,pix.height))]:
            target = ROOT / f'crops/page-{n:02d}-{half}.png'
            if target.exists():
                raise ValueError('refuse existing crop')
            crop = pymupdf.Pixmap(pix.colorspace, pymupdf.IRect(rect), pix.alpha)
            crop.copy(pix, pymupdf.IRect(rect))
            data = crop.tobytes('png')
            row = Crop(page=n, source_path=source.relative_to(ROOT).as_posix(),
                       source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                       rect=rect, path=target.relative_to(ROOT).as_posix(),
                       sha256=hashlib.sha256(data).hexdigest(), size_bytes=len(data))
            temp = target.with_suffix('.tmp')
            with temp.open('xb') as f:
                f.write(data)
            os.replace(temp,target)
            rows.append(row.model_dump_json())
    target = ROOT / 'CROPS.jsonl'
    with target.with_suffix('.tmp').open('x', encoding='utf-8') as f:
        f.write('\n'.join(rows)+'\n')
    os.replace(target.with_suffix('.tmp'), target)

if __name__ == '__main__':
    main()
