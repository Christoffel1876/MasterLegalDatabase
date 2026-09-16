"""Validate portable EB013 reconciliation without external paths, network or writes."""
from __future__ import annotations

import argparse
import ast
import importlib.util
import json
import logging
import re
import sys
from collections import Counter
from hashlib import sha256
from pathlib import Path, PurePosixPath
from typing import Annotated, Literal

import jsonschema
import pymupdf
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from frozen.reconciliation_models import Reconciliation

SHA = Annotated[str, Field(pattern=r'^[0-9a-f]{64}$')]
FINAL_SHA = '7f77104042b259162bee7981ad3d3091aefc088865a3b74dbde0310ad38e7da4'
EXCLUDED_HELPERS = {
    'freeze_inputs.py', 'freeze_comparison.py', 'build_reconciliation.py',
    'validate_reconciliation.py',
}


class Strict(BaseModel):
    """Reject unmodeled fields and coercion."""
    model_config = ConfigDict(extra='forbid', strict=True)


class Asset(Strict):
    """A confined relative path with exact original bytes."""
    path: str
    sha256: SHA
    size_bytes: int = Field(ge=0)

    @model_validator(mode='after')
    def confined(self) -> Asset:
        """Keep all runtime reads inside the portable package."""
        p = PurePosixPath(self.path)
        if (p.is_absolute() or '..' in p.parts or '\\' in self.path or ':' in self.path
                or p.as_posix() != self.path or self.path == '.'):
            raise ValueError('Unconfined package path')
        return self


class InputDisposition(Strict):
    """Explicit account of a frozen handoff input, including excluded helper code."""
    original: Asset
    local: Asset | None
    disposition: Literal['unchanged_copy', 'excluded_historical_helper']
    original_bytes_recomputed_offline: bool
    note: str

    @model_validator(mode='after')
    def identity(self) -> InputDisposition:
        """Do not claim excluded bytes have been checked offline."""
        if self.disposition == 'unchanged_copy':
            if self.local is None or not self.original_bytes_recomputed_offline:
                raise ValueError('Copied input lacks local proof')
            if (self.local.sha256, self.local.size_bytes) != (
                    self.original.sha256, self.original.size_bytes):
                raise ValueError('Copy differs from original')
        elif (self.local is not None or self.original_bytes_recomputed_offline
              or self.original.path not in EXCLUDED_HELPERS):
            raise ValueError('Unexpected exclusion')
        return self


class FontSupport(Strict):
    """Bounded native font metadata supporting previously recorded visual findings."""
    physical_page: int = Field(ge=1, le=8)
    text: str
    font: str
    flags: int
    bbox: list[float] = Field(min_length=4, max_length=4)


class PackageRecord(Strict):
    """Additive reconciliation status; the prior source-review package stays unchanged."""
    schema_version: Literal[1] = 1
    prepared_at: AwareDatetime
    assignment: Literal['EB-PDF-013'] = 'EB-PDF-013'
    status: Literal['external_report_reconciled_with_qualifications']
    frozen_reconciliation: Asset
    frozen_final_manifest: Asset
    source_package_directory: Literal['frozen/comparison/committed-package']
    inputs: list[InputDisposition]
    external_findings: Literal[23] = 23
    external_errata: Literal[4] = 4
    atlas_supplements: Literal[3] = 3
    dispositions: dict[str, int]
    e03_disposition: Literal['rejected'] = 'rejected'
    e04_disposition: Literal['rejected'] = 'rejected'
    native_word_or_number_corrections_required: Literal[0] = 0
    source_and_candidate_changed: Literal[False] = False
    prior_source_package_changed: Literal[False] = False
    external_reports_changed: Literal[False] = False
    prior_package_pending_status_is_historical: Literal[True] = True
    source_document_status: Literal['visibly_draft'] = 'visibly_draft'
    green_blank_redaction_proven: Literal[False] = False
    hidden_dates_inferred: Literal[False] = False
    exact_unicode_certified_from_images: Literal[False] = False
    external_blind_method_independently_verified: Literal[False] = False
    legal_currentness: Literal['not_verified'] = 'not_verified'
    operative_effect_verified: Literal[False] = False
    coverage_promoted: Literal[False] = False
    public_opens: Literal[0] = 0
    new_visual_review_performed_during_packaging: Literal[False] = False
    limits: list[str]

    @model_validator(mode='after')
    def scope(self) -> PackageRecord:
        """Require all known dispositions and fixed immutable handoff identity."""
        if self.dispositions != {'qualified': 13, 'accepted': 8,
                                 'source_observation': 5, 'rejected': 4}:
            raise ValueError('Disposition inventory differs')
        if self.frozen_final_manifest.sha256 != FINAL_SHA:
            raise ValueError('Wrong frozen reconciliation inventory')
        paths = [x.original.path for x in self.inputs]
        if len(paths) != len(set(paths)):
            raise ValueError('Duplicate original input')
        excluded = {x.original.path for x in self.inputs
                    if x.disposition == 'excluded_historical_helper'}
        if excluded != EXCLUDED_HELPERS:
            raise ValueError('Unexpected excluded inputs')
        return self


