"""Prepare the bounded final scanner using only root-reviewed identity additions."""
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json
import sys

import jsonschema
from pydantic import BaseModel, ConfigDict, Field

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
REPO = BASE.parents[1]/'MasterLegalDatabase'


class Ref(BaseModel):
    """Exact approved repository payload identity."""

    model_config = ConfigDict(extra='forbid', strict=True)
    path: str
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    size_bytes: int = Field(ge=0)


class Approval(BaseModel):
    """Frozen accepted-wrapper set and final CI installation pins."""

    model_config = ConfigDict(extra='forbid', strict=True)
    recorded_at: str
    inherited_scan: Ref
    scanner_decision: Ref
    wrappers: list[Ref]
    installation: Ref
    installation_schema: Ref
    legal_currentness: str


def ref(path: Path, relative: Path = REPO) -> Ref:
    """Hash actual bytes without substituting for a supplied expected digest."""
    data = path.read_bytes()
    return Ref(path=path.relative_to(relative).as_posix(), sha256=sha256(data).hexdigest(),
               size_bytes=len(data))


def require(path: Path, expected_hash: str, size: int | None = None) -> Ref:
    """Compare actual local bytes with an independently supplied root pin."""
    found = ref(path)
    if found.sha256 != expected_hash or (size is not None and found.size_bytes != size):
        raise ValueError('Expected root pin differs: '+found.path)
    return found


def main() -> None:
    """Produce strict approvals and adapted code once; do not execute the scanner."""
    original = (HERE/'REVIEWED_SCANNER.py').read_bytes()
    if sha256(original).hexdigest() != '6970412367b108fda28516ecdf27c3e8a4467ebd58180475103facd1c5499194':
        raise ValueError('Reviewed scanner differs')
    prior_path = BASE/'plato-packaging-scan-audit/proposed-runs/reviewed-current-no-staging/SCAN.json'
    prior_raw = prior_path.read_bytes()
    if sha256(prior_raw).hexdigest() != 'cb6b6e42115eb8df248c26ae6509c24983b361790c3c0f89e1b51d8a25ba08fa':
        raise ValueError('Inherited scan differs')
    prior = json.loads(prior_raw)
    wrappers = []
    for item in prior['files']:
        if 'closed wrapper inventory' in item['basis']:
            wrappers.append(require(REPO/item['path'], item['sha256'], item['size_bytes']))
    if len(wrappers) != 19:
        raise ValueError('Expected nineteen inherited wrappers')
    added = REPO/'research/local_review/git-packaging-scanner-audit-2026-09-13'
    decision = require(added/'DECISION.json',
                       'd06b3b87dfc0fe6a8ae22031d59fff9b75f9071ea0862399f1c29728b36cf222')
    wrappers.append(ref(added/'INVENTORY.json'))
    ci = REPO/'research/local_review/manual-watch-ci-integration-2026-09-13'
    wrappers.append(require(ci/'INVENTORY.json',
                            '988546abc8c4e68ba925c1599f313976d7f53faf49999188354f15917b115c39',
                            111618))
    receipt = require(ci/'INSTALLATION.json',
                      '5a9e25492d0fe21f1a2ff44a90d705550cb1eb7b8bd9733ea627fc9257819d5b',
                      3915)
    schema = require(ci/'INSTALLATION.schema.json',
                     '0f864f0f441c1034fb14cd956703b3a5e44ca9e2d6f404dfd2e00c4ea6cbab9c',
                     2191)
    approval = Approval(recorded_at=datetime.now(timezone.utc).isoformat(),
                        inherited_scan=ref(prior_path, BASE), scanner_decision=decision,
                        wrappers=wrappers, installation=receipt, installation_schema=schema,
                        legal_currentness='not_verified')
    approval_raw = (approval.model_dump_json(indent=2)+'\n').encode()
    approval_schema = Approval.model_json_schema()
    jsonschema.validate(json.loads(approval_raw), approval_schema)
    (HERE/'APPROVALS.schema.json').write_text(json.dumps(approval_schema, indent=2)+'\n')
    with (HERE/'APPROVALS.json').open('xb') as handle:
        handle.write(approval_raw)
    approval_hash = sha256(approval_raw).hexdigest()
    code = original.decode().replace("dst=B/'plato-packaging-scan-audit'/'proposed-runs'/args.name;",
                                   "dst=B/'plato-final-packaging-scan'/'runs'/args.name;")
    old = " if rel in ['docs/audits/PROJECT_STATUS_2026-09-09.md','geode/schemas/models 2.py']:raise ValueError('user path')"
    new = " if p.name.casefold() in {'project_status_2026-09-09.md','models 2.py'}:raise ValueError('excluded user basename')"
    if old not in code:
        raise ValueError('User-exclusion anchor absent')
    code = code.replace(old, new)
    anchor = 'wrappers=0\n'
    new = f'''approval_raw=(B/'plato-final-packaging-scan/APPROVALS.json').read_bytes()
if sha256(approval_raw).hexdigest()!='{approval_hash}':raise ValueError('approved wrapper set changed')
approval=json.loads(approval_raw)
approved_wrappers={{a['path']:(a['sha256'],a['size_bytes']) for a in approval['wrappers']}}
if len(approved_wrappers)!=21:raise ValueError('expected exactly twenty-one approved wrappers')
observed_wrappers=set()
wrappers=0
'''
    code = code.replace(anchor, new, 1)
    old = " root=inv.parent;inv_raw=inv.read_bytes();obj=json.loads(inv_raw);"
    new = """ wrapper_rel=inv.relative_to(R).as_posix()
 if wrapper_rel not in approved_wrappers:raise ValueError('wrapper not explicitly reviewed '+wrapper_rel)
 observed_wrappers.add(wrapper_rel)
 root=inv.parent;inv_raw=inv.read_bytes()
 if (sha256(inv_raw).hexdigest(),len(inv_raw))!=approved_wrappers[wrapper_rel]:raise ValueError('approved wrapper inventory differs')
 obj=json.loads(inv_raw);"""
    if old not in code:
        raise ValueError('Wrapper anchor absent')
    code = code.replace(old, new, 1)
    anchor = '# Previously independently reviewed exact ignored candidates retain their published hashes.'
    code = code.replace(anchor, "if observed_wrappers!=set(approved_wrappers):raise ValueError('approved wrapper absent')\n"+anchor, 1)
    code = code.replace("if (R/ci).exists():", "if not (R/ci).is_file():raise ValueError('reviewed CI installation absent')\nif (R/ci).exists():", 1)
    anchor = " d=bound_json(ci);ci_schema=bound_json(ci.removesuffix('.json')+'.schema.json')"
    new = """ for pin in [approval['installation'],approval['installation_schema']]:
  if expected_identities.get(pin['path'])!=(pin['sha256'],pin['size_bytes']):raise ValueError('final CI receipt/schema pin differs')
 d=bound_json(ci);ci_schema=bound_json(ci.removesuffix('.json')+'.schema.json')"""
    code = code.replace(anchor, new, 1)
    with (HERE/'FINAL_SCANNER.py').open('x') as handle:
        handle.write(code)
    sys.stdout.write('Prepared exact twenty-one-wrapper scanner; not run by builder.\n')


if __name__ == '__main__':
    main()
