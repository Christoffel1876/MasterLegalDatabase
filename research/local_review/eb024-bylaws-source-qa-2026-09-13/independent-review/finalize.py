"""Seal the new source-review package after its bounded offline checks complete."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from typing import Literal

from pydantic import AwareDatetime, TypeAdapter

from build_review import HashCheck, new_file
from review import ROOT, SOURCE_SHA, Asset, Review, Strict, asset, check_review, read


class Validation(Strict):
    """Actual validation evidence; automated and visual scopes are separate."""
    completed_at: AwareDatetime
    source_id: Literal["el-paso-boh-bylaws-sd011"]
    authority_id: Literal["CO-COUNTY-EL_PASO"]
    source_sha256: Literal[SOURCE_SHA]
    qa: Asset
    qa_schema: Asset
    verifier: Asset
    final_tests: Asset
    tests_passed: Literal[16]
    warnings: Literal[5]
    visual_pages: Literal[5]
    native_bytes: Literal[12640]
    nonblank_native_lines: Literal[170]
    nonwhitespace_unicode_characters: Literal[9999]
    paragraph_portions: Literal[54]
    additional_report_hash_checks: list[HashCheck]
    timestamp_texts_match_recorded_claims: bool
    structural_replay_passed: bool
    full_png_replay_receipt: Asset
    pixel_replay_is_visual_judgment: Literal[False]
    legal_currentness: Literal["not_verified"]
    public_requests: Literal[0]
    canonical_writes: Literal[0]


def main() -> None:
    """Validate before writing a new receipt and closed inventory."""
    record = Review.model_validate_json(read(ROOT, "SOURCE_QA.json"))
    check_review(ROOT, record)
    tests = read(ROOT, "tests-final.log").decode()
    if "16 passed, 5 warnings" not in tests or "FAILED " in tests:
        raise ValueError("Focused final test run not passing")
    freeze = json.loads(read(ROOT, "received/PASS1_FREEZE_RECEIPT.json"))
    completion = json.loads(read(ROOT, "received/COMPLETION_RECEIPT.json"))
    checks = []
    for claim, name, expected in [
        ("Pass1 task prompt", "received/prompts/PASS1_TASK_PROMPT.txt",
         freeze["assistance"]["task_prompt_retained_sha256"]),
        ("candidate_actual_sha256", "candidate/candidate.txt", completion["candidate_actual_sha256"]),
        ("Pass1 source PDF", "source/original.pdf", freeze["original_pdf_sha256"]),
        ("Pass1 frozen self-recorded digest", "received/PASS1_frozen.md", freeze["pass1_frozen_sha256"]),
    ]:
        ref = asset(ROOT, name)
        checks.append(HashCheck(claim=claim, actual=ref, expected_sha256=expected,
                                matches=ref.sha256 == expected))
    if not all(c.matches for c in checks):
        raise ValueError("Additional report hash claim mismatch")
    time_checks = (read(ROOT, "received/START_UTC.txt").decode().strip() == completion["utc_start"]
                   and read(ROOT, "received/CANDIDATE_RELEASE_UTC.txt").decode().strip()
                   == completion["utc_candidate_release"])
    if not time_checks:
        raise ValueError("Recorded timestamp texts disagree")
    result = Validation(completed_at=datetime.now(timezone.utc),
        source_id="el-paso-boh-bylaws-sd011", authority_id="CO-COUNTY-EL_PASO",
        source_sha256=SOURCE_SHA, qa=asset(ROOT, "SOURCE_QA.json"),
        qa_schema=asset(ROOT, "SOURCE_QA.schema.json"), verifier=asset(ROOT, "review.py"),
        final_tests=asset(ROOT, "tests-final.log"), tests_passed=16, warnings=5,
        visual_pages=5, native_bytes=12640, nonblank_native_lines=170,
        nonwhitespace_unicode_characters=9999, paragraph_portions=54,
        additional_report_hash_checks=checks, timestamp_texts_match_recorded_claims=True,
        structural_replay_passed=True, full_png_replay_receipt=asset(ROOT, "RENDER_CHECK.json"),
        pixel_replay_is_visual_judgment=False, legal_currentness="not_verified",
        public_requests=0, canonical_writes=0)
    raw = result.model_dump_json(indent=2) + "\n"
    Validation.model_validate_json(raw)
    new_file("VALIDATION.schema.json", (json.dumps(Validation.model_json_schema(), indent=2) + "\n").encode())
    new_file("VALIDATION.json", raw.encode())
    new_file("FINAL_MANIFEST.schema.json",
             (json.dumps(TypeAdapter(list[Asset]).json_schema(), indent=2) + "\n").encode())
    files = []
    for path in sorted(ROOT.rglob("*")):
        if path.is_symlink() or not (path.is_file() or path.is_dir()):
            raise ValueError("Nonordinary review member")
        if path.is_file():
            files.append(asset(ROOT, path.relative_to(ROOT).as_posix()))
    payload = TypeAdapter(list[Asset]).dump_json(files, indent=2) + b"\n"
    TypeAdapter(list[Asset]).validate_json(payload)
    new_file("FINAL_MANIFEST.json", payload)
    sys.stdout.write(json.dumps({"files": len(files), "bytes": sum(f.size_bytes for f in files),
        "qa": result.qa.model_dump(), "schema": result.qa_schema.model_dump(),
        "validation": asset(ROOT, "VALIDATION.json").model_dump(),
        "manifest": asset(ROOT, "FINAL_MANIFEST.json").model_dump()}, indent=2) + "\n")


if __name__ == "__main__":
    main()
