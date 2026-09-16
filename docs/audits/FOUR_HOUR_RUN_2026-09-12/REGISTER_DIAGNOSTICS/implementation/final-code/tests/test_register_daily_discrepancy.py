"""Exact source-disappearance evidence and non-destructive Register failure reporting."""

from __future__ import annotations

import hashlib
import html
import json
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import jsonschema
import pytest
from pydantic import ValidationError

from geode.pipeline import register_daily as daily
from geode.utils.file_io import iter_jsonl
from tests.test_register_daily import (
    HEARING,
    INDEX_URL,
    ISSUE,
    NOW,
    SINCE,
    FakeSources,
    _bootstrap,
    _files,
    _listing,
    _write,
    pilot_root,
)

FIXTURES = Path(__file__).parent / "fixtures/register_daily_discrepancy"
REAL_URL = (
    "https://www.sos.state.co.us/CCR/RegisterContents.do?publicationDay=08/10/2026"
    "&Volume=49&yearPublishNumber=15&Month=8&Year=2026"
)
MISSING = ["RM-2026-daily-6ae185cdffa4fdedd5bb", "RM-2026-daily-fe6fe04b708089735009"]


def real_provenance() -> dict[str, dict[str, Any]]:
    """Validate the selected real source rows, streaming the frozen JSONL fixture."""

    result = {}
    with (FIXTURES / "selected_provenance.jsonl").open("rb") as handle:
        for line in handle:
            row = daily.NoticeProvenance.model_validate_json(line)
            result[row.notice_id] = row.model_dump(mode="json")
    return result


def real_rows(name: str) -> list[daily.DailyNoticeRow]:
    """Parse the exact original issue bytes without resolving links over a network."""

    return daily.parse_register_issue(
        daily.decode_register_html((FIXTURES / name).read_bytes(), "text/html;charset=ISO-8859-1"),
        date(2026, 8, 10), REAL_URL,
    )


def real_state() -> daily.IssueState:
    """Build the declared50-ID baseline from the validated custody selection."""

    return daily.IssueState(
        publication_date=date(2026, 8, 10),
        source_sha256=hashlib.sha256((FIXTURES / "archived.html").read_bytes()).hexdigest(),
        notice_ids=sorted(real_provenance()),
    )


def real_records() -> dict[str, dict[str, Any]]:
    """Represent each selected row's previously indexed canonical notice identity."""

    result = {}
    for identity, payload in real_provenance().items():
        provenance = daily.NoticeProvenance.model_validate(payload)
        notice = daily._notice(provenance.row, provenance.sources[0])
        result[identity] = notice.model_copy(update={"id": identity}).model_dump(mode="json")
    return result


def remove_proposal(sources: FakeSources) -> None:
    """Remove the single proposed row while retaining its recognized table header."""

    body = sources.responses[ISSUE].content
    marker = body.index(b"ProposedRuleAttach2026-00370")
    start, end = body.rfind(b"<tr>", 0, marker), body.index(b"</tr>", marker) + 5
    sources.set_html(ISSUE, body[:start] + body[end:])


def failed_report(root: Path) -> tuple[daily.RefreshReport, FakeSources]:
    """Collect only deterministic fixture responses for an unambiguous missing source row."""

    sources = FakeSources()
    _bootstrap(root, sources)
    remove_proposal(sources)
    sources.calls.clear()
    report = daily.refresh_register(root, SINCE, fetch=sources, now=NOW + timedelta(days=1))
    assert report.status == "failed" and report.issue_diagnostics
    return report, sources


def test_real_fixture_selection_and_complete_comparison() -> None:
    """Both complete originals and the50-row selection retain exact custody hashes."""

    selection = json.loads((FIXTURES / "selection.json").read_bytes())
    schema = json.loads((FIXTURES / "selection.schema.json").read_bytes())
    jsonschema.validate(selection, schema)
    for name, digest in selection["fixture_hashes"].items():
        assert hashlib.sha256((FIXTURES / name).read_bytes()).hexdigest() == digest
    assert hashlib.sha256((FIXTURES / "selected_provenance.jsonl").read_bytes()).hexdigest() == (
        selection["output_sha256"]
    )
    assert selection["record_count"] == 50
    assert selection["selected_notice_ids"] == sorted(real_provenance())
    assert len(real_rows("archived.html")) == 50 and len(real_rows("fresh.html")) == 48
    assert daily._early_missing_rows(
        REAL_URL, real_state(), real_rows("fresh.html"), real_provenance(), real_records(),
    ) == MISSING
    assert daily._early_missing_rows(
        REAL_URL, real_state(), real_rows("archived.html"), real_provenance(), real_records(),
    ) == []


