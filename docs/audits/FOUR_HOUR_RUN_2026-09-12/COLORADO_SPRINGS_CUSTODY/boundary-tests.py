"""Boundary checks for the frozen, read-only Colorado Springs scope verifier."""
from pathlib import Path
import importlib.util
import hashlib
import json
import shutil
import sys
import pytest

SOURCE = Path(__file__).parent / "colorado-springs-fire-fees-source-review"
spec = importlib.util.spec_from_file_location("fire_scope_validator", SOURCE / "validate_scope.py")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def test_exact_scope_is_read_only():
    before = {p.relative_to(SOURCE): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in SOURCE.rglob("*") if p.is_file()}
    result = module.validate(SOURCE)
    assert result["sources"] == 2 and result["pages"] == 14
    assert result["white_text_regions"] == 8 and result["selected_passages"] == 7
    assert result["complete_table_qa"] is False
    assert before == {p.relative_to(SOURCE): hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in SOURCE.rglob("*") if p.is_file()}


@pytest.mark.parametrize("damage", ["source", "native", "image", "scope", "scope_rehashed",
                                     "header", "extra", "symlink", "missing"])
def test_custody_damage_rejected(tmp_path, damage):
    copied = tmp_path / "packet"
    shutil.copytree(SOURCE, copied)
    target = {
        "source": "SD014-01/original.pdf", "native": "SD014-02/page-0007.txt",
        "image": "SD014-02/page-0001.png", "scope": "SOURCE_SCOPE.json",
        "scope_rehashed": "SOURCE_SCOPE.json", "header": "acquisition/SD014-02/public-headers.json",
        "extra": "extra.txt", "symlink": "SD014-02/page-0007.txt",
        "missing": "SD014-01/page-0001.txt",
    }[damage]
    path = copied / target
    if damage == "symlink":
        path.unlink()
        path.symlink_to(SOURCE / target)
    elif damage == "missing":
        path.unlink()
    else:
        path.write_bytes(path.read_bytes() + b" " if path.exists() else b"extra")
        if damage == "scope_rehashed":
            inv = json.loads((copied / "FINAL_MANIFEST.json").read_bytes())
            ref = next(r for r in inv["files"] if r["path"] == target)
            ref.update(sha256=hashlib.sha256(path.read_bytes()).hexdigest(), size_bytes=path.stat().st_size)
            (copied / "FINAL_MANIFEST.json").write_text(json.dumps(inv))
    with pytest.raises((ValueError, FileNotFoundError)):
        module.validate(copied)
