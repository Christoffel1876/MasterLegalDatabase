"""Keep the event-tree CI workflow offline without requiring a YAML dependency."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import pytest

WORKFLOW = Path(__file__).resolve().parents[1] / ".github/workflows/manual-source-watch-ci.yml"


def _readiness_command() -> str:
    """Extract the literal shell command used by the offline readiness step."""
    workflow = WORKFLOW.read_text(encoding="utf-8")
    match = re.search(
        r"^          python -B scripts/manual_source_watch_ci\.py.*"
        r"(?:\n            .*)*",
        workflow,
        flags=re.MULTILINE,
    )
    assert match is not None, "Offline readiness invocation must remain explicit"
    return "\n".join(line[10:] for line in match.group().splitlines())


def test_offline_workflow_checks_event_tree_with_read_only_permissions() -> None:
    """The PR and dispatch paths cannot switch checkout to trusted main or publish."""
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "  pull_request:\n    branches: [main]" in workflow
    assert "  push:\n    branches: [main]" in workflow
    assert "  workflow_dispatch:\n" in workflow
    assert "pull_request_target" not in workflow
    assert "schedule:" not in workflow
    assert "inputs:" not in workflow
    assert "ref:" not in workflow
    assert "if: github.ref" not in workflow
    assert "permissions:\n  contents: read" in workflow
    assert "persist-credentials: false" in workflow
    assert "lfs: false" in workflow and "GIT_LFS_SKIP_SMUDGE: '1'" in workflow
    assert not re.search(r"^\s*(?:contents|pull-requests|id-token): write", workflow, re.MULTILINE)
    for forbidden in ("secrets.", "GH_TOKEN", "publish_register", "--execute", "vars."):
        assert forbidden not in workflow


@pytest.mark.parametrize("ambient_live_flag", ["false", "true"])
def test_actual_shell_command_cannot_enable_live_source_requests(
    tmp_path: Path, ambient_live_flag: str
) -> None:
    """Execute only command-recording stubs with hostile ambient activation flags."""
    binaries = tmp_path / "bin"
    binaries.mkdir()
    recorder = binaries / "python"
    recorder.write_text('#!/bin/sh\nprintf "%s\\n" "$@" > "$CAPTURED_ARGV"\n')
    recorder.chmod(0o700)
    git = binaries / "git"
    git.write_text('#!/bin/sh\nprintf "fixture-commit\\n"\n')
    git.chmod(0o700)
    captured = tmp_path / "argv.txt"
    env = {
        **os.environ,
        "PATH": str(binaries) + os.pathsep + "/usr/bin:/bin",
        "CAPTURED_ARGV": str(captured),
        "GITHUB_WORKSPACE": str(tmp_path / "checkout with spaces"),
        "WATCH_RUN_ID": "123",
        "WATCH_RUN_ATTEMPT": "2",
        "WATCH_EXECUTE": ambient_live_flag,
        "MANUAL_WATCH_DAILY_ENABLED": ambient_live_flag,
        "INPUT_EXECUTE": ambient_live_flag,
    }
    completed = subprocess.run(
        ["/bin/bash", "--noprofile", "--norc", "-e", "-o", "pipefail", "-c",
         _readiness_command()],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        check=False,
        timeout=5,
    )
    assert completed.returncode == 0, completed.stderr.decode()
    assert captured.read_text().splitlines() == [
        "-B", "scripts/manual_source_watch_ci.py", "--root",
        str(tmp_path / "checkout with spaces"), "--run-name", "offline-123-2",
        "--event", "local_readiness", "--commit", "fixture-commit",
    ]


def test_offline_failures_and_branch_coverage_are_visible() -> None:
    """Setup, tests and readiness retain evidence without an unchanged-source claim."""
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "--cov=scripts.manual_source_watch_ci --cov-branch --cov-fail-under=90" in workflow
    assert "tests/test_manual_watch*.py tests/test_manual_source_watch*.py" in workflow
    assert "--junitxml=.geode_runtime/manual-watch-offline-ci/tests.xml" in workflow
    assert workflow.count("if: always()") == 2
    assert workflow.index("Initialize setup evidence") < workflow.index("Install frozen")
    assert "Setup failed before a retained readiness report existed" in workflow
    assert "No source HTTP result is established" in workflow
    assert "include-hidden-files: true" in workflow
    assert "timeout-minutes: 15" in workflow
    assert "uses: actions/upload-artifact@" in workflow
    assert "python-version: '3.11'" in workflow and "runs-on: ubuntu-24.04" in workflow
