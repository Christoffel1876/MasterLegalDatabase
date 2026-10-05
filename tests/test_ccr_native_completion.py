"""Boundary tests for exact native completions and committed Transportation text."""
from pathlib import Path
import sys
from types import SimpleNamespace
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from verify_ccr_native_completion import (
    Asset, common, exact_ledger, exact_union, transportation, working_directory,
)


def original(digest: str = 'a' * 64, text: str = 'b' * 64) -> dict:
    """One small complete original/page identity."""
    return {digest: common.Original(sha256=digest, pages=[common.Page(
        physical_page=1, text_sha256=text, text_bytes=2)])}


@pytest.mark.parametrize('changed', [dict(), original('c' * 64), original(text='d' * 64)])
def test_exact_rebuilt_ledger_rejects_substitution(changed: dict) -> None:
    with pytest.raises(ValueError, match='ledger differs'):
        exact_ledger(original(), changed)


def test_identical_native_ledger() -> None:
    exact_ledger(original(), original())


def test_working_directory_restored_on_error(tmp_path: Path) -> None:
    before = Path.cwd()
    with pytest.raises(RuntimeError):
        with working_directory(tmp_path):
            assert Path.cwd() == tmp_path
            raise RuntimeError('bounded failure')
    assert Path.cwd() == before


def test_duplicate_native_ledger_chain_rejected() -> None:
    refs = [Asset(path=f'{n}.jsonl', sha256=str(n) * 64, bytes=2) for n in range(7)]
    previous = SimpleNamespace(prior_page_sets=refs[:3], new_page_set=refs[3])
    index = SimpleNamespace(ledgers=refs[:6] + [refs[5]],
                            packages=[SimpleNamespace(ledger=r) for r in refs[4:]])
    with pytest.raises(ValueError, match='chain differs'):
        exact_union(index, previous, [original()] * 7)


def test_overlapping_originals_rejected() -> None:
    refs = [Asset(path=f'{n}.jsonl', sha256=str(n) * 64, bytes=2) for n in range(7)]
    previous = SimpleNamespace(prior_page_sets=refs[:3], new_page_set=refs[3])
    index = SimpleNamespace(ledgers=refs,
                            packages=[SimpleNamespace(ledger=r) for r in refs[4:]])
    with pytest.raises(ValueError, match='overlapping'):
        exact_union(index, previous, [original()] * 7)


def test_changed_committed_transportation_text_rejected(tmp_path: Path) -> None:
    import pymupdf
    pdf = pymupdf.open()
    for number in range(10):
        pdf.new_page().insert_text((30, 40), f'Page {number + 1}')
    raw = pdf.tobytes()
    pdf.close()
    (tmp_path / 'source.pdf').write_bytes(raw)
    digest = common.sha(raw)
    folder = tmp_path / 'docs/audits/CCR_NATIVE_COMPLETION_2026-10-05/transportation-native'
    folder.mkdir(parents=True)
    pages = []
    with pymupdf.open(stream=raw, filetype='pdf') as doc:
        for number, page in enumerate(doc, 1):
            text = page.get_text('text', sort=False).encode()
            (folder / f'{number:04d}.txt').write_bytes(text)
            pages.append(common.Page(physical_page=number, text_sha256=common.sha(text),
                                     text_bytes=len(text)))
    expected = {digest: common.Original(sha256=digest, pages=pages)}
    index = SimpleNamespace(transportation_pdf=Asset(path='source.pdf', sha256=digest,
                                                    bytes=len(raw)))
    transportation(tmp_path, index, common.Reader(tmp_path), expected)
    before = (folder / '0001.txt').read_bytes()
    (folder / '0001.txt').write_bytes(b'X' * len(before))
    with pytest.raises(ValueError, match='hash differs'):
        transportation(tmp_path, index, common.Reader(tmp_path), expected)


def test_reference_escape_and_symlink(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match='Unsafe'):
        common.Reader(tmp_path).read(Asset(path='../source', sha256='0' * 64, bytes=0))
    (tmp_path / 'source').write_bytes(b'x')
    (tmp_path / 'alias').symlink_to(tmp_path / 'source')
    with pytest.raises(ValueError, match='Symlink'):
        common.Reader(tmp_path).read(Asset(path='alias', sha256=common.sha(b'x'), bytes=1))


def test_department_page_aliases_do_not_double_count(tmp_path: Path) -> None:
    from geode.pipeline.ccr_source_text import Asset as NativeAsset, Page
    from verify_ccr_native_completion import rebuilt_ledger
    text = NativeAsset(path='native/' + 'a' * 64 + '/00001.txt',
                       sha256='b' * 64, size_bytes=2)
    page = Page(document_id='c' * 64, physical_page=1, original_sha256='a' * 64,
                text=text, native_empty=False)
    alias = page.model_copy(update={'document_id': 'd' * 64})
    (tmp_path / 'pages.jsonl').write_text(page.model_dump_json() + '\n' +
                                       alias.model_dump_json() + '\n')
    assert rebuilt_ledger(tmp_path) == original()
    changed = alias.model_copy(update={'text': text.model_copy(update={'sha256': 'e' * 64})})
    (tmp_path / 'pages.jsonl').write_text(page.model_dump_json() + '\n' +
                                       changed.model_dump_json() + '\n')
    with pytest.raises(ValueError, match='Conflicting duplicate'):
        rebuilt_ledger(tmp_path)
