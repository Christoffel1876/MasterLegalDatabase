"""Small offline fixture checks; no Git repository or staged tree is exported."""
import io
from pathlib import Path
from unittest.mock import patch

import pytest

from models import Digest, IndexEntry, Scan, ScanAsset
from verify_staged_export import Runner, USER_PATHS, compare_scan, digest, parse_index, safe_path

OID = 'a'*40


def listing(path: str = 'approved.txt', mode: str = '100644', stage: str = '0') -> bytes:
    """Build one synthetic index-metadata row."""
    return f'{mode} {OID} {stage}\t{path}\0'.encode()


def scan() -> Scan:
    """Build a strict synthetic selected-file scan."""
    return Scan(status='prepared_exact_paths_not_staged', recorded_at='2026-09-13T00:00:00Z',
                head='b'*40, wrappers=0, new_raw_originals=6,
                files=[ScanAsset(path='approved.txt', **digest(b'ok').model_dump(),
                                 tracked=False, ignored=False, basis=['fixture'])],
                excluded_user_paths=sorted(USER_PATHS), qualifications=['Synthetic fixture'])


def test_index_normal_and_selected_scope() -> None:
    """Accept only the exact selected staged change."""
    entries = parse_index(listing())
    compare_scan(scan(), entries, b'approved.txt\0')
    assert entries['approved.txt'].oid == OID


@pytest.mark.parametrize('row', [listing(stage='2'), listing(mode='120000'),
                                listing()+listing(), listing()+listing('APPROVED.txt'),
                                listing('../escape'), listing().rstrip(b'\0')])
def test_unsafe_index_rows_rejected(row: bytes) -> None:
    """Reject unmerged entries, symlinks, aliases, traversal and framing defects."""
    with pytest.raises(ValueError):
        parse_index(row)


@pytest.mark.parametrize('path', sorted(USER_PATHS)+[p.upper() for p in USER_PATHS])
def test_user_files_refused(path: str) -> None:
    """Neither excluded user file may exist in the staged index."""
    with pytest.raises(ValueError, match='Excluded user'):
        parse_index(listing(path))


def test_unreviewed_staged_change_and_missing_scan_rejected() -> None:
    """Refuse both extra staged modifications and missing selected content."""
    with pytest.raises(ValueError, match='outside'):
        compare_scan(scan(), parse_index(listing()), b'other.txt\0')
    with pytest.raises(ValueError, match='absent'):
        compare_scan(scan(), parse_index(listing('other.txt')), b'')


@pytest.mark.parametrize('path', ['/outside', './file', 'a//b', '.git/config', 'a\\b'])
def test_path_aliases_rejected(path: str) -> None:
    """Do not normalize ambiguous export paths into accepted members."""
    with pytest.raises(ValueError):
        safe_path(path)


class FakeProcess:
    """An in-memory Git batch stream; never starts a subprocess."""

    def __init__(self, raw: bytes) -> None:
        """Supply exact simulated pipe bytes."""
        self.stdin = io.BytesIO()
        self.stdout = io.BytesIO(raw)
        self.stderr = io.BytesIO()
        self.returncode = 0

    def wait(self, timeout: int = 0) -> int:
        """Return a deterministic fixture exit code."""
        return self.returncode

    def kill(self) -> None:
        """Record fixture termination without touching a real process."""
        self.returncode = -9


@pytest.mark.parametrize('body,expected,success', [(b'ok', digest(b'ok'), True),
                                                  (b'bad', digest(b'ok'), False)])
def test_batch_bytes_match_expected_before_export(tmp_path: Path, body: bytes,
                                                expected: Digest, success: bool) -> None:
    """Hash the consumed bytes; reject changed data with no export requested."""
    raw = f'{OID} blob {len(body)}\n'.encode()+body+b'\n'
    runner = Runner(tmp_path, tmp_path)
    entry = IndexEntry(path='approved.txt', mode='100644', oid=OID)
    with patch('verify_staged_export.subprocess.Popen', return_value=FakeProcess(raw)):
        if success:
            assets = runner.blobs([entry], None, {'approved.txt': expected})
            assert assets[0].sha256 == expected.sha256
        else:
            with pytest.raises(ValueError, match='differs'):
                runner.blobs([entry], None, {'approved.txt': expected})
    assert not (tmp_path/'approved.txt').exists()
    assert runner.commands[0].stdout_file is None


def test_batch_truncation_retained_as_failure(tmp_path: Path) -> None:
    """Reject partial blobs while preserving the typed command outcome."""
    runner = Runner(tmp_path, tmp_path)
    entry = IndexEntry(path='approved.txt', mode='100644', oid=OID)
    with patch('verify_staged_export.subprocess.Popen',
               return_value=FakeProcess(f'{OID} blob 10\na'.encode())):
        with pytest.raises(ValueError, match='Truncated'):
            runner.blobs([entry], None)
    assert runner.commands[0].exit_code == -9
