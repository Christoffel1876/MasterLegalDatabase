"""Accept the county's recorded migration while retaining exact-host boundaries."""
from __future__ import annotations

import pytest

from geode.pipeline.manual_source_intake import ManualSourceIntakeRequest
from geode.schemas.validators import require_official_source_url

SOURCE_URL = 'https://www.douglasco.gov/documents/fee-schedule.pdf/'


@pytest.mark.parametrize('url', [
    SOURCE_URL,
    'https://www.douglasco.gov/health-department/fees/',
    'https://www.douglas.co.us/',
    'https://publicnotices.douglas.co.us/',
])
def test_migrated_and_preexisting_official_urls(url: str) -> None:
    """Accept retained official referral destinations without removing the old domains."""
    assert require_official_source_url(url) == url


@pytest.mark.parametrize('url', [
    'http://www.douglasco.gov/documents/fee-schedule.pdf/',
    'https://douglasco.gov/documents/fee-schedule.pdf/',
    'https://evil.www.douglasco.gov/example.pdf',
    'https://www.douglasco.gov.example.org/example.pdf',
    'https://www-douglasco.gov/example.pdf',
    'https://www.douglasco.gov@evil.example/example.pdf',
    'https://evil.example@www.douglasco.gov/example.pdf',
    'https://www.douglasco.gov:8443/example.pdf',
    'https://www.douglasco.gov./example.pdf',
])
def test_unproved_hosts_and_url_forms_remain_rejected(url: str) -> None:
    """Keep HTTPS, exact hostname, userinfo and port restrictions intact."""
    with pytest.raises(ValueError):
        require_official_source_url(url)


def test_manual_request_keeps_exact_source_url_and_digest() -> None:
    """Exercise the intake boundary that previously rejected the verified source."""
    request = ManualSourceIntakeRequest(
        record_id='douglas-ehs-fees-atlas-directed', layer_id='08_County_Authorities',
        source_file='review/original.pdf', official_source_name='Douglas County EHS fee schedule',
        official_source_url=SOURCE_URL, acquisition_method='manual_official_download',
        received_from='Retained official county response', reviewer_name='Atlas',
        custody_note='Exact official referral and PDF response are retained separately.',
        expected_sha256='35e90b9c3b73b414155ed965898c8c270757f1c367cbe50d7645956039dbb687')
    assert request.official_source_url == SOURCE_URL
    assert request.expected_sha256 == (
        '35e90b9c3b73b414155ed965898c8c270757f1c367cbe50d7645956039dbb687')
    assert request.allow_duplicate is False
