"""Read-only custody/structure replay; does not certify visual or legal judgment."""
import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path, PurePosixPath

import jsonschema
import pymupdf

from models import Correction, Crop, Manifest, Ref, SourceQA
from prepare_ocr import OcrEvent, OcrOutput

SOURCE_SHA = '0688818dfd4d7726f1eb84b5b57c47580d01b094297a92d4ce88c600ccfe7eba'
RETRIEVAL_SHA = '0ad7b970736921a175de778e05629db8b9191ba2394a692d3715c0a51421c95f'
POPPLER_SHA = 'de772e88ab9977ccde25def9b403bf42675d75f5dd82b19fbd7d8123ad183159'


def require(value: bool, message: str) -> None:
    """Fail closed without depending on Python assertions."""
    if not value:
        raise ValueError(message)


def digest(data: bytes) -> str:
    """Hash an exact captured buffer."""
    return hashlib.sha256(data).hexdigest()


def ordinary(path: Path) -> bytes:
    """Read an ordinary file after rejecting lexical symlink ancestors."""
    absolute = Path(os.path.abspath(path))
    for part in (absolute, *absolute.parents):
        require(not part.is_symlink(), f'symlink: {part}')
    require(absolute.is_file(), f'not an ordinary file: {absolute}')
    return absolute.read_bytes()


def safe_name(name: str) -> str:
    """Reject ambiguous or escaping package-relative paths."""
    parsed = PurePosixPath(name)
    require(bool(name) and not parsed.is_absolute() and parsed.as_posix() == name,
            'unsafe or noncanonical relative path')
    require('\\' not in name and all(p not in ('..', '.') for p in parsed.parts),
            'unsafe relative path')
    return name


def checked_ref(reference: Ref, buffers: dict[str, bytes]) -> bytes:
    """Resolve an exact reference solely from captured verified buffers."""
    name = safe_name(reference.path)
    require(name in buffers, f'missing referenced file: {name}')
    data = buffers[name]
    require(len(data) == reference.size_bytes and digest(data) == reference.sha256,
            f'reference differs: {name}')
    return data


def capture(root: Path) -> dict[str, bytes]:
    """Capture every closed manifest member once and verify its identity."""
    raw_manifest = ordinary(root / 'FINAL_MANIFEST.json')
    manifest = Manifest.model_validate_json(raw_manifest)
    names = [safe_name(r.path) for r in manifest.files]
    require(names == sorted(set(names)), 'manifest ordering or duplicate member')
    require('FINAL_MANIFEST.json' not in names, 'manifest cannot include itself')
    require(manifest.payload_count == len(names), 'manifest payload count')
    actual = set()
    for path in root.rglob('*'):
        require(not path.is_symlink(), 'symlink in package tree')
        if path.is_file():
            actual.add(path.relative_to(root).as_posix())
    require(actual == set(names) | {'FINAL_MANIFEST.json'}, 'closed inventory differs')
    buffers = {'FINAL_MANIFEST.json': raw_manifest}
    for record in manifest.files:
        buffers[record.path] = ordinary(root / record.path)
        checked_ref(record, buffers)
    schema = json.loads(buffers['MANIFEST.schema.json'])
    require(schema == Manifest.model_json_schema(), 'manifest schema differs')
    jsonschema.validate(json.loads(raw_manifest), schema)
    return buffers


