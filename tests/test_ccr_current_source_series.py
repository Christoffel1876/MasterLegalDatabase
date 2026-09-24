"""Source subdivisions must not collapse into the base CCR identity."""
from __future__ import annotations

from urllib.parse import quote

import pytest

from geode.pipeline import ccr_current as ccr
from geode.pipeline.register_daily import FetchResult
from tests.test_ccr_current import AGENCY_URL, RULE_URL, STATE, INVENTORY, run, world


def changed_world(original: dict, suffix: str) -> dict:
    """Extend all independent source labels/links in a coherent synthetic source set."""
    old = '8 CCR 1301-1'
    new = old + suffix
    result = {}
    for key, value in original.items():
        url = key.replace(quote(old), quote(new))
        body = value.content.replace(old.encode(), new.encode())
        body = body.replace(quote(old).encode(), quote(new).encode())
        result[url] = FetchResult(url, body, value.content_type)
    return result


@pytest.mark.parametrize('suffix', [' 8.000', ' Rules 1-17', ' R18 Ex 02-06', ' A', ' MED 11E'])
def test_complete_collection_preserves_exact_suffixed_source(tmp_path, world, suffix) -> None:
    """Observed suffix forms remain separate source records with exact download labels."""
    source = changed_world(world, suffix)
    report = run(tmp_path, source)
    assert report.status == 'updated', report.errors
    record = ccr.CCRCurrentRecord.model_validate_json((tmp_path/INVENTORY).read_bytes())
    assert record.ccr_citation == '8 CCR 1301-1' + suffix
    assert record.id == '8_CCR_1301-1__rule_2567'
    assert all(quote(record.ccr_citation) in url
               for version in record.versions for url in version.document_urls)
    assert (tmp_path/STATE).is_file()


def test_distinct_source_series_have_distinct_stable_identities() -> None:
    """Base identity compatibility and explicit SOS subdivision identity are different cases."""
    assert ccr.record_identity('8 CCR 1301-1','2567') == '8_CCR_1301-1'
    assert ccr.record_identity('10 CCR 2505-10 8.100','1') != ccr.record_identity(
        '10 CCR 2505-10 8.200','2')


@pytest.mark.parametrize('mismatch', ['listing', 'title', 'handler'])
def test_suffix_disagreement_fails_before_any_inventory(tmp_path, world, mismatch) -> None:
    """A shared base citation cannot mask disagreement about the exact source subdivision."""
    source=changed_world(world,' 8.000')
    rule_url=RULE_URL.replace(quote('8 CCR 1301-1'),quote('8 CCR 1301-1 8.000'))
    if mismatch == 'listing':
        url=AGENCY_URL
        before=b'8 CCR 1301-1 8.000 </a>'
        after=b'8 CCR 1301-1 8.100 </a>'
    elif mismatch == 'title':
        url=rule_url
        before=b'8 CCR 1301-1 8.000 &nbsp;'
        after=b'8 CCR 1301-1 8.0000 &nbsp;'
    else:
        url=rule_url
        before=b"'8 CCR 1301-1 8.000'"
        after=b"'8 CCR 1301-1 8.100'"
    value=source[url]
    assert before in value.content
    source[url]=FetchResult(url,value.content.replace(before,after),value.content_type)
    report=run(tmp_path,source)
    assert report.status=='failed' and not report.validation_passed
    assert not (tmp_path/INVENTORY).exists()


@pytest.mark.parametrize('value', [
    '8 CCR 1301-1 ../other', '8 CCR 1301-1 &x=y', '8 CCR 1301-1\\x',
    '8 CCR 1301-1\n8 CCR 1301-2', '8 CCR 1301-1 ' + 'X'*201,
])
def test_unbounded_or_executable_labels_are_refused(value) -> None:
    """Series labels are literal bounded source fields, not paths or script fragments."""
    with pytest.raises(ValueError,match='citation'):
        ccr.record_identity(value,'2567')
