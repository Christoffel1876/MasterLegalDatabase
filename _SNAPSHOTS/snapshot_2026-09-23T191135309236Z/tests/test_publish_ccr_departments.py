"""Exercise explicit department selection and checked payload boundaries without HTTP."""

from __future__ import annotations

import hashlib
import io
import json
import re
import subprocess
import sys
from datetime import timedelta
from pathlib import Path
from typing import Any

import pytest

from geode.pipeline import ccr_current as ccr
from geode.pipeline.register_daily import FetchResult
from scripts import publish_ccr_current as publisher
from tests import test_ccr_current as collection
from tests.test_ccr_current_source_series import changed_world
from tests.test_publish_ccr_current import (
    FIXED_WORD_BYTES,
    candidate,
    checkout,
    update_evidence,
    write,
    write_report,
)


@pytest.mark.parametrize("value", [
    "0", "012", "15/../12", "15\n", " 15", "١٥", 15, True, None, "10000", "15,16",
])
def test_selector_rejects_aliases_before_git(tmp_path: Path, value: Any) -> None:
    """Invalid selectors cannot create a baseline or touch a Git repository."""
    with pytest.raises(ValueError, match="Department ID"):
        publisher.prepare(tmp_path, tmp_path / "output", value)
    assert list(tmp_path.iterdir()) == []


def test_explicit_scope_keeps_default_compatibility() -> None:
    """One selector cannot expand into adjacent, zero-padded or canonical regulation paths."""
    assert publisher.branch_name() == publisher.BRANCH
    assert publisher.branch_name("15") == "codex/ccr-current-department-15-update"
    assert publisher.allowed_path(f"{ccr.VERIFICATION_PREFIX}department-15.jsonl", "15")
    for name in ("department-12.jsonl", "department-150.jsonl", "department-015-state.json"):
        assert not publisher.allowed_path(ccr.VERIFICATION_PREFIX + name, "15")
    assert not publisher.allowed_path("02_Regulations_CCR/_index.jsonl", "15")


@pytest.fixture
def payload(tmp_path: Path) -> dict[str, bytes]:
    """Capture a real collector-produced department 15 fixture rather than a success stub."""
    update_evidence(tmp_path, "department fifteen", "15")
    return {
        path.relative_to(tmp_path).as_posix(): path.read_bytes()
        for path in tmp_path.rglob("*") if path.is_file()
    }


