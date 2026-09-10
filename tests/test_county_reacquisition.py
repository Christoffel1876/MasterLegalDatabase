"""County preservation must remain bounded, source-linked, reviewable, and reversible."""

from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import pymupdf
from pydantic import ValidationError

from geode.pipeline import county_reacquisition as county
from geode.pipeline.register_daily import FetchResult

NOW = datetime(2026, 9, 10, 15, tzinfo=timezone.utc)
CATALOG = "https://www.jeffco.us/321/Codes"
PDF = "https://www.jeffco.us/DocumentCenter/View/123"
OTHER = "https://www.jeffco.us/b.pdf"


def pdf_bytes(text: str = "Selected county source", encrypted: bool = False) -> bytes:
    """Build a genuine PDF so preservation tests exercise the actual format validator."""
    with pymupdf.open() as document:
        document.new_page().insert_text((72, 72), text)
        return document.tobytes(
            encryption=pymupdf.PDF_ENCRYPT_AES_256 if encrypted else pymupdf.PDF_ENCRYPT_NONE,
            owner_pw="owner" if encrypted else None, user_pw="reader" if encrypted else None,
        )


PDF_BYTES = pdf_bytes()
HTML = (
    '<html><body><div id="page"><h1>County sources</h1>'
    '<a href="/DocumentCenter/View/123">Land <b>use</b> (PDF)</a>'
    '<a href="/b.pdf">Fees</a><a href="/not-selected.docx">Other rules</a>'
    '<a href="https://external.example/other.pdf">External source</a>'
    '<a href="/DocumentCenter/Home">Document library</a>'
    '<a href="/DocumentCenter/View/123">Land use (PDF)</a>'
    '<a href="/ordinary-page">Navigation</a><a>No link</a></div>'
    '<footer><a href="/footer.pdf">Footer PDF</a></footer></body></html>'
).encode()


def plan() -> county.CountyPilotManifest:
    """A small declared selection with additional unselected and external source gaps."""
    return county.CountyPilotManifest(
        boundary="Two selected sources; no jurisdiction-wide completeness claim.",
        catalogs=[dict(source_id="catalog", authority_id="CO-COUNTY-JEFFERSON",
                       authority_name="Jefferson County", url=CATALOG, title="County sources")],
        documents=[dict(source_id=key, authority_id="CO-COUNTY-JEFFERSON",
                        authority_name="Jefferson County", url=url, catalog_url=CATALOG,
                        source_label=label, category=category)
                   for key, url, label, category in (
                       ("land-use", PDF, "Land use (PDF)", "land_use_zoning"),
                       ("fees", OTHER, "Fees", "fees"))],
    )


@pytest.fixture
def world() -> dict[str, FetchResult]:
    """Controlled source responses; no test needs network access."""
    return {CATALOG: FetchResult(CATALOG, HTML, "text/html; charset=utf-8"),
            PDF: FetchResult(PDF, PDF_BYTES, "application/pdf"),
            OTHER: FetchResult(OTHER, pdf_bytes("other"), "application/pdf")}


def run(root: Path, world: dict[str, FetchResult], **kwargs) -> county.CountyReacquisitionReport:
    """Collect into an isolated fixture corpus."""
    return county.collect_county_reacquisition(
        root, plan(), fetch=world.__getitem__, now=NOW, **kwargs
    )


def files(root: Path) -> dict[str, bytes]:
    """Capture all fixture bytes for no-change and rollback assertions."""
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}


def mutate(world: dict[str, FetchResult], url: str, content: bytes) -> None:
    """Replace one response without changing its endpoint or content type."""
    previous = world[url]
    world[url] = FetchResult(previous.url, content, previous.content_type)