def verify_review(buffers: dict[str, bytes]) -> dict[str, int | str | bool]:
    """Replay source/native/OCR/transcript/markup/context bindings from captured bytes."""
    schema = json.loads(buffers['SOURCE_QA.schema.json'])
    require(schema == SourceQA.model_json_schema(), 'review schema differs')
    jsonschema.validate(json.loads(buffers['SOURCE_QA.json']), schema)
    qa = SourceQA.model_validate_json(buffers['SOURCE_QA.json'])
    pdf_bytes = checked_ref(qa.source,buffers)
    require(qa.source_sha == SOURCE_SHA == digest(pdf_bytes), 'source identity differs')
    require(qa.source.path == 'source/original.pdf' and len(pdf_bytes) == 1146747,
            'source path or size differs')
    require(pdf_bytes.startswith(b'%PDF-'), 'missing PDF magic')
    document = pymupdf.open(stream=pdf_bytes, filetype='pdf')
    require(len(document) == 14, 'page count differs')
    event = json.loads(checked_ref(qa.acquisition.source_event,buffers))
    require(qa.acquisition.source_event.path == 'custody/retrieval/events/A001/RESULT.json',
            'wrong HTTP event path')
    require(digest(checked_ref(qa.acquisition.frozen_retrieval_manifest,buffers)) == RETRIEVAL_SHA,
            'retrieval manifest differs')
    retrieval = json.loads(buffers['custody/retrieval/FINAL_MANIFEST.json'])
    for row in retrieval['files']:
        ref = Ref.model_validate(row)
        copied = Ref(path='custody/retrieval/'+ref.path,sha256=ref.sha256,size_bytes=ref.size_bytes)
        checked_ref(copied,buffers)
    require(event['body']['sha256'] == SOURCE_SHA and
            buffers['custody/retrieval/events/A001/response.body'] == pdf_bytes,
            'HTTP source body differs')
    for field in ('requested_url','final_url'):
        require(getattr(qa.acquisition,field) == event[field], 'HTTP URL differs')
    require(qa.acquisition.actual_started_at == event['started_at'] and
            qa.acquisition.actual_completed_at == event['completed_at'], 'HTTP time differs')
    require(event['http_status'] == 200 and event['body_complete'] and
            not event['partial_or_unknown'] and event['process_exit'] == 0,
            'incomplete HTTP custody')
    require([p.page for p in qa.pages] == list(range(1,15)), 'page order differs')
    ids = [s.id for s in qa.segments]
    require(len(set(ids)) == len(ids), 'duplicate segment identity')
    by_id = {s.id:s for s in qa.segments}
    line_total = 0
    text_total = 0
    for page in qa.pages:
        n=page.page
        require(page.image.path == f'pages/page-{n:02d}.png', 'page image association differs')
        image_bytes=checked_ref(page.image,buffers)
        image=pymupdf.Pixmap(image_bytes)
        require((image.width,image.height) == (2550,3300), 'image dimensions differ')
        native=checked_ref(page.native,buffers)
        require(page.native.path == f'native/page-{n:04d}.txt', 'native page differs')
        require(native == b'' == document[n-1].get_text('text',flags=195,sort=False).encode(),
                'native extraction differs')
        raw=checked_ref(page.ocr_candidate,buffers)
        stdout=checked_ref(page.ocr_stdout,buffers)
        stderr=checked_ref(page.ocr_stderr,buffers)
        ocr=OcrOutput.model_validate_json(stdout)
        for filename,model in [('OCR_OUTPUT',OcrOutput),('OCR_EVENT',OcrEvent)]:
            require(json.loads(buffers[filename+'.schema.json']) == model.model_json_schema(),
                    'OCR schema differs')
        require(raw == ('\n'.join(line.text for line in ocr.lines)+'\n').encode(),
                'raw OCR candidate/order differs')
        require(ocr.revision == 3 and len(ocr.lines) == page.ocr_line_count,'OCR counts differ')
        captured_event=checked_ref(page.ocr_event,buffers)
        oe=OcrEvent.model_validate_json(captured_event)
        require(oe.page == n and oe.exit_code == 0 and not oe.correction_performed and stderr == b'',
                'OCR event status differs')
        for field,expected in [('image',image_bytes),('stdout',stdout),('stderr',stderr),
                               ('candidate',raw)]:
            r=Ref.model_validate(getattr(oe,field).model_dump())
            require(checked_ref(r,buffers) == expected,'OCR event binding differs')
        for field in ('executable','swift_source'):
            checked_ref(Ref.model_validate(getattr(oe,field).model_dump()),buffers)
        require(datetime.fromisoformat(oe.started_at) <= datetime.fromisoformat(oe.completed_at),
                'OCR interval reversed')
        lines=raw.splitlines(keepends=True)
        offsets=[0]
        for line in lines:
            offsets.append(offsets[-1]+len(line))
        segments=[s for s in qa.segments if s.page == n]
        require([s.id for s in segments] == page.segment_ids, 'page segment order differs')
        line_numbers=[]
        transcript=checked_ref(page.checked_transcript,buffers)
        rebuilt=b''
        for segment in segments:
            require(segment.image_path == page.image.path,'segment image differs')
            x0,y0,x1,y1=segment.pixel_rect
            require(0 <= x0 < x1 <= 2550 and 0 <= y0 < y1 <= 3300, 'bad pixel rect')
            expected_crops=[f'crops/page-{n:02d}-{half}.png' for half in
                (['top'] if y1 <=1650 else ['bottom'] if y0 >=1650 else ['top','bottom'])]
            require(segment.crop_paths == expected_crops,'crop/page association differs')
            numbers=segment.ocr_line_numbers
            line_numbers.extend(numbers)
            if numbers:
                require(numbers == list(range(numbers[0],numbers[-1]+1)), 'OCR range gap')
                require(1 <= numbers[0] <= numbers[-1] <= len(lines), 'OCR range outside page')
                require(segment.ocr_span is not None,'missing OCR span')
                s=segment.ocr_span
                require((s.start,s.end)==(offsets[numbers[0]-1],offsets[numbers[-1]]),
                        'OCR offset differs')
                require(raw[s.start:s.end] == segment.ocr_text.encode() and
                        digest(raw[s.start:s.end]) == s.sha256,'OCR span content differs')
            else:
                require(segment.id == 'CWRC-P03-V01' and segment.ocr_span is None and
                        segment.ocr_text == '', 'unexpected OCR-unmatched region')
            if segment.checked_text is None:
                require(segment.kind == 'handwriting_uncertain' and segment.checked_span is None
                        and not segment.markup,'null transcript outside uncertain handwriting')
            else:
                require(segment.checked_span is not None,'missing checked span')
                data=segment.checked_text.encode()
                s=segment.checked_span
                require(s.start==len(rebuilt) and s.end==len(rebuilt)+len(data) and
                        s.sha256==digest(data),'checked offset differs')
                require(transcript[s.start:s.end] == data, 'checked text differs')
                rebuilt+=data+b'\n'
                for markup in segment.markup:
                    require(data[markup.start:markup.end] == markup.text.encode(),
                            'markup word/offset differs')
            if segment.continuation_of:
                require(segment.continuation_of in by_id and
                        by_id[segment.continuation_of].page == n-1,'bad continuation')
        require(line_numbers == list(range(1,len(lines)+1)),'dropped/duplicate/reordered OCR lines')
        require(rebuilt == transcript,'extra/dropped checked transcript bytes')
        line_total += len(lines)
        text_total += len(transcript)
    crop_rows=[Crop.model_validate_json(line) for line in buffers['CROPS.jsonl'].splitlines()]
    require(len(crop_rows)==28,'crop count differs')
    require([(c.page,c.rect[1]) for c in crop_rows] ==
            [(n,y) for n in range(1,15) for y in (0,1650)],'crop coverage differs')
    for crop in crop_rows:
        require(crop.source_path == f'pages/page-{crop.page:02d}.png','crop source differs')
        require(digest(buffers[crop.source_path]) == crop.source_sha256,'crop source hash differs')
        source=pymupdf.Pixmap(buffers[crop.source_path])
        rectangle=pymupdf.IRect(crop.rect)
        derived=pymupdf.Pixmap(source.colorspace,rectangle,source.alpha)
        derived.copy(source,rectangle)
        data=checked_ref(Ref(path=crop.path,sha256=crop.sha256,size_bytes=crop.size_bytes),buffers)
        require(derived.tobytes('png') == data,'crop pixels differ')
    for record in [*qa.observations,*qa.date_claims]:
        require(bool(record.segment_ids) and all(i in by_id for i in record.segment_ids),
                'unbound observation or date')
    corrections=[Correction.model_validate_json(line)
                 for line in buffers['CORRECTIONS.jsonl'].splitlines()]
    seen=set()
    for c in corrections:
        key=(c.page,c.line)
        require(key not in seen,'duplicate correction')
        seen.add(key)
        raw=buffers[f'ocr/page-{c.page:04d}/candidate.txt'].decode().splitlines()
        require(raw[c.line-1] == c.raw_ocr,'correction candidate binding differs')
        segment=next(s for s in qa.segments if s.page==c.page and c.line in s.ocr_line_numbers)
        require(c.checked is None if segment.checked_text is None else
                c.checked is not None and c.checked in segment.checked_text,
                'correction not reflected in checked text')
    document.close()
    return dict(status='PASS',physical_pages=14,full_pages_visually_reviewed=14,
                exact_half_page_crops=28,segments=len(qa.segments),ocr_lines=line_total,
                native_bytes=0,checked_transcript_bytes=text_total,answer_safe=False,
                legal_currentness='not_verified')


