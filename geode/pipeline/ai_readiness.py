"""Audit whether Geode is usable by an AI as a verified knowledge layer."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, ValidationError

from geode.pipeline.local_review import LocalReviewSummary
from geode.utils.file_io import atomic_write_json, iter_jsonl, load_json
from geode.utils.lfs_pointer import UnhydratedLfsPointerError, require_hydrated_file

CONTRACT_FILES = (
    "AI_READ_ORDER.json",
    "AI_QUERY_CONTRACT.json",
    "AI_RETRIEVAL_CONTRACT.json",
    "AI_ANSWER_CONTRACT.json",
)

LOCAL_LAYERS = ("08_County_Authorities", "09_District_Authorities", "10_Municipal_Authorities")


class ReadinessCheck(BaseModel):
    """One prerequisite observation, without an implied legal-currentness finding."""

    model_config = ConfigDict(extra="forbid", strict=True)

    check: str
    passed: bool
    detail: str | None = None
    path: str | None = None
    artifact_status: str | None = None
    rows: int | None = Field(default=None, ge=0)
    declared_object_sha256: str | None = None
    declared_object_bytes: int | None = Field(default=None, ge=0)


class AIReadinessReport(BaseModel):
    """Validated diagnostic output for selected query prerequisites."""

    model_config = ConfigDict(extra="forbid", strict=True)

    version: Literal["1.0"] = "1.0"
    generated_at: AwareDatetime
    purpose: str
    checks: list[ReadinessCheck]
    passed_checks: int = Field(ge=0)
    total_checks: int = Field(ge=0)
    status: Literal["ready", "needs_review"]
    known_limits: list[str]


def _jsonl_check(
    path: Path,
    root: Path,
    name: str,
    *,
    allow_empty: bool = False,
    expected_rows: int | None = None,
) -> ReadinessCheck:
    """Check complete JSONL syntax by streaming, reporting pointers separately."""

    relative = path.relative_to(root).as_posix()
    try:
        require_hydrated_file(path)
        count = sum(1 for _ in iter_jsonl(path))
    except UnhydratedLfsPointerError as exc:
        return ReadinessCheck(
            check=name, passed=False, path=relative, artifact_status="unhydrated_lfs",
            detail="This file contains a Git LFS pointer, not its declared JSONL content.",
            declared_object_sha256=exc.pointer.sha256,
            declared_object_bytes=exc.pointer.size_bytes,
        )
    except FileNotFoundError:
        return ReadinessCheck(check=name, passed=False, path=relative, artifact_status="missing")
    except (OSError, ValueError) as exc:
        return ReadinessCheck(
            check=name, passed=False, path=relative, artifact_status="invalid_or_unreadable",
            detail=str(exc),
        )
    passed = (allow_empty or count > 0) and (expected_rows is None or count == expected_rows)
    detail = "JSONL syntax checked; ownership, currency and query behavior are separate checks."
    if expected_rows is not None and count != expected_rows:
        detail = f"Queue has {count} rows; its summary declares {expected_rows}."
    return ReadinessCheck(
        check=name, passed=passed, path=relative, rows=count,
        artifact_status="valid_jsonl" if count else "empty", detail=detail,
    )


def build_ai_readiness_report(root: Path) -> dict[str, Any]:
    """Build a machine-readable AI-use readiness report from existing artifacts."""

    control = root / "_CONTROL_PLANE"
    checks: list[ReadinessCheck] = []

    for name in CONTRACT_FILES:
        path = control / name
        checks.append(ReadinessCheck(
            check=f"control_plane/{name}", passed=_load_json(path) is not None,
            path=path.relative_to(root).as_posix(),
        ))

    manifest = _load_json(control / "MASTER_MANIFEST.json")
    checks.append(ReadinessCheck(
        check="master_manifest", passed=bool(manifest and manifest.get("data_layers")),
    ))
    catalog = control / "RETRIEVAL_CATALOG.jsonl"
    checks.append(_jsonl_check(catalog, root, "retrieval_catalog"))
    for layer in LOCAL_LAYERS:
        if (root / layer).exists():
            checks.append(_jsonl_check(
                root / layer / "_index.jsonl", root, f"local_index/{layer}", allow_empty=True,
            ))

    summary_path = control / "LOCAL_REVIEW_SUMMARY.json"
    if any((control / name).exists() for name in (
        "LOCAL_REVIEW_SUMMARY.json", "LOCAL_REVIEW_QUEUE.jsonl", "LOCAL_OCR_QUEUE.jsonl",
    )):
        try:
            review = LocalReviewSummary.model_validate(_load_json(summary_path))
        except ValidationError:
            checks.append(ReadinessCheck(
                check="local_review_queues", passed=False,
                path=summary_path.relative_to(root).as_posix(),
                detail="The local review summary is invalid or unreadable.",
            ))
        else:
            checks.append(ReadinessCheck(
                check="local_answer_safe_filter",
                passed=(review.answer_safe_local_rule_units == 0
                        and review.semantic_review_items > 0),
                detail="Local preservation-only material is excluded until reviewed.",
            ))
            checks.append(ReadinessCheck(
                check="local_review_queues", passed=True,
                detail="Summary schema checked; dependent queue files are checked separately.",
            ))
            checks.append(_jsonl_check(
                control / "LOCAL_REVIEW_QUEUE.jsonl", root, "local_review_queue",
                allow_empty=True, expected_rows=review.total_review_items,
            ))
            checks.append(_jsonl_check(
                control / "LOCAL_OCR_QUEUE.jsonl", root, "local_ocr_queue",
                allow_empty=True, expected_rows=review.ocr_items,
            ))

    stress_path = control / "LOCAL_STRESS_TEST_REPORT.json"
    stress = _load_json(stress_path)
    if stress_path.exists():
        checks.append(ReadinessCheck(
            check="local_stress_tests", passed=bool(stress and stress.get("passed") is True),
            path=stress_path.relative_to(root).as_posix(),
        ))

    golden_path = control / "LOCAL_GOLDEN_EVALUATION.json"
    local_golden = _load_json(golden_path)
    if golden_path.exists():
        checks.append(ReadinessCheck(
            check="local_golden_questions",
            passed=bool(local_golden and local_golden.get("failed", 1) == 0
                        and local_golden.get("passed", 0) == local_golden.get("total", -1)),
            path=golden_path.relative_to(root).as_posix(),
        ))

    promotion_path = control / "LOCAL_PROMOTION_REPORT.json"
    promotion_report = _load_json(promotion_path)
    if promotion_path.exists():
        checks.append(ReadinessCheck(
            check="local_promotion_boundary",
            passed=bool(promotion_report and promotion_report.get("blocked", 0) == 0),
            path=promotion_path.relative_to(root).as_posix(),
            detail="Only validated reviewer decisions may promote local evidence.",
        ))

    passed = sum(1 for check in checks if check.passed)
    report = AIReadinessReport(
        generated_at=datetime.now(timezone.utc),
        purpose="Check selected artifact and review prerequisites for AI retrieval.",
        checks=checks, passed_checks=passed, total_checks=len(checks),
        status="ready" if checks and passed == len(checks) else "needs_review",
        known_limits=[
            "Local source-preservation-only records remain available for audit "
            "but are not answer-safe.",
            "Unknown currency must be disclosed until the source is verified "
            "against a current official version.",
            "Coverage gaps are findings, not proof that no rule exists.",
            "Passing these artifact checks does not execute a query "
            "or certify complete legal coverage.",
        ],
    )
    return report.model_dump(mode="json", exclude_none=True)


def write_ai_readiness_report(root: Path) -> dict[str, Any]:
    """Write the AI readiness report to the control plane."""

    report = build_ai_readiness_report(root)
    path = root / "_CONTROL_PLANE" / "AI_READINESS_REPORT.json"
    atomic_write_json(path, AIReadinessReport.model_validate_json(json.dumps(report)), root)
    return report


def _load_json(path: Path) -> dict[str, Any] | None:
    """Load an optional JSON control-plane file."""

    if not path.exists():
        return None
    try:
        require_hydrated_file(path)
        payload = load_json(path)
    except (OSError, ValueError):
        return None
    return payload if isinstance(payload, dict) else None
