"""Validate portable SD009 received research evidence, without network or writes."""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import re
from pathlib import Path, PurePosixPath
from typing import Annotated, Literal

import jsonschema
import pymupdf
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from audit_models import Audit, SourceAssessment

SHA = Annotated[str, Field(pattern=r'^[0-9a-f]{64}$')]
SOURCE_HASHES = {
    'SD009-01': 'a1a3dc6c43ba6d9d5e4dafb984d611f224f3f56a0ff10ee659c06e23f52caf2b',
    'SD009-02': '7d2d2fef60bb94a83076b060cd46fe0b2864ad2538c7115fa24b1ce6cc1f80d0',
    'SD009-03': '88e4c7dcceb70d55e286b809471da7531dc1f5493f080d4487a8988706d9f0bc',
}
EXPECTED_SOURCE_SCOPE = {
    'SD009-01': (2, [1, 2], 'staff_recommendation'),
    'SD009-02': (5, [1, 2, 3, 4, 5], 'unsigned_extension_draft'),
    'SD009-03': (20, [1, 9, 10], 'board_minutes'),
}


class Strict(BaseModel):
    """Reject undeclared fields and coercion."""
    model_config = ConfigDict(extra='forbid', strict=True)


class Asset(Strict):
    """A normalized confined relative path and exact byte identity."""
    path: str
    sha256: SHA
    size_bytes: int = Field(ge=0)

    @model_validator(mode='after')
    def confined(self) -> Asset:
        """Reject escaping or ambiguous paths without accessing external files."""
        path = PurePosixPath(self.path)
        if (path.is_absolute() or '..' in path.parts or '\\' in self.path
                or ':' in self.path or path.as_posix() != self.path or self.path == '.'):
            raise ValueError('Unconfined asset path')
        return self


class InputBinding(Strict):
    """Original audit identity, with explicit copy/redaction/exclusion disposition."""
    original: Asset
    historical_absolute_path: str
    disposition: Literal['unchanged_copy', 'redacted_header', 'hash_only_excluded']
    local: Asset | None
    reason: str
    removed_header_fields: list[str]
    original_bytes_recomputed_offline: bool

    @model_validator(mode='after')
    def shape(self) -> InputBinding:
        """Never pass a derived header or absent file off as original bytes."""
        if self.disposition == 'unchanged_copy':
            if self.local is None or (self.local.sha256, self.local.size_bytes) != (
                    self.original.sha256, self.original.size_bytes):
                raise ValueError('Unchanged copy differs')
            if self.removed_header_fields or not self.original_bytes_recomputed_offline:
                raise ValueError('Unchanged copy metadata differs')
        elif self.disposition == 'redacted_header':
            if (self.local is None or self.local.sha256 == self.original.sha256
                    or not self.removed_header_fields or self.original_bytes_recomputed_offline):
                raise ValueError('Redacted-header provenance differs')
        elif self.local is not None or self.original_bytes_recomputed_offline:
            raise ValueError('Excluded input cannot claim offline byte validation')
        return self


class ReviewedImage(Strict):
    """A prior visually inspected page image, with reproducible source rendering."""
    source_priority_id: Literal['SD009-01', 'SD009-02', 'SD009-03']
    physical_page: int = Field(ge=1)
    image: Asset
    evidence_origin: Literal['final_atlas_audit', 'root_precheck']
    rendering_dpi: Literal[144] = 144
    pixel_reproduction_only: Literal[True] = True
    new_visual_review_performed: Literal[False] = False


class Source(Strict):
    """An unchanged received PDF and the exact qualified Atlas assessment."""
    assessment: SourceAssessment
    artifact: Asset
    artifact_storage_role: Literal['received_research_evidence_only']
    authenticated_publisher_original: Literal[False] = False
    actual_original_acquisition_at: None = None
    verified_exact_download_endpoint: None = None
    manual_intake_record_created: Literal[False] = False


class URLConflict(Strict):
    """Retained conflicting acquisition claims, not evidence of source replacement."""
    claimed_url: Literal['https://larimercoco.portal.civicclerk.com/event/2812/files/agenda/3563']
    prior_event_id: Literal['SD007-B012']
    prior_recorded_sha256: Literal['15933b2bbfc05894ab6f6cc49b8f8e1c4490815036f6afab9b22c7dc2cdbf10e']
    prior_recorded_pages: Literal[194]
    prior_pdf_included: Literal[False]
    prior_pdf_reopened_for_packaging: Literal[False]
    current_event_id: Literal['SD009-B005']
    current_received_sha256: Literal['88e4c7dcceb70d55e286b809471da7531dc1f5493f080d4487a8988706d9f0bc']
    current_structural_pages: Literal[20]
    exact_endpoint_verified: Literal[False]
    source_replacement_inferred: Literal[False]
    note: str


