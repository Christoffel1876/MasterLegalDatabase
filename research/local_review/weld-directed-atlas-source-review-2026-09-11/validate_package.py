"""Validate both unchanged Weld source audits using their offline read-only verifiers."""
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
FROZEN_MANIFESTS = {
    'ordinance': 'a9eeb6eb55aac8047c9a86798bfe210a0ab46fb1d12c2f3be15977c107a34f5b',
    'ehs': '30bf267e562f2d6864a1131dd04eed1818098e86f30cbb675f530bc28ffabdc0',
}


class Strict(BaseModel):
    """Forbid coercion and unmodeled fields."""
    model_config = ConfigDict(extra='forbid', strict=True)


class Asset(Strict):
    """A confined file and exact byte identity."""
    path: str
    sha256: SHA
    size_bytes: int = Field(ge=0)

    @model_validator(mode='after')
    def confined(self) -> Asset:
        """Reject paths outside the portable package."""
        p = PurePosixPath(self.path)
        if (p.is_absolute() or '..' in p.parts or '\\' in self.path or ':' in self.path
                or p.as_posix() != self.path or self.path == '.'):
            raise ValueError('Unconfined asset path')
        return self


class SourceBinding(Strict):
    """Explicit link from an unchanged source-audit ID to its pending intake ID."""
    slug: Literal['ordinance', 'ehs']
    authority_id: Literal['CO-COUNTY-WELD']
    historical_audit_source_id: str
    pending_intake_source_id: str
    frozen_directory: str
    frozen_file_count: int
    source_pdf: Asset
    source_review: Asset
    frozen_manifest: Asset
    pages: int
    native_bytes: int
    source_role: str
    adoption_date_as_stated: str | None
    effective_date_as_stated: str | None
    role_and_date_limits: list[str]
    original_audit_id_changed: Literal[False]
    legal_currentness: Literal['not_verified']


class PackageRecord(Strict):
    """Additive source-review status, separate from canonical intake and currentness."""
    schema_version: Literal[1]
    prepared_at: AwareDatetime
    status: Literal['source_reviews_complete_pending_separate_intake']
    sources: list[SourceBinding] = Field(min_length=2, max_length=2)
    frozen_files_preserved: Literal[71]
    source_pages: Literal[8]
    native_bytes_preserved: Literal[16651]
    ordinance_observations: Literal[18]
    ordinance_source_dates: Literal[11]
    ehs_rows: Literal[137]
    ehs_groups: Literal[11]
    ehs_native_lines: Literal[313]
    ehs_printed_fee_cells: Literal[136]
    ehs_blank_fee_cells: Literal[1]
    new_visual_review_during_packaging: Literal[False]
    external_reports_consulted: Literal[False]
    all_frozen_bytes_unchanged: Literal[True]
    source_or_native_edits: Literal[False]
    canonical_intake_performed_by_this_package: Literal[False]
    legal_currentness: Literal['not_verified']
    operative_effect_verified: Literal[False]
    coverage_promoted: Literal[False]
    public_opens: Literal[0]
    historical_absolute_paths_used_for_portable_validation: Literal[False]
    limits: list[str]

    @model_validator(mode='after')
    def scope(self) -> PackageRecord:
        """Require both exact source identities and the explicit ordinance ID mapping."""
        expected = {
            'ordinance': ('weld-ordinance26-01', 'weld-ordinance-26-01-atlas-directed', 45, 5, 9284),
            'ehs': ('weld-ehs-fees-2026-atlas-directed',
                    'weld-ehs-fees-2026-atlas-directed', 26, 3, 7367),
        }
        if [s.slug for s in self.sources] != ['ordinance', 'ehs']:
            raise ValueError('Expected exactly the two ordered source audits')
        for s in self.sources:
            values = (s.historical_audit_source_id, s.pending_intake_source_id,
                      s.frozen_file_count, s.pages, s.native_bytes)
            if values != expected[s.slug] or s.frozen_directory != 'frozen/' + s.slug:
                raise ValueError('Source mapping or scope differs')
            if s.frozen_manifest.sha256 != FROZEN_MANIFESTS[s.slug]:
                raise ValueError('Frozen manifest differs')
        return self


class Inventory(Strict):
    """The complete combined package inventory, excluding its own JSON and schema."""
    schema_version: Literal[1]
    prepared_at: AwareDatetime
    files: list[Asset]
    file_count: int
    listed_bytes: int
    excludes: Literal['evidence-manifest.json,evidence-manifest.schema.json']

    @model_validator(mode='after')
    def totals(self) -> Inventory:
        """Reject duplicate paths or incorrect byte/file counts."""
        if len(self.files) != self.file_count or len({x.path for x in self.files}) != self.file_count:
            raise ValueError('File inventory differs')
        if sum(x.size_bytes for x in self.files) != self.listed_bytes:
            raise ValueError('Byte inventory differs')
        return self


