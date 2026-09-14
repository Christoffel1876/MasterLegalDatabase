"""One-time validated initial-review seal; never modify or rebuild an existing seal."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import AwareDatetime, Field

from build_review import export_json, ref, write_new
from review_models import FileRef, Manifest, Strict
from verify_review import verify_buffers

ROOT = Path(__file__).absolute().parent


class TestReceipt(Strict):
    """Record actual focused tests and their limited verification-code coverage."""

    recorded_at: AwareDatetime
    pytest_status: Literal["passed"]
    tests_passed: Literal[38]
    reported_warnings: Literal[5]
    elapsed_seconds: Literal[6.73]
    log: FileRef
    coverage: FileRef
    test_source: FileRef
    verified_modules: list[FileRef]
    covered_statements: int = Field(ge=0)
    total_statements: int = Field(gt=0)
    covered_branches: int = Field(ge=0)
    total_branches: int = Field(gt=0)
    combined_percent: float = Field(ge=0, le=100)
    qualification: str


def main() -> None:
    """Seal validated evidence without mutating source/QA/earlier preparation inputs."""
    if (ROOT / "FINAL_MANIFEST.json").exists():
        raise RuntimeError("Already frozen; use an additive review instead")
    for local, name in [("/private/tmp/eb026-review-focused-final.log", "focused-tests.log"),
                        ("/private/tmp/eb026-review-coverage-final.json", "coverage.json")]:
        write_new(ROOT / "validation" / name, Path(local).read_bytes())
    coverage = json.loads((ROOT / "validation/coverage.json").read_bytes())["totals"]
    log = (ROOT / "validation/focused-tests.log").read_text()
    if "38 passed, 5 warnings in 6.73s" not in log:
        raise ValueError("Unexpected actual test log")
    receipt = TestReceipt(
        recorded_at=datetime.now(timezone.utc), pytest_status="passed", tests_passed=38,
        reported_warnings=5, elapsed_seconds=6.73,
        log=ref(ROOT / "validation/focused-tests.log"), coverage=ref(ROOT / "validation/coverage.json"),
        test_source=ref(ROOT / "test_review.py"),
        verified_modules=[ref(ROOT / "review_models.py"), ref(ROOT / "verify_review.py")],
        covered_statements=coverage["covered_lines"], total_statements=coverage["num_statements"],
        covered_branches=coverage["covered_branches"], total_branches=coverage["num_branches"],
        combined_percent=coverage["percent_covered"],
        qualification="Coverage measures strict models and read-only verifier, not visual judgment "
        "or historical builders. The actual relocated child CLI passed; its __main__ line is not "
        "attributed to the measured original module. Earlier33-test receipt and field-access "
        "failure remain in preparation-history. No public requests or canonical changes occurred.")
    export_json(ROOT / "validation/TEST_RECEIPT.json", receipt)
    buffers = {p.relative_to(ROOT).as_posix(): p.read_bytes()
               for p in ROOT.rglob("*") if p.is_file()}
    replay = verify_buffers(buffers, rerender=True)
    export_json(ROOT / "validation/REPLAY.json", replay)
    write_new(ROOT / "FINAL_MANIFEST.schema.json",
              (json.dumps(Manifest.model_json_schema(), indent=2) + "\n").encode())
    manifest = Manifest(
        schema_version="geode.eb026.source-qa.inventory.v1", created_at=datetime.now(timezone.utc),
        status="frozen_initial_source_qa",
        files=[ref(p) for p in sorted(ROOT.rglob("*")) if p.is_file()],
        public_requests=0, canonical_writes=0, source_changes=0)
    data = (manifest.model_dump_json(indent=2) + "\n").encode()
    Manifest.model_validate_json(data)
    write_new(ROOT / "FINAL_MANIFEST.json", data)


if __name__ == "__main__":
    main()
