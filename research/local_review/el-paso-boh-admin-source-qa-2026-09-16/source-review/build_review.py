"""Package reviewed source wording without changing its original machine evidence."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re

import jsonschema

from review_models import (
    Asset, Crop, DateStatement, Finding, Inspection, Line, Link, Page, Passage,
    Provenance, Review, Span,
)

ROOT = Path(__file__).resolve().parent


def asset(name: str) -> Asset:
    """Bind a local immutable payload."""
    raw = (ROOT / name).read_bytes()
    return Asset(path=name, sha256=sha256(raw).hexdigest(), size_bytes=len(raw))


def span(raw: bytes, start: int, end: int) -> Span:
    """Bind exact parent bytes."""
    return Span(start=start, end=end, sha256=sha256(raw[start:end]).hexdigest())


def save(name: str, model: object) -> None:
    """Publish schema before validated write-once data."""
    schema = type(model).model_json_schema()
    raw = model.model_dump_json(indent=2) + '\n'
    jsonschema.validate(json.loads(raw), schema)
    path = ROOT / name
    path.with_suffix('.schema.json').write_text(json.dumps(schema, indent=2) + '\n')
    with path.open('x') as handle:
        handle.write(raw)


def derive_passages() -> tuple[list[Page], list[Passage]]:
    """Deterministically bind the manually checked paragraph/heading structure."""
    prep = json.loads((ROOT / 'inputs/packet-preparation.json').read_bytes())
    candidate = (ROOT / 'native/candidate.txt').read_bytes()
    pages, passages = [], []
    section = None
    current_parent = None
    for number in range(1, 8):
        image = asset(f'pages/page-{number:04d}.png')
        native = asset(f'native/page-{number:04d}.native.txt')
        raw = (ROOT / native.path).read_bytes()
        lines, offset = [], 0
        for line_number, line in enumerate(raw.splitlines(keepends=True), 1):
            lines.append((line_number, offset, offset + len(line), line.decode()))
            offset += len(line)
        starts = []
        for index, (_, begin, end, text) in enumerate(lines):
            clean = text.strip()
            if not clean:
                continue
            if clean == '5/23/2012':
                starts.append((index, f'P{number}-DATE', 'footer_date', None, None, None))
            elif number == 1:
                if clean.startswith('COUNTY BOARD'):
                    continue
                labels = {'REGULATIONS': 'TITLE', 'EL PASO': 'LOCATION',
                          'Chapter': 'CHAPTER', 'Administrative': 'SUBTITLE',
                          'El Paso': 'AGENCY'}
                for prefix, suffix in labels.items():
                    if clean.startswith(prefix):
                        starts.append((index, f'P1-{suffix}', 'cover_text', None, None, None))
                        break
            elif clean.startswith('SECTION '):
                section = re.match(r'SECTION (2\.\d+):', clean).group(1)
                current_parent = section
                starts.append((index, section, 'section_heading', section, None, None))
            elif re.match(r'^[A-P]\.\s', clean):
                label = clean[0]
                current_parent = f'{section}{label}'
                starts.append((index, current_parent, 'paragraph', section, label+'.', section))
            elif re.match(r'^[1-5]\.\s', clean):
                label = clean[0]
                starts.append((index, f'2.10F.{label}', 'paragraph', '2.10', label+'.', '2.10F'))
            elif clean.startswith('The regulations of the El Paso County Board') and section == '2.3':
                starts.append((index, '2.3-TEXT', 'paragraph', section, None, section))
            elif clean.startswith('It is the intention of the Board') and section == '2.8':
                starts.append((index, '2.8-TEXT', 'paragraph', section, None, section))
            elif clean.startswith('The Board of Health may adopt a temporary'):
                starts.append((index, '2.11-UNLETTERED', 'paragraph', '2.11', None, '2.11'))
        page_passages = []
        assignment = {}
        base = prep['native_pages'][number-1]['candidate_start']
        for pos, (index, ident, kind, sec, label, parent) in enumerate(starts):
            stop = starts[pos+1][0] if pos+1 < len(starts) else len(lines)
            while stop > index and not lines[stop-1][3].strip():
                stop -= 1
            begin, end = lines[index][1], lines[stop-1][2]
            text = ' '.join(raw[begin:end].decode().split())
            for line_number, _, _, _ in lines[index:stop]:
                assignment[line_number] = ident
            markup = ['bold', 'underlined'] if kind == 'section_heading' else []
            if ident in ['P1-TITLE', 'P1-LOCATION', 'P1-AGENCY']:
                markup = ['bold']
            if ident in ['P1-CHAPTER', 'P1-SUBTITLE']:
                markup = ['bold', 'underlined']
            crops = {'2.4': ['p2-affect'], '2.4A': ['p2-affect'], '2.4B': ['p2-affect'],
                     '2.7F': ['p4-definition'], '2.10F': ['p5-certificate'],
                     '2.11O': ['p7-final-procedure'], '2.11P': ['p7-final-procedure'],
                     '2.11-UNLETTERED': ['p7-final-procedure']}.get(ident, [])
            notes = []
            if ident == '2.4A':
                notes = ['Source visibly says affect, not effect; retained without repair.']
            if ident == '2.7F':
                notes = ['Source visibly spells EXECITOVE; F continues Section 2.7 across pages 3–4.']
            if ident == '2.10F':
                notes = ['Source visibly says in compliance. Do not insert non- or otherwise repair the clause.']
            if ident == '2.11-UNLETTERED':
                notes = ['No letter Q is visibly printed. This separate left-aligned paragraph follows P.']
            passage = Passage(id=ident, page=number, kind=kind, section=sec,
                              label_as_printed=label, parent_id=parent, image=image, native=native,
                              native_span=span(raw, begin, end),
                              candidate_span=span(candidate, base+begin, base+end),
                              native_line_start=lines[index][0], native_line_end=lines[stop-1][0],
                              text=text, visible_markup=markup, crop_ids=crops, notes=notes)
            passages.append(passage); page_passages.append(passage.id)
        native_lines = []
        for line_number, begin, end, text in lines:
            if text.strip() and line_number not in assignment:
                raise ValueError('Nonempty native line not assigned to reviewed passage')
            native_lines.append(Line(number=line_number, native_span=span(raw, begin, end),
                                     candidate_span=span(candidate, base+begin, base+end),
                                     raw_text=text, passage_id=assignment.get(line_number),
                                     whitespace_only=not bool(text.strip())))
        coverage = {
            1: 'Complete cover, title, issuer and unlabelled footer date; no table or signature block.',
            2: 'Sections 2.1–2.4, all lettered items and unlettered Section 2.3 body; footer.',
            3: 'Sections 2.5 A–H, 2.6 A–B, 2.7 A–E; footer.',
            4: 'Section 2.7 F continuation; 2.8 body; 2.9 A–B; 2.10 A–E; footer.',
            5: 'Section 2.10 F with five nested items; Section 2.11 A and exclusions; footer.',
            6: 'Section 2.11 B–L continuation, complete notices/hearing provisions; footer.',
            7: 'Section 2.11 M–P and separate unlettered emergency paragraph; footer and blank remainder.',
        }[number]
        pages.append(Page(physical_page=number, image=image, width_px=2550, height_px=3300,
                          native=native, candidate_span=span(candidate, base, base+len(raw)),
                          native_lines=native_lines, checked_passage_ids=page_passages,
                          coverage=coverage, full_image_directly_viewed=True,
                          unchecked_substantive_regions=[]))
    return pages, passages


def main() -> None:
    """Write the declared complete review and a readable normalized transcript."""
    recipes = json.loads((ROOT/'crop-recipes.json').read_bytes())
    inspection = Inspection(reviewer='Plato', recorded_at=datetime.now(timezone.utc),
        method='direct_view_image_full_pages_then_native_comparison_and_crops',
        full_pages=[asset(f'pages/page-{n:04d}.png') for n in range(1,8)],
        crops=[Crop.model_validate(x) for x in recipes],
        full_pages_displayed_size='view_image displayed all seven at 1376×1780 from 2550×3300 originals; four focused exact-pixel crops also directly viewed.',
        prior_exposure='Prepared this packet and read inventory/custody metadata. All seven full images were then directly viewed before opening the native text during this review. This is candidate-aware internal review, not blind external review.',
        native_candidate_read_after_full_images=True, external_reports_consulted=False,
        chronology_limit='Recorded after actual tool use; individual view timestamps were not captured. This attestation does not authenticate external bot chronology or independent model families.')
    save('INSPECTION.json', inspection)
    pages, passages = derive_passages()
    links = [Link(id='L1',kind='enumeration_continues',from_id='2.7E',to_id='2.7F',
                  note='Definitions A–E on page 3 continue with F at top of page 4.'),
             Link(id='L2',kind='enumeration_continues',from_id='2.10E',to_id='2.10F',
                  note='Compliance A–E on page 4 continue with F at top of page 5.'),
             Link(id='L3',kind='enumeration_continues',from_id='2.11A',to_id='2.11B',
                  note='Administrative procedures continue from page 5 to page 6.'),
             Link(id='L4',kind='enumeration_continues',from_id='2.11L',to_id='2.11M',
                  note='Administrative procedures continue from page 6 to page 7.')]
    links += [Link(id=f'L{n+4}',kind='nested_under',from_id='2.10F',to_id=f'2.10F.{n}',
                   note='Indented numbered item is subordinate to the certificate paragraph F.') for n in range(1,6)]
    findings = [
        ('F01','source_anomaly',['2.4A'],'The visible source and native text both say general and permanent affect. No correction to effect.'),
        ('F02','source_anomaly',['2.7F'],'The visible source and native both spell EXECITOVE DIRECTOR. No silent repair to EXECUTIVE.'),
        ('F03','source_anomaly',['2.10F'],'The certificate clause says said real property in compliance with any public health law. Preserve the wording despite possible semantic awkwardness.'),
        ('F04','structure',['2.11P','2.11-UNLETTERED'],'The emergency paragraph is unlettered, left-aligned separately after P. Do not invent Q or merge it into P.'),
        ('F05','exception_scope',['2.9A','2.9B'],'The January 21, 2009 repeal statement is expressly except as provided below; B retains specified actions and their underlying rules for those actions. No general repeal conclusion here.'),
        ('F06','exception_scope',['2.10F.1','2.10F.2'],'Item 1 states thirty (30) calendar days prior; item 2 states thirty (30) days after mailing or posting and may, but is not required. These remain separate clauses; no deadline arithmetic.'),
        ('F07','exception_scope',['2.11A','2.11O','2.11P','2.11-UNLETTERED'],'Preserve the listed exclusions in A, unless otherwise provided in O, if feasible in P, and all emergency conditions and three (3) months / shorter-period qualifications.'),
        ('F08','extraction_whitespace',['2.10C'],'The native extraction has many leading whitespace-only lines and extra blank lines within 2.10C. Every raw byte is preserved; reviewed text collapses whitespace only.'),
        ('F09','date_role',['P1-DATE','P2-DATE','P3-DATE','P4-DATE','P5-DATE','P6-DATE','P7-DATE'],'5/23/2012 is a repeated unlabelled footer date. It is not certified here as adoption, publication, amendment or effective date.'),
        ('F10','encoding_limit',[],'The visual review supports readable wording and meaning-bearing punctuation. Native Unicode code points, exact typographic whitespace and underline pixel extents are not independently certified from pixels.'),
    ]
    provenance=json.loads((ROOT/'inputs/source-provenance.selected.jsonl').read_bytes())
    record=json.loads((ROOT/'inputs/canonical-record.jsonl').read_bytes())
    dates=[DateStatement(literal='5/23/2012',role='unlabelled_repeated_footer_date',
                        passage_ids=[f'P{n}-DATE' for n in range(1,8)],operative_date_certified=False,
                        qualification='Visible on all seven pages; source role beyond repeated footer is not identified.'),
           DateStatement(literal='January 21, 2009',role='stated_prior_regulation_cutoff_in_repeal_clause',
                         passage_ids=['2.9A','2.9B'],operative_date_certified=False,
                         qualification='Read with the express exception and retained-action clause; not the date this document was adopted.')]
    review=Review(schema_version=1,source_id='el-paso-boh-admin-regulations-sd011',
        authority_id='CO-COUNTY-EL_PASO',layer='08_County_Authorities',
        issuer='El Paso County Board of Health; cover also names El Paso County Public Health.',
        source_role='Chapter 2 administrative regulations, as printed; no operative chain verified.',
        source=asset('inputs/original.pdf'),
        status='complete_candidate_aware_source_fidelity_review_pending_atlas_acceptance',
        review_kind='checked_passages',legal_currentness='not_verified',answer_safe=False,
        reviewer='Plato',reviewed_at=datetime.now(timezone.utc),
        method='Direct view_image of all seven full Poppler page renders, then comparison of every substantive native passage and four focused crops. Internal candidate-aware source-fidelity review.',
        prior_exposure=inspection.prior_exposure,external_reports_consulted=False,
        scope='Complete seven physical pages: cover, Sections 2.1–2.11, all enumerated/nested and unlettered paragraphs, source footer dates and heading markup. No tables present.',
        normalization='Passage text uses a single ASCII space for runs of native whitespace; all wording, punctuation and source anomalies retained. Exact unaltered native files, line bytes and candidate offsets are separately preserved. No source text corrections made.',
        candidate=asset('native/candidate.txt'),packet_manifest=asset('inputs/packet-manifest.json'),
        packet_preparation=asset('inputs/packet-preparation.json'),inspection=asset('INSPECTION.json'),
        provenance=Provenance(acquisition_method='received_review_package',
            original_http_independently_verified=False,verified_http_acquired_at=None,
            supplied_url=provenance['requested_url_claim'],
            supplied_acquisition_started_at=datetime.fromisoformat(provenance['acquisition_started_at_claim'].replace('Z','+00:00')),
            supplied_acquisition_completed_at=datetime.fromisoformat(provenance['acquisition_completed_at_claim'].replace('Z','+00:00')),
            repository_received_at=datetime.fromisoformat(record['received_at'].replace('Z','+00:00')),
            canonical_path_claim=record['archive_path'],canonical_record=asset('inputs/canonical-record.jsonl'),
            selected_source_provenance=asset('inputs/source-provenance.selected.jsonl'),
            intake_receipt=asset('inputs/intake-receipt.json'),intake_intent=asset('inputs/intake-intent.json')),
        pages=pages,checked_passages=passages,structural_links=links,dates=dates,
        findings=[Finding(id=i,category=c,passage_ids=ids,finding=t,candidate_change_required=False)
                  for i,c,ids,t in findings],substantive_candidate_corrections=[],table_count=0,
        limitations=['Candidate-aware direct review by Plato, who also prepared the packet; not blind, not an independent model-family experiment.',
                     'No Ebenezer, new Sherlock, or root direct-review findings consulted for this review.',
                     'Source/currentness/adoption chain, subsequent amendments, applicability and cited statute currency are not verified.',
                     'No signatures or handwritten identity authentication asserted. Heading underlines are typographic, not amendment effect.',
                     'No fee arithmetic, deadline calculation, current office-address validation or cross-version comparison performed.',
                     'Original HTTP acquisition remains a supplied claim; actual repository intake time is separate. Copied custody is a selected subset, not a new full upstream audit.',
                     'Mechanical verifier proves byte/structure bindings, not the truth of the visual-review attestation or legal content.'])
    save('SOURCE_QA.json',review)
    transcript=['# Reviewed source transcript\n','Candidate-aware direct image review by Plato. Whitespace normalized; original native bytes unchanged. No legal currentness certification.\n']
    for page in pages:
        transcript.append(f'\n## Physical page {page.physical_page}\n')
        for passage in passages:
            if passage.page==page.physical_page:
                transcript.append(f'\n### {passage.id}\n\n{passage.text}\n')
    (ROOT/'REVIEWED_TRANSCRIPT.md').write_text(''.join(transcript))
    print(f'{len(passages)} checked passages; {sum(len(p.native_lines) for p in pages)} native lines; all seven pages.')


if __name__=='__main__':
    main()
