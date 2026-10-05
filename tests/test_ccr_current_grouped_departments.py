"""Combined SOS numerical groupings must each contain a complete agency list."""
from __future__ import annotations

import pytest

from geode.pipeline import ccr_current as ccr


def catalog(*, omit_second: bool = False, missing_agency: bool = False,
            duplicate_heading: bool = False, foreign_department: bool = False) -> ccr._Document:
    """Build a small explicit catalog with SOS's repeated-group structure."""
    rows = []
    groups = ["1305"] if omit_second else ["1305", "2505"]
    if duplicate_heading:
        groups.append("2505")
    for group in groups:
        rows.append(f'<tr><td><a name="{group}">{group}</a></td><td>Example Department</td></tr>')
        for agency in ["47", "69"]:
            if missing_agency and group == "2505" and agency == "69":
                continue
            dept = "99" if foreign_department and group == "2505" and agency == "69" else "7"
            rows.append('<tr><td></td><td><a href="/CCR/NumericalCCRDocList.do?'
                        f'deptID={dept}&deptName=2505,1305 Example Department&agencyID={agency}'
                        f'&agencyName=Agency {agency}">Agency {agency}</a></td></tr>')
    body = ('<html><body><table>' + ''.join(rows) + '</table></body></html>').encode()
    return ccr._parse_html(body, 'text/html')


def test_combined_department_accepts_two_complete_alias_sections() -> None:
    """Distinct numerical headers can name the same complete department."""
    assert set(ccr._agencies(catalog(), ccr.CATALOG_URL, "7")) == {"47", "69"}


@pytest.mark.parametrize('change,reason', [
    ({'omit_second': True}, 'Missing or ambiguous'),
    ({'duplicate_heading': True}, 'Missing or ambiguous'),
    ({'missing_agency': True}, 'identities disagree'),
    ({'foreign_department': True}, 'unexpected endpoint or department'),
])
def test_every_alias_section_is_checked(change: dict, reason: str) -> None:
    """Do not let another complete alias hide an incomplete or contradictory one."""
    with pytest.raises(ValueError, match=reason):
        ccr._agencies(catalog(**change), ccr.CATALOG_URL, "7")
