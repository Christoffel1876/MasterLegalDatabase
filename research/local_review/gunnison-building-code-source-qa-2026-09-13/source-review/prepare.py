"""Preserve exact local source and render full pages without changing the source."""
from pathlib import Path
import hashlib
import json
import subprocess
from datetime import datetime, timezone
import pymupdf
from models import Asset, Custody, ProcessReceipt

ROOT = Path(__file__).resolve().parent
REPO = Path('/Users/mcoors/Documents/Project Geode/MasterLegalDatabase')


def write(path: Path, data: bytes) -> None:
    """Write a new asset, or require a byte-identical existing asset."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        assert path.read_bytes() == data
        return
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_bytes(data)
    temporary.replace(path)


def asset(path: Path) -> Asset:
    """Hash one ordinary local asset."""
    data = path.read_bytes()
    return Asset(path=path.relative_to(ROOT).as_posix(),
                 sha256=hashlib.sha256(data).hexdigest(), size_bytes=len(data))


def main() -> None:
    """Preserve already captured custody and create derived renderings."""
    with (ROOT / 'custody/exact-record.jsonl').open('rb') as stream:
        record = json.loads(next(stream))
    write(ROOT / 'original.pdf', (REPO / record['archive_path']).read_bytes())
    intake = REPO / 'research/local_review/gunnison-county-intake-2026-09-13'
    intake /= 'prepared-transaction'
    for name, out in [('PREPARATION.json', 'preparation.json'),
                      ('execution/RECEIPT.json', 'intake-receipt.json')]:
        write(ROOT / 'custody' / out, (intake / name).read_bytes())
    custody = Custody(
        source_id=record['record_id'], authority_id='CO-COUNTY-GUNNISON',
        layer_id='08_County_Authorities', acquisition_method='received_review_package',
        official_source_url=None, original_http_acquisition_verified=False,
        received_at=record['received_at'], record_line=66,
        manifest=asset(ROOT / 'custody/manual_source_intake_manifest.jsonl'),
        exact_record=asset(ROOT / 'custody/exact-record.jsonl'),
        preparation=asset(ROOT / 'custody/preparation.json'),
        receipt=asset(ROOT / 'custody/intake-receipt.json'),
        supplied_url='https://gunnisoncounty.org/DocumentCenter/View/13880/'
        'Resolution-2023-22-2021-Code-Adoption-and-Further-Amendments-to-IWUI-Code',
        limits=['Original HTTP URL/status/times are supplied Sherlock claims, '
                'not independently witnessed acquisition.',
                'Repository received_at is intake time only.',
                'Source preservation does not authenticate signatures, adoption, '
                'effective status or legal currentness.'])
    write(ROOT / 'CUSTODY.json', (custody.model_dump_json(indent=2) + '\n').encode())
    document = pymupdf.open(ROOT / 'original.pdf')
    assert len(document) == 16
    for number, page in enumerate(document, 1):
        text = page.get_text('text', flags=195, sort=False).encode()
        assert not text
        write(ROOT / f'native/page-{number:04}.txt', text)
    old = ROOT.parent / 'plato-gunnison-fees-source-qa/tools'
    for name in ['apple-vision-ocr', 'apple_vision_ocr.swift']:
        write(ROOT / 'tools' / name, (old / name).read_bytes())
    (ROOT / 'tools/apple-vision-ocr').chmod(0o755)
    (ROOT / 'pages').mkdir(exist_ok=True)
    command = ['/Users/mcoors/.cache/codex-runtimes/codex-primary-runtime/'
               'dependencies/bin/override/pdftoppm', '-r', '150', '-png',
               str(ROOT / 'original.pdf'), str(ROOT / 'pages/page')]
    started = datetime.now(timezone.utc).isoformat()
    result = subprocess.run(command, capture_output=True)
    completed = datetime.now(timezone.utc).isoformat()
    write(ROOT / 'render.stdout', result.stdout)
    write(ROOT / 'render.stderr', result.stderr)
    receipt = ProcessReceipt(started_at=started, completed_at=completed,
                             command=command, returncode=result.returncode,
                             stdout=asset(ROOT / 'render.stdout'),
                             stderr=asset(ROOT / 'render.stderr'))
    write(ROOT / 'RENDER.json', (receipt.model_dump_json(indent=2) + '\n').encode())
    assert result.returncode == 0


if __name__ == '__main__':
    main()
