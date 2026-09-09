"""Transactional daily Register ingestion using source excerpts and fake downloads."""

from __future__ import annotations

import hashlib
import io
import json
import re
import sys
import zipfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

from geode.pipeline import register_daily as daily
from geode.schemas.models import CrosswalkEntry, LayerIndexRecord, RulemakingNotice
from geode.utils.file_io import iter_jsonl

FIXTURES = Path(__file__).parent / "fixtures" / "register_daily"
ISSUE = "https://www.sos.state.co.us/CCR/RegisterContents.do?publicationDay=08/25/2026"
HEARING = "https://www.sos.state.co.us/CCR/DisplayHearingDetails.do?trackingNumber=2026-00370"
INDEX_URL = daily.REGISTER_URL + "?pyear=2026"
SINCE = date(2026, 7, 1)
NOW = datetime(2026, 9, 7, 12, tzinfo=timezone.utc)
HISTORIC_PATH = "04_Rulemaking/2026/register_2026_Q2.jsonl"
DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


class FakeSources:
    """Serve deterministic fixture responses, rejecting any unexpected fetch."""

    def __init__(self) -> None:
        """Load official table excerpts and synthetic linked document bodies."""

        issue = (FIXTURES / "official_2026_08_25_excerpt.html").read_bytes()
        self.responses = {
            INDEX_URL: daily.FetchResult(INDEX_URL, _listing([ISSUE]), "text/html"),
            ISSUE: daily.FetchResult(ISSUE, issue, "text/html"),
            HEARING: daily.FetchResult(
                HEARING,
                (FIXTURES / "official_hearing_2026_00370_excerpt.html").read_bytes(),
                "text/html",
            ),
        }
        self.document_urls = [
            "https://www.sos.state.co.us" + path.decode()
            for path in re.findall(rb'href="(/CCR/Upload/[^\"]+\.docx)"', issue)
        ]
        for url in self.document_urls:
            self.responses[url] = daily.FetchResult(url, _docx(url), DOCX_MIME)
        self.calls: list[str] = []
        self.fail_url: str | None = None
        self.closed = False

    def __call__(self, url: str) -> daily.FetchResult:
        """Return a fixture or raise a simulated source outage."""

        self.calls.append(url)
        if url == self.fail_url:
            raise RuntimeError("Simulated official-source outage")
        assert url in self.responses, f"Unexpected source request: {url}"
        return self.responses[url]

    def set_html(self, url: str, content: bytes) -> None:
        """Replace a fixture response for a subsequent source check."""

        self.responses[url] = daily.FetchResult(url, content, "text/html")

    def close(self) -> None:
        """Record CLI resource cleanup without opening a network client."""

        self.closed = True


@pytest.fixture
def pilot_root(tmp_path: Path) -> Path:
    """Seed mutually consistent historical data without a prior pilot state."""

    root = tmp_path / "repository"
    historic = RulemakingNotice(
        id="RM-2026-historic",
        title="Synthetic historical fixture",
        notice_type="proposed",
        ccr_rule_affected="5_CCR_1001-9",
        agency_code="CDPHE_AQCC",
        summary="Synthetic historical notice retained by incremental refresh.",
        publication_date=date(2026, 6, 10),
        subject_tags=["rulemaking"],
        source_url="https://www.sos.state.co.us/CCR/RegisterContents.do?publicationDay=06/10/2026",
        confidence={"overall": 0.0},
    )
    index = LayerIndexRecord(
        id=historic.id,
        layer=daily.LAYER,
        entity_type="rulemaking_notice",
        title=historic.title,
        path=HISTORIC_PATH,
        meta_path=daily.META,
        source_url=historic.source_url,
        source_path=str(historic.source_url),
        last_updated=NOW - timedelta(days=70),
        sha256=hashlib.sha256(historic.model_dump_json().encode()).hexdigest(),
        confidence=0.0,
    )
    crosswalk = CrosswalkEntry(
        source_id=historic.id,
        source_type="rulemaking_notice",
        target_id=historic.ccr_rule_affected,
        target_type="regulation_rule",
        relationship="cites",
        confidence=0.0,
        data_retrieved=date(2026, 6, 10),
        source_url=historic.source_url,
    )
    manifest = daily.ExistingManifest.model_validate({
        "project": {"name": "Test fixture"},
        "data_layers": [{
            "id": daily.LAYER,
            "path": daily.LAYER,
            "record_count": 1,
            "last_checked": "2026-07-08",
            "staleness_days": 0,
            "status": "ready",
            "known_gaps": ["Historical sources require review."],
        }],
        "unrelated_metadata": {"preserve": True},
    })
    for relative in (HISTORIC_PATH, daily.META, daily.DATASET):
        _write(root, relative, (historic.model_dump_json() + "\n").encode())
    _write(root, daily.INDEX, (index.model_dump_json() + "\n").encode())
    _write(root, daily.CROSSWALK, (crosswalk.model_dump_json() + "\n").encode())
    _write(root, daily.MANIFEST, manifest.model_dump_json(indent=2).encode())
    return root


