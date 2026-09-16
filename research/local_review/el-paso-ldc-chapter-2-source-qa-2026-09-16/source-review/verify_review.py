"""Read-only closed source review validation, with optional exact Poppler rerender."""
import argparse
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import jsonschema
import pymupdf

from build_review import transcript
from review_models import Asset, Inspection, Manifest, Review, SOURCE_SHA
from source_structure import LINKS, SPECS, visual_order

ROOT=Path(__file__).resolve().parent
PACKET_SHA='06ad921d92cc9c436caf9bd47977d4a9f24e425912071b91e8d95194543ba7b8'
PDFTOPPM='/Users/mcoors/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/override/pdftoppm'
COPIES={
 'inputs/original.pdf':'01-source-only/A01/original.pdf',
 'inputs/candidate.txt':'02-candidate-text/A01/candidate.txt',
 'inputs/packet-manifest.schema.json':'MANIFEST.schema.json',
 'inputs/packet-preparation.json':'04-verification/PREPARATION.json',
 'inputs/packet-preparation.schema.json':'04-verification/PREPARATION.schema.json',
 'inputs/canonical-record.jsonl':'03-custody/canonical-record.jsonl',
 'inputs/source-provenance.selected.jsonl':'03-custody/source-provenance.selected.jsonl',
 'inputs/intake-receipt.json':'03-custody/RECEIPT.json',
 'inputs/intake-intent.json':'03-custody/INTENT.json',
 'inputs/public-headers.txt':'03-custody/public-headers.txt',
}
for n in range(1,8):
    COPIES[f'pages/page-{n:04}.png']=f'01-source-only/A01/page-{n:04}.png'
    COPIES[f'native/page-{n:04}.txt']=f'02-candidate-text/A01/page-{n:04}.native.txt'


def digest(raw: bytes) -> str:
    """Return the exact hash."""
    return sha256(raw).hexdigest()


def checked(asset: Asset, data: dict[str, bytes]) -> bytes:
    """Consume only captured bytes that match the asserted identity."""
    raw=data[asset.path]
    if (digest(raw),len(raw))!=(asset.sha256,asset.size_bytes):
        raise ValueError('Asset identity differs: '+asset.path)
    return raw


def check_span(raw: bytes, span: object) -> bytes:
    """Check a half-open source-byte slice."""
    if not 0<=span.start<=span.end<=len(raw):
        raise ValueError('Span outside parent')
    body=raw[span.start:span.end]
    if digest(body)!=span.sha256:
        raise ValueError('Span hash differs')
    return body