class Manifest(Strict):
    """Exact physical file inventory, excluding its own bytes."""
    schema_version: Literal[1] = 1
    prepared_at: AwareDatetime
    files: list[Asset]
    file_count: int = Field(gt=0)
    listed_bytes: int = Field(gt=0)
    excludes_own_bytes: Literal[True] = True

    @model_validator(mode='after')
    def count(self) -> Manifest:
        """Reject omitted, duplicate or incorrectly totaled files."""
        if len(self.files) != self.file_count or len({a.path for a in self.files}) != self.file_count:
            raise ValueError('File inventory count differs')
        if sum(a.size_bytes for a in self.files) != self.listed_bytes:
            raise ValueError('Inventory byte count differs')
        return self


def read_asset(root: Path, asset: Asset) -> bytes:
    """Verify an ordinary local file without following symlinks."""
    path = root / asset.path
    if not path.is_file() or any(x.is_symlink() for x in (path, *path.parents)):
        raise ValueError('Evidence is not an ordinary file')
    raw = path.read_bytes()
    if len(raw) != asset.size_bytes or sha256(raw).hexdigest() != asset.sha256:
        raise ValueError(f'File differs: {asset.path}')
    return raw


def validate_package(root: Path) -> dict[str, object]:
    """Replay all portable source/custody/disposition and limited typography bindings."""
    if any(x.is_symlink() for x in (root, *root.parents)):
        raise ValueError('Package root has symlink ancestor')
    entries = list(root.rglob('*'))
    if any(x.is_symlink() for x in entries):
        raise ValueError('Package contains symlink')
    manifest = Manifest.model_validate_json((root / 'evidence-manifest.json').read_bytes())
    expected = {x.path for x in manifest.files} | {'evidence-manifest.json'}
    if {p.relative_to(root).as_posix() for p in entries if p.is_file()} != expected:
        raise ValueError('Missing or unlisted package file')
    assets = {a.path: a for a in manifest.files}
    for asset in assets.values():
        read_asset(root, asset)
    record = PackageRecord.model_validate_json((root / 'package-record.json').read_bytes())
    for name, value in [('package-record', record), ('evidence-manifest', manifest)]:
        jsonschema.Draft202012Validator(json.loads(
            (root / (name + '.schema.json')).read_bytes())).validate(value.model_dump(mode='json'))
    inputs = {d.original.path: d for d in record.inputs}
    for item in inputs.values():
        if item.local is not None and assets.get(item.local.path) != item.local:
            raise ValueError('Copied original not in package inventory')

    def original(name: str) -> bytes:
        item = inputs[name]
        if item.local is None:
            raise ValueError(f'Original excluded from package: {name}')
        return read_asset(root, item.local)

    final = json.loads(read_asset(root, record.frozen_final_manifest))
    jsonschema.Draft202012Validator(json.loads(original('FINAL_MANIFEST.schema.json'))).validate(final)
    if len(final['files']) != 103:
        raise ValueError('Frozen handoff inventory scope differs')
    for row in final['files']:
        if inputs[row['path']].original.model_dump(mode='json') != row:
            raise ValueError('Frozen handoff identity differs')
    reconciliation = Reconciliation.model_validate_json(read_asset(root, record.frozen_reconciliation))
    jsonschema.Draft202012Validator(json.loads(original('RECONCILIATION.schema.json'))).validate(
        reconciliation.model_dump(mode='json'))
    if reconciliation.disposition_counts != record.dispositions:
        raise ValueError('Disposition counts changed')
    decisions = {d.id: d for d in reconciliation.decisions}
    for key in ['EB013-P1-E03', 'EB013-P1-E04', 'EB013-P2-023']:
        if decisions[key].disposition != 'rejected':
            raise ValueError('Rejected typography/redaction claim was promoted')
    for ref in [reconciliation.source_pdf, reconciliation.native_candidate,
                reconciliation.committed_review, *reconciliation.receipts,
                *reconciliation.supplemental_evidence]:
        if (inputs[ref.path].original.sha256, inputs[ref.path].original.size_bytes) != (
                ref.sha256, ref.size_bytes):
            raise ValueError('Reconciliation evidence binding differs')
        original(ref.path)
    custody = json.loads(original('CUSTODY_RECEIPT.json'))
    comparison = json.loads(original('COMPARISON_RECEIPT.json'))
    for name, value in [('CUSTODY_RECEIPT', custody), ('COMPARISON_RECEIPT', comparison)]:
        jsonschema.Draft202012Validator(json.loads(original(name + '.schema.json'))).validate(value)
    if len(custody['files']) != 4 or len(comparison['files']) != 75:
        raise ValueError('Report/comparison custody count differs')
    for row in custody['files']:
        name = 'received/' + Path(row['received_path']).name
        if (inputs[name].original.sha256, inputs[name].original.size_bytes) != (
                row['sha256'], row['size_bytes']):
            raise ValueError('External report custody differs')
    for row in comparison['files']:
        item = inputs[row['copy_path']]
        if (item.original.sha256, item.original.size_bytes) != (row['sha256'], row['size_bytes']):
            raise ValueError('Comparison-copy identity differs')
    claims = comparison['hash_claims']
    hashes = {a.sha256 for a in assets.values()}
    if len(claims) != 15:
        raise ValueError('Hash-claim count differs')
    for claim in claims:
        if not claim['matches'] or claim['expected_sha256'] != claim['actual_sha256']:
            raise ValueError('Claimed hash mismatch')
        if claim['expected_sha256'] not in hashes:
            raise ValueError('Claimed asset is not present in portable bytes')
    verified = {c['expected_sha256'] for c in claims}
    for name in ['PASS1_frozen.md', 'PASS2_REVIEW.md',
                 'PASS1_FREEZE_RECEIPT.json', 'COMPLETION_RECEIPT.json']:
        if not set(re.findall(r'\b[0-9a-f]{64}\b', original('received/' + name).decode())) <= verified:
            raise ValueError('Unresolved external asset hash')
    child = root / record.source_package_directory
    spec = importlib.util.spec_from_file_location('eb013_frozen_source_validator',
                                                child / 'validate_package.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    baseline = module.validate_package(child)
    if (baseline['pages'], baseline['native_bytes'], baseline['observations'],
            baseline['annotations']) != (8, 18881, 72, 126):
        raise ValueError('Unchanged source-review scope differs')
    draft = json.loads(original(reconciliation.committed_review.path))
    annotations = {a['id']: a for a in draft['annotations']}
    for decision in reconciliation.decisions:
        lines = original('received/' + decision.external_report).decode().splitlines()
        if lines[decision.external_line - 1] != decision.external_claim:
            raise ValueError('External claim line changed')
        for number, image in zip(decision.physical_pages, decision.page_images, strict=True):
            page = draft['pages'][number - 1]
            if image.sha256 != page['image']['sha256']:
                raise ValueError('Decision physical-page image differs')
            original(image.path)
        if any(aid not in annotations or annotations[aid]['physical_page'] not in decision.physical_pages
               for aid in decision.atlas_annotation_ids):
            raise ValueError('Decision annotation association differs')
    pass2 = original('received/PASS2_REVIEW.md').decode()
    if (len(re.findall(r'^\| EB013-P2-\d{3} \|', pass2, re.M)),
            len(re.findall(r'^\| EB013-P1-E\d{2} \|', pass2, re.M))) != (23, 4):
        raise ValueError('External row inventory differs')
    counts = json.loads(original('received/COMPLETION_RECEIPT.json'))['finding_counts']
    if counts != {'critical': 10, 'minor': 7, 'unresolved': 2, 'info_preserved': 4, 'pass1_errata': 4}:
        raise ValueError('External count arithmetic differs')
    # Replay only the recorded native metadata, without converting it into visual or legal proof.
    font_rows = [FontSupport.model_validate_json(json.dumps(x))
                 for x in json.loads(original('native-font-support.json'))]
    with pymupdf.open(stream=original(reconciliation.source_pdf.path), filetype='pdf') as pdf:
        available = []
        for n, page in enumerate(pdf, 1):
            for block in page.get_text('dict')['blocks']:
                for line in block.get('lines', []):
                    for span in line['spans']:
                        available.append(FontSupport(physical_page=n, text=span['text'],
                            font=span['font'], flags=span['flags'], bbox=list(span['bbox'])))
        if any(row not in available for row in font_rows):
            raise ValueError('Bounded native-font support does not reproduce')
    tree = ast.parse(original('inspect_support.py'))
    boxes = next(ast.literal_eval(node.value) for node in tree.body
                 if isinstance(node, ast.Assign)
                 and any(isinstance(t, ast.Name) and t.id == 'boxes' for t in node.targets))
    for name, (page, (left, top, right, bottom)) in boxes.items():
        parent = pymupdf.Pixmap(original(
            f'comparison/committed-package/images/page-{page:04}.png'))
        crop = pymupdf.Pixmap(original(f'crops/{name}.png'))
        if not (0 <= left < right <= parent.width and 0 <= top < bottom <= parent.height):
            raise ValueError('Crop outside source image')
        samples = parent.samples
        pixels = b''.join(samples[(y * parent.width + left) * parent.n:
                                  (y * parent.width + right) * parent.n]
                          for y in range(top, bottom))
        if (crop.width, crop.height, crop.n, crop.samples) != (
                right - left, bottom - top, parent.n, pixels):
            raise ValueError('Diagnostic crop pixels differ')
    return {
        'status': 'passed', 'external_findings': 23, 'external_errata': 4,
        'atlas_supplements': 3, 'dispositions': dict(Counter(d.disposition for d in reconciliation.decisions)),
        'source_pages': 8, 'native_bytes_unchanged': 18881, 'native_word_corrections': 0,
        'native_font_spans_reproduced': len(font_rows), 'diagnostic_crops_reproduced': len(boxes),
        'package_files_verified': manifest.file_count, 'excluded_historical_helpers': 4,
        'external_review_status': record.status, 'source_status': 'visibly_draft',
        'legal_currentness': 'not_verified', 'operative_effect_verified': False,
        'historical_git_verification_repeated': False,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    logging.info(json.dumps(validate_package(args.package), indent=2))
