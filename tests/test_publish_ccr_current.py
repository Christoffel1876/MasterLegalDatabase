"""Exercise publication boundaries and pending-branch persistence using real Git."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import publish_ccr_current as publisher


@pytest.fixture
def checkout(tmp_path: Path) -> Path:
    """Create an isolated repository with a local bare remote."""
    remote = tmp_path / "origin.git"
    root = tmp_path / "checkout"
    publisher.run(tmp_path, "git", "init", "--bare", "--initial-branch=main", str(remote))
    publisher.run(tmp_path, "git", "clone", str(remote), str(root))
    publisher.git(root, "config", "user.name", "Test")
    publisher.git(root, "config", "user.email", "test@example.invalid")
    (root / "README.md").write_text("baseline\n", encoding="utf-8")
    (root / ".gitignore").write_text(".geode_runtime/\n_RAW_ARCHIVE/\n", encoding="utf-8")
    publisher.git(root, "add", "README.md", ".gitignore")
    publisher.git(root, "commit", "-m", "baseline")
    publisher.git(root, "push", "origin", "main")
    return root


def source_path(content: bytes) -> str:
    """Return an allowed immutable source path."""
    return f"_RAW_ARCHIVE/ccr/current/{hashlib.sha256(content).hexdigest()}.html"


def write(root: Path, path: str, content: bytes) -> None:
    """Write one fixture file."""
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)


def candidate(root: Path, paths: list[str]) -> Path:
    """Write a successful report and build the exact transaction."""
    output = root / ".geode_runtime/candidate"
    report = root / ".geode_runtime/report"
    publisher.save_json(report / "report.json", {
        "status": "updated" if paths else "no_change", "validation_passed": True,
        "full_department_discovery": True, "department_id": "12", "changed_paths": paths,
    })
    publisher.save_json(report / "changes.json", paths)
    publisher.build(root, output, report)
    return output


@pytest.mark.parametrize("path", [
    "../02_Regulations_CCR/_verification/current/department-12.jsonl",
    "/02_Regulations_CCR/_verification/current/department-12.jsonl",
    "04_Rulemaking/../README.md", ".github/workflows/evil.yml", "geode/evil.py",
    "04_Rulemaking/_dataset/code.py", "_RAW_ARCHIVE/ccr/current/unhashed.html",
    "04_Rulemaking//_index.jsonl", "04_Rulemaking\\_index.jsonl",
])
def test_rejects_paths_outside_exact_allowlist(path: str) -> None:
    assert not publisher.allowed_path(path)


def test_build_stages_only_manifest_and_includes_ignored_original(
    checkout: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = checkout / ".geode_runtime/candidate"
    publisher.prepare(checkout, output)
    workflow_output = output / "github-output.txt"
    monkeypatch.setenv("GITHUB_OUTPUT", str(workflow_output))
    raw = source_path(b"official original")
    write(checkout, raw, b"official original")
    write(checkout, "02_Regulations_CCR/_verification/current/department-12.jsonl", b'{}\n')
    write(checkout, "unrelated-untracked.txt", b"keep out of commit")
    candidate(checkout, [raw, "02_Regulations_CCR/_verification/current/department-12.jsonl"])
    changed = publisher.validate_tree(checkout, "origin/main", "HEAD")
    expected = [raw, "02_Regulations_CCR/_verification/current/department-12.jsonl"]
    assert sorted(changed) == sorted(expected)
    assert (output / "candidate.bundle").is_file()
    assert workflow_output.read_text() == "has_changes=true\n"


def test_no_change_creates_no_commit_or_candidate_bundle(checkout: Path) -> None:
    output = checkout / ".geode_runtime/candidate"
    publisher.prepare(checkout, output)
    baseline = publisher.git(checkout, "rev-parse", "HEAD")
    candidate(checkout, [])
    assert publisher.git(checkout, "rev-parse", "HEAD") == baseline
    assert not (output / "candidate.bundle").exists()
    assert not json.loads((output / "candidate.json").read_text())["has_changes"]


def test_pending_branch_keeps_unmerged_originals_and_state(checkout: Path) -> None:
    output = checkout / ".geode_runtime/candidate"
    publisher.prepare(checkout, output)
    raw = source_path(b"unmerged original")
    state = "02_Regulations_CCR/_verification/current/department-12-state.json"
    write(checkout, raw, b"unmerged original")
    write(checkout, state, b'{"source_hash": "retained"}\n')
    candidate(checkout, [raw, state])
    previous = publisher.git(checkout, "rev-parse", "HEAD")
    publisher.git(checkout, "push", "origin", f"HEAD:refs/heads/{publisher.BRANCH}")
    publisher.git(checkout, "switch", "main")
    publisher.prepare(checkout, output)
    assert publisher.git(checkout, "rev-parse", "HEAD") == previous
    assert (checkout / raw).read_bytes() == b"unmerged original"
    assert json.loads((checkout / state).read_text())["source_hash"] == "retained"
    candidate(checkout, [])
    assert json.loads((output / "candidate.json").read_text())["pending"] == previous


def test_pending_branch_resumes_after_squash_merge_without_losing_history(checkout: Path) -> None:
    output = checkout / ".geode_runtime/candidate"
    publisher.prepare(checkout, output)
    write(checkout, "02_Regulations_CCR/_verification/current/department-12.jsonl", b'{}\n')
    candidate(checkout, ["02_Regulations_CCR/_verification/current/department-12.jsonl"])
    publisher.git(checkout, "push", "origin", f"HEAD:refs/heads/{publisher.BRANCH}")
    prior = publisher.git(checkout, "rev-parse", "HEAD")
    publisher.git(checkout, "switch", "main")
    publisher.git(checkout, "merge", "--squash", prior)
    publisher.git(checkout, "commit", "-m", "reviewed squash merge")
    publisher.git(checkout, "push", "origin", "main")
    publisher.prepare(checkout, output)
    candidate(checkout, [])
    assert not json.loads((output / "candidate.json").read_text())["has_changes"]


def test_prepare_rejects_unreviewed_code_on_pending_branch(checkout: Path) -> None:
    write(checkout, "malicious.py", b"raise SystemExit(0)\n")
    publisher.git(checkout, "add", "malicious.py")
    publisher.git(checkout, "commit", "-m", "unexpected code")
    publisher.git(checkout, "push", "origin", f"HEAD:refs/heads/{publisher.BRANCH}")
    publisher.git(checkout, "switch", "--detach", "origin/main")
    # origin/main points to the original baseline until pushed above only to bot branch.
    with pytest.raises(ValueError, match="Disallowed"):
        publisher.prepare(checkout, checkout / ".geode_runtime/candidate")


def test_build_rejects_failed_report(checkout: Path) -> None:
    output = checkout / ".geode_runtime/candidate"
    publisher.prepare(checkout, output)
    report = checkout / ".geode_runtime/report"
    publisher.save_json(report / "report.json", {"status": "failed", "validation_passed": False})
    publisher.save_json(report / "changes.json", [])
    with pytest.raises(ValueError, match="successful"):
        publisher.build(checkout, output, report)


@pytest.mark.parametrize("kind", ["wrong_hash", "symlink", "delete", "unlisted"])
def test_build_rejects_unsafe_transaction(checkout: Path, kind: str) -> None:
    output = checkout / ".geode_runtime/candidate"
    publisher.prepare(checkout, output)
    path = "02_Regulations_CCR/_verification/current/department-12.jsonl"
    if kind == "wrong_hash":
        path = source_path(b"expected")
        write(checkout, path, b"different")
    elif kind == "symlink":
        (checkout / path).parent.mkdir(parents=True)
        (checkout / path).symlink_to(checkout / "README.md")
    elif kind == "delete":
        (checkout / "README.md").unlink()
    else:
        (checkout / "README.md").write_text("unlisted tracked mutation", encoding="utf-8")
    with pytest.raises(ValueError):
        candidate(checkout, [] if kind in {"delete", "unlisted"} else [path])


def test_immutable_original_cannot_be_overwritten(checkout: Path) -> None:
    output = checkout / ".geode_runtime/candidate"
    publisher.prepare(checkout, output)
    path = source_path(b"original")
    write(checkout, path, b"original")
    candidate(checkout, [path])
    write(checkout, path, b"overwrite")
    with pytest.raises(ValueError, match="overwritten"):
        candidate(checkout, [path])


def test_publish_validates_bundle_and_rejects_branch_race(
    checkout: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = checkout / ".geode_runtime/candidate"
    monkeypatch.setenv("GITHUB_RUN_ID", "1234")
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(checkout / ".geode_runtime/summary.md"))
    publisher.prepare(checkout, output)
    write(checkout, "02_Regulations_CCR/_verification/current/department-12.jsonl", b'{}\n')
    candidate(checkout, ["02_Regulations_CCR/_verification/current/department-12.jsonl"])
    actual_run = publisher.run
    calls = []

    def fake_gh(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
        if args[0] != "gh":
            return actual_run(root, *args, check=check)
        calls.append(args)
        return subprocess.CompletedProcess(args, 0, b"[]" if "list" in args else
                                           b"https://github.com/example/geode/pull/1\n", b"")

    monkeypatch.setattr(publisher, "run", fake_gh)
    url = publisher.publish(checkout, output, checkout / ".geode_runtime/report", "example/geode")
    assert url.endswith("/pull/1")
    assert publisher.remote_head(checkout) == publisher.git(checkout, "rev-parse", "HEAD")
    assert any("create" in call for call in calls)
    # The same stale candidate expected a missing remote branch, so a retry cannot overwrite it.
    with pytest.raises(ValueError, match="changed after validation"):
        publisher.publish(checkout, output, checkout / ".geode_runtime/report", "example/geode")
    publisher.prepare(checkout, output)
    candidate(checkout, [])

    def existing_gh(
        root: Path, *args: str, check: bool = True,
    ) -> subprocess.CompletedProcess[bytes]:
        if args[0] != "gh":
            return actual_run(root, *args, check=check)
        calls.append(args)
        existing = [{"number": 1, "url": url}]
        return subprocess.CompletedProcess(args, 0, json.dumps(existing).encode()
                                           if "list" in args else b"", b"")

    monkeypatch.setattr(publisher, "run", existing_gh)
    result = publisher.publish(
        checkout, output, checkout / ".geode_runtime/report", "example/geode",
    )
    assert result == url
    assert any("edit" in call for call in calls)
    assert "/actions/runs/1234" in (output / "pull-request-body.md").read_text()
    assert url in (checkout / ".geode_runtime/summary.md").read_text()


@pytest.mark.parametrize("corruption", ["main", "candidate", "pending", "paths", "bundle"])
def test_publish_rejects_tampered_artifact_metadata(checkout: Path, corruption: str) -> None:
    output = checkout / ".geode_runtime/candidate"
    publisher.prepare(checkout, output)
    write(checkout, "02_Regulations_CCR/_verification/current/department-12.jsonl", b'{}\n')
    candidate(checkout, ["02_Regulations_CCR/_verification/current/department-12.jsonl"])
    metadata = json.loads((output / "candidate.json").read_text())
    if corruption == "bundle":
        metadata["candidate"] = metadata["main"]
    else:
        metadata[corruption] = [] if corruption == "paths" else "--malicious-argument"
    publisher.save_json(output / "candidate.json", metadata)
    with pytest.raises(ValueError):
        publisher.publish(checkout, output, checkout / ".geode_runtime/report", "example/geode")
    assert publisher.remote_head(checkout) is None


def test_publish_rejects_new_main_after_validation(checkout: Path) -> None:
    output = checkout / ".geode_runtime/candidate"
    publisher.prepare(checkout, output)
    write(checkout, "02_Regulations_CCR/_verification/current/department-12.jsonl", b'{}\n')
    candidate(checkout, ["02_Regulations_CCR/_verification/current/department-12.jsonl"])
    publisher.git(checkout, "switch", "main")
    write(checkout, "README.md", b"updated main\n")
    publisher.git(checkout, "commit", "-am", "other reviewed work")
    publisher.git(checkout, "push", "origin", "main")
    with pytest.raises(ValueError, match="main changed"):
        publisher.publish(checkout, output, checkout / ".geode_runtime/report", "example/geode")
    assert publisher.remote_head(checkout) is None


@pytest.mark.parametrize("bad_paths", [
    None, [1], ["README.md"], ["02_Regulations_CCR/_verification/current/department-12.jsonl"] * 2,
])
def test_build_rejects_malformed_change_manifests(checkout: Path, bad_paths: object) -> None:
    output = checkout / ".geode_runtime/candidate"
    report = checkout / ".geode_runtime/report"
    publisher.prepare(checkout, output)
    publisher.save_json(report / "report.json", {"status": "updated", "validation_passed": True,
        "full_department_discovery": True, "department_id": "12", "changed_paths": bad_paths})
    publisher.save_json(report / "changes.json", bad_paths)
    with pytest.raises(ValueError):
        publisher.build(checkout, output, report)


def test_prepare_stops_on_conflicting_reviewed_data(checkout: Path) -> None:
    path = "02_Regulations_CCR/_verification/current/department-12.jsonl"
    write(checkout, path, b'{"baseline":1}\n')
    publisher.git(checkout, "add", path)
    publisher.git(checkout, "commit", "-m", "initial data")
    publisher.git(checkout, "push", "origin", "main")
    output = checkout / ".geode_runtime/candidate"
    publisher.prepare(checkout, output)
    write(checkout, path, b'{"pending":2}\n')
    candidate(checkout, [path])
    publisher.git(checkout, "push", "origin", f"HEAD:refs/heads/{publisher.BRANCH}")
    pending = publisher.remote_head(checkout)
    publisher.git(checkout, "switch", "main")
    write(checkout, path, b'{"reviewed":3}\n')
    publisher.git(checkout, "commit", "-am", "other reviewed data")
    publisher.git(checkout, "push", "origin", "main")
    with pytest.raises(RuntimeError, match="git failed"):
        publisher.prepare(checkout, output)
    assert publisher.remote_head(checkout) == pending


def test_cli_phases_and_failure_exit(checkout: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    output = checkout / ".geode_runtime/candidate"
    report = checkout / ".geode_runtime/report"
    arguments = ["publisher", "prepare", "--root", str(checkout), "--output", str(output),
                 "--report-dir", str(report)]
    monkeypatch.setattr(sys, "argv", arguments)
    assert publisher.main() == 0
    publisher.save_json(report / "report.json", {"status": "no_change", "validation_passed": True,
        "full_department_discovery": True, "department_id": "12", "changed_paths": []})
    publisher.save_json(report / "changes.json", [])
    arguments[1] = "build"
    assert publisher.main() == 0
    arguments[1] = "publish"
    monkeypatch.setenv("GITHUB_REPOSITORY", "invalid repository")
    assert publisher.main() == 1


@pytest.mark.parametrize("field,value", [
    ("department_id", "13"), ("department_id", 12), ("department_id", None),
    ("validation_passed", False), ("validation_passed", 1),
    ("full_department_discovery", False), ("full_department_discovery", None),
    ("errors", ["catalog incomplete"]), ("changed_paths", ["README.md"]),
    ("status", "updated"),
])
def test_requires_complete_department12_report(
    tmp_path: Path, field: str, value: object,
) -> None:
    report = {"status": "no_change", "validation_passed": True,
              "full_department_discovery": True, "department_id": "12", "changed_paths": []}
    report[field] = value
    publisher.save_json(tmp_path / "report.json", report)
    publisher.save_json(tmp_path / "changes.json", [])
    with pytest.raises(ValueError):
        publisher.validated_report(tmp_path)


@pytest.mark.parametrize("path", [
    "02_Regulations_CCR/_verification/current/department-13.jsonl",
    "02_Regulations_CCR/_verification/current/department-012-state.json",
    "02_Regulations_CCR/_index.jsonl",
    "_RAW_ARCHIVE/register/daily/" + "a" * 64 + ".html",
    "_SNAPSHOTS/ccr_current/" + "a" * 64 + ".csv",
])
def test_no_other_department_or_register_data(path: str) -> None:
    assert not publisher.allowed_path(path)


def test_build_rejects_prestaged_and_dirty_prepare(checkout: Path) -> None:
    output = checkout / ".geode_runtime/candidate"
    publisher.prepare(checkout, output)
    write(checkout, "README.md", b"unrelated staged edit")
    publisher.git(checkout, "add", "README.md")
    with pytest.raises(ValueError, match="clean tracked"):
        publisher.prepare(checkout, output)
    with pytest.raises(ValueError, match="Index must be empty"):
        candidate(checkout, [])


@pytest.mark.parametrize("kind", ["executable", "snapshot_hash", "delete"])
def test_tree_validation_checks_modes_snapshot_hashes_and_deletions(
    checkout: Path, kind: str,
) -> None:
    baseline = publisher.git(checkout, "rev-parse", "HEAD")
    if kind == "delete":
        publisher.git(checkout, "rm", "README.md")
    else:
        path = ("02_Regulations_CCR/_verification/current/department-12.jsonl"
                if kind == "executable" else "_SNAPSHOTS/ccr_current/" + "0" * 64 + ".json")
        write(checkout, path, b"untrusted")
        if kind == "executable":
            (checkout / path).chmod(0o755)
        publisher.git(checkout, "add", path)
    publisher.git(checkout, "commit", "-m", "unsafe candidate")
    with pytest.raises(ValueError):
        publisher.validate_tree(checkout, baseline, "HEAD")


def test_prepare_rejects_pending_branch_moving_during_fetch(
    checkout: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = checkout / ".geode_runtime/candidate"
    publisher.prepare(checkout, output)
    path = "02_Regulations_CCR/_verification/current/department-12.jsonl"
    write(checkout, path, b"{}\n")
    candidate(checkout, [path])
    publisher.git(checkout, "push", "origin", f"HEAD:refs/heads/{publisher.BRANCH}")
    actual_git = publisher.git

    def moved(root: Path, *args: str) -> str:
        result = actual_git(root, *args)
        return "0" * 40 if args == ("rev-parse", "FETCH_HEAD") else result

    monkeypatch.setattr(publisher, "git", moved)
    with pytest.raises(ValueError, match="during preparation"):
        publisher.prepare(checkout, output)


def test_failed_pr_creation_preserves_branch_and_retries_without_new_commit(
    checkout: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    output, report = checkout / ".geode_runtime/candidate", checkout / ".geode_runtime/report"
    publisher.prepare(checkout, output)
    path = "02_Regulations_CCR/_verification/current/department-12.jsonl"
    write(checkout, path, b"{}\n")
    candidate(checkout, [path])
    expected = publisher.git(checkout, "rev-parse", "HEAD")
    actual_run, calls = publisher.run, []
    failing = True

    def gh(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
        if args[0] != "gh":
            return actual_run(root, *args, check=check)
        calls.append(args)
        if "create" in args and failing:
            raise RuntimeError("GitHub PR API unavailable")
        return subprocess.CompletedProcess(args, 0, b"[]" if "list" in args else
                                           b"https://github.com/example/geode/pull/2\n", b"")

    monkeypatch.setattr(publisher, "run", gh)
    with pytest.raises(RuntimeError, match="API unavailable"):
        publisher.publish(checkout, output, report, "example/geode")
    assert publisher.remote_head(checkout) == expected
    failing = False
    publisher.prepare(checkout, output)
    candidate(checkout, [])
    assert publisher.publish(checkout, output, report, "example/geode").endswith("/pull/2")
    assert publisher.remote_head(checkout) == expected
    assert all("--repo" in call for call in calls)
    assert not any("approve" in call or "merge" in call for call in calls)


def test_nonforce_push_rejects_concurrent_pending_commit(
    checkout: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    output, report = checkout / ".geode_runtime/candidate", checkout / ".geode_runtime/report"
    publisher.prepare(checkout, output)
    path = "02_Regulations_CCR/_verification/current/department-12.jsonl"
    write(checkout, path, b'{"first":true}\n')
    candidate(checkout, [path])
    actual_git, actual_run = publisher.git, publisher.run
    rival = checkout.parent / "rival"
    actual_run(checkout.parent, "git", "clone", str(checkout.parent / "origin.git"), str(rival))
    actual_git(rival, "config", "user.name", "Concurrent run")
    actual_git(rival, "config", "user.email", "test@example.invalid")
    write(rival, path, b'{"concurrent":true}\n')
    actual_git(rival, "add", path)
    actual_git(rival, "commit", "-m", "concurrent pending data")
    rival_head = actual_git(rival, "rev-parse", "HEAD")

    def raced_git(root: Path, *args: str) -> str:
        if args and args[0] == "push":
            actual_git(rival, "push", "origin", f"HEAD:refs/heads/{publisher.BRANCH}")
        return actual_git(root, *args)

    def gh(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
        if args[0] == "gh":
            assert "list" in args
            return subprocess.CompletedProcess(args, 0, b"[]", b"")
        return actual_run(root, *args, check=check)

    monkeypatch.setattr(publisher, "git", raced_git)
    monkeypatch.setattr(publisher, "run", gh)
    with pytest.raises(RuntimeError, match="git failed"):
        publisher.publish(checkout, output, report, "example/geode")
    assert publisher.remote_head(checkout) == rival_head


def test_multiple_open_prs_stops_before_push(
    checkout: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    output, report = checkout / ".geode_runtime/candidate", checkout / ".geode_runtime/report"
    publisher.prepare(checkout, output)
    path = "02_Regulations_CCR/_verification/current/department-12.jsonl"
    write(checkout, path, b"{}\n")
    candidate(checkout, [path])
    actual_run = publisher.run

    def gh(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
        if args[0] == "gh":
            return subprocess.CompletedProcess(args, 0, b'[{"number":1},{"number":2}]', b"")
        return actual_run(root, *args, check=check)

    monkeypatch.setattr(publisher, "run", gh)
    with pytest.raises(ValueError, match="More than one"):
        publisher.publish(checkout, output, report, "example/geode")
    assert publisher.remote_head(checkout) is None


def test_script_direct_entrypoint_supports_existing_workflow_cli(tmp_path: Path) -> None:
    script = Path(publisher.__file__).resolve()
    result = subprocess.run([sys.executable, str(script), "--help"], cwd=tmp_path,
                            capture_output=True, check=False)
    assert result.returncode == 0
    assert b"prepare,build,publish" in result.stdout
