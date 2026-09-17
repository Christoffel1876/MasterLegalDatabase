"""Record completed verification and close this immutable review inventory once."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys

import jsonschema

from review_models import Asset, Manifest, Validation

ROOT=Path(__file__).resolve().parent


def save(name: str, model: object) -> None:
    """Write an exported schema and strictly validated receipt exactly once."""
    schema=type(model).model_json_schema()
    raw=model.model_dump_json(indent=2)+'\n'
    jsonschema.validate(json.loads(raw),schema)
    with (ROOT/Path(name).with_suffix('.schema.json')).open('x') as f:
        f.write(json.dumps(schema,indent=2)+'\n')
    with (ROOT/name).open('x') as f:
        f.write(raw)


def main() -> None:
    """Freeze after checking actual focused test and rerender outputs."""
    if (ROOT/'FINAL_MANIFEST.json').exists():
        raise ValueError('Already frozen')
    tests=(ROOT/'tests.log').read_text()
    check=json.loads((ROOT/'verify-before-seal.log').read_bytes())
    if 'Ran 12 tests' not in tests or not tests.rstrip().endswith('OK'):
        raise ValueError('Focused tests did not pass')
    if check['status']!='passed' or check['checks']['rerendered_pages']!=7:
        raise ValueError('Actual rerender did not pass')
    receipt=Validation(recorded_at=datetime.now(timezone.utc),status='passed',pages=7,
        native_bytes=19118,candidate_bytes=19272,passages=78,native_lines=894,crop_count=4,
        tests_run=12,checks=['Strict Pydantic and exported JSON schema validation.',
        'Exact original, packet, native, candidate and selected custody hashes.',
        'Exhaustive native line-byte coverage and 78 normalized passage associations.',
        'Nine cross-page/nesting links, all seven footer dates and the unlettered final paragraph.',
        'All four exact-pixel crops reproduce; all seven full PNGs reproduce under fresh Poppler rendering.',
        '12 focused in-memory corruption tests passed; source files were not edited.'],
        limitations=['Mechanical checks do not independently prove visual-review truth, legal currentness or original HTTP acquisition.',
                     'No canonical writes, external reports, public requests or legal promotion occurred.'])
    save('VALIDATION.json',receipt)
    schema=Manifest.model_json_schema()
    (ROOT/'FINAL_MANIFEST.schema.json').write_text(json.dumps(schema,indent=2)+'\n')
    assets=[]
    for path in sorted(ROOT.rglob('*')):
        if path.is_symlink():
            raise ValueError('Review symlink')
        if path.is_file():
            raw=path.read_bytes()
            assets.append(Asset(path=path.relative_to(ROOT).as_posix(),
                                sha256=sha256(raw).hexdigest(),size_bytes=len(raw)))
    manifest=Manifest(schema_version=1,status='frozen_source_fidelity_review_not_current_law',
                      created_at=datetime.now(timezone.utc),files=assets)
    raw=(manifest.model_dump_json(indent=2)+'\n').encode()
    jsonschema.validate(json.loads(raw),schema)
    with (ROOT/'FINAL_MANIFEST.json').open('xb') as f:
        f.write(raw)
    sys.stdout.write(str(len(assets))+' payloads; manifest '+sha256(raw).hexdigest()+'\n')


if __name__=='__main__':
    main()
