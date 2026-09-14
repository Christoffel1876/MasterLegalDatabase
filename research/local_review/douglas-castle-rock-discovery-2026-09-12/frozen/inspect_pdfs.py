"""Bounded structural PDF preservation; native extraction is explicitly unreviewed."""
from __future__ import annotations
import json
from pathlib import Path
import pymupdf
from pydantic import BaseModel, ConfigDict, Field
from capture import Event, Ref, HERE, ref, write

class Page(BaseModel):
    """One unchanged native extraction and optional complete-page rendering."""
    model_config = ConfigDict(strict=True, extra='forbid')
    physical_page: int
    native: Ref
    width_points: float
    height_points: float
    render: Ref | None

class Document(BaseModel):
    """Structure, not a full transcription or legal-currentness certificate."""
    model_config = ConfigDict(strict=True, extra='forbid')
    event_id: str
    source: Ref
    page_count: int
    repaired: bool
    encrypted: bool
    engine: str
    native_method: str
    native_review_status: str
    render_dpi: int
    pages: list[Page]

def main() -> None:
    """Preserve each PDF page's native bytes and selected full-page PNGs."""
    for eid in ['E013','E015','E017','E018','E019','E026','E028','E031']:
        event = Event.model_validate_json((HERE/'events'/eid/'event.json').read_bytes())
        data = (HERE/event.body.path).read_bytes()
        if not data.startswith(b'%PDF-'):
            raise ValueError('Expected PDF magic')
        doc = pymupdf.open(stream=data, filetype='pdf')
        if doc.is_encrypted or doc.is_repaired or len(doc) == 0:
            raise ValueError('PDF structure requires separate review')
        pages=[]
        rendered={0}
        if eid in ['E013','E019','E026']:
            rendered.add(1)
        if eid in ['E013','E018','E026','E028','E031']:
            rendered.add(len(doc)-1)
        for i,page in enumerate(doc):
            native=HERE/'pdf-evidence'/eid/f'page-{i+1:04d}.native.txt'
            write(native,page.get_text('text',sort=False,flags=195).encode('utf-8'))
            png=None
            if i in rendered:
                target=HERE/'pdf-evidence'/eid/f'page-{i+1:04d}.png'
                write(target,page.get_pixmap(dpi=150,alpha=False).tobytes('png'))
                png=ref(target)
            pages.append(Page(physical_page=i+1,native=ref(native),
                              width_points=float(page.rect.width),
                              height_points=float(page.rect.height),render=png))
        record=Document(event_id=eid,source=event.body,page_count=len(doc),
                        repaired=doc.is_repaired,encrypted=doc.is_encrypted,
                        engine='PyMuPDF '+pymupdf.VersionBind,
                        native_method='get_text(text, sort=False, flags=195); UTF-8 unchanged',
                        native_review_status='machine_native_text_unreviewed',
                        render_dpi=150,pages=pages)
        write(HERE/'pdf-evidence'/eid/'STRUCTURE.json',
              record.model_dump_json(indent=2).encode()+b'\n')
        print(eid,len(doc),len(rendered))
    write(HERE/'PDF_STRUCTURE.schema.json',
          (json.dumps(Document.model_json_schema(),indent=2)+'\n').encode())

if __name__=='__main__':
    main()
