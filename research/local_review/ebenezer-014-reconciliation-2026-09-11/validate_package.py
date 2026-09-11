"""Validate portable EB014 reconciliation without network or original handoff paths."""
from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
from hashlib import sha256
from pathlib import Path, PurePosixPath
from typing import Annotated, Literal

import jsonschema
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

SHA = Annotated[str, Field(pattern=r'^[0-9a-f]{64}$')]
FINAL_SHA = '449bff25ace84f7dffa817f3088b8d10aa40d8e44224c46ecfd220e81fe2d8c2'


class Strict(BaseModel):
    """Reject unmodeled fields and coercion."""
    model_config = ConfigDict(extra='forbid', strict=True)


class Asset(Strict):
    """A confined ordinary file with its exact byte identity."""
    path: str
    sha256: SHA
    size_bytes: int = Field(ge=0)

    @model_validator(mode='after')
    def confined(self) -> Asset:
        """Reject absolute, noncanonical and traversing paths."""
        path = PurePosixPath(self.path)
        if (path.is_absolute() or '..' in path.parts or '\\' in self.path or ':' in self.path
                or path.as_posix() != self.path or self.path == '.'):
            raise ValueError('Unconfined package path')
        return self


class PackageRecord(Strict):
    """Additive status for the unchanged frozen reconciliation and prior source review."""
    schema_version: Literal[1]
    prepared_at: AwareDatetime
    assignment: Literal['EB-PDF-014']
    status: Literal['external_report_reconciled_with_qualifications']
    frozen_directory: Literal['frozen']
    frozen_file_count: Literal[85]
    frozen_final_manifest: Asset
    frozen_reconciliation: Asset
    source_package_directory: Literal['frozen/comparison/committed-package']
    external_reports: Literal[4]
    findings: Literal[21]
    errata: Literal[3]
    unresolved_themes: Literal[5]
    dispositions: dict[str, int]
    inspected_physical_pages: list[int]
    inspected_crops: Literal[11]
    native_bytes_preserved: Literal[13579]
    candidate_bytes_preserved: Literal[14370]
    source_pdf_bytes_preserved: Literal[340287]
    native_word_or_number_corrections_required: Literal[0]
    all_frozen_inputs_copied_unchanged: Literal[True]
    excluded_frozen_inputs: list[str]
    original_reports_changed: Literal[False]
    original_source_package_changed: Literal[False]
    source_and_candidate_changed: Literal[False]
    prior_source_pending_status_is_historical: Literal[True]
    historical_absolute_paths_used_for_portable_validation: Literal[False]
    new_visual_review_during_packaging: Literal[False]
    external_pdf_rehash_independently_certified: Literal[False]
    atlas_pdf_hash_checked: Literal[True]
    external_blindness_independently_certified: Literal[False]
    legal_currentness: Literal['not_verified']
    operative_effect_verified: Literal[False]
    coverage_promoted: Literal[False]
    public_opens: Literal[0]
    limits: list[str]

    @model_validator(mode='after')
    def scope(self) -> PackageRecord:
        """Require exact frozen identities, complete scope and no hidden omissions."""
        if self.frozen_final_manifest.sha256 != FINAL_SHA:
            raise ValueError('Wrong frozen reconciliation manifest')
        if self.dispositions != {'qualified': 11, 'accepted': 8, 'source_observation': 10}:
            raise ValueError('Disposition count differs')
        if self.inspected_physical_pages != list(range(1, 8)) or self.excluded_frozen_inputs:
            raise ValueError('Incomplete frozen review scope')
        return self


class Manifest(Strict):
    """The complete portable file inventory, excluding its own JSON and schema."""
    schema_version: Literal[1]
    prepared_at: AwareDatetime
    files: list[Asset]
    file_count: int = Field(gt=0)
    listed_bytes: int = Field(gt=0)
    excluded_self_files: Literal['evidence-manifest.json,evidence-manifest.schema.json']

    @model_validator(mode='after')
    def count(self) -> Manifest:
        """Reject duplicate paths and incorrect totals."""
        if len(self.files) != self.file_count or len({x.path for x in self.files}) != self.file_count:
            raise ValueError('File count differs')
        if sum(x.size_bytes for x in self.files) != self.listed_bytes:
            raise ValueError('Byte count differs')
        return self


