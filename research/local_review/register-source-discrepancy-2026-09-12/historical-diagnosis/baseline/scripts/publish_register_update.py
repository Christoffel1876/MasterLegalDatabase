"""Prepare and publish narrowly scoped, reviewable Colorado Register data updates.

The collection job can create a local candidate but has read-only credentials.
Only the publish job may push, and it rechecks the complete candidate tree.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any

LOGGER = logging.getLogger(__name__)
BRANCH = "codex/register-daily-update"
BASE = "main"
SHA = re.compile(r"[0-9a-f]{40}\Z")
RAW = re.compile(r"_RAW_ARCHIVE/register/daily/([0-9a-f]{64})\.(html|pdf|docx|doc|rtf)\Z")
SNAPSHOT = re.compile(r"_SNAPSHOTS/register_daily/([0-9a-f]{64})\.(json|jsonl|csv)\Z")
DATA = re.compile(r"04_Rulemaking/(?:_index\.jsonl|"
                  r"(?P<year>[0-9]{4})/register_(?P=year)_Q[1-4]\.jsonl)\Z")
CONTROL = {
    "_CROSSWALKS/rulemaking_to_regulation.jsonl",
    "_CONTROL_PLANE/MASTER_MANIFEST.json",
    "_CONTROL_PLANE/REGISTER_REFRESH_STATE.json",
    "04_Rulemaking/_meta/rulemaking_notices_meta.jsonl",
    "04_Rulemaking/_dataset/rulemaking_notices.jsonl",
    "04_Rulemaking/_dataset/rulemaking_notices.csv",
    "04_Rulemaking/_dataset/register_daily_sources.jsonl",
}


def run(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    """Run an argument-vector command without shell interpolation."""
    result = subprocess.run(args, cwd=root, capture_output=True, check=False)
    if check and result.returncode:
        raise RuntimeError(f"{args[0]} failed: {result.stderr.decode(errors='replace').strip()}")
    return result


def git(root: Path, *args: str) -> str:
    """Read a Git command's UTF-8 output."""
    return run(root, "git", *args).stdout.decode().strip()


