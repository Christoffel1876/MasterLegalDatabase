"""Exact RGB source-image crops, with no resampling or source modification."""
from pathlib import Path
import pymupdf
from pydantic import Field
from models import Asset, Strict


class Crop(Strict):
    """Integer bounds in the retained full image, origin upper left."""
    id: str
    page: int
    box: list[int] = Field(min_length=4, max_length=4)
    image: Asset


class Crops(Strict):
    """All derived crop receipts."""
    crops: list[Crop]


def crop_bytes(source: Path, box: list[int]) -> bytes:
    """Crop exact RGB pixels and encode with the installed PyMuPDF version."""
    pix = pymupdf.Pixmap(str(source))
    x0, y0, x1, y1 = box
    if pix.n != 3 or not (0 <= x0 < x1 <= pix.width and 0 <= y0 < y1 <= pix.height):
        raise ValueError('Invalid RGB crop bounds')
    rows = [pix.samples[y * pix.stride + x0 * 3:y * pix.stride + x1 * 3]
            for y in range(y0, y1)]
    result = pymupdf.Pixmap(pymupdf.csRGB, x1 - x0, y1 - y0, b''.join(rows), False)
    return result.tobytes('png')