def test_first_refresh_preserves_history_and_resolves_proposal(pilot_root: Path) -> None:
    """Complete source rows extend the corpus while preserving historical records."""

    sources = FakeSources()
    old_quarter = (pilot_root / HISTORIC_PATH).read_bytes()
    old_notice = list(iter_jsonl(pilot_root / daily.META))[0]

    report = daily.refresh_register(pilot_root, SINCE, fetch=sources, now=NOW)

    assert report.status == "updated", report.errors
    assert report.validation_passed is True
    assert report.notices_added == 4
    assert report.notices_updated == 0
    assert report.publications_checked == 1
    rows = list(iter_jsonl(pilot_root / daily.META))
    assert len(rows) == 5
    assert next(row for row in rows if row["id"] == old_notice["id"]) == old_notice
    assert (pilot_root / HISTORIC_PATH).read_bytes() == old_quarter
    assert {row["id"] for row in iter_jsonl(pilot_root / daily.DATASET)} == {
        row["id"] for row in rows
    }
    assert {row["id"] for row in iter_jsonl(pilot_root / daily.INDEX)} == {
        row["id"] for row in rows
    }
    proposal = next(row for row in rows if row.get("edocket_tracking_number") == "2026-00370")
    assert proposal["ccr_rule_affected"] == "1_CCR_304-1"
    assert proposal["notice_type"] == "proposed"
    assert proposal["effective_date"] is None
    assert proposal["agency"] == "Facility Schools Board"
    assert proposal["agency_code"] is None
    assert HEARING in sources.calls
    provenance = next(
        row for row in iter_jsonl(pilot_root / daily.PROVENANCE)
        if row["notice_id"] == proposal["id"]
    )
    assert "CCR Number: 1 CCR 304-1" in provenance["resolved_ccr_evidence"]
    assert {source["url"] for source in provenance["sources"]} >= {ISSUE, HEARING}
    manifest = json.loads((pilot_root / daily.MANIFEST).read_bytes())
    assert manifest["data_layers"][0]["last_checked"] == "2026-07-08"
    assert manifest["data_layers"][0]["record_count"] == 5
    assert daily.PROVENANCE in manifest["data_layers"][0]["derived_files"]
    assert daily.STATE in manifest["data_layers"][0]["derived_files"]
    assert manifest["unrelated_metadata"] == {"preserve": True}
    assert "Historical sources require review." in manifest["data_layers"][0]["known_gaps"]
    assert len(list(iter_jsonl(pilot_root / daily.CROSSWALK))) == 5
    state = daily.RefreshState.model_validate_json((pilot_root / daily.STATE).read_bytes())
    for source in state.sources.values():
        archived = (pilot_root / source.path).read_bytes()
        assert archived == sources.responses[source.url].content
        assert hashlib.sha256(archived).hexdigest() == source.sha256


def test_second_check_keeps_all_repository_bytes_stable(pilot_root: Path) -> None:
    """An unchanged check on a later day must not rewrite state or provenance."""

    sources = FakeSources()
    _bootstrap(pilot_root, sources)
    before = _files(pilot_root)
    sources.calls.clear()

    report = daily.refresh_register(
        pilot_root, SINCE, fetch=sources, now=NOW + timedelta(days=1),
    )

    assert report.status == "no_change", report.errors
    assert report.validation_passed is True
    assert report.changed_paths == []
    assert report.notices_added == report.notices_updated == 0
    assert len(sources.calls) == len(sources.responses)
    assert _files(pilot_root) == before


