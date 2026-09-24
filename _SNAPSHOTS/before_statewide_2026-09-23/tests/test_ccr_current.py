"""Current-source verification with actual SOS pages and controlled failures."""

from __future__ import annotations

import hashlib
import io
import json
import re
import zipfile
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from geode.pipeline import ccr_current as ccr
from geode.pipeline.register_daily import FetchResult

FIXTURES = Path(__file__).parent / "fixtures" / "ccr_current"
CONTENT_TYPE = "text/html;charset=ISO-8859-1"
NOW = datetime(2026, 9, 9, 23, tzinfo=timezone.utc)
BASE = "https://www.sos.state.co.us/CCR/"
AGENCY_URL = (
    BASE + "NumericalCCRDocList.do?deptID=12&deptName=1300%20Department%20of%20Local%20Affairs"
    "&agencyID=10&agencyName=1301%20Board%20of%20Assessment%20Appeals"
)
RULE_URL = (
    BASE + "DisplayRule.do?action=ruleinfo&ruleId=2567&deptID=12&agencyID=10"
    "&deptName=Department%20of%20Local%20Affairs&agencyName=Board%20of%20Assessment%20Appeals"
    "&seriesNum=8%20CCR%201301-1"
)
PDF_URL = BASE + "GenerateRulePdf.do?ruleVersionId=8205&fileName=8%20CCR%201301-1"
WORD_URL = BASE + "GenerateRulePdf.do?type=word&ruleVersionId=8205&fileName=8%20CCR%201301-1"
INVENTORY = ccr.VERIFICATION_PREFIX + "department-12.jsonl"
STATE = ccr.VERIFICATION_PREFIX + "department-12-state.json"