def test_real50_to48_fails_after_contents_before_any_linked_fetch(pilot_root: Path) -> None:
    """The actual incident reports both missing IDs after two fixture calls, retaining all data."""

    provenance = real_provenance()
    primary = daily.SourceArtifact.model_validate(next(iter(provenance.values()))["sources"][0])
    source_bytes = (FIXTURES / "archived.html").read_bytes()
    notices = [daily._notice(daily.NoticeProvenance.model_validate(row).row, primary).model_copy(
        update={"id": identity},
    ) for identity, row in provenance.items()]
    previous = [
        daily.RulemakingNotice.model_validate(row) for row in iter_jsonl(pilot_root / daily.META)
    ]
    indexes = [
        daily.LayerIndexRecord.model_validate(row) for row in iter_jsonl(pilot_root / daily.INDEX)
    ]
    for name in (daily.META, daily.DATASET):
        _write(pilot_root, name, daily._rows_bytes([*previous, *notices]))
    _write(pilot_root, "04_Rulemaking/2026/register_2026_Q3.jsonl", daily._rows_bytes(notices))
    _write(pilot_root, daily.INDEX, daily._rows_bytes([
        *indexes, *[daily._index_row(row, NOW) for row in notices],
    ]))
    _write(pilot_root, daily.PROVENANCE, (FIXTURES / "selected_provenance.jsonl").read_bytes())
    _write(pilot_root, primary.path, source_bytes)
    state = daily.RefreshState(
        since=SINCE, issues={REAL_URL: real_state()}, sources={REAL_URL: primary},
    )
    _write(pilot_root, daily.STATE, daily._json_bytes(state))
    before = _files(pilot_root)
    calls = []

    def fetch(url: str) -> daily.FetchResult:
        """Any attachment or detail request would fail this regression."""

        calls.append(url)
        assert url in {INDEX_URL, REAL_URL}
        body = _listing([REAL_URL]) if url == INDEX_URL else (FIXTURES / "fresh.html").read_bytes()
        return daily.FetchResult(url, body, "text/html;charset=ISO-8859-1")

    report = daily.refresh_register(pilot_root, SINCE, fetch=fetch, now=NOW)
    assert calls == [INDEX_URL, REAL_URL]
    assert report.status == "failed" and report.validation_passed is False
    assert report.notices_added == report.notices_updated == 0 and report.changed_paths == []
    diagnostic = report.issue_diagnostics[0]
    assert diagnostic.stage == "source_row_preflight"
    assert [row.notice_id for row in diagnostic.missing_notices] == MISSING
    assert [row.docket for row in diagnostic.missing_notices] == ["2026-00337", "2026-00328"]
    assert (diagnostic.old_row_count, diagnostic.fresh_row_count) == (50, 48)
    assert diagnostic.original.sha256 == (
        "8f346e73c4d3af81e7c643d5129966c4420f60c42523d51d6db317dd40eac3a1"
    )
    assert _files(pilot_root) == before