@pytest.mark.parametrize("changed_source", ["issue", "document"])
def test_changed_source_is_preserved_without_overwriting_prior_evidence(
    pilot_root: Path, changed_source: str,
) -> None:
    """Both changed issue rows and document-only corrections remain reviewable."""

    sources = FakeSources()
    _bootstrap(pilot_root, sources)
    old_archives = _files(pilot_root / "_RAW_ARCHIVE")
    old_metadata = (pilot_root / daily.META).read_bytes()
    if changed_source == "issue":
        sources.set_html(
            ISSUE, sources.responses[ISSUE].content.replace(b"09/14/2026", b"09/15/2026"),
        )
    else:
        url = sources.document_urls[0]
        sources.responses[url] = daily.FetchResult(url, _docx("Corrected attachment"), DOCX_MIME)

    report = daily.refresh_register(
        pilot_root, SINCE, fetch=sources, now=NOW + timedelta(days=1),
    )

    assert report.status == "updated", report.errors
    assert daily.PROVENANCE in report.changed_paths
    assert daily.STATE in report.changed_paths
    for name, body in old_archives.items():
        assert (pilot_root / "_RAW_ARCHIVE" / name).read_bytes() == body
    assert len(_files(pilot_root / "_RAW_ARCHIVE")) > len(old_archives)
    if changed_source == "issue":
        adopted = next(
            row for row in iter_jsonl(pilot_root / daily.META) if row["notice_type"] == "adopted"
        )
        assert adopted["effective_date"] == "2026-09-15"
        assert report.notices_updated >= 1
    else:
        assert (pilot_root / daily.META).read_bytes() == old_metadata
        assert report.notices_updated == 0
    stable = _files(pilot_root)
    assert daily.refresh_register(
        pilot_root, SINCE, fetch=sources, now=NOW + timedelta(days=2),
    ).status == "no_change"
    assert _files(pilot_root) == stable


def test_source_failure_keeps_corpus_and_state_unchanged_and_reports_failure(
    pilot_root: Path, tmp_path: Path,
) -> None:
    """An attachment outage is a failed check, with no partial corpus update."""

    sources = FakeSources()
    _bootstrap(pilot_root, sources)
    before = _files(pilot_root)
    sources.fail_url = sources.document_urls[-1]

    report = daily.refresh_register(pilot_root, SINCE, fetch=sources, now=NOW)

    assert report.status == "failed"
    assert report.validation_passed is False
    assert report.changed_paths == []
    assert "Simulated official-source outage" in report.errors[0]
    assert _files(pilot_root) == before
    reports = tmp_path / "run-reports"
    daily.write_run_report(report, reports)
    saved = daily.RefreshReport.model_validate_json((reports / "report.json").read_bytes())
    assert saved.status == "failed"
    assert "**failed**" in (reports / "summary.md").read_text()


@pytest.mark.parametrize(
    "mutation", ["duplicate_row", "removed_row", "empty_listing", "removed_issue"],
)
def test_coverage_regressions_fail_without_mutating_canonical_files(
    pilot_root: Path, mutation: str,
) -> None:
    """Source omissions or duplicate identities cannot silently remove coverage."""

    sources = FakeSources()
    other_issue = ISSUE.replace("08/25/2026", "08/10/2026")
    if mutation == "removed_issue":
        sources.set_html(INDEX_URL, _listing([other_issue, ISSUE]))
        sources.set_html(other_issue, sources.responses[ISSUE].content)
    _bootstrap(pilot_root, sources)
    before = _files(pilot_root)
    issue = sources.responses[ISSUE].content
    if mutation == "duplicate_row":
        issue = re.sub(rb"(<tbody>\s*)(<tr>.*?</tr>)", rb"\1\2\2", issue, count=1, flags=re.S)
        sources.set_html(ISSUE, issue)
    elif mutation == "removed_row":
        bodies = list(re.finditer(rb"<tbody>.*?</tbody>", issue, re.S))
        last = bodies[-1]
        sources.set_html(ISSUE, issue[:last.start()] + b"<tbody></tbody>" + issue[last.end():])
    elif mutation == "empty_listing":
        sources.set_html(INDEX_URL, _listing([]))
    else:
        sources.set_html(INDEX_URL, _listing([ISSUE]))

    report = daily.refresh_register(pilot_root, SINCE, fetch=sources, now=NOW)

    assert report.status == "failed", mutation
    assert report.validation_passed is False
    assert report.errors
    assert _files(pilot_root) == before