def edit_payload(payload: dict[str, bytes], mutation: str) -> None:
    """Corrupt an association and rehash the inventory to exercise semantic guards."""
    prefix = f"{ccr.VERIFICATION_PREFIX}department-15"
    state = json.loads(payload[f"{prefix}-state.json"])
    records = [json.loads(line) for line in io.BytesIO(payload[f"{prefix}.jsonl"])]
    record = records[0]
    primary = record["source_page_url"]
    source = state["sources"][primary]
    if mutation == "state_department":
        state["department_id"] = "16"
    elif mutation == "record_department":
        record["department_id"] = "16"
    elif mutation == "rule_ids":
        state["rule_ids"] = []
    elif mutation == "agency_duplicate":
        state["agency_ids"] *= 2
    elif mutation == "agency_invalid":
        state["agency_ids"] = ["../15"]
    elif mutation == "record_agency":
        record["agency_id"] = "99"
    elif mutation == "record_id":
        record["id"] = "9_CCR_1301-1"
    elif mutation == "duplicate_rule":
        records.append(record.copy())
    elif mutation == "duplicate_citation":
        other = record.copy()
        other["rule_id"] = "9999"
        records.append(other)
        state["rule_ids"].append("9999")
    elif mutation == "source_size":
        source["bytes"] += 1
        record["sources"][0] = source.copy()
    elif mutation == "source_bytes":
        payload[source["path"]] += b"corrupt"
    elif mutation == "source_provenance":
        record["sources"][0]["first_retrieved_at"] = "2020-01-01T00:00:00Z"
    elif mutation == "source_key":
        url = next(url for url in state["sources"] if "NumericalCCRDocList" in url)
        state["sources"][url + "&wrong=1"] = state["sources"].pop(url)
    elif mutation == "missing_catalog":
        del state["sources"][state["catalog_url"]]
    elif mutation == "catalog_scope":
        state["agency_ids"] = ["9999", record["agency_id"]]
    elif mutation == "different_department_url":
        url = next(url for url in state["sources"] if "NumericalCCRDocList" in url)
        item = state["sources"].pop(url)
        url = url.replace("deptID=15", "deptID=16")
        item["url"] = item["final_url"] = url
        state["sources"][url] = item
    elif mutation == "source_metadata":
        record["versions"][0]["filing_type"] = "Emergency Rule"
    elif mutation == "source_title":
        record["title"] += " unsupported"
    elif mutation == "repeal_date":
        record["repeal_date"] = "2026-01-01"
    elif mutation == "legal_promotion":
        record["boundary"] = "Certified current law"
    elif mutation == "missing_document":
        record["sources"].pop()
    elif mutation == "agency_name":
        record["agency_name"] = "Different agency"
    elif mutation == "naive_observed_time":
        record["observed_at"] = "2026-09-10T23:00:00"
    elif mutation == "extra_source":
        url = "https://www.sos.state.co.us/CCR/unselected.html"
        item = source.copy()
        item["url"] = item["final_url"] = url
        state["sources"][url] = item
    elif mutation == "wrong_format":
        item = record["sources"][-1]
        original = item["path"]
        item["path"] = str(Path(original).with_suffix(".html"))
        payload[item["path"]] = payload.pop(original)
        state["sources"][item["url"]] = item.copy()
    else:
        assert mutation == "inventory_digest"
    body = b"".join((json.dumps(row) + "\n").encode() for row in records)
    payload[f"{prefix}.jsonl"] = body
    state["inventory_sha256"] = ("0" * 64 if mutation == "inventory_digest"
                                 else hashlib.sha256(body).hexdigest())
    payload[f"{prefix}-state.json"] = json.dumps(state).encode()


@pytest.mark.parametrize("mutation", [
    "state_department", "record_department", "rule_ids", "agency_duplicate", "agency_invalid",
    "record_agency", "record_id", "duplicate_rule", "duplicate_citation", "source_size",
    "source_bytes", "source_provenance", "source_key", "missing_catalog", "catalog_scope",
    "different_department_url", "source_metadata", "source_title", "missing_document",
    "agency_name", "naive_observed_time", "extra_source", "wrong_format", "inventory_digest",
    "repeal_date", "legal_promotion",
])
def test_rehashed_payload_cannot_change_scope_or_source_facts(
    payload: dict[str, bytes], mutation: str,
) -> None:
    """Self-consistent JSON hashes do not excuse an unsupported source claim."""
    assert publisher.validate_payload(payload.__getitem__, "15")
    edit_payload(payload, mutation)
    with pytest.raises((ValueError, KeyError)):
        publisher.validate_payload(payload.__getitem__, "15")


@pytest.mark.parametrize("field,value", [
    ("department_name", "another department"), ("agencies_checked", 2), ("rules_checked", 2),
    ("sources_checked", 5), ("classification_counts", {"ambiguous": 1}),
    ("source_publication_cutoff", "2026-08-12"),
    ("downloaded_bytes", -1), ("downloaded_bytes", ccr.MAX_TOTAL_BYTES + 1),
    ("boundary", "Certified current law"),
])
def test_report_counts_and_classification_are_bound(
    tmp_path: Path, field: str, value: Any,
) -> None:
    """A valid report model must still describe the actual selected payload."""
    paths = update_evidence(tmp_path, "department fifteen", "15")
    directory = write_report(tmp_path, paths, "15")
    raw = json.loads((directory / "report.json").read_bytes())
    raw[field] = value
    report = ccr.CCRCurrentReport.model_validate_json(json.dumps(raw), strict=True)
    with pytest.raises(ValueError, match="report disagrees"):
        publisher.validate_payload(lambda path: (tmp_path / path).read_bytes(), "15", report)


