"""Read-only portable hash, byte, geometry, association and crop verifier."""
import argparse
import io
import json
import sys
from pathlib import Path, PurePosixPath
import jsonschema
import pymupdf
from build_review import CANDIDATE, SOURCE, derive, digest
from crop_recipes import RECIPES
from review_models import QA, Seal

PACKET_MANIFEST = 'd189522f93ec1bcdb6bb87d08723da698871cd5e3e1391a54f976d518199896d'
SOURCE_HASH = '555570a62a5a557a824d1bcf3ecd2e60d57e48d19ea401f06a2e5b7ccb177e56'
CANDIDATE_HASH = '2874494d69b8b9a5abf11d915668c3ca63c9f2a06301bb15c0721717c93459c0'
ROOT = Path(__file__).resolve().parent


def safe_read(base: Path, name: str) -> bytes:
    """Reject path escapes, symlinks, missing files and oversized artifacts."""
    posix = PurePosixPath(name)
    assert not posix.is_absolute() and '..' not in posix.parts
    path = base / posix
    for node in [path, *path.parents]:
        assert not node.is_symlink(), node
    assert path.is_file() and path.stat().st_size <= 6_000_000
    return path.read_bytes()


def captured_inputs(qa: QA) -> dict[str, bytes]:
    """Capture the exact validated subset, without importing upstream code."""
    base = ROOT/'inputs'
    buffers = {}
    for a in qa.assets:
        assert a.path not in buffers
        raw = safe_read(base,a.path)
        assert len(raw)==a.size_bytes and digest(raw)==a.sha256, a.path
        buffers[a.path]=raw
    actual = {p.relative_to(base).as_posix() for p in base.rglob('*') if p.is_file()}
    assert actual==set(buffers)
    assert digest(buffers['MANIFEST.json'])==PACKET_MANIFEST
    manifest = json.loads(buffers['MANIFEST.json'])
    upstream = {a['path']:a for a in manifest['files']}
    for a in qa.assets:
        if a.path not in ['MANIFEST.json','MANIFEST.schema.json']:
            assert a.model_dump()==upstream[a.path]
    assert digest(buffers[SOURCE])==SOURCE_HASH==qa.source_sha256
    assert digest(buffers[CANDIDATE])==CANDIDATE_HASH==qa.candidate_sha256
    return buffers


def validate_content(qa: QA, buffers: dict[str, bytes]) -> None:
    """Reject altered source associations, visibility, context and offsets."""
    lines, rows, paragraphs = derive(buffers)
    assert qa.lines==lines, 'Native line/offset/geometry/visibility mismatch'
    assert qa.rows==rows, 'Reviewed fee/column/group/context association mismatch'
    assert qa.paragraphs==paragraphs, 'Definition/context association mismatch'
    assert len(lines)==670 and len(rows)==197 and len(paragraphs)==25
    assert qa.full_pages_inspected==list(range(1,8))
    assert sum(l.end-l.start for l in lines)==18343
    assert len([l for l in lines if l.visibility!='visible'])==11
    by={l.id:l for l in lines}
    for row in rows:
        for cell in row.fee_refs:
            assert all(by[key].visibility=='visible' for key in cell)
    prep=json.loads(buffers['04-verification/PREPARATION.json'])
    records=[]
    for line in io.BytesIO(buffers['03-custody/canonical-record.jsonl']):
        records.append(json.loads(line))
    assert len(records)==1
    original_line=None
    for number,line in enumerate(io.BytesIO(buffers['03-custody/raw-manifest.snapshot.jsonl']),1):
        if number==prep['canonical_line_number']: original_line=line
    assert original_line==buffers['03-custody/canonical-record.jsonl']
    # The complete typed raw line is preserved; source identity appears in its exact bytes.
    assert qa.source_id.encode() in original_line and SOURCE_HASH.encode() in original_line
    result=json.loads(buffers['03-custody/result.json'])
    receipt=json.loads(buffers['03-custody/RECEIPT.json'])
    assert result['body']['sha256']==SOURCE_HASH and result['body']['size_bytes']==162682
    assert result['http_status']==200 and result['partial_body'] is False
    assert result['reservation_sha256']==digest(buffers['03-custody/reservation.json'])
    assert result['public_headers']['sha256']==digest(buffers['03-custody/public-headers.json'])
    assert result['finished_at']==prep['original_http_completed_at']
    assert receipt['intent_sha256']==digest(buffers['03-custody/INTENT.json'])
    matching=[r for r in receipt['intent']['records'] if r['record_id']==qa.source_id]
    assert matching==records
    assert records[0]['received_at']==prep['repository_received_at']
    assert receipt['actual_repository_received_at']==records[0]['received_at']
    doc=pymupdf.open(stream=buffers[SOURCE],filetype='pdf')
    assert len(doc)==7
    for n in range(1,8):
        image=pymupdf.Pixmap(buffers[f'01-source-only/A01/page-{n:04}.png'])
        assert (image.width,image.height,image.n)==(3073,3976,3)
        for line in [l for l in lines if l.page==n and l.visibility!='visible']:
            x0,y0,x1,y1=line.bbox
            # Source page coordinates mapped to 300 dpi; crop stays within white glyph extent.
            box=[int(x0*300/72),int(y0*300/72),int(x1*300/72)+1,int(y1*300/72)+1]
            raw=image.samples
            assert all(min(raw[y*image.stride+box[0]*3:y*image.stride+box[2]*3])==255
                       for y in range(box[1],box[3])), line.id