def test_unapproved_final_response_url_fails_before_writes(pilot_root: Path) -> None:
    """A callback's final URL is validated independently from the requested URL."""

    sources = FakeSources()
    before = _files(pilot_root)
    sources.responses[INDEX_URL] = daily.FetchResult(
        "https://external.example/CCR/RegisterHome.do", _listing([ISSUE]), "text/html",
    )

    report = daily.refresh_register(pilot_root, SINCE, fetch=sources, now=NOW)

    assert report.status == "failed"
    assert "Unapproved source URL" in report.errors[0]
    assert _files(pilot_root) == before


@pytest.mark.parametrize("existing_pilot", [False, True])
def test_write_failure_rolls_back_new_and_replaced_canonical_files(
    pilot_root: Path, monkeypatch: pytest.MonkeyPatch, existing_pilot: bool,
) -> None:
    """A mid-transaction disk error restores prior bytes and removes new outputs."""

    sources = FakeSources()
    if existing_pilot:
        _bootstrap(pilot_root, sources)
        sources.set_html(
            ISSUE, sources.responses[ISSUE].content.replace(b"09/14/2026", b"09/15/2026"),
        )
    before = _canonical_files(pilot_root)
    original_replace = daily.os.replace
    failed = False

    def fail_state_once(source: Path, target: Path) -> None:
        nonlocal failed
        if Path(target) == pilot_root / daily.STATE and not failed:
            failed = True
            raise OSError("Simulated disk write failure")
        original_replace(source, target)

    monkeypatch.setattr(daily.os, "replace", fail_state_once)

    report = daily.refresh_register(pilot_root, SINCE, fetch=sources, now=NOW)

    assert failed is True
    assert report.status == "failed"
    assert "Simulated disk write failure" in report.errors[0]
    assert report.changed_paths == []
    assert report.notices_added == report.notices_updated == 0
    assert _canonical_files(pilot_root) == before
    assert not list(pilot_root.rglob("*.daily-tmp"))
    assert not list(pilot_root.rglob("*.rollback-tmp"))


def test_corrupt_content_addressed_archive_is_never_overwritten(pilot_root: Path) -> None:
    """Existing bytes at a source hash path must be checked before reuse."""

    sources = FakeSources()
    digest = hashlib.sha256(sources.responses[INDEX_URL].content).hexdigest()
    archive = daily.RAW_PREFIX + digest + ".html"
    _write(pilot_root, archive, b"Corrupted source evidence")
    before = _files(pilot_root)

    report = daily.refresh_register(pilot_root, SINCE, fetch=sources, now=NOW)

    assert report.status == "failed"
    assert "Corrupt content-addressed source" in report.errors[0]
    assert _files(pilot_root) == before


@pytest.mark.parametrize("quarter_exists", [False, True])
def test_touched_quarter_preserves_or_rejects_missing_historical_records(
    pilot_root: Path, quarter_exists: bool,
) -> None:
    """An existing historical row in the touched quarter cannot silently disappear."""

    historic = RulemakingNotice.model_validate(next(iter_jsonl(pilot_root / daily.META)))
    historic = historic.model_copy(update={"publication_date": date(2026, 8, 10)})
    quarter_path = "04_Rulemaking/2026/register_2026_Q3.jsonl"
    index = LayerIndexRecord.model_validate(next(iter_jsonl(pilot_root / daily.INDEX)))
    index = index.model_copy(update={"path": quarter_path})
    for name in (daily.META, daily.DATASET):
        _write(pilot_root, name, (historic.model_dump_json() + "\n").encode())
    _write(pilot_root, daily.INDEX, (index.model_dump_json() + "\n").encode())
    (pilot_root / HISTORIC_PATH).unlink()
    if quarter_exists:
        _write(pilot_root, quarter_path, (historic.model_dump_json() + "\n").encode())
    before = _files(pilot_root)

    report = daily.refresh_register(pilot_root, SINCE, fetch=FakeSources(), now=NOW)

    if quarter_exists:
        assert report.status == "updated", report.errors
        rows = list(iter_jsonl(pilot_root / quarter_path))
        assert len(rows) == 5
        assert next(row for row in rows if row["id"] == historic.id) == historic.model_dump(
            mode="json",
        )
    else:
        assert report.status == "failed"
        assert _files(pilot_root) == before