@pytest.mark.parametrize("label", [
    "Current title", "[Repealed 07/01/2018]", "[Repealed 07/01/2027]",
])
def test_source_printed_repeal_date_stays_separate_from_effective_date(
    tmp_path: Path, label: str,
) -> None:
    """Current, repealed and future-repeal source labels retain the collector's exact fields."""
    paths = update_evidence(tmp_path, label, "15")
    report_dir = write_report(tmp_path, paths, "15")
    report = ccr.CCRCurrentReport.model_validate_json((report_dir / "report.json").read_bytes())
    assert publisher.validate_payload(lambda path: (tmp_path / path).read_bytes(), "15", report)


def test_actual_no_change_report_retains_separate_fetched_byte_count(checkout: Path) -> None:
    """A recognized passive wrapper change may alter fetched length but preserve old originals."""
    output = checkout / ".geode_runtime/candidate"
    publisher.prepare(checkout, output)
    initial_head = publisher.git(checkout, "rev-parse", "HEAD")
    state_path = checkout / f"{ccr.VERIFICATION_PREFIX}department-12-state.json"
    state = ccr.CCRState.model_validate_json(state_path.read_bytes())
    retained = {path: (checkout / path).read_bytes()
                for path in publisher.data_paths() | {s.path for s in state.sources.values()}}
    world = collection.world.__wrapped__()
    word = world[collection.WORD_URL]
    world[collection.WORD_URL] = FetchResult(word.url, FIXED_WORD_BYTES, word.content_type)
    original = world[collection.RULE_URL]
    source = original.content.replace(b"PROCEDURES OF REVIEW", b"baseline")
    rotated = re.sub(rb"r:'[a-f0-9]{16}'", b"r:'0123456789abcdef0123456789abcdef'", source)
    assert len(rotated) == len(source) + 16
    world[collection.RULE_URL] = FetchResult(original.url, rotated, original.content_type)
    report = ccr.collect_ccr_current(
        checkout, "12", fetch=world.__getitem__, now=collection.NOW + timedelta(days=2),
    )
    assert report.status == "no_change" and not report.changed_paths, report.errors
    assert report.downloaded_bytes == sum(s.bytes for s in state.sources.values()) + 16
    report_dir = checkout / ".geode_runtime/report"
    ccr.write_run_report(report, report_dir)
    assert publisher.build(checkout, output, report_dir) is False
    assert publisher.git(checkout, "rev-parse", "HEAD") == initial_head
    assert all((checkout / path).read_bytes() == body for path, body in retained.items())


