"""Prevent missing LFS content from appearing ready or blaming a valid summary."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from geode.orchestration.contracts import (
    AuthorityLevel, Intent, QueryState, RetrievalStep, RetrievalStrategyType,
)
from geode.orchestration.services.retrieval import LocalKnowledgeRetrievalBackend
from geode.pipeline.ai_readiness import (
    CONTRACT_FILES, build_ai_readiness_report, write_ai_readiness_report,
)
from geode.schemas import ValidationResult
from geode.utils.lfs_pointer import UnhydratedLfsPointerError, require_hydrated_file
from geode.validation.checks import _validate_local_operating_artifacts, validate_jsonl_file

OID = "e12d942b4c8098281d86a8e0db7a76b22512a8a75d050ff590a8e876c7b840b4"
POINTER = f"version https://git-lfs.github.com/spec/v1\noid sha256:{OID}\nsize 225796201\n"


def write_json(path: Path, value: object) -> None:
    """Create a test-only artifact."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


@pytest.fixture
def ready_root(tmp_path: Path) -> Path:
    """Provide readable prerequisite fixtures without pretending they execute a query."""
    control = tmp_path / "_CONTROL_PLANE"
    for name in CONTRACT_FILES:
        write_json(control / name, {"fixture": True})
    write_json(control / "MASTER_MANIFEST.json", {"data_layers": {"state": {}}})
    (control / "RETRIEVAL_CATALOG.jsonl").write_text('{"id":"test"}\n', encoding="utf-8")
    return tmp_path


def add_local_artifacts(root: Path) -> Path:
    """Create mutually consistent local summary, queues and supporting reports."""
    control = root / "_CONTROL_PLANE"
    write_json(control / "LOCAL_REVIEW_SUMMARY.json", {
        "generated_at": "2026-09-11T21:00:00Z", "semantic_review_items": 1,
        "ocr_items": 0, "source_classification_items": 0, "downloaded_source_review_items": 0,
        "blocked_source_recovery_items": 0, "metadata_version_items": 0,
        "total_review_items": 1, "answer_safe_local_rule_units": 0, "boundary": "fixture",
    })
    (control / "LOCAL_REVIEW_QUEUE.jsonl").write_text('{"id":"review"}\n', encoding="utf-8")
    (control / "LOCAL_OCR_QUEUE.jsonl").write_text("", encoding="utf-8")
    write_json(control / "LOCAL_SOURCE_FRESHNESS.json", {"sources_checked": 0, "records": []})
    write_json(control / "LOCAL_OCR_REPORT.json", {
        "pending_items": 0, "completed_items": 0, "items": [],
    })
    write_json(control / "LOCAL_STRESS_TEST_REPORT.json", {"passed": True})
    write_json(control / "LOCAL_PROMOTION_REPORT.json", {"blocked": 0})
    write_json(control / "LOCAL_GOLDEN_EVALUATION.json", {"failed": 0, "passed": 1, "total": 1})
    return control


def checks(root: Path) -> dict[str, dict]:
    """Read the diagnostic checks by their stable key."""
    return {row["check"]: row for row in build_ai_readiness_report(root)["checks"]}


def test_literal_pointer_reports_declared_identity_without_changing_file(tmp_path: Path) -> None:
    """A nonempty pointer has none of the declared original bytes."""
    path = tmp_path / "catalog.jsonl"
    path.write_text(POINTER, encoding="utf-8")
    before = path.read_bytes()
    with pytest.raises(UnhydratedLfsPointerError) as caught:
        require_hydrated_file(path)
    assert caught.value.pointer.sha256 == OID
    assert caught.value.pointer.size_bytes == 225796201
    assert "original content is not present" in str(caught.value)
    assert path.read_bytes() == before


@pytest.mark.parametrize("body", [
    POINTER.replace("\n", "\r\n"), POINTER.replace("size 225796201", "size 0"),
    POINTER.replace("oid sha256:", "ext-0-test sha256:abc\noid sha256:"),
])
def test_pointer_variants_remain_unavailable(tmp_path: Path, body: str) -> None:
    """Line endings, extension metadata or declared zero size do not hydrate content."""
    path = tmp_path / "pointer"
    path.write_bytes(body.encode())
    with pytest.raises(UnhydratedLfsPointerError):
        require_hydrated_file(path)


