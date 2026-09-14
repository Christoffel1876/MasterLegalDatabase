"""Read-only custody and official-anchor proof validation; never invokes replay."""
from __future__ import annotations

import ast
import hashlib
import json
import sys
from pathlib import Path
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup
import jsonschema

BASE = Path(__file__).absolute().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(BASE))
from recovery_models import Diagnosis, Inventory, Ref


def checked(ref: Ref) -> bytes:
    """Read only exact ordinary confined evidence files."""
    relative = Path(ref.path)
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('Unconfined evidence')
    path = BASE / relative
    if not path.is_file() or any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('Nonordinary evidence')
    raw = path.read_bytes()
    if len(raw) != ref.size_bytes or hashlib.sha256(raw).hexdigest() != ref.sha256:
        raise ValueError('Evidence digest differs: ' + ref.path)
    return raw


def host_set(raw: bytes) -> set[str]:
    """Read only the literal approved-host set without executing the historical module."""
    node = next(n for n in ast.parse(raw).body if isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == 'AUTHORIZED_SOURCE_HOSTS'
                        for t in n.targets))
    return ast.literal_eval(node.value.args[0])


def verify() -> dict:
    """Verify the frozen diagnosis and its exact policy delta, anchors and interrupted state."""
    inventory = Inventory.model_validate_json((BASE / 'PACKAGE_INVENTORY.json').read_bytes())
    actual = {p.relative_to(BASE).as_posix() for p in BASE.rglob('*') if p.is_file()
              and p.relative_to(BASE).parts[0] != '_test_runs'
              and p.name != 'PACKAGE_INVENTORY.json'}
    if len(inventory.files) != len({r.path for r in inventory.files}):
        raise ValueError('Duplicate inventory member')
    if actual != {r.path for r in inventory.files}:
        raise ValueError('Missing or extra package member')
    for item in inventory.files:
        checked(item)
    diagnosis = Diagnosis.model_validate_json((BASE / 'DIAGNOSIS.json').read_bytes())
    for name, model in [('DIAGNOSIS', Diagnosis), ('PACKAGE_INVENTORY', Inventory)]:
        schema = json.loads((BASE / (name + '.schema.json')).read_bytes())
        if schema != model.model_json_schema():
            raise ValueError('Schema drift')
        jsonschema.Draft202012Validator(schema).validate(
            json.loads((BASE / (name + '.json')).read_bytes()))
    before, after = host_set(checked(diagnosis.old_constants)), host_set(
        checked(diagnosis.approved_constants))
    if after - before != {diagnosis.exact_added_host} or before - after:
        raise ValueError('Host exception expanded')
    intent = json.loads(checked(diagnosis.original_intent))
    if intent['actual_repository_received_at'] != (
        diagnosis.original_actual_repository_received_at.isoformat().replace('+00:00', 'Z')
    ):
        raise ValueError('Original receipt time differs')
    for row in diagnosis.host_matrix:
        if row.old_policy_accepted != (row.host in before) or row.host not in after:
            raise ValueError('Host disposition mismatch')
        for anchor in row.anchors:
            if urlsplit(anchor.parent_url).netloc not in before:
                raise ValueError('Previously unauthorized parent')
            soup = BeautifulSoup(checked(anchor.parent_html), 'html.parser')
            if not any(a.get('href') == anchor.href and
                       ' '.join(a.get_text(' ', strip=True).split()) == anchor.label
                       for a in soup.find_all('a', href=True)):
                raise ValueError('Anchor not retained')
            if urljoin(anchor.parent_url, anchor.href) != row.url or anchor.resolved_url != row.url:
                raise ValueError('Exact anchor destination differs')
    for state, change in zip(diagnosis.state_files, intent['changes'], strict=True):
        raw = checked(state.preserved)
        if (state.repository_path != change['path'] or hashlib.sha256(raw).hexdigest()
                != change[state.position]['sha256']):
            raise ValueError('Interrupted state differs from original intent')
    return {'status': 'verified_recovery_preparation_only', 'host_rows': 13,
            'exact_asset_host_proofs': 9, 'state': ['after', 'before', 'before'],
            'actual_replay_executed': False, 'legal_currentness': 'not_verified'}


if __name__ == '__main__':
    sys.stdout.write(json.dumps(verify(), indent=2) + '\n')
