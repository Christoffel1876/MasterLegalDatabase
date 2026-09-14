"""Strict data-only models and reproducible native/table geometry for this four-page source."""
from __future__ import annotations
import difflib
import hashlib
import math
import re
from pathlib import Path, PurePosixPath
from typing import Literal
import pymupdf
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

SOURCE_SHA = '0ba13c07bede5bf07c24dd8bbbe604c61745e8a73be773a7987e26dfa601414b'
PASS1_SHA = 'b69b9808827de0e6adafcbe44a9b50829962f4437ceee50613acad8ea85643b8'
COUNTS = [13, 14, 14, 3]
class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
class Ref(Strict):
    path: str
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    size_bytes: int = Field(ge=0)
    @model_validator(mode='after')
    def confined(self):
        p = PurePosixPath(self.path)
        if p.is_absolute() or '..' in p.parts or str(p) != self.path or '\\' in self.path:
            raise ValueError('unsafe relative evidence path')
        return self
class Line(Strict):
    id: str
    start_byte: int = Field(ge=0)
    end_byte: int = Field(gt=0)
    text: str
    sha256: str
    bbox: list[float] | None
class Page(Strict):
    physical_page: int = Field(ge=1, le=4)
    width: float
    height: float
    native: Ref
    image: Ref
    lines: list[Line]
    horizontal_table_boundaries: list[float]
    context_line_ids: list[str]
class Cell(Strict):
    role: Literal['application', 'fee']
    bbox: list[float]
    pixel_bbox: list[int]
    line_ids: list[str]
    native_text: str
    reviewed_display: str
class Nested(Strict):
    id: str
    kind: Literal['paired_subcategory', 'fee_bullet']
    application_line_ids: list[str]
    fee_line_ids: list[str]
    application_display: str
    fee_display: str
    inherited_note_line_ids: list[str]
class Row(Strict):
    row_id: str
    physical_page: int
    application: Cell
    fee: Cell
    nested: list[Nested]
class Annotation(Strict):
    id: str
    kind: Literal['reviewer_erratum', 'source_graphical_mark', 'normalization', 'source_context']
    affected_rows: list[str]
    pages: list[int]
    statement: str
    limitation: str
    proof_paths: list[str]
class Crop(Strict):
    physical_page: int
    clip: list[float]
    scale: float
    artifact: Ref
    pixel_sha256: str
class QA(Strict):
    source: Ref
    source_id: Literal['city-pueblo-planning-fees']
    authority_id: Literal['CO-MUNICIPAL-PUEBLO']
    source_format: Literal['publisher_pdf_as_received']
    prepared_at: AwareDatetime
    review_method: str
    pass1: Ref
    custody_event: Ref
    requested_url: Literal['https://www.pueblo.us/DocumentCenter/View/21956/Fee-Schedule?bidId=']
    request_started_at: AwareDatetime
    response_finished_at: AwareDatetime
    repository_received_at: None = None
    actual_page_count: Literal[4] = 4
    native_byte_count: Literal[4923] = 4923
    physical_application_row_count: Literal[44] = 44
    pages: list[Page] = Field(min_length=4, max_length=4)
    rows: list[Row] = Field(min_length=44, max_length=44)
    annotations: list[Annotation]
    reproducible_crops: list[Crop]
    source_graphic_bbox: list[float]
    repeated_region_equality: dict[str, list[str]]
    source_date_claim: Literal['2-13-26 appears on all four pages without an explicit adoption/effective-date label']
    qualifications: list[str]
    legal_currentness: Literal['not_verified'] = 'not_verified'
    adoption_verified: Literal[False] = False
    answer_safe: Literal[False] = False
    monitoring_enrolled: Literal[False] = False
class Inventory(Strict):
    files: list[Ref]
    @model_validator(mode='after')
    def unique(self):
        if len({f.path for f in self.files}) != len(self.files):raise ValueError('duplicate inventory path')
        return self

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
def ordinary(path: Path) -> Path:
    if path.is_symlink() or any(p.is_symlink() for p in path.parents) or not path.is_file():
        raise ValueError('nonordinary evidence')
    return path
