"""Record the scoped independent maintained-policy check; never requests a URL."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict
from models import Asset, URLS

HERE = Path(__file__).absolute().parent
REPO = HERE.parents[2] / 'MasterLegalDatabase'
sys.dont_write_bytecode = True
sys.path.insert(0, str(REPO))
from geode.constants import AUTHORIZED_SOURCE_HOSTS
from geode.schemas.validators import require_official_source_url


class PolicyReview(BaseModel):
    """Local code review/probe receipt; prior suite counts remain root-attributed."""
    model_config = ConfigDict(extra='forbid', strict=True)
    recorded_at: AwareDatetime
    reviewer: Literal['Popper']
    status: Literal['no_blocker_in_new_path_scoped_branch']
    copied_root_decision: Asset
    copied_root_inventory: Asset
    copied_policy_subset: list[Asset]
    accepted_exact_urls: list[str]
    rejected_probe_urls: list[str]
    root_reported_focused_tests: Literal[126]
    root_tests_independently_rerun: Literal[False]
    limitations: list[str]
    public_requests: Literal[0]
    canonical_changes: Literal[0]


def main() -> None:
    if (HERE / 'POLICY_REVIEW.json').exists():
        raise ValueError('Policy receipt already frozen')
    prior = REPO / 'research/local_review/chaffee-publisher-policy-2026-09-13'
    copied = []
    names = ['DECISION.json', 'DECISION.schema.json', 'INVENTORY.json', 'INVENTORY.schema.json']
    names += ['maintained-code-at-decision/' + n for n in
              ('constants.py', 'validators.py', 'test_chaffee_source_path.py')]
    for name in names:
        body = (prior / name).read_bytes()
        path = HERE / 'inputs/policy-subset' / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            raise ValueError('Refuse overwrite')
        temp = path.with_name(path.name + '.tmp'); temp.write_bytes(body); os.replace(temp, path)
        copied.append(Asset(path=path.relative_to(HERE).as_posix(),
                            sha256=hashlib.sha256(body).hexdigest(), size_bytes=len(body)))
    if copied[0].sha256 != 'ab02a886a3f9dd801db64f75483e21b8efdb966676d8fc1700ead9fb4c490350':
        raise ValueError('root policy decision changed')
    for name, code in [('geode/constants.py', 'constants.py'),
                       ('geode/schemas/validators.py', 'validators.py')]:
        retained = prior / 'maintained-code-at-decision' / code
        if (REPO / name).read_bytes() != retained.read_bytes():
            raise ValueError('maintained code differs from root decision')
    for url in URLS.values():
        if require_official_source_url(url) != url:
            raise ValueError('actual URL changed')
    rejected = [
        'https://cms2.revize.com/revize/chaffeecounty-other/a.pdf',
        'https://cms2.revize.com/revize/chaffeecounty/%2e%2e/other/a.pdf',
        'https://cms2.revize.com/revize/chaffeecounty/%252e%252e/other/a.pdf',
        'https://cms2.revize.com/revize/chaffeecounty/%5cother.pdf',
        'https://cms2.revize.com:443/revize/chaffeecounty/a.pdf',
        'https://x@cms2.revize.com/revize/chaffeecounty/a.pdf',
        'https://cms2.revize.com/revize/anothercounty/a.pdf',
        'https://cms2.revize.com/revize/chaffeecounty/a%00.pdf',
    ]
    for url in rejected:
        try:
            require_official_source_url(url)
        except ValueError:
            continue
        raise ValueError('unsafe probe URL admitted')
    if 'cms2.revize.com' in AUTHORIZED_SOURCE_HOSTS:
        raise ValueError('unintended shared-host approval')
    value = PolicyReview(
        recorded_at=datetime.now(timezone.utc), reviewer='Popper',
        status='no_blocker_in_new_path_scoped_branch', copied_root_decision=copied[0],
        copied_root_inventory=copied[2], copied_policy_subset=copied,
        accepted_exact_urls=list(URLS.values()), rejected_probe_urls=rejected,
        root_reported_focused_tests=126, root_tests_independently_rerun=False,
        limitations=[
            'Read-only review of the actual constants/validator diff and root tests; two '
            'exact positive URLs plus eight independent refusal probes passed locally.',
            'This review is scoped to the new exact-netloc/tenant-path branch, not a global '
            'audit of historical host rules or a crawler/HTTP redirect authorization.',
            'The policy subset omits root preimages and its redundant retrieval copy. The '
            'complete public retrieval packet is retained separately at inputs/retrieval/. '
            'The full external policy INVENTORY is bound, but is not claimed fully copied.',
            'Root reports 126 relevant tests passed; these were read rather than rerun here. '
            'Transaction tests and live preflight are recorded independently in VALIDATION.',
        ], public_requests=0, canonical_changes=0,
    )
    raw = value.model_dump_json(indent=2).encode() + b'\n'
    PolicyReview.model_validate_json(raw)
    temp = HERE / 'POLICY_REVIEW.tmp'; temp.write_bytes(raw)
    os.replace(temp, HERE / 'POLICY_REVIEW.json')
    (HERE / 'POLICY_REVIEW.schema.json').write_text(
        json.dumps(PolicyReview.model_json_schema(), indent=2) + '\n')
    print(hashlib.sha256(raw).hexdigest())


if __name__ == '__main__':
    main()
