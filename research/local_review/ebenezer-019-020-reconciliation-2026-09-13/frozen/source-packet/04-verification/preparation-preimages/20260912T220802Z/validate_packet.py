"""Verify the sealed Weld packet locally without editing sources or contacting services."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path
from typing import Literal

import jsonschema
import pymupdf
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

SPECS = [
    ('EB-PDF-018', 'weld-building-fees-sd008-01', 5,
     '8fb5dc78f67407a22857160f107a0253da42320e9e502387be573ef53cab9f27'),
    ('EB-PDF-019', 'weld-ordinance-26-01-atlas-directed', 5,
     '2ba9073aa06420e41a5dce98fade56278df96729630f5d61d3ab1c910e839eb0'),
    ('EB-PDF-020', 'weld-ehs-fees-2026-atlas-directed', 3,
     '852801c5ad0056c7b0dde6300e66e86f2e4235ce0efc16471d5210d74aa17ed3'),
]


class Strict(BaseModel):
    """Reject extra fields and implicit scalar conversion."""
    model_config = ConfigDict(extra='forbid', strict=True)


class FileRef(Strict):
    """A confined immutable packet file."""
    path: str = Field(min_length=1)
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    size_bytes: int = Field(ge=0)

    @model_validator(mode='after')
    def confined(self) -> FileRef:
        """Disallow absolute paths and traversal in executable packet references."""
        path = Path(self.path)
        if path.is_absolute() or '..' in path.parts or str(path) != self.path:
            raise ValueError('Unconfined packet path')
        return self


class HistoricalRef(Strict):
    """Exact original location, retained as history and never opened by this verifier."""
    path: str
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    size_bytes: int = Field(ge=0)


class Copy(Strict):
    """A byte-exact frozen copy of an explicit historical input."""
    original: HistoricalRef
    frozen: FileRef
    role: str

    @model_validator(mode='after')
    def same(self) -> Copy:
        """Require byte-identity claims to agree."""
        if (self.original.sha256, self.original.size_bytes) != (
            self.frozen.sha256, self.frozen.size_bytes
        ):
            raise ValueError('Copy identity differs')
        return self


class JSONLRow(Strict):
    """One exact streamed line in a frozen, schema-validated JSONL file."""
    file: FileRef
    schema_file: FileRef
    physical_line: int = Field(ge=1)
    line_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    line_size_bytes: int = Field(gt=0)


class ImageIdentity(Strict):
    """One complete source-page image; no interpretations."""
    physical_page: int = Field(ge=1)
    image: FileRef
    width: int = Field(gt=0)
    height: int = Field(gt=0)


class BlindDocument(Strict):
    """Neutral source identities available before candidate release."""
    assignment_id: str
    source_id: str
    authority_id: Literal['CO-COUNTY-WELD'] = 'CO-COUNTY-WELD'
    expected_pages: int = Field(gt=0)
    original: FileRef
    pages: list[ImageIdentity]

    @model_validator(mode='after')
    def complete(self) -> BlindDocument:
        """Require the precise authorized original and all ordered pages."""
        spec = (self.assignment_id, self.source_id, self.expected_pages, self.original.sha256)
        if spec not in SPECS:
            raise ValueError('Wrong assignment identity')
        if [p.physical_page for p in self.pages] != list(range(1, self.expected_pages + 1)):
            raise ValueError('Missing, duplicate or reordered page')
        return self


class SourceIdentities(Strict):
    """Only source identities and hash bindings, without prior review/candidate content."""
    schema_version: Literal[1] = 1
    packet_id: Literal['ebenezer-next-weld-2026-09-12'] = 'ebenezer-next-weld-2026-09-12'
    status: Literal['PREPARED_NOT_DISPATCHED'] = 'PREPARED_NOT_DISPATCHED'
    documents: list[BlindDocument] = Field(min_length=3, max_length=3)
    authority_limit: Literal['Collection identity only; no legal-authority conclusion.'] = (
        'Collection identity only; no legal-authority conclusion.'
    )
    legal_currentness: Literal['not_verified'] = 'not_verified'

    @model_validator(mode='after')
    def order(self) -> SourceIdentities:
        """Keep exactly the assigned order."""
        if [d.assignment_id for d in self.documents] != [s[0] for s in SPECS]:
            raise ValueError('Wrong queue order')
        return self


class NativePage(Strict):
    """Full unchanged native page bytes, not an accuracy certification."""
    schema_version: Literal[1] = 1
    source_id: str
    source_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    physical_page: int = Field(ge=1)
    expected_pages: int = Field(ge=1)
    source_image_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    extracted_at: AwareDatetime
    engine: Literal['PyMuPDF'] = 'PyMuPDF'
    engine_version: Literal['1.28.2'] = '1.28.2'
    method: Literal['Page.get_text("text", sort=False, flags=195)'] = (
        'Page.get_text("text", sort=False, flags=195)'
    )
    text: str
    text_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    text_size_bytes: int = Field(gt=0)
    status: Literal['machine_native_text_unreviewed'] = 'machine_native_text_unreviewed'
    changes: Literal['none'] = 'none'

    @model_validator(mode='after')
    def content(self) -> NativePage:
        """Bind text bytes and the complete, nonblank page."""
        b = self.text.encode('utf-8')
        if not b.strip() or self.physical_page > self.expected_pages:
            raise ValueError('Blank or invalid native page')
        if (len(b), hashlib.sha256(b).hexdigest()) != (self.text_size_bytes, self.text_sha256):
            raise ValueError('Native text hash/length differs')
        return self


class CandidatePage(Strict):
    """Exact page evidence and complete candidate byte slice."""
    physical_page: int = Field(ge=1)
    evidence: FileRef
    text_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    text_size_bytes: int = Field(gt=0)
    start_byte: int = Field(ge=0)
    end_byte_exclusive: int = Field(gt=0)

    @model_validator(mode='after')
    def span(self) -> CandidatePage:
        """Reject truncation and impossible spans."""
        if self.end_byte_exclusive - self.start_byte != self.text_size_bytes:
            raise ValueError('Wrong candidate span length')
        return self


class Custody(Strict):
    """Retained intake history, withheld from the source-first reviewer."""
    raw_copy: Copy
    manual_record: JSONLRow
    provenance_record: JSONLRow
    preserved_acquisition_method: Literal['received_review_package', 'manual_official_download']
    preserved_repository_received_at: AwareDatetime
    original_acquisition_replayed_by_packet: Literal[False] = False
    interpretation: Literal['Frozen intake/provenance claims retain their original qualifications.'] = (
        'Frozen intake/provenance claims retain their original qualifications.'
    )


class Document(Strict):
    """Sealed complete candidate/custody binding for one neutral source identity."""
    identity: BlindDocument
    custody: Custody
    candidate: FileRef
    candidate_pages: list[CandidatePage]
    native_evidence_schema: FileRef
    candidate_status: Literal['machine_native_text_unreviewed'] = 'machine_native_text_unreviewed'
    candidate_changes: Literal['none'] = 'none'
    candidate_packaging: Literal['UTF-8 page markers outside unchanged native bytes'] = (
        'UTF-8 page markers outside unchanged native bytes'
    )
    render_method: Literal['pdftoppm -r 300 -png original.pdf page'] = (
        'pdftoppm -r 300 -png original.pdf page'
    )
    render_version: Literal['26.05.0'] = '26.05.0'
    render_scope: Literal['Entire physical page; no crop, annotation, or rescaling'] = (
        'Entire physical page; no crop, annotation, or rescaling'
    )
    legal_currentness: Literal['not_verified'] = 'not_verified'

    @model_validator(mode='after')
    def pages(self) -> Document:
        """Keep every page and raw-source hash consistently bound."""
        if [p.physical_page for p in self.candidate_pages] != list(
            range(1, self.identity.expected_pages + 1)
        ):
            raise ValueError('Candidate page set differs')
        if self.custody.raw_copy.frozen != self.identity.original:
            raise ValueError('Custody does not bind packet PDF')
        return self


class Manifest(Strict):
    """Immutable prepared packet, never a dispatch receipt or legal certification."""
    schema_version: Literal[1] = 1
    packet_id: Literal['ebenezer-next-weld-2026-09-12'] = 'ebenezer-next-weld-2026-09-12'
    prepared_at: AwareDatetime
    status: Literal['PREPARED_NOT_DISPATCHED'] = 'PREPARED_NOT_DISPATCHED'
    start_no_document_at_or_after: Literal['2026-09-13T01:25:00Z']
    hard_stop: Literal['2026-09-13T01:55:00Z']
    stop_after: Literal['EB-PDF-020'] = 'EB-PDF-020'
    dispatch_at: None = None
    task_id: Literal['01a08848-5f8e-7c51-9b66-fd82eff860fe']
    source_only_identities: FileRef
    source_only_schema: FileRef
    instructions: FileRef
    documents: list[Document] = Field(min_length=3, max_length=3)
    custody_copies: list[Copy]
    limitations: list[str] = Field(min_length=4)
    legal_currentness: Literal['not_verified'] = 'not_verified'

    @model_validator(mode='after')
    def order(self) -> Manifest:
        """Enforce the finite declared order."""
        if [d.identity.assignment_id for d in self.documents] != [s[0] for s in SPECS]:
            raise ValueError('Unexpected assignment order')
        return self


class Inventory(Strict):
    """Closed immutable file set; self and schema are explicit exclusions."""
    schema_version: Literal[1] = 1
    files: list[FileRef]
    exclusions: Literal['INVENTORY.json and INVENTORY.schema.json only'] = (
        'INVENTORY.json and INVENTORY.schema.json only'
    )


class CheckReceipt(Strict):
    """Measured preparation and render QA, distinct from source transcription review."""
    prepared_at: AwareDatetime
    status: Literal['PREPARED_NOT_DISPATCHED'] = 'PREPARED_NOT_DISPATCHED'
    manifest: FileRef
    prior_activation: Copy
    documents: Literal[3] = 3
    physical_pages: Literal[13] = 13
    native_pages: Literal[13] = 13
    candidate_packages: Literal[3] = 3
    native_bytes: int = Field(gt=0)
    render_qa_viewed: list[str]
    render_qa_scope: Literal['Complete PNG framing/legibility only; not a fresh text accuracy review.'] = (
        'Complete PNG framing/legibility only; not a fresh text accuracy review.'
    )
    original_bytes_changed: Literal[False] = False
    new_source_requests: Literal[0] = 0
    dispatched: Literal[False] = False
    source_accuracy_certified: Literal[False] = False
    legal_currentness: Literal['not_verified'] = 'not_verified'


def ordinary(path: Path) -> Path:
    """Require an ordinary file without symlink ancestors."""
    if path.is_symlink() or any(p.is_symlink() for p in path.parents) or not path.is_file():
        raise ValueError(f'Not an ordinary file: {path}')
    return path


def digest(path: Path) -> str:
    """Hash bytes with a bounded-memory stream."""
    with ordinary(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def ref(base: Path, path: Path) -> FileRef:
    """Construct a measured confined reference."""
    return FileRef(path=str(path.relative_to(base)), sha256=digest(path),
                   size_bytes=path.stat().st_size)


def verify_ref(base: Path, item: FileRef) -> Path:
    """Verify exact ordinary bytes before opening the artifact."""
    path = ordinary(base / item.path)
    if ref(base, path) != item:
        raise ValueError(f'File hash/size changed: {item.path}')
    return path


def schema_model(base: Path, path: str, schema: str, model: type[Strict]) -> Strict:
    """Validate a strict model against its retained generated schema."""
    body = ordinary(base / path).read_bytes()
    supplied = json.loads(ordinary(base / schema).read_bytes())
    if supplied != model.model_json_schema():
        raise ValueError(f'Schema differs: {schema}')
    result = model.model_validate_json(body)
    jsonschema.Draft202012Validator(supplied).validate(json.loads(body))
    return result


def row(base: Path, item: JSONLRow) -> dict:
    """Stream the frozen JSONL and validate all rows, retaining only the selected row."""
    path = verify_ref(base, item.file)
    schema = json.loads(verify_ref(base, item.schema_file).read_bytes())
    validator = jsonschema.Draft202012Validator(schema)
    selected = None
    with path.open('rb') as stream:
        for number, line in enumerate(stream, 1):
            obj = json.loads(line)
            validator.validate(obj)
            if number == item.physical_line:
                if (hashlib.sha256(line).hexdigest(), len(line)) != (
                    item.line_sha256, item.line_size_bytes
                ):
                    raise ValueError('Selected custody line changed')
                selected = obj
    if selected is None:
        raise ValueError('Selected custody line absent')
    return selected


def verify(base: Path, rerender: bool = False, poppler: str = 'pdftoppm') -> dict:
    """Check the closed package, complete native bytes, custody and optional PNG rerender."""
    if base.is_symlink() or any(p.is_symlink() for p in base.parents):
        raise ValueError('Symlink package root')
    base = base.resolve(strict=True)
    if any(p.is_symlink() for p in base.rglob('*')):
        raise ValueError('Symlink packet entry')
    inventory = schema_model(base, 'INVENTORY.json', 'INVENTORY.schema.json', Inventory)
    expected = {item.path for item in inventory.files}
    if len(expected) != len(inventory.files):
        raise ValueError('Duplicate inventory reference')
    actual = {str(p.relative_to(base)) for p in base.rglob('*') if p.is_file()}
    if actual != expected | {'INVENTORY.json', 'INVENTORY.schema.json'}:
        raise ValueError('Unexpected or missing packet files')
    expected_dirs = {str(parent) for name in actual for parent in Path(name).parents
                     if str(parent) != '.'}
    actual_dirs = {str(p.relative_to(base)) for p in base.rglob('*') if p.is_dir()}
    if actual_dirs != expected_dirs:
        raise ValueError('Unexpected empty packet directory')
    for item in inventory.files:
        verify_ref(base, item)
    manifest = schema_model(base, 'manifest.json', 'manifest.schema.json', Manifest)
    ids = schema_model(base, manifest.source_only_identities.path,
                       manifest.source_only_schema.path, SourceIdentities)
    if ids.documents != [d.identity for d in manifest.documents]:
        raise ValueError('Neutral source identities differ')
    for copy in manifest.custody_copies:
        verify_ref(base, copy.frozen)
    native_bytes = 0
    if pymupdf.VersionBind != '1.28.2':
        raise ValueError('Native engine version differs from the extraction receipt')
    for doc in manifest.documents:
        identity = doc.identity
        original = verify_ref(base, identity.original)
        raw = row(base, doc.custody.manual_record)
        provenance = row(base, doc.custody.provenance_record)
        if (raw['record_id'], raw['sha256'], raw['size_bytes'], raw['layer_id']) != (
            identity.source_id, identity.original.sha256, identity.original.size_bytes,
            '08_County_Authorities'
        ):
            raise ValueError('Intake source binding differs')
        if raw['acquisition_method'] != doc.custody.preserved_acquisition_method:
            raise ValueError('Acquisition method was relabeled')
        if raw['received_at'] != doc.custody.preserved_repository_received_at.isoformat().replace('+00:00', 'Z'):
            raise ValueError('Repository receipt time changed')
        if (provenance['source_id'], provenance['authority_id'], provenance['intake_id'],
            provenance['canonical_original']['sha256'],
            provenance['canonical_original']['size_bytes'],
            provenance['repository_received_at']) != (
                identity.source_id, identity.authority_id, raw['intake_id'],
                identity.original.sha256, identity.original.size_bytes, raw['received_at']
            ):
            raise ValueError('Provenance source/custody differs')
        candidate = verify_ref(base, doc.candidate).read_bytes()
        rebuilt = bytearray()
        with pymupdf.open(original) as pdf:
            if pdf.is_repaired or pdf.is_encrypted or len(pdf) != identity.expected_pages:
                raise ValueError('PDF structure changed')
            for image, cp in zip(identity.pages, doc.candidate_pages, strict=True):
                image_path = verify_ref(base, image.image)
                with image_path.open('rb') as stream:
                    header = stream.read(24)
                if header[:8] != b'\x89PNG\r\n\x1a\n' or struct.unpack('>II', header[16:24]) != (
                    image.width, image.height
                ):
                    raise ValueError('PNG structure changed')
                ev = schema_model(base, cp.evidence.path, doc.native_evidence_schema.path, NativePage)
                number = image.physical_page
                native = pdf[number - 1].get_text('text', sort=False, flags=195).encode('utf-8')
                native_bytes += len(native)
                if (ev.source_id, ev.source_sha256, ev.physical_page, ev.expected_pages,
                    ev.source_image_sha256) != (identity.source_id, identity.original.sha256,
                                               number, len(pdf), image.image.sha256):
                    raise ValueError('Native source/image binding differs')
                if native != ev.text.encode('utf-8') or hashlib.sha256(native).hexdigest() != cp.text_sha256:
                    raise ValueError('Native text reproduction differs')
                rebuilt.extend(f'===== PHYSICAL PDF PAGE {number} OF {len(pdf)} (PACKAGING MARKER) =====\n'.encode())
                if len(rebuilt) != cp.start_byte:
                    raise ValueError('Candidate start differs')
                rebuilt.extend(native)
                if len(rebuilt) != cp.end_byte_exclusive:
                    raise ValueError('Candidate end differs')
                rebuilt.extend(f'\n===== END PHYSICAL PDF PAGE {number} (PACKAGING MARKER) =====\n\n'.encode())
        if bytes(rebuilt) != candidate:
            raise ValueError('Candidate truncation, correction or repackaging')
        if rerender:
            with tempfile.TemporaryDirectory(prefix='weld-review-verify-') as temporary:
                target = Path(temporary)
                subprocess.run([poppler, '-r', '300', '-png', str(original), str(target / 'page')],
                               check=True, capture_output=True)
                for image in identity.pages:
                    if digest(target / f'page-{image.physical_page}.png') != image.image.sha256:
                        raise ValueError('Full-page render does not reproduce')
    check = schema_model(base, '04-verification/PREPARATION_CHECK.json',
                         '04-verification/PREPARATION_CHECK.schema.json', CheckReceipt)
    verify_ref(base, check.manifest)
    verify_ref(base, check.prior_activation.frozen)
    if (base / 'MANIFEST_SHA256.txt').read_text() != digest(base / 'manifest.json') + '\n':
        raise ValueError('Neutral manifest hash differs')
    if check.native_bytes != native_bytes:
        raise ValueError('Wrong measured native-byte count')
    expected_pages = [f'{d.identity.source_id}:page-{p.physical_page:04d}'
                      for d in manifest.documents for p in d.identity.pages]
    if check.render_qa_viewed != expected_pages:
        raise ValueError('Render QA page coverage missing')
    return {'status': 'PREPARED_NOT_DISPATCHED', 'documents': 3, 'physical_pages': 13,
            'native_bytes': native_bytes, 'files': len(actual), 'rerendered': rerender,
            'legal_currentness': 'not_verified'}


def main() -> None:
    """Validate the current portable directory without changing its contents."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rerender', action='store_true')
    parser.add_argument('--poppler', default=shutil.which('pdftoppm') or 'pdftoppm')
    args = parser.parse_args()
    print(json.dumps(verify(Path(__file__).resolve().parents[1], args.rerender, args.poppler)))


if __name__ == '__main__':
    main()