@pytest.mark.parametrize("body", [
    POINTER.replace(OID, "bad"), POINTER.replace("size 225796201", "size -1"),
    POINTER + "size 12\n", POINTER.replace(f"oid sha256:{OID}\n", ""),
    POINTER + "x" * 5000,
])
def test_malformed_pointer_is_not_treated_as_source(tmp_path: Path, body: str) -> None:
    """Malformed pointer declarations fail closed without guessing their identity."""
    path = tmp_path / "pointer"
    path.write_bytes(body.encode())
    with pytest.raises(ValueError, match="Git LFS pointer"):
        require_hydrated_file(path)


def test_regular_content_with_quoted_lfs_marker_is_not_a_pointer(tmp_path: Path) -> None:
    """A document mentioning the LFS marker remains ordinary content."""
    path = tmp_path / "rows.jsonl"
    write_json(path, {"quote": "version https://git-lfs.github.com/spec/v1"})
    require_hydrated_file(path)


def test_readiness_rejects_catalog_pointer_and_checks_actual_local_indexes(
    ready_root: Path,
) -> None:
    """Catalog and county stubs are diagnosed independently despite being nonempty."""
    catalog = ready_root / "_CONTROL_PLANE/RETRIEVAL_CATALOG.jsonl"
    index = ready_root / "08_County_Authorities/_index.jsonl"
    index.parent.mkdir()
    for path in [catalog, index]:
        path.write_text(POINTER, encoding="utf-8")
    rows = checks(ready_root)
    for key in ["retrieval_catalog", "local_index/08_County_Authorities"]:
        assert rows[key]["passed"] is False
        assert rows[key]["artifact_status"] == "unhydrated_lfs"
        assert rows[key]["declared_object_sha256"] == OID
        assert rows[key]["declared_object_bytes"] == 225796201
    assert build_ai_readiness_report(ready_root)["status"] == "needs_review"


@pytest.mark.parametrize("body,status", [
    ("", "empty"), ('{"id":1}\nnot json\n', "invalid_or_unreadable"),
    ('{"id":1}\n\n', "invalid_or_unreadable"), ('[1,2]\n', "invalid_or_unreadable"),
])
def test_readiness_checks_entire_catalog_syntax(ready_root: Path, body: str, status: str) -> None:
    """A valid first record cannot conceal malformed later records or an empty catalog."""
    (ready_root / "_CONTROL_PLANE/RETRIEVAL_CATALOG.jsonl").write_text(body, encoding="utf-8")
    result = checks(ready_root)["retrieval_catalog"]
    assert result["artifact_status"] == status and not result["passed"]


def test_missing_catalog_and_present_invalid_optional_report_fail(ready_root: Path) -> None:
    """An absent required file and a present unreadable report are explicit failures."""
    (ready_root / "_CONTROL_PLANE/RETRIEVAL_CATALOG.jsonl").unlink()
    control = ready_root / "_CONTROL_PLANE"
    for name in ["LOCAL_STRESS_TEST_REPORT.json", "LOCAL_GOLDEN_EVALUATION.json",
                 "LOCAL_PROMOTION_REPORT.json"]:
        (control / name).write_text(POINTER, encoding="utf-8")
    result = checks(ready_root)
    assert result["retrieval_catalog"]["artifact_status"] == "missing"
    for key in ["local_stress_tests", "local_golden_questions", "local_promotion_boundary"]:
        assert not result[key]["passed"]


def test_valid_summary_does_not_substitute_for_missing_queue(ready_root: Path) -> None:
    """Summary schema and the availability of its queue are distinct checks."""
    control = add_local_artifacts(ready_root)
    (control / "LOCAL_REVIEW_QUEUE.jsonl").write_text(POINTER, encoding="utf-8")
    rows = checks(ready_root)
    assert rows["local_review_queues"]["passed"]
    assert rows["local_review_queue"]["artifact_status"] == "unhydrated_lfs"
    assert rows["local_ocr_queue"]["passed"] and rows["local_ocr_queue"]["rows"] == 0
    assert build_ai_readiness_report(ready_root)["status"] == "needs_review"