def test_provenance_repair_archives_state_before_adding_snapshot_reference(
    pilot_root: Path,
) -> None:
    """A derived-file repair must archive state even when its source map is unchanged."""

    sources = FakeSources()
    _bootstrap(pilot_root, sources)
    before_state = (pilot_root / daily.STATE).read_bytes()
    rows = [
        daily.NoticeProvenance.model_validate(row)
        for row in iter_jsonl(pilot_root / daily.PROVENANCE)
    ]
    rows[0] = rows[0].model_copy(update={"resolved_ccr_evidence": "Stale local evidence value"})
    _write(
        pilot_root, daily.PROVENANCE,
        b"".join((row.model_dump_json() + "\n").encode() for row in rows),
    )

    report = daily.refresh_register(pilot_root, SINCE, fetch=sources, now=NOW)

    assert report.status == "updated", report.errors
    assert report.notices_added == report.notices_updated == 0
    state_snapshot = (
        pilot_root / daily.SNAPSHOT_PREFIX / (hashlib.sha256(before_state).hexdigest() + ".json")
    )
    assert state_snapshot.read_bytes() == before_state


def test_preexisting_temporary_symlink_cannot_escape_project_root(
    pilot_root: Path, tmp_path: Path,
) -> None:
    """Reserved temporary paths must not allow writes through an external symlink."""

    sentinel = tmp_path / "outside-corpus.txt"
    sentinel.write_bytes(b"Outside file must remain untouched")
    temporary = pilot_root / (daily.META + ".daily-tmp")
    temporary.symlink_to(sentinel)
    before_meta = (pilot_root / daily.META).read_bytes()

    report = daily.refresh_register(pilot_root, SINCE, fetch=FakeSources(), now=NOW)

    assert sentinel.read_bytes() == b"Outside file must remain untouched"
    assert not (pilot_root / daily.META).is_symlink()
    if report.status == "failed":
        assert (pilot_root / daily.META).read_bytes() == before_meta
    else:
        assert report.status == "updated"
        assert len(list(iter_jsonl(pilot_root / daily.META))) == 5


def test_redirect_to_wrong_official_issue_cannot_change_publication_identity(
    pilot_root: Path,
) -> None:
    """A permitted SOS host does not make a different issue an equivalent source."""

    sources = FakeSources()
    sources.responses[ISSUE] = daily.FetchResult(
        ISSUE.replace("08/25/2026", "08/10/2026"), sources.responses[ISSUE].content, "text/html",
    )
    before = _files(pilot_root)

    report = daily.refresh_register(pilot_root, SINCE, fetch=sources, now=NOW)

    assert report.status == "failed"
    assert _files(pilot_root) == before


def test_unchanged_notice_keeps_one_crosswalk_with_original_historical_link(
    pilot_root: Path,
) -> None:
    """Updating source text must not duplicate relation identities or lose old links."""

    sources = FakeSources()
    before_link = next(iter_jsonl(pilot_root / daily.CROSSWALK))
    _bootstrap(pilot_root, sources)
    sources.set_html(
        ISSUE, sources.responses[ISSUE].content.replace(b"09/14/2026", b"09/15/2026"),
    )

    report = daily.refresh_register(pilot_root, SINCE, fetch=sources, now=NOW)

    assert report.status == "updated", report.errors
    links = list(iter_jsonl(pilot_root / daily.CROSSWALK))
    keys = [(row["source_id"], row.get("target_id"), row["relationship"]) for row in links]
    assert len(keys) == len(set(keys)) == 5
    assert next(row for row in links if row["source_id"] == "RM-2026-historic") == before_link
    adopted = next(
        row for row in iter_jsonl(pilot_root / daily.META) if row["notice_type"] == "adopted"
    )
    adopted_link = next(row for row in links if row["source_id"] == adopted["id"])
    assert adopted_link["source_evidence"] == adopted["source_evidence"]


