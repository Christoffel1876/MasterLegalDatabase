"""Validate the EB015–017 packet locally; no network or source modifications."""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import struct
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Annotated, Literal

import jsonschema
import pymupdf
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

SHA = Annotated[str, Field(pattern=r'^[a-f0-9]{64}$')]
SPECS = [
    ('EB-PDF-015', 'greeley-building-fees-sd008-06', 1,
     'fa8a90dae00525c2dcb62ef4d69aeb84b7032a0fd2dc64f45c1685981e9becd4'),
    ('EB-PDF-016', 'greeley-development-impact-fee-memo-sd008-07', 3,
     '9effbd15196898c16105913ee21032db52ad1e259f4f9def0586804726f78709'),
    ('EB-PDF-017', 'greeley-water-sewer-proposed-pif-notice-sd008-08', 2,
     'edfd4eecc57657bec922b8e0e63597fbf2fc957936d8f26a1a457b195dac145c'),
]
SID = Literal['greeley-building-fees-sd008-06',
              'greeley-development-impact-fee-memo-sd008-07',
              'greeley-water-sewer-proposed-pif-notice-sd008-08']
AID = Literal['EB-PDF-015', 'EB-PDF-016', 'EB-PDF-017']


class Strict(BaseModel):
    """Reject extra fields and silent scalar conversions."""
    model_config = ConfigDict(extra='forbid', strict=True)


class FileRef(Strict):
    """Exact file reference; its scope is explicit in the containing field."""
    path: str = Field(min_length=1)
    sha256: SHA
    size_bytes: int = Field(gt=0)


class PacketFile(FileRef):
    """Require a confined relative packet path."""
    @model_validator(mode='after')
    def confined(self) -> PacketFile:
        """Reject traversal, absolute references and empty paths."""
        path = Path(self.path)
        if path.is_absolute() or '..' in path.parts or self.path == '.':
            raise ValueError('Unconfined packet path')
        return self


class NativePage(Strict):
    """An unchanged native text page bound to its source and rendered image."""
    schema_version: Literal[1] = 1
    source_id: SID
    source_sha256: SHA
    physical_page: int = Field(ge=1, le=8)
    expected_pages: int = Field(ge=1, le=8)
    source_image_sha256: SHA
    extracted_at: AwareDatetime
    text: str = Field(min_length=1)
    text_sha256: SHA
    text_size_bytes: int = Field(gt=0)
    meaningful_native_text_preflight: Literal[True] = True
    changes: Literal['none'] = 'none'
    method_family: Literal['native'] = 'native'
    engine: Literal['PyMuPDF'] = 'PyMuPDF'
    engine_version: Literal['1.28.2'] = '1.28.2'
    method: Literal['Page.get_text("text", sort=False, flags=195)'] = (
        'Page.get_text("text", sort=False, flags=195)'
    )
    sort: Literal[False] = False
    flags: Literal[195] = 195
    status: Literal['machine_native_text_unreviewed'] = 'machine_native_text_unreviewed'

    @model_validator(mode='after')
    def integrity(self) -> NativePage:
        """Bind every text byte and disallow blank native candidates."""
        raw = self.text.encode('utf-8')
        if self.physical_page > self.expected_pages or not self.text.strip():
            raise ValueError('Invalid or blank native page')
        if digest(raw) != self.text_sha256 or len(raw) != self.text_size_bytes:
            raise ValueError('Changed native text')
        return self


class Page(Strict):
    """One complete physical page and exact candidate byte slice."""
    physical_page: int = Field(ge=1, le=8)
    image: PacketFile
    image_width: int = Field(gt=0)
    image_height: int = Field(gt=0)
    evidence: PacketFile
    text_sha256: SHA
    text_size_bytes: int = Field(gt=0)
    candidate_text_offset_bytes: int = Field(ge=0)
    candidate_text_end_byte_exclusive: int = Field(gt=0)

    @model_validator(mode='after')
    def offsets(self) -> Page:
        """Require the byte slice to fit exactly its unchanged text."""
        if self.candidate_text_end_byte_exclusive - self.candidate_text_offset_bytes != (
            self.text_size_bytes
        ):
            raise ValueError('Wrong candidate slice length')
        return self


class CustodyCopy(Strict):
    """A frozen exact copy resolves a potentially mutable original path."""
    original: FileRef
    frozen: PacketFile
    role: str = Field(min_length=1)
    captured_at: AwareDatetime

    @model_validator(mode='after')
    def equality(self) -> CustodyCopy:
        """Require the same byte identity on both sides of the custody copy."""
        if (self.original.sha256, self.original.size_bytes) != (
            self.frozen.sha256, self.frozen.size_bytes
        ):
            raise ValueError('Custody copy mismatch')
        return self


