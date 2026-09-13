"""Record focused fixture tests and one live read-only preflight; never applies canonically."""
from __future__ import annotations
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from models import Asset, CommandResult, Validation

HERE = Path(__file__).absolute().parent
PROJECT = HERE.parents[2]
REPO = PROJECT / "MasterLegalDatabase"


def sha(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def ref(path):
    return Asset(path=path.relative_to(HERE).as_posix(), sha256=sha(path),
                 size_bytes=path.stat().st_size)


def main():
    if (HERE / "VALIDATION.json").exists():
        raise ValueError("Final validation already frozen")
    plan = json.loads((HERE / "PREPARATION.json").read_bytes())
    before = {item["repository_path"]: sha(REPO / item["repository_path"])
              for item in plan["baseline"]}
    commands = [
        ("focused_tests", [sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider",
            str(HERE / "test_transaction.py"), "--cov=transaction", "--cov=models", "--cov-branch",
            "--cov-report=term-missing",
            "--cov-report=json:" + str(HERE / "validation/coverage.json")]),
        ("live_read_only_preflight", [sys.executable, "-B", str(HERE / "transaction.py"),
                                     "--dry-run", "--root", str(REPO)]),
    ]
    (HERE / "validation").mkdir(exist_ok=True)
    receipts = []
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1",
           "COVERAGE_FILE": "/private/tmp/popper-chaffee-final-recorded-coverage"}
    for label, command in commands:
        started = datetime.now(timezone.utc)
        result = subprocess.run(command, cwd=PROJECT, env=env, capture_output=True, check=False)
        completed = datetime.now(timezone.utc)
        stdout = HERE / "validation" / (label + ".stdout.txt")
        stderr = HERE / "validation" / (label + ".stderr.txt")
        stdout.write_bytes(result.stdout); stderr.write_bytes(result.stderr)
        if result.returncode:
            raise ValueError(label + " failed; exact output retained")
        receipts.append(CommandResult(
            label=label, command=command, working_directory=str(PROJECT),
            started_at=started, completed_at=completed, exit_code=0,
            stdout=ref(stdout), stderr=ref(stderr),
        ))
    coverage = json.loads((HERE / "validation/coverage.json").read_bytes())
    percent = coverage["totals"]["percent_covered"]
    if b"75 passed" not in (HERE / receipts[0].stdout.path).read_bytes():
        raise ValueError("Unexpected test count")
    after = {path: sha(REPO / path) for path in before}
    if before != after or (HERE / "execution").exists():
        raise ValueError("Actual canonical state or execution directory changed")
    validation = Validation(
        status="passed_preparation_only", completed_at=datetime.now(timezone.utc),
        preparation_sha256=sha(HERE / "PREPARATION.json"),
        transaction_sha256=sha(HERE / "transaction.py"), results=receipts, test_count=75,
        combined_branch_inclusive_coverage_percent=percent,
        coverage=ref(HERE / "validation/coverage.json"),
        canonical_managed_sha256_before=before, canonical_managed_sha256_after=after,
        canonical_managed_bytes_unchanged=True, actual_execution_directory_created=False,
        limitations=[
            "All mutations exercised by tests target temporary fixture repositories only.",
            "The first adapted fixture omitted the new sources directory, causing 36 failures; "
            "that test preimage, exact failure log and coverage are retained. After the fixture "
            "copy fix 74 tests passed. This final 75-case run adds coherent "
            "backdated-intent refusal.",
            "No full suite, public request, source content review, canonical apply, currentness "
            "certification or global noncooperating-writer lock is asserted.",
        ],
    )
    raw = validation.model_dump_json(indent=2).encode() + b"\n"
    Validation.model_validate_json(raw)
    temporary = HERE / "VALIDATION.tmp"
    temporary.write_bytes(raw)
    os.replace(temporary, HERE / "VALIDATION.json")
    (HERE / "VALIDATION.schema.json").write_text(
        json.dumps(Validation.model_json_schema(), indent=2) + "\n")
    print(validation.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