def test_no_change_check_rejects_missing_previously_managed_quarter(pilot_root: Path) -> None:
    """Identical remote sources cannot certify an incomplete local pilot corpus."""

    sources = FakeSources()
    _bootstrap(pilot_root, sources)
    (pilot_root / "04_Rulemaking/2026/register_2026_Q3.jsonl").unlink()
    before = _files(pilot_root)
    sources.calls.clear()

    report = daily.refresh_register(pilot_root, SINCE, fetch=sources, now=NOW)

    assert report.status == "failed"
    assert report.validation_passed is False
    assert sources.calls == []
    assert _files(pilot_root) == before


@pytest.mark.parametrize("since", [date(2026, 9, 10), date(2023, 1, 1)])
def test_invalid_pilot_window_fails_before_fetching(pilot_root: Path, since: date) -> None:
    """Future or unbounded historical windows cannot trigger collection."""

    sources = FakeSources()
    before = _files(pilot_root)

    report = daily.refresh_register(pilot_root, since, fetch=sources, now=NOW)

    assert report.status == "failed"
    assert sources.calls == []
    assert _files(pilot_root) == before


def test_changing_existing_window_requires_review(pilot_root: Path) -> None:
    """A scheduler configuration change cannot silently expand or shrink coverage."""

    sources = FakeSources()
    _bootstrap(pilot_root, sources)
    before = _files(pilot_root)
    sources.calls.clear()

    report = daily.refresh_register(pilot_root, date(2026, 8, 1), fetch=sources, now=NOW)

    assert report.status == "failed"
    assert "migration" in report.errors[0]
    assert sources.calls == []
    assert _files(pilot_root) == before


@pytest.mark.parametrize("corruption", [
    "duplicate_metadata", "missing_index", "missing_dataset", "dataset_values",
    "quarter_values", "index_path",
])
def test_inconsistent_existing_identity_fails_before_fetching(
    pilot_root: Path, corruption: str,
) -> None:
    """The collector cannot silently reconcile ambiguous or incomplete metadata."""

    if corruption == "duplicate_metadata":
        original = (pilot_root / daily.META).read_bytes()
        _write(pilot_root, daily.META, original + original)
    elif corruption == "missing_index":
        (pilot_root / daily.INDEX).unlink()
    elif corruption == "missing_dataset":
        (pilot_root / daily.DATASET).unlink()
    elif corruption in {"dataset_values", "quarter_values"}:
        name = daily.DATASET if corruption == "dataset_values" else HISTORIC_PATH
        row = RulemakingNotice.model_validate(next(iter_jsonl(pilot_root / name)))
        row = row.model_copy(update={"summary": "A conflicting historical source statement."})
        _write(pilot_root, name, (row.model_dump_json() + "\n").encode())
    else:
        row = LayerIndexRecord.model_validate(next(iter_jsonl(pilot_root / daily.INDEX)))
        row = row.model_copy(update={"path": "04_Rulemaking/2026/unexpected.jsonl"})
        _write(pilot_root, daily.INDEX, (row.model_dump_json() + "\n").encode())
    sources = FakeSources()
    before = _files(pilot_root)

    report = daily.refresh_register(pilot_root, SINCE, fetch=sources, now=NOW)

    assert report.status == "failed"
    assert sources.calls == []
    assert _files(pilot_root) == before


@pytest.mark.parametrize("limit", ["MAX_SOURCES", "MAX_TOTAL_BYTES", "MAX_SOURCE_BYTES"])
def test_download_limits_never_publish_partial_coverage(
    pilot_root: Path, monkeypatch: pytest.MonkeyPatch, limit: str,
) -> None:
    """Exceeding any download bound must stop the whole transaction."""

    monkeypatch.setattr(daily, limit, 2)
    before = _files(pilot_root)

    report = daily.refresh_register(pilot_root, SINCE, fetch=FakeSources(), now=NOW)

    assert report.status == "failed"
    assert report.validation_passed is False
    assert report.changed_paths == []
    assert _files(pilot_root) == before


