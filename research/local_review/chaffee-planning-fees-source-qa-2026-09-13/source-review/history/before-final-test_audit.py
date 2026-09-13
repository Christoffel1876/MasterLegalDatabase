"""Source-based adversarial checks, including repeated fee values and note scopes."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import pytest
import validate_audit as v
from audit_models import Asset, Inventory

ROOT = Path(__file__).resolve().parent


@pytest.fixture()
def qa() -> v.Review:
    """Load the unchanged Atlas source record for isolated mutation."""
    return v.Review.model_validate_json((ROOT / 'received/SOURCE_QA.json').read_bytes())


@pytest.fixture()
def copy(tmp_path: Path) -> Path:
    """Create a disposable packet; never modify source or production files."""
    path = tmp_path / 'packet'
    shutil.copytree(ROOT, path, ignore=shutil.ignore_patterns('__pycache__', '.pytest_cache'))
    return path


def test_complete_actual_qa(qa: v.Review) -> None:
    """All rows, geometry, notes, source bytes and eight crops validate."""
    assert v.verify_qa(ROOT / 'received', qa)['rows'] == 49


@pytest.mark.parametrize('pair', [(2, 4), (5, 6), (7, 8), (21, 22), (28, 30)])
def test_repeated_fee_cannot_be_swapped(qa: v.Review, pair: tuple[int, int]) -> None:
    """Equal monetary strings must stay beside their own physical application row."""
    first, second = pair
    assert qa.rows[first].fee == qa.rows[second].fee
    qa.rows[first].fee_native, qa.rows[second].fee_native = (
        qa.rows[second].fee_native, qa.rows[first].fee_native)
    with pytest.raises(ValueError, match='another source row'):
        v.verify_qa(ROOT / 'received', qa)


@pytest.mark.parametrize('change', ['amount', 'label', 'page', 'group', 'span', 'hash',
                                    'missing_note', 'broad_note', 'missing_row'])
def test_row_mutations(qa: v.Review, change: str) -> None:
    """Wrong amounts, missing context and page/section reassignment are refused."""
    row = qa.rows[0]
    if change == 'amount':
        row.fee = '$321'
    elif change == 'label':
        row.application = 'All zoning permits'
    elif change == 'page':
        row.page = 2
    elif change == 'group':
        row.group_id = 'G02'
    elif change == 'span':
        row.application_native[0].start += 1
    elif change == 'hash':
        row.application_native[0].sha256 = '0' * 64
    elif change == 'missing_note':
        row.related_note_ids = []
    elif change == 'broad_note':
        row.related_note_ids.append('N01')
    else:
        qa.rows.pop()
    with pytest.raises(ValueError):
        v.verify_qa(ROOT / 'received', qa)


@pytest.mark.parametrize('identity', ['N01', 'N02', 'H01', 'N03'])
def test_note_scope(qa: v.Review, identity: str) -> None:
    """No marked or global fee qualification may disappear or spread to other rows."""
    passage = next(p for p in qa.passages if p.id == identity)
    passage.applies_to_rows = ['R01']
    with pytest.raises(ValueError, match='source scope'):
        v.verify_qa(ROOT / 'received', qa)


def test_entire_hourly_condition(qa: v.Review) -> None:
    """Do not expose hourly rates without discretionary and GIS conditions."""
    passage = next(p for p in qa.passages if p.id == 'H01')
    passage.text = 'All applications are billed hourly.'
    with pytest.raises(ValueError, match='full source wording'):
        v.verify_qa(ROOT / 'received', qa)


def test_escrow_tail_cannot_be_dropped(qa: v.Review) -> None:
    """The additional-fee and individual-application clauses remain included."""
    passage = next(p for p in qa.passages if p.id == 'N03')
    passage.native.pop()
    passage.text = v.normalize(''.join(s.text for s in passage.native))
    with pytest.raises(ValueError, match='association mismatch'):
        v.verify_qa(ROOT / 'received', qa)


@pytest.mark.parametrize('change', ['continuation', 'parent', 'members', 'heading'])
def test_category_structure(qa: v.Review, change: str) -> None:
    """Preserve the page break within subdivision exemptions and all headings."""
    group = qa.groups[4]
    if change == 'continuation':
        group.heading_on_page2 = True
    elif change == 'parent':
        group.parent_heading = 'LAND USE/DEVELOPMENT APPLICATIONS'
    elif change == 'members':
        group.row_ids.pop()
    else:
        group.heading = 'SUBDIVISIONS'
    with pytest.raises(ValueError):
        v.verify_qa(ROOT / 'received', qa)


@pytest.mark.parametrize('field,value', [('legal_currentness', 'verified'),
                                       ('answer_safe', True),
                                       ('verified_effective_date', '2025-01-01'),
                                       ('authority_id', 'CO-MUNICIPAL-SALIDA')])
def test_no_status_or_ownership_promotion(field: str, value: object) -> None:
    """Source-printed dates and county ownership cannot be relabeled."""
    data = json.loads((ROOT / 'received/SOURCE_QA.json').read_bytes())
    data[field] = value
    with pytest.raises(ValueError):
        v.Review.model_validate(data)


def test_native_tail(qa: v.Review) -> None:
    """All native bytes, including reordered footer lines, remain bound."""
    qa.native_lines.pop()
    with pytest.raises(ValueError, match='tail omitted'):
        v.verify_qa(ROOT / 'received', qa)


def test_missing_source(copy: Path, qa: v.Review) -> None:
    """The actual source file is mandatory."""
    (copy / 'received/source/original.pdf').unlink()
    with pytest.raises(ValueError):
        v.verify_qa(copy / 'received', qa)


@pytest.mark.parametrize('name', ['../source.pdf', '/tmp/source.pdf', './source.pdf',
                                  'a//b', 'a\\b'])
def test_unsafe_paths(name: str) -> None:
    """Reject traversal, absolute and ambiguous path spellings before reading."""
    with pytest.raises(ValueError, match='Unsafe path'):
        v.safe(ROOT, name)


def test_symlink(copy: Path) -> None:
    """Exact bytes behind a symlink do not satisfy ordinary-file custody."""
    (copy / 'alias').symlink_to(copy / 'received/source/original.pdf')
    with pytest.raises(ValueError, match='Nonordinary'):
        v.safe(copy, 'alias')


def test_real_custody() -> None:
    """Replay exact retained catalog/base, prior302 and successful200 joins."""
    v.verify_custody(ROOT)


def test_crop_bounds(copy: Path, qa: v.Review) -> None:
    """A partial crop cannot replace the declared full table context."""
    path = copy / 'received/CROPS.json'
    data = json.loads(path.read_bytes())
    data[0]['rect'][0] += 1
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match='Crop does not reproduce'):
        v.verify_qa(copy / 'received', qa)


def test_actual_closed_package() -> None:
    """The standalone closed validator reads no original-workspace inputs."""
    assert v.validate(ROOT)['native_bytes'] == 3769


def test_actual_rerender() -> None:
    """Both full Poppler pages reproduce from the exact retained PDF."""
    binary = ('/Users/mcoors/.cache/codex-runtimes/codex-primary-runtime/'
              'dependencies/bin/override/pdftoppm')
    assert v.validate(ROOT, binary)['pages'] == 2


def test_closed_extra_payload(copy: Path) -> None:
    """Unlisted payloads cannot silently enter the reviewed packet."""
    (copy / 'extra').write_text('unlisted')
    with pytest.raises(ValueError, match='Closed inventory'):
        v.validate(copy)


def test_cli(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture) -> None:
    """Ordinary CLI verifies the actual two-page source package."""
    monkeypatch.setattr(sys, 'argv', ['validate_audit.py', '--root', str(ROOT)])
    v.main()
    assert json.loads(capsys.readouterr().out)['status'] == 'pass'