def verify_crops(qa: QA, buffers: dict[str, bytes]) -> None:
    """Reconstruct every crop from captured original pixels."""
    assert len(qa.crops)==len(RECIPES)
    for crop,(name,page,box) in zip(qa.crops,RECIPES):
        assert crop.page==page and crop.pixel_box==box
        assert crop.asset.path==f'crops/{name}.png' and crop.inspected_at
        source=pymupdf.Pixmap(buffers[f'01-source-only/A01/page-{page:04}.png'])
        x0,y0,x1,y1=box
        raw=source.samples
        samples=b''.join(raw[y*source.stride+x0*3:y*source.stride+x1*3] for y in range(y0,y1))
        expected=pymupdf.Pixmap(pymupdf.csRGB,x1-x0,y1-y0,samples,False).tobytes('png')
        actual=safe_read(ROOT,crop.asset.path)
        assert expected==actual and len(actual)==crop.asset.size_bytes
        assert digest(actual)==crop.asset.sha256


def verify(sealed: bool = True) -> dict[str, int | str]:
    """Check closed local inventory and all captured review evidence."""
    if sealed:
        seal=Seal.model_validate_json(safe_read(ROOT,'FINAL_MANIFEST.json'))
        expected={a.path for a in seal.files}
        actual={p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file()}
        assert actual==expected|{'FINAL_MANIFEST.json'}
        for a in seal.files:
            raw=safe_read(ROOT,a.path)
            assert digest(raw)==a.sha256 and len(raw)==a.size_bytes,a.path
    qa=QA.model_validate_json(safe_read(ROOT,'SOURCE_QA.json'))
    schema=json.loads(safe_read(ROOT,'SOURCE_QA.schema.json'))
    assert schema==QA.model_json_schema()
    jsonschema.validate(qa.model_dump(),schema)
    buffers=captured_inputs(qa)
    validate_content(qa,buffers)
    verify_crops(qa,buffers)
    return {'status':'pass','pages':7,'native_bytes':18343,'lines':670,'fee_associations':197,
            'two_column_rows':53,'context_records':15,'definitions':10,'crops':len(RECIPES)}


def main() -> None:
    """Run only local verification; no rendering, fetching or source writes."""
    parser=argparse.ArgumentParser()
    parser.add_argument('--unsealed',action='store_true')
    args=parser.parse_args()
    sys.stdout.write(json.dumps(verify(not args.unsealed),sort_keys=True)+'\n')


if __name__=='__main__':
    main()