def file_ref(root: Path, path: Path) -> Ref:
    with ordinary(path).open('rb') as h:digest = hashlib.file_digest(h, 'sha256').hexdigest()
    return Ref(path=path.relative_to(root).as_posix(), sha256=digest, size_bytes=path.stat().st_size)
def checked(root: Path, value: Ref) -> bytes:
    if file_ref(root, root / value.path) != value:raise ValueError('evidence hash or size mismatch')
    data = (root / value.path).read_bytes()
    if sha(data) != value.sha256:raise ValueError('evidence changed while reading')
    return data
def norm(text: str) -> str:
    text = re.sub(r'(?m)^\s*[-•]\s*', '', text)
    return re.sub(r'\s+', '', text)
def box(value) -> list[float]:
    return [round(float(x), 5) for x in value]
def pixels(value: list[float]) -> list[int]:
    return [math.floor(value[0]*160/72), math.floor(value[1]*160/72),
            math.ceil(value[2]*160/72), math.ceil(value[3]*160/72)]
def native_lines(page, raw: bytes, number: int) -> list[Line]:
    actual = raw.decode('utf-8').splitlines(keepends=True)
    geometry = [(''.join(s['text'] for s in line['spans'])+'\n', box(line['bbox']))
                for block in page.get_text('dict')['blocks'] if 'lines' in block
                for line in block['lines']]
    mapping = {}
    for match in difflib.SequenceMatcher(a=actual, b=[t for t, _ in geometry], autojunk=False).get_matching_blocks():
        for k in range(match.size):mapping[match.a+k] = geometry[match.b+k][1]
    offset = 0; lines = []
    for i, text in enumerate(actual):
        if i not in mapping and text.strip():raise ValueError('nonblank native geometry unmatched')
        end = offset + len(text.encode())
        lines.append(Line(id=f'P{number}-L{i+1:03d}', start_byte=offset, end_byte=end,
                          text=text, sha256=sha(text.encode()), bbox=mapping.get(i)))
        offset = end
    if offset != len(raw):raise ValueError('native byte coverage differs')
    return lines

def grid(page) -> list[float]:
    values = set()
    for drawing in page.get_drawings():
        for item in drawing['items']:
            if item[0] == 're':
                rect = item[1]
                if abs(rect.x0-72.48)<.02 and 178<rect.width<179 and 0<rect.height<1:
                    values.add(round(rect.y0, 5))
    return sorted(values)

def cell_lines(lines: list[Line], bounds: list[float]) -> list[Line]:
    return [line for line in lines if line.bbox is not None and
            bounds[0] < (line.bbox[0]+line.bbox[2])/2 < bounds[2] and
            bounds[1] < (line.bbox[1]+line.bbox[3])/2 < bounds[3]]
def find_slice(lines: list[Line], target: str) -> list[str]:
    wanted = norm(target)
    for start in range(len(lines)):
        value = ''
        for end in range(start, len(lines)):
            value += lines[end].text
            if norm(value) == wanted:return [line.id for line in lines[start:end+1]]
            if len(norm(value)) > len(wanted):break
    raise ValueError('nested source association not located: '+target)