def test_selected_collection_preserves_sources_and_catalog_gaps(
    tmp_path: Path, world: dict,
) -> None:
    canonical = tmp_path / "08_County_Authorities/_index.jsonl"
    canonical.parent.mkdir()
    canonical.write_bytes(b"version https://git-lfs.github.com/spec/v1\n")
    result = run(tmp_path, world)
    assert result.status == "updated", result.errors
    assert result.validation_passed and result.manifest_complete
    assert (result.catalogs_checked, result.documents_checked, result.sources_checked) == (1, 2, 3)
    assert len(result.changed_paths) == 5
    state = county.CountyReacquisitionState.model_validate_json(
        (tmp_path / county.STATE_PATH).read_bytes()
    )
    assert len(state.catalog_links) == 5
    assert {link.disposition for link in state.catalog_links} == {
        "selected", "unselected", "external_or_disallowed"}
    assert len(state.sources) == 3
    assert state.inventory_sha256 == county._digest((tmp_path / county.INVENTORY_PATH).read_bytes())
    for source in state.sources.values():
        assert (tmp_path / source.path).read_bytes() == world[source.url].content
        assert source.sha256 == county._digest(world[source.url].content)
    records = [county.CountyPreservationRecord.model_validate_json(line)
               for line in (tmp_path / county.INVENTORY_PATH).read_bytes().splitlines()]
    assert len(records) == 2
    assert all(record.semantic_status == "source_preservation_only"
               and record.legal_status == "unknown" and record.review_required is True
               for record in records)
    assert canonical.read_bytes().startswith(b"version https://git-lfs.github.com/spec/v1")


def test_identical_replay_refetches_every_source_without_rewriting_any_bytes(
    tmp_path: Path, world: dict,
) -> None:
    assert run(tmp_path, world).status == "updated"
    before = files(tmp_path)
    requested = []

    def fetch(url: str) -> FetchResult:
        requested.append(url)
        return world[url]

    result = county.collect_county_reacquisition(tmp_path, plan(), fetch=fetch,
                                                now=NOW + timedelta(days=1))
    assert result.status == "no_change" and result.changed_paths == []
    assert set(requested) == set(world)
    assert files(tmp_path) == before


def test_repeated_transitions_report_only_actual_file_changes(tmp_path: Path, world: dict) -> None:
    """A reused snapshot must not become a fictitious changed path in a publisher report."""
    changed_pdf = pdf_bytes("revised source")
    for body in (PDF_BYTES, changed_pdf, PDF_BYTES, changed_pdf):
        before = files(tmp_path)
        mutate(world, PDF, body)
        result = run(tmp_path, world)
        after = files(tmp_path)
        assert result.status == "updated", result.errors
        assert result.changed_paths == sorted(
            name for name, content in after.items() if before.get(name) != content
        )
    assert set(result.changed_paths) == {county.INVENTORY_PATH, county.STATE_PATH}


def test_corrupt_reused_snapshot_stops_before_any_promotion(tmp_path: Path, world: dict) -> None:
    assert run(tmp_path, world).status == "updated"
    old = (tmp_path / county.INVENTORY_PATH).read_bytes()
    snapshot = tmp_path / f"{county.SNAPSHOT_PREFIX}{county._digest(old)}.jsonl"
    snapshot.parent.mkdir(parents=True)
    snapshot.write_bytes(b"corrupted immutable snapshot")
    before = files(tmp_path)
    mutate(world, PDF, pdf_bytes("amendment"))
    result = run(tmp_path, world)
    assert result.status == "failed" and "snapshot is corrupt" in " ".join(result.errors)
    assert files(tmp_path) == before


def test_reappearing_source_uses_new_observation_time_without_rewriting_original(
    tmp_path: Path, world: dict,
) -> None:
    assert run(tmp_path, world).status == "updated"
    mutate(world, PDF, pdf_bytes("amendment"))
    assert run(tmp_path, world).status == "updated"
    mutate(world, PDF, PDF_BYTES)
    later = NOW + timedelta(days=1)
    result = county.collect_county_reacquisition(
        tmp_path, plan(), fetch=world.__getitem__, now=later,
    )
    assert result.status == "updated"
    assert not any(path.startswith(county.RAW_PREFIX) for path in result.changed_paths)
    state = county.CountyReacquisitionState.model_validate_json(
        (tmp_path / county.STATE_PATH).read_bytes()
    )
    assert state.sources[PDF].first_retrieved_at == later
    before = files(tmp_path)
    assert run(tmp_path, world).status == "no_change"
    assert files(tmp_path) == before


@pytest.mark.parametrize("malformed", ["missing_region", "duplicate_region", "wrong_heading",
                                       "duplicate_heading", "selected_only_in_footer"])
