"""Validate portable EB013 draft-source review evidence without writes or network."""
from __future__ import annotations
import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Annotated, Literal
import pymupdf
from jsonschema import Draft202012Validator
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

SID = 'fort-collins-wildfire-code-sd005-05'
SHA = Annotated[str, Field(pattern=r'^[a-f0-9]{64}$')]

class Strict(BaseModel):
    """Reject unmodeled evidence fields."""
    model_config = ConfigDict(extra='forbid')

class Asset(Strict):
    """A confined package-relative file binding."""
    path: str
    sha256: SHA
    size_bytes: int = Field(gt=0)
    @model_validator(mode='after')
    def confined(self) -> Asset:
        path = PurePosixPath(self.path)
        if path.is_absolute() or '..' in path.parts or '\\' in self.path or ':' in self.path:
            raise ValueError('unconfined package path')
        if path.as_posix() != self.path or self.path == '.':
            raise ValueError('noncanonical package path')
        return self

class CopyBinding(Strict):
    """The original location is historical provenance; validation uses the local copy."""
    historical_path: str
    local: Asset

class Span(Strict):
    """Exact page-native UTF-8 bytes, with no inserted annotation characters."""
    start_byte: int = Field(ge=0)
    end_byte_exclusive: int = Field(gt=0)
    text: str
    sha256: SHA
    @model_validator(mode='after')
    def exact(self) -> Span:
        data = self.text.encode('utf-8')
        if len(data) != self.end_byte_exclusive - self.start_byte or digest(data) != self.sha256:
            raise ValueError('span length or hash differs')
        return self

class Chunk(Strict):
    """One interval in an exhaustive native page partition."""
    id: str
    span: Span

class Observation(Strict):
    """Preserved independent source finding; never an enacted legal rule."""
    id: str
    physical_page: int = Field(ge=1, le=8)
    audit: Asset
    audit_observation_id: str
    spans: list[Span] = Field(min_length=1)
    finding: str
    qualifications: list[str]
    review_mode: Literal['candidate_aware_not_blind'] = 'candidate_aware_not_blind'
    legal_effect: Literal['not_determined'] = 'not_determined'

class Annotation(Strict):
    """A visual or contextual annotation anchored outside the native text."""
    id: str
    observation_id: str
    physical_page: int = Field(ge=1, le=8)
    category: Literal[
        'strikethrough', 'yellow_highlight', 'green_blank', 'blank_field', 'draft_label',
        'source_anomaly', 'date_wording', 'reading_order', 'outline', 'source_association',
        'lexical_or_condition', 'typography', 'page_continuation',
    ]
    bound_scope: Literal['marked_text', 'containing_source_region', 'context']
    spans: list[Span] = Field(min_length=1)
    explanation: str
    changes_native_text: Literal[False] = False
    establishes_legal_effect: Literal[False] = False

class Page(Strict):
    """A complete native page plus separate display-order references."""
    physical_page: int = Field(ge=1, le=8)
    image: Asset
    native_receipt: Asset
    native_text: str
    native_sha256: SHA
    native_bytes: int = Field(gt=0)
    candidate_start_byte: int = Field(ge=0)
    candidate_end_byte_exclusive: int = Field(gt=0)
    chunks_in_native_order: list[Chunk]
    visual_reading_order_ids: list[str]
    source_review_audit: Asset
    full_image_review_recorded: Literal[True] = True
    @model_validator(mode='after')
    def partition(self) -> Page:
        raw = self.native_text.encode('utf-8')
        if len(raw) != self.native_bytes or digest(raw) != self.native_sha256:
            raise ValueError('native page hash or size differs')
        if self.candidate_end_byte_exclusive - self.candidate_start_byte != len(raw):
            raise ValueError('candidate interval size differs')
        cursor = 0
        ids = []
        for chunk in self.chunks_in_native_order:
            if chunk.span.start_byte != cursor:
                raise ValueError('native partition gap or overlap')
            validate_span(raw, chunk.span)
            cursor = chunk.span.end_byte_exclusive
            ids.append(chunk.id)
        if cursor != len(raw) or len(ids) != len(set(ids)):
            raise ValueError('incomplete or duplicate native partition')
        if sorted(ids) != sorted(self.visual_reading_order_ids):
            raise ValueError('display references lose or duplicate native chunks')
        return self

