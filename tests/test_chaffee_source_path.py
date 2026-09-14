"""Accept the retained county referrals without approving other publisher tenants."""
import pytest

from geode.constants import AUTHORIZED_SOURCE_HOSTS, AUTHORIZED_SOURCE_PATHS
from geode.pipeline.manual_source_intake import ManualSourceIntakeRequest
from geode.schemas.validators import require_official_source_url

PREFIX = "https://cms2.revize.com/revize/chaffeecounty/"
SOURCES = (
    PREFIX + "Documents/Departments/Building%20Department/Adopted%20Codes%20&%20Design%20Criteria/"
    "2026-02%20Ordinance%20Adopting%20the%20CWRC%20with%20Local%20"
    "Amendments_RECORDED.pdf?t=202606021136110",
    PREFIX + "2026-01%20Ordinance%20Chaffee%20County%20Electric%20Preferred%20"
    "Amendments_RECORDED.pdf?t=202608031134050",
)

@pytest.mark.parametrize("url", SOURCES)
def test_exact_retained_referral_urls_are_preserved(url: str) -> None:
    """Keep the exact official referral strings after validation."""
    assert require_official_source_url(url) == url

@pytest.mark.parametrize("url", [
    "http://cms2.revize.com/revize/chaffeecounty/a.pdf",
    "https://cms2.revize.com/revize/anothercounty/a.pdf",
    "https://cms2.revize.com/revize/chaffeecounty-other/a.pdf",
    "https://cms2.revize.com/revize/chaffeecounty",
    "https://cms2.revize.com/",
    "https://cms2.revize.com.evil.example/revize/chaffeecounty/a.pdf",
    "https://evil.cms2.revize.com/revize/chaffeecounty/a.pdf",
    "https://cms2.revize.com@evil.example/revize/chaffeecounty/a.pdf",
    "https://evil.example@cms2.revize.com/revize/chaffeecounty/a.pdf",
    "https://cms2.revize.com:443/revize/chaffeecounty/a.pdf",
    "https://cms2.revize.com:8443/revize/chaffeecounty/a.pdf",
    "https://cms2.revize.com./revize/chaffeecounty/a.pdf",
    PREFIX + "../anothercounty/a.pdf",
    PREFIX + "./a.pdf",
    PREFIX + "folder/../../anothercounty/a.pdf",
    PREFIX + "%2e%2e/anothercounty/a.pdf",
    PREFIX + "%2E./anothercounty/a.pdf",
    PREFIX + "%252e%252e/anothercounty/a.pdf",
    PREFIX + "%2e%2e%2fanothercounty/a.pdf",
    PREFIX + "%2E%2E%2Fanothercounty/a.pdf",
    PREFIX + "%5c..%5canothercounty/a.pdf",
    PREFIX + "\\..\\anothercounty/a.pdf",
    PREFIX + "..;ignored/anothercounty/a.pdf",
    PREFIX + "%2e%2e%3bignored/anothercounty/a.pdf",
    PREFIX + "%00/a.pdf",
    PREFIX + "%0a/a.pdf",
    PREFIX + "%7f/a.pdf",
    PREFIX + "a\nb.pdf",
    PREFIX + "%ff.pdf",
    PREFIX + "%invalid.pdf",
])
def test_cross_tenant_and_ambiguous_urls_are_rejected(url: str) -> None:
    """Reject ambiguous or cross-tenant paths before intake."""
    with pytest.raises(ValueError):
        require_official_source_url(url)

def test_shared_host_does_not_get_hostwide_approval() -> None:
    """Limit publisher approval to the reviewed county tenant."""
    assert "cms2.revize.com" not in AUTHORIZED_SOURCE_HOSTS
    assert AUTHORIZED_SOURCE_PATHS["cms2.revize.com"] == ("/revize/chaffeecounty/",)

def test_actual_download_request_keeps_exact_identity() -> None:
    """Preserve URL and source identity through the intake model."""
    request = ManualSourceIntakeRequest(
        record_id="chaffee-electric-ordinance-2026-01-atlas-directed",
        layer_id="08_County_Authorities", source_file="source/original.pdf",
        official_source_name="Chaffee County Ordinance 2026-01",
        official_source_url=SOURCES[1], acquisition_method="manual_official_download",
        received_from="County-linked publisher; exact response evidence retained",
        reviewer_name="Atlas",
        custody_note="Actual HTTP receipt and later repository intake remain separate.",
        expected_sha256="c0bfb6e8d4adb846fd62ec7dabbdd824286f7432be6a82b6b2d2264d4553cdf6",
    )
    assert request.official_source_url == SOURCES[1]
    assert request.acquisition_method == "manual_official_download"
    assert not request.allow_duplicate