def test_queue_count_and_missing_summary_are_not_ready(ready_root: Path) -> None:
    """Hydration alone does not prove that a queue agrees with its summary."""
    control = add_local_artifacts(ready_root)
    (control / "LOCAL_REVIEW_QUEUE.jsonl").write_text("", encoding="utf-8")
    row = checks(ready_root)["local_review_queue"]
    assert not row["passed"] and "summary declares 1" in row["detail"]
    (control / "LOCAL_REVIEW_SUMMARY.json").unlink()
    assert not checks(ready_root)["local_review_queues"]["passed"]


@pytest.mark.parametrize("name", [
    "LOCAL_REVIEW_QUEUE.jsonl", "LOCAL_OCR_QUEUE.jsonl", "LOCAL_SOURCE_FRESHNESS.json",
    "LOCAL_OCR_REPORT.json", "LOCAL_STRESS_TEST_REPORT.json", "LOCAL_PROMOTION_REPORT.json",
    "LOCAL_GOLDEN_EVALUATION.json",
])
def test_operating_validation_names_failing_dependency(ready_root: Path, name: str) -> None:
    """Valid summaries must not receive errors belonging to another artifact."""
    control = add_local_artifacts(ready_root)
    summary_before = (control / "LOCAL_REVIEW_SUMMARY.json").read_bytes()
    (control / name).write_text(POINTER, encoding="utf-8")
    result = ValidationResult.empty(layer="all", checked_at=datetime.now(timezone.utc))
    _validate_local_operating_artifacts(result, control, ready_root)
    assert len(result.issues) == 1
    assert result.issues[0].path == f"_CONTROL_PLANE/{name}"
    assert "Git LFS content unavailable" in result.issues[0].message
    assert (control / "LOCAL_REVIEW_SUMMARY.json").read_bytes() == summary_before


def test_county_validation_reports_lfs_pointer_at_actual_index(ready_root: Path) -> None:
    """The county index gets a missing-content diagnosis, not a JSON syntax guess."""
    path = ready_root / "08_County_Authorities/_index.jsonl"
    path.parent.mkdir()
    path.write_text(POINTER, encoding="utf-8")
    result = ValidationResult.empty(layer="all", checked_at=datetime.now(timezone.utc))
    assert validate_jsonl_file(result, path, ready_root) == []
    assert result.issues[0].path == "08_County_Authorities/_index.jsonl"
    assert OID in result.issues[0].message


def test_runtime_retrieval_rejects_pointer_before_returning_evidence(ready_root: Path) -> None:
    """An unavailable catalog cannot silently become an absence-of-regulation result."""
    (ready_root / "_CONTROL_PLANE/RETRIEVAL_CATALOG.jsonl").write_text(POINTER, encoding="utf-8")
    state = QueryState(intent=Intent(raw_query="permit"))
    step = RetrievalStep(step_id="local", category_id="local_rules",
                         strategy=RetrievalStrategyType.DISCOVERY_SWEEP,
                         authority_level=AuthorityLevel.COUNTY, targets=["rule_unit"])
    with pytest.raises(UnhydratedLfsPointerError):
        LocalKnowledgeRetrievalBackend(ready_root).search(state, step)


def test_read_only_audit_and_snapshotting_writer(ready_root: Path) -> None:
    """Audit reads leave source inputs intact; writing snapshots the prior report."""
    control = add_local_artifacts(ready_root)
    previous = control / "AI_READINESS_REPORT.json"
    previous.write_text('{"old_report":true}\n', encoding="utf-8")
    before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in control.iterdir()}
    report = build_ai_readiness_report(ready_root)
    assert report["status"] == "ready"
    assert any("does not execute a query" in item for item in report["known_limits"])
    assert before == {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in control.iterdir()}
    written = write_ai_readiness_report(ready_root)
    assert written["status"] == "ready"
    snapshots = list((ready_root / "_SNAPSHOTS").glob("*/_CONTROL_PLANE/AI_READINESS_REPORT.json"))
    assert len(snapshots) == 1 and snapshots[0].read_text() == '{"old_report":true}\n'