@pytest.mark.parametrize("ambiguity", [
    "no_state", "empty_state", "duplicate_state", "missing_provenance", "wrong_notice_id",
    "wrong_source", "wrong_date", "missing_docket", "old_duplicate_docket", "fresh_duplicate",
    "fresh_missing_docket", "extra_provenance",
])
def test_ambiguous_preflight_defers_to_final_identity_gate(ambiguity: str) -> None:
    """Incomplete or non-unique source identities cannot justify a fast-path conclusion."""

    state = real_state()
    rows = real_rows("fresh.html")
    provenance = real_provenance()
    key = next(iter(provenance))
    if ambiguity == "no_state":
        state = None
    elif ambiguity == "empty_state":
        state.notice_ids = []
    elif ambiguity == "duplicate_state":
        state.notice_ids.append(state.notice_ids[0])
    elif ambiguity == "missing_provenance":
        del provenance[key]
    elif ambiguity == "extra_provenance":
        provenance["extra"] = provenance[key]
    elif ambiguity == "wrong_notice_id":
        provenance[key]["notice_id"] = "wrong-id"
    elif ambiguity == "wrong_source":
        provenance[key]["row"]["source_url"] = ISSUE
    elif ambiguity == "wrong_date":
        provenance[key]["row"]["publication_date"] = "2026-08-11"
    elif ambiguity == "missing_docket":
        provenance[key]["row"]["edocket_tracking_number"] = None
    elif ambiguity == "old_duplicate_docket":
        second = list(provenance)[1]
        provenance[second]["row"]["notice_type"] = provenance[key]["row"]["notice_type"]
        provenance[second]["row"]["edocket_tracking_number"] = (
            provenance[key]["row"]["edocket_tracking_number"]
        )
    elif ambiguity == "fresh_duplicate":
        rows.append(rows[0])
    else:
        rows[0] = rows[0].model_copy(update={"edocket_tracking_number": None})
    assert daily._early_missing_rows(REAL_URL, state, rows, provenance, real_records()) == []


def test_row_movement_is_not_absence() -> None:
    """Source ordering alone cannot trigger the early removal gate."""

    rows = list(reversed(real_rows("archived.html")))
    for index, row in enumerate(rows, 1):
        rows[index - 1] = row.model_copy(update={"row_number": index})
    assert daily._early_missing_rows(
        REAL_URL, real_state(), rows, real_provenance(), real_records(),
    ) == []


def test_changed_citation_still_reaches_final_identity_gate(pilot_root: Path) -> None:
    """A stable docket with a new CCR citation is never excused by the early check."""

    sources = FakeSources()
    _bootstrap(pilot_root, sources)
    before = _files(pilot_root)
    changed = sources.responses[ISSUE].content.replace(b"1 CCR 204-30", b"1 CCR 204-31")
    sources.set_html(ISSUE, changed)
    report = daily.refresh_register(pilot_root, SINCE, fetch=sources, now=NOW)
    assert report.status == "failed"
    assert report.issue_diagnostics[0].stage == "final_identity"
    assert len(report.issue_diagnostics[0].missing_notices) == 1
    assert report.issue_diagnostics[0].missing_notices[0].ccr_citation == "1 CCR 204-30"
    assert _files(pilot_root) == before


@pytest.mark.parametrize("damage", ["malformed", "duplicate", "encoding"])
def test_issue_failures_preserve_actual_source_bytes(pilot_root: Path, damage: str) -> None:
    """Malformed/duplicate/undecodable sources stay failed with inspectable original evidence."""

    sources = FakeSources()
    _bootstrap(pilot_root, sources)
    before = _files(pilot_root)
    body = sources.responses[ISSUE].content
    if damage == "malformed":
        body = body.replace(b"<b>Proposed rules</b>", b"<b>Unexpected heading</b>")
    elif damage == "duplicate":
        marker = body.index(b"ProposedRuleAttach2026-00370")
        start, end = body.rfind(b"<tr>", 0, marker), body.index(b"</tr>", marker) + 5
        body = body[:end] + body[start:end] + body[end:]
    else:
        body += b"\xff"
    sources.responses[ISSUE] = daily.FetchResult(ISSUE, body, "text/html;charset=utf-8")
    report = daily.refresh_register(pilot_root, SINCE, fetch=sources, now=NOW)
    assert report.status == "failed" and _files(pilot_root) == before
    diagnostic = report.issue_diagnostics[0]
    assert report._diagnostic_payloads[diagnostic.original.path] == body
    assert diagnostic.stage == ("row_processing" if damage == "duplicate" else "parse_error")
    assert diagnostic.view_method == (
        "hex_source_in_passive_pre" if damage == "encoding" else "escaped_source_in_passive_pre"
    )