class PackageReview(Strict):
    """Qualified portable research evidence with all operative conclusions withheld."""
    schema_version: Literal[1] = 1
    prepared_at: AwareDatetime
    package_status: Literal['portable_received_research_evidence_pending_pipeline']
    source_audit: Asset
    original_final_manifest: Asset
    sources: list[Source] = Field(min_length=3, max_length=3)
    reviewed_images: list[ReviewedImage] = Field(min_length=20, max_length=20)
    input_bindings: list[InputBinding]
    url_conflict: URLConflict
    structural_pages: Literal[27] = 27
    distinct_pages_visually_inspected_in_prior_reviews: Literal[10] = 10
    full_minutes_transcription_certified: Literal[False] = False
    consolidated_public_rows: Literal[12] = 12
    public_attempt_lower_bound: Literal[13] = 13
    exact_public_attempt_count: None = None
    cap_compliance_certified: Literal[False] = False
    literal_draft_effective_wording: Literal['August 25, 2025']
    literal_draft_first_recital_date: Literal['April 7, 2026']
    literal_draft_first_recital_reception: Literal['20260016505']
    final_february_instrument_supplied: Literal[False] = False
    final_july_instrument_supplied: Literal[False] = False
    legal_currentness: Literal['not_verified'] = 'not_verified'
    operative_law_promoted: Literal[False] = False
    coverage_promoted: Literal[False] = False
    raw_or_control_records_changed: Literal[False] = False
    public_source_opens: Literal[0] = 0
    report_custody: Literal['complete_frozen_report_and_metadata_with_explicit_input_dispositions']
    limits: list[str]

    @model_validator(mode='after')
    def bind(self) -> PackageReview:
        """Fix three artifact identities/classes and the exact ten-page visual scope."""
        if [s.assessment.priority_id for s in self.sources] != list(SOURCE_HASHES):
            raise ValueError('Wrong source inventory')
        for source in self.sources:
            assessment = source.assessment
            expected = EXPECTED_SOURCE_SCOPE[assessment.priority_id]
            if (assessment.pages, assessment.inspected_physical_pages, assessment.role) != expected:
                raise ValueError('Changed source classification or visual scope')
            if source.artifact.sha256 != SOURCE_HASHES[assessment.priority_id]:
                raise ValueError('Wrong received source bytes')
        names = [x.original.path for x in self.input_bindings]
        if len(names) != len(set(names)):
            raise ValueError('Duplicate original input path')
        for origin in ['final_atlas_audit', 'root_precheck']:
            expected = {(sid, page) for sid, (_, pages, _) in EXPECTED_SOURCE_SCOPE.items()
                        for page in pages}
            actual = [(i.source_priority_id, i.physical_page) for i in self.reviewed_images
                      if i.evidence_origin == origin]
            if len(actual) != 10 or set(actual) != expected:
                raise ValueError('Image review scope differs')
        return self


class Manifest(Strict):
    """Inventory actual package files separately from historical delivery counts."""
    schema_version: Literal[1] = 1
    prepared_at: AwareDatetime
    files: list[Asset]
    file_count: int = Field(gt=0)
    listed_bytes: int = Field(gt=0)
    excludes_own_bytes: Literal[True] = True
    status: Literal['research_evidence_only'] = 'research_evidence_only'

    @model_validator(mode='after')
    def counts(self) -> Manifest:
        """Reject repeated file paths and incorrect counts or size totals."""
        if len(self.files) != self.file_count or len({x.path for x in self.files}) != self.file_count:
            raise ValueError('Inventory file count differs')
        if sum(x.size_bytes for x in self.files) != self.listed_bytes:
            raise ValueError('Inventory byte total differs')
        return self


def digest(data: bytes) -> str:
    """SHA256 over exact bytes."""
    return hashlib.sha256(data).hexdigest()


def read_asset(root: Path, asset: Asset) -> bytes:
    """Only read a package-local regular file with unchanged size/hash."""
    path = root / asset.path
    if not path.is_file() or any(x.is_symlink() for x in (path, *path.parents)):
        raise ValueError('Evidence is not an ordinary file')
    raw = path.read_bytes()
    if len(raw) != asset.size_bytes or digest(raw) != asset.sha256:
        raise ValueError(f'File hash/size differs: {asset.path}')
    return raw


