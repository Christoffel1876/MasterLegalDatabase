"""Reproduce typed review records from unchanged bytes and reviewed structure, offline."""
from datetime import datetime, timezone
from hashlib import sha256
import json
import sys
from pathlib import Path

from review_models import Asset, Inspection, Review
from source_structure import SPECS, LINKS, visual_order

ROOT=Path(__file__).resolve().parent


def digest(raw: bytes) -> str:
    """Return the exact byte digest."""
    return sha256(raw).hexdigest()


def asset(path: str) -> dict:
    """Describe a local immutable input."""
    raw=(ROOT/path).read_bytes()
    return {'path':path,'sha256':digest(raw),'size_bytes':len(raw)}


def span(raw: bytes, start: int, end: int) -> dict:
    """Bind a half-open byte range."""
    return {'start':start,'end':end,'sha256':digest(raw[start:end])}


def save(name: str, model: type, value: dict) -> None:
    """Export schema before validating and writing the typed object."""
    (ROOT/(name+'.schema.json')).write_text(json.dumps(model.model_json_schema(),indent=2)+'\n')
    validated=model.model_validate_json(json.dumps(value))
    (ROOT/(name+'.json')).write_text(validated.model_dump_json(indent=2)+'\n')


def transcript(review: Review) -> bytes:
    """Render normalized wording in checked visual order, retaining native separately."""
    out=['---\nsource_id: el-paso-ldc-chapter-2-sd011\nstatus: checked_source_wording_not_current_law\nreviewer: Plato\n---\n# Reviewed source transcript\n',
         'Candidate-aware direct image review by Plato within the same Codex model family. '
         'Whitespace normalized; original native bytes unchanged. Footer lines moved to their '
         'visible bottom-of-page position. No legal currentness certification.\n']
    by_id={p.id:p for p in review.checked_passages}
    for page in review.pages:
        out.append(f'\n## Physical page {page.physical_page}\n')
        for ident in page.visual_order:
            out.append(f'\n### {ident}\n\n{by_id[ident].text}\n')
    return ''.join(out).encode()


