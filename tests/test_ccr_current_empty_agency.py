"""Source-derived and contradictory empty-catalog acceptance cases."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from geode.pipeline import ccr_current as c
from geode.pipeline.ccr_current import _explicit_empty_agency as explicit_empty_agency

HERE = Path(__file__).resolve().parent / 'fixtures/ccr_current'
BODY = (HERE / 'agency-empty-228.html').read_bytes()
URL = json.loads((HERE / 'agency-empty-228-receipt.json').read_bytes())['url']


def check(body: bytes = BODY, url: str = URL) -> bool:
    """Parse and test the frozen or mutated source."""
    return explicit_empty_agency(c._parse_html(body, 'text/html;charset=ISO-8859-1'), url)


def test_actual_empty() -> None:
    """Accept the retained explicit response, whereas old parser refuses it."""
    assert check()
    assert c._rules(c._parse_html(BODY, 'text/html;charset=ISO-8859-1'), URL) == {}


@pytest.mark.parametrize('old,new', [
    (b'No results found', b''),
    (b'No results found', b'No results currently found'),
    (b'No results found', b'<p>No results found</p>'),
])
def test_no_exact_direct_marker(old: bytes, new: bytes) -> None:
    """Missing, altered and misplaced markers cannot authorize emptiness."""
    assert not check(BODY.replace(old, new))


@pytest.mark.parametrize('old,new', [
    (b'No results found', b'No results found<tr><td>No results found</td></tr>'),
    (b'No results found', b'No results found<table><tr><th>CCR#</th><th>Title</th></tr></table>'),
    (b'No results found', b'No results found<table><tr><td>unparsed rule</td></tr></table>'),
    (b'No results found', b'No results found<a href="DisplayRule.do?ruleId=1">rule</a>'),
    (b'No results found', b'No results found ignored extra result'),
    (b'&gt; Pesticide Disposal Enterprise Board', b'&gt; Another Board'),
    (b'NumericalAgencyList.do?&deptID=1', b'NumericalAgencyList.do?&deptID=2'),
    (b'>Department of Agriculture</a> &gt;', b'>Another Department</a> &gt;'),
    (b'value="Back"', b'value="Next"'),
    (b'</html>', b''),
])
def test_ambiguous_or_contradictory_source(old: bytes, new: bytes) -> None:
    """Reject malformed structure, incompatible rows and mismatched identity."""
    assert old in BODY
    with pytest.raises(ValueError):
        changed = BODY.replace(old, new)
        if not check(changed):
            c._rules(c._parse_html(changed, 'text/html;charset=ISO-8859-1'), URL)


@pytest.mark.parametrize('url', [
    URL + '&agencyID=228',
    URL.replace('agencyID=228', 'agencyID=other'),
    URL.replace('deptID=1', 'deptID=2'),
    URL.replace('1210%20Pesticide', 'Pesticide'),
    URL.replace('NumericalCCRDocList.do', 'DisplayRule.do'),
    URL.replace('https://www.sos.state.co.us', 'https://example.com'),
])
def test_requested_identity_refusal(url: str) -> None:
    """Require exact source endpoint and unique matching request identities."""
    with pytest.raises(ValueError):
        check(url=url)


def test_empty_source_cannot_silently_remove_previously_collected_rules(tmp_path) -> None:
    """An explicit empty page is observed evidence, not permission to discard prior rules."""
    from tests.test_ccr_current import AGENCY_URL, STATE, run, world
    from geode.pipeline.register_daily import FetchResult

    source = world.__wrapped__()
    assert run(tmp_path, source).validation_passed
    previous = (tmp_path / STATE).read_bytes()
    empty = BODY.replace(b'Department of Agriculture', b'Department of Local Affairs')
    empty = empty.replace(b'deptID=1&', b'deptID=12&')
    empty = empty.replace(b'Pesticide Disposal Enterprise Board', b'Board of Assessment Appeals')
    source[AGENCY_URL] = FetchResult(AGENCY_URL, empty, 'text/html;charset=ISO-8859-1')
    report = run(tmp_path, source)
    assert report.status == 'failed' and any('disappeared' in e for e in report.errors)
    assert (tmp_path / STATE).read_bytes() == previous


HYPHEN_BODY = (HERE / 'agency-empty-229.html').read_bytes()
HYPHEN_URL = json.loads((HERE / 'agency-empty-229-receipt.json').read_bytes())['url']


def test_hyphenated_numeric_empty_agency_prefix() -> None:
    """Accept the exact source's numbered enterprise without weakening DOM checks."""
    assert check(HYPHEN_BODY, HYPHEN_URL)
    document = c._parse_html(HYPHEN_BODY, 'text/html;charset=ISO-8859-1')
    assert c._rules(document, HYPHEN_URL) == {}


@pytest.mark.parametrize('prefix', [
    '702--11', '-702-11', '702-', '702A-11', '702,', ',702',
    '702,,11', '702-11x', '', '702/11',
])
def test_malformed_empty_agency_numeric_prefix(prefix: str) -> None:
    """Only complete decimal components separated by one comma or hyphen qualify."""
    with pytest.raises(ValueError):
        check(HYPHEN_BODY, HYPHEN_URL.replace('702-11%20', prefix + '%20'))


@pytest.mark.parametrize('old,new', [
    (b'&gt; STRENGTHEN COLORADO HOMES ENTERPRISE', b'&gt; SOME OTHER ENTERPRISE'),
    (b'NumericalAgencyList.do?&deptID=18', b'NumericalAgencyList.do?&deptID=1'),
    (b'No results found', b'No results found<table><tr><td>unparsed rule</td></tr></table>'),
    (b'No results found', b'No results found<a href="DisplayRule.do?ruleId=1">rule</a>'),
    (b'No results found', b'No results found<tr><td>No results found</td></tr>'),
])
def test_hyphenated_source_contradictions(old: bytes, new: bytes) -> None:
    """The new numeric form must retain all prior identity and content refusals."""
    assert old in HYPHEN_BODY
    with pytest.raises(ValueError):
        check(HYPHEN_BODY.replace(old, new), HYPHEN_URL)
