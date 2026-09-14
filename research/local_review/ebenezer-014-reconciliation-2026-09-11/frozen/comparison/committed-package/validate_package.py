"""Validate portable EB014 source review without writes, repository imports or network."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import logging
from pathlib import Path, PurePosixPath
from typing import Annotated, Literal

import jsonschema
import pymupdf
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

SOURCE_ID = 'fort-collins-land-use-article-1-sd005-07'
SOURCE_SHA = '555a05553af57619c818c5b9ab90d1b751e161a307d8bb65fc73141991a73d2a'
SHA = Annotated[str, Field(pattern=r'^[0-9a-f]{64}$')]
RECT = Annotated[list[float], Field(min_length=4, max_length=4)]
PAGE = Annotated[int, Field(ge=1, le=7)]


def sha(raw: bytes) -> str:
    """Return exact byte SHA256."""
    return hashlib.sha256(raw).hexdigest()


class StrictModel(BaseModel):
    """Disallow coercion and unspecified fields."""
    model_config = ConfigDict(extra='forbid', strict=True)


class FileRef(StrictModel):
    """A regular local file and immutable byte identity."""
    path: str
    sha256: SHA
    size_bytes: Annotated[int, Field(gt=0)]

    @model_validator(mode='after')
    def confined(self) -> FileRef:
        """Reject noncanonical or escaping package paths."""
        p = PurePosixPath(self.path)
        if (p.is_absolute() or '..' in p.parts or '\\' in self.path or ':' in self.path
                or p.as_posix() != self.path or self.path == '.'):
            raise ValueError('Unconfined package path')
        return self


class Span(StrictModel):
    """Exact native text plus page-relative and full-candidate byte bounds."""
    start_byte: Annotated[int, Field(ge=0)]
    end_byte_exclusive: Annotated[int, Field(gt=0)]
    candidate_start_byte: Annotated[int, Field(ge=0)]
    candidate_end_byte_exclusive: Annotated[int, Field(gt=0)]
    text: str
    sha256: SHA

    @model_validator(mode='after')
    def check(self) -> Span:
        """Validate span lengths and hash."""
        data = self.text.encode()
        if not data or sha(data) != self.sha256:
            raise ValueError('Bad span bytes')
        if self.end_byte_exclusive-self.start_byte != len(data):
            raise ValueError('Native length mismatch')
        if self.candidate_end_byte_exclusive-self.candidate_start_byte != len(data):
            raise ValueError('Candidate length mismatch')
        return self


class Chunk(StrictModel):
    """Disjoint chunk preserving exact native bytes, separate from visibility."""
    id: str
    role: Literal['layout_whitespace', 'header', 'footer', 'body', 'cover_title', 'cover_purpose']
    visibility: Literal['visible_text', 'not_visible_in_checked_render', 'layout_whitespace']
    span: Span


class PageReview(StrictModel):
    """Complete original native page with image binding and visible order."""
    physical_page: PAGE
    source_sha256: SHA
    page_role: Literal['cover', 'accessibility', 'contents', 'substantive']
    printed_page_label: str | None
    native_page_label: str | None
    image: FileRef
    native_evidence: FileRef
    original_native_file: FileRef
    native_text: str
    native_sha256: SHA
    candidate_start_byte: int
    candidate_end_byte_exclusive: int
    chunks: list[Chunk]
    visible_chunk_order: list[str]
    full_page_visually_checked: Literal[True]
    lexical_result: Literal['body_wording_matches_preserve_separate_layout_and_image_gaps']

    @model_validator(mode='after')
    def partition(self) -> PageReview:
        """Require exhaustive partition and visible-order completeness."""
        raw = self.native_text.encode()
        if sha(raw) != self.native_sha256:
            raise ValueError('Native hash mismatch')
        if self.candidate_end_byte_exclusive-self.candidate_start_byte != len(raw):
            raise ValueError('Page/candidate length mismatch')
        cursor = 0
        for chunk in self.chunks:
            s = chunk.span
            if s.start_byte != cursor or raw[s.start_byte:s.end_byte_exclusive] != s.text.encode():
                raise ValueError('Chunk gap, overlap or byte mismatch')
            if s.candidate_start_byte != self.candidate_start_byte + s.start_byte:
                raise ValueError('Chunk candidate offset mismatch')
            cursor = s.end_byte_exclusive
        if cursor != len(raw):
            raise ValueError('Incomplete native partition')
        visible = [c.id for c in self.chunks if c.visibility == 'visible_text']
        if len({c.id for c in self.chunks}) != len(self.chunks):
            raise ValueError('Duplicate chunk ID')
        if sorted(visible) != sorted(self.visible_chunk_order):
            raise ValueError('Visible-order inventory mismatch')
        return self


class Crop(StrictModel):
    """A direct 300 dpi PDF clip used as an inspection aid."""
    id: str
    physical_page: PAGE
    pdf_rect_points: RECT
    file: FileRef
    rendering: Literal['PyMuPDF 1.28.2; Matrix(300/72,300/72); clip; alpha=False']
    visually_checked: Literal[True]


class Observation(StrictModel):
    """Checked region with native or explicitly image-only evidence."""
    id: str
    physical_page: PAGE
    source_sha256: SHA
    source_image_sha256: SHA
    kind: Literal['lexical_verified', 'source_anomaly', 'reading_order',
                  'native_not_visible', 'image_only', 'scope_boundary', 'source_layout']
    region: str
    pdf_rect_points: RECT
    native_spans: list[Span]
    image_only_words: str | None
    finding: str
    risk_or_limit: str
    crop_ids: list[str]
    legal_effect: Literal['not_determined']

    @model_validator(mode='after')
    def evidence(self) -> Observation:
        """Do not pretend image-only words have native byte offsets."""
        if self.kind != 'image_only' and not self.native_spans:
            raise ValueError('Native observation needs a byte span')
        if self.kind != 'image_only' and self.image_only_words is not None:
            raise ValueError('Image-only text in native claim')
        if self.kind == 'image_only' and self.native_spans:
            raise ValueError('Image-only claim must not invent native offsets')
        return self


class PDFLink(StrictModel):
    """PDF annotation metadata only; no link was opened."""
    id: str
    physical_page: PAGE
    source_sha256: SHA
    xref: int
    kind: Literal['uri', 'internal']
    pdf_rect_points: RECT
    uri: str | None
    destination_physical_page: PAGE | None
    destination_point: Annotated[list[float], Field(min_length=2, max_length=2)] | None
    destination_zoom: float | None
    source_method: Literal['PyMuPDF 1.28.2 Page.get_links()']
    target_opened: Literal[False]

    @model_validator(mode='after')
    def shape(self) -> PDFLink:
        """Keep URI and internal target roles separate."""
        if self.kind == 'uri':
            if self.uri is None or self.destination_physical_page is not None:
                raise ValueError('URI target shape mismatch')
        elif self.uri is not None or self.destination_physical_page is None:
            raise ValueError('Internal target shape mismatch')
        return self


class SourceReview(StrictModel):
    """Seven-page source QA without current-law or external-review conclusions."""
    schema_version: Literal[1]
    reviewed_at: datetime
    source_id: Literal['fort-collins-land-use-article-1-sd005-07']
    assignment_id: Literal['EB-PDF-014']
    status: Literal['seven_page_candidate_aware_source_qa_complete_pending_parent_integration']
    legal_currentness: Literal['not_verified']
    review_mode: Literal['candidate_aware_not_blind']
    external_review_consulted: Literal[False]
    prior_exposure: str
    source: FileRef
    canonical_raw_source: FileRef
    packet_manifest: FileRef
    candidate: FileRef
    expected_pages: Literal[7]
    pages: list[PageReview]
    crops: list[Crop]
    observations: list[Observation]
    pdf_links: list[PDFLink]
    text_edits_applied: Annotated[list[str], Field(max_length=0)]
    preservation_policy: str
    limits: list[str]
    checks: list[str]

    @model_validator(mode='after')
    def bind(self) -> SourceReview:
        """Require fixed source and exact page/span associations."""
        if self.source.sha256 != SOURCE_SHA or self.canonical_raw_source.sha256 != SOURCE_SHA:
            raise ValueError('Wrong source')
        pages = {p.physical_page: p for p in self.pages}
        if list(pages) != list(range(1,8)) or len(self.pages) != 7:
            raise ValueError('Incorrect seven-page inventory')
        crop_map = {c.id: c for c in self.crops}
        for p in pages.values():
            if p.source_sha256 != self.source.sha256:
                raise ValueError('Wrong page source')
        if len({o.id for o in self.observations}) != len(self.observations):
            raise ValueError('Duplicate observation IDs')
        for o in self.observations:
            p = pages[o.physical_page]
            if o.source_sha256 != self.source.sha256 or o.source_image_sha256 != p.image.sha256:
                raise ValueError('Observation source/image mismatch')
            for s in o.native_spans:
                if p.native_text.encode()[s.start_byte:s.end_byte_exclusive] != s.text.encode():
                    raise ValueError('Observation native mismatch')
                if s.candidate_start_byte != p.candidate_start_byte+s.start_byte:
                    raise ValueError('Observation candidate offset mismatch')
            for cid in o.crop_ids:
                if crop_map[cid].physical_page != o.physical_page:
                    raise ValueError('Wrong observation crop page')
        for link in self.pdf_links:
            if link.source_sha256 != self.source.sha256:
                raise ValueError('Wrong link source')
        return self



class IntakeRecord(StrictModel):
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

class Custody(StrictModel):
    """Frozen historical custody, separate from unverified upstream acquisition claims."""
    frozen_raw_manifest: FileRef
    raw_manifest_line_number: Literal[18] = 18
    raw_manifest_line_sha256: SHA
    raw_manifest_line_bytes: int = Field(gt=0)
    selected_intake_record: IntakeRecord
    frozen_intake_receipt: FileRef
    frozen_source_provenance: FileRef
    provenance_line_number: Literal[6] = 6
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


class CopyBinding(StrictModel):
    """Historical location mapped to verified local evidence bytes."""
    historical_path: str
    local: FileRef


class Association(StrictModel):
    """Related reviewed regions retained together without inserting native words."""
    id: str
    observation_ids: Annotated[list[str], Field(min_length=2)]
    relationship: Literal[
        'purpose_list_and_qualification', 'cross_page_continuation',
        'visible_native_and_image_distinction', 'displayed_labels_and_pdf_metadata',
        'source_anomalies_not_editorial_corrections',
    ]
    note: str
    changes_native_text: Literal[False] = False
    establishes_legal_effect: Literal[False] = False


class PackageReview(StrictModel):
    """Portable source QA plus retained receipt custody, pending external review."""
    schema_version: Literal[1] = 1
    assignment_id: Literal['EB-PDF-014'] = 'EB-PDF-014'
    source_id: Literal['fort-collins-land-use-article-1-sd005-07'] = SOURCE_ID
    prepared_at: AwareDatetime
    extraction_review_status: Literal['atlas_seven_page_source_review_complete']
    external_review_status: Literal['external_review_pending']
    external_reports_consulted: Literal[False] = False
    document_scope: Literal['retained_seven_page_article_1_only']
    edition_date: None = None
    adoption_date: None = None
    effective_date: None = None
    dates_qualification: str
    legal_currentness: Literal['not_verified'] = 'not_verified'
    legal_effect_verified: Literal[False] = False
    semantic_or_coverage_promotion: Literal[False] = False
    candidate_changes: Literal['none'] = 'none'
    candidate_status_unchanged: Literal['machine_native_text_unreviewed']
    original_intake_status: Literal['archived_pending_pipeline']
    original_source_audit: FileRef
    retained_source_audit_with_local_bindings: SourceReview
    custody: Custody
    associations: list[Association]
    limits: list[str]

    @model_validator(mode='after')
    def complete(self) -> PackageReview:
        """Require this exact seven-page scope and explicit related-region identities."""
        audit = self.retained_source_audit_with_local_bindings
        if (sum(len(p.native_text.encode()) for p in audit.pages) != 13579
                or sum(len(p.chunks) for p in audit.pages) != 27
                or len(audit.observations) != 29 or len(audit.crops) != 10
                or sum(len(o.native_spans) for o in audit.observations) != 36
                or len(audit.pdf_links) != 12):
            raise ValueError('Review scope/count differs')
        if len({x.id for x in self.associations}) != len(self.associations):
            raise ValueError('Duplicate association ID')
        ids = {o.id for o in audit.observations}
        for association in self.associations:
            if len(set(association.observation_ids)) != len(association.observation_ids):
                raise ValueError('Duplicate association member')
            if not set(association.observation_ids) <= ids:
                raise ValueError('Unknown association member')
        return self


class Manifest(StrictModel):
    """Inventory all portable files except this manifest's own bytes."""
    schema_version: Literal[1] = 1
    assignment_id: Literal['EB-PDF-014'] = 'EB-PDF-014'
    prepared_at: AwareDatetime
    files: list[FileRef]
    copy_bindings: list[CopyBinding]
    file_count: Annotated[int, Field(gt=0)]
    total_listed_bytes: Annotated[int, Field(gt=0)]
    external_review_status: Literal['external_review_pending']
    legal_currentness: Literal['not_verified'] = 'not_verified'

    @model_validator(mode='after')
    def inventory(self) -> Manifest:
        """Reject duplicate/unlisted copied paths and inaccurate totals."""
        files = {x.path: x for x in self.files}
        if len(files) != self.file_count or len(self.files) != self.file_count:
            raise ValueError('Inventory count or duplicate path differs')
        if sum(x.size_bytes for x in self.files) != self.total_listed_bytes:
            raise ValueError('Inventory total bytes differs')
        histories = [x.historical_path for x in self.copy_bindings]
        if len(set(histories)) != len(histories):
            raise ValueError('Duplicate historical copy identity')
        for binding in self.copy_bindings:
            if files.get(binding.local.path) != binding.local:
                raise ValueError('Copy binding is not inventoried')
        return self


