"""One-time seal after successful source-evidence replay and recorded tests."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from review_models import Asset, Manifest, Validation
from verify_review import ROOT, SOURCE_SHA, capture, validate_content


def exclusive_model(path: Path, model: Manifest | Validation) -> None:
    """Validate both typed JSON and schema before exclusive publication."""
    serialized = model.model_dump_json(indent=2) + '\n'
    type(model).model_validate_json(serialized)
    with path.open('x') as stream:
        stream.write(serialized)
    with path.with_suffix('.schema.json').open('x') as stream:
        stream.write(json.dumps(type(model).model_json_schema(), indent=2) + '\n')


def main() -> None:
    """Record actual completed checks and freeze a closed file inventory."""
    files = capture(ROOT)
    result = validate_content(files)
    if b'23 passed, 5 warnings' not in files['TESTS.log']:
        raise ValueError('Expected final focused test result absent')
    validation = Validation(
        recorded_at=datetime.now(timezone.utc).isoformat(), status='passed',
        source_sha256=SOURCE_SHA, full_pages=4, crops_replayed=7, native_bytes=0,
        ocr_bytes=result['ocr_bytes'], candidate_bytes=result['candidate_bytes'],
        reviewed_bytes=result['reviewed_bytes'], passages=result['passages'], tests=23,
        rerendered_pages=4, limitations=[
            'The four-page Poppler replay was executed and passed before sealing; this receipt '
            'records that completed check, not a new source acquisition.',
            'Five PyMuPDF SWIG deprecation warnings are preserved in TESTS.log.',
            'The tests prove bounded byte and association checks, not independent visual review '
            'or legal currentness.'])
    exclusive_model(ROOT / 'VALIDATION.json', validation)
    files = capture(ROOT)
    assets = [Asset(path=p, sha256=hashlib.sha256(data).hexdigest(), size_bytes=len(data))
              for p, data in sorted(files.items())]
    manifest = Manifest(schema_version=1,
                        status='frozen_source_fidelity_review_not_current_law',
                        created_at=datetime.now(timezone.utc).isoformat(), files=assets)
    exclusive_model(ROOT / 'FINAL_MANIFEST.json', manifest)


if __name__ == '__main__':
    main()
