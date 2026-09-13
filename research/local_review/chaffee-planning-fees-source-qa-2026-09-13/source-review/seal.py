"""Create a closed inventory without modifying retained draft or source files."""
from pathlib import Path
import hashlib
from audit_models import Asset, Inventory

ROOT = Path(__file__).resolve().parent


def main() -> None:
    """Archive an existing inventory, then atomically write the validated successor."""
    target = ROOT / 'FINAL_MANIFEST.json'
    if target.exists():
        raw = target.read_bytes()
        old = ROOT / 'history' / (hashlib.sha256(raw).hexdigest() + '.json')
        old.parent.mkdir(exist_ok=True)
        if old.exists():
            assert old.read_bytes() == raw
        else:
            old.write_bytes(raw)
    files = []
    for path in sorted(ROOT.rglob('*')):
        if path.is_symlink():
            raise ValueError('Symlink refused')
        if not path.is_file() or path == target:
            continue
        if '__pycache__' in path.parts or '.pytest_cache' in path.parts:
            raise ValueError('Unwanted runtime cache')
        raw = path.read_bytes()
        files.append(Asset(path=path.relative_to(ROOT).as_posix(),
                           sha256=hashlib.sha256(raw).hexdigest(), size_bytes=len(raw)))
    value = Inventory(status='independent_source_audit_no_legal_promotion', files=files)
    temporary = target.with_suffix('.json.tmp')
    temporary.write_text(value.model_dump_json(indent=2) + '\n')
    temporary.replace(target)


if __name__ == '__main__':
    main()