def validate_package(root: Path) -> dict[str, object]:
    """Replay packaged evidence without treating excluded historical bytes as present."""
    if any(x.is_symlink() for x in (root, *root.parents)):
        raise ValueError('Package root has symlink ancestor')
    entries = list(root.rglob('*'))
    if any(x.is_symlink() for x in entries):
        raise ValueError('Package contains a symlink')
    manifest = Manifest.model_validate_json((root / 'evidence-manifest.json').read_bytes())
    expected = {a.path for a in manifest.files} | {'evidence-manifest.json'}
    if {p.relative_to(root).as_posix() for p in entries if p.is_file()} != expected:
        raise ValueError('Missing or unlisted package file')
    files = {a.path: a for a in manifest.files}
    for asset in manifest.files:
        raw = read_asset(root, asset)
        if asset.path.endswith(('.txt', '.json', '.jsonl', '.md', '.html')):
            matches = re.findall(rb'(?im)^(?:set-cookie|cookie|authorization|proxy-authorization):[^\r\n]*', raw)
            if any(m.split(b':', 1)[1].strip() != b'[REDACTED]' for m in matches):
                raise ValueError('Unredacted credential/cookie header in distributable file')
    package = PackageReview.model_validate_json((root / 'received-evidence.json').read_bytes())
    for name, value in [('received-evidence', package), ('evidence-manifest', manifest)]:
        jsonschema.Draft202012Validator(json.loads(
            (root / (name + '.schema.json')).read_bytes())).validate(value.model_dump(mode='json'))
    bindings = {b.original.path: b for b in package.input_bindings}

    def original_bytes(name: str) -> bytes:
        binding = bindings[name]
        if binding.disposition != 'unchanged_copy' or binding.local is None:
            raise ValueError(f'Original bytes are not included: {name}')
        return read_asset(root, binding.local)

    for binding in bindings.values():
        if binding.local is not None:
            if files.get(binding.local.path) != binding.local:
                raise ValueError('Input binding is not inventoried')
            read_asset(root, binding.local)
    raw_audit = read_asset(root, package.source_audit)
    audit = Audit.model_validate_json(raw_audit)
    jsonschema.Draft202012Validator(json.loads(original_bytes(
        'INTAKE_AUDIT.schema.json'))).validate(json.loads(raw_audit))
    final = json.loads(read_asset(root, package.original_final_manifest))
    jsonschema.Draft202012Validator(json.loads(original_bytes(
        'FINAL_MANIFEST.schema.json'))).validate(final)
    for row in final['files']:
        binding = bindings[row['path']]
        if binding.original.model_dump(mode='json') != row:
            raise ValueError('Frozen original inventory identity differs')
    custody = json.loads(original_bytes('CUSTODY_RECEIPT.json'))
    jsonschema.Draft202012Validator(json.loads(original_bytes(
        'CUSTODY_RECEIPT.schema.json'))).validate(custody)
    if len(custody['files']) != 97 or sum(r['size_bytes'] for r in custody['files']) != 71496968:
        raise ValueError('Historical delivery counts differ')
    for row in custody['files']:
        key = next((k for k, b in bindings.items()
                    if b.historical_absolute_path == row['received_path']), None)
        if key is None or (bindings[key].original.sha256, bindings[key].original.size_bytes) != (
                row['sha256'], row['size_bytes']):
            raise ValueError('Historical custody identity lacks an explicit disposition')
    for support in audit.supporting_files:
        if (bindings[support.path].original.sha256, bindings[support.path].original.size_bytes) != (
                support.sha256, support.size_bytes):
            raise ValueError('Audit support identity differs')
        original_bytes(support.path)
    for finding in audit.findings:
        if any(name not in bindings for name in finding.evidence_paths):
            raise ValueError('Finding evidence has no disposition')
    precheck = json.loads(original_bytes('comparison-evidence/root-precheck/SOURCE_PRECHECK.json'))
    jsonschema.Draft202012Validator(json.loads(original_bytes(
        'comparison-evidence/root-precheck/SOURCE_PRECHECK.schema.json'))).validate(precheck)
    structural = json.loads(original_bytes('structural-facts.json'))
    structure_map = {x['sha256']: x for x in structural['source_pdfs']}
    for source in package.sources:
        assessment = source.assessment
        if assessment != next(s for s in audit.sources if s.priority_id == assessment.priority_id):
            raise ValueError('Original qualified source assessment changed')
        raw = read_asset(root, source.artifact)
        if raw != original_bytes(assessment.file.path):
            raise ValueError('Source differs from frozen audit')
        with pymupdf.open(stream=raw, filetype='pdf') as pdf:
            if len(pdf) != assessment.pages or pdf.is_repaired or pdf.is_encrypted:
                raise ValueError('PDF structural scope differs')
            if pdf.metadata != structure_map[source.artifact.sha256]['metadata']:
                raise ValueError('Source metadata differs')
            for page in pdf:
                page.get_text()
            for image in package.reviewed_images:
                if image.source_priority_id != assessment.priority_id:
                    continue
                retained = pymupdf.Pixmap(read_asset(root, image.image))
                replay = pdf[image.physical_page - 1].get_pixmap(
                    matrix=pymupdf.Matrix(2, 2), alpha=False)
                if (retained.width, retained.height, retained.n, retained.samples) != (
                        replay.width, replay.height, replay.n, replay.samples):
                    raise ValueError('Reviewed image does not reproduce from source page')
                if image.evidence_origin == 'root_precheck':
                    prior = next(s for s in precheck['sources']
                                 if s['sha256'] == source.artifact.sha256)
                    name = f"images/{Path(assessment.file.path).stem}-p{image.physical_page:02}.png"
                    if prior['image_sha256'][name] != image.image.sha256:
                        raise ValueError('Root precheck image binding differs')
    for excerpt in audit.excerpts:
        image = next(i for i in package.reviewed_images
                     if i.evidence_origin == 'final_atlas_audit'
                     and i.source_priority_id == excerpt.source_priority_id
                     and i.physical_page == excerpt.physical_page)
        if image.image.sha256 != excerpt.image.sha256:
            raise ValueError('Scoped excerpt image binding differs')
    logs = json.loads(original_bytes('received/20260911T190213Z/logs/attempted_urls.json'))
    public = [r for r in logs['events'] if r['public_open']]
    if len(logs['events']) != 13 or len(public) != 12 or len({r['requested_url'] for r in public}) != 9:
        raise ValueError('Consolidated log row/target facts differ')
    browser003 = next(r for r in public if r['event_id'] == 'SD009-B003')
    if 'One controlled retry after spinner.' not in browser003['note']:
        raise ValueError('Retained retry evidence differs')
    facts = json.loads(original_bytes('comparison-facts.json'))
    prior = facts['prior_packet_log_rows'][0]
    current = next(r for r in public if r['event_id'] == 'SD009-B005')
    conflict = package.url_conflict
    if (prior['requested_url'], current['requested_url'], prior['sha256'], current['sha256']) != (
            conflict.claimed_url, conflict.claimed_url, conflict.prior_recorded_sha256,
            conflict.current_received_sha256):
        raise ValueError('Same-URL acquisition conflict differs')
    for directory, expected_rows in [('pinned', 12), ('current', 38)]:
        raw = original_bytes('comparison-evidence/' + directory
                             + '/_RAW_ARCHIVE/manual_intake/manual_source_intake_manifest.jsonl')
        rows = [json.loads(line) for line in raw.splitlines()]
        if len(rows) != expected_rows or any(r['sha256'] in SOURCE_HASHES.values() for r in rows):
            raise ValueError('Scoped manual-manifest digest comparison differs')
    legacy = original_bytes('comparison-evidence/pinned/_CONTROL_PLANE/LOCAL_DOWNLOAD_MANIFEST.jsonl')
    if (len(legacy.splitlines()) != 48390
            or any(json.loads(r).get('sha256') in SOURCE_HASHES.values() for r in legacy.splitlines())):
        raise ValueError('Historical manifest digest comparison differs')
    return {
        'status': 'passed', 'received_pdf_artifacts': 3, 'structural_pages': 27,
        'prior_visual_page_scope': 10, 'images_reproduced': 20,
        'source_assessments_preserved': 3, 'scoped_excerpts_preserved': len(audit.excerpts),
        'historical_delivery_files': 97, 'package_files_verified': manifest.file_count,
        'redacted_header_inputs': sum(b.disposition == 'redacted_header' for b in bindings.values()),
        'excluded_historical_inputs': sum(b.disposition == 'hash_only_excluded' for b in bindings.values()),
        'exact_publisher_acquisition_verified': False, 'legal_currentness': 'not_verified',
        'raw_or_control_records_changed': False, 'new_visual_review_performed': False,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    logging.info(json.dumps(validate_package(args.package), indent=2))
