"""Publish Jefferson and Clear Creek source evidence through an isolated Git bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
from pathlib import Path, PurePosixPath

if __package__:
    from .publish_register_update import diff_entries, git, run, save_json
else:
    from publish_register_update import diff_entries, git, run, save_json

LOGGER = logging.getLogger(__name__)
BRANCH = "codex/county-reacquisition-update"
BASE = "main"
SHA = re.compile(r"[0-9a-f]{40}\Z")
RAW = re.compile(r"_RAW_ARCHIVE/local/reacquisition/([0-9a-f]{64})\.(html|pdf)\Z")
SNAPSHOT = re.compile(r"_SNAPSHOTS/county_reacquisition/([0-9a-f]{64})\.(json|jsonl)\Z")
DATA = {
    "08_County_Authorities/_verification/reacquisition/jefferson-clear-creek.jsonl",
    "08_County_Authorities/_verification/reacquisition/jefferson-clear-creek-state.json",
}


def allowed_path(value: str) -> bool:
    """Allow only Jefferson and Clear Creek verification records and immutable evidence."""
    path = PurePosixPath(value)
    return (str(path) == value and not path.is_absolute() and ".." not in path.parts
            and "\\" not in value
            and bool(value in DATA or RAW.fullmatch(value) or SNAPSHOT.fullmatch(value)))


def validate_tree(root: Path, base: str, candidate: str) -> list[str]:
    """Reject scope escapes, deletions, special file modes, and corrupt originals."""
    changed = []
    for status, path in diff_entries(root, base, candidate):
        if status not in {"A", "M"} or not allowed_path(path):
            raise ValueError(f"Disallowed candidate change: {status} {path}")
        if git(root, "ls-tree", candidate, "--", path).split()[0] != "100644":
            raise ValueError(f"Only ordinary non-executable files may be published: {path}")
        immutable = RAW.fullmatch(path) or SNAPSHOT.fullmatch(path)
        if immutable:
            if status != "A":
                raise ValueError(f"Immutable evidence cannot be overwritten: {path}")
            content = run(root, "git", "show", f"{candidate}:{path}").stdout
            if hashlib.sha256(content).hexdigest() != immutable[1]:
                raise ValueError(f"Evidence content hash does not match its name: {path}")
        changed.append(path)
    validate_referenced_originals(root, candidate)
    return changed


def validate_referenced_originals(root: Path, candidate: str) -> None:
    """Verify source references against committed bytes, including unchanged originals.

    Collection validates record schemas. This separate Git-tree check catches originals
    left untracked by an interrupted local transaction, even when present on disk.
    """
    verified: dict[str, tuple[str, int]] = {}
    for path in sorted(DATA):
        if not git(root, "ls-tree", candidate, "--", path):
            continue
        content = run(root, "git", "show", f"{candidate}:{path}").stdout
        records = ([json.loads(content)] if path.endswith(".json") else
                   [json.loads(line) for line in content.splitlines()])
        for record in records:
            if not isinstance(record, dict):
                raise ValueError("County verification records must be JSON objects")
            sources = record.get("sources", [])
            if isinstance(sources, dict):
                sources = list(sources.values())
            if not isinstance(sources, list):
                raise ValueError("County source references must be an array or URL map")
            for source in sources:
                if not isinstance(source, dict):
                    raise ValueError("Invalid county source reference")
                original = source.get("path", "")
                match = RAW.fullmatch(original) if isinstance(original, str) else None
                if not match or source.get("sha256") != match[1]:
                    raise ValueError("Invalid referenced original path or hash")
                if original not in verified:
                    entry = git(root, "ls-tree", candidate, "--", original).split()
                    if not entry or entry[0] != "100644":
                        raise ValueError(
                            f"Referenced original is absent from candidate: {original}")
                    body = run(root, "git", "show", f"{candidate}:{original}").stdout
                    verified[original] = hashlib.sha256(body).hexdigest(), len(body)
                if verified[original] != (source["sha256"], source.get("bytes")):
                    raise ValueError(
                        f"Referenced original content differs from metadata: {original}")


def validated_report(directory: Path) -> list[str]:
    """Require successful collection of the selected manifest and a valid change list."""
    report = json.loads((directory / "report.json").read_text(encoding="utf-8"))
    if (not isinstance(report, dict) or report.get("status") not in {"updated", "no_change"}
            or report.get("validation_passed") is not True
            or report.get("manifest_complete") is not True
            or report.get("pilot_id") != "jefferson-clear-creek" or report.get("errors")):
        raise ValueError("Source check lacks successful county manifest validation")
    paths = json.loads((directory / "changes.json").read_text(encoding="utf-8"))
    if not isinstance(paths, list) or any(not isinstance(path, str) for path in paths):
        raise ValueError("changes.json must be an array of repository-relative paths")
    if len(paths) != len(set(paths)) or any(not allowed_path(path) for path in paths):
        raise ValueError("changes.json includes duplicate or disallowed paths")
    if report.get("changed_paths") != paths:
        raise ValueError("Run report and changes.json disagree")
    if (report["status"] == "no_change") != (not paths):
        raise ValueError("Run status disagrees with the changed paths")
    return paths


def remote_head(root: Path) -> str | None:
    """Read pending data without treating a failed remote query as absence."""
    result = git(root, "ls-remote", "--heads", "origin", f"refs/heads/{BRANCH}")
    return result.split()[0] if result else None


def prepare(root: Path, output: Path) -> None:
    """Resume validated pending data and merge current main without discarding conflicts."""
    if git(root, "status", "--porcelain", "--untracked-files=no"):
        raise ValueError("Preparation requires a clean tracked working tree and index")
    main, pending = git(root, "rev-parse", "origin/main"), remote_head(root)
    git(root, "config", "user.name", "github-actions[bot]")
    git(root, "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
    if pending:
        git(root, "fetch", "origin", f"refs/heads/{BRANCH}")
        if git(root, "rev-parse", "FETCH_HEAD") != pending:
            raise ValueError("Pending branch changed during preparation; retry")
        validate_tree(root, git(root, "merge-base", main, pending), pending)
        git(root, "switch", "--detach", pending)
        git(root, "merge", "--no-edit", main)
    else:
        git(root, "switch", "--detach", main)
    save_json(output / "baseline.json", {"main": main, "pending": pending})


def build(root: Path, output: Path, report_dir: Path) -> bool:
    """Commit only the validated transaction and bundle all pending verification data."""
    baseline = json.loads((output / "baseline.json").read_text(encoding="utf-8"))
    paths = validated_report(report_dir)
    for path in paths:
        target = root / path
        if target.is_symlink() or not target.is_file() or not target.resolve().is_relative_to(root):
            raise ValueError(f"Change is not an ordinary file inside the checkout: {path}")
    if git(root, "diff", "--cached", "--name-only"):
        raise ValueError("Index must be empty before staging the validated transaction")
    if not {path for _, path in diff_entries(root)}.issubset(paths):
        raise ValueError("Tracked changes are missing from changes.json")
    for offset in range(0, len(paths), 100):
        git(root, "--literal-pathspecs", "add", "-f", "--", *paths[offset:offset + 100])
    validate_tree(root, "HEAD", git(root, "write-tree"))
    if diff_entries(root, "--cached"):
        git(root, "commit", "-m", "data: preserve Jefferson and Clear Creek pilot sources")
    candidate = git(root, "rev-parse", "HEAD")
    changed = validate_tree(root, baseline["main"], candidate)
    save_json(output / "candidate.json", {
        **baseline, "candidate": candidate, "paths": changed, "has_changes": bool(changed),
    })
    if changed:
        git(root, "bundle", "create", str(output / "candidate.bundle"),
            "HEAD", f"^{baseline['main']}")
    if os.environ.get("GITHUB_OUTPUT"):
        with Path(os.environ["GITHUB_OUTPUT"]).open("a", encoding="utf-8") as handle:
            handle.write(f"has_changes={str(bool(changed)).lower()}\n")
    return bool(changed)


def publish(root: Path, output: Path, report_dir: Path, repository: str) -> str:
    """Verify the bundle and races, then push without force and maintain one review PR."""
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("Invalid GitHub repository")
    validated_report(report_dir)
    metadata = json.loads((output / "candidate.json").read_text(encoding="utf-8"))
    for field in ("main", "candidate", "pending"):
        if field == "pending" and metadata[field] is None:
            continue
        if not isinstance(metadata[field], str) or not SHA.fullmatch(metadata[field]):
            raise ValueError(f"Invalid {field} commit")
    pending = metadata["pending"]
    if remote_head(root) != pending:
        raise ValueError("Pending branch changed after validation; retry")
    main = git(root, "ls-remote", "origin", "refs/heads/main").split()
    if not main or main[0] != metadata["main"]:
        raise ValueError("main changed after validation; retry")
    git(root, "fetch", str(output / "candidate.bundle"), "HEAD")
    candidate = git(root, "rev-parse", "FETCH_HEAD")
    if candidate != metadata["candidate"]:
        raise ValueError("Candidate bundle does not match its metadata")
    git(root, "merge-base", "--is-ancestor", metadata["main"], candidate)
    if pending:
        git(root, "merge-base", "--is-ancestor", pending, candidate)
    paths = validate_tree(root, metadata["main"], candidate)
    if not paths or paths != metadata["paths"] or metadata.get("has_changes") is not True:
        raise ValueError("Candidate paths do not match the validated metadata")
    existing = json.loads(run(root, "gh", "pr", "list", "--repo", repository, "--state", "open",
                              "--head", BRANCH, "--base", BASE, "--json", "number,url").stdout)
    if len(existing) > 1:
        raise ValueError("More than one pending county PR exists; reconcile manually")
    git(root, "push", "origin", f"{candidate}:refs/heads/{BRANCH}")
    run_url = os.environ.get("GITHUB_SERVER_URL", "https://github.com") + "/" + repository
    if os.environ.get("GITHUB_RUN_ID"):
        run_url += "/actions/runs/" + os.environ["GITHUB_RUN_ID"]
    body_path = output / "pull-request-body.md"
    body_path.write_text(
        "This update preserves selected Jefferson and Clear Creek source documents, "
        "their catalog labels, retrieval times, hashes, and unselected catalog links. "
        "It does not replace inherited county legal text or establish complete county coverage.\n\n"
        "All documents remain source-preservation-only with unknown legal status. "
        "Review the originals, catalog gaps, effective dates, and later amendments. "
        "This workflow never approves or merges this PR.\n\n"
        f"[Validated workflow run and source-check report]({run_url})\n\n"
        f"Candidate commit: `{candidate}`. Changed paths: {len(paths)}.\n",
        encoding="utf-8",
    )
    if existing:
        run(root, "gh", "pr", "edit", str(existing[0]["number"]), "--repo", repository,
            "--body-file", str(body_path))
        url = existing[0]["url"]
    else:
        url = run(root, "gh", "pr", "create", "--repo", repository, "--head", BRANCH,
                  "--base", BASE, "--title",
                  "data: preserve Jefferson and Clear Creek pilot sources",
                  "--body-file", str(body_path)).stdout.decode().strip()
    save_json(output / "published.json", {"url": url, "candidate": candidate})
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with Path(os.environ["GITHUB_STEP_SUMMARY"]).open("a", encoding="utf-8") as handle:
            handle.write(f"\nReviewable county evidence: [{BRANCH}]({url})\n")
    LOGGER.info("Reviewable county evidence: %s", url)
    return url


def main() -> int:
    """Run one publication phase; failures prevent publication."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("prepare", "build", "publish"))
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--report-dir", type=Path, default=Path(".geode_runtime/county-reacquisition"),
    )
    parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY", ""))
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    try:
        root, output, report = args.root.resolve(), args.output.resolve(), args.report_dir.resolve()
        if args.phase == "prepare":
            prepare(root, output)
        elif args.phase == "build":
            build(root, output, report)
        else:
            publish(root, output, report, args.repository)
    except (ValueError, RuntimeError, OSError, KeyError, TypeError) as error:
        LOGGER.error("County publication stopped: %s", error)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
