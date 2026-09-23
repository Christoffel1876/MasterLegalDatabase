"""Offline refusal tests for portable source metadata; canonical evidence stays read-only."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from scripts import verify_ccr_source_coverage as MODULE

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def index() -> Any:
    """Read the frozen proposed index into a new model for each test."""
    path = ROOT / "_CONTROL_PLANE/CCR_SOURCE_COVERAGE_2026-09-23.json"
    return MODULE.Index.model_validate_json(path.read_bytes())


@pytest.mark.parametrize("path", ["/tmp/body", "../body", "a/../b", "a//b", "a\\b"])
def test_repository_path_refusal(path: str) -> None:
    """Index assets cannot escape or ambiguously address the chosen repository."""
    with pytest.raises(ValueError, match="path"):
        MODULE.Asset(path=path, sha256="0" * 64, size_bytes=0)


def test_ordinary_reader_refuses_unavailable_and_indirect(tmp_path: Path) -> None:
    """Missing/LFS/oversized/symlink inputs cannot masquerade as available source bytes."""
    with pytest.raises(ValueError, match="Missing"):
        MODULE.ordinary(tmp_path, "absent")
    (tmp_path / "body").write_bytes(b"version https://git-lfs.github.com/spec/v1\n")
    with pytest.raises(ValueError, match="LFS"):
        MODULE.ordinary(tmp_path, "body")
    (tmp_path / "other").write_bytes(b"abcdef")
    with pytest.raises(ValueError, match="oversized"):
        MODULE.ordinary(tmp_path, "other", limit=3)
    (tmp_path / "link").symlink_to(tmp_path / "other")
    with pytest.raises(ValueError, match="Symlink"):
        MODULE.ordinary(tmp_path, "link")
    assert MODULE.ordinary(tmp_path, "other") == b"abcdef"


def test_catalog_hash_refused(index: Any) -> None:
    """A wrong retained catalog digest fails before any department traversal."""
    changed = index.model_copy(update={
        "catalog": index.catalog.model_copy(update={"sha256": "0" * 64})
    })
    with pytest.raises(ValueError, match="hash/size"):
        MODULE.verify(ROOT, changed)


def test_wrong_denominator_refused(index: Any) -> None:
    """Historical or fabricated department counts cannot override actual retained catalog links."""
    changed = index.model_copy(update={"catalog_department_ids": ["1"]})
    with pytest.raises(ValueError, match="denominator"):
        MODULE.verify(ROOT, changed)


def test_duplicate_department_refused(index: Any) -> None:
    """Duplicating one department cannot inflate coverage totals."""
    changed = index.model_copy(update={"departments": index.departments + [index.departments[0]]})
    with pytest.raises(ValueError, match="Duplicate"):
        MODULE.verify(ROOT, changed)


@pytest.mark.parametrize("field,value,pattern", [
    ("catalog_names", ["Wrong owner"], "Catalog name"),
    ("catalog_url", "https://example.test", "Catalog name"),
    ("rule_count", 999, "counts or identity"),
    ("publication_cutoff_claim", "2099-01-01", "counts or identity"),
    ("source_classification_counts", {"source_current": 999}, "counts or identity"),
    ("source_url_associations", 999, "counts or identity"),
    ("declared_unique_original_counts", {".pdf": 999}, "formats"),
    ("record_observed_range", None, "timestamp"),
])
def test_false_first_department_claim_refused(
    index: Any, field: str, value: Any, pattern: str,
) -> None:
    """Source counts, ownership labels, dates and phases remain bound to captured metadata."""
    entries = list(index.departments)
    entries[0] = entries[0].model_copy(update={field: value})
    with pytest.raises(ValueError, match=pattern):
        MODULE.verify(ROOT, index.model_copy(update={"departments": entries}))


def test_wrong_department_target_refused(index: Any) -> None:
    """A valid hash cannot bind department1 to a department4 target path."""
    entries = list(index.departments)
    bad = entries[0].state.model_copy(update={
        "path": "02_Regulations_CCR/_verification/current/department-4-state.json"
    })
    entries[0] = entries[0].model_copy(update={"state": bad})
    with pytest.raises(ValueError, match="target path"):
        MODULE.verify(ROOT, index.model_copy(update={"departments": entries}))


def test_catalog_only_zero_is_not_unknown(index: Any) -> None:
    """Unadmitted sources cannot be reported as zero historical acquisition."""
    unknown = next(item for item in index.departments if item.phase == "catalog_only")
    entries = [unknown.model_copy(update={"rule_count": 0})]
    entries.extend(item for item in index.departments
                   if item.department_id != unknown.department_id)
    with pytest.raises(ValueError, match="must remain unknown"):
        MODULE.verify(ROOT, index.model_copy(update={"departments": entries}))


def test_model_refuses_currentness_and_answer_promotion(index: Any) -> None:
    """Validated records never certify legal currentness or answer safety."""
    body = index.model_dump()
    body["answer_safe"] = True
    with pytest.raises(ValueError):
        MODULE.Index.model_validate(body)

    body = index.model_dump()
    body["legal_currentness"] = "current"
    with pytest.raises(ValueError):
        MODULE.Index.model_validate(body)


def test_cli_requires_exact_index_pin() -> None:
    """The maintained CLI must refuse an absent or incorrect external index identity."""
    prefix = [sys.executable, "-B", str(ROOT / "scripts/verify_ccr_source_coverage.py"),
              "--root", str(ROOT), "--index",
              str(ROOT / "_CONTROL_PLANE/CCR_SOURCE_COVERAGE_2026-09-23.json")]
    missing = subprocess.run(prefix, capture_output=True, timeout=30, check=False)
    assert missing.returncode == 2 and b"--index-sha256" in missing.stderr
    wrong = subprocess.run(prefix + ["--index-sha256", "0" * 64],
                           capture_output=True, timeout=30, check=False)
    assert wrong.returncode != 0 and b"Index manifest pin differs" in wrong.stderr


def test_committed_source_checkpoint_replays(index: Any) -> None:
    """The portable committed checkpoint retains its exact source-only denominators."""
    result = MODULE.verify(ROOT, index)
    assert result["status"] == "pass"
    assert result["new_departments"] == len(index.new_department_ids)
    assert result["new_rule_records"] == index.new_rule_record_count
    assert result["catalog_departments"] == len(index.catalog_department_ids)


def test_main_replays_the_pinned_index(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    """The public entry point accepts a valid pin and emits one machine-readable result."""
    path = ROOT / "_CONTROL_PLANE/CCR_SOURCE_COVERAGE_2026-09-23.json"
    pin = hashlib.sha256(path.read_bytes()).hexdigest()
    monkeypatch.setattr(sys, "argv", [
        "verify_ccr_source_coverage.py", "--root", str(ROOT), "--index", str(path),
        "--index-sha256", pin,
    ])
    MODULE.main()
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "pass"
    assert result["new_departments"] > 0


def test_main_refuses_wrong_pin(monkeypatch: pytest.MonkeyPatch) -> None:
    """CLI argument parsing does not bypass exact index identity verification."""
    monkeypatch.setattr(sys, "argv", [
        "verify_ccr_source_coverage.py", "--root", str(ROOT), "--index-sha256", "0" * 64,
    ])
    with pytest.raises(ValueError, match="Index manifest pin differs"):
        MODULE.main()


def test_snapshot_requires_state(index: Any) -> None:
    """A declared source snapshot cannot omit its state identity."""
    entries = list(index.departments)
    entries[0] = entries[0].model_copy(update={"state": None})
    with pytest.raises(ValueError, match="Snapshot metadata missing"):
        MODULE.verify(ROOT, index.model_copy(update={"departments": entries}))