class Provenance(Strict):
    """Frozen local custody and retained referral evidence; no new HTTP retrieval."""
    canonical_raw_pdf: FileRef
    received_original: FileRef
    original_acquisition_time: None = None
    upstream_http_acquisition_independently_verified_in_this_preparation: Literal[False] = False
    actual_repository_received_at: AwareDatetime
    intake_record_id: str
    intake_status: Literal['archived_pending_pipeline'] = 'archived_pending_pipeline'
    acquisition_method: Literal['received_review_package'] = 'received_review_package'
    frozen_raw_manifest: PacketFile
    raw_manifest_line_number: int = Field(ge=1)
    raw_manifest_line_sha256: SHA
    raw_manifest_line_size_bytes: int = Field(gt=0)
    frozen_intake_receipt: PacketFile
    frozen_source_provenance: PacketFile
    provenance_line_number: int = Field(ge=1)
    provenance_line_sha256: SHA
    provenance_line_size_bytes: int = Field(gt=0)
    reported_requested_url: str = Field(pattern=r'^https://cogy-p-001\.sitecorecontenthub\.cloud/')
    reported_final_url: str = Field(pattern=r'^https://cogy-p-001\.sitecorecontenthub\.cloud/')
    reported_acquisition_at: AwareDatetime
    reported_method: Literal['mac_curl'] = 'mac_curl'
    acquisition_evidence_label: Literal['retained_curl_body_and_headers'] = 'retained_curl_body_and_headers'
    canonical_official_source_url: None = None
    null_official_source_url_reason: Literal['direct_host_not_in_existing_allowlist'] = 'direct_host_not_in_existing_allowlist'
    official_referral_url: str = Field(pattern=r'^https://greeleyco\.gov/')
    reported_referral_label: str
    frozen_referral_html: PacketFile
    requested_url_found_in_saved_referral_anchor: Literal[True] = True
    frozen_derived_response_headers: PacketFile
    original_response_header_identity: FileRef
    header_transformation: Literal['Only Set-Cookie header lines omitted; other bytes unchanged'] = 'Only Set-Cookie header lines omitted; other bytes unchanged'
    full_response_headers_in_packet: Literal[False] = False
    source_role_claim: Literal['municipal_building_fee_schedule',
                               'fee_adjustment_memorandum_with_schedules',
                               'proposed_utility_fee_notice_with_schedule']
    role_basis: Literal['supplied intake label; no adopted/current legal effect established'] = 'supplied intake label; no adopted/current legal effect established'
    caveats: list[str]


class Document(Strict):
    """One finite review assignment with a complete page set."""
    queue_order: int = Field(ge=1, le=3)
    assignment_id: AID
    source_id: SID
    authority_id: Literal['CO-MUNICIPAL-GREELEY'] = 'CO-MUNICIPAL-GREELEY'
    authority_basis: Literal['collection context only; not a legal-authority finding'] = (
        'collection context only; not a legal-authority finding'
    )
    expected_pages: int = Field(ge=1, le=8)
    original: PacketFile
    provenance: Provenance
    rendering_engine: Literal['Poppler pdftoppm'] = 'Poppler pdftoppm'
    rendering_version: Literal['26.05.0'] = '26.05.0'
    rendering_command: Literal['pdftoppm -r 300 -png original.pdf page'] = (
        'pdftoppm -r 300 -png original.pdf page'
    )
    rendering_dpi: Literal[300] = 300
    rendering_scope: Literal['entire physical pages; no crop, annotation or rescaling'] = (
        'entire physical pages; no crop, annotation or rescaling'
    )
    candidate: PacketFile
    candidate_status: Literal['machine_native_text_unreviewed'] = 'machine_native_text_unreviewed'
    candidate_changes: Literal['none'] = 'none'
    candidate_packaging: Literal['UTF-8 page markers outside unchanged native byte slices'] = (
        'UTF-8 page markers outside unchanged native byte slices'
    )
    page_evidence_schema: PacketFile
    pages: list[Page]
    legal_currentness: Literal['not_verified'] = 'not_verified'
    legal_review: Literal['pending'] = 'pending'

    @model_validator(mode='after')
    def complete(self) -> Document:
        """Enforce the assigned source, hash and complete ordered page count."""
        if (self.assignment_id, self.source_id, self.expected_pages, self.original.sha256) != (
            SPECS[self.queue_order - 1]
        ):
            raise ValueError('Wrong assignment identity')
        if [p.physical_page for p in self.pages] != list(range(1, self.expected_pages + 1)):
            raise ValueError('Missing or repeated page')
        if self.original.sha256 != self.provenance.canonical_raw_pdf.sha256:
            raise ValueError('Wrong raw source binding')
        return self


