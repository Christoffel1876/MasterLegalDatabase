"""Read-only source QA replay, exact byte coverage and optional fresh Poppler rendering."""
import argparse
from hashlib import sha256
import json
import re
from pathlib import Path
import subprocess
import sys
import tempfile

import jsonschema
import pymupdf

from review_models import Asset, Inspection, Manifest, Review, SOURCE_SHA

ROOT = Path(__file__).resolve().parent
PACKET_SHA = 'd56601d12ad756636c89f06484794d5ea0398da57197d208a9eb65f3121a2fd7'
PDFTOPPM = '/Users/mcoors/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/override/pdftoppm'
EXPECTED_IDS = [
    ['P1-TITLE','P1-LOCATION','P1-CHAPTER','P1-SUBTITLE','P1-AGENCY','P1-DATE'],
    ['2.1','2.1A','2.1B','2.1C','2.2','2.2A','2.2B','2.3','2.3-TEXT','2.4','2.4A','2.4B','P2-DATE'],
    ['2.5']+[f'2.5{x}' for x in 'ABCDEFGH']+['2.6','2.6A','2.6B','2.7']+
    [f'2.7{x}' for x in 'ABCDE']+['P3-DATE'],
    ['2.7F','2.8','2.8-TEXT','2.9','2.9A','2.9B','2.10']+
    [f'2.10{x}' for x in 'ABCDE']+['P4-DATE'],
    ['2.10F']+[f'2.10F.{x}' for x in range(1,6)]+['2.11','2.11A','P5-DATE'],
    [f'2.11{x}' for x in 'BCDEFGHIJKL']+['P6-DATE'],
    [f'2.11{x}' for x in 'MNOP']+['2.11-UNLETTERED','P7-DATE'],
]


def digest(raw: bytes) -> str:
    """Return the exact SHA256."""
    return sha256(raw).hexdigest()


def checked(asset: Asset, data: dict[str, bytes]) -> bytes:
    """Bind identities to the exact captured bytes consumed by validation."""
    raw = data[asset.path]
    if (digest(raw), len(raw)) != (asset.sha256, asset.size_bytes):
        raise ValueError('Asset identity differs: '+asset.path)
    return raw


def check_span(raw: bytes, span: object) -> bytes:
    """Enforce bounds and the digest of a half-open range."""
    if not 0 <= span.start <= span.end <= len(raw):
        raise ValueError('Span outside parent')
    body = raw[span.start:span.end]
    if digest(body) != span.sha256:
        raise ValueError('Span hash differs')
    return body