def read_asset(root: Path, asset: FileRef) -> bytes:
    """Verify a confined ordinary file, rejecting symlinks through every ancestor."""
    path = root / asset.path
    if any(p.is_symlink() for p in (path, *path.parents)) or not path.is_file():
        raise ValueError('Evidence is not an ordinary file')
    data = path.read_bytes()
    if len(data) != asset.size_bytes or sha(data) != asset.sha256:
        raise ValueError(f'Evidence size/hash mismatch: {asset.path}')
    return data


def collect_links(pdf: pymupdf.Document) -> list[PDFLink]:
    """Replay PDF annotation metadata without following any target."""
    links: list[PDFLink] = []
    for n, page in enumerate(pdf, 1):
        for raw in page.get_links():
            if raw['kind'] not in (1, 2):
                raise ValueError('Unexpected link kind')
            internal = raw['kind'] == 1
            links.append(PDFLink(
                id=f'PDF-P{n}-XREF-{raw["xref"]}', physical_page=n,
                source_sha256=SOURCE_SHA, xref=raw['xref'],
                kind='internal' if internal else 'uri',
                pdf_rect_points=[float(x) for x in raw['from']], uri=raw.get('uri'),
                destination_physical_page=raw['page'] + 1 if internal else None,
                destination_point=[float(x) for x in raw['to']] if internal else None,
                destination_zoom=float(raw['zoom']) if internal else None,
                source_method='PyMuPDF 1.28.2 Page.get_links()', target_opened=False,
            ))
    return links