def test_restored_rows_remain_no_change_without_any_status_migration(pilot_root: Path) -> None:
    """A later source restoration naturally passes against the untouched original state."""

    report, sources = failed_report(pilot_root)
    before = _files(pilot_root)
    sources.set_html(ISSUE, FakeSources().responses[ISSUE].content)
    restored = daily.refresh_register(pilot_root, SINCE, fetch=sources, now=NOW)
    assert restored.status == "no_change" and restored.issue_diagnostics == []
    assert report.issue_diagnostics[0].disposition == "review_required_no_notice_status_change"
    assert _files(pilot_root) == before


def test_report_preserves_exact_state_code_prepared_json_and_passive_view(
    pilot_root: Path, tmp_path: Path,
) -> None:
    """Failure artifacts bind the actual input baseline, without exposing active source HTML."""

    sources = FakeSources()
    _bootstrap(pilot_root, sources)
    remove_proposal(sources)
    prepared = tmp_path / "baseline.json"
    prepared.write_bytes(b'{"main":"' + b"a" * 40 + b'","pending":null}\n')
    state_bytes = (pilot_root / daily.STATE).read_bytes()
    report = daily.refresh_register(
        pilot_root, SINCE, fetch=sources, now=NOW, prepared_baseline=prepared,
    )
    output = tmp_path / "report"
    daily.write_run_report(report, output)
    saved = daily.RefreshReport.model_validate_json((output / "report.json").read_bytes())
    assert saved.baseline is not None and saved.baseline.state is not None
    assert saved.baseline.prepared.main == "a" * 40 and saved.baseline.prepared.pending is None
    assert (output / saved.baseline.prepared_artifact.path).read_bytes() == prepared.read_bytes()
    assert (output / saved.baseline.state.path).read_bytes() == state_bytes
    for name, artifact in saved.baseline.implementation.items():
        module_bytes = Path(sys.modules[name].__file__).read_bytes()
        assert (output / artifact.path).read_bytes() == module_bytes
    diagnostic = saved.issue_diagnostics[0]
    assert (output / diagnostic.original.path).read_bytes() == sources.responses[ISSUE].content
    passive = (output / diagnostic.passive_view.path).read_text()
    assert "<script" not in passive and "<iframe" not in passive
    assert "&lt;script" in passive
    assert html.unescape(passive.split("<pre>")[1].split("</pre>")[0]) == (
        daily.decode_register_html(sources.responses[ISSUE].content, "text/html")
    )
    assert "review_required_no_notice_status_change" in (output / "report.json").read_text()
    assert "Missing identities" in (output / "summary.md").read_text()


@pytest.mark.parametrize("bad_baseline", [
    b'{}', b'{"main":"invalid","pending":null}',
    b'{"main":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","authorization":"secret"}',
    b'{"main":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","pending":"bad"}',
])
def test_prepared_baseline_rejects_unknown_or_invalid_fields_before_fetch(
    pilot_root: Path, tmp_path: Path, bad_baseline: bytes,
) -> None:
    """Arbitrary workflow fields cannot become published baseline evidence or error text."""

    path = tmp_path / "bad.json"
    path.write_bytes(bad_baseline)
    sources = FakeSources()
    report = daily.refresh_register(
        pilot_root, SINCE, fetch=sources, now=NOW, prepared_baseline=path,
    )
    assert report.status == "failed" and sources.calls == []
    assert bad_baseline not in report._diagnostic_payloads.values()
    assert "secret" not in " ".join(report.errors)


@pytest.mark.parametrize("location", ["directory", "ancestor", "evidence", "report", "prepared"])
def test_symlink_evidence_paths_never_read_or_overwrite_outside(
    pilot_root: Path, tmp_path: Path, location: str,
) -> None:
    """Both report output and optional prepared inputs reject symlink ancestry."""

    report, _sources = failed_report(pilot_root)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "sentinel").write_bytes(b"untouched")
    output = tmp_path / "report"
    if location == "directory":
        output.symlink_to(outside, target_is_directory=True)
    elif location == "ancestor":
        output.symlink_to(outside, target_is_directory=True)
        output = output / "nested"
    elif location == "prepared":
        target = outside / "baseline.json"
        target.write_bytes(b'{"main":"' + b"a" * 40 + b'","pending":null}\n')
        link = tmp_path / "input-link"
        link.symlink_to(outside, target_is_directory=True)
        sources = FakeSources()
        failed = daily.refresh_register(
            pilot_root, SINCE, fetch=sources, now=NOW, prepared_baseline=link / "baseline.json",
        )
        assert failed.status == "failed" and sources.calls == []
        return
    else:
        output.mkdir()
        (output / ("evidence" if location == "evidence" else "report.json")).symlink_to(outside)
    before = _files(outside)
    with pytest.raises(ValueError, match="symlink"):
        daily.write_run_report(report, output)
    assert _files(outside) == before