def read_asset(root: Path, asset: Asset) -> bytes:
    """Verify exact bytes without following symlink files or ancestors."""
    path = root / asset.path
    if not path.is_file() or any(x.is_symlink() for x in (path, *path.parents)):
        raise ValueError(f'Not an ordinary source file: {asset.path}')
    raw = path.read_bytes()
    if len(raw) != asset.size_bytes or sha256(raw).hexdigest() != asset.sha256:
        raise ValueError(f'File bytes differ: {asset.path}')
    return raw


def load_model(root: Path, name: str, model: type[Strict]) -> Strict:
    """Check strict model and its exported JSON Schema."""
    data = (root / f'{name}.json').read_bytes()
    schema = json.loads((root / f'{name}.schema.json').read_bytes())
    if schema != model.model_json_schema():
        raise ValueError(f'Schema differs: {name}')
    value = model.model_validate_json(data)
    jsonschema.Draft202012Validator(schema).validate(json.loads(data))
    return value


def validate_package(root: Path) -> dict[str, object]:
    """Verify inventory then run the unchanged frozen portable semantic validator."""
    if any(x.is_symlink() for x in (root, *root.parents)):
        raise ValueError('Package path contains symlink')
    manifest = load_model(root, 'evidence-manifest', Manifest)
    actual = set()
    for path in root.rglob('*'):
        if path.is_symlink():
            raise ValueError('Package contains symlink')
        if path.is_file() and '__pycache__' not in path.parts:
            actual.add(path.relative_to(root).as_posix())
    actual -= {'evidence-manifest.json', 'evidence-manifest.schema.json'}
    if actual != {x.path for x in manifest.files}:
        raise ValueError('Portable inventory has missing or extra files')
    for asset in manifest.files:
        read_asset(root, asset)
    record = load_model(root, 'package-record', PackageRecord)
    final = json.loads(read_asset(root, record.frozen_final_manifest))
    reconciliation = json.loads(read_asset(root, record.frozen_reconciliation))
    frozen_files = {name.removeprefix('frozen/') for name in actual if name.startswith('frozen/')}
    expected = {x['path'] for x in final['files']}
    expected |= {'FINAL_MANIFEST.json', 'FINAL_MANIFEST.schema.json'}
    if frozen_files != expected or len(frozen_files) != record.frozen_file_count:
        raise ValueError('Frozen audit is incomplete')
    if reconciliation['disposition_counts'] != record.dispositions:
        raise ValueError('Additive status differs from frozen reconciliation')
    for asset in final['files']:
        read_asset(root / 'frozen', Asset.model_validate(asset))
    command = [sys.executable, '-B', str(root / 'frozen/validate_reconciliation.py')]
    completed = subprocess.run(command, capture_output=True, text=True, check=True, timeout=120)
    result = json.loads(completed.stdout)
    schema = json.loads((root / 'frozen/VALIDATION_RESULT.schema.json').read_bytes())
    jsonschema.Draft202012Validator(schema).validate(result)
    if result['original_paths_checked'] is not False:
        raise ValueError('Portable validation unexpectedly depended on original paths')
    return {
        'status': 'passed', 'assignment': record.assignment,
        'portable_files_verified': manifest.file_count + 2,
        'frozen_files_preserved': record.frozen_file_count,
        'external_findings': record.findings, 'errata': record.errata,
        'unresolved_themes': record.unresolved_themes,
        'dispositions': record.dispositions,
        'historical_absolute_paths_used': False,
        'candidate_changed': False, 'legal_currentness': 'not_verified',
        'frozen_validator': result,
    }


def main() -> None:
    """Run validation from any current working directory without writing files."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    logging.info(json.dumps(validate_package(args.package.absolute()), indent=2))


if __name__ == '__main__':
    main()
