"""Validate the exact county asset host supported by retained official referrals."""

from __future__ import annotations

import pytest

from geode.constants import AUTHORIZED_SOURCE_HOSTS
from geode.schemas.validators import require_official_source_url


SOURCE_URLS = (
    'https://epc-assets.elpasoco.com/wp-content/uploads/sites/12/fees/Fee-Schedule-2026-ADA.pdf',
    (
        'https://epc-assets.elpasoco.com/wp-content/uploads/sites/18/2025/06/3-BoH-2024-EHS'
        '-Fee-Schedule-Chapter-3_Acc-Checked-June-2025.pdf'
    ),
    'https://epc-assets.elpasoco.com/wp-content/uploads/sites/5/Ordinance-26-01-Accessible.pdf',
    (
        'https://epc-assets.elpasoco.com/wp-content/uploads/sites/12/LDC-Resolution/Appendi'
        'x-E-Wildfire-Resiliency-Requirements-ADA.pdf'
    ),
    (
        'https://epc-assets.elpasoco.com/wp-content/uploads/sites/5/18-03-Unsafe-Buildings-'
        'Accessible.pdf'
    ),
    (
        'https://epc-assets.elpasoco.com/wp-content/uploads/sites/18/2025/06/2-BoH.Regulati'
        'on.Chapter.2.Admin_.Regs_.2011_1Acc-Checked-June-2025.pdf'
    ),
    (
        'https://epc-assets.elpasoco.com/wp-content/uploads/sites/18/2025/06/1-BoH.Regulati'
        'on.Chapter.1.Bylaws.2011_0Acc-Checked-June-2025.pdf'
    ),
    (
        'https://epc-assets.elpasoco.com/wp-content/uploads/sites/18/2025/06/1-SpanishBoh.-'
        'Regulation-Chapter1-SpanishAcc-Checked-June-2025.pdf'
    ),
    (
        'https://epc-assets.elpasoco.com/wp-content/uploads/sites/18/2025/06/3-Spanish-BoH-'
        '2024-EHS-Fee-Schedule-Chapter-3_EspanolAcc-Checked-June-2025.pdf'
    ),
)


@pytest.mark.parametrize("url", SOURCE_URLS)
def test_el_paso_official_referral_asset_urls_are_accepted(url: str) -> None:
    """Accept all nine exact document destinations bound by official county anchors."""
    assert require_official_source_url(url) == url


@pytest.mark.parametrize("url", [
    "http://epc-assets.elpasoco.com/example.pdf",
    "https://epc-assets.elpasoco.com.example.org/example.pdf",
    "https://evil.epc-assets.elpasoco.com/example.pdf",
    "https://epc-assets-elpasoco.com/example.pdf",
    "https://epc-assets.elpasoco.com@evil.example/example.pdf",
    "https://evil.example@epc-assets.elpasoco.com/example.pdf",
    "https://epc-assets.elpasoco.com:8443/example.pdf",
    "https://epc-assets.elpasoco.com./example.pdf",
])
def test_asset_host_addition_does_not_accept_lookalikes(url: str) -> None:
    """Keep non-HTTPS, lookalikes, subdomains, userinfo and nonstandard ports rejected."""
    with pytest.raises(ValueError):
        require_official_source_url(url)


def test_only_exact_el_paso_asset_host_is_present() -> None:
    """The explicit addition does not grant wildcard access to related hosts."""
    assert "epc-assets.elpasoco.com" in AUTHORIZED_SOURCE_HOSTS
    assert "evil.epc-assets.elpasoco.com" not in AUTHORIZED_SOURCE_HOSTS