def test_changed_report_snapshots_then_replays_without_mutation(
    pilot_root: Path, tmp_path: Path,
) -> None:
    """Report history is preserved, and repeated evidence writes are deterministic."""

    report, _sources = failed_report(pilot_root)
    output = tmp_path / "report"
    output.mkdir()
    (output / "report.json").write_bytes(b'{"old":"report"}\n')
    old = (output / "report.json").read_bytes()
    daily.write_run_report(report, output)
    saved = output / f"{daily.SNAPSHOT_PREFIX}{hashlib.sha256(old).hexdigest()}.json"
    assert saved.read_bytes() == old
    before = _files(output)
    daily.write_run_report(report, output)
    assert _files(output) == before


@pytest.mark.parametrize("corruption", ["memory", "missing", "disk", "snapshot"])
def test_report_tampering_fails_before_any_output_change(
    pilot_root: Path, tmp_path: Path, corruption: str,
) -> None:
    """Evidence integrity failures cannot leave a misleading newly written report."""

    report, _sources = failed_report(pilot_root)
    output = tmp_path / "report"
    artifact = report.issue_diagnostics[0].original
    if corruption == "memory":
        report._diagnostic_payloads[artifact.path] = b"altered"
    elif corruption == "missing":
        report._diagnostic_payloads.pop(artifact.path)
    elif corruption == "disk":
        target = output / artifact.path
        target.parent.mkdir(parents=True)
        target.write_bytes(b"altered existing evidence")
    else:
        output.mkdir()
        (output / "report.json").write_bytes(b"old")
        target = output / f"{daily.SNAPSHOT_PREFIX}{hashlib.sha256(b'old').hexdigest()}.json"
        target.parent.mkdir(parents=True)
        target.write_bytes(b"corrupt")
    before = _files(output) if output.exists() else {}
    with pytest.raises(ValueError):
        daily.write_run_report(report, output)
    assert (_files(output) if output.exists() else {}) == before