def test_catalog_identity_and_content_region_fail_closed(
    tmp_path: Path, world: dict, malformed: str,
) -> None:
    body = HTML
    if malformed == "missing_region":
        body = body.replace(b'id="page"', b'id="unrelated"')
    elif malformed == "duplicate_region":
        body = body.replace(b"<footer>", b'<div id="page"></div><footer>')
    elif malformed == "wrong_heading":
        body = body.replace(b"County sources", b"Unrelated page")
    elif malformed == "duplicate_heading":
        body = body.replace(b"</h1>", b"</h1><h1>Another heading</h1>")
    else:
        body = body.replace(b'href="/b.pdf"', b'href="/other.pdf"')
        body = body.replace(b"<footer>", b'<footer><a href="/b.pdf">Fees</a>')
    mutate(world, CATALOG, body)
    result = run(tmp_path, world)
    assert result.status == "failed" and not result.manifest_complete
    assert not files(tmp_path)


@pytest.mark.parametrize("malformed", ["header_only", "truncated", "invalid_structure",
                                       "repaired", "encrypted"])
def test_corrupt_or_inaccessible_pdf_cannot_be_promoted(
    tmp_path: Path, world: dict, malformed: str,
) -> None:
    bodies = {
        "header_only": b"%PDF-1.7\n", "truncated": PDF_BYTES[:128],
        "invalid_structure": b"%PDF-1.7\n%%EOF\n",
        "repaired": re.sub(rb"startxref\s+\d+", b"startxref\n0", PDF_BYTES),
        "encrypted": pdf_bytes(encrypted=True),
    }
    mutate(world, PDF, bodies[malformed])
    result = run(tmp_path, world)
    assert result.status == "failed" and not result.validation_passed
    assert not files(tmp_path)


