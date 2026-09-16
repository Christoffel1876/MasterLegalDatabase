"""Validate the portable discovery copy with six explicit header exclusions."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import logging
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import jsonschema
from pydantic import BaseModel, ConfigDict, Field, model_validator

BASE = Path(__file__).resolve().parent
FROZEN = BASE / 'frozen'
EXPECTED_HEADER_IDS = {'E004', 'E005', 'E007', 'E008', 'E009', 'E011'}
EXPECTED_FINAL_SHA = 'ac6be3540538777548338de819f4ee03b55d85bd4ca347272247a4fcdb5af547'


class Strict(BaseModel):
    """Disallow fields outside this package's declared contract."""

    model_config = ConfigDict(extra='forbid')


class FileRecord(Strict):
    """Identify exact distributed bytes."""

    path: str
    sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    bytes: int = Field(ge=0)


class Redaction(Strict):
    """Bind an omitted header original to a visibly redacted derivative."""

    event_id: str
    original_path: str
    original_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    original_bytes: int = Field(ge=1)
    derivative: FileRecord
    removed_field_count: Literal[3]
    fields: list[Literal['set-cookie']]
    method: Literal['replace_entire_sensitive_header_value_with_REDACTED']
    original_distributed: Literal[False] = False


class PackageRecord(Strict):
    """Describe additive packaging without changing frozen discovery outcomes."""

    schema_version: Literal[1] = 1
    package_id: Literal['mesa-grand-junction-discovery-2026-09-11']
    prepared_at: datetime
    original_handoff_path: str
    original_final_manifest_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    original_files: Literal[356]
    unchanged_original_files: Literal[350]
    omitted_original_files: Literal[6]
    header_derivatives: list[Redaction] = Field(min_length=6, max_length=6)
    acquisition_status: Literal['frozen_discovery_custody_only']
    legal_currentness: Literal['not_verified'] = 'not_verified'
    completeness: Literal['not_assessed'] = 'not_assessed'
    canonical_intake_status: Literal['not_asserted_by_this_package']
    later_review_status: Literal['not_asserted_by_this_package']
    verification_policy: list[str]
    limitations: list[str]

    @model_validator(mode='after')
    def exact_exclusions(self) -> PackageRecord:
        """Permit only the six previously identified header exclusions."""
        if {r.event_id for r in self.header_derivatives} != EXPECTED_HEADER_IDS:
            raise ValueError('unexpected header exclusions')
        for row in self.header_derivatives:
            if row.original_path != f'events/{row.event_id}/headers.txt':
                raise ValueError('unexpected original header path')
            if row.derivative.path != f'redacted/{row.event_id}/headers.redacted.txt':
                raise ValueError('unexpected derivative header path')
            if row.fields != ['set-cookie']:
                raise ValueError('unexpected header field classes')
        if self.original_final_manifest_sha256 != EXPECTED_FINAL_SHA:
            raise ValueError('wrong frozen discovery manifest')
        if self.prepared_at.tzinfo is None:
            raise ValueError('aware packaging time required')
        return self


class Inventory(Strict):
    """Bind all distributed files except the inventory itself."""

    schema_version: Literal[1] = 1
    package_id: Literal['mesa-grand-junction-discovery-2026-09-11']
    created_at: datetime
    excluded_self: Literal['evidence-manifest.json'] = 'evidence-manifest.json'
    files: list[FileRecord]


def sha256(path: Path) -> str:
    """Stream a file digest."""
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(chunk)
    return result.hexdigest()


def safe(path: str) -> Path:
    """Read only files confined to this package without symlink ancestors."""
    relative = Path(path)
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('unsafe package path')
    result = BASE / relative
    for component in (result, *result.parents):
        if component.is_symlink():
            raise ValueError('symlink in package path')
        if component == BASE:
            break
    if not result.is_file():
        raise ValueError(f'missing package file: {path}')
    return result


def check_file(record: FileRecord) -> None:
    """Verify one exact file binding."""
    path = safe(record.path)
    if path.stat().st_size != record.bytes or sha256(path) != record.sha256:
        raise ValueError(f'file hash or size mismatch: {record.path}')


