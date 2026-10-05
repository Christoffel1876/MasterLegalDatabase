"""Publish one explicitly selected CCR department through an isolated Git bundle."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import logging
import os
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Callable
from urllib.parse import parse_qs, urlparse
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field, field_validator

if __package__:
    from .publish_register_update import diff_entries, git, run, save_json
else:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from publish_register_update import diff_entries, git, run, save_json

from geode.pipeline import ccr_current as ccr
from geode.pipeline.ccr_current import CCRCurrentRecord, CCRCurrentReport, CCRState
from geode.pipeline.register_daily import FetchResult, _media_suffix

LOGGER = logging.getLogger(__name__)
BRANCH = "codex/ccr-current-update"
BASE = "main"
RAW = re.compile(r"_RAW_ARCHIVE/ccr/current/([0-9a-f]{64})\.(html|pdf|docx|doc|rtf)\Z")
SNAPSHOT = re.compile(r"_SNAPSHOTS/ccr_current/([0-9a-f]{64})\.(json|jsonl)\Z")
PREFIX = "02_Regulations_CCR/_verification/current/"
MAX_HISTORY_UPDATES = 100


def department(value: str) -> str:
    """Require a canonical positive numeric selection without aliases or path syntax."""
    if not isinstance(value, str) or not re.fullmatch(r"[1-9][0-9]{0,3}", value):
        raise ValueError("Department ID must be 1–4 ASCII digits without leading zeroes")
    return value


def data_paths(department_id: str = "12") -> set[str]:
    """Return exactly the two derived paths admitted for the selected department."""
    selected = department(department_id)
    return {f"{PREFIX}department-{selected}.jsonl", f"{PREFIX}department-{selected}-state.json"}


def branch_name(department_id: str = "12") -> str:
    """Keep the existing department 12 branch and isolate other department proposals."""
    selected = department(department_id)
    return BRANCH if selected == "12" else f"codex/ccr-current-department-{selected}-update"


class Baseline(BaseModel):
    """Bind preparation to its selected department and exact remote preimages."""

    model_config = ConfigDict(extra="forbid", strict=True)
    department_id: str
    main: str = Field(pattern=r"^[a-f0-9]{40}$")
    pending: str | None = Field(pattern=r"^[a-f0-9]{40}$")

    @field_validator("department_id")
    @classmethod
    def selected_department(cls, value: str) -> str:
        """Reject selector aliases in retained metadata."""
        return department(value)


class Candidate(Baseline):
    """Bind a validated Git payload to the exact report consumed during build."""

    candidate: str = Field(pattern=r"^[a-f0-9]{40}$")
    paths: list[str]
    has_changes: bool
    report_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    changes_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


def _blob(root: Path, tree: str, path: str) -> bytes:
    """Read only an ordinary blob at an immutable Git tree identity."""
    entry = git(root, "ls-tree", tree, "--", path).split()
    if not entry or entry[0] != "100644":
        raise ValueError(f"Missing or nonordinary payload file: {path}")
    return run(root, "git", "show", f"{tree}:{path}").stdout


def _local_blob(root: Path, path: str) -> bytes:
    """Reject symlinks before reading a prospective staged payload."""
    target = root / path
    if (not target.is_file() or not target.resolve().is_relative_to(root.resolve())
            or any(item.is_symlink() for item in (target, *target.parents))):
        raise ValueError(f"Missing or nonordinary payload file: {path}")
    return target.read_bytes()


def _records(content: bytes, department_id: str) -> list[CCRCurrentRecord]:
    """Validate captured JSONL one line at a time, preserving exact inventory bytes."""
    result = []
    for line in io.BytesIO(content):
        record = CCRCurrentRecord.model_validate_json(line, strict=True)
        if record.department_id != department_id:
            raise ValueError("Inventory record belongs to a different department")
        result.append(record)
    if len({record.rule_id for record in result}) != len(result):
        raise ValueError("Duplicate rule identity in inventory")
    if len({record.id for record in result}) != len(result):
        raise ValueError("Duplicate CCR identity in inventory")
    return result


def _sources(state: CCRState, read: Callable[[str], bytes]) -> dict[str, bytes]:
    """Check every declared immutable source, including unchanged referenced originals."""
    bodies = {}
    if (not 1 <= len(state.sources) <= ccr.MAX_SOURCES
            or sum(source.bytes for source in state.sources.values()) > ccr.MAX_TOTAL_BYTES):
        raise ValueError("Declared source payload exceeds collection limits")
    for url, source in state.sources.items():
        if url != source.url:
            raise ValueError("Source map key disagrees with its provenance URL")
        for key in ("deptID", "agencyID", "ruleId", "ruleVersionId"):
            if key in parse_qs(urlparse(url).query):
                if ccr._query(source.final_url, key) != ccr._query(url, key):
                    raise ValueError(f"Source redirect changed {key}: {url}")
        body = read(source.path)
        if len(body) != source.bytes or hashlib.sha256(body).hexdigest() != source.sha256:
            raise ValueError(f"Missing or corrupt declared source: {source.path}")
        suffix = _media_suffix(FetchResult(source.final_url, body, source.content_type))
        if Path(source.path).suffix != f".{suffix}":
            raise ValueError("Declared source format differs from its body")
        bodies[url] = body
    if state.catalog_url not in state.sources or state.welcome_url not in state.sources:
        raise ValueError("State omits its discovery sources")
    return bodies


def _source_scope(
    state: CCRState, records: list[CCRCurrentRecord], bodies: dict[str, bytes],
) -> None:
    """Replay catalog identities and literal version metadata from the checked source buffers."""
    def document(url: str) -> ccr._Document:
        if Path(state.sources[url].path).suffix != ".html":
            raise ValueError("Catalog or rule page has non-HTML source bytes")
        return ccr._parse_html(bodies[url], state.sources[url].content_type)

    agencies = ccr._agencies(document(state.catalog_url), state.catalog_url, state.department_id)
    if sorted(agencies) != sorted(state.agency_ids):
        raise ValueError("State agency scope differs from the preserved catalog")
    expected_rules = {}
    expected_sources = {state.catalog_url, state.welcome_url}
    for agency_id, (url, name, department_name) in agencies.items():
        if department_name != state.department_name or url not in bodies:
            raise ValueError("Selected catalog ownership or agency evidence differs")
        expected_sources.add(url)
        for rule_id, (rule_url, citation, _title) in ccr._rules(document(url), url).items():
            if rule_id in expected_rules:
                raise ValueError("Duplicate source rule across selected agencies")
            expected_rules[rule_id] = (agency_id, name, rule_url, citation)
    if sorted(expected_rules) != sorted(state.rule_ids):
        raise ValueError("Inventory omits or adds a source-listed rule")
    for record in records:
        if expected_rules[record.rule_id] != (
            record.agency_id, record.agency_name, record.source_page_url, record.ccr_citation,
        ) or record.observed_at.tzinfo is None:
            raise ValueError("Inventory ownership differs from the source catalog")
        parsed = document(record.source_page_url)
        versions = ccr._versions(parsed, record.source_page_url)
        checked = record.observed_at.astimezone(ZoneInfo("America/Denver")).date()
        status, reason, selected = ccr._classify(parsed, versions, checked)
        repeal = ccr.DATE_RE.search(reason)
        repeal_date = (
            datetime.strptime(repeal[0], "%m/%d/%Y").date()
            if re.match(r"(?:\[| - )Repealed\b", reason, re.I) and repeal else None
        )
        if (record.title != ccr._title(parsed) or record.versions != versions
                or record.classification != status or record.classification_evidence != reason
                or record.selected_version_id != (selected.version_id if selected else None)
                or record.effective_date != (selected.effective_date if selected else None)
                or record.repeal_date != repeal_date
                or record.boundary != CCRCurrentRecord.model_fields["boundary"].default
                or ccr._cutoff(document(state.welcome_url), checked)
                != state.source_publication_cutoff):
            raise ValueError("Inventory metadata differs from its checked source bytes")
        expected = {record.source_page_url} | {
            url for version in versions
            if version.designation in {"current", "future", "unknown"}
            for url in version.document_urls
        }
        if {source.url for source in record.sources} != expected:
            raise ValueError("Inventory omits or adds selected document provenance")
        if any(Path(state.sources[url].path).suffix == ".html"
               for url in expected - {record.source_page_url}):
            raise ValueError("Selected document URL has HTML instead of document bytes")
        expected_sources.update(expected)
    if set(bodies) != expected_sources:
        raise ValueError("State includes evidence outside the selected source traversal")


def validate_payload(
    read: Callable[[str], bytes], department_id: str = "12",
    report: CCRCurrentReport | None = None,
) -> set[str]:
    """Bind selected scope, typed state, inventory, provenance, and all source bytes."""
    selected = department(department_id)
    state = CCRState.model_validate_json(
        read(f"{PREFIX}department-{selected}-state.json"), strict=True,
    )
    inventory = read(f"{PREFIX}department-{selected}.jsonl")
    if state.department_id != selected:
        raise ValueError("State belongs to a different department")
    if hashlib.sha256(inventory).hexdigest() != state.inventory_sha256:
        raise ValueError("Inventory hash differs from the captured state")
    records = _records(inventory, selected)
    if sorted(record.rule_id for record in records) != sorted(state.rule_ids):
        raise ValueError("State and inventory rule identities disagree")
    if (len(state.agency_ids) != len(set(state.agency_ids))
            or any(not re.fullmatch(r"[0-9]+", value) for value in state.agency_ids)):
        raise ValueError("Invalid or duplicate state agency identity")
    for record in records:
        query = parse_qs(urlparse(record.source_page_url).query)
        if (record.department_name != state.department_name
                or record.source_publication_cutoff != state.source_publication_cutoff
                or record.agency_id not in state.agency_ids
                or query.get("deptID") != [selected]
                or query.get("agencyID") != [record.agency_id]
                or query.get("ruleId") != [record.rule_id]
                or record.id != ccr.record_identity(record.ccr_citation, record.rule_id)
                or record.source_page_url not in state.sources
                or any(state.sources.get(source.url) != source for source in record.sources)):
            raise ValueError("Inventory provenance disagrees with selected state")
    for url in state.sources:
        query = parse_qs(urlparse(url).query)
        if "deptID" in query and query["deptID"] != [selected]:
            raise ValueError("Source URL belongs to a different department")
    bodies = _sources(state, read)
    _source_scope(state, records, bodies)
    if report is not None:
        counts = dict(Counter(record.classification for record in records))
        # A recognized passive-wrapper change can retain older bytes than the fresh transfer.
        if (report.department_id != selected or report.department_name != state.department_name
                or report.source_publication_cutoff != state.source_publication_cutoff
                or report.agencies_checked != len(state.agency_ids)
                or report.rules_checked != len(records)
                or report.sources_checked != len(state.sources)
                or report.classification_counts != counts
                or not 0 < report.downloaded_bytes <= ccr.MAX_TOTAL_BYTES
                or report.boundary != CCRCurrentReport.model_fields["boundary"].default):
            raise ValueError("Run report disagrees with the selected payload")
    return {source.path for source in state.sources.values()}


def allowed_path(value: str, department_id: str = "12") -> bool:
    """Allow only selected verification records and content-addressed evidence paths."""
    path = PurePosixPath(value)
    return (str(path) == value and not path.is_absolute() and ".." not in path.parts
            and "\\" not in value
            and bool(value in data_paths(department_id)
                     or RAW.fullmatch(value) or SNAPSHOT.fullmatch(value)))


def _historical_preimages(
    root: Path, base: str, candidate: str, department_id: str,
) -> tuple[dict[str, bytes], set[str]]:
    """Bind snapshots to actual predecessor trees and replay each selected source scope.

    A staged tree has HEAD as its only immediate preimage. A cumulative pending
    commit can also preserve earlier updates, whose parent trees remain in Git.
    Caller-supplied snapshot JSON is never itself authority to admit raw originals.
    """
    paths = sorted(data_paths(department_id))
    trees = {git(root, "rev-parse", f"{base}^{{tree}}")}
    if git(root, "cat-file", "-t", candidate) == "commit":
        history = git(
            root, "rev-list", "--full-history", f"--max-count={MAX_HISTORY_UPDATES + 1}",
            f"{base}..{candidate}", "--", *paths,
        ).splitlines()
        if len(history) > MAX_HISTORY_UPDATES:
            raise ValueError("Candidate selected-department history exceeds review limit")
        for commit in history:
            parents = git(root, "show", "-s", "--format=%P", commit).split()
            trees.update(git(root, "rev-parse", f"{parent}^{{tree}}") for parent in parents)
    preimages, sources = {}, set()
    for tree in sorted(trees):
        listed = git(root, "ls-tree", "--name-only", tree, "--", *paths).splitlines()
        if not listed:
            continue
        if sorted(listed) != paths:
            raise ValueError("Historical department preimage is incomplete")
        read = lambda path: _blob(root, tree, path)
        sources.update(validate_payload(read, department_id))
        for path in paths:
            body = read(path)
            name = f"_SNAPSHOTS/ccr_current/{hashlib.sha256(body).hexdigest()}{Path(path).suffix}"
            preimages[name] = body
    return preimages, sources


def validate_tree(
    root: Path, base: str, candidate: str, department_id: str = "12",
    report: CCRCurrentReport | None = None,
) -> list[str]:
    """Reject scope escapes, deletions, special file modes, and corrupt originals."""
    selected = department(department_id)
    tree = git(root, "rev-parse", f"{candidate}^{{tree}}")
    changed = []
    snapshots = []
    for status, path in diff_entries(root, base, candidate):
        if status not in {"A", "M"} or not allowed_path(path, selected):
            raise ValueError(f"Disallowed candidate change: {status} {path}")
        if git(root, "ls-tree", tree, "--", path).split()[0] != "100644":
            raise ValueError(f"Only ordinary non-executable files may be published: {path}")
        immutable = RAW.fullmatch(path) or SNAPSHOT.fullmatch(path)
        if immutable:
            if status != "A":
                raise ValueError(f"Immutable evidence cannot be overwritten: {path}")
            content = _blob(root, tree, path)
            if hashlib.sha256(content).hexdigest() != immutable[1]:
                raise ValueError(f"Evidence content hash does not match its name: {path}")
            if SNAPSHOT.fullmatch(path):
                snapshots.append((path, content))
        changed.append(path)
    read = lambda path: _blob(root, tree, path)
    declared = validate_payload(read, selected, report)
    if snapshots:
        preimages, historical_sources = _historical_preimages(root, base, candidate, selected)
        for path, content in snapshots:
            if preimages.get(path) != content:
                raise ValueError("Snapshot is not an actual selected-department preimage")
        declared.update(historical_sources)
    if any(RAW.fullmatch(path) and path not in declared for path in changed):
        raise ValueError("Candidate contains an undeclared source original")
    return changed


def _report(
    directory: Path, department_id: str,
) -> tuple[CCRCurrentReport, list[str], str, str]:
    """Validate and hash the same captured report bytes, without a later reread."""
    selected = department(department_id)
    body = (directory / "report.json").read_bytes()
    changes = (directory / "changes.json").read_bytes()
    report = CCRCurrentReport.model_validate_json(body, strict=True)
    if (report.status not in {"updated", "no_change"} or not report.validation_passed
            or not report.full_department_discovery or report.department_id != selected
            or report.errors):
        raise ValueError(f"Source check lacks successful complete department {selected} validation")
    paths = json.loads(changes)
    if not isinstance(paths, list) or any(not isinstance(path, str) for path in paths):
        raise ValueError("changes.json must be an array of repository-relative paths")
    if len(paths) != len(set(paths)) or any(not allowed_path(path, selected) for path in paths):
        raise ValueError("changes.json includes duplicate or disallowed paths")
    if report.changed_paths != paths:
        raise ValueError("Run report and changes.json disagree")
    if (report.status == "no_change") != (not paths):
        raise ValueError("Run status disagrees with the changed paths")
    return report, paths, hashlib.sha256(body).hexdigest(), hashlib.sha256(changes).hexdigest()


def validated_report(directory: Path, department_id: str = "12") -> list[str]:
    """Require a successful selected-department report and exact scoped change list."""
    return _report(directory, department_id)[1]


def remote_head(root: Path, department_id: str = "12") -> str | None:
    """Read pending data without treating a failed remote query as absence."""
    branch = branch_name(department_id)
    result = git(root, "ls-remote", "--heads", "origin", f"refs/heads/{branch}")
    return result.split()[0] if result else None


def prepare(root: Path, output: Path, department_id: str = "12") -> None:
    """Resume validated pending data and merge current main without discarding conflicts."""
    selected, branch = department(department_id), branch_name(department_id)
    if git(root, "status", "--porcelain", "--untracked-files=no"):
        raise ValueError("Preparation requires a clean tracked working tree and index")
    main, pending = git(root, "rev-parse", "origin/main"), remote_head(root, selected)
    git(root, "config", "user.name", "github-actions[bot]")
    git(root, "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
    if pending:
        git(root, "fetch", "origin", f"refs/heads/{branch}")
        if git(root, "rev-parse", "FETCH_HEAD") != pending:
            raise ValueError("Pending branch changed during preparation; retry")
        validate_tree(root, git(root, "merge-base", main, pending), pending, selected)
        git(root, "switch", "--detach", pending)
        git(root, "merge", "--no-edit", main)
    else:
        git(root, "switch", "--detach", main)
    baseline = Baseline(department_id=selected, main=main, pending=pending)
    save_json(output / "baseline.json", baseline.model_dump())


def build(root: Path, output: Path, report_dir: Path, department_id: str = "12") -> bool:
    """Commit only the validated transaction and bundle all pending verification data."""
    selected = department(department_id)
    baseline = Baseline.model_validate_json((output / "baseline.json").read_bytes())
    if baseline.department_id != selected:
        raise ValueError("Preparation belongs to a different selected department")
    report, paths, report_sha, changes_sha = _report(report_dir, selected)
    for path in paths:
        target = root / path
        if target.is_symlink() or not target.is_file() or not target.resolve().is_relative_to(root):
            raise ValueError(f"Change is not an ordinary file inside the checkout: {path}")
    if git(root, "diff", "--cached", "--name-only"):
        raise ValueError("Index must be empty before staging the validated transaction")
    if not {path for _, path in diff_entries(root)}.issubset(paths):
        raise ValueError("Tracked changes are missing from changes.json")
    validate_payload(lambda path: _local_blob(root, path), selected, report)
    for offset in range(0, len(paths), 100):
        git(root, "--literal-pathspecs", "add", "-f", "--", *paths[offset:offset + 100])
    validate_tree(root, "HEAD", git(root, "write-tree"), selected, report)
    if diff_entries(root, "--cached"):
        git(root, "commit", "-m", f"data: verify current CCR department {selected} sources")
    candidate = git(root, "rev-parse", "HEAD")
    changed = validate_tree(root, baseline.main, candidate, selected, report)
    metadata = Candidate(
        **baseline.model_dump(), candidate=candidate, paths=changed, has_changes=bool(changed),
        report_sha256=report_sha, changes_sha256=changes_sha,
    )
    save_json(output / "candidate.json", metadata.model_dump())
    if changed:
        git(root, "bundle", "create", str(output / "candidate.bundle"),
            "HEAD", f"^{baseline.main}")
    if os.environ.get("GITHUB_OUTPUT"):
        with Path(os.environ["GITHUB_OUTPUT"]).open("a", encoding="utf-8") as handle:
            handle.write(f"has_changes={str(bool(changed)).lower()}\n")
    return bool(changed)


def publish(
    root: Path, output: Path, report_dir: Path, repository: str, department_id: str = "12",
) -> str:
    """Verify the bundle and races, then push without force and maintain one review PR."""
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("Invalid GitHub repository")
    selected, branch = department(department_id), branch_name(department_id)
    report, _paths, report_sha, changes_sha = _report(report_dir, selected)
    metadata = Candidate.model_validate_json((output / "candidate.json").read_bytes())
    if (metadata.department_id != selected or metadata.report_sha256 != report_sha
            or metadata.changes_sha256 != changes_sha):
        raise ValueError("Candidate scope or exact report binding differs from validation")
    pending = metadata.pending
    if remote_head(root, selected) != pending:
        raise ValueError("Pending branch changed after validation; retry")
    main = git(root, "ls-remote", "origin", "refs/heads/main").split()
    if not main or main[0] != metadata.main:
        raise ValueError("main changed after validation; retry")
    git(root, "fetch", str(output / "candidate.bundle"), "HEAD")
    candidate = git(root, "rev-parse", "FETCH_HEAD")
    if candidate != metadata.candidate:
        raise ValueError("Candidate bundle does not match its metadata")
    git(root, "merge-base", "--is-ancestor", metadata.main, candidate)
    if pending:
        git(root, "merge-base", "--is-ancestor", pending, candidate)
    paths = validate_tree(root, metadata.main, candidate, selected, report)
    if not paths or paths != metadata.paths or not metadata.has_changes:
        raise ValueError("Candidate paths do not match the validated metadata")
    existing = json.loads(run(root, "gh", "pr", "list", "--repo", repository, "--state", "open",
                              "--head", branch, "--base", BASE, "--json", "number,url").stdout)
    if len(existing) > 1:
        raise ValueError("More than one pending CCR PR exists; reconcile manually")
    git(root, "push", "origin", f"{candidate}:refs/heads/{branch}")
    run_url = os.environ.get("GITHUB_SERVER_URL", "https://github.com") + "/" + repository
    if os.environ.get("GITHUB_RUN_ID"):
        run_url += "/actions/runs/" + os.environ["GITHUB_RUN_ID"]
    body_path = output / "pull-request-body.md"
    body_path.write_text(
        f"This update preserves official CCR department {selected} source documents "
        "and a reconciled "
        "verification inventory, including source publication cutoffs and version status. "
        "It does not replace inherited regulation text or establish statewide coverage.\n\n"
        "Review original evidence, completeness results, and effective dates before merging. "
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
        url = run(root, "gh", "pr", "create", "--repo", repository, "--head", branch,
                  "--base", BASE, "--title",
                  f"data: verify current CCR department {selected} sources",
                  "--body-file", str(body_path)).stdout.decode().strip()
    save_json(output / "published.json", {"url": url, "candidate": candidate})
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with Path(os.environ["GITHUB_STEP_SUMMARY"]).open("a", encoding="utf-8") as handle:
            handle.write(f"\nReviewable CCR evidence: [{branch}]({url})\n")
    LOGGER.info("Reviewable CCR evidence: %s", url)
    return url


def main() -> int:
    """Run one publication phase; failures prevent publication."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("prepare", "build", "publish"))
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, default=Path(".geode_runtime/ccr-current"))
    parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY", ""))
    parser.add_argument("--department-id", default="12")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    try:
        root, output, report = args.root.resolve(), args.output.resolve(), args.report_dir.resolve()
        if args.phase == "prepare":
            prepare(root, output, args.department_id)
        elif args.phase == "build":
            build(root, output, report, args.department_id)
        else:
            publish(root, output, report, args.repository, args.department_id)
    except (ValueError, RuntimeError, OSError, KeyError, TypeError) as error:
        LOGGER.error("CCR publication stopped: %s", error)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