class IntakeRecord(Strict):
    """Original manual-intake record schema, retained without repo-module dependencies."""
    intake_id: str
    record_id: str
    layer_id: str
    official_source_name: str
    official_source_url: str | None
    acquisition_method: str
    received_from: str
    reviewer_name: str
    reviewer_email: str | None
    custody_note: str
    original_filename: str
    archive_path: str
    sha256: SHA
    size_bytes: int = Field(gt=0)
    source_format: str
    received_at: AwareDatetime
    status: str
    blocked_queue_match: bool
    boundary: str

class Custody(Strict):
    """Frozen historical custody, separate from unverified upstream acquisition claims."""
    frozen_raw_manifest: Asset
    raw_manifest_line_number: Literal[17] = 17
    raw_manifest_line_sha256: SHA
    raw_manifest_line_bytes: int = Field(gt=0)
    selected_intake_record: IntakeRecord
    frozen_intake_receipt: Asset
    frozen_source_provenance: Asset
    provenance_line_number: Literal[5] = 5
    provenance_line_sha256: SHA
    provenance_line_bytes: int = Field(gt=0)
    source_original_acquisition_time: None = None
    upstream_http_acquisition_verified: Literal[False] = False
    claimed_official_url: str
    claimed_final_url: str
    claimed_referral_url: str
    claimed_attempt_time: str
    claimed_status: Literal[200] = 200
    claim_qualification: str
    upstream_archive_reopened: Literal[False] = False

class Review(Strict):
    """Eight-page source-reviewed draft evidence; external review is explicitly pending."""
    schema_version: Literal[1] = 1
    assignment_id: Literal['EB-PDF-013'] = 'EB-PDF-013'
    source_id: Literal['fort-collins-wildfire-code-sd005-05'] = SID
    prepared_at: AwareDatetime
    document_status: Literal['visibly_draft_not_adopted_effect_verified']
    extraction_review_status: Literal['atlas_eight_page_source_review_complete']
    external_review_status: Literal['pending_receipt_and_reconciliation']
    external_reports_consulted: Literal[False] = False
    candidate_changes: Literal['none'] = 'none'
    candidate_status_unchanged: Literal['machine_native_text_unreviewed']
    original_intake_status: Literal['archived_pending_pipeline']
    legal_currentness: Literal['not_verified'] = 'not_verified'
    legal_effect_verified: Literal[False] = False
    semantic_or_coverage_promotion: Literal[False] = False
    original: Asset
    candidate: Asset
    original_packet_manifest: Asset
    custody: Custody
    pages: list[Page]
    observations: list[Observation]
    annotations: list[Annotation]
    limits: list[str]
    @model_validator(mode='after')
    def complete(self) -> Review:
        if [p.physical_page for p in self.pages] != list(range(1, 9)):
            raise ValueError('missing or duplicated page')
        observations = {o.id: o for o in self.observations}
        if len(observations) != 72 or len(self.observations) != 72:
            raise ValueError('independent observation count or identity differs')
        if len({a.id for a in self.annotations}) != len(self.annotations):
            raise ValueError('duplicate annotation id')
        for observation in self.observations:
            raw = self.pages[observation.physical_page - 1].native_text.encode()
            for span in observation.spans:
                validate_span(raw, span)
        for annotation in self.annotations:
            observation = observations.get(annotation.observation_id)
            if observation is None or observation.physical_page != annotation.physical_page:
                raise ValueError('annotation observation/page binding differs')
            for span in annotation.spans:
                validate_span(self.pages[annotation.physical_page - 1].native_text.encode(), span)
                if not any(s.start_byte <= span.start_byte < span.end_byte_exclusive <= s.end_byte_exclusive
                           for s in observation.spans):
                    raise ValueError('annotation extends beyond its independently reviewed region')
        return self

class Manifest(Strict):
    """All local package files, excluding this inventory's own bytes."""
    schema_version: Literal[1] = 1
    assignment_id: Literal['EB-PDF-013'] = 'EB-PDF-013'
    prepared_at: AwareDatetime
    files: list[Asset]
    copy_bindings: list[CopyBinding]
    file_count: int = Field(gt=0)
    total_listed_bytes: int = Field(gt=0)
    external_review_status: Literal['pending_receipt_and_reconciliation']
    source_status: Literal['visibly_draft']
    @model_validator(mode='after')
    def inventory(self) -> Manifest:
        if len(self.files) != self.file_count or len({x.path for x in self.files}) != self.file_count:
            raise ValueError('manifest duplicate paths or wrong count')
        if sum(x.size_bytes for x in self.files) != self.total_listed_bytes:
            raise ValueError('manifest byte total differs')
        return self

