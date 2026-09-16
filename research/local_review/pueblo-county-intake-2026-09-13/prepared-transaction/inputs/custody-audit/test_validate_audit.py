"""Offline custody mutations: no source transcription, public transport or canonical writes."""
from __future__ import annotations

import json
from pathlib import Path
import shutil

import pytest

from validate_audit import validate

SOURCE = Path(__file__).resolve().parent


@pytest.fixture
def audit_copy(tmp_path: Path) -> Path:
    """Copy the existing audit into a private mutation fixture."""
    target = tmp_path / 'audit'
    shutil.copytree(SOURCE, target)
    return target


def test_actual_custody_without_external_repository(audit_copy: Path) -> None:
    """Measured source identities and portable metadata checks need no original workspace."""
    result = validate(audit_copy, check_manifest=False)
    assert result.events[0].body.size_bytes == 75214
    assert result.events[1].reported_http_status == 403
    assert result.canonical_intakes_by_auditor == result.independent_source_visual_pages == 0


@pytest.mark.parametrize('path', [
    'received/raw/SHEXT002-A001.pdf', 'received/raw/SHEXT002-A001.bin',
    'received/raw/SHEXT002-A002.html', 'received/headers/SHEXT002-A001.json',
    'received/reservations/SHEXT002-A001.json', 'received/results/SHEXT002-A002.json',
    'parent-audit/received/raw/SHEXT001-A031.html',
    'received/derived/SHEXT002-A001_page_02_of_02.png',
])
def test_changed_original_or_referral_refused(audit_copy: Path, path: str) -> None:
    """Original bytes, requested-action records and authorized referral remain immutable."""
    item = audit_copy / path
    item.write_bytes(item.read_bytes() + b'alteration')
    with pytest.raises(ValueError, match='Changed evidence'):
        validate(audit_copy, check_manifest=False)


@pytest.mark.parametrize('field,value', [
    ('answer_safe', True), ('legal_currentness', 'current'),
    ('independent_source_visual_pages', 2), ('canonical_intakes_by_auditor', 1),
    ('hidden_network_requests_measured', True),
])
def test_no_status_promotion(audit_copy: Path, field: str, value: object) -> None:
    """Custody checks cannot silently become legal-currentness or direct visual certification."""
    path = audit_copy / 'AUDIT.json'
    data = json.loads(path.read_bytes())
    data[field] = value
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        validate(audit_copy, check_manifest=False)


def test_wrong_authority_and_incoming_filename_refused(audit_copy: Path) -> None:
    """The recommendation is county-specific and keeps the actual incoming basename."""
    path = audit_copy / 'INTAKE_RECOMMENDATION.json'
    original = json.loads(path.read_bytes())
    wrong = dict(original, authority_id='CO-MUNICIPAL-PUEBLO')
    path.write_text(json.dumps(wrong))
    with pytest.raises(ValueError):
        validate(audit_copy, check_manifest=False)
    wrong = dict(original, original_filename='invented-publisher-title.pdf')
    path.write_text(json.dumps(wrong))
    with pytest.raises(ValueError, match='filename'):
        validate(audit_copy, check_manifest=False)


def test_symlinked_parent_directory_refused(audit_copy: Path, tmp_path: Path) -> None:
    """An unchanged leaf digest does not authorize traversal through a substituted parent."""
    raw = audit_copy / 'received/raw'
    moved = tmp_path / 'external-raw'
    raw.rename(moved)
    raw.symlink_to(moved, target_is_directory=True)
    with pytest.raises(ValueError, match='Nonordinary'):
        validate(audit_copy, check_manifest=False)


def test_false_delivered_by_cutoff_claim_refused(audit_copy: Path) -> None:
    """A late audit capture cannot assert an earlier delivery deadline was independently met."""
    path = audit_copy / 'AUDIT.json'
    data = json.loads(path.read_bytes())
    data['delivery_captured_at'] = '2026-09-13T02:25:00Z'
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match='report cutoff'):
        validate(audit_copy, check_manifest=False)