def verify_content(review: Review, data: dict[str, bytes]) -> dict:
    """Replay exact inputs, exhaustive source associations, dates and custody."""
    pdf_raw=checked(review.source,data)
    if digest(pdf_raw)!=SOURCE_SHA or len(pdf_raw)!=116324:
        raise ValueError('Wrong original source')
    packet_raw=checked(review.packet_manifest,data)
    if digest(packet_raw)!=PACKET_SHA:
        raise ValueError('Wrong packet')
    packet=json.loads(packet_raw)
    jsonschema.validate(packet,json.loads(data['inputs/packet-manifest.schema.json']))
    packet_assets={a['path']:a for a in packet['files']}
    for local,original in COPIES.items():
        expected=packet_assets[original]
        raw=data[local]
        if (digest(raw),len(raw))!=(expected['sha256'],expected['size_bytes']):
            raise ValueError('Copied packet input differs: '+local)
    prep=json.loads(checked(review.packet_preparation,data))
    jsonschema.validate(prep,json.loads(data['inputs/packet-preparation.schema.json']))
    candidate=checked(review.candidate,data)
    if len(candidate)!=16520 or review.source.path!='inputs/original.pdf':
        raise ValueError('Source/candidate binding differs')
    if [p.physical_page for p in review.pages]!=list(range(1,8)):
        raise ValueError('Page coverage differs')
    expected_ids=[s[0] for n in range(1,8) for s in SPECS[n]]
    if [p.id for p in review.checked_passages]!=expected_ids:
        raise ValueError('Complete passage structure differs')
    by_id={p.id:p for p in review.checked_passages}
    reconstructed=bytearray();total_native=total_lines=0
    with pymupdf.open(stream=pdf_raw,filetype='pdf') as pdf:
        if pdf.page_count!=7:
            raise ValueError('Wrong source page count')
        for page,physical in zip(review.pages,pdf):
            n=page.physical_page
            if page.image.path!=f'pages/page-{n:04}.png' or page.native.path!=f'native/page-{n:04}.txt':
                raise ValueError('Page asset identity differs')
            png=checked(page.image,data);pix=pymupdf.Pixmap(png)
            if (pix.width,pix.height)!=(2550,3300):
                raise ValueError('Wrong image dimensions')
            native=checked(page.native,data)
            if physical.get_text('text',flags=195,sort=False).encode()!=native:
                raise ValueError('Native replay differs')
            reconstructed.extend(f'[PHYSICAL PAGE {n:04d}]\n'.encode());base=len(reconstructed)
            if page.candidate_span.start!=base or check_span(candidate,page.candidate_span)!=native:
                raise ValueError('Page candidate span differs')
            reconstructed.extend(native);reconstructed.extend(b'\n')
            if page.visual_order!=visual_order(n):
                raise ValueError('Visual footer/body order differs')
            if page.checked_passage_ids!=[s[0] for s in SPECS[n]]:
                raise ValueError('Page passage coverage differs')
            owners={i:s[0] for s in SPECS[n] for i in range(s[1],s[2]+1)}
            lines=native.splitlines(keepends=True);offset=0;bounds=[0]
            if len(lines)!=len(page.native_lines):
                raise ValueError('Native line coverage differs')
            for i,(line,record) in enumerate(zip(lines,page.native_lines),1):
                if (record.number!=i or record.native_span.start!=offset or
                    record.native_span.end!=offset+len(line) or
                    check_span(native,record.native_span)!=line or record.raw_text!=line.decode() or
                    record.passage_id!=owners[i] or record.whitespace_only!=(not bool(line.strip())) or
                    record.candidate_span.start!=base+offset or
                    check_span(candidate,record.candidate_span)!=line):
                    raise ValueError('Native line literal/coverage association differs')
                offset+=len(line);bounds.append(offset)
            if offset!=len(native):
                raise ValueError('Native trailing bytes omitted')
            for ident,a,b,kind,unit,parent,label in SPECS[n]:
                p=by_id[ident]
                if (p.page,p.kind,p.logical_unit_id,p.parent_id,p.label_as_printed,
                    p.native_line_start,p.native_line_end)!=(n,kind,unit,parent,label,a,b):
                    raise ValueError('Paragraph/numbering/parent association differs')
                if p.section!=(None if unit.startswith('P') else unit):
                    raise ValueError('Section association differs')
                if p.image!=page.image or p.native!=page.native:
                    raise ValueError('Passage source/image binding differs')
                body=native[bounds[a-1]:bounds[b]]
                if (p.native_span.start,p.native_span.end)!=(bounds[a-1],bounds[b]) or check_span(native,p.native_span)!=body:
                    raise ValueError('Passage native range differs')
                if p.text!=' '.join(body.decode().split()):
                    raise ValueError('Reviewed wording silently changed')
                if p.candidate_span.start!=base+bounds[a-1] or check_span(candidate,p.candidate_span)!=body:
                    raise ValueError('Passage candidate range differs')
                if label is not None and p.text.split()[0]!=label:
                    raise ValueError('Printed label differs')
                markup=['bold'] if kind=='section_heading' else ['regular'] if kind=='document_title' else ['bold','blue'] if kind=='page_header' else []
                if p.visible_markup!=markup:
                    raise ValueError('Heading style omitted')
            total_native+=len(native);total_lines+=len(lines)
    if bytes(reconstructed)!=candidate or total_native!=16366 or total_lines!=302:
        raise ValueError('Full unchanged candidate packaging differs')
    if [(s.kind,s.from_id,s.to_id) for s in review.structural_links]!=LINKS:
        raise ValueError('Cross-page continuation differs')
    for link in review.structural_links:
        if by_id[link.from_id].logical_unit_id!=by_id[link.to_id].logical_unit_id:
            raise ValueError('Cross-page logical unit differs')
    if (len(review.dates)!=1 or review.dates[0].literal!='Effective 12/12/2017' or
        review.dates[0].role!='source_stated_effective_date_unverified' or
        review.dates[0].passage_ids!=[f'P{n}-DATE' for n in range(1,8)]):
        raise ValueError('Printed date role or coverage differs')
    for n in range(1,8):
        if by_id[f'P{n}-DATE'].text!='Effective 12/12/2017':
            raise ValueError('Effective footer source text differs')
    if [f.id for f in review.findings]!=[f'F{n:02}' for n in range(1,12)]:
        raise ValueError('Additive source findings omitted')
    if any(i not in by_id for f in review.findings for i in f.passage_ids):
        raise ValueError('Unbound finding')
    if review.substantive_candidate_corrections:
        raise ValueError('Unreviewed correction added')
    provenance=review.provenance
    row=json.loads(checked(provenance.canonical_record,data))
    source_prov=json.loads(checked(provenance.selected_source_provenance,data))
    intent_raw=checked(provenance.intake_intent,data);intent=json.loads(intent_raw)
    receipt=json.loads(checked(provenance.intake_receipt,data))
    if (digest(intent_raw)!=receipt['intent_sha256'] or intent!=receipt['intent'] or
        [r for r in intent['records'] if r['record_id']==review.source_id]!=[row]):
        raise ValueError('Intake receipt/record binding differs')
    if (row['sha256']!=SOURCE_SHA or row['archive_path']!=provenance.canonical_path_claim or
        row['acquisition_method']!='received_review_package' or
        datetime.fromisoformat(row['received_at'].replace('Z','+00:00'))!=provenance.repository_received_at or
        source_prov['authority_id']!=review.authority_id or source_prov['original']['sha256']!=SOURCE_SHA or
        source_prov['requested_url_claim']!=provenance.supplied_url or
        source_prov['final_url_claim']!=provenance.supplied_final_url or
        source_prov['verified_http_acquired_at'] is not None or source_prov['source_referrals']!=[] or
        source_prov['referral_basis']!='inherited_url_no_fresh_anchor'):
        raise ValueError('Custody authority/URL/referral qualification differs')
    for claim,actual in [('acquisition_started_at_claim',provenance.supplied_acquisition_started_at),
                         ('acquisition_completed_at_claim',provenance.supplied_acquisition_completed_at)]:
        if datetime.fromisoformat(source_prov[claim].replace('Z','+00:00'))!=actual:
            raise ValueError('Supplied acquisition date changed')
    headers=checked(provenance.public_headers,data)
    if digest(headers)!=source_prov['public_headers']['sha256']:
        raise ValueError('Public header derivative differs')
    inspection=Inspection.model_validate_json(checked(review.inspection,data))
    jsonschema.validate(inspection.model_dump(mode='json'),json.loads(data['INSPECTION.schema.json']))
    if inspection.full_pages!=[p.image for p in review.pages] or len(inspection.crops)!=7:
        raise ValueError('Inspection coverage differs')
    if inspection.model_dump(mode='json')['crops']!=json.loads(data['crop-recipes.json']):
        raise ValueError('Crop recipes differ')
    for crop in inspection.crops:
        raw=data[crop.input_path]
        if digest(raw)!=crop.input_sha256:
            raise ValueError('Crop original differs')
        pix=pymupdf.Pixmap(raw);l,t,r,b=crop.pixel_box
        if not 0<=l<r<=pix.width or not 0<=t<b<=pix.height:
            raise ValueError('Invalid crop bounds')
        s=pix.samples
        part=b''.join(s[y*pix.stride+l*pix.n:y*pix.stride+r*pix.n] for y in range(t,b))
        result=pymupdf.Pixmap(pix.colorspace,r-l,b-t,part,pix.alpha).tobytes('png')
        if result!=data[crop.output_path] or digest(result)!=crop.output_sha256:
            raise ValueError('Crop pixels do not replay')
    if transcript(review)!=data['REVIEWED_TRANSCRIPT.md']:
        raise ValueError('Reviewed visual-order transcript differs')
    return {'pages':7,'passages':119,'native_lines':302,'native_bytes':16366,
            'candidate_bytes':16520,'cross_page_links':5,'crops':7}