@pytest.mark.parametrize("body,mime", [
    (b"", "text/html"),
    (b"<html><body>Access denied</body></html>", "text/html"),
    (b"%PDF-1.4 fixture", "application/pdf"),
    (b"Unexpected binary source", "application/octet-stream"),
])
def test_invalid_index_responses_cannot_count_as_success(
    pilot_root: Path, body: bytes, mime: str,
) -> None:
    """An empty, blocked, non-HTML, or unrecognized index cannot verify coverage."""

    sources = FakeSources()
    sources.responses[INDEX_URL] = daily.FetchResult(INDEX_URL, body, mime)
    before = _files(pilot_root)

    report = daily.refresh_register(pilot_root, SINCE, fetch=sources, now=NOW)

    assert report.status == "failed"
    assert _files(pilot_root) == before


def test_document_link_served_html_fails_without_reporting_uncommitted_additions(
    pilot_root: Path,
) -> None:
    """A 200 HTML error page cannot be archived as a successfully downloaded rule."""

    sources = FakeSources()
    url = sources.document_urls[-1]
    sources.set_html(url, b"<html><body>The requested document is unavailable.</body></html>")
    before = _files(pilot_root)

    report = daily.refresh_register(pilot_root, SINCE, fetch=sources, now=NOW)

    assert report.status == "failed"
    assert report.validation_passed is False
    assert report.notices_added == report.notices_updated == 0
    assert _files(pilot_root) == before


def test_valid_docx_served_as_generic_binary_is_preserved(pilot_root: Path) -> None:
    """The real SOS generic MIME type must not reject a valid Word package."""

    sources = FakeSources()
    url = sources.document_urls[0]
    sources.responses[url] = daily.FetchResult(
        url, sources.responses[url].content, "application/octet-stream",
    )

    report = daily.refresh_register(pilot_root, SINCE, fetch=sources, now=NOW)

    assert report.status == "updated", report.errors
    state = daily.RefreshState.model_validate_json((pilot_root / daily.STATE).read_bytes())
    source = state.sources[url]
    assert source.path.endswith(".docx")
    assert (pilot_root / source.path).read_bytes() == sources.responses[url].content


@pytest.mark.parametrize("broken_zip", [False, True])
def test_non_docx_zip_cannot_be_accepted_as_rule_document(
    pilot_root: Path, broken_zip: bool,
) -> None:
    """A ZIP signature or DOCX MIME label alone cannot establish document format."""

    sources = FakeSources()
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr("unrelated.txt", "Synthetic non-Word package")
    content = b"PK\x03\x04broken zip fixture" if broken_zip else output.getvalue()
    url = sources.document_urls[0]
    sources.responses[url] = daily.FetchResult(url, content, DOCX_MIME)
    before = _files(pilot_root)

    report = daily.refresh_register(pilot_root, SINCE, fetch=sources, now=NOW)

    assert report.status == "failed"
    assert report.notices_added == report.notices_updated == 0
    assert _files(pilot_root) == before