class Manifest(Strict):
    """An immutable, prepared but unsent three-document queue."""
    schema_version: Literal[1] = 1
    packet_id: Literal['grok-pdf-review-2026-09-11-batch-5'] = (
        'grok-pdf-review-2026-09-11-batch-5'
    )
    prepared_at: AwareDatetime
    status: Literal['PREPARED_NOT_DISPATCHED'] = 'PREPARED_NOT_DISPATCHED'
    purpose: Literal['independent_pdf_transcription_review'] = 'independent_pdf_transcription_review'
    start_no_document_at_or_after: Literal['2026-09-11T20:50:00Z'] = '2026-09-11T20:50:00Z'
    finish_by: Literal['2026-09-11T21:20:00Z'] = '2026-09-11T21:20:00Z'
    stop_after: Literal['EB-PDF-017'] = 'EB-PDF-017'
    independence: Literal['procedural source-first pass; per-document frozen receipt before candidate'] = (
        'procedural source-first pass; per-document frozen receipt before candidate'
    )
    legal_currentness: Literal['not_verified'] = 'not_verified'
    documents: list[Document] = Field(min_length=3, max_length=3)
    custody_copies: list[CustodyCopy]
    supporting_payloads: list[PacketFile]
    assignment: CustodyCopy
    limitations: list[str]

    @model_validator(mode='after')
    def ordered(self) -> Manifest:
        """Allow only EB015 then EB016 then EB017, with no extra assignment."""
        if [d.queue_order for d in self.documents] != [1, 2, 3]:
            raise ValueError('Wrong queue')
        return self


def digest(body: bytes) -> str:
    """Hash exact bytes."""
    return hashlib.sha256(body).hexdigest()


def read(path: Path) -> bytes:
    """Reject symlink inputs; packet verification never follows untrusted file links."""
    if path.is_symlink() or any(p.is_symlink() for p in path.parents):
        raise ValueError('Symlink reference')
    return path.read_bytes()


def encoded(model: BaseModel) -> bytes:
    """Validate records before serializing them for storage."""
    body = (model.model_dump_json(indent=2) + '\n').encode()
    type(model).model_validate_json(body)
    return body