def main() -> None:
    """Build only this new handoff; do not touch original packet or canonical files."""
    if (ROOT/'FINAL_MANIFEST.json').exists():
        raise ValueError('Frozen review cannot be rebuilt')
    now=datetime.now(timezone.utc).isoformat()
    exposure=('Plato prepared the packet and read its custody metadata earlier. This review '
              'directly displayed all seven full images before reading the frozen native candidate, '
              'then inspected seven crops. It is candidate-aware internal review in the same '
              'Codex family, not a blind external or independent-model-family review. Atlas later sent title-weight and three printed-heading-label feedback after the initial complete comparison. Plato re-opened page 1 and confirmed regular title weight; checked exact native heading tokens against the previously viewed images. Root feedback is acknowledged and is not independent-model-family evidence. No external reviewer report was consulted.')
    recipes=json.loads((ROOT/'crop-recipes.json').read_text())
    inspection={'reviewer':'Plato','recorded_at':now,
        'method':'direct_view_image_full_pages_then_native_comparison_and_crops',
        'full_pages':[asset(f'pages/page-{n:04}.png') for n in range(1,8)],'crops':recipes,
        'full_pages_displayed_size':'Tool full-page display approximately 1376 x 1780; original 2550 x 3300 pixels preserved. Crops displayed directly at tool size.',
        'prior_exposure':exposure,'native_candidate_read_after_full_images':True,
        'external_reports_consulted':False,
        'chronology_limit':'Reviewer attestation recorded after actual tool use. This package does not authenticate internal model cognition or external chat history. Source location text was used only to choose crop bounds, followed by direct pixel inspection.'}
    save('INSPECTION',Inspection,inspection)
    candidate=(ROOT/'inputs/candidate.txt').read_bytes()
    prep=json.loads((ROOT/'inputs/packet-preparation.json').read_text())
    pages=[];passages=[]
    crop_links={'2.1.2-p1':['P1-NOTICE'],'2.2.2A-part2':['P4-PROCEEDINGS'],
        '2.2.2B.5-text':['P4-CRS','P4-CRS-FULL'],'2.2.3A-text':['P5-PUBLIC'],
        '2.2.3B-intro':['P5-CODE'],'2.2.4B.8-text':['P7-LDC']}
    for n in range(1,8):
        native=(ROOT/f'native/page-{n:04}.txt').read_bytes()
        lines=native.splitlines(keepends=True);bounds=[0]
        for line in lines: bounds.append(bounds[-1]+len(line))
        base=prep['native_pages'][n-1]['candidate_start']
        image=asset(f'pages/page-{n:04}.png');nat=asset(f'native/page-{n:04}.txt')
        owners={i:s[0] for s in SPECS[n] for i in range(s[1],s[2]+1)}
        if sorted(owners)!=list(range(1,len(lines)+1)):
            raise ValueError('Incomplete reviewed page structure')
        for ident,a,b,kind,unit,parent,label in SPECS[n]:
            raw=native[bounds[a-1]:bounds[b]]
            passages.append({'id':ident,'page':n,'kind':kind,
                'section':unit if not unit.startswith('P') else None,'logical_unit_id':unit,
                'label_as_printed':label,'parent_id':parent,'image':image,'native':nat,
                'native_span':span(native,bounds[a-1],bounds[b]),
                'candidate_span':span(candidate,base+bounds[a-1],base+bounds[b]),
                'native_line_start':a,'native_line_end':b,'text':' '.join(raw.decode().split()),
                'visible_markup':['bold'] if kind=='section_heading' else ['regular'] if kind=='document_title' else ['bold','blue'] if kind=='page_header' else [],
                'crop_ids':crop_links.get(ident,[]),
                'notes':['The header has separate left/right labels; normalized spacing is not a single source sentence.'] if kind=='page_header' else
                        ['Visible at the page bottom; native extraction places this before body text.'] if kind in ('page_footer','footer_date') else []})
        pages.append({'physical_page':n,'image':image,'width_px':2550,'height_px':3300,
            'native':nat,'candidate_span':span(candidate,base,base+len(native)),
            'native_lines':[{'number':i,'native_span':span(native,bounds[i-1],bounds[i]),
                'candidate_span':span(candidate,base+bounds[i-1],base+bounds[i]),
                'raw_text':line.decode(),'passage_id':owners[i],'whitespace_only':not bool(line.strip())}
                for i,line in enumerate(lines,1)],
            'checked_passage_ids':[s[0] for s in SPECS[n]],'visual_order':visual_order(n),
            'coverage':'Complete physical page including margins, header, body, all headings/enumerators and both footer fields; blank lower area on page 7 included.',
            'full_image_directly_viewed':True,'unchecked_substantive_regions':[]})
    def finding(ident: str, cat: str, ids: list[str], text: str) -> dict:
        """Build an additive finding without modifying native evidence."""
        return {'id':ident,'category':cat,'passage_ids':ids,'finding':text,'candidate_change_required':False}
    findings=[
      finding('F01','structure',[f'P{n}-FOOTER' for n in range(1,8)]+[f'P{n}-DATE' for n in range(1,8)],'Native order is header, two footer fields, then body on every page. The separate visual_order/transcript moves the footer fields after the body; native/candidate bytes remain exact.'),
      finding('F02','source_anomaly',['2.1.2-p1'],'Preserve source wording "The public notice requirements the Procedures Manual" without inserting a preposition.'),
      finding('F03','source_anomaly',['2.2.3A-text'],'Preserve the visible double period in "open to the public..".'),
      finding('F04','source_anomaly',['2.2.3B-intro'],'Preserve "in accordance with this Code the Procedures Manual" without inserting a conjunction or punctuation.'),
      finding('F05','source_anomaly',['2.2.2A-part2','2.2.2B.5-text','2.2.4B.8-text'],'These paragraphs end without a visible terminal period. Preserve "proceedings", "CRS §30-28-110", and "this LDC" as printed. CRS spelling differs from other C.R.S. citations; do not normalize.'),
      finding('F06','structure',[x for _,a,b in LINKS for x in (a,b)],'Five explicit cross-page links preserve two split paragraphs and three headings separated from their bodies. A footer or new physical page does not terminate the logical unit.'),
      finding('F07','exception_scope',['2.1.2-p2','2.1.2-p3','2.1.2-p4','2.1.3-text','2.1.4-text'],'Preserve distinct 30-day submission/comment periods, "may, but are not required to, endorse", advisory-only Master Plan treatment/Appendix A § A.1.6(B), and the substantial-change resubmittal exception. These are source statements, not current procedural advice.'),
      finding('F08','exception_scope',['2.2.1C-part1','2.2.1C-part2','2.2.1F-text','2.2.1H-text','2.2.1I-text'],'Revocation grounds continue into the hearing/proper-notice clause; delegation and express-appeal-procedure exceptions remain attached; waiver scope refers to Chapters 6, 7 and 8.'),
      finding('F09','exception_scope',['2.2.2B-intro','2.2.2B.8-text','2.2.3A-text','2.2.3B-intro','2.2.3B.1-text','2.2.4B.1-text'],'Preserve recommendation/decision distinctions, Board membership 5 and affirmative vote at least 4, prohibition on appeals to BoCC, physical-requirements-but-not-use variance scope, and Director interpretations applicable to 2 or more properties.'),
      finding('F10','date_role',[f'P{n}-DATE' for n in range(1,8)],'All seven pages visibly state "Effective 12/12/2017". This is a printed effective-date assertion, not verified adoption, present operation, or currentness. The inherited URL filename contains 2016; it is not substituted for the printed statement.'),
      finding('F11','encoding_limit',[],'No substantive native-word correction found in this visual comparison. Glyph appearance does not independently certify exact Unicode codepoints, font metrics, or invisible text outside the compared native extraction. Normalization changes whitespace only.')]
    p=prep
    provenance={'acquisition_method':'received_review_package','original_http_independently_verified':False,
        'verified_http_acquired_at':None,'supplied_url':p['source_url'],
        'supplied_final_url':p['final_url_claim'],
        'source_referral_evidence':'Inherited URL, no fresh retained official referral anchor; requested/final URL distinction is a supplied redirect claim, not a new verified HTTP event.',
        'public_headers':asset('inputs/public-headers.txt'),
        'supplied_acquisition_started_at':p['acquisition_started_at_claim'],
        'supplied_acquisition_completed_at':p['acquisition_completed_at_claim'],
        'repository_received_at':p['repository_received_at'],'canonical_path_claim':p['canonical_path_claim'],
        'canonical_record':asset('inputs/canonical-record.jsonl'),
        'selected_source_provenance':asset('inputs/source-provenance.selected.jsonl'),
        'intake_receipt':asset('inputs/intake-receipt.json'),'intake_intent':asset('inputs/intake-intent.json')}
    review={'schema_version':1,'source_id':'el-paso-ldc-chapter-2-sd011',
        'authority_id':'CO-COUNTY-EL_PASO','layer':'08_County_Authorities',
        'issuer':'El Paso County, Colorado','source_role':'Land Development Code, Chapter Two: Administration; this is not the separately referenced Procedures Manual.',
        'source':asset('inputs/original.pdf'),
        'status':'complete_candidate_aware_source_fidelity_review_pending_atlas_acceptance',
        'review_kind':'checked_passages','legal_currentness':'not_verified','answer_safe':False,
        'reviewer':'Plato','reviewed_at':now,'method':inspection['method'],'prior_exposure':exposure,
        'external_reports_consulted':False,'scope':'All seven physical pages, every native line and substantive paragraph/heading/printed enumeration; no tables, fee values, signatures or amendment strike markings appear in the reviewed pages.',
        'normalization':'Reviewed text collapses Unicode whitespace with split/join; no word, numeral, punctuation or source grammatical repair. Raw native and packaged candidate remain unchanged. Visual-order transcript relocates the two footer fields only.',
        'candidate':asset('inputs/candidate.txt'),'packet_manifest':asset('inputs/packet-manifest.json'),
        'packet_preparation':asset('inputs/packet-preparation.json'),'inspection':asset('INSPECTION.json'),
        'provenance':provenance,'pages':pages,'checked_passages':passages,
        'structural_links':[{'id':f'L{n:02}','kind':kind,'from_id':a,'to_id':b,
            'note':'Directly checked continuation into the next physical page, preserving the same source logical unit.'} for n,(kind,a,b) in enumerate(LINKS,1)],
        'dates':[{'literal':'Effective 12/12/2017','role':'source_stated_effective_date_unverified',
            'passage_ids':[f'P{n}-DATE' for n in range(1,8)],'operative_date_certified':False,
            'qualification':'All seven printed footers checked; no external amendment/adoption/current-law verification.'}],
        'findings':findings,'substantive_candidate_corrections':[],'table_count':0,
        'limitations':['Same Codex family candidate-aware internal QA; no external review or independent-family verification credited.',
            'Source text fidelity only. No currentness, adoption, amendment chain, supersession, jurisdiction applicability or legal advice certified.',
            'Exact original and derivative bindings do not repair the inherited requested/final URL and missing official referral-anchor gap. Original HTTP times/statuses remain supplied claims; actual repository receipt is separate.',
            'Copied custody is a declared selected subset, not the whole historical SD011 delivery. Earlier cap failure or omissions are not repaired.',
            'The public-header derivative is preserved as received; no new credential-removal procedure or complete original-header audit is claimed.',
            'Whitespace-normalized reviewed text is not an exact source-codepoint or typography certification. Original native bytes remain available and bound.',
            'Source preparation status and pre-intake provenance fields remain historical; this review does not modify or promote canonical inventory.']}
    save('SOURCE_QA',Review,review)
    validated=Review.model_validate_json((ROOT/'SOURCE_QA.json').read_bytes())
    (ROOT/'REVIEWED_TRANSCRIPT.md').write_bytes(transcript(validated))
    sys.stdout.write(json.dumps({'pages':len(pages),'passages':len(passages),'lines':sum(len(p['native_lines']) for p in pages)})+'\n')


if __name__=='__main__':
    main()