def test_failed_report_write_rolls_back_mutable_report_and_keeps_corpus(
    pilot_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An interrupted report publication cannot produce a successful candidate."""

    report, _sources = failed_report(pilot_root)
    original_corpus = _files(pilot_root)
    output = tmp_path / "report"
    output.mkdir()
    (output / "report.json").write_bytes(b"old report")
    replace = daily.os.replace
    stopped = False

    def fail_once(source: str, destination: Path) -> None:
        """Fail on the final summary write, allowing rollback replacements to succeed."""

        nonlocal stopped
        if Path(destination).name == "summary.md" and not stopped:
            stopped = True
            raise OSError("Simulated report disk failure")
        replace(source, destination)

    monkeypatch.setattr(daily.os, "replace", fail_once)
    with pytest.raises(OSError, match="report disk failure"):
        daily.write_run_report(report, output)
    assert stopped and report.status == "failed"
    assert (output / "report.json").read_bytes() == b"old report"
    assert not (output / "changes.json").exists()
    assert _files(pilot_root) == original_corpus


@pytest.mark.parametrize("field,value", [
    ("status", "no_change"), ("validation_passed", True), ("changed_paths", [daily.STATE]),
    ("notices_added", 1), ("notices_updated", 1),
])
def test_discrepancy_can_never_be_serialized_as_success(
    pilot_root: Path, tmp_path: Path, field: str, value: Any,
) -> None:
    """Strict output validation prevents failed evidence from being used as clean status."""

    report, _sources = failed_report(pilot_root)
    setattr(report, field, value)
    with pytest.raises(ValidationError, match="failed, unchanged"):
        daily.write_run_report(report, tmp_path / "report")


def test_cli_includes_optional_prepared_baseline_in_failure_artifacts(
    pilot_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The scheduled invocation retains branch identities even when collection stops early."""

    sources = FakeSources()
    sources.fail_url = INDEX_URL
    path = tmp_path / "prepared.json"
    path.write_text(json.dumps({"main": "a" * 40, "pending": "b" * 40}))
    output = tmp_path / "reports"
    monkeypatch.setattr(daily, "OfficialSourceClient", lambda delay: sources)
    monkeypatch.setattr(sys, "argv", [
        "register_daily", "--root", str(pilot_root), "--report-dir", str(output),
        "--prepared-baseline", str(path),
    ])
    assert daily.main() == 1
    report = daily.RefreshReport.model_validate_json((output / "report.json").read_bytes())
    assert report.baseline.prepared.pending == "b" * 40
    assert (output / report.baseline.prepared_artifact.path).read_bytes() == path.read_bytes()
    assert sources.closed


@pytest.mark.parametrize("tamper", ["source_hash", "duplicate_missing", "row_count"])
def test_issue_diagnostic_schema_binds_original_counts_and_identity(
    pilot_root: Path, tamper: str,
) -> None:
    """Durable discrepancy objects reject contradictory byte and row identities."""

    report, _sources = failed_report(pilot_root)
    value = report.issue_diagnostics[0].model_dump(mode="json")
    if tamper == "source_hash":
        value["fresh_source_sha256"] = "a" * 64
    elif tamper == "duplicate_missing":
        value["missing_notices"].append(value["missing_notices"][0])
    else:
        value["fresh_row_count"] += 1
    with pytest.raises(ValidationError):
        daily.IssueDiagnostic.model_validate(value)


def test_artifact_and_baseline_require_complete_binding() -> None:
    """Declared digest filenames and prepared identities cannot be independently substituted."""

    with pytest.raises(ValidationError, match="filename"):
        daily.DiagnosticArtifact(path=f"evidence/{'a' * 64}.json", sha256="b" * 64, bytes=10)
    with pytest.raises(ValidationError, match="paired"):
        daily.RunBaseline(
            captured_at=NOW, implementation={}, prepared=daily.PreparedBaseline(main="a" * 40),
        )


def test_diagnostic_total_budget_is_bounded_and_duplicate_bytes_are_reused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Repeated identical input does not grow evidence, while an additional payload is bounded."""

    report = daily.RefreshReport(checked_at=NOW, since=SINCE)
    monkeypatch.setattr(daily, "MAX_DIAGNOSTIC_BYTES", 3)
    artifact = daily._diagnostic_artifact(report, b"abc", "json")
    assert daily._diagnostic_artifact(report, b"abc", "json") == artifact
    with pytest.raises(ValueError, match="limit"):
        daily._diagnostic_artifact(report, b"d", "json")
    assert len(report._diagnostic_payloads) == 1


@pytest.mark.parametrize("body", [b"", b"too many bytes"])
def test_baseline_read_has_an_independent_size_bound(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, body: bytes,
) -> None:
    """Baseline inputs cannot cause unbounded reads or be silently treated as absent."""

    path = tmp_path / "input"
    path.write_bytes(body)
    monkeypatch.setattr(daily, "MAX_BASELINE_BYTES", 3)
    with pytest.raises(ValueError, match="Empty or oversized"):
        daily._bounded_diagnostic_input(path)


def test_traversal_is_rejected_before_report_creation(tmp_path: Path) -> None:
    """A traversal spelling cannot redirect diagnostic output through another directory."""

    report = daily.RefreshReport(checked_at=NOW, since=SINCE)
    with pytest.raises(ValueError, match="traversal"):
        daily.write_run_report(report, tmp_path / "unused" / ".." / "report")
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("race", ["appeared", "disappeared", "changed"])
def test_input_state_race_fails_before_any_source_request(
    pilot_root: Path, monkeypatch: pytest.MonkeyPatch, race: str,
) -> None:
    """The state used by collection must equal the exact before-run evidence capture."""

    sources = FakeSources()
    if race != "appeared":
        _bootstrap(pilot_root, sources)
    capture = daily._capture_baseline

    def changed_state(root: Path, report: daily.RefreshReport, prepared: Path | None) -> None:
        """Simulate an external state change immediately after baseline capture."""

        capture(root, report, prepared)
        target = root / daily.STATE
        if race == "appeared":
            _write(root, daily.STATE, daily._json_bytes(daily.RefreshState(since=SINCE)))
        elif race == "disappeared":
            target.unlink()
        else:
            target.write_bytes(target.read_bytes() + b"\n")

    monkeypatch.setattr(daily, "_capture_baseline", changed_state)
    sources.calls.clear()
    report = daily.refresh_register(pilot_root, SINCE, fetch=sources, now=NOW)
    assert report.status == "failed" and sources.calls == []
    assert "changed after run baseline" in report.errors[0]


def test_invalid_state_is_not_copied_or_echoed_as_diagnostic_evidence(pilot_root: Path) -> None:
    """Unexpected input fields cannot leak into the report through validation-error rendering."""

    secret = b'{"authorization":"private-value"}'
    _write(pilot_root, daily.STATE, secret)
    sources = FakeSources()
    report = daily.refresh_register(pilot_root, SINCE, fetch=sources, now=NOW)
    assert report.status == "failed" and sources.calls == []
    assert secret not in report._diagnostic_payloads.values()
    assert "private-value" not in " ".join(report.errors)


def test_failure_evidence_preparation_error_cannot_change_failed_outcome(
    pilot_root: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The collector remains failed even if its diagnostic evidence cannot be assembled."""

    sources = FakeSources()
    _bootstrap(pilot_root, sources)
    remove_proposal(sources)
    before = _files(pilot_root)

    def fail_evidence(*args: Any, **kwargs: Any) -> None:
        """Simulate an in-memory evidence-preservation failure."""

        raise OSError("simulated evidence failure")

    monkeypatch.setattr(daily, "_retain_issue_diagnostic", fail_evidence)
    report = daily.refresh_register(pilot_root, SINCE, fetch=sources, now=NOW)
    assert report.status == "failed" and not report.validation_passed
    assert any("Failure evidence could not be prepared" in error for error in report.errors)
    assert _files(pilot_root) == before


def test_missing_historical_provenance_keeps_unknown_fields_explicit() -> None:
    """The final gate can report a missing ID without inventing lost docket metadata."""

    report = daily.RefreshReport(checked_at=NOW, since=SINCE)
    response = daily.FetchResult(REAL_URL, (FIXTURES / "fresh.html").read_bytes(), "text/html")
    daily._retain_issue_diagnostic(
        report, REAL_URL, real_state(), response, real_rows("fresh.html"),
        ["RM-2026-unknown"], {}, "final_identity",
    )
    missing = report.issue_diagnostics[0].missing_notices[0]
    assert missing.docket is None and missing.ccr_citation is None


@pytest.mark.parametrize("mismatch", ["missing_record", "changed_citation"])
def test_preflight_requires_provenance_to_match_indexed_identity(mismatch: str) -> None:
    """A provenance docket alone cannot attach a disappearance to contradictory metadata."""

    records = real_records()
    key = next(iter(records))
    if mismatch == "missing_record":
        del records[key]
    else:
        records[key]["ccr_rule_affected"] = "1_CCR_999-1"
    assert daily._early_missing_rows(
        REAL_URL, real_state(), real_rows("fresh.html"), real_provenance(), records,
    ) == []


def test_duplicate_prior_provenance_fails_without_silently_dropping_rows(pilot_root: Path) -> None:
    """An old duplicate notice key cannot be silently overwritten before preflight matching."""

    sources = FakeSources()
    _bootstrap(pilot_root, sources)
    target = pilot_root / daily.PROVENANCE
    with target.open("rb") as handle:
        duplicate = next(handle)
    target.write_bytes(target.read_bytes() + duplicate)
    before = _files(pilot_root)
    sources.calls.clear()
    report = daily.refresh_register(pilot_root, SINCE, fetch=sources, now=NOW)
    assert report.status == "failed" and sources.calls == []
    assert "Duplicate prior notice provenance" in report.errors[0]
    assert _files(pilot_root) == before
