"""Real source snippets and deliberately synthetic edge cases for the daily parser."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from geode.connectors.register_daily_parser import (
    RegisterParseError,
    decode_register_html,
    parse_edocket_detail,
    parse_register_index,
    parse_register_issue,
    register_html_fingerprint,
)

FIXTURES = Path(__file__).parent / "fixtures" / "register_daily"
ISSUE = "https://www.sos.state.co.us/CCR/RegisterContents.do?publicationDay=08/25/2026"
HEARING = "https://www.sos.state.co.us/CCR/DisplayHearingDetails.do?trackingNumber=2026-00370"


def issue_html() -> str:
    """Read a factual excerpt with one row from each live rulemaking table."""

    return (FIXTURES / "official_2026_08_25_excerpt.html").read_text()


def test_real_tables_keep_proposals_and_distinguish_material_dates() -> None:
    """The actual source's AG opinion, effective, and expiration columns differ."""

    rows = parse_register_issue(issue_html(), date(2026, 8, 25), ISSUE)
    assert [row.notice_type for row in rows] == ["proposed", "adopted", "emergency", "terminated"]
    proposed, adopted, emergency, terminated = rows
    assert proposed.ccr_citation is None
    assert proposed.edocket_tracking_number == "2026-00370"
    assert proposed.hearing_detail_url == HEARING
    assert proposed.hearing_date == date(2026, 10, 8)
    assert proposed.document_urls == [
        "https://www.sos.state.co.us/CCR/Upload/NoticeOfRulemaking/"
        "ProposedRuleAttach2026-00370.docx"
    ]
    assert proposed.title == "RULES FOR THE ADMINISTRATION OF THE FACILITY SCHOOLS ACT"
    assert adopted.ccr_rule_affected == "1_CCR_204-30"
    assert adopted.effective_date == date(2026, 9, 14)
    assert "08/03/2026" in adopted.source_evidence  # The earlier AG opinion is preserved.
    assert emergency.effective_date == date(2026, 8, 12)
    assert emergency.expiration_date == date(2026, 11, 13)
    assert terminated.termination_date == date(2026, 8, 5)
    assert terminated.effective_date is None
    assert terminated.edocket_url == (
        "https://www.sos.state.co.us/CCR/eDocketDetails.do?trackingNum=2026-00275"
    )
    assert "The hearing will be rescheduled." in terminated.source_evidence
    assert [row.row_number for row in rows] == [1, 2, 3, 4]


def test_real_hearing_detail_resolves_only_labeled_ccr_and_tracking() -> None:
    """The hearing detail identifies a proposal whose index row lacks its CCR."""

    html = (FIXTURES / "official_hearing_2026_00370_excerpt.html").read_text()
    detail = parse_edocket_detail(html, HEARING)
    assert detail.ccr_citation == "1 CCR 304-1"
    assert detail.ccr_rule_affected == "1_CCR_304-1"
    assert detail.tracking_number == "2026-00370"
    assert detail.effective_date is None
    with pytest.raises(RegisterParseError, match="differs"):
        parse_edocket_detail(html, HEARING.replace("2026-00370", "2026-00001"))


def test_index_html_only_sorted_and_deduplicated() -> None:
    """Synthetic index links use factual URL shapes; PDF versions are excluded."""

    first = "/CCR/RegisterContents.do?publicationDay=08/10/2026&Volume=49"
    second = "/CCR/RegisterContents.do?publicationDay=08/25/2026&Volume=49"
    html = (
        f'<h1>Colorado Register</h1><a href="{second}">HTML</a>'
        f'<a href="{first}">HTML</a><a href="{first}">HTML</a>'
        '<a href="/CCR/RegisterPdfContents.do?publicationDay=08/25/2026">PDF</a>'
    )
    rows = parse_register_index(html, "https://www.sos.state.co.us/CCR/RegisterHome.do?pyear=2026")
    assert [row.publication_date for row in rows] == ["2026-08-10", "2026-08-25"]


@pytest.mark.parametrize("replacement", ["Adoption date", "Effective from"])
def test_changed_date_header_fails_closed(replacement: str) -> None:
    """Synthetic schema drift must not silently reinterpret the date column."""

    html = issue_html().replace("Effective date", replacement)
    with pytest.raises(RegisterParseError, match="Unexpected columns"):
        parse_register_issue(html, date(2026, 8, 25), ISSUE)