def verify(base: Path, rerender: bool = False) -> dict[str, int]:
    """Recheck every local payload, all candidate bytes, custody and optional renders."""
    raw = read(base / 'manifest.json')
    m = Manifest.model_validate_json(raw)
    schema = json.loads(read(base / 'manifest.schema.json'))
    if schema != Manifest.model_json_schema():
        raise ValueError('Manifest schema does not match its model')
    jsonschema.Draft202012Validator(schema).validate(json.loads(raw))
    raw_ref = m.documents[0].provenance.frozen_raw_manifest
    raw_lines = read(base / raw_ref.path).splitlines(keepends=True)
    if len(raw_lines) != 38:
        raise ValueError('Frozen raw manifest must contain 38 records')
    manual_schema = json.loads(read(base / '03-custody/manual-record.schema.json'))
    for line in raw_lines:
        jsonschema.Draft202012Validator(manual_schema).validate(json.loads(line))
    receipt_schema = json.loads(read(base / '03-custody/intake-receipt.schema.json'))
    jsonschema.Draft202012Validator(receipt_schema).validate(
        json.loads(read(base / '03-custody/intake-receipt.json')))
    prov_schema = json.loads(read(base / '03-custody/source-provenance.schema.json'))
    for line in read(base / '03-custody/source-provenance.jsonl').splitlines():
        jsonschema.Draft202012Validator(prov_schema).validate(json.loads(line))
    checks = 0

    def payload(f: PacketFile) -> bytes:
        nonlocal checks
        b = read(base / f.path)
        if digest(b) != f.sha256 or len(b) != f.size_bytes:
            raise ValueError(f'Changed packet payload {f.path}')
        checks += 1
        return b

    for f in m.supporting_payloads:
        payload(f)
    for copy in m.custody_copies + [m.assignment]:
        payload(copy.frozen)
    for d in m.documents:
        source = payload(d.original)
        candidate = payload(d.candidate)
        es = json.loads(payload(d.page_evidence_schema))
        if es != NativePage.model_json_schema():
            raise ValueError('Native evidence schema changed')
        pr = d.provenance
        lines = payload(pr.frozen_raw_manifest).splitlines(keepends=True)
        line = lines[pr.raw_manifest_line_number - 1]
        if digest(line) != pr.raw_manifest_line_sha256 or len(line) != pr.raw_manifest_line_size_bytes:
            raise ValueError('Raw manifest line differs')
        ir = json.loads(line)
        if ir['record_id'] != d.source_id or ir['sha256'] != d.original.sha256:
            raise ValueError('Wrong intake record')
        if ir['intake_id'] != pr.intake_record_id or ir['size_bytes'] != len(source):
            raise ValueError('Wrong intake identity')
        plines = payload(pr.frozen_source_provenance).splitlines(keepends=True)
        pline = plines[pr.provenance_line_number - 1]
        if digest(pline) != pr.provenance_line_sha256 or len(pline) != pr.provenance_line_size_bytes:
            raise ValueError('Provenance line differs')
        pro = json.loads(pline)
        if (pro['source_id'], pro['intake_id'], pro['canonical_original']['sha256'],
            pro['canonical_original']['size_bytes'], pro['repository_received_at']) != (
            d.source_id, ir['intake_id'], ir['sha256'], ir['size_bytes'], ir['received_at']
        ):
            raise ValueError('Provenance/intake discrepancy')
        if pro['reported_requested_url'] != pr.reported_requested_url or pro['reported_final_url'] != pr.reported_final_url:
            raise ValueError('Reported URL discrepancy')
        from html.parser import HTMLParser
        class Anchors(HTMLParser):
            def __init__(self):
                super().__init__(convert_charrefs=True)
                self.hrefs = []
            def handle_starttag(self, tag, attrs):
                if tag.lower() == 'a':
                    self.hrefs.extend(v for k, v in attrs if k.lower() == 'href' and v)
        parser = Anchors()
        parser.feed(payload(pr.frozen_referral_html).decode('utf-8'))
        if pr.reported_requested_url not in parser.hrefs:
            raise ValueError('Saved official referral anchor missing')
        header = payload(pr.frozen_derived_response_headers)
        if b'Set-Cookie:' in header or b'set-cookie:' in header:
            raise ValueError('Derived headers unexpectedly contain cookies')
        if pro['http_evidence']['derived_header_without_cookies']['sha256'] != digest(header):
            raise ValueError('Derived response header binding differs')
        receipt = json.loads(payload(pr.frozen_intake_receipt))
        if receipt['raw_manifest_after']['sha256'] != pr.frozen_raw_manifest.sha256:
            raise ValueError('Receipt does not bind frozen manifest')
        rebuild = bytearray()
        with pymupdf.open(stream=source, filetype='pdf') as pdf:
            if pdf.is_repaired or pdf.is_encrypted or len(pdf) != d.expected_pages:
                raise ValueError('PDF structure changed')
            for pg in d.pages:
                image = payload(pg.image)
                if image[:8] != b'\x89PNG\r\n\x1a\n':
                    raise ValueError('Not PNG')
                if struct.unpack('>II', image[16:24]) != (pg.image_width, pg.image_height):
                    raise ValueError('Image dimensions changed')
                ebody = payload(pg.evidence)
                e = NativePage.model_validate_json(ebody)
                jsonschema.Draft202012Validator(es).validate(json.loads(ebody))
                text = pdf[pg.physical_page - 1].get_text('text', sort=False, flags=195).encode()
                if (e.source_id, e.source_sha256, e.physical_page, e.expected_pages) != (
                    d.source_id, d.original.sha256, pg.physical_page, d.expected_pages
                ) or e.source_image_sha256 != pg.image.sha256:
                    raise ValueError('Page/source/image mismatch')
                if text != e.text.encode() or digest(text) != pg.text_sha256:
                    raise ValueError('Fresh native extraction differs')
                i = pg.physical_page
                rebuild.extend(f'===== PHYSICAL PDF PAGE {i} OF {d.expected_pages} '
                               '(PACKAGING MARKER) =====\n'.encode())
                if len(rebuild) != pg.candidate_text_offset_bytes:
                    raise ValueError('Wrong starting offset')
                rebuild.extend(text)
                if len(rebuild) != pg.candidate_text_end_byte_exclusive:
                    raise ValueError('Wrong ending offset')
                if candidate[pg.candidate_text_offset_bytes:pg.candidate_text_end_byte_exclusive] != text:
                    raise ValueError('Candidate slice differs')
                rebuild.extend(f'\n===== END PHYSICAL PDF PAGE {i} (PACKAGING MARKER) =====\n\n'.encode())
        if bytes(rebuild) != candidate:
            raise ValueError('Full candidate packaging differs')
        if rerender:
            with tempfile.TemporaryDirectory(
                prefix='geode-eb015-017-verify-', dir=Path(tempfile.gettempdir()).resolve()
            ) as temp:
                output = Path(temp) / 'page'
                subprocess.run(['pdftoppm', '-r', '300', '-png', str(base / d.original.path),
                                str(output)], check=True, capture_output=True)
                for pg in d.pages:
                    if read(Path(temp) / f'page-{pg.physical_page}.png') != payload(pg.image):
                        raise ValueError('Fresh full-page rendering differs')
    return {'documents': 3, 'physical_pages': 6, 'payload_reference_checks': checks}


def main() -> None:
    """Run packet verification from its own portable root."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rerender', action='store_true')
    args = parser.parse_args()
    result = verify(Path(__file__).resolve().parents[1], args.rerender)
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    logging.info('Verified %s', result)


if __name__ == '__main__':
    main()