def save_json(path: Path, value: Any) -> None:
    """Atomically save workflow metadata."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def allowed_path(value: str) -> bool:
    """Accept only canonical pilot data and immutable evidence paths."""
    path = PurePosixPath(value)
    if str(path) != value or path.is_absolute() or ".." in path.parts or "\\" in value:
        return False
    return bool(value in CONTROL or DATA.fullmatch(value) or RAW.fullmatch(value)
                or SNAPSHOT.fullmatch(value))


def diff_entries(root: Path, *refs: str) -> list[tuple[str, str]]:
    """Return unambiguous, non-renaming Git changes between trees or index."""
    output = run(root, "git", "diff", "--name-status", "--no-renames", "-z", *refs).stdout
    fields = output.decode().split("\0")
    return list(zip(fields[0:-1:2], fields[1:-1:2], strict=True))


def validate_tree(root: Path, base: str, candidate: str) -> list[str]:
    """Reject code, deletions, symlinks, and overwritten or misnamed evidence."""
    changed = []
    for status, path in diff_entries(root, base, candidate):
        if status not in {"A", "M"} or not allowed_path(path):
            raise ValueError(f"Disallowed candidate change: {status} {path}")
        mode = git(root, "ls-tree", candidate, "--", path).split()[0]
        if mode != "100644":
            raise ValueError(f"Only ordinary, non-executable files may be published: {path}")
        immutable = RAW.fullmatch(path) or SNAPSHOT.fullmatch(path)
        if immutable:
            if status != "A":
                raise ValueError(f"Immutable evidence cannot be overwritten: {path}")
            content = run(root, "git", "show", f"{candidate}:{path}").stdout
            if hashlib.sha256(content).hexdigest() != immutable[1]:
                raise ValueError(f"Evidence content hash does not match its name: {path}")
        changed.append(path)
    return changed


def remote_head(root: Path) -> str | None:
    """Read the current pending branch, distinguishing absence from fetch failure."""
    result = git(root, "ls-remote", "--heads", "origin", f"refs/heads/{BRANCH}")
    return result.split()[0] if result else None


def prepare(root: Path, output: Path) -> None:
    """Preserve pending data and merge current main before another source check."""
    if git(root, "status", "--porcelain", "--untracked-files=no"):
        raise ValueError("Preparation requires a clean tracked working tree and index")
    main = git(root, "rev-parse", "origin/main")
    pending = remote_head(root)
    git(root, "config", "user.name", "github-actions[bot]")
    git(root, "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
    if pending:
        git(root, "fetch", "origin", f"refs/heads/{BRANCH}")
        if git(root, "rev-parse", "FETCH_HEAD") != pending:
            raise ValueError("Pending branch changed during preparation; retry the run")
        common = git(root, "merge-base", main, pending)
        validate_tree(root, common, pending)
        git(root, "switch", "--detach", pending)
        # A conflict stops the job; neither side is silently discarded.
        git(root, "merge", "--no-edit", main)
    else:
        git(root, "switch", "--detach", main)
    save_json(output / "baseline.json", {"main": main, "pending": pending})


def build(root: Path, output: Path, report_dir: Path) -> bool:
    """Commit the exact validated transaction and export a candidate Git bundle."""
    baseline = json.loads((output / "baseline.json").read_text(encoding="utf-8"))
    report = json.loads((report_dir / "report.json").read_text(encoding="utf-8"))
    if (report.get("status") not in {"updated", "no_change"}
            or report.get("validation_passed") is not True or report.get("errors")):
        raise ValueError("Source check did not report successful transaction validation")
    paths = json.loads((report_dir / "changes.json").read_text(encoding="utf-8"))
    if not isinstance(paths, list) or any(not isinstance(p, str) for p in paths):
        raise ValueError("changes.json must be an array of repository-relative paths")
    if len(paths) != len(set(paths)) or any(not allowed_path(p) for p in paths):
        raise ValueError("changes.json includes duplicate or disallowed paths")
    if report["status"] == "no_change" and paths:
        raise ValueError("A no-change report cannot contain changed paths")
    for path in paths:
        target = root / path
        if target.is_symlink() or not target.is_file() or not target.resolve().is_relative_to(root):
            raise ValueError(f"Change is not an ordinary file inside the checkout: {path}")
    if git(root, "diff", "--cached", "--name-only"):
        raise ValueError("Index must be empty before staging the validated transaction")
    modified = {p for _, p in diff_entries(root)}
    if not modified.issubset(paths):
        raise ValueError("Tracked changes are missing from changes.json")
    for offset in range(0, len(paths), 100):
        git(root, "--literal-pathspecs", "add", "-f", "--", *paths[offset:offset + 100])
    staged = git(root, "write-tree")
    validate_tree(root, "HEAD", staged)
    if diff_entries(root, "--cached"):
        git(root, "commit", "-m", "data: refresh Colorado Register pilot sources")
    candidate = git(root, "rev-parse", "HEAD")
    changed = validate_tree(root, baseline["main"], candidate)
    metadata = {**baseline, "candidate": candidate, "paths": changed, "has_changes": bool(changed)}
    save_json(output / "candidate.json", metadata)
    if changed:
        git(root, "bundle", "create", str(output / "candidate.bundle"),
            "HEAD", f"^{baseline['main']}")
    if os.environ.get("GITHUB_OUTPUT"):
        with Path(os.environ["GITHUB_OUTPUT"]).open("a", encoding="utf-8") as handle:
            handle.write(f"has_changes={str(bool(changed)).lower()}\n")
    return bool(changed)


def publish(root: Path, output: Path, report_dir: Path, repository: str) -> str:
    """Recheck and push a candidate without force, then create or update its PR."""
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("Invalid GitHub repository")
    metadata = json.loads((output / "candidate.json").read_text(encoding="utf-8"))
    for field in ("main", "candidate"):
        if not SHA.fullmatch(metadata[field]):
            raise ValueError(f"Invalid {field} commit")
    pending = metadata["pending"]
    if pending is not None and not SHA.fullmatch(pending):
        raise ValueError("Invalid pending commit")
    if remote_head(root) != pending:
        raise ValueError("Pending branch changed after validation; retry instead of overwriting")
    # main moving is also a retry, so this PR always includes the tested main version.
    if git(root, "ls-remote", "origin", "refs/heads/main").split()[0] != metadata["main"]:
        raise ValueError("main changed after validation; retry the daily check")
    git(root, "fetch", str(output / "candidate.bundle"), "HEAD")
    candidate = git(root, "rev-parse", "FETCH_HEAD")
    if candidate != metadata["candidate"]:
        raise ValueError("Candidate bundle does not match its metadata")
    git(root, "merge-base", "--is-ancestor", metadata["main"], candidate)
    if pending:
        git(root, "merge-base", "--is-ancestor", pending, candidate)
    paths = validate_tree(root, metadata["main"], candidate)
    if not paths or paths != metadata["paths"]:
        raise ValueError("Candidate changed paths do not match the validated metadata")
    git(root, "push", "origin", f"{candidate}:refs/heads/{BRANCH}")
    run_url = os.environ.get("GITHUB_SERVER_URL", "https://github.com") + "/" + repository
    if os.environ.get("GITHUB_RUN_ID"):
        run_url += "/actions/runs/" + os.environ["GITHUB_RUN_ID"]
    body = (
        "The daily Colorado Register pilot found official source updates since July 1, 2026. "
        "This PR preserves original source bytes, updates factual rulemaking records and links, "
        "and records the hashes used for the next source check.\n\n"
        "Validation covers this pilot transaction and its offline regression tests; it does "
        "not certify the historical statewide or county corpus. Review source evidence and "
        "the run's report before merging.\n\n"
        f"[Validated workflow run and retained source-check report]({run_url})\n\n"
        f"Candidate commit: `{candidate}`. Changed paths: {len(paths)}.\n\n"
        "Bot-token PR checks may require maintainer approval in GitHub Actions. "
        "The collection job already runs the pilot regression checks before publication.\n"
    )
    body_path = output / "pull-request-body.md"
    body_path.write_text(body, encoding="utf-8")
    existing = json.loads(run(root, "gh", "pr", "list", "--repo", repository, "--state", "open",
                              "--head", BRANCH, "--base", BASE, "--json", "number,url").stdout)
    if len(existing) > 1:
        raise ValueError("More than one pending Register PR exists; reconcile manually")
    if existing:
        run(root, "gh", "pr", "edit", str(existing[0]["number"]), "--repo", repository,
            "--body-file", str(body_path))
        url = existing[0]["url"]
    else:
        url = run(root, "gh", "pr", "create", "--repo", repository, "--head", BRANCH,
                  "--base", BASE, "--title", "data: refresh Colorado Register pilot sources",
                  "--body-file", str(body_path)).stdout.decode().strip()
    save_json(output / "published.json", {"url": url, "candidate": candidate})
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with Path(summary).open("a", encoding="utf-8") as handle:
            handle.write(f"\nReviewable data update: [{BRANCH}]({url})\n")
    LOGGER.info("Reviewable data update: %s", url)
    return url


def main() -> int:
    """Run one phase of the isolated workflow publishing harness."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("prepare", "build", "publish"))
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, default=Path(".geode_runtime/register-refresh"))
    parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY", ""))
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    try:
        root, output = args.root.resolve(), args.output.resolve()
        if args.phase == "prepare":
            prepare(root, output)
        elif args.phase == "build":
            build(root, output, args.report_dir.resolve())
        else:
            publish(root, output, args.report_dir.resolve(), args.repository)
    except (ValueError, RuntimeError, OSError, KeyError, TypeError) as error:
        LOGGER.error("Register publication stopped: %s", error)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