def fixture(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


def document(name: str) -> ccr._Document:
    return ccr._parse_html(fixture(name), CONTENT_TYPE)


def html_result(url: str, value: str | bytes) -> FetchResult:
    return FetchResult(url, value.encode() if isinstance(value, str) else value, CONTENT_TYPE)


def word_bytes() -> bytes:
    result = io.BytesIO()
    with zipfile.ZipFile(result, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("word/document.xml", "<document/>")
    return result.getvalue()


@pytest.fixture
def world() -> dict[str, FetchResult]:
    catalog = (
        '<html><body><table><tr><td><a name="1300">1300</a></td>'
        '<td>Department of Local Affairs</td></tr><tr><td></td><td><a href="'
        + AGENCY_URL.replace("%20", " ") + '">'
        "Board of Assessment Appeals</a></td></tr></table></body></html>"
    )
    return {
        ccr.WELCOME_URL: html_result(ccr.WELCOME_URL, fixture("welcome.html")),
        ccr.CATALOG_URL: html_result(ccr.CATALOG_URL, catalog),
        AGENCY_URL: html_result(AGENCY_URL, fixture("agency-10.html")),
        RULE_URL: html_result(RULE_URL, fixture("rule-current.html")),
        PDF_URL: FetchResult(PDF_URL, b"%PDF-1.7\nSynthetic test document", "application/pdf"),
        WORD_URL: FetchResult(WORD_URL, word_bytes(), "application/octet-stream"),
    }


def run(root: Path, world: dict, **kwargs) -> ccr.CCRCurrentReport:
    return ccr.collect_ccr_current(root, "12", fetch=world.__getitem__, now=NOW, **kwargs)


def files(root: Path) -> dict[str, bytes]:
    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in root.rglob("*") if path.is_file()
    }


def mutate(world: dict, url: str, before: str, after: str) -> None:
    source = world[url]
    assert before.encode() in source.content
    world[url] = FetchResult(
        url, source.content.replace(before.encode(), after.encode()), source.content_type,
    )


def test_actual_department_catalog_preserves_all_agencies() -> None:
    agencies = ccr._agencies(document("catalog.html"), ccr.CATALOG_URL, "12")
    assert set(agencies) == {"10", "51", "93", "63", "103", "91", "184"}
    assert agencies["10"][0] == AGENCY_URL
    assert ccr._cutoff(document("welcome.html"), NOW.date()) == date(2026, 8, 13)


@pytest.mark.parametrize("name,status,effective,repeal", [
    ("rule-current.html", "source_current", date(2019, 8, 15), None),
    ("rule-repealed.html", "source_repealed", date(2018, 7, 1), "07/01/2018"),
    ("rule-undated.html", "ambiguous", None, None),
])
def test_real_source_status_overrides_current_table_label(name, status, effective, repeal) -> None:
    doc = document(name)
    versions = ccr._versions(doc, RULE_URL)
    classification, evidence, selected = ccr._classify(doc, versions, NOW.date())
    assert classification == status
    assert selected.effective_date == effective
    if repeal:
        assert repeal in evidence
    if name == "rule-current.html":
        assert len(versions) == 4
        assert selected.adopted_date == date(2019, 6, 17)
        assert selected.publication_date == date(2019, 7, 25)
        assert selected.edocket_urls == [BASE + "eDocketDetails.do?trackingNum=2019-00189"]
        assert selected.document_urls == [PDF_URL, WORD_URL]
        assert versions[-1].effective_date is None


def test_complete_collection_preserves_evidence_and_canonical_files(tmp_path, world) -> None:
    canonical = tmp_path / "02_Regulations_CCR" / "_index.jsonl"
    canonical.parent.mkdir()
    canonical.write_bytes(b"Inherited data must remain unchanged\n")
    report = run(tmp_path, world)
    assert report.status == "updated", report.errors
    assert report.validation_passed and report.full_department_discovery
    assert (report.agencies_checked, report.rules_checked, report.sources_checked) == (1, 1, 6)
    assert report.classification_counts == {"source_current": 1}
    assert canonical.read_bytes() == b"Inherited data must remain unchanged\n"
    record = ccr.CCRCurrentRecord.model_validate_json((tmp_path / INVENTORY).read_bytes())
    assert record.title.endswith("PROCEDURES OF PRACTICE AND PROCEDURES OF REVIEW")
    assert record.source_publication_cutoff == date(2026, 8, 13)
    assert len(record.sources) == 3
    state = ccr.CCRState.model_validate_json((tmp_path / STATE).read_bytes())
    for url, source in state.sources.items():
        body = (tmp_path / source.path).read_bytes()
        assert body == world[url].content
        assert hashlib.sha256(body).hexdigest() == source.sha256


def test_no_change_rechecks_all_urls_and_preserves_every_byte(tmp_path, world) -> None:
    assert run(tmp_path, world).status == "updated"
    before = files(tmp_path)
    checked = []

    def fetch(url):
        checked.append(url)
        return world[url]

    report = ccr.collect_ccr_current(
        tmp_path, "12", fetch=fetch, now=NOW.replace(day=10),
    )
    assert report.status == "no_change", report.errors
    assert report.changed_paths == []
    assert set(checked) == set(world)
    assert files(tmp_path) == before


def test_rotating_exact_passive_script_is_ignored_without_rewriting_raw(tmp_path, world) -> None:
    assert run(tmp_path, world).status == "updated"
    before = files(tmp_path)
    original = world[RULE_URL]
    body = re.sub(rb"r:'[a-f0-9]{16}'", b"r:'123456789abcdef0'", original.content)
    assert body != original.content
    world[RULE_URL] = FetchResult(RULE_URL, body, CONTENT_TYPE)
    assert run(tmp_path, world).status == "no_change"
    assert files(tmp_path) == before


def test_changed_legal_source_creates_immutable_snapshots(tmp_path, world) -> None:
    assert run(tmp_path, world).status == "updated"
    before = files(tmp_path)
    mutate(world, RULE_URL, "PROCEDURES OF REVIEW", "PROCEDURES OF REVIEW AMENDED")
    report = run(tmp_path, world)
    assert report.status == "updated", report.errors
    for name in (INVENTORY, STATE):
        digest = hashlib.sha256(before[name]).hexdigest()
        snapshot = tmp_path / f"{ccr.SNAPSHOT_PREFIX}{digest}{Path(name).suffix}"
        assert snapshot.read_bytes() == before[name]
    for name, body in before.items():
        if name.startswith(ccr.RAW_PREFIX):
            assert (tmp_path / name).read_bytes() == body


def test_future_effective_date_rollover_updates_only_interpretation(tmp_path, world) -> None:
    mutate(world, RULE_URL, "08/15/2019", "09/10/2026")
    first = run(tmp_path, world)
    assert first.classification_counts == {"future_effective": 1}
    raw_before = {
        key: value for key, value in files(tmp_path).items() if key.startswith(ccr.RAW_PREFIX)
    }
    report = ccr.collect_ccr_current(
        tmp_path, "12", fetch=world.__getitem__, now=NOW.replace(day=10),
    )
    assert report.status == "updated"
    assert report.classification_counts == {"source_current": 1}
    assert {
        key: value for key, value in files(tmp_path).items() if key.startswith(ccr.RAW_PREFIX)
    } == raw_before


def test_future_rule_uses_colorado_calendar_date(tmp_path, world) -> None:
    mutate(world, RULE_URL, "08/15/2019", "09/10/2026")
    before_midnight = datetime(2026, 9, 10, 1, tzinfo=timezone.utc)
    report = ccr.collect_ccr_current(tmp_path, "12", fetch=world.__getitem__, now=before_midnight)
    assert report.classification_counts == {"future_effective": 1}


def add_rule(world: dict, *, separate_agency: bool) -> tuple[str, str]:
    agency_id = "11" if separate_agency else "10"
    rule_url = RULE_URL.replace("ruleId=2567", "ruleId=9999").replace(
        "agencyID=10", f"agencyID={agency_id}",
    ).replace("1301-1", "1301-2")
    rule_body = fixture("rule-current.html").replace(b"1301-1", b"1301-2")
    world[rule_url] = html_result(rule_url, rule_body)
    for old_url in (PDF_URL, WORD_URL):
        new_url = old_url.replace("1301-1", "1301-2")
        old = world[old_url]
        world[new_url] = FetchResult(new_url, old.content, old.content_type)
    if separate_agency:
        agency_url = AGENCY_URL.replace("agencyID=10", "agencyID=11")
        agency_body = fixture("agency-10.html").replace(b"agencyID=10", b"agencyID=11").replace(
            b"ruleId=2567", b"ruleId=9999",
        ).replace(b"1301-1", b"1301-2")
        world[agency_url] = html_result(agency_url, agency_body)
        mutate(world, ccr.CATALOG_URL, "</table>", (
            f'<tr><td></td><td><a href="{agency_url}">Second agency</a></td></tr></table>'
        ))
    else:
        agency_url = AGENCY_URL
        row = f'<tr><td><a href="{rule_url}">8 CCR 1301-2</a></td><td>Second rule</td></tr>'
        mutate(world, AGENCY_URL, "</TBODY>", row + "</TBODY>")
    return agency_url, rule_url


@pytest.mark.parametrize("separate_agency,error", [
    (True, "agency disappeared"), (False, "rule disappeared"),
])
def test_disappearing_scope_member_blocks_update(tmp_path, world, separate_agency, error) -> None:
    original_catalog = world[ccr.CATALOG_URL]
    original_agency = world[AGENCY_URL]
    add_rule(world, separate_agency=separate_agency)
    first = run(tmp_path, world)
    assert first.status == "updated", first.errors
    assert first.rules_checked == 2
    before = files(tmp_path)
    if separate_agency:
        world[ccr.CATALOG_URL] = original_catalog
    else:
        world[AGENCY_URL] = original_agency
    report = run(tmp_path, world)
    assert error in " ".join(report.errors)
    assert files(tmp_path) == before


def test_regressing_publication_cutoff_blocks_update(tmp_path, world) -> None:
    assert run(tmp_path, world).status == "updated"
    mutate(world, ccr.WELCOME_URL, "08/13/2026", "07/13/2026")
    assert "moved backwards" in " ".join(run(tmp_path, world).errors)


def test_source_mime_change_is_preserved_and_not_hidden_as_no_change(tmp_path, world) -> None:
    assert run(tmp_path, world).status == "updated"
    old = world[RULE_URL]
    world[RULE_URL] = FetchResult(RULE_URL, old.content, "text/html;charset=windows-1252")
    assert run(tmp_path, world).status == "updated"
    state = json.loads((tmp_path / STATE).read_bytes())
    assert state["sources"][RULE_URL]["content_type"] == "text/html;charset=windows-1252"


def test_multiple_current_or_undated_repeal_remain_ambiguous() -> None:
    doc = document("rule-current.html")
    versions = ccr._versions(doc, RULE_URL)
    versions[1] = versions[1].model_copy(update={"designation": "current"})
    assert ccr._classify(doc, versions, NOW.date())[0] == "ambiguous"
    body = fixture("rule-repealed.html").replace(b"eff. 07/01/2018]", b"eff. unknown]")
    doc = ccr._parse_html(body, CONTENT_TYPE)
    assert ccr._classify(doc, ccr._versions(doc, RULE_URL), NOW.date())[0] == "ambiguous"


def test_future_repeal_is_not_already_repealed() -> None:
    body = fixture("rule-repealed.html").replace(b"eff. 07/01/2018]", b"eff. 09/10/2026]")
    doc = ccr._parse_html(body, CONTENT_TYPE)
    result = ccr._classify(doc, ccr._versions(doc, RULE_URL), NOW.date())
    assert result[0] == "future_effective"
    assert "09/10/2026" in result[1]


@pytest.mark.parametrize("change,error", [
    ({"department_id": "99"}, "different department"),
    ({"rule_ids": ["999"]}, "identities disagree"),
])
def test_prior_state_identity_mismatch_fails(tmp_path, world, change, error) -> None:
    assert run(tmp_path, world).status == "updated"
    state = json.loads((tmp_path / STATE).read_bytes())
    state.update(change)
    (tmp_path / STATE).write_text(json.dumps(state))
    assert error in " ".join(run(tmp_path, world).errors)


def test_partial_table_row_cannot_disappear_silently(tmp_path, world) -> None:
    add_rule(world, separate_agency=False)
    mutate(world, AGENCY_URL, "8 CCR 1301-2</a>", "unknown</a>")
    assert run(tmp_path, world).status == "failed"


def test_timezone_and_unsafe_paths_are_rejected(tmp_path, world) -> None:
    report = ccr.collect_ccr_current(
        tmp_path, "12", fetch=world.__getitem__, now=NOW.replace(tzinfo=None),
    )
    assert "timezone" in " ".join(report.errors)
    for path in ("/outside", "../outside"):
        with pytest.raises(ValueError, match="Unsafe evidence"):
            ccr._target(tmp_path, path)


def test_source_schema_requires_matching_hash_path(tmp_path, world) -> None:
    assert run(tmp_path, world).status == "updated"
    state = json.loads((tmp_path / STATE).read_bytes())
    source = state["sources"][PDF_URL]
    source["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="does not match"):
        ccr.CCRSource.model_validate(source)


@pytest.mark.parametrize("replacement", ["MovedEndpoint.do", "#missing"])
def test_changed_agency_endpoint_cannot_be_silently_skipped(replacement) -> None:
    original = fixture("catalog.html")
    target = (
        b"NumericalCCRDocList.do?deptID=12&deptName=1300 Department of Local Affairs&agencyID=51"
    )
    body = original.replace(target, target.replace(b"NumericalCCRDocList.do", replacement.encode()))
    assert body != original
    with pytest.raises(ValueError, match="unexpected endpoint"):
        ccr._agencies(ccr._parse_html(body, CONTENT_TYPE), ccr.CATALOG_URL, "12")


@pytest.mark.parametrize("key,replacement", [
    ("agencyID=10", "agencyID=11"), ("deptID=12", "deptID=13"),
])
def test_foreign_scope_rule_link_is_not_attributed_to_this_department(
    tmp_path, world, key, replacement,
) -> None:
    mutate(world, AGENCY_URL, key, replacement)
    report = run(tmp_path, world)
    assert "another department or agency" in " ".join(report.errors)
    assert not files(tmp_path)


@pytest.mark.parametrize("url,before,after,error", [
    (ccr.WELCOME_URL, "08/13/2026", "08/13/2027", "cutoff"),
    (ccr.WELCOME_URL, "effective on or before", "effective as of", "cutoff"),
    (ccr.CATALOG_URL, "deptID=12", "deptID=99", "no agencies"),
    (AGENCY_URL, "DisplayRule.do", "MissingRule.do", "no verifiable"),
    (AGENCY_URL, "ruleId=2567", "ruleId=invalid", "numeric"),
    (AGENCY_URL, "8 CCR 1301-1 </a>", "unknown </a>", "no CCR citation"),
    (AGENCY_URL, "PROCEDURES OF PRACTICE AND PROCEDURES OF REVIEW</TD>", "</TD>", "Incomplete"),
    (RULE_URL, "Current version</b>", "New version</b>", "Current version"),
    (RULE_URL, "Archived versions</b>", "Old versions</b>", "Archived versions"),
    (RULE_URL, "Filing Type</b>", "Changed header</b>", "headers"),
    (RULE_URL, "OpenRuleWindow('8205'", "UnsupportedDownload('8205'", "no source PDF"),
    (RULE_URL, "OpenRuleWordVersion('8205'", "OpenRuleWordVersion('8206'", "Mismatched"),
    (RULE_URL, "08/15/2019 (DOCX)", "08/16/2019 (DOCX)", "dates disagree"),
    (RULE_URL, "08/15/2019 (PDF)", "02/30/2019 (PDF)", "day"),
    (RULE_URL, "class=\"pagehead5\"", "class=\"missingTitle\"", "title"),
    (RULE_URL, "</html>", "", "terminator"),
])
def test_incomplete_or_ambiguous_source_fails_before_writes(
    tmp_path, world, url, before, after, error,
) -> None:
    mutate(world, url, before, after)
    report = run(tmp_path, world)
    assert report.status == "failed"
    assert not report.full_department_discovery
    assert error.casefold() in " ".join(report.errors).casefold(), report.errors
    assert not files(tmp_path)


@pytest.mark.parametrize("href", ["?page=2", "?offset=20", "?start=10", "?pageNum=2"])
def test_pagination_is_an_incomplete_scope_error(tmp_path, world, href) -> None:
    mutate(world, AGENCY_URL, "</body>", f'<a href="{href}">2</a></body>')
    assert "pagination" in " ".join(run(tmp_path, world).errors)


@pytest.mark.parametrize("replacement", [
    b"<html><body>Access denied</body></html>", b"", b"not a PDF", b"PK\x03\x04broken",
])
def test_invalid_document_response_does_not_promote(tmp_path, world, replacement) -> None:
    world[PDF_URL] = FetchResult(PDF_URL, replacement, "application/pdf")
    assert run(tmp_path, world).status == "failed"
    assert not files(tmp_path)


def test_redirected_wrong_version_and_external_url_are_rejected(tmp_path, world) -> None:
    world[PDF_URL] = FetchResult(
        PDF_URL.replace("8205", "9999"), b"%PDF-1.7\nwrong", "application/pdf",
    )
    assert "redirect changed" in " ".join(run(tmp_path, world).errors)
    world[PDF_URL] = FetchResult(
        "https://example.com/incorrect.pdf", b"%PDF-1.7\n", "application/pdf",
    )
    assert "Unapproved" in " ".join(run(tmp_path, world).errors)


@pytest.mark.parametrize("limits", [
    {"max_sources": 3}, {"max_total_bytes": 20}, {"max_sources": 0},
    {"max_sources": 301}, {"max_total_bytes": 150_000_001},
])
def test_resource_limits_are_failures_not_partial_success(tmp_path, world, limits) -> None:
    assert run(tmp_path, world, **limits).status == "failed"
    assert not files(tmp_path)


def test_network_failure_preserves_previous_inventory(tmp_path, world) -> None:
    assert run(tmp_path, world).status == "updated"
    before = files(tmp_path)
    del world[PDF_URL]
    report = run(tmp_path, world)
    assert report.status == "failed" and report.changed_paths == []
    assert files(tmp_path) == before


@pytest.mark.parametrize("name", [INVENTORY, STATE])
def test_partial_prior_state_is_rejected(tmp_path, world, name) -> None:
    assert run(tmp_path, world).status == "updated"
    (tmp_path / name).unlink()
    assert "both exist" in " ".join(run(tmp_path, world).errors)


def test_modified_inventory_and_missing_original_fail(tmp_path, world) -> None:
    assert run(tmp_path, world).status == "updated"
    original = (tmp_path / INVENTORY).read_bytes()
    (tmp_path / INVENTORY).write_bytes(original + b"\n")
    assert "hash mismatch" in " ".join(run(tmp_path, world).errors)
    (tmp_path / INVENTORY).write_bytes(original)
    state = json.loads((tmp_path / STATE).read_bytes())
    (tmp_path / state["sources"][PDF_URL]["path"]).unlink()
    assert "Missing or corrupt prior source" in " ".join(run(tmp_path, world).errors)


def test_preexisting_corrupt_content_address_is_not_overwritten(tmp_path, world) -> None:
    digest = hashlib.sha256(world[PDF_URL].content).hexdigest()
    target = tmp_path / f"{ccr.RAW_PREFIX}{digest}.pdf"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"corrupt")
    assert "Corrupt immutable" in " ".join(run(tmp_path, world).errors)
    assert target.read_bytes() == b"corrupt"


def test_symlink_output_is_rejected(tmp_path, world) -> None:
    target = tmp_path / "outside"
    target.mkdir()
    (tmp_path / "02_Regulations_CCR").symlink_to(target)
    assert "symlink" in " ".join(run(tmp_path, world).errors)
    assert not list(target.iterdir())


def test_derived_failure_rolls_back_and_keeps_original_evidence(
    tmp_path, world, monkeypatch,
) -> None:
    assert run(tmp_path, world).status == "updated"
    before = files(tmp_path)
    mutate(world, RULE_URL, "PROCEDURES OF REVIEW", "PROCEDURES OF REVIEW AMENDED")
    real_replace = ccr.os.replace
    attempts = 0

    def fail_second(src, dst):
        nonlocal attempts
        attempts += 1
        if attempts == 2:
            raise OSError("simulated disk failure")
        return real_replace(src, dst)

    monkeypatch.setattr(ccr.os, "replace", fail_second)
    report = run(tmp_path, world)
    assert report.status == "failed"
    assert (tmp_path / INVENTORY).read_bytes() == before[INVENTORY]
    assert (tmp_path / STATE).read_bytes() == before[STATE]
    for name, body in before.items():
        assert (tmp_path / name).read_bytes() == body
    assert not list((tmp_path / ccr.VERIFICATION_PREFIX).glob("tmp*"))


def test_first_run_failure_rolls_back_new_derived_file(tmp_path, world, monkeypatch) -> None:
    real_replace = ccr.os.replace
    attempts = 0

    def fail_second(src, dst):
        nonlocal attempts
        attempts += 1
        if attempts == 2:
            raise OSError("simulated disk failure")
        return real_replace(src, dst)

    monkeypatch.setattr(ccr.os, "replace", fail_second)
    assert run(tmp_path, world).status == "failed"
    assert not (tmp_path / INVENTORY).exists()
    assert not (tmp_path / STATE).exists()


def test_run_report_and_cli(tmp_path, world, monkeypatch) -> None:
    class Client:
        def __init__(self, delay):
            self.delay = delay

        def __call__(self, url):
            return world[url]

        def close(self):
            pass

    monkeypatch.setattr(ccr, "OfficialSourceClient", Client)
    reports = tmp_path / "reports"
    args = ["--root", str(tmp_path), "--department-id", "12", "--report-dir", str(reports)]
    assert ccr.main(args) == 0
    assert json.loads((reports / "report.json").read_text())["validation_passed"]
    del world[PDF_URL]
    assert ccr.main(args) == 1
    assert "Errors:" in (reports / "summary.md").read_text()
    with pytest.raises(SystemExit):
        ccr.main(["--department-id", "12", "--delay", "-1"])


def test_repeal_date_and_review_requirement_are_preserved(tmp_path, world) -> None:
    mutate(world, RULE_URL, "PROCEDURES OF REVIEW </p>", (
        "PROCEDURES OF REVIEW [Repealed eff. 08/15/2019] </p>"
    ))
    report = run(tmp_path, world)
    assert report.classification_counts == {"source_repealed": 1}
    record = json.loads((tmp_path / INVENTORY).read_bytes())
    assert record["repeal_date"] == "2019-08-15"
    assert record["review_required"] is True
    record["review_required"] = False
    with pytest.raises(ValueError):
        ccr.CCRCurrentRecord.model_validate(record)


@pytest.mark.parametrize("mode,error", [
    ("url_key", "map key"), ("provenance", "provenance disagrees"),
    ("scope", "different collection scope"),
])
def test_inconsistent_prior_provenance_is_rejected(tmp_path, world, mode, error) -> None:
    assert run(tmp_path, world).status == "updated"
    state = json.loads((tmp_path / STATE).read_bytes())
    if mode == "url_key":
        state["sources"][PDF_URL]["url"] = WORD_URL
    elif mode == "provenance":
        state["sources"][PDF_URL]["first_retrieved_at"] = "2026-01-01T00:00:00Z"
    else:
        state["catalog_url"] = ccr.CATALOG_URL + "?changed=true"
    (tmp_path / STATE).write_text(json.dumps(state))
    assert error in " ".join(run(tmp_path, world).errors)


@pytest.mark.parametrize("before,after,error", [
    ("agencyID=10", "agencyID=10&agencyID=11", "exactly one"),
    ("NumericalCCRDocList.do", "NumericalCCRDocList.do/changed", "endpoint"),
    ("</body>", '<a href="?more=true">Next page</a></body>', "pagination"),
    ("1300 Department", "Department", "numerical grouping"),
    ('name="1300"', 'name="9999"', "department section"),
])
def test_malformed_catalog_or_query_requires_review(tmp_path, world, before, after, error) -> None:
    mutate(world, ccr.CATALOG_URL, before, after)
    assert error in " ".join(run(tmp_path, world).errors)