def test_unknown_section_missing_cells_and_unknown_js_fail_closed() -> None:
    """Synthetic malformed source variants must reject the complete issue."""

    mutations = [
        issue_html().replace("Emergency Rules Adopted", "Special Rules Adopted"),
        issue_html().replace("<td> Facility Schools Board </td>", ""),
        issue_html().replace("'/CCR/DisplayHearingDetails.do?trackingNumber='", "'/other='"),
    ]
    for html in mutations:
        with pytest.raises(RegisterParseError):
            parse_register_issue(html, date(2026, 8, 25), ISSUE)


@pytest.mark.parametrize("html", ["", "<h1>Colorado Register</h1>", "<p>Access denied</p>"])
def test_empty_or_blocked_source_cannot_be_a_success(html: str) -> None:
    """Synthetic failures differ from a successful no-change source check."""

    with pytest.raises(RegisterParseError):
        parse_register_issue(html, date(2026, 8, 25), ISSUE)
    with pytest.raises(RegisterParseError):
        parse_register_index(html, "https://www.sos.state.co.us/CCR/RegisterHome.do")


@pytest.mark.parametrize("bad_url", [
    "http://www.sos.state.co.us/CCR/x.docx",
    "https://www.sos.state.co.us.evil.example/CCR/x.docx",
    "https://other.example/x.docx",
])
def test_document_links_require_https_sos(bad_url: str) -> None:
    """Synthetic external or insecure document links cannot enter the fetch queue."""

    html = issue_html().replace(
        "/CCR/Upload/NoticeOfRulemaking/ProposedRuleAttach2026-00370.docx", bad_url,
    )
    with pytest.raises(RegisterParseError, match="HTTPS"):
        parse_register_issue(html, date(2026, 8, 25), ISSUE)


def test_missing_labeled_ccr_does_not_use_unrelated_citation() -> None:
    """Synthetic narrative citations cannot substitute for the authoritative CCR field."""

    html = (
        "<h1>Hearing detail</h1><p>See also 5 CCR 1001-3</p>"
        "<table><tr><th>Tracking Number</th><td>2026-00370</td></tr></table>"
    )
    with pytest.raises(RegisterParseError, match="explicit CCR"):
        parse_edocket_detail(html, HEARING)


def test_valid_empty_rule_table_and_ignored_calendar() -> None:
    """Synthetic explicit empty tables are distinguishable from empty responses."""

    html = (
        '<h1>Colorado Register</h1><h2>Notices of proposed rulemaking</h2>'
        '<table><tr><th>Department</th><th>Agency</th><th>Proposed rules</th>'
        '<th>Hearing</th></tr></table><h2>Calendar of Hearings</h2>'
        '<table><tr><th>Agency</th><th>Rule</th><th>Hearing</th></tr>'
        '<tr><td>A</td><td>Some rule</td><td>09/25/2026</td></tr></table>'
    )
    assert parse_register_issue(html, date(2026, 8, 25), ISSUE) == []


def test_wrong_issue_or_index_year_is_rejected() -> None:
    """Synthetic wrong-page responses cannot be treated as a source update."""

    html = issue_html().replace(
        "<h1>Colorado Register</h1>",
        "<h1>Colorado Register</h1><p>July 25, 2026 - Volume 49 , No. 14</p>",
    )
    with pytest.raises(RegisterParseError, match="heading differs"):
        parse_register_issue(html, date(2026, 8, 25), ISSUE)
    with pytest.raises(RegisterParseError, match="publication date differs"):
        parse_register_issue(issue_html(), date(2026, 8, 10), ISSUE)
    index = (
        '<h1>Colorado Register</h1><a href="/CCR/RegisterContents.do?'
        'publicationDay=08/25/2026">HTML</a>'
    )
    with pytest.raises(RegisterParseError, match="different publication year"):
        parse_register_index(index, "https://www.sos.state.co.us/CCR/RegisterHome.do?pyear=2025")