def relocalize(value: object, mapping: dict[str, dict[str, object]]) -> object:
    """Substitute only retained file-reference paths; all source findings stay exact."""
    if isinstance(value, dict):
        if set(value) == {'path', 'sha256', 'size_bytes'}:
            local = mapping.get(value['path'])
            if local is None or (local['sha256'], local['size_bytes']) != (
                    value['sha256'], value['size_bytes']):
                raise ValueError('Original audit file has no exact portable copy')
            return local
        return {k: relocalize(v, mapping) for k, v in value.items()}
    if isinstance(value, list):
        return [relocalize(v, mapping) for v in value]
    return value


def validate_package(root: Path) -> dict[str, object]:
    """Replay inventory, unchanged QA/native/links and qualified receipt provenance."""
    if any(p.is_symlink() for p in (root, *root.parents)):
        raise ValueError('Package root has symlink ancestor')
    manifest_path = root / 'evidence-manifest.json'
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise ValueError('Manifest is not ordinary')
    manifest = Manifest.model_validate_json(manifest_path.read_bytes())
    expected = {a.path for a in manifest.files} | {'evidence-manifest.json'}
    entries = list(root.rglob('*'))
    if any(p.is_symlink() for p in entries):
        raise ValueError('Package contains symlink')
    actual = {p.relative_to(root).as_posix() for p in entries if p.is_file()}
    if actual != expected:
        raise ValueError('Unlisted or missing package file')
    for asset in manifest.files:
        read_asset(root, asset)
    package = PackageReview.model_validate_json((root / 'reviewed-text.json').read_bytes())
    for name, value in [('reviewed-text', package), ('evidence-manifest', manifest)]:
        schema = json.loads((root / (name + '.schema.json')).read_bytes())
        jsonschema.Draft202012Validator(schema).validate(value.model_dump(mode='json'))
    audit = package.retained_source_audit_with_local_bindings
    original_audit = json.loads(read_asset(root, package.original_source_audit))
    original_schema = json.loads((root / 'audit/SOURCE_QA.schema.json').read_bytes())
    jsonschema.Draft202012Validator(original_schema).validate(original_audit)
    mapping = {x.historical_path: x.local.model_dump(mode='json')
               for x in manifest.copy_bindings}
    if relocalize(original_audit, mapping) != audit.model_dump(mode='json'):
        raise ValueError('Source findings/visibility/ordering changed during packaging')
    original = read_asset(root, audit.source)
    if read_asset(root, audit.canonical_raw_source) != original:
        raise ValueError('Canonical binding differs')
    candidate = read_asset(root, audit.candidate)
    packet = json.loads(read_asset(root, audit.packet_manifest))
    jsonschema.Draft202012Validator(json.loads(
        (root / 'packet/manifest.schema.json').read_bytes())).validate(packet)
    document = next(d for d in packet['documents'] if d['source_id'] == SOURCE_ID)
    for actual_asset, key in [(audit.source, 'original'), (audit.candidate, 'candidate')]:
        if (actual_asset.sha256, actual_asset.size_bytes) != (
                document[key]['sha256'], document[key]['size_bytes']):
            raise ValueError('Original packet source/candidate differs')
    with pymupdf.open(stream=original, filetype='pdf') as pdf:
        if len(pdf) != 7 or pdf.is_repaired or pdf.is_encrypted:
            raise ValueError('Source PDF structure differs')
        for page in audit.pages:
            declared = document['pages'][page.physical_page - 1]
            image = read_asset(root, page.image)
            evidence = json.loads(read_asset(root, page.native_evidence))
            jsonschema.Draft202012Validator(json.loads(
                (root / 'native-evidence/page.schema.json').read_bytes())).validate(evidence)
            if (page.image.sha256 != declared['image']['sha256']
                    or page.native_evidence.sha256 != declared['evidence']['sha256']
                    or page.candidate_start_byte != declared['candidate_text_offset_bytes']
                    or page.candidate_end_byte_exclusive != declared[
                        'candidate_text_end_byte_exclusive']
                    or evidence['source_sha256'] != SOURCE_SHA
                    or evidence['source_image_sha256'] != page.image.sha256
                    or evidence['physical_page'] != page.physical_page
                    or evidence['text'] != page.native_text):
                raise ValueError('Page receipt or original packet binding differs')
            dimensions = [int.from_bytes(image[x:x + 4], 'big') for x in (16, 20)]
            if image[:8] != b'\x89PNG\r\n\x1a\n' or dimensions != [2550, 3300]:
                raise ValueError('Page image dimensions differ')
            native = page.native_text.encode()
            if candidate[page.candidate_start_byte:page.candidate_end_byte_exclusive] != native:
                raise ValueError('Candidate native slice differs')
            if read_asset(root, page.original_native_file) != native:
                raise ValueError('Saved original-native bytes differ')
            if pdf[page.physical_page - 1].get_text('text', sort=False, flags=195) != page.native_text:
                raise ValueError('Native replay differs')
        if collect_links(pdf) != audit.pdf_links:
            raise ValueError('Embedded PDF link metadata differs')
        for crop in audit.crops:
            preserved = read_asset(root, crop.file)
            replay = pdf[crop.physical_page - 1].get_pixmap(
                matrix=pymupdf.Matrix(300 / 72, 300 / 72),
                clip=pymupdf.Rect(crop.pdf_rect_points), alpha=False,
            )
            actual_pixels = pymupdf.Pixmap(preserved)
            if (replay.width, replay.height, replay.n, replay.samples) != (
                    actual_pixels.width, actual_pixels.height,
                    actual_pixels.n, actual_pixels.samples):
                raise ValueError('Source crop pixel reproduction differs')
    custody = package.custody
    lines = read_asset(root, custody.frozen_raw_manifest).splitlines(keepends=True)
    records = [IntakeRecord.model_validate_json(line) for line in lines]
    selected = lines[custody.raw_manifest_line_number - 1]
    if (len(records) != 31 or sha(selected) != custody.raw_manifest_line_sha256
            or len(selected) != custody.raw_manifest_line_bytes):
        raise ValueError('Frozen raw custody line differs')
    row = records[custody.raw_manifest_line_number - 1]
    if row != custody.selected_intake_record or (
            row.record_id, row.sha256, row.size_bytes, row.status, row.acquisition_method) != (
                SOURCE_ID, audit.source.sha256, audit.source.size_bytes,
                'archived_pending_pipeline', 'received_review_package'):
        raise ValueError('Selected manual intake does not bind pending source')
    provenance_lines = read_asset(root, custody.frozen_source_provenance).splitlines(keepends=True)
    provenance = provenance_lines[custody.provenance_line_number - 1]
    if (sha(provenance) != custody.provenance_line_sha256
            or len(provenance) != custody.provenance_line_bytes):
        raise ValueError('Frozen provenance line differs')
    source_provenance = json.loads(provenance)
    if (source_provenance['source_id'] != SOURCE_ID
            or IntakeRecord.model_validate_json(json.dumps(
                source_provenance['manual_intake'])) != row
            or source_provenance['original']['sha256'] != audit.source.sha256
            or source_provenance['original']['path'] != row.archive_path):
        raise ValueError('Source provenance identity differs from manual custody')
    claims = source_provenance['claims']
    if (claims['requested_url'], claims['final_url'], claims['logged_at'],
            claims['claimed_referral_url'], claims['supplied_http_status']) != (
                custody.claimed_official_url, custody.claimed_final_url,
                custody.claimed_attempt_time, custody.claimed_referral_url,
                custody.claimed_status):
        raise ValueError('Upstream claims were not preserved exactly')
    for name in ['intake-receipt', 'source-provenance']:
        schema = json.loads((root / 'custody' / (name + '.schema.json')).read_bytes())
        if name == 'intake-receipt':
            payload = json.loads(read_asset(root, custody.frozen_intake_receipt))
            jsonschema.Draft202012Validator(schema).validate(payload)
            if [s for s in payload['sources'] if s['source_id'] == SOURCE_ID] != [source_provenance]:
                raise ValueError('Intake receipt selected source differs')
        else:
            for line in provenance_lines:
                jsonschema.Draft202012Validator(schema).validate(json.loads(line))
    return {
        'status': 'passed', 'pages': 7, 'native_bytes': 13579, 'native_chunks': 27,
        'observations': 29, 'native_observation_spans': 36, 'crops_reproduced': 10,
        'pdf_links_reproduced': 12, 'files_verified': manifest.file_count,
        'candidate_changed': False, 'external_review_status': 'external_review_pending',
        'legal_currentness': 'not_verified', 'semantic_or_coverage_promotion': False,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    logging.info(json.dumps(validate_package(args.package), indent=2))