def test_department15_collection_bundle_and_no_change_replay(
    checkout: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Real offline collection feeds the publisher; replay preserves the pending commit."""
    output = checkout / ".geode_runtime/candidate"
    baseline = publisher.git(checkout, "rev-parse", "HEAD")
    publisher.prepare(checkout, output, "15")
    paths = update_evidence(checkout, "department fifteen", "15")
    candidate(checkout, paths, "15")
    metadata = publisher.Candidate.model_validate_json((output / "candidate.json").read_bytes())
    assert metadata.department_id == "15"
    assert publisher.validate_tree(checkout, baseline, "HEAD", "15") == metadata.paths
    assert not any("department-12" in path for path in metadata.paths)
    actual_run = publisher.run
    calls = []

    def local_gh(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
        if args[0] != "gh":
            return actual_run(root, *args, check=check)
        calls.append(args)
        return subprocess.CompletedProcess(args, 0, b"[]" if "list" in args else
                                           b"https://github.com/example/geode/pull/15\n", b"")

    monkeypatch.setattr(publisher, "run", local_gh)
    report_dir = checkout / ".geode_runtime/report"
    assert publisher.publish(checkout, output, report_dir, "example/geode", "15").endswith("/15")
    published = publisher.remote_head(checkout, "15")
    assert publisher.remote_head(checkout) is None
    assert all(publisher.branch_name("15") in call for call in calls)
    assert "department 15" in (output / "pull-request-body.md").read_text()
    publisher.prepare(checkout, output, "15")
    assert update_evidence(checkout, "department fifteen", "15") == []
    candidate(checkout, [], "15")
    assert publisher.git(checkout, "rev-parse", "HEAD") == published
    assert publisher.remote_head(checkout, "15") == published


def test_mixed_preparation_refused_before_staging(checkout: Path) -> None:
    """A department 12 preparation cannot be repurposed by selecting department 15 later."""
    output = checkout / ".geode_runtime/candidate"
    publisher.prepare(checkout, output)
    paths = update_evidence(checkout, "department fifteen", "15")
    report = write_report(checkout, paths, "15")
    with pytest.raises(ValueError, match="Preparation belongs"):
        publisher.build(checkout, output, report, "15")
    assert publisher.git(checkout, "diff", "--cached", "--name-only") == ""


@pytest.mark.parametrize("tamper", ["report", "department", "changes"])
def test_exact_report_and_department_pins_before_publication(
    checkout: Path, monkeypatch: pytest.MonkeyPatch, tamper: str,
) -> None:
    """Changing valid report bytes or the selector stops before remote calls."""
    output = checkout / ".geode_runtime/candidate"
    publisher.prepare(checkout, output, "15")
    candidate(checkout, update_evidence(checkout, "department fifteen", "15"), "15")
    report_dir = checkout / ".geode_runtime/report"
    if tamper == "department":
        path = output / "candidate.json"
        value = json.loads(path.read_bytes())
        value["department_id"] = "12"
        path.write_text(json.dumps(value))
    else:
        path = report_dir / ("report.json" if tamper == "report" else "changes.json")
        path.write_bytes(path.read_bytes() + b"\n")

    def denied_remote(*args: Any, **kwargs: Any) -> str:
        raise AssertionError("Remote query must not occur after changed metadata")

    monkeypatch.setattr(publisher, "remote_head", denied_remote)
    with pytest.raises(ValueError, match="exact report binding"):
        publisher.publish(checkout, output, report_dir, "example/geode", "15")


@pytest.mark.parametrize("kind", ["unreferenced_raw", "foreign_snapshot", "foreign_inventory"])
def test_closed_tree_refuses_extra_evidence(checkout: Path, kind: str) -> None:
    """Allowed-looking filenames cannot import another department or undeclared originals."""
    output = checkout / ".geode_runtime/candidate"
    publisher.prepare(checkout, output, "15")
    paths = update_evidence(checkout, "department fifteen", "15")
    if kind == "unreferenced_raw":
        body = b"unrelated original"
        extra = f"{ccr.RAW_PREFIX}{hashlib.sha256(body).hexdigest()}.html"
    else:
        suffix = ".jsonl" if kind == "foreign_inventory" else ".json"
        original = (f"{ccr.VERIFICATION_PREFIX}department-12.jsonl" if suffix == ".jsonl"
                    else f"{ccr.VERIFICATION_PREFIX}department-12-state.json")
        body = (checkout / original).read_bytes()
        extra = f"{ccr.SNAPSHOT_PREFIX}{hashlib.sha256(body).hexdigest()}{suffix}"
    write(checkout, extra, body)
    with pytest.raises(ValueError, match="department|undeclared"):
        candidate(checkout, paths + [extra], "15")


@pytest.mark.parametrize("include_extra", [False, True])
def test_invented_same_department_snapshot_is_not_a_preimage(
    checkout: Path, include_extra: bool,
) -> None:
    """A fresh self-hashed snapshot cannot make unrelated evidence look like earlier data."""
    output = checkout / ".geode_runtime/candidate"
    publisher.prepare(checkout, output, "15")
    paths = update_evidence(checkout, "department fifteen", "15")
    state_path = checkout / f"{ccr.VERIFICATION_PREFIX}department-15-state.json"
    state = ccr.CCRState.model_validate_json(state_path.read_bytes())
    if include_extra:
        body = b"<html>Unselected evidence</html>"
        sha = hashlib.sha256(body).hexdigest()
        name = f"{ccr.RAW_PREFIX}{sha}.html"
        url = "https://www.sos.state.co.us/CCR/unselected.html"
        source = next(iter(state.sources.values())).model_copy(update={
            "url": url, "final_url": url, "sha256": sha, "path": name,
            "bytes": len(body), "content_type": "text/html",
        })
        state = state.model_copy(update={"sources": {**state.sources, url: source}})
        write(checkout, name, body)
        paths.append(name)
    snapshot = state.model_dump_json().encode()
    name = f"{ccr.SNAPSHOT_PREFIX}{hashlib.sha256(snapshot).hexdigest()}.json"
    write(checkout, name, snapshot)
    with pytest.raises(ValueError, match="actual selected-department preimage"):
        candidate(checkout, paths + [name], "15")


def test_cumulative_pending_updates_keep_exact_historical_preimages(checkout: Path) -> None:
    """Staged trees anchor HEAD, and a later candidate retains both validated update histories."""
    output = checkout / ".geode_runtime/candidate"
    publisher.prepare(checkout, output)
    first_paths = update_evidence(checkout, "first pending update")
    candidate(checkout, first_paths)
    first_head = publisher.git(checkout, "rev-parse", "HEAD")
    first_originals = {path: (checkout / path).read_bytes() for path in first_paths}
    candidate(checkout, update_evidence(checkout, "second pending update"))
    assert publisher.git(checkout, "rev-parse", "HEAD") != first_head
    metadata = publisher.Candidate.model_validate_json((output / "candidate.json").read_bytes())
    assert len([path for path in metadata.paths if path.startswith(ccr.SNAPSHOT_PREFIX)]) == 4
    assert publisher.validate_tree(checkout, metadata.main, metadata.candidate) == metadata.paths
    for path, body in first_originals.items():
        if path.startswith((ccr.RAW_PREFIX, ccr.SNAPSHOT_PREFIX)):
            assert (checkout / path).read_bytes() == body


def test_anchored_but_invalid_historical_scope_is_refused(checkout: Path) -> None:
    """An actual Git parent is not sufficient when its source traversal is inconsistent."""
    output = checkout / ".geode_runtime/candidate"
    publisher.prepare(checkout, output)
    state_path = f"{ccr.VERIFICATION_PREFIX}department-12-state.json"
    state = ccr.CCRState.model_validate_json((checkout / state_path).read_bytes())
    url = "https://www.sos.state.co.us/CCR/extra-source.html"
    source = next(iter(state.sources.values())).model_copy(update={"url": url, "final_url": url})
    state = state.model_copy(update={"sources": {**state.sources, url: source}})
    write(checkout, state_path, state.model_dump_json().encode())
    publisher.git(checkout, "add", state_path)
    publisher.git(checkout, "commit", "-m", "Untrusted inconsistent historical state fixture")
    paths = update_evidence(checkout, "valid current update")
    with pytest.raises(ValueError, match="outside the selected source traversal"):
        candidate(checkout, paths)


def test_source_suffix_identity_uses_the_shared_collector_contract(tmp_path: Path) -> None:
    """An exact source subdivision survives validation without collapsing to its base CCR ID."""
    world = changed_world(collection.world.__wrapped__(), " Rules 1-17")
    report = ccr.collect_ccr_current(tmp_path, "12", fetch=world.__getitem__, now=collection.NOW)
    assert report.status == "updated", report.errors
    assert publisher.validate_payload(lambda path: (tmp_path / path).read_bytes(), "12", report)
    record = ccr.CCRCurrentRecord.model_validate_json(
        (tmp_path / collection.INVENTORY).read_bytes(),
    )
    assert record.id == "8_CCR_1301-1__rule_2567"
    assert record.ccr_citation == "8 CCR 1301-1 Rules 1-17"


def test_direct_cli_selector_outside_checkout(tmp_path: Path) -> None:
    """Direct script imports its maintained models independently of current cwd."""
    script = Path(publisher.__file__).resolve()
    result = subprocess.run(
        [sys.executable, "-B", str(script), "prepare", "--department-id", "015",
         "--root", str(tmp_path), "--output", str(tmp_path / "output")],
        cwd=tmp_path, capture_output=True, check=False,
    )
    assert result.returncode == 1
    assert b"Department ID" in result.stderr
    assert not (tmp_path / "output").exists()


@pytest.mark.parametrize("document_kind", ["word", "pdf"])
def test_rehashed_html_error_is_not_a_document(
    payload: dict[str, bytes], document_kind: str,
) -> None:
    """An HTTP-success error page remains HTML even when every artifact pin is updated."""
    prefix = f"{ccr.VERIFICATION_PREFIX}department-15"
    state = json.loads(payload[f"{prefix}-state.json"])
    records = [json.loads(line) for line in io.BytesIO(payload[f"{prefix}.jsonl"])]
    url = next(
        key for key in state["sources"]
        if "GenerateRulePdf.do" in key and ("type=word" in key) == (document_kind == "word")
    )
    body = b"<html><head><title>ERROR</title></head><body>Source error</body></html>"
    source = state["sources"][url].copy()
    digest = hashlib.sha256(body).hexdigest()
    source.update(path=f"{ccr.RAW_PREFIX}{digest}.html", sha256=digest,
                  bytes=len(body), content_type="text/html;charset=ISO-8859-1")
    payload[source["path"]] = body
    state["sources"][url] = source
    for record in records:
        record["sources"] = [source if item["url"] == url else item for item in record["sources"]]
    inventory = b"".join((json.dumps(row) + "\n").encode() for row in records)
    payload[f"{prefix}.jsonl"] = inventory
    state["inventory_sha256"] = hashlib.sha256(inventory).hexdigest()
    payload[f"{prefix}-state.json"] = json.dumps(state).encode()
    with pytest.raises(ValueError, match="HTML instead of document"):
        publisher.validate_payload(payload.__getitem__, "15")


@pytest.mark.parametrize("signature", [
    b"%PDF-1.7\n", b"\xd0\xcf\x11\xe0fixture", b"{\\rtf1 fixture}",
])
def test_document_roles_keep_collector_non_html_format_contract(
    payload: dict[str, bytes], signature: bytes,
) -> None:
    """The role guard admits collector-supported document signatures without claiming extraction."""
    prefix = f"{ccr.VERIFICATION_PREFIX}department-15"
    state = json.loads(payload[f"{prefix}-state.json"])
    records = [json.loads(line) for line in io.BytesIO(payload[f"{prefix}.jsonl"])]
    url = next(key for key in state["sources"] if "type=word" in key)
    suffix = publisher._media_suffix(FetchResult(url, signature, "application/octet-stream"))
    source = state["sources"][url].copy()
    digest = hashlib.sha256(signature).hexdigest()
    source.update(path=f"{ccr.RAW_PREFIX}{digest}.{suffix}", sha256=digest,
                  bytes=len(signature), content_type="application/octet-stream")
    payload[source["path"]] = signature
    state["sources"][url] = source
    for record in records:
        record["sources"] = [source if item["url"] == url else item for item in record["sources"]]
    inventory = b"".join((json.dumps(row) + "\n").encode() for row in records)
    payload[f"{prefix}.jsonl"] = inventory
    state["inventory_sha256"] = hashlib.sha256(inventory).hexdigest()
    payload[f"{prefix}-state.json"] = json.dumps(state).encode()
    assert publisher.validate_payload(payload.__getitem__, "15")


@pytest.mark.parametrize("role", ["catalog", "rule_page"])
def test_html_role_rejects_non_html_body_even_with_embedded_markup(
    payload: dict[str, bytes], role: str,
) -> None:
    """A parseable HTML fragment inside a document does not satisfy an HTML-page source role."""
    prefix = f"{ccr.VERIFICATION_PREFIX}department-15"
    state = json.loads(payload[f"{prefix}-state.json"])
    records = [json.loads(line) for line in io.BytesIO(payload[f"{prefix}.jsonl"])]
    url = state["catalog_url"] if role == "catalog" else records[0]["source_page_url"]
    source = state["sources"][url].copy()
    body = b"%PDF-1.7\n" + payload[source["path"]]
    digest = hashlib.sha256(body).hexdigest()
    source.update(path=f"{ccr.RAW_PREFIX}{digest}.pdf", sha256=digest,
                  bytes=len(body), content_type="application/pdf")
    payload[source["path"]] = body
    state["sources"][url] = source
    for record in records:
        record["sources"] = [source if item["url"] == url else item for item in record["sources"]]
    inventory = b"".join((json.dumps(row) + "\n").encode() for row in records)
    payload[f"{prefix}.jsonl"] = inventory
    state["inventory_sha256"] = hashlib.sha256(inventory).hexdigest()
    payload[f"{prefix}-state.json"] = json.dumps(state).encode()
    with pytest.raises(ValueError, match="non-HTML source bytes"):
        publisher.validate_payload(payload.__getitem__, "15")
