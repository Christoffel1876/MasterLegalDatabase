"""Read-only checks of the closed inventory proposal; optional live canonical evidence replay."""
import argparse
import ast
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import jsonschema

from models import Manifest, Preparation

BASE = Path(__file__).resolve().parent


def require(value: bool, message: str) -> None:
    """Refuse mismatched evidence even under optimized Python."""
    if not value:
        raise ValueError(message)


def sha(data: bytes) -> str:
    """Hash exactly the consumed data."""
    return hashlib.sha256(data).hexdigest()


def capture() -> dict[str, bytes]:
    """Read finite ordinary files without following links or historical absolute paths."""
    require(not any(p.is_symlink() for p in [BASE, *BASE.parents]), 'Unsafe preparation root')
    buffers = {}
    for path in sorted(BASE.rglob('*')):
        require(not path.is_symlink(), 'Symlinked preparation member')
        if path.is_dir():
            continue
        require(path.is_file() and path.stat().st_size < 40_000_000, 'Unsafe preparation member')
        buffers[path.relative_to(BASE).as_posix()] = path.read_bytes()
    require(sum(map(len, buffers.values())) < 100_000_000, 'Preparation byte cap')
    return buffers


def checked(buffers: dict[str, bytes], ref: Any) -> bytes:
    """Return a captured hash-bound artifact."""
    if hasattr(ref, 'model_dump'):
        ref = ref.model_dump()
    path = ref['path']
    require(not Path(path).is_absolute() and '..' not in Path(path).parts,
            'Unsafe preparation reference')
    require(path in buffers, 'Missing preparation artifact')
    data = buffers[path]
    require(sha(data) == ref['sha256'] and len(data) == ref['size_bytes'],
            'Changed preparation artifact: ' + path)
    return data


def verify(repository: Path | None = None) -> dict[str, Any]:
    """Prove exact old-row preservation and the fixed three-schema addition."""
    buffers = capture()
    manifest = Manifest.model_validate_json(buffers['FINAL_MANIFEST.json'])
    require(json.loads(buffers['FINAL_MANIFEST.schema.json']) == Manifest.model_json_schema(),
            'Manifest schema differs')
    names = {ref.path for ref in manifest.files}
    actual = {name for name in buffers if not name.startswith('execution/')}
    require(len(names) == len(manifest.files)
            and actual == names | {'FINAL_MANIFEST.json', 'FINAL_MANIFEST.schema.json'},
            'Closed preparation inventory differs')
    for ref in manifest.files:
        checked(buffers, ref)
    prep = Preparation.model_validate_json(buffers['PREPARATION.json'])
    require(json.loads(buffers['PREPARATION.schema.json']) == Preparation.model_json_schema(),
            'Preparation schema differs')
    plan = json.loads(buffers['proposed/join-plan.json'])
    old_plan = json.loads(buffers['preimages/join-plan.json'])
    new = json.loads(buffers['proposed/inventory.json'])
    old = json.loads(buffers['preimages/inventory.json'])
    jsonschema.validate(plan, json.loads(buffers['preimages/join-plan.schema.json']))
    jsonschema.validate(new, json.loads(buffers['proposed/inventory.schema.json']))
    require((len(new['sources']), new['rows_with_review'], new['rows_without_review'])
            == (69, 33, 36), 'Proposed counts differ')
    require((len(old['sources']), old['rows_with_review'], old['rows_without_review'])
            == (67, 30, 37), 'Historical counts differ')
    require(plan['authorities'][:67] == old_plan['authorities']
            and len(plan['authorities']) == 69, 'Old authority joins changed')
    require(plan['reviews'][:30] == old_plan['reviews'] and len(plan['reviews']) == 33,
            'Old review joins changed')
    for before, after in zip(old['sources'], new['sources'][:67], strict=True):
        if before['record_id'] == prep.only_old_row_with_new_review:
            require(before['reviews'] is None and len(after['reviews']) == 1,
                    'Old IWUIC review scope differs')
            after = {**after, 'reviews': None, 'review_status': 'metadata_only_review_unknown'}
        require(after == before, 'Prior custody/source metadata changed')
    require(new['unchanged_legacy_ledger'] == old['unchanged_legacy_ledger'],
            'Legacy ledger binding changed')
    require(new['manual_manifest'] == prep.raw_manifest.model_dump(), 'Raw binding differs')
    expected_ids = [r.source_id for r in prep.reviews]
    require([r['record_id'] for r in plan['reviews'][30:]] == expected_ids,
            'New review selection differs')
    for join, review in zip(plan['reviews'][30:], prep.reviews, strict=True):
        require(join['review'] == review.review.model_dump()
                and join['review_schema'] == review.review_schema.model_dump(),
                'Accepted review binding differs')
    trees = [ast.parse(buffers[f'{p}/manual_review_inventory.py'])
             for p in ['preimages', 'proposed']]
    allowlists = []
    for tree in trees:
        entry = next(n for n in tree.body if isinstance(n, ast.AnnAssign)
                     and isinstance(n.target, ast.Name) and n.target.id == 'ALLOWED_REVIEW_SCHEMAS')
        allowlists.append(ast.literal_eval(entry.value))
        tree.body.remove(entry)
    require(ast.dump(trees[0]) == ast.dump(trees[1]), 'Unapproved module behavior change')
    expected = {r.review_schema.sha256: 'checked_passages' for r in prep.reviews}
    require(allowlists[1] == {**allowlists[0], **expected}
            and not set(expected) & set(allowlists[0]), 'Schema allowlist change differs')
    require(b'129 passed' in checked(buffers, prep.test_log), 'Focused test result differs')
    if repository is not None:
        repository = repository.resolve()
        for ref in [prep.actual_intake_receipt, prep.raw_manifest,
                    *[a for r in prep.reviews for a in [r.acceptance, r.acceptance_schema,
                                                        r.review, r.review_schema]]]:
            path = repository / ref.path
            require(not any(p.is_symlink() for p in [path, *path.parents]), 'Linked repository input')
            raw = path.read_bytes()
            require(sha(raw) == ref.sha256 and len(raw) == ref.size_bytes,
                    'Repository evidence differs: ' + ref.path)
        sys.path.insert(0, str(repository))
        module = ModuleType('prepared_inventory')
        module.__file__ = str(BASE / 'proposed/manual_review_inventory.py')
        sys.modules[module.__name__] = module
        exec(compile(buffers['proposed/manual_review_inventory.py'], module.__file__, 'exec'),
             module.__dict__)
        original = module.safe_path
        def staged(root: Path, name: str) -> Path:
            """Redirect only the checked plan while replaying all current evidence."""
            if root == repository and name == module.PLAN.as_posix():
                return BASE / 'proposed/join-plan.json'
            return original(root, name)
        module.safe_path = staged
        rebuilt = module.build_inventory(repository)
        require(rebuilt.model_dump(mode='json') == new, 'Live inventory replay differs')
    return {'status': 'passed', 'sources': 69, 'reviewed': 33, 'unmapped': 36,
            'prior_authorities_unchanged': 67, 'prior_reviews_unchanged': 30,
            'new_schema_entries': 3, 'repository_replayed': repository is not None}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', type=Path)
    args = parser.parse_args()
    sys.stdout.write(json.dumps(verify(args.repository), sort_keys=True) + '\n')