def verify_content(review: Review, data: dict[str, bytes]) -> dict:
    """Verify complete line/paragraph associations and unchanged source bindings."""
    raw = checked(review.source, data)
    if digest(raw) != SOURCE_SHA or len(raw) != 189000:
        raise ValueError('Wrong original source')
    packet_raw = checked(review.packet_manifest, data)
    if digest(packet_raw) != PACKET_SHA:
        raise ValueError('Wrong frozen source packet')
    packet = json.loads(packet_raw)
    packet_assets = {a['path']:a for a in packet['files']}
    prep_raw = checked(review.packet_preparation, data)
    prep = json.loads(prep_raw)
    if digest(prep_raw) != packet['preparation']['sha256']:
        raise ValueError('Packet preparation binding differs')
    candidate = checked(review.candidate, data)
    if (digest(candidate),len(candidate)) != (prep['candidate']['sha256'],prep['candidate']['size_bytes']):
        raise ValueError('Original candidate binding differs')
    if len(review.pages)!=7 or [p.physical_page for p in review.pages]!=list(range(1,8)):
        raise ValueError('Page coverage differs')
    if [[p.id for p in review.checked_passages if p.page==n] for n in range(1,8)]!=EXPECTED_IDS:
        raise ValueError('Expected complete paragraph/heading structure differs')
    by_id={p.id:p for p in review.checked_passages}
    if len(by_id)!=len(review.checked_passages):
        raise ValueError('Duplicate passage id')
    reconstructed=bytearray()
    total_lines=total_native=0
    with pymupdf.open(stream=raw,filetype='pdf') as pdf:
        if pdf.page_count!=7:
            raise ValueError('Original page count differs')
        for page, pdf_page in zip(review.pages,pdf):
            n=page.physical_page
            image=checked(page.image,data)
            expected_image=packet['identities']['pages'][n-1]['image']
            if (digest(image),len(image))!=(expected_image['sha256'],expected_image['size_bytes']):
                raise ValueError('Frozen render differs')
            pix=pymupdf.Pixmap(image)
            if (pix.width,pix.height)!=(page.width_px,page.height_px):
                raise ValueError('Page geometry differs')
            native=checked(page.native,data)
            expected_native=prep['native_pages'][n-1]['native']
            if (digest(native),len(native))!=(expected_native['sha256'],expected_native['size_bytes']):
                raise ValueError('Frozen native differs')
            if pdf_page.get_text('text',flags=195,sort=False).encode()!=native:
                raise ValueError('Native extraction does not reproduce')
            reconstructed.extend(f'[PHYSICAL PAGE {n:04d}]\n'.encode())
            base=len(reconstructed)
            if page.candidate_span.start!=base or check_span(candidate,page.candidate_span)!=native:
                raise ValueError('Page candidate span differs')
            reconstructed.extend(native);reconstructed.extend(b'\n')
            offset=0
            seen={}
            for number,line in enumerate(page.native_lines,1):
                if line.number!=number or line.native_span.start!=offset:
                    raise ValueError('Native line coverage has a gap or reorder')
                body=check_span(native,line.native_span)
                if body.decode()!=line.raw_text or line.whitespace_only!=not_empty_inverted(body):
                    raise ValueError('Native line literal or whitespace status differs')
                if (line.candidate_span.start!=base+offset or
                        check_span(candidate,line.candidate_span)!=body):
                    raise ValueError('Line candidate span differs')
                if body.strip() and line.passage_id is None:
                    raise ValueError('Nonempty native line omitted from review')
                if line.passage_id is not None:
                    seen.setdefault(line.passage_id,[]).append(number)
                offset=line.native_span.end
            if offset!=len(native):
                raise ValueError('Trailing native bytes omitted')
            if page.checked_passage_ids!=EXPECTED_IDS[n-1] or set(seen)!=set(EXPECTED_IDS[n-1]):
                raise ValueError('Page passage coverage differs')
            for ident in page.checked_passage_ids:
                passage=by_id[ident]
                if passage.image!=page.image or passage.native!=page.native:
                    raise ValueError('Passage/page asset association differs')
                body=check_span(native,passage.native_span)
                if ' '.join(body.decode().split())!=passage.text:
                    raise ValueError('Reviewed wording silently changed')
                if (passage.candidate_span.start!=base+passage.native_span.start or
                        check_span(candidate,passage.candidate_span)!=body):
                    raise ValueError('Passage candidate association differs')
                if seen[ident]!=list(range(passage.native_line_start,passage.native_line_end+1)):
                    raise ValueError('Passage line coverage differs')
                if (page.native_lines[passage.native_line_start-1].native_span.start!=passage.native_span.start or
                        page.native_lines[passage.native_line_end-1].native_span.end!=passage.native_span.end):
                    raise ValueError('Passage line/byte boundaries differ')
                if passage.parent_id is not None and passage.parent_id not in by_id:
                    raise ValueError('Dangling paragraph parent')
                match = re.match(r'^(2\.\d+)([A-P])(?:\.([1-5]))?$', ident)
                if match:
                    sec, letter, nested = match.groups()
                    want_parent = sec+letter if nested else sec
                    want_label = (nested if nested else letter)+'.'
                    if (passage.parent_id != want_parent or passage.section != sec or
                            passage.label_as_printed != want_label or passage.kind != 'paragraph'):
                        raise ValueError('Printed enumeration or section association differs')
            total_native+=len(native);total_lines+=len(page.native_lines)
    if bytes(reconstructed)!=candidate or total_native!=19118 or len(candidate)!=19272:
        raise ValueError('Complete candidate/native packaging differs')
    expected_links=[('2.7E','2.7F'),('2.10E','2.10F'),('2.11A','2.11B'),('2.11L','2.11M')]
    expected_links += [('2.10F',f'2.10F.{n}') for n in range(1,6)]
    if [(link.from_id,link.to_id) for link in review.structural_links]!=expected_links:
        raise ValueError('Cross-page or nested structure differs')
    for n in range(1,6):
        if by_id[f'2.10F.{n}'].parent_id!='2.10F':
            raise ValueError('Nested numbered item misassociated')
    if by_id['2.11-UNLETTERED'].label_as_printed is not None:
        raise ValueError('Invented source label')
    for p in review.checked_passages:
        if p.kind=='section_heading' and p.visible_markup!=['bold','underlined']:
            raise ValueError('Source heading markup omitted')
    if [d.literal for d in review.dates]!=['5/23/2012','January 21, 2009']:
        raise ValueError('Source date role set differs')
    if review.dates[0].passage_ids!=[f'P{n}-DATE' for n in range(1,8)]:
        raise ValueError('Repeated source date coverage differs')
    for finding in review.findings:
        if any(ident not in by_id for ident in finding.passage_ids):
            raise ValueError('Unbound finding')
    provenance=review.provenance
    row=json.loads(checked(provenance.canonical_record,data))
    original_provenance=json.loads(checked(provenance.selected_source_provenance,data))
    intent_raw=checked(provenance.intake_intent,data)
    intent=json.loads(intent_raw)
    receipt=json.loads(checked(provenance.intake_receipt,data))
    if (digest(intent_raw)!=receipt['intent_sha256'] or intent!=receipt['intent'] or
            [r for r in intent['records'] if r['record_id']==review.source_id]!=[row]):
        raise ValueError('Actual intake record binding differs')
    from datetime import datetime
    actual=datetime.fromisoformat(row['received_at'].replace('Z','+00:00'))
    if (row['sha256']!=SOURCE_SHA or row['archive_path']!=provenance.canonical_path_claim or
            row['acquisition_method']!='received_review_package' or
            provenance.repository_received_at!=actual or
            original_provenance['authority_id']!=review.authority_id or
            original_provenance['original']['sha256']!=SOURCE_SHA or
            original_provenance['verified_http_acquired_at'] is not None or
            original_provenance['requested_url_claim']!=provenance.supplied_url):
        raise ValueError('Source authority/custody qualification differs')
    inspection=Inspection.model_validate_json(checked(review.inspection,data))
    jsonschema.validate(inspection.model_dump(mode='json'),json.loads(data['INSPECTION.schema.json']))
    if inspection.full_pages!=[p.image for p in review.pages] or len(inspection.crops)!=4:
        raise ValueError('Inspection page/crop coverage differs')
    for crop in inspection.crops:
        page_image=data[crop.input_path]
        if digest(page_image)!=crop.input_sha256:
            raise ValueError('Crop input differs')
        pix=pymupdf.Pixmap(page_image)
        left,top,right,bottom=crop.pixel_box
        if not 0<=left<right<=pix.width or not 0<=top<bottom<=pix.height:
            raise ValueError('Unsafe crop rectangle')
        samples=pix.samples
        selected=b''.join(samples[y*pix.stride+left*pix.n:y*pix.stride+right*pix.n]
                          for y in range(top,bottom))
        result=pymupdf.Pixmap(pix.colorspace,right-left,bottom-top,selected,pix.alpha)
        expected=data[crop.output_path]
        if result.tobytes('png')!=expected or digest(expected)!=crop.output_sha256:
            raise ValueError('Exact pixel crop does not reproduce')
    transcript=['# Reviewed source transcript\n',
        'Candidate-aware direct image review by Plato. Whitespace normalized; original native bytes unchanged. No legal currentness certification.\n']
    for page in review.pages:
        transcript.append(f'\n## Physical page {page.physical_page}\n')
        for passage in review.checked_passages:
            if passage.page==page.physical_page:
                transcript.append(f'\n### {passage.id}\n\n{passage.text}\n')
    if ''.join(transcript).encode()!=data['REVIEWED_TRANSCRIPT.md']:
        raise ValueError('Readable transcript differs from checked passage records')
    return {'pages':7,'native_bytes':total_native,'candidate_bytes':len(candidate),
            'passages':len(by_id),'native_lines':total_lines,'crops':4}