def nested_entries(row_id: str, app: Cell, fee: Cell, lines: list[Line]) -> list[Nested]:
    lookup = {line.id:line for line in lines}
    app_lines = [lookup[x] for x in app.line_ids]
    fee_lines = [lookup[x] for x in fee.line_ids]
    paired = row_id in {'P1-08','P1-13','P3-04'}
    notes = []
    if row_id == 'P4-01':notes = find_slice(fee_lines, '(Note: fees per plat)')
    if paired:
        labels = app.reviewed_display.split('\n- ')[1:]
        fees = [x.removeprefix('- ') for x in fee.reviewed_display.splitlines()]
        if len(labels) != len(fees):raise ValueError('paired list lengths differ')
        result = []; app_cursor = 0; fee_cursor = 0
        for i,(label,amount) in enumerate(zip(labels,fees),1):
            native_amount = amount.replace('$150_+', '$150 +') if row_id=='P3-04' else amount
            app_ids = find_slice(app_lines[app_cursor:], label)
            fee_ids = find_slice(fee_lines[fee_cursor:], native_amount)
            app_cursor = next(j for j, line in enumerate(app_lines) if line.id == app_ids[-1]) + 1
            fee_cursor = next(j for j, line in enumerate(fee_lines) if line.id == fee_ids[-1]) + 1
            result.append(Nested(id=f'{row_id}-N{i:02d}',kind='paired_subcategory',
                application_line_ids=app_ids, fee_line_ids=fee_ids, application_display=label,
                fee_display=amount,inherited_note_line_ids=notes))
        return result
    if not fee.reviewed_display.startswith('- '):return []
    amounts = fee.reviewed_display.split('\n- ')
    result = []
    for i, amount in enumerate(amounts,1):
        amount = amount.removeprefix('- ').split('\n(Note:')[0]
        result.append(Nested(id=f'{row_id}-N{i:02d}',kind='fee_bullet',
            application_line_ids=app.line_ids, fee_line_ids=find_slice(fee_lines, amount),
            application_display=app.reviewed_display, fee_display=amount,
            inherited_note_line_ids=notes))
    return result

def derive_tables(root: Path, frozen_rows: list[dict]) -> tuple[list[Page], list[Row]]:
    """Replay every native byte, source grid edge, physical cell and nested association."""
    doc = pymupdf.open(root/'original.pdf');pages=[];rows=[]
    if len(doc)!=4 or doc.is_repaired or doc.is_encrypted:raise ValueError('PDF structure differs')
    for number,page in enumerate(doc,1):
        native_ref=file_ref(root,root/f'native/page-{number:04d}.txt');raw=checked(root,native_ref)
        if page.get_text('text').encode()!=raw:raise ValueError('native extraction differs')
        lines=native_lines(page,raw,number);boundaries=grid(page)
        if len(boundaries)!=COUNTS[number-1]+2:raise ValueError('table boundary count differs')
        used=set(); local_rows=[row for row in frozen_rows if row['physical_page']==number]
        for i,old in enumerate(local_rows,1):
            row_id=f'P{number}-{i:02d}'
            if old['row_id']!=row_id:raise ValueError('physical row ordering differs')
            cells=[]
            for role,left,right in [('application',72.48,251.12),('fee',251.6,547.2)]:
                bounds=box([left,boundaries[i]+.48,right,boundaries[i+1]])
                selected=cell_lines(lines,bounds);text=''.join(line.text for line in selected)
                display=old['application' if role=='application' else 'fee']
                if row_id=='P1-11' and role=='fee':display=display.replace('footprint or site','footprint nor site')
                comparison=display.replace('$150_+','$150 +') if row_id=='P3-04' and role=='fee' else display
                if norm(text)!=norm(comparison):raise ValueError(f'visual/native mismatch {row_id} {role}: {text!r} vs {comparison!r}')
                cells.append(Cell(role=role,bbox=bounds,pixel_bbox=pixels(bounds),
                    line_ids=[line.id for line in selected],native_text=text,reviewed_display=display))
                used.update(line.id for line in selected)
            rows.append(Row(row_id=row_id,physical_page=number,application=cells[0],fee=cells[1],
                            nested=nested_entries(row_id,cells[0],cells[1],lines)))
        pages.append(Page(physical_page=number,width=float(page.rect.width),height=float(page.rect.height),
            native=native_ref,image=file_ref(root,root/f'page-{number:04d}.png'),lines=lines,
            horizontal_table_boundaries=boundaries,context_line_ids=[l.id for l in lines if l.id not in used]))
    return pages,rows
