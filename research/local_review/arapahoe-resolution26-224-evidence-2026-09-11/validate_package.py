#!/usr/bin/env python3
"""Verify portable retained evidence with one explicit session-header exclusion."""
import argparse
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any

import jsonschema
import pymupdf

from package_models import Asset, Inventory, Status

EXCLUDED = 'http/E008.headers'
EXCLUDED_SHA = '78257b8f02bc6dee6582c744cebf7698b4b402d7bae242ba78c86d5cb2569b71'


def ordinary(root: Path, relative: str) -> Path:
    """Reject paths or symlinks escaping the selected package."""
    Asset(path=relative, sha256='0'*64, size_bytes=0)
    p = root / relative
    if any(x.is_symlink() for x in [p, *p.parents]) or not p.is_file():
        raise ValueError(f'ordinary local file required: {relative}')
    return p


def check(root: Path, value: Any, allow_header_exclusion: bool = False) -> bytes | None:
    """Verify retained bytes or acknowledge the one declared unavailable original."""
    a = Asset.model_validate(value) if isinstance(value, dict) else value
    if allow_header_exclusion and a.path == EXCLUDED:
        assert a.sha256 == EXCLUDED_SHA and a.size_bytes == 367
        assert not (root / EXCLUDED).exists()
        return None
    b = ordinary(root, a.path).read_bytes()
    assert len(b) == a.size_bytes and hashlib.sha256(b).hexdigest() == a.sha256, a.path
    return b


def validate(root: Path) -> dict[str, Any]:
    """Replay the retained source checks without pretending to hash excluded bytes."""
    inventory = Inventory.model_validate_json(ordinary(root,'evidence-manifest.json').read_bytes())
    status = Status.model_validate_json(ordinary(root,'package-status.json').read_bytes())
    for name, value in [('package-status',status), ('evidence-manifest',inventory)]:
        schema = json.loads(ordinary(root,f'{name}.schema.json').read_bytes())
        jsonschema.Draft202012Validator(schema).validate(value.model_dump(mode='json'))
    expected = [a.path for a in inventory.files]
    assert expected == sorted(set(expected))
    actual = set()
    for p in root.rglob('*'):
        assert not p.is_symlink()
        if p.is_file():
            actual.add(p.relative_to(root).as_posix())
    assert actual == set(expected) | {'evidence-manifest.json'}
    for a in inventory.files:
        check(root,a)
    frozen = root / 'frozen'
    assert status.frozen_handoff_inventory.path == 'frozen/evidence-manifest.json'
    assert status.frozen_handoff_inventory.sha256 == (
        'b267d0f32ddd1c3098faac002be05856a7a4f74292cea6ef67f03a28f6a0e414'
    )
    historical = json.loads(check(root,status.frozen_handoff_inventory))
    historical_paths = {a['path'] for a in historical['files']} | {'evidence-manifest.json'}
    included = [a for a in inventory.files if a.path.startswith('frozen/')]
    assert {a.path.removeprefix('frozen/') for a in included} == historical_paths - {EXCLUDED}
    assert len(included) == 35 and sum(a.size_bytes for a in included) == 1513543
    for a in historical['files']:
        check(frozen,a,True)
    redaction = status.redactions[0]
    assert redaction.excluded_original.path == 'frozen/' + EXCLUDED
    assert redaction.excluded_original.sha256 == EXCLUDED_SHA
    assert redaction.excluded_original.size_bytes == 367
    header = check(root,redaction.derivative)
    sensitive = [line for line in header.splitlines() if re.match(
        rb'(?i)(set-cookie|cookie|authorization|proxy-authorization|x-api-key|x-auth-token)\s*:',
        line)]
    assert sensitive == [b'Set-Cookie: [REDACTED SESSION COOKIE]']
    metrics = json.loads(ordinary(frozen,'http/E008.curl-metrics.txt').read_bytes())
    assert not any(metrics.get(k) for k in metrics if k.endswith(('.password','.user','.options')))
    # Reuse unchanged frozen types and native-asset walker; never run its capture helper.
    sys.path.insert(0,str(frozen))
    spec = importlib.util.spec_from_file_location('retained_audit_gate',frozen/'validate_audit.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    audit = module.Audit.model_validate_json(check(root,status.frozen_audit))
    schema = json.loads(ordinary(frozen,'ACCESS_AUDIT.schema.json').read_bytes())
    jsonschema.Draft202012Validator(schema).validate(audit.model_dump(mode='json'))
    for a in module.walk_assets(audit.model_dump()):
        check(frozen,a,True)
    response = json.loads(ordinary(frozen,'E008.json').read_bytes())
    schema = json.loads(ordinary(frozen,'E008.schema.json').read_bytes())
    jsonschema.Draft202012Validator(schema).validate(response)
    for a in response['response_files'].values():
        check(frozen,a,True)
    assert response['http_status'] == 200 and response['curl_exit_code'] == 0
    assert response['requested_url'] == audit.events[-1].requested_url
    assert audit.subject_fee_source.sha256 == (
        'ce519b6fe89546cf85a77934fcbdb6b6bf08473e19c545cf4c51414e1cdcb818'
    )
    source = check(frozen,audit.related_resolution_response)
    assert source == check(frozen,audit.related_resolution_pdf_copy)
    assert hashlib.sha256(source).hexdigest() == status.source_attachment_sha256
    assert source.startswith(b'%PDF-') and source.rstrip().endswith(b'%%EOF')
    assert pymupdf.VersionBind == '1.28.2'
    doc = pymupdf.open(stream=source,filetype='pdf')
    assert len(doc) == 2 and not doc.is_repaired and not doc.is_encrypted
    for n in [1,2]:
        native = ordinary(frozen,f'resolution/page-{n:04d}.txt').read_bytes()
        assert doc[n-1].get_text('text',sort=False,flags=195).encode() == native
        image = doc[n-1].get_pixmap(matrix=pymupdf.Matrix(200/72,200/72),alpha=False)
        assert image.tobytes('png') == ordinary(frozen,f'resolution/page-{n:04d}.png').read_bytes()
    for e in audit.excerpts:
        native = check(frozen,e.native)
        assert e.source_sha256 == status.source_attachment_sha256
        assert native[e.start_byte:e.end_byte_exclusive] == e.exact_native.encode()
    return {
        'validation_passed':True, 'exact_handoff_files':35,
        'excluded_original_header_hash_recomputed':False, 'redacted_header_verified':True,
        'pdf_pages_reproduced':2, 'exact_excerpts':len(audit.excerpts),
        'original_counted_public_events':8, 'new_public_access_events':0,
        'numbered_executed_resolution_confirmed':False,
        'adoption_date':None, 'effective_date':None, 'legal_currentness':'not_verified',
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).absolute().parent)
    args = parser.parse_args()
    sys.stdout.write(json.dumps(validate(args.root.absolute()),indent=2)+'\n')
