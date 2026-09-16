"""Offline preservation and evidence-tamper regressions."""
import json
import shutil
from pathlib import Path
import pytest
from validate_audit import verify, ordinary

HERE = Path(__file__).parent

@pytest.fixture
def package(tmp_path):
    root = tmp_path / 'portable'
    shutil.copytree(HERE, root)
    return root


def test_original_package():
    result = verify(HERE)
    assert result['actions'] == 30
    assert result['legacy_rows_per_snapshot'] == 48390
    assert result['visually_reviewed_pages'] == 3


@pytest.mark.parametrize('name', [
    'received/raw/SHEXT003-A026.pdf',
    'received/results/SHEXT003-A030.json',
    'received/headers/SHEXT003-A025.json',
    'CHAFFEE_REPAIR_PROPOSAL.json',
    'comparison/full-legacy.jsonl',
    'visual/A027-page1.png',
])
def test_mutated_evidence_rejected(package, name):
    path = package / name
    with path.open('ab') as handle:
        handle.write(b'changed')
    with pytest.raises(ValueError, match='bytes differ'):
        verify(package)


def test_extra_file_rejected(package):
    (package / 'unlisted').write_bytes(b'x')
    with pytest.raises(ValueError, match='membership differs'):
        verify(package)


def test_missing_body_rejected(package):
    (package / 'received/raw/SHEXT003-A026.pdf').unlink()
    with pytest.raises(ValueError, match='membership differs'):
        verify(package)


def test_symlink_rejected(package):
    (package / 'linked').symlink_to(package / 'AUDIT.json')
    with pytest.raises(ValueError, match='Nonordinary'):
        verify(package)


@pytest.mark.parametrize('name', ['../outside', '/etc/passwd'])
def test_external_reference_rejected(package, name):
    with pytest.raises(ValueError, match='Unsafe'):
        ordinary(package, name)