def test_only_known_passive_script_nonce_is_ignored_in_comparison() -> None:
    """A verified source wrapper's random tokens do not invent legal changes."""

    import re

    script = (FIXTURES / "official_passive_cf_script.html").read_bytes()
    changed_script = re.sub(rb"r:'[^']+'", b"r:'0123456789abcdef'", script)
    changed_script = re.sub(rb"t:'[^']+'", b"t:'MDEyMzQ1Njc4OQ=='", changed_script)
    content = b"<html><h1>Colorado Register</h1><p>Fee: $10</p>"
    first = content + script + b"</html>"
    second = content + changed_script + b"</html>"
    assert first != second
    assert register_html_fingerprint(first) == register_html_fingerprint(second)
    assert register_html_fingerprint(first) == register_html_fingerprint(content + b"</html>")
    assert register_html_fingerprint(first) != register_html_fingerprint(
        second.replace(b"Fee: $10", b"Fee: $20")
    )
    assert script in first  # The caller's archived source bytes remain intact.


def test_unknown_or_extended_scripts_remain_significant() -> None:
    """Neither generic scripts nor a changed wrapper can hide a material change."""

    first = b"<html><script>var fee = 10;</script></html>"
    second = first.replace(b"10", b"20")
    assert register_html_fingerprint(first) != register_html_fingerprint(second)
    script = (FIXTURES / "official_passive_cf_script.html").read_bytes()
    extended = script.replace(b"<script>", b"<script>var legalContent='changed';")
    assert register_html_fingerprint(script) != register_html_fingerprint(extended)
    unknown = (
        b"<script>window.__CF$cv$params = 'fee10';"
        b"var path = '/cdn-cgi/challenge-platform/scripts/jsd/main.js';</script>"
    )
    assert register_html_fingerprint(unknown) != register_html_fingerprint(
        unknown.replace(b"fee10", b"fee20")
    )


@pytest.mark.parametrize("label", ["windows-1252", "ISO-8859-1", "us-ascii"])
def test_declared_legacy_html_preserves_curly_quotes(label: str) -> None:
    """HTML's Latin-1 and ASCII labels use the Windows-1252 mapping."""

    body = b"<html><p>The agency\x92s \x93approved\x94 rules \x96 revised.</p></html>"
    decoded = decode_register_html(body, f'text/html; charset="{label}"')
    assert "agency’s “approved” rules – revised" in decoded
    assert "\ufffd" not in decoded


def test_bom_meta_and_utf8_defaults_preserve_text() -> None:
    """BOM outranks headers, headers outrank meta, and undeclared UTF-8 stays UTF-8."""

    import codecs

    text = "<html><p>The agency’s rules</p></html>"
    utf8 = text.encode("utf-8")
    assert decode_register_html(codecs.BOM_UTF8 + utf8, "text/html; charset=latin1") == text
    assert decode_register_html(utf8, "text/html") == text
    cp1252 = text.encode("windows-1252")
    assert decode_register_html(cp1252, "text/html") == text
    meta = b'<html><head><meta charset="windows-1252"></head><p>Agency\x92s rules</p></html>'
    assert "Agency’s rules" in decode_register_html(meta, "text/html")
    pragma = meta.replace(
        b'charset="windows-1252"',
        b'http-equiv="Content-Type" content="text/html; charset=ISO-8859-1"',
    )
    assert "Agency’s rules" in decode_register_html(pragma, "text/html")
    assert "Agency’s rules" in decode_register_html(
        meta.replace(b"windows-1252", b"utf-8"), "text/html; charset=windows-1252"
    )


@pytest.mark.parametrize("label", ["made-up", "utf-7", "utf-32", ""])
def test_unknown_declared_encoding_fails(label: str) -> None:
    """Unsupported source declarations require review, even for ASCII-only content."""

    with pytest.raises(RegisterParseError, match="Unknown or unsupported"):
        decode_register_html(b"<html>text</html>", f'text/html; charset="{label}"')
    with pytest.raises(RegisterParseError, match="Unknown or unsupported"):
        decode_register_html(f'<html><meta charset="{label}"></html>'.encode(), "text/html")


def test_declared_utf8_errors_never_silently_fall_back() -> None:
    """A malformed declared encoding is an error, rather than replacement text."""

    body = b"<html>Agency\x92s rules</html>"
    with pytest.raises(UnicodeDecodeError):
        decode_register_html(body, "text/html; charset=utf-8")
    with pytest.raises(RegisterParseError, match="non-HTML"):
        decode_register_html(b"not HTML\x92", "application/octet-stream")
    with pytest.raises(UnicodeDecodeError):
        decode_register_html(b"<html>undefined \x81</html>", "text/html")