def rerender(buffers: dict[str, bytes], executable: Path) -> None:
    """Compare complete Poppler renders in a temporary directory, offline only."""
    require(digest(ordinary(executable)) == POPPLER_SHA,'renderer executable differs')
    with tempfile.TemporaryDirectory(prefix='cwrc-rerender-') as temp:
        directory=Path(temp)
        pdf=directory/'source.pdf'
        pdf.write_bytes(buffers['source/original.pdf'])
        result=subprocess.run([str(executable),'-r','300','-png',str(pdf),str(directory/'page')],
                              capture_output=True,timeout=60,check=False)
        require(result.returncode==0,'Poppler rendering failed')
        for n in range(1,15):
            require((directory/f'page-{n:02d}.png').read_bytes()==buffers[f'pages/page-{n:02d}.png'],
                    f'rendered page {n} differs')


def main() -> None:
    """Validate a sealed portable packet; optional offline rendering uses a pinned binary."""
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parent)
    parser.add_argument('--rerender',type=Path,metavar='PDFTOPPM')
    args=parser.parse_args()
    root=Path(os.path.abspath(args.root.expanduser()))
    buffers=capture(root)
    result=verify_review(buffers)
    if args.rerender:
        rerender(buffers,args.rerender)
        result['poppler_rerender']='PASS'
    sys.stdout.write(json.dumps(result,indent=2)+'\n')


if __name__ == '__main__':
    main()