def validate() -> dict:
    """Run portable custody checks and the unchanged frozen semantic verifier."""
    if not __debug__:
        raise RuntimeError('run without -O; the frozen validator uses assertions')
    package = PackageRecord.model_validate_json(safe('package-record.json').read_text())
    inventory = Inventory.model_validate_json(safe('evidence-manifest.json').read_text())
    for instance, schema in [('package-record.json', 'package-record.schema.json'),
                             ('evidence-manifest.json', 'evidence-manifest.schema.json')]:
        jsonschema.validate(json.loads(safe(instance).read_text()),
                            json.loads(safe(schema).read_text()))
    paths = [row.path for row in inventory.files]
    if len(set(paths)) != len(paths):
        raise ValueError('duplicate package inventory path')
    for row in inventory.files:
        check_file(row)
    actual = {str(path.relative_to(BASE)) for path in BASE.rglob('*')
              if path.is_file() and '__pycache__' not in path.parts}
    if actual - {inventory.excluded_self} != set(paths):
        raise ValueError('unbound or extra package file')
    if sha256(safe('frozen/FINAL_MANIFEST.json')) != EXPECTED_FINAL_SHA:
        raise ValueError('frozen manifest changed')

    # The frozen verifier remains byte-identical. Its imports are read-only on import.
    sys.path.insert(0, str(FROZEN))
    spec = importlib.util.spec_from_file_location(
        '_atlas_frozen_mesa_validation', FROZEN / 'validate_package.py')
    if spec is None or spec.loader is None:
        raise RuntimeError('frozen verifier unavailable')
    frozen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(frozen)
    original_custody_type = frozen.Custody
    original_safe = frozen.safe
    omissions = {row.original_path: row for row in package.header_derivatives}
    original_final = original_custody_type.model_validate_json(
        safe('frozen/FINAL_MANIFEST.json').read_text())
    if len(original_final.files) + 1 != package.original_files:
        raise ValueError('wrong original source inventory count')
    for row in original_final.files:
        if row.path in omissions:
            omission = omissions[row.path]
            if row.sha256 != omission.original_sha256 or row.bytes != omission.original_bytes:
                raise ValueError('excluded original header binding mismatch')
            if (FROZEN / row.path).exists():
                raise ValueError('sensitive original header was distributed')
        else:
            check_file(FileRecord(path='frozen/' + row.path,
                                  sha256=row.sha256, bytes=row.bytes))
    copied = [path for path in FROZEN.rglob('*') if path.is_file()
              and '__pycache__' not in path.parts]
    if len(copied) != package.unchanged_original_files:
        raise ValueError('wrong unchanged original count')

    for omission in package.header_derivatives:
        check_file(omission.derivative)
        content = safe(omission.derivative.path).read_bytes()
        matches = re.findall(
            rb'(?im)^(set-cookie|cookie|authorization|proxy-authorization):([^\r\n]*)',
            content)
        if len(matches) != omission.removed_field_count:
            raise ValueError('redacted header field count mismatch')
        if any(key.lower() != b'set-cookie' or value.strip() != b'[REDACTED]'
               for key, value in matches):
            raise ValueError('unredacted sensitive header or unexpected field')

    class ScopedCustody:
        """Exclude precisely six absent originals from original byte validation."""

        @staticmethod
        def model_validate_json(text: str):
            """Keep every original custody row except declared omitted headers."""
            record = original_custody_type.model_validate_json(text)
            found = {row.path for row in record.files if row.path in omissions}
            if found != set(omissions):
                raise ValueError('original custody does not match exclusions')
            return record.model_copy(update={
                'files': [row for row in record.files if row.path not in omissions]})

    def redacted_header_safe(path: str) -> Path:
        """Route only known original-header references to marked derivatives."""
        if path in omissions:
            return safe(omissions[path].derivative.path)
        return original_safe(path)

    # No source/report/native bytes, hash functions, sizes or meanings are replaced.
    frozen.Custody = ScopedCustody
    frozen.safe = redacted_header_safe
    try:
        semantic = frozen.validate()
    finally:
        frozen.Custody = original_custody_type
        frozen.safe = original_safe
    if semantic.checked_files != 347:
        raise ValueError('unexpected scoped frozen validation count')
    return {
        'passed': True,
        'validated_at': datetime.now(timezone.utc).isoformat(),
        'distributed_files': len(paths) + 1,
        'unchanged_original_files': len(copied),
        'omitted_sensitive_original_headers': len(omissions),
        'redacted_header_derivatives': len(omissions),
        'frozen_semantic_validation': semantic.model_dump(mode='json'),
        'legal_currentness': package.legal_currentness,
        'completeness': package.completeness,
        'note': ('Original sensitive header hashes are declarations bound to frozen custody; '
                 'their omitted bytes cannot be recomputed here. All distributed bytes are '
                 'verified; redacted headers retain status and Location for semantic checks.'),
    }


if __name__ == '__main__':
    logging.warning(json.dumps(validate(), indent=2))
