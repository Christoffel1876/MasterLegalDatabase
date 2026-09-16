"""Adversarial integrity tests; these do not manufacture visual-review evidence."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import pytest
from models import Asset, Manifest, Review
from crop_tools import crop_bytes
import validate_qa as verifier

ROOT = Path(__file__).resolve().parent


@pytest.fixture()
def review() -> Review:
    """Load the actual reviewed record for isolated metadata mutation."""
    return Review.model_validate_json((ROOT / 'SOURCE_QA.json').read_bytes())


@pytest.fixture()
def copied(tmp_path: Path) -> Path:
    """Use a temporary packet; production/source files are never changed."""
    result = tmp_path / 'packet'
    shutil.copytree(ROOT, result, ignore=shutil.ignore_patterns('__pycache__', '.pytest_cache'))
    return result


def test_actual_review(review: Review) -> None:
    """All source, page, transcript, crop and custody bindings pass."""
    result = verifier.verify_review(ROOT, review)
    assert result['pages'] == 16
    assert result['design_entries'] == 27
    assert result['transcript_bytes'] == 27923


@pytest.mark.parametrize('change', ['value', 'label', 'parent', 'context', 'order', 'drop'])
def test_design_association_mutations(review: Review, change: str) -> None:
    """Reject changed values and misleading grouping even with unchanged transcript."""
    item = review.associations[5]
    if change == 'value':
        item.value = 'A for soil site class D'
    elif change == 'label':
        item.label = 'Wind Design Category'
    elif change == 'parent':
        item.parent_heading = 'Wind Design'
    elif change == 'context':
        item.context_block_ids = ['P01B01']
    elif change == 'order':
        item.id = 'DESIGN-99'
    else:
        review.associations.pop()
    with pytest.raises(ValueError):
        verifier.verify_review(ROOT, review)


@pytest.mark.parametrize('change', ['start', 'end', 'page', 'text', 'digest'])
def test_wrong_span(review: Review, change: str) -> None:
    """Reject byte offsets, content, page or digests that do not match."""
    selected = review.pages[3].blocks[2].span
    if change == 'start':
        selected.start += 1
    elif change == 'end':
        selected.end += 1
    elif change == 'page':
        selected.page = 5
    elif change == 'text':
        selected.text = selected.text.replace('120', '121') + 'x'
    else:
        selected.sha256 = '0' * 64
    with pytest.raises(ValueError):
        verifier.verify_review(ROOT, review)


@pytest.mark.parametrize('change', ['gap', 'tail', 'duplicate', 'box', 'continuation',
                                    'exception_continuation', 'note', 'strike'])
def test_context_and_markings(review: Review, change: str) -> None:
    """Preserve full-page coverage, both continuations and explicit struck wording."""
    if change == 'gap':
        review.pages[3].blocks.pop(1)
    elif change == 'tail':
        review.pages[3].blocks.pop()
    elif change == 'duplicate':
        review.pages[3].blocks[0].id = review.pages[0].blocks[0].id
    elif change == 'box':
        review.pages[0].blocks[0].pixel_box = [-1, 0, 1200, 1600]
    elif change == 'continuation':
        review.pages[7].blocks[0].continuation_of = None
    elif change == 'exception_continuation':
        review.pages[12].blocks[0].continuation_of = 'P01B01'
    elif change == 'note':
        review.pages[3].notes[0].exact_transcript = 'changed'
    else:
        review.markings.pop(0)
    with pytest.raises(ValueError):
        verifier.verify_review(ROOT, review)


@pytest.mark.parametrize('field,value', [
    ('source_currentness', 'current'), ('answer_safe', True),
    ('legal_adoption_verified', True), ('signature_identity_verified', True),
    ('external_reports_consulted', True), ('native_total_bytes', 1), ('page_count', 15),
    ('authority_id', 'CO-MUNICIPAL-GUNNISON')])
def test_promotion_or_wrong_scope_refused(field: str, value: object) -> None:
    """The typed review cannot be promoted or reassigned by changing a flag."""
    data = json.loads((ROOT / 'SOURCE_QA.json').read_bytes())
    data[field] = value
    with pytest.raises(ValueError):
        Review.model_validate(data)


@pytest.mark.parametrize('path', ['../original.pdf', '/tmp/original.pdf',
                                  './original.pdf', 'a//b', 'a\\b'])
def test_unsafe_path(path: str) -> None:
    """Reject noncanonical paths before access."""
    with pytest.raises(ValueError):
        verifier.local(ROOT, path)


def test_symlink(copied: Path) -> None:
    """Reject an apparently matching file accessed through a symlink."""
    target = copied / 'alias.pdf'
    target.symlink_to(copied / 'original.pdf')
    with pytest.raises(ValueError):
        verifier.local(copied, 'alias.pdf')


def test_source_rebound_to_changed_bytes(copied: Path, review: Review) -> None:
    """Even a freshly recalculated asset digest cannot substitute another PDF."""
    path = copied / 'original.pdf'
    raw = path.read_bytes() + b'\nchanged'
    path.write_bytes(raw)
    review.source.sha256 = hashlib.sha256(raw).hexdigest()
    review.source.size_bytes = len(raw)
    with pytest.raises(ValueError, match='Wrong fixed source'):
        verifier.verify_review(copied, review)


def test_native_cannot_be_filled(copied: Path, review: Review) -> None:
    """OCR may not be relabeled as native text."""
    p = review.pages[0]
    path = copied / p.native.path
    path.write_bytes(b'Invented native text')
    p.native.sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
    p.native.size_bytes = path.stat().st_size
    with pytest.raises(ValueError, match='empty native'):
        verifier.verify_review(copied, review)


def test_receipt_clock(copied: Path, review: Review) -> None:
    """A coherent asset rehash does not turn intake time into acquisition time."""
    path = copied / review.custody.receipt.path
    data = json.loads(path.read_bytes())
    data['actual_repository_received_at'] = '2023-11-07T00:00:00Z'
    raw = json.dumps(data).encode()
    path.write_bytes(raw)
    review.custody.receipt.sha256 = hashlib.sha256(raw).hexdigest()
    review.custody.receipt.size_bytes = len(raw)
    with pytest.raises(ValueError, match='receipt custody'):
        verifier.verify_review(copied, review)


def test_wrong_manifest_line(review: Review) -> None:
    """Nearby county rows cannot substitute for the selected source."""
    review.custody.record_line = 65
    with pytest.raises(ValueError, match='manifest line'):
        verifier.verify_review(ROOT, review)


def test_candidate_rebound(copied: Path, review: Review) -> None:
    """A changed OCR text asset must still derive exactly from raw engine output."""
    p = review.pages[0]
    raw = (copied / p.ocr_text.path).read_bytes().replace(b'2021', b'2022')
    (copied / p.ocr_text.path).write_bytes(raw)
    p.ocr_text.sha256 = hashlib.sha256(raw).hexdigest()
    p.ocr_text.size_bytes = len(raw)
    with pytest.raises(ValueError, match='OCR candidate'):
        verifier.verify_review(copied, review)


def test_wrong_crop_bounds(copied: Path, review: Review) -> None:
    """A tighter crop cannot silently masquerade as the retained full region."""
    path = copied / 'CROPS.json'
    data = json.loads(path.read_bytes())
    data['crops'][0]['box'][0] += 1
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match='Crop pixels'):
        verifier.verify_review(copied, review)


@pytest.mark.parametrize('box', [[-1, 0, 10, 10], [0, 0, 0, 10], [0, 0, 9999, 9999]])
def test_crop_bounds(box: list[int]) -> None:
    """Reject empty or out-of-page crops."""
    with pytest.raises(ValueError):
        crop_bytes(ROOT / 'pages/page-01.png', box)


def test_seal_extra_file(copied: Path) -> None:
    """Closed packages cannot gain a payload unnoticed."""
    (copied / 'extra.txt').write_text('unlisted')
    with pytest.raises(ValueError, match='payload set'):
        verifier.verify_manifest(copied)


def test_seal_changed_file(copied: Path) -> None:
    """An unchanged filename does not excuse changed bytes."""
    with (copied / 'original.pdf').open('ab') as stream:
        stream.write(b'x')
    with pytest.raises(ValueError, match='Asset mismatch'):
        verifier.verify_manifest(copied)


def test_wrong_pages() -> None:
    """All pages are mandatory and ordered."""
    data = json.loads((ROOT / 'SOURCE_QA.json').read_bytes())
    data['pages'][0], data['pages'][1] = data['pages'][1], data['pages'][0]
    with pytest.raises(ValueError):
        Review.model_validate(data)


def reseal(root: Path) -> None:
    """Seal a temporary mutated fixture to test checks beyond basic file hashes."""
    files = []
    for p in sorted(root.rglob('*')):
        if p.is_file() and p.name != 'FINAL_MANIFEST.json':
            raw = p.read_bytes()
            files.append(Asset(path=p.relative_to(root).as_posix(),
                               sha256=hashlib.sha256(raw).hexdigest(), size_bytes=len(raw)))
    manifest = Manifest(schema_version='1.0',
                        status='source_review_only_currentness_not_verified', files=files)
    (root / 'FINAL_MANIFEST.json').write_text(manifest.model_dump_json())


def test_complete_closed_validation() -> None:
    """Exercise the actual closed schema/inventory/semantic path."""
    result = verifier.validate(ROOT)
    assert result['pages'] == 16
    assert result['machine_lines'] == 521


def test_frozen_qa_pin_survives_reseal(copied: Path) -> None:
    """Resealing a changed fee cannot manufacture a new source-reviewed decision."""
    path = copied / 'SOURCE_QA.json'
    data = json.loads(path.read_bytes())
    data['pages'][5]['notes'][0]['statement'] = 'The fee has been corrected to $75.00.'
    path.write_text(json.dumps(data))
    reseal(copied)
    with pytest.raises(ValueError, match='Frozen reviewed record'):
        verifier.validate(copied)


def test_changed_schema_rejected(copied: Path) -> None:
    """A permissive supplied JSON schema cannot weaken the typed model."""
    path = copied / 'SOURCE_QA.schema.json'
    path.write_text('{}')
    reseal(copied)
    with pytest.raises(ValueError, match='Exported schema'):
        verifier.validate(copied)


def test_duplicate_manifest(copied: Path) -> None:
    """Duplicate payload declarations must not hide omission."""
    path = copied / 'FINAL_MANIFEST.json'
    data = json.loads(path.read_bytes())
    data['files'].append(data['files'][0])
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match='Duplicate'):
        verifier.verify_manifest(copied)


def test_manifest_symlink_directory(copied: Path) -> None:
    """The closed walker must reject symlinked directories even without followed files."""
    (copied / 'linked').symlink_to(copied / 'native', target_is_directory=True)
    with pytest.raises(ValueError, match='Symlink directory'):
        verifier.verify_manifest(copied)


def test_missing_ordinary_file(tmp_path: Path) -> None:
    """Missing paths cannot pass ordinary-file validation."""
    with pytest.raises(ValueError, match='Ordinary file'):
        verifier.ordinary(tmp_path / 'missing')


def test_streamed_manifest_hash(copied: Path, review: Review) -> None:
    """A changed JSONL preimage is detected by streaming byte verification."""
    path = copied / review.custody.manifest.path
    with path.open('ab') as stream:
        stream.write(b'{}\n')
    with pytest.raises(ValueError, match='Streamed asset'):
        verifier.verify_review(copied, review)


def test_duplicate_note_ids() -> None:
    """No source annotation can silently alias another."""
    data = json.loads((ROOT / 'SOURCE_QA.json').read_bytes())
    data['pages'][1]['notes'][0]['id'] = data['pages'][0]['notes'][0]['id']
    with pytest.raises(ValueError, match='Duplicate note'):
        Review.model_validate(data)


def test_real_full_page_rerender(review: Review) -> None:
    """Reproduce all sixteen full source images from the exact original PDF."""
    binary = ('/Users/mcoors/.cache/codex-runtimes/codex-primary-runtime/'
              'dependencies/bin/override/pdftoppm')
    verifier.rerender(ROOT, review, binary)


def test_rerender_failure(review: Review, monkeypatch: pytest.MonkeyPatch) -> None:
    """A failed renderer cannot be reported as verified."""
    monkeypatch.setattr(verifier.subprocess, 'run',
                        lambda *a, **k: subprocess.CompletedProcess(a, 1))
    with pytest.raises(ValueError, match='rerender failed'):
        verifier.rerender(ROOT, review, '/non-executed/test-renderer')


def test_rerender_wrong_pixels(review: Review, monkeypatch: pytest.MonkeyPatch) -> None:
    """A successful renderer producing the wrong complete image fails verification."""
    def fake(command: list[str], **kwargs: object) -> subprocess.CompletedProcess:
        prefix = Path(command[-1])
        (prefix.parent / 'page-01.png').write_bytes(b'wrong image')
        return subprocess.CompletedProcess(command, 0)
    monkeypatch.setattr(verifier.subprocess, 'run', fake)
    with pytest.raises(ValueError, match='render mismatch'):
        verifier.rerender(ROOT, review, '/non-executed/test-renderer')


def test_cli_actual(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture) -> None:
    """Exercise the ordinary CLI against the actual packet."""
    monkeypatch.setattr(sys, 'argv', ['validate_qa.py', '--root', str(ROOT)])
    verifier.main()
    assert json.loads(capsys.readouterr().out)['status'] == 'pass'


def test_cli_missing_renderer(monkeypatch: pytest.MonkeyPatch) -> None:
    """Optional render proof requires a known executable, with no install fallback."""
    monkeypatch.setattr(sys, 'argv', ['validate_qa.py', '--rerender'])
    monkeypatch.setattr(verifier.shutil, 'which', lambda _: None)
    with pytest.raises(SystemExit):
        verifier.main()


def test_failed_attempt_mapping(copied: Path) -> None:
    """The retained historical failure cannot silently point at the successful retry."""
    path = copied / 'DERIVATION.json'
    data = json.loads(path.read_bytes())
    data['initial_failed_attempt']['retained_stdout'] = data['successful_attempts'][0][
        'retained_stdout']
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match='remapping'):
        verifier.verify_derivation(copied)


def test_failed_attempt_relocation_disclosure(copied: Path) -> None:
    """Relocated historical receipt paths must stay explicitly distinguished."""
    path = copied / 'DERIVATION.json'
    data = json.loads(path.read_bytes())
    data['initial_failed_attempt']['original_paths_relocated'] = False
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match='relocation'):
        verifier.verify_derivation(copied)


def test_derivation_complete_pages(copied: Path) -> None:
    """A partial collection cannot claim all sixteen successful OCR pages."""
    path = copied / 'DERIVATION.json'
    data = json.loads(path.read_bytes())
    data['successful_attempts'].pop()
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match='complete page set'):
        verifier.verify_derivation(copied)
