"""Offline verification of the closed final scan, without Git or repository access."""
from hashlib import sha256
from pathlib import Path
import json
import sys

import jsonschema

from prepare_final import Approval
from seal_models import Manifest


def main() -> None:
    """Check closure, root approvals, exact selection lists and recorded command pins."""
    root = Path(__file__).resolve().parent
    manifest = Manifest.model_validate_json((root/'FINAL_MANIFEST.json').read_bytes())
    jsonschema.validate(manifest.model_dump(mode='json'),
                        json.loads((root/'FINAL_MANIFEST.schema.json').read_bytes()))
    files = set()
    for path in root.rglob('*'):
        if path.is_symlink():
            raise ValueError('Symlink in frozen scan')
        if path.is_file():
            files.add(path.relative_to(root).as_posix())
    expected = {ref.path for ref in manifest.files}
    if len(expected) != len(manifest.files) or files != expected | {'FINAL_MANIFEST.json'}:
        raise ValueError('Frozen scan closure differs')
    for ref in manifest.files:
        path = Path(ref.path)
        if path.is_absolute() or '..' in path.parts:
            raise ValueError('Unsafe scan member')
        raw = (root/path).read_bytes()
        if (sha256(raw).hexdigest(), len(raw)) != (ref.sha256, ref.size_bytes):
            raise ValueError('Frozen member differs: '+ref.path)
    approval = Approval.model_validate_json((root/'APPROVALS.json').read_bytes())
    jsonschema.validate(approval.model_dump(mode='json'),
                        json.loads((root/'APPROVALS.schema.json').read_bytes()))
    run = json.loads((root/'RUN.json').read_bytes())
    jsonschema.validate(run, json.loads((root/'RUN.schema.json').read_bytes()))
    for field, path in [('scanner_sha256', 'FINAL_SCANNER.py'),
                        ('approvals_sha256', 'APPROVALS.json'),
                        ('stdout_sha256', 'scan.stdout.log'), ('stderr_sha256', 'scan.stderr.log')]:
        if run[field] != sha256((root/path).read_bytes()).hexdigest():
            raise ValueError('Actual command pin differs')
    if run['exit_code'] != 0 or run['git_mutations'] or run['public_requests']:
        raise ValueError('Unexpected command disposition')
    folder = root/'runs/final-ci-installed'
    scan = json.loads((folder/'SCAN.json').read_bytes())
    jsonschema.validate(scan, json.loads((folder/'SCAN.schema.json').read_bytes()))
    selected = scan['files']
    paths = [ref['path'] for ref in selected]
    force = [ref['path'] for ref in selected if ref['ignored'] and not ref['tracked']]
    if (scan['wrappers'], len(selected), len(force), scan['new_raw_originals']) != (21, 3052, 119, 6):
        raise ValueError('Final scope differs')
    if sum(ref['size_bytes'] for ref in selected) != 199789316:
        raise ValueError('Selected byte count differs')
    excluded = {'models 2.py', 'project_status_2026-09-09.md'}
    if len(paths) != len(set(paths)) or any(Path(path).name.casefold() in excluded for path in paths):
        raise ValueError('Duplicate selection or excluded user basename')
    for name, names in [('paths.nul', paths), ('force-add.nul', force)]:
        if (folder/name).read_bytes() != b'\0'.join(path.encode() for path in names)+b'\0':
            raise ValueError('Staging list differs')
    selected_by_path = {ref['path']: ref for ref in selected}
    for ref in approval.wrappers + [approval.installation, approval.installation_schema]:
        actual = selected_by_path[ref.path]
        if (actual['sha256'], actual['size_bytes']) != (ref.sha256, ref.size_bytes):
            raise ValueError('Approved identity not carried into final assets')
    sys.stdout.write('PASS: closed final scan, 21 approved wrappers, exact selection lists.\n')


if __name__ == '__main__':
    main()