def not_empty_inverted(raw: bytes) -> bool:
    """Classify only literal whitespace; never silently discard substantive bytes."""
    return not bool(raw.strip())


def main() -> None:
    """Validate closed payloads; allow an explicit development-only preseal mode."""
    parser=argparse.ArgumentParser()
    parser.add_argument('--unsealed',action='store_true')
    parser.add_argument('--rerender',action='store_true')
    parser.add_argument('--pdftoppm',default=PDFTOPPM)
    args=parser.parse_args()
    data={}
    for p in ROOT.rglob('*'):
        if p.is_symlink():
            raise ValueError('Review symlink')
        if p.is_file():
            data[p.relative_to(ROOT).as_posix()]=p.read_bytes()
    if not args.unsealed:
        manifest=Manifest.model_validate_json(data['FINAL_MANIFEST.json'])
        jsonschema.validate(manifest.model_dump(mode='json'),json.loads(data['FINAL_MANIFEST.schema.json']))
        expected={a.path for a in manifest.files}
        if len(expected)!=len(manifest.files) or len({x.casefold() for x in expected})!=len(expected):
            raise ValueError('Duplicate/case-aliased manifest member')
        if set(data)!=expected|{'FINAL_MANIFEST.json'}:
            raise ValueError('Closed review inventory differs')
        for a in manifest.files:
            if Path(a.path).is_absolute() or '..' in Path(a.path).parts:
                raise ValueError('Unsafe manifest path')
            checked(a,data)
    review=Review.model_validate_json(data['SOURCE_QA.json'])
    jsonschema.validate(review.model_dump(mode='json'),json.loads(data['SOURCE_QA.schema.json']))
    result=verify_content(review,data)
    if args.rerender:
        prep=json.loads(data['inputs/packet-preparation.json'])
        executable=Path(args.pdftoppm)
        if digest(executable.read_bytes())!=prep['renderer_sha256']:
            raise ValueError('Renderer executable differs from frozen receipt')
        with tempfile.TemporaryDirectory(prefix='geode-plato-render-') as temp:
            work=Path(temp);(work/'original.pdf').write_bytes(data['inputs/original.pdf'])
            run=subprocess.run([str(executable),'-f','1','-l','7','-r','300','-png',
                                str(work/'original.pdf'),str(work/'page')],capture_output=True,
                               timeout=180,check=False)
            if run.returncode:
                raise ValueError('Fresh Poppler rerender failed')
            for page in review.pages:
                actual=(work/f'page-{page.physical_page}.png').read_bytes()
                if actual!=data[page.image.path]:
                    raise ValueError('Fresh render bytes differ')
        result['rerendered_pages']=7
    sys.stdout.write(json.dumps({'status':'passed','checks':result,
                                'legal_currentness':'not_verified'},indent=2)+'\n')


if __name__=='__main__':
    main()