def digest(data: bytes) -> str:
    """Hash unchanged bytes."""
    return hashlib.sha256(data).hexdigest()

def validate_span(native: bytes, span: Span) -> None:
    """Reject changed text or intervals outside the native page."""
    if span.end_byte_exclusive > len(native) or native[span.start_byte:span.end_byte_exclusive] != span.text.encode():
        raise ValueError('source-native interval differs')

def read_asset(root: Path, asset: Asset) -> bytes:
    """Read only a confined ordinary package file and verify size/hash."""
    path = root / asset.path
    if any(p.is_symlink() for p in (path, *path.parents)) or not path.is_file():
        raise ValueError('evidence is not an ordinary file')
    data = path.read_bytes()
    if len(data) != asset.size_bytes or digest(data) != asset.sha256:
        raise ValueError(f'evidence size/hash mismatch: {asset.path}')
    return data

def validate_package(root: Path) -> dict[str, object]:
    """Verify portable source identity, full native inventory, annotations and custody."""
    manifest = Manifest.model_validate_json((root / 'evidence-manifest.json').read_bytes())
    actual = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
    expected = {a.path for a in manifest.files} | {'evidence-manifest.json'}
    if actual != expected:
        raise ValueError('unlisted or missing package file')
    for asset in manifest.files:
        read_asset(root, asset)
    for binding in manifest.copy_bindings:
        read_asset(root, binding.local)
    review = Review.model_validate_json((root / 'reviewed-draft.json').read_bytes())
    for name, value in [('reviewed-draft', review), ('evidence-manifest', manifest)]:
        schema = json.loads((root / (name + '.schema.json')).read_bytes())
        Draft202012Validator(schema).validate(value.model_dump(mode='json'))
    original = read_asset(root, review.original)
    candidate = read_asset(root, review.candidate)
    packet = json.loads(read_asset(root, review.original_packet_manifest))
    document = next(d for d in packet['documents'] if d['source_id'] == SID)
    if document['original']['sha256'] != review.original.sha256 or document['candidate']['sha256'] != review.candidate.sha256:
        raise ValueError('original packet source/candidate differs')
    a14 = json.loads((root / 'audits/pages1-4/SOURCE_QA.json').read_bytes())
    a58 = json.loads((root / 'audits/pages5-8/SOURCE_REVIEW.json').read_bytes())
    for subpath, payload in [('audits/pages1-4/SOURCE_QA', a14), ('audits/pages5-8/SOURCE_REVIEW', a58)]:
        Draft202012Validator(json.loads((root / (subpath + '.schema.json')).read_bytes())).validate(payload)
    if a14['external_review_consulted'] or a58['external_ebenezer_reports_consulted']:
        raise ValueError('unexpected external review input')
    audit14obs = {o['id']: o for o in a14['observations']}
    audit58obs = {o['id']: o for p in a58['pages'] for o in p['observations_in_native_order']}
    for obs in review.observations:
        prior = audit14obs[obs.audit_observation_id] if obs.physical_page <= 4 else audit58obs[obs.audit_observation_id]
        if obs.physical_page <= 4:
            spans = [(s['start_byte'], s['end_byte_exclusive'], s['exact_native_text']) for s in prior['spans']]
            if obs.finding != prior['finding'] or obs.qualifications != [prior['risk_or_limit']]:
                raise ValueError('imported pages1-4 finding was changed')
        else:
            spans = [(prior['original_start_byte'], prior['original_end_byte_exclusive'], prior['native_text'])]
            if obs.qualifications != prior['association_risks']:
                raise ValueError('imported pages5-8 qualifications were changed')
        if [(s.start_byte, s.end_byte_exclusive, s.text) for s in obs.spans] != spans:
            raise ValueError('independent observation bytes differ')
    with pymupdf.open(stream=original, filetype='pdf') as pdf:
        if len(pdf) != 8 or pdf.is_repaired or pdf.is_encrypted:
            raise ValueError('source PDF structure differs')
        for page in review.pages:
            d = document['pages'][page.physical_page - 1]
            image = read_asset(root, page.image)
            evidence = json.loads(read_asset(root, page.native_receipt))
            Draft202012Validator(json.loads((root / 'native-evidence/page.schema.json').read_bytes())).validate(evidence)
            if (page.image.sha256 != d['image']['sha256'] or page.native_receipt.sha256 != d['evidence']['sha256']
                or page.candidate_start_byte != d['candidate_text_offset_bytes']
                or page.candidate_end_byte_exclusive != d['candidate_text_end_byte_exclusive']
                or evidence['source_sha256'] != review.original.sha256
                or evidence['source_image_sha256'] != page.image.sha256
                or evidence['physical_page'] != page.physical_page or evidence['text'] != page.native_text):
                raise ValueError('page receipt or original packet binding differs')
            if image[:8] != b'\x89PNG\r\n\x1a\n' or [int.from_bytes(image[x:x+4], 'big') for x in (16, 20)] != [2550, 3300]:
                raise ValueError('page image dimensions differ')
            native = page.native_text.encode()
            if candidate[page.candidate_start_byte:page.candidate_end_byte_exclusive] != native:
                raise ValueError('candidate native slice differs')
            if pdf[page.physical_page - 1].get_text('text', sort=False, flags=195) != page.native_text:
                raise ValueError('native replay differs')
    custody = review.custody
    manifest_bytes = read_asset(root, custody.frozen_raw_manifest)
    lines = manifest_bytes.splitlines(keepends=True)
    records = [IntakeRecord.model_validate_json(line) for line in lines]
    selected = lines[custody.raw_manifest_line_number - 1]
    if len(records) != 31 or digest(selected) != custody.raw_manifest_line_sha256 or len(selected) != custody.raw_manifest_line_bytes:
        raise ValueError('frozen raw custody line differs')
    row = records[custody.raw_manifest_line_number - 1]
    if row != custody.selected_intake_record or (row.record_id, row.sha256, row.size_bytes, row.status, row.acquisition_method) != (
            SID, review.original.sha256, review.original.size_bytes, 'archived_pending_pipeline', 'received_review_package'):
        raise ValueError('selected manual intake does not bind pending source')
    provenance = read_asset(root, custody.frozen_source_provenance).splitlines(keepends=True)[custody.provenance_line_number - 1]
    if digest(provenance) != custody.provenance_line_sha256 or len(provenance) != custody.provenance_line_bytes:
        raise ValueError('frozen provenance line differs')
    source_provenance = json.loads(provenance)
    if (source_provenance['source_id'] != SID
        or IntakeRecord.model_validate(source_provenance['manual_intake']) != row
        or source_provenance['original']['sha256'] != review.original.sha256
        or source_provenance['original']['path'] != row.archive_path):
        raise ValueError('source-provenance identity differs from manual custody')
    claims = source_provenance['claims']
    if (claims['requested_url'], claims['final_url'], claims['logged_at'],
        claims['claimed_referral_url'], claims['supplied_http_status']) != (
        custody.claimed_official_url, custody.claimed_final_url, custody.claimed_attempt_time,
        custody.claimed_referral_url, custody.claimed_status):
        raise ValueError('upstream claims were not preserved exactly')
    for name in ['intake-receipt', 'source-provenance']:
        schema = json.loads((root / 'custody' / (name + '.schema.json')).read_bytes())
        if name == 'intake-receipt':
            payload = json.loads(read_asset(root, custody.frozen_intake_receipt))
            Draft202012Validator(schema).validate(payload)
            selected = [s for s in payload['sources'] if s['source_id'] == SID]
            if selected != [source_provenance]:
                raise ValueError('intake receipt differs from selected source provenance')
        else:
            for line in read_asset(root, custody.frozen_source_provenance).splitlines():
                Draft202012Validator(schema).validate(json.loads(line))
    # Structural byte validation is separate from the previously recorded visual judgments.
    return {'status': 'passed', 'pages': 8, 'native_bytes': sum(p.native_bytes for p in review.pages),
            'observations': len(review.observations), 'annotations': len(review.annotations),
            'files_verified': len(manifest.files), 'candidate_changed': False,
            'document_status': 'visibly_draft', 'external_review_status': review.external_review_status,
            'legal_currentness': 'not_verified', 'semantic_or_coverage_promotion': False}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    print(json.dumps(validate_package(args.package), indent=2))