def test_remaining_payload_budget_bounds_client_before_next_source(
    tmp_path: Path, world: dict, monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = county.CountySourceClient(0)
    caps = []

    def fetch(url: str) -> FetchResult:
        caps.append(client.max_response_bytes)
        return world[url]

    monkeypatch.setattr(county.CountySourceClient, "__call__", lambda _, url: fetch(url))
    limit = len(HTML) + len(PDF_BYTES)
    result = county.collect_county_reacquisition(
        tmp_path, plan(), fetch=client, now=NOW, max_total_bytes=limit,
    )
    assert result.status == "failed" and "exhausted" in " ".join(result.errors)
    assert caps == [limit, len(PDF_BYTES)]
    assert not files(tmp_path)


def test_changed_bytes_preserve_previous_versions_and_original_retrieval_times(
    tmp_path: Path, world: dict,
) -> None:
    assert run(tmp_path, world).status == "updated"
    before = files(tmp_path)
    mutate(world, PDF, pdf_bytes("amendment"))
    result = county.collect_county_reacquisition(tmp_path, plan(), fetch=world.__getitem__,
                                                now=NOW + timedelta(days=1))
    assert result.status == "updated", result.errors
    for name in (county.INVENTORY_PATH, county.STATE_PATH):
        snapshot = f"{county.SNAPSHOT_PREFIX}{county._digest(before[name])}{Path(name).suffix}"
        assert (tmp_path / snapshot).read_bytes() == before[name]
    for name, content in before.items():
        if name.startswith(county.RAW_PREFIX):
            assert (tmp_path / name).read_bytes() == content
    state = county.CountyReacquisitionState.model_validate_json(
        (tmp_path / county.STATE_PATH).read_bytes()
    )
    assert state.sources[CATALOG].first_retrieved_at == NOW
    assert state.sources[PDF].first_retrieved_at == NOW + timedelta(days=1)
    before = files(tmp_path)
    mutate(world, CATALOG, HTML.replace(b"Navigation", b"New navigation"))
    assert run(tmp_path, world).status == "updated"
    assert files(tmp_path) != before, "No broad HTML normalization may hide catalog changes"


@pytest.mark.parametrize("change,error", [
    ("missing_label", "link or label disappeared"),
    ("missing_link", "link or label disappeared"),
    ("truncated_html", "terminator"),
    ("html_instead_of_pdf", "Unexpected source format"),
    ("pdf_instead_of_html", "Unexpected source format"),
    ("outside_redirect", "Unapproved"),
    ("wrong_county", "Unapproved"),
    ("unsupported", "Unrecognized"),
    ("challenge", "access challenge"),
])
def test_partial_sources_fail_before_derived_promotion(
    tmp_path: Path, world: dict, change: str, error: str,
) -> None:
    assert run(tmp_path, world).status == "updated"
    before = files(tmp_path)
    if change == "missing_label":
        mutate(world, CATALOG, HTML.replace(b"Land", b"Different"))
    elif change == "missing_link":
        mutate(world, CATALOG, HTML.replace(b"/b.pdf", b"/missing.pdf"))
    elif change == "truncated_html":
        mutate(world, CATALOG, HTML.replace(b"</html>", b""))
    elif change == "html_instead_of_pdf":
        mutate(world, PDF, HTML)
    elif change == "pdf_instead_of_html":
        mutate(world, CATALOG, PDF_BYTES)
    elif change in {"outside_redirect", "wrong_county"}:
        host = "external.example" if change == "outside_redirect" else "www.clearcreekcounty.us"
        world[PDF] = FetchResult(f"https://{host}/a.pdf", PDF_BYTES, "application/pdf")
    elif change == "unsupported":
        mutate(world, OTHER, b"unrecognized")
    else:
        mutate(world, CATALOG, b"<html><title>Access denied</title></html>")
    result = run(tmp_path, world)
    assert result.status == "failed" and error in " ".join(result.errors)
    assert not result.validation_passed and not result.manifest_complete
    assert result.changed_paths == []
    assert files(tmp_path) == before


def test_selected_fetch_exception_is_failure_not_partial_success(
    tmp_path: Path, world: dict,
) -> None:
    del world[OTHER]
    result = run(tmp_path, world)
    assert result.status == "failed"
    assert result.documents_checked == 1
    assert not files(tmp_path)


@pytest.mark.parametrize("limits", [
    {"max_total_bytes": 1}, {"max_source_bytes": 10}, {"max_total_bytes": 0},
    {"max_source_bytes": 30_000_001}, {"max_total_bytes": 100_000_001},
])
def test_hard_limits_fail_without_promotion(tmp_path: Path, world: dict, limits: dict) -> None:
    result = run(tmp_path, world, **limits)
    assert result.status == "failed" and not files(tmp_path)


def test_whole_zoning_source_fits_explicit_thirty_megabyte_cap(tmp_path: Path, world: dict) -> None:
    with pymupdf.open(stream=PDF_BYTES, filetype="pdf") as document:
        stream = document.get_new_xref()
        document.update_object(stream, "<<>>")
        document.update_stream(stream, b" " * 25_000_000, compress=False)
        mutate(world, PDF, document.tobytes(deflate=False))
    result = run(tmp_path, world)
    assert result.status == "updated"
    assert result.downloaded_bytes > 25_000_000


@pytest.mark.parametrize("field,value", [
    ("source_id", "catalog"), ("url", CATALOG),
    ("url", "https://www.clearcreekcounty.us/a.pdf"),
    ("url", "https://www.jeffco.us/ordinary-page"),
    ("authority_name", "Unrelated county"), ("catalog_url", "https://www.jeffco.us/unknown"),
    ("source_label", "   "),
])
def test_manifest_rejects_ambiguous_or_mismatched_selection(field: str, value: str) -> None:
    payload = plan().model_dump()
    payload["documents"][0][field] = value
    with pytest.raises(ValidationError):
        county.CountyPilotManifest.model_validate(payload)


def test_manifest_count_limits_and_unknown_fields() -> None:
    payload = plan().model_dump()
    payload["documents"] *= 16
    with pytest.raises(ValidationError):
        county.CountyPilotManifest.model_validate(payload)
    payload = plan().model_dump()
    payload["catalogs"] *= 5
    with pytest.raises(ValidationError):
        county.CountyPilotManifest.model_validate(payload)
    payload = plan().model_dump()
    payload["inferred_currentness"] = True
    with pytest.raises(ValidationError):
        county.CountyPilotManifest.model_validate(payload)


def test_prior_manifest_changes_require_explicit_migration(tmp_path: Path, world: dict) -> None:
    assert run(tmp_path, world).status == "updated"
    updated = plan().model_copy(update={"boundary": "Changed scope"})
    result = county.collect_county_reacquisition(
        tmp_path, updated, fetch=world.__getitem__, now=NOW
    )
    assert result.status == "failed" and "migration" in " ".join(result.errors)


@pytest.mark.parametrize("mutation", ["missing_state", "bad_inventory", "missing_original",
                                      "bad_original", "wrong_map_key", "wrong_ids", "provenance"])
def test_corrupt_prior_state_stops_before_fetching(
    tmp_path: Path, world: dict, mutation: str,
) -> None:
    assert run(tmp_path, world).status == "updated"
    path = tmp_path / county.STATE_PATH
    state = json.loads(path.read_text())
    if mutation == "missing_state":
        path.unlink()
    elif mutation == "bad_inventory":
        (tmp_path / county.INVENTORY_PATH).write_bytes(b"bad inventory")
    elif mutation == "missing_original":
        (tmp_path / state["sources"][PDF]["path"]).unlink()
    elif mutation == "bad_original":
        (tmp_path / state["sources"][PDF]["path"]).write_bytes(b"wrong original")
    elif mutation == "wrong_map_key":
        state["sources"][OTHER] = state["sources"].pop(PDF)
    elif mutation == "wrong_ids":
        state["document_ids"] = ["unexpected"]
    else:
        state["sources"][PDF]["content_type"] = "changed/provenance"
    if mutation not in {"missing_state", "bad_inventory", "missing_original", "bad_original"}:
        path.write_text(json.dumps(state))
    result = county.collect_county_reacquisition(tmp_path, plan(), fetch=lambda _: pytest.fail(
        "Corrupt prior state must fail before network access"), now=NOW)
    assert result.status == "failed"


def test_derived_write_failure_rolls_back_and_keeps_only_complete_immutable_bytes(
    tmp_path: Path, world: dict, monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert run(tmp_path, world).status == "updated"
    before = files(tmp_path)
    mutate(world, PDF, pdf_bytes("update"))
    replace = county._replace
    failed = False

    def fail_once(path: Path, content: bytes) -> None:
        nonlocal failed
        if path.name.endswith("-state.json") and not failed:
            failed = True
            raise OSError("simulated storage failure")
        replace(path, content)

    monkeypatch.setattr(county, "_replace", fail_once)
    result = run(tmp_path, world)
    assert result.status == "failed" and result.changed_paths == []
    for name, content in before.items():
        assert (tmp_path / name).read_bytes() == content
    for path in (tmp_path / county.RAW_PREFIX).iterdir():
        assert county._digest(path.read_bytes()) == path.stem
    assert run(tmp_path, world).status == "updated"


def test_first_transaction_rollback_removes_partial_derived_inventory(
    tmp_path: Path, world: dict, monkeypatch: pytest.MonkeyPatch,
) -> None:
    replace = county._replace

    def fail_state(path: Path, content: bytes) -> None:
        if path.name.endswith("-state.json"):
            raise OSError("failure")
        replace(path, content)

    monkeypatch.setattr(county, "_replace", fail_state)
    assert run(tmp_path, world).status == "failed"
    assert not (tmp_path / county.INVENTORY_PATH).exists()
    assert not (tmp_path / county.STATE_PATH).exists()


def test_output_symlinks_and_path_traversal_are_rejected(tmp_path: Path, world: dict) -> None:
    (tmp_path / "_RAW_ARCHIVE").symlink_to(tmp_path.parent, target_is_directory=True)
    assert run(tmp_path, world).status == "failed"
    with pytest.raises(ValueError):
        county._target(tmp_path, "../escape")
    with pytest.raises(ValueError):
        county._target(tmp_path, "/escape")


def test_immutable_writes_reject_corruption_and_survive_matching_race(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "original"
    county._immutable(target, b"first")
    county._immutable(target, b"first")
    with pytest.raises(ValueError, match="differs"):
        county._immutable(target, b"changed")
    target.unlink()

    def raced(source: Path, destination: Path) -> None:
        destination.write_bytes(source.read_bytes())
        raise FileExistsError("another process published the identical original")

    monkeypatch.setattr(county.os, "link", raced)
    county._immutable(target, b"identical")
    assert target.read_bytes() == b"identical"
    target.unlink()

    def corrupt_race(source: Path, destination: Path) -> None:
        destination.write_bytes(b"different")
        raise FileExistsError("race")

    monkeypatch.setattr(county.os, "link", corrupt_race)
    with pytest.raises(ValueError, match="Concurrent"):
        county._immutable(target, b"expected")
    assert sorted(p.name for p in tmp_path.iterdir()) == ["original"]


@pytest.mark.parametrize("url", ["http://www.jeffco.us/a.pdf", "https://external.example/a.pdf",
                                  "https://user@www.jeffco.us/a.pdf",
                                  "https://www.jeffco.us:444/a.pdf",
                                  "https://www.jeffco.us/a\n.pdf"])
def test_outbound_url_allowlist(url: str) -> None:
    with pytest.raises(ValueError):
        county.require_county_url(url)


def test_client_validates_redirect_before_following(monkeypatch: pytest.MonkeyPatch) -> None:
    client = county.CountySourceClient(delay=0)
    calls = []

    def request(url: str) -> tuple[int, dict, bytes]:
        calls.append(url)
        return 302, {"location": "https://external.example/a.pdf"}, b""

    monkeypatch.setattr(client, "_request", request)
    with pytest.raises(ValueError, match="Unapproved"):
        client(PDF)
    assert calls == [PDF]
    client.close()


def test_client_retries_temporary_errors_and_follows_same_county_redirect(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = county.CountySourceClient(delay=0.1)
    sleeps = []
    responses = iter([(503, {}, b""), (302, {"location": OTHER}, b""),
                      (200, {"content-type": "application/pdf"}, PDF_BYTES)])
    monkeypatch.setattr(county.time, "sleep", sleeps.append)
    monkeypatch.setattr(client, "_request", lambda _: next(responses))
    result = client(PDF)
    assert result.url == OTHER and result.content == PDF_BYTES
    assert sleeps
    with pytest.raises(ValueError):
        county.CountySourceClient(-1)


@pytest.mark.parametrize("response,error", [
    ((403, {}, b"denied"), "HTTP 403"), ((206, {}, PDF_BYTES), "HTTP 206"),
    ((302, {}, b""), "Location"), ((302, {"location": PDF}, b""), "redirect limit"),
    ((503, {}, b""), "HTTP 503"),
    ((200, {"cf-mitigated": "challenge"}, HTML), "access challenge"),
    ((200, {}, b""), "Empty source"),
])
def test_client_source_errors_are_never_success(
    monkeypatch: pytest.MonkeyPatch, response: tuple, error: str,
) -> None:
    client = county.CountySourceClient(0)
    monkeypatch.setattr(county.time, "sleep", lambda _: None)
    monkeypatch.setattr(client, "_request", lambda _: response)
    with pytest.raises(ValueError, match=error):
        client(PDF)


def test_curl_request_uses_plain_https_bounded_files_and_last_header_block(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def curl(command: list[str], **kwargs) -> subprocess.CompletedProcess:
        assert "--location" not in command and "--insecure" not in command
        assert command[1] == "--disable"
        assert command[command.index("--max-filesize") + 1] == "30000000"
        assert "ProjectGeode" in command[command.index("--user-agent") + 1]
        Path(command[command.index("--output") + 1]).write_bytes(PDF_BYTES)
        Path(command[command.index("--dump-header") + 1]).write_bytes(
            b"HTTP/1.1 200 Connection established\r\nProxy: yes\r\n\r\n"
            b"HTTP/2 200\r\nContent-Type: application/pdf\r\nIgnored-line\r\n\r\n")
        return subprocess.CompletedProcess(command, 0, "200", "")

    monkeypatch.setattr(county.subprocess, "run", curl)
    status, headers, body = county.CountySourceClient(0)._request(PDF)
    assert status == 200 and headers == {"content-type": "application/pdf"} and body == PDF_BYTES


@pytest.mark.parametrize("failure", ["missing_curl", "timeout", "transport", "bad_status",
                                    "missing_headers", "missing_body", "oversized"])
def test_curl_transport_failures_are_explicit(
    monkeypatch: pytest.MonkeyPatch, failure: str,
) -> None:
    def curl(command: list[str], **kwargs) -> subprocess.CompletedProcess:
        if failure == "missing_curl":
            raise FileNotFoundError("curl")
        if failure == "timeout":
            raise subprocess.TimeoutExpired(command, 50)
        if failure == "transport":
            return subprocess.CompletedProcess(command, 63, "200", "too large")
        if failure != "missing_headers":
            Path(command[command.index("--dump-header") + 1]).write_bytes(b"HTTP/2 200\r\n\r\n")
        if failure != "missing_body":
            Path(command[command.index("--output") + 1]).write_bytes(PDF_BYTES)
        return subprocess.CompletedProcess(
            command, 0, "bad" if failure == "bad_status" else "200", ""
        )

    monkeypatch.setattr(county.subprocess, "run", curl)
    if failure == "oversized":
        monkeypatch.setattr(county, "MAX_SOURCE_BYTES", 1)
    with pytest.raises(ValueError):
        county.CountySourceClient(0)._request(PDF)


@pytest.mark.parametrize("body", [b"PK\x03\x04archive", b"\xd0\xcf\x11\xe0document",
                                  b"{\\rtf1 document}"])
def test_unreviewed_word_formats_remain_outside_selected_pilot(body: bytes) -> None:
    with pytest.raises(ValueError, match="Unrecognized"):
        county._suffix(FetchResult(PDF, body, "application/octet-stream"), 1000)


def test_catalog_base_url_and_unknown_candidate_labels(tmp_path: Path, world: dict) -> None:
    mutate(world, CATALOG, HTML.replace(
        b"<body>", b'<head><base href="https://www.jeffco.us/"></head><body>'
    ))
    assert run(tmp_path, world).status == "updated"
    mutate(world, CATALOG, HTML.replace(b"<body>", b'<base href="/"><base href="/other"><body>'))
    result = run(tmp_path, world)
    assert result.status == "failed" and "ambiguous base" in " ".join(result.errors)


def test_report_writes_are_validated_snapshotted_and_symlink_safe(
    tmp_path: Path, world: dict,
) -> None:
    result = run(tmp_path / "corpus", world)
    output = tmp_path / "reports"
    county.write_run_report(result, output)
    original = (output / "report.json").read_bytes()
    county.write_run_report(result, output)
    assert not (output / "_SNAPSHOTS").exists()
    county.write_run_report(result.model_copy(update={"errors": ["test error"]}), output)
    assert (output / "_SNAPSHOTS" / f"{county._digest(original)}.json").read_bytes() == original
    (output / "changes.json").unlink()
    (output / "changes.json").symlink_to(output / "report.json")
    with pytest.raises(ValueError, match="symlink"):
        county.write_run_report(result, output)


def test_cli_success_failure_and_report_boundaries(
    tmp_path: Path, world: dict, monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(plan().model_dump_json())
    monkeypatch.setattr(county.CountySourceClient, "__call__", lambda _, url: world[url])
    args = ["--root", str(tmp_path), "--manifest", "manifest.json",
            "--report-dir", str(tmp_path / "reports"), "--delay", "0"]
    assert county.main(args) == 0
    del world[PDF]
    assert county.main(args) == 1
    manifest.write_text("invalid")
    assert county.main(args) == 1
    manifest.write_bytes(b" " * 1_000_001)
    assert county.main(args) == 1
    with pytest.raises(SystemExit):
        county.main([*args, "--delay", "-1"])
    with pytest.raises(SystemExit):
        county.main([*args, "--report-dir", str(tmp_path / "_RAW_ARCHIVE/reports")])


def test_timestamp_and_provenance_schema_invariants(tmp_path: Path, world: dict) -> None:
    result = county.collect_county_reacquisition(tmp_path, plan(), fetch=world.__getitem__,
                                                now=datetime(2026, 9, 10))
    assert result.status == "failed"
    assert run(tmp_path, world).status == "updated"
    record = json.loads((tmp_path / county.INVENTORY_PATH).read_text().splitlines()[0])
    for updates in [{"id": "wrong"}, {"review_required": False}, {"legal_status": "current"},
                    {"observed_at": "2026-09-10"}, {"source_url": PDF}]:
        with pytest.raises(ValidationError):
            county.CountyPreservationRecord.model_validate({**record, **updates})
    original = record["sources"][0]
    for updates in [{"sha256": "0" * 64}, {"first_retrieved_at": "2026-09-10"},
                    {"final_url": "https://www.clearcreekcounty.us/a.pdf"}]:
        with pytest.raises(ValidationError):
            county.CountySource.model_validate({**original, **updates})
