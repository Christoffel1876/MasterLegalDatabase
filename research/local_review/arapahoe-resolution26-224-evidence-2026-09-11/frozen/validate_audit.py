"""Offline read-only integrity checks; no public requests or legal inference."""
from pathlib import Path
import argparse
import hashlib
import json
import sys

import jsonschema
import pymupdf

from audit_models import Asset, Audit, Inventory


def ordinary(root, rel):
    path = root / rel
    if Path(rel).is_absolute() or '..' in Path(rel).parts:
        raise ValueError('nonlocal file reference')
    if any(p.is_symlink() for p in [path, *path.parents]) or not path.is_file():
        raise ValueError('ordinary local file required')
    return path


def check(root, asset):
    if isinstance(asset, dict):
        asset = Asset.model_validate(asset)
    data = ordinary(root, asset.path).read_bytes()
    assert len(data) == asset.size_bytes, asset.path
    assert hashlib.sha256(data).hexdigest() == asset.sha256, asset.path
    return data


def walk_assets(value):
    if isinstance(value, dict):
        if set(value) == {'path','sha256','size_bytes'}:
            yield value
        else:
            for child in value.values():
                yield from walk_assets(child)
    elif isinstance(value,list):
        for child in value:
            yield from walk_assets(child)


def validate(root):
    inventory = Inventory.model_validate_json(ordinary(root,'evidence-manifest.json').read_bytes())
    actual = set()
    for path in root.rglob('*'):
        assert not path.is_symlink()
        if path.is_file():
            actual.add(path.relative_to(root).as_posix())
    assert actual == {a.path for a in inventory.files} | {'evidence-manifest.json'}
    for asset in inventory.files:
        check(root,asset)
    audit = Audit.model_validate_json(ordinary(root,'ACCESS_AUDIT.json').read_bytes())
    jsonschema.Draft202012Validator(json.loads(ordinary(root,'ACCESS_AUDIT.schema.json').read_bytes())).validate(audit.model_dump(mode='json'))
    for asset in walk_assets(audit.model_dump()):
        check(root,asset)
    record = json.loads(ordinary(root,'E008.json').read_bytes())
    jsonschema.Draft202012Validator(json.loads(ordinary(root,'E008.schema.json').read_bytes())).validate(record)
    for asset in record['response_files'].values():
        check(root,asset)
    assert record['http_status'] == 200 and record['curl_exit_code'] == 0
    assert record['requested_url'] == audit.events[-1].requested_url
    assert audit.subject_fee_source.sha256 == 'ce519b6fe89546cf85a77934fcbdb6b6bf08473e19c545cf4c51414e1cdcb818'
    source = check(root,audit.related_resolution_response)
    assert source == check(root,audit.related_resolution_pdf_copy)
    assert hashlib.sha256(source).hexdigest() == audit.related_resolution_sha256
    assert source.startswith(b'%PDF-') and source.rstrip().endswith(b'%%EOF')
    assert pymupdf.VersionBind == '1.28.2'
    doc = pymupdf.open(stream=source,filetype='pdf')
    assert len(doc) == 2 and not doc.is_repaired and not doc.is_encrypted
    for n in [1,2]:
        native = ordinary(root,f'resolution/page-{n:04d}.txt').read_bytes()
        assert doc[n-1].get_text('text',sort=False,flags=195).encode() == native
        image = doc[n-1].get_pixmap(matrix=pymupdf.Matrix(200/72,200/72),alpha=False).tobytes('png')
        assert image == ordinary(root,f'resolution/page-{n:04d}.png').read_bytes()
    for excerpt in audit.excerpts:
        data = check(root,excerpt.native)
        assert excerpt.source_sha256 == audit.related_resolution_sha256
        assert data[excerpt.start_byte:excerpt.end_byte_exclusive] == excerpt.exact_native.encode()
    return {'validation_passed':True,'counted_public_events':8,'distinct_observed_targets':6,
            'pdf_pages':2,'checked_excerpts':len(audit.excerpts),
            'confirmed_resolution_26_224_identity':False,'confirmed_adoption_date':None,
            'confirmed_effective_date':None,'legal_currentness':'not_verified'}


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).absolute().parent)
    args=parser.parse_args()
    sys.stdout.write(json.dumps(validate(args.root.absolute()),indent=2)+'\n')
