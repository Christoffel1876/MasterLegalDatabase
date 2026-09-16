"""Exact RGB pixel crops from already preserved full-page source images."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import pymupdf
from pydantic import BaseModel, ConfigDict

ROOT = Path(__file__).resolve().parent


class Crop(BaseModel):
    """Exact top-left pixel rectangle and both byte identities."""
    model_config = ConfigDict(extra='forbid', strict=True)
    page: int
    image_path: str
    image_sha256: str
    rectangle: tuple[int, int, int, int]
    path: str
    sha256: str


class Receipt(BaseModel):
    """Local crop generation, distinct from subsequent inspection."""
    model_config = ConfigDict(extra='forbid', strict=True)
    created_at: str
    method: str
    crops: list[Crop]


def main() -> None:
    """Create only the seven chosen source-detail crops."""
    definitions = [
        (1, 'p1-citation', (200, 680, 2400, 1090)),
        (1, 'p1-numbered', (200, 1750, 2400, 2440)),
        (1, 'p1-execution', (180, 2440, 2390, 2640)),
        (2, 'p2-execution', (170, 300, 2410, 1440)),
        (3, 'p3-upper', (200, 680, 2400, 1700)),
        (3, 'p3-lower', (190, 1660, 2440, 3090)),
        (4, 'p4-complete-text', (170, 40, 2370, 930)),
    ]
    crops = []
    for page, name, rectangle in definitions:
        image_path = f'pages/page-{page:04}.png'
        image = (ROOT / image_path).read_bytes()
        pix = pymupdf.Pixmap(image)
        x0, y0, x1, y1 = rectangle
        assert 0 <= x0 < x1 <= pix.width and 0 <= y0 < y1 <= pix.height
        samples = b''.join(pix.samples[y * pix.stride + x0 * pix.n:
                                      y * pix.stride + x1 * pix.n] for y in range(y0, y1))
        output = ROOT / f'crops/{name}.png'
        assert not output.exists()
        pymupdf.Pixmap(pymupdf.csRGB, x1 - x0, y1 - y0, samples, False).save(output)
        crops.append(Crop(page=page, image_path=image_path,
                          image_sha256=hashlib.sha256(image).hexdigest(), rectangle=rectangle,
                          path=str(output.relative_to(ROOT)),
                          sha256=hashlib.sha256(output.read_bytes()).hexdigest()))
    receipt = Receipt(created_at=datetime.now(timezone.utc).isoformat(),
                      method='Exact RGB top-left pixel slice; no resampling or text modification.',
                      crops=crops)
    for name, data in [('CROPS.json', receipt.model_dump_json(indent=2)),
                       ('CROPS.schema.json', json.dumps(Receipt.model_json_schema(), indent=2))]:
        with (ROOT / name).open('x') as handle:
            handle.write(data + '\n')


if __name__ == '__main__':
    main()