def test_passive_cloudflare_token_changes_do_not_hide_real_issue_changes(
    pilot_root: Path,
) -> None:
    """Ignore only observed passive security tokens while preserving complete source bytes."""

    sources = FakeSources()
    script = (FIXTURES / "official_passive_cf_script.html").read_bytes()
    original_issue = sources.responses[ISSUE].content.replace(b"</body>", script + b"</body>")
    sources.set_html(ISSUE, original_issue)
    _bootstrap(pilot_root, sources)
    state = daily.RefreshState.model_validate_json((pilot_root / daily.STATE).read_bytes())
    original_archive = state.sources[ISSUE].path
    assert (pilot_root / original_archive).read_bytes() == original_issue
    before = _files(pilot_root)
    rotated = re.sub(rb"r:'[^']+'", b"r:'0123456789abcdef'", original_issue)
    rotated = re.sub(rb"t:'[^']+'", b"t:'MDEyMzQ1Njc4OQ=='", rotated)
    assert rotated != original_issue
    sources.set_html(ISSUE, rotated)

    unchanged = daily.refresh_register(
        pilot_root, SINCE, fetch=sources, now=NOW + timedelta(days=1),
    )

    assert unchanged.status == "no_change", unchanged.errors
    assert _files(pilot_root) == before
    changed_issue = rotated.replace(b"09/14/2026", b"09/15/2026")
    changed_issue = re.sub(rb"r:'[^']+'", b"r:'fedcba9876543210'", changed_issue)
    sources.set_html(ISSUE, changed_issue)

    changed = daily.refresh_register(
        pilot_root, SINCE, fetch=sources, now=NOW + timedelta(days=2),
    )

    assert changed.status == "updated", changed.errors
    assert changed.notices_updated > 0
    assert (pilot_root / original_archive).read_bytes() == original_issue
    next_state = daily.RefreshState.model_validate_json((pilot_root / daily.STATE).read_bytes())
    assert next_state.sources[ISSUE].path != original_archive
    assert (pilot_root / next_state.sources[ISSUE].path).read_bytes() == changed_issue
    adopted = next(
        row for row in iter_jsonl(pilot_root / daily.META) if row["notice_type"] == "adopted"
    )
    assert adopted["effective_date"] == "2026-09-15"


@pytest.mark.parametrize("outcome", ["updated", "no_change", "failed"])
def test_cli_reports_outcome_exit_status_and_releases_client(
    pilot_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, outcome: str,
) -> None:
    """Schedulers receive a nonzero exit on failure and a report for every outcome."""

    sources = FakeSources()
    if outcome == "no_change":
        _bootstrap(pilot_root, sources)
    elif outcome == "failed":
        sources.fail_url = INDEX_URL
    monkeypatch.setattr(daily, "OfficialSourceClient", lambda delay: sources)
    report_dir = tmp_path / "cli-report"
    monkeypatch.setattr(sys, "argv", [
        "register_daily", "--root", str(pilot_root), "--since", SINCE.isoformat(),
        "--report-dir", str(report_dir), "--delay", "0",
    ])

    result = daily.main()

    assert result == (1 if outcome == "failed" else 0)
    report = daily.RefreshReport.model_validate_json((report_dir / "report.json").read_bytes())
    assert report.status == outcome
    assert sources.closed is True
    assert json.loads((report_dir / "changes.json").read_bytes()) == report.changed_paths


def test_cli_rejects_negative_delay_before_creating_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Invalid scheduler options fail without starting downloads."""

    monkeypatch.setattr(sys, "argv", ["register_daily", "--delay", "-1"])
    with pytest.raises(SystemExit) as error:
        daily.main()
    assert error.value.code == 2


def _bootstrap(root: Path, sources: FakeSources) -> None:
    """Run and require the first successful collection for follow-up scenarios."""

    report = daily.refresh_register(root, SINCE, fetch=sources, now=NOW)
    assert report.status == "updated", report.errors


def _write(root: Path, relative: str, content: bytes) -> None:
    """Write a validated fixture payload to its isolated repository."""

    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)


def _files(root: Path) -> dict[str, bytes]:
    """Capture all fixture file bytes for no-change and immutability assertions."""

    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in root.rglob("*") if path.is_file()
    }


def _canonical_files(root: Path) -> dict[str, bytes]:
    """Exclude immutable evidence left behind by a failed derived-file commit."""

    return {
        name: body for name, body in _files(root).items()
        if not name.startswith(("_RAW_ARCHIVE/", "_SNAPSHOTS/"))
    }


def _listing(issues: list[str]) -> bytes:
    """Construct a synthetic official-format listing around the real issue URL."""

    links = "".join(f'<a href="{url}">HTML</a>' for url in issues)
    return f"<html><body><h1>Colorado Register</h1>{links}</body></html>".encode()


def _docx(text: str) -> bytes:
    """Build a tiny deterministic synthetic Word document for source archiving."""

    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr(zipfile.ZipInfo("[Content_Types].xml"), "<Types/>")
        archive.writestr(zipfile.ZipInfo("word/document.xml"), f"<document>{text}</document>")
    return output.getvalue()
