"""One-time closeout after successful direct review and read-only verification."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

import jsonschema
from prepare import ROOT, DELIVERY, Inputs, asset
from role_models import Manifest, Review
from check_failures import Checks
from verify import verify_content, verify_closed


def main() -> None:
    """Freeze exact artifacts only after validating actual checks and supplied identities."""
    if (ROOT/'FINAL_MANIFEST.json').exists(): raise ValueError('Already sealed')
    inputs=Inputs.model_validate_json((ROOT/'INPUTS.json').read_bytes())
    for source in inputs.sources:
        supplied=(DELIVERY/'raw'/f'{source.action_id}.body').read_bytes()
        if supplied!=(ROOT/source.source.path).read_bytes(): raise ValueError('Supplied source changed')
    review=Review.model_validate_json((ROOT/'ROLE_DECISIONS.json').read_bytes())
    checks=Checks.model_validate_json((ROOT/'CHECKS.json').read_bytes())
    jsonschema.validate(json.loads((ROOT/'CHECKS.json').read_bytes()),Checks.model_json_schema())
    if checks.review_sha256!=asset(ROOT/'ROLE_DECISIONS.json').sha256:
        raise ValueError('Checks do not bind final review')
    if checks.verifier_sha256!=asset(ROOT/'verify.py').sha256:
        raise ValueError('Checks do not bind final verifier')
    verify_content(ROOT,review)
    paths=sorted(p for p in ROOT.rglob('*') if p.is_file())
    manifest=Manifest(schema_version=1,package='plato-document-roles',
        sealed_at=datetime.now(timezone.utc).isoformat(),files=[asset(p) for p in paths])
    schema=Manifest.model_json_schema()
    jsonschema.validate(json.loads(manifest.model_dump_json()),schema)
    (ROOT/'FINAL_MANIFEST.schema.json').write_text(json.dumps(schema,indent=2)+'\n')
    (ROOT/'FINAL_MANIFEST.json').write_text(manifest.model_dump_json(indent=2)+'\n')
    count=verify_closed(ROOT)
    result={'status':'sealed_verified','payloads':count,'total_payload_bytes':sum(a.size_bytes for a in manifest.files),
        'role_decisions':asset(ROOT/'ROLE_DECISIONS.json').model_dump(),
        'schema':asset(ROOT/'ROLE_DECISIONS.schema.json').model_dump(),
        'manifest':asset(ROOT/'FINAL_MANIFEST.json').model_dump(),
        'verifier':asset(ROOT/'verify.py').model_dump()}
    sys.stdout.write(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