def read_asset(root: Path, asset: Asset) -> bytes:
    """Verify regular-file bytes without following symlinks."""
    p = root / asset.path
    if not p.is_file() or any(x.is_symlink() for x in (p, *p.parents)):
        raise ValueError(f'Not an ordinary file: {asset.path}')
    raw = p.read_bytes()
    if len(raw) != asset.size_bytes or sha256(raw).hexdigest() != asset.sha256:
        raise ValueError(f'Byte identity differs: {asset.path}')
    return raw


def load_model(root: Path, name: str, model: type[Strict]) -> Strict:
    """Validate data with its strict model and exported JSON Schema."""
    raw = (root / f'{name}.json').read_bytes()
    schema = json.loads((root / f'{name}.schema.json').read_bytes())
    if schema != model.model_json_schema():
        raise ValueError('Schema differs')
    value = model.model_validate_json(raw)
    jsonschema.Draft202012Validator(schema).validate(json.loads(raw))
    return value


def validate_package(root: Path) -> dict[str, object]:
    """Check unchanged copies, then invoke the two existing read-only verifier modes."""
    inventory = load_model(root, 'evidence-manifest', Inventory)
    actual = set()
    for p in root.rglob('*'):
        if p.is_symlink():
            raise ValueError('Symlink in package')
        if p.is_file() and '__pycache__' not in p.parts:
            actual.add(p.relative_to(root).as_posix())
    actual -= {'evidence-manifest.json', 'evidence-manifest.schema.json'}
    if actual != {x.path for x in inventory.files}:
        raise ValueError('Package inventory missing or extra files')
    for asset in inventory.files:
        read_asset(root, asset)
    record = load_model(root, 'package-record', PackageRecord)
    for s in record.sources:
        manifest = json.loads(read_asset(root, s.frozen_manifest))
        jsonschema.Draft202012Validator(json.loads(
            (root / s.frozen_directory / 'FINAL_MANIFEST.schema.json').read_bytes())).validate(manifest)
        subroot = root / s.frozen_directory
        expected = {x['path'] for x in manifest['files']}
        expected |= {'FINAL_MANIFEST.json', 'FINAL_MANIFEST.schema.json'}
        present = {p.relative_to(subroot).as_posix() for p in subroot.rglob('*')
                   if p.is_file() and '__pycache__' not in p.parts}
        if present != expected or len(present) != s.frozen_file_count:
            raise ValueError('Frozen input files differ')
        for asset in manifest['files']:
            read_asset(subroot, Asset.model_validate(asset))
        qa = json.loads(read_asset(root, s.source_review))
        if qa['source_id'] != s.historical_audit_source_id:
            raise ValueError('Historical source identity was changed')
        read_asset(root, s.source_pdf)
    commands = {
        'ordinance': [sys.executable, '-B', str(root / 'frozen/ordinance/validate_source_review.py')],
        'ehs': [sys.executable, '-B', str(root / 'frozen/ehs/build_review.py'), '--verify'],
    }
    results = {}
    for key, command in commands.items():
        run = subprocess.run(command, capture_output=True, text=True, check=True, timeout=120)
        output = run.stdout if run.stdout.strip() else run.stderr
        # The unchanged EHS verifier uses logging.warning; its JSON follows the logging prefix.
        results[key] = json.loads(output[output.index('{'):])
        if results[key]['status'] != 'passed' or results[key]['legal_currentness'] != 'not_verified':
            raise ValueError('Child verifier did not preserve status/currentness')
    if results['ordinance']['original_paths_checked'] is not False:
        raise ValueError('Portable verification used historical input paths')
    if (results['ehs']['rows'], results['ehs']['groups'], results['ehs']['native_bytes'],
            results['ehs']['native_lines'], results['ehs']['printed_fee_cells'],
            results['ehs']['blank_fee_cells']) != (137, 11, 7367, 313, 136, 1):
        raise ValueError('EHS scope differs from frozen review')
    return {
        'status': 'passed', 'portable_files_verified': inventory.file_count + 2,
        'frozen_files_preserved': 71, 'source_pages': 8, 'native_bytes': 16651,
        'historical_absolute_paths_used': False, 'source_or_native_changed': False,
        'canonical_intake_performed': False, 'legal_currentness': 'not_verified',
        'source_verifiers': results,
    }


def main() -> None:
    """Run offline package validation from any working directory without writes."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    logging.info(json.dumps(validate_package(args.package.absolute()), indent=2))


if __name__ == '__main__':
    main()