def load(root: Path, sealed: bool=True) -> dict[str, bytes]:
    """Capture each file once and validate a closed, symlink-free inventory."""
    data={}
    for path in root.rglob('*'):
        if path.is_symlink():
            raise ValueError('Symlink in review')
        if path.is_file():
            data[path.relative_to(root).as_posix()]=path.read_bytes()
    if sealed:
        m=Manifest.model_validate_json(data['FINAL_MANIFEST.json'])
        jsonschema.validate(m.model_dump(mode='json'),json.loads(data['FINAL_MANIFEST.schema.json']))
        expected={a.path for a in m.files}
        if len(expected)!=len(m.files) or len({p.casefold() for p in expected})!=len(expected):
            raise ValueError('Duplicate inventory path')
        if set(data)!=expected|{'FINAL_MANIFEST.json'}:
            raise ValueError('Closed inventory differs')
        for a in m.files:
            if Path(a.path).is_absolute() or '..' in Path(a.path).parts:
                raise ValueError('Unsafe inventory path')
            checked(a,data)
    return data


def main() -> None:
    """Replay frozen evidence offline; optional rendering writes only to a temporary directory."""
    p=argparse.ArgumentParser();p.add_argument('--unsealed',action='store_true')
    p.add_argument('--rerender',action='store_true');p.add_argument('--pdftoppm',default=PDFTOPPM)
    args=p.parse_args();data=load(ROOT,not args.unsealed)
    review=Review.model_validate_json(data['SOURCE_QA.json'])
    jsonschema.validate(review.model_dump(mode='json'),json.loads(data['SOURCE_QA.schema.json']))
    result=verify_content(review,data)
    if args.rerender:
        prep=json.loads(data['inputs/packet-preparation.json']);exe=Path(args.pdftoppm)
        if digest(exe.read_bytes())!=prep['renderer_sha256']:
            raise ValueError('Pinned renderer differs')
        with tempfile.TemporaryDirectory(prefix='plato-ldc-render-') as tmp:
            work=Path(tmp);(work/'original.pdf').write_bytes(data['inputs/original.pdf'])
            run=subprocess.run([str(exe),'-f','1','-l','7','-r','300','-png',str(work/'original.pdf'),str(work/'page')],capture_output=True,timeout=180,check=False)
            if run.returncode:
                raise ValueError('Poppler rerender failed')
            for n in range(1,8):
                if (work/f'page-{n}.png').read_bytes()!=data[f'pages/page-{n:04}.png']:
                    raise ValueError('Fresh rendered image differs')
        result['rerendered_pages']=7
    sys.stdout.write(json.dumps({'status':'passed','checks':result,'legal_currentness':'not_verified'},indent=2)+'\n')


if __name__=='__main__':
    main()
