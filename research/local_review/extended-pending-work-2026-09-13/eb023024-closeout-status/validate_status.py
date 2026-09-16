"""Read-only portable closeout custody verification, without source-content review."""
import hashlib
import json
import sys
from pathlib import Path
from models import Manifest, Receipt, RootObservation


def digest(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def asset(root, value):
    name = Path(value['path'])
    if name.is_absolute() or '..' in name.parts:
        raise ValueError('Unsafe evidence path')
    path = root
    for part in name.parts:
        path = path / part
        if path.is_symlink():
            raise ValueError('Linked evidence')
    if not path.is_file() or path.stat().st_size != value['size_bytes']:
        raise ValueError('Evidence type/size differs')
    if digest(path) != value['sha256']:
        raise ValueError('Evidence digest differs')
    return path


def main():
    root = Path(__file__).resolve().parent
    manifest = Manifest.model_validate_json((root / 'FINAL_MANIFEST.json').read_bytes())
    expected = {x.path for x in manifest.files} | {'FINAL_MANIFEST.json'}
    actual = set()
    for path in root.rglob('*'):
        if path.is_symlink() or not (path.is_file() or path.is_dir()):
            raise ValueError('Nonordinary member')
        if path.is_file():
            actual.add(path.relative_to(root).as_posix())
    if expected != actual or len(expected) != len(manifest.files) + 1:
        raise ValueError('Closed membership differs')
    for item in manifest.files:
        asset(root, item.model_dump())
    receipt = Receipt.model_validate_json((root / 'STATUS_RECEIPT.json').read_bytes())
    RootObservation.model_validate_json((root / 'ROOT_UI_OBSERVATION.json').read_bytes())
    for model, name in [(Receipt, 'STATUS_RECEIPT'), (Manifest, 'FINAL_MANIFEST'),
                        (RootObservation, 'ROOT_UI_OBSERVATION')]:
        if json.loads((root / (name + '.schema.json')).read_bytes()) != model.model_json_schema():
            raise ValueError('Stored schema differs')
    for item in receipt.retained_files:
        asset(root, item.model_dump())
    if len(receipt.original_files) != 61 or len(receipt.retained_files) != 61:
        raise ValueError('Delivery count differs')
    for old, retained in zip(receipt.original_files, receipt.retained_files):
        if (old.sha256, old.size_bytes) != (retained.sha256, retained.size_bytes):
            raise ValueError('Exact copied delivery identity differs')
    for document in receipt.documents:
        for check in document.checks:
            if not check.matches or check.expected_sha256 != check.actual_sha256:
                raise ValueError('Expected hash mismatch recorded')
            if digest(root / check.evidence_path) != check.actual_sha256:
                raise ValueError('Delivered binding differs')
        if not (document.reported_pass1_freeze_at < document.reported_candidate_release_at
                < document.reported_completion_at):
            raise ValueError('Claimed chronology differs')
    if digest(root / 'packet/MANIFEST.json') != receipt.packet_manifest_sha256:
        raise ValueError('Original packet manifest differs')
    sys.stdout.write(json.dumps({'status': 'passed', 'worker_documents_complete': 2,
        'worker_documents_pending': 0, 'pending_atlas_verification': 2,
        'copied_delivery_files': 61, 'verified_bindings': 52,
        'methods': 'caption-mediated; historical reopening declared, not independently witnessed',
        'network_requests': 0}) + '\n')


if __name__ == '__main__':
    main()
