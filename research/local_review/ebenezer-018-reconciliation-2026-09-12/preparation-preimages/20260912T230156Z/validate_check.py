"""Read-only verification of the additive, candidate-aware EB018 check."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator
import pymupdf

HERE = Path(__file__).absolute().parent
ROOT_INVENTORY = 'caef1211d7a8b310234b403e1e4c8d3ed01dfb57d5f6fa4b291abc91a87f8f65'
ROOT_VERIFIER = '4224251ff28d743ac5a26e30f768cde896d9be0349fa5bf396cde3475d4bbeec'
SOURCE_SHA = '8fb5dc78f67407a22857160f107a0253da42320e9e502387be573ef53cab9f27'
CANDIDATE_SHA = '3c00b78086a8d596f4a86afa677cd8507ccf471f58fd5cde9bd730d96d25ef51'

class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)

class Asset(Strict):
    path: str
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    size_bytes: int = Field(ge=0)

class Crop(Strict):
    path: str
    physical_page: int = Field(ge=1, le=5)
    source_image: Asset
    pixel_box: tuple[int, int, int, int]
    method: Literal['PyMuPDF Pixmap.copy: exact source PNG pixels, no resampling']
    scope: str

class Slice(Strict):
    id: str
    physical_page: int = Field(ge=1, le=5)
    native_evidence: Asset
    start_byte: int = Field(ge=0)
    end_byte: int = Field(gt=0)
    exact_native_text: str
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    purpose: str

class Observation(Strict):
    id: str
    disposition_ids: list[str]
    physical_pages: list[int]
    conclusion: str
    native_slice_ids: list[str]
    crop_paths: list[str]
    correction_required: Literal[False] = False

class Check(Strict):
    schema_version: Literal[1] = 1
    source_id: Literal['weld-building-fees-sd008-01']
    authority_id: Literal['CO-COUNTY-WELD']
    review_mode: Literal['candidate_report_and_prior_review_aware_direct_image_check']
    completed_at: str
    status: Literal['no_actionable_issue_in_scoped_reconciliation_check']
    original_root_inventory_sha256: Literal[ROOT_INVENTORY]
    frozen_inputs: list[Asset]
    original_delivery_reports: list[Asset]
    full_page_images_directly_inspected: list[int]
    report_disposition_ids_read: list[str]
    pdf_page_count: Literal[5] = 5
    native_page_count_reproduced: Literal[5] = 5
    total_native_bytes: Literal[14311] = 14311
    candidate_bytes: Literal[14876] = 14876
    selected_slices: list[Slice]
    crops: list[Crop]
    observations: list[Observation]
    limits: list[str]
    blind_review: Literal[False] = False
    exhaustive_252_cell_review: Literal[False] = False
    currentness: Literal['not_verified'] = 'not_verified'
    answer_safe: Literal[False] = False
    source_changes: Literal[False] = False
    native_changes: Literal[False] = False
    external_report_changes: Literal[False] = False
    @model_validator(mode='after')
    def coverage(self):
        if self.full_page_images_directly_inspected != [1,2,3,4,5]:
            raise ValueError('Expected five directly viewed full page images')
        if self.report_disposition_ids_read != [f'EB018-P2-{n:03}' for n in range(1,21)]:
            raise ValueError('Expected all twenty dispositions read')
        if len({x.id for x in self.selected_slices}) != len(self.selected_slices):
            raise ValueError('Duplicate slice')
        if len({x.path for x in self.frozen_inputs}) != len(self.frozen_inputs):
            raise ValueError('Duplicate frozen input')
        if len(self.original_delivery_reports) != 5:
            raise ValueError('Five external reports/receipts required')
        return self

class Inventory(Strict):
    schema_version: Literal[1] = 1
    files: list[Asset]
    exclusions: Literal['INVENTORY.json and INVENTORY.schema.json only']
    @model_validator(mode='after')
    def unique(self):
        if len({x.path for x in self.files}) != len(self.files):
            raise ValueError('Duplicate inventory path')
        return self

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def ordinary(path: Path) -> None:
    for parent in (path, *path.parents):
        if parent.is_symlink():
            raise ValueError('Symlink not admitted')
    if not path.is_file():
        raise ValueError('Ordinary file required')

def checked(ref: Asset) -> bytes:
    rel = Path(ref.path)
    if rel.is_absolute() or '..' in rel.parts or rel.as_posix() != ref.path:
        raise ValueError('Non-canonical relative path')
    p = HERE / rel
    ordinary(p)
    data = p.read_bytes()
    if len(data) != ref.size_bytes or sha(data) != ref.sha256:
        raise ValueError(f'Hash/size mismatch: {ref.path}')
    return data

def verify() -> None:
    for p in HERE.rglob('*'):
        if p.is_symlink() or not (p.is_file() or p.is_dir()):
            raise ValueError('Nonordinary inventory entry')
    inv = Inventory.model_validate_json((HERE/'INVENTORY.json').read_bytes())
    expected = {x.path for x in inv.files} | {'INVENTORY.json','INVENTORY.schema.json'}
    actual = {p.relative_to(HERE).as_posix() for p in HERE.rglob('*') if p.is_file()}
    if actual != expected:
        raise ValueError('Closed inventory differs')
    for ref in inv.files:
        checked(ref)
    rec = Check.model_validate_json((HERE/'INDEPENDENT_CHECK.json').read_bytes())
    if json.loads((HERE/'INDEPENDENT_CHECK.schema.json').read_bytes()) != Check.model_json_schema():
        raise ValueError('Receipt schema differs')
    if json.loads((HERE/'INVENTORY.schema.json').read_bytes()) != Inventory.model_json_schema():
        raise ValueError('Inventory schema differs')
    frozen = HERE/'frozen-root-reconciliation'
    if sha((frozen/'INVENTORY.json').read_bytes()) != ROOT_INVENTORY:
        raise ValueError('Root inventory pin differs')
    if sha((frozen/'build_reconciliation.py').read_bytes()) != ROOT_VERIFIER:
        raise ValueError('Root verifier pin differs')
    frozen_paths = {p.relative_to(HERE).as_posix() for p in frozen.rglob('*') if p.is_file()}
    if frozen_paths != {x.path for x in rec.frozen_inputs}:
        raise ValueError('Frozen package set differs')
    for ref in rec.frozen_inputs + rec.original_delivery_reports:
        checked(ref)
    if {x.path for x in rec.original_delivery_reports} != {
        f'frozen-root-reconciliation/reports/{name}' for name in (
            'PASS1_frozen.md','PASS1_NOTES.md','PASS1_FREEZE_RECEIPT.json',
            'PASS2_REVIEW.md','COMPLETION_RECEIPT.json')}:
        raise ValueError('External report set differs')
    subprocess.run([sys.executable,'-I','-B',str(frozen/'build_reconciliation.py'),'--verify'],
                   cwd=HERE, check=True, timeout=30)
    original = frozen/'source/original.pdf'
    if sha(original.read_bytes()) != SOURCE_SHA:
        raise ValueError('PDF pin differs')
    candidate = bytearray()
    native = {}
    with pymupdf.open(original) as pdf:
        if len(pdf) != 5:
            raise ValueError('Source page count differs')
        for n in range(1,6):
            row = json.loads((frozen/f'native-evidence/page-{n:04}.json').read_bytes())
            text = pdf[n-1].get_text('text',sort=False,flags=195).encode('utf-8')
            native[n] = text
            if (row['source_id'] != rec.source_id or row['source_sha256'] != SOURCE_SHA
                or row['physical_page'] != n or row['expected_pages'] != 5
                or row['text'].encode() != text or row['text_sha256'] != sha(text)
                or row['text_size_bytes'] != len(text)
                or row['source_image_sha256'] != sha((frozen/f'source/page-{n:04}.png').read_bytes())):
                raise ValueError('Native evidence binding differs')
            candidate += f'===== PHYSICAL PDF PAGE {n} OF 5 (PACKAGING MARKER) =====\n'.encode()
            candidate += text
            candidate += f'\n===== END PHYSICAL PDF PAGE {n} (PACKAGING MARKER) =====\n\n'.encode()
    if (sum(map(len,native.values())) != rec.total_native_bytes or len(candidate) != rec.candidate_bytes
        or sha(candidate) != CANDIDATE_SHA or candidate != (frozen/'source/candidate.txt').read_bytes()):
        raise ValueError('Candidate/native preservation differs')
    for entry in rec.selected_slices:
        checked(entry.native_evidence)
        if entry.native_evidence.path != f'frozen-root-reconciliation/native-evidence/page-{entry.physical_page:04}.json':
            raise ValueError('Slice page binding differs')
        selected = native[entry.physical_page][entry.start_byte:entry.end_byte]
        if entry.end_byte > len(native[entry.physical_page]) or entry.start_byte >= entry.end_byte:
            raise ValueError('Slice out of bounds')
        if selected != entry.exact_native_text.encode() or sha(selected) != entry.sha256:
            raise ValueError('Slice bytes differ')
    for crop in rec.crops:
        checked(crop.source_image)
        if crop.source_image.path != f'frozen-root-reconciliation/source/page-{crop.physical_page:04}.png':
            raise ValueError('Crop page binding differs')
        image = pymupdf.Pixmap(str(HERE/crop.source_image.path))
        box = pymupdf.IRect(crop.pixel_box)
        if box.is_empty or not image.irect.contains(box):
            raise ValueError('Crop bounds differ')
        observed = pymupdf.Pixmap(str(HERE/crop.path))
        replay = pymupdf.Pixmap(image.colorspace,box,image.alpha)
        replay.copy(image,box)
        if (observed.width,observed.height,observed.n,observed.samples) != (
                replay.width,replay.height,replay.n,replay.samples):
            raise ValueError('Crop pixels differ')
    slice_ids = {s.id for s in rec.selected_slices}
    crop_paths = {c.path for c in rec.crops}
    for ob in rec.observations:
        if (not set(ob.native_slice_ids) <= slice_ids or not set(ob.crop_paths) <= crop_paths
            or not set(ob.disposition_ids) <= set(rec.report_disposition_ids_read)):
            raise ValueError('Observation reference differs')
    for ref in inv.files:
        checked(ref)
    print('PASS: five native pages reproduced; five original reports bound; '
          'five direct-image crops reproduced; scoped independent receipt valid.')

if __name__ == '__main__':
    verify()
