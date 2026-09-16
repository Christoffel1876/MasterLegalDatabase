"""Write the first validated source-QA record after direct image inspections."""
import json
from datetime import datetime, timezone
from pathlib import Path
from build_review import ROOT, PACKET, SOURCE, CANDIDATE, asset, derive
from crop_recipes import RECIPES
from review_models import Asset, Crop, QA


def write_new(path: Path, content: bytes) -> None:
    """Publish a new file only, using a temporary sibling."""
    assert not path.exists(), path
    temp = path.with_suffix(path.suffix + '.tmp')
    with temp.open('xb') as stream:
        stream.write(content)
    temp.rename(path)


def main() -> None:
    """Bind directly reviewed source and exact structural records."""
    now = datetime.now(timezone.utc).isoformat()
    schema = QA.model_json_schema()
    write_new(ROOT / 'SOURCE_QA.schema.json', (json.dumps(schema,indent=2)+'\n').encode())
    lines, rows, paragraphs = derive()
    manifest = json.loads((PACKET/'MANIFEST.json').read_bytes())
    assets = [Asset.model_validate(a) for a in manifest['files'] if (PACKET/a['path']).is_file()]
    assets += [asset(PACKET/name,PACKET) for name in ['MANIFEST.json','MANIFEST.schema.json'] if name not in {a.path for a in assets}]
    prep = json.loads((PACKET/'04-verification/PREPARATION.json').read_bytes())
    qa = QA(schema_version='cs-code-fees-qa-1',
        source_id='colorado-springs-code-services-fees-2015-atlas-directed',
        authority_id='CO-MUNICIPAL-COLORADO_SPRINGS', review_kind='checked_tables',
        status='complete_source_fidelity_review_pending_atlas_acceptance',
        legal_currentness='not_verified',answer_safe=False,source_year_as_printed='2015',
        adoption_date=None,effective_date=None,packet_root_claim=str(PACKET),
        canonical_original_claim=prep['canonical_path_claim'],assets=assets,
        source_sha256=asset(PACKET/SOURCE,PACKET).sha256,
        candidate_sha256=asset(PACKET/CANDIDATE,PACKET).sha256,
        full_pages_inspected=list(range(1,8)),
        full_page_inspection_interval=['2026-09-14T20:25:45Z','2026-09-14T20:27:23Z'],
        method='Plato candidate-aware internal direct review. Prepared this packet and previously read metadata concerns. All seven full PNGs were directly inspected before reading the candidate in this QA turn; the native text was then compared to the images and targeted pixel crops. No external Ebenezer report consulted. Full-page interval is the bounded assignment-to-completion interval, not authenticated per-image timing. Every native byte remains unchanged; physical display associations are additive.',
        lines=lines,rows=rows,paragraphs=paragraphs,
        crops=[Crop(asset=asset(ROOT/'crops'/f'{name}.png',ROOT),page=pn,pixel_box=box,
                    inspected_at=now) for name,pn,box in RECIPES],
        findings=[
            'F01: P1-L000 through P1-L005 encode white 124, 82, 86 and dollar symbols. They are not visible in the source page; they are retained as extraction-only lines, never fee rows.',
            'F02: P2-L082/P3-L082/P4-L094/P5-L209/P6-L097 encode white 2015 Proposed changes. Full images and corresponding pixel crops do not display that text. Neither those strings nor the visible 2015 title establish adoption, effectiveness or currentness.',
            'F03: Page 7 native order lists all ten headings first and inserts Property Condition body before Fire Watch. D1-D10 associate each exact body with its visible heading and physical position. No body is silently reassigned by sequence.',
            'F04: Page 2 R2-025 and R2-026 are two fee associations within the same M up-to-10,000-square-foot physical row: $296 and additional fuel dispensing $506. R2-029 literally says M - Greater through 100,001 sq. ft.; thresholds are not repaired.',
            'F05: Page 3 construction HP9 and HP19 bulk charges differ from page 5 operational amounts and ranges. Separate rows preserve every printed number; no equivalence or arithmetic is inferred. Source non-flamable and galllons spellings remain exact.',
            'F06: Page 5 has 53 two-column fee-bearing rows. Annual Revocable and Prescribed remain separate. n/a, no charge and missing fee cells in category headings are not converted to zero. Special events and fairs has no printed OP3 prefix; none is supplied.',
            'F07: Page 5 HP25 literally reads Spaying/dipping operations; page 3 reads Spraying/dipping operations. The page 5 *Hot Work Operations temporary-burn-permit condition and **Abandonments approval note are preserved.',
            'F08: Page 6 Medical Squad (Two Person) Do we need to assign a unit type is visibly printed as the category heading. Its four on-duty/overtime rate associations remain $272/$60/$304/$93. The drafting question is not silently removed or answered.',
            'F09: Page 3 reinspection condition and page 6 condition are preserved separately: page 6 includes or completed. Both keep the same-contractor/same-project limitation and hourly clauses; no bare $123 row is detached from context.',
            'F10: All 197 fee associations preserve literal strings, including closeout Annual Operational Permit fee, 1.5 x original plan review fee, no charge and n/c. Page 6 First Hour Free of Charge is a context line without an invented fee-column value.',
            'F11: Page 7 source headings say Assesments; its text includes bon fires and environment site assessments. Native spelling is retained. Dot-leader counts, exact source font codepoints and semantic legal sufficiency are not certified.',
        ],
        limitations=[
            'Review concerns only this complete seven-page preserved English source. It does not establish current law, adoption, effective date, supersession or equivalence to another schedule.',
            'Actual September 12 HTTP completion and later repository received_at are retained in the linked preparation/custody records and remain distinct from this review date.',
            'The portable inputs directory contains an exact selected subset: original PDF, all seven full PNGs, native/candidate bytes, identities, preparation and selected custody. The copied packet manifest describes a larger upstream package: unselected files were not copied or independently revalidated here. Packet historical PREPARED_NOT_DISPATCHED status remains unchanged; root reports separate later activation.',
            'Every row carries all context records on its page plus all ten definitions. This conservative context envelope is not a claim that every definition applies to every row; consumers must retain these records rather than calculate a fee.',
            'The 197 count is fee associations, not 197 distinct legal fees or physical grid rows. Page 2 nested fuel dispensing is separately addressable; page 4 closeout is a textual reference. Category-only rows and all remaining text remain available in the exhaustive 670-line record.',
            '14 crops were directly displayed; two initial crops named bulk-anomalies and m-threshold cover neighboring material rather than the full intended row. They remain unchanged and are not proof for the missed text. Complete page inspection and a separate complete bulk crop support the findings.',
            'Inspection timestamps for crops record this receipt creation after actual display, not independently authenticated tool chronology. Source title visibility is established; no ownership or signature authenticity beyond printed issuer is asserted.',
        ])
    write_new(ROOT/'SOURCE_QA.json',(qa.model_dump_json(indent=2)+'\n').encode())
    by = {line.id:line for line in qa.lines}
    def text(ids: list[str]) -> str:
        return ' '.join(by[i].text.strip() for i in ids)
    md = ['---','reviewer: Plato','status: source_fidelity_only','legal_currentness: not_verified','---',
          '# Colorado Springs Code Services: reviewed source associations','',qa.method,'',
          'All amounts and units below are literal source text. Contexts and definitions accompany the rows. No fee totals are computed.','']
    for page in range(1,8):
        md += [f'## Physical page {page}','']
        if page in [1,7]:
            if page == 1:
                md += [l.text.strip() for l in sorted(qa.lines,key=lambda x:(x.bbox[1],x.bbox[0])) if l.page==1 and l.visibility=='visible']
            else:
                for p in qa.paragraphs:
                    if p.page==7: md += [f'### {p.id}: {text(p.heading_refs)}','',text(p.body_refs),'']
        else:
            for row in [r for r in qa.rows if r.page==page]:
                md += [f'### {row.id}','',f'Category: {text(row.group_refs)}','',
                       f'Label: {text(row.label_refs)}','']
                for name,cell in zip(row.columns,row.fee_refs):md += [f'- {name}: {text(cell)}']
                md += ['',f'Context links: {", ".join(row.context_refs)}','']
            for p in [p for p in qa.paragraphs if p.page==page]:
                md += [f'### {p.id}','',text(p.body_refs),'']
    md += ['## Source observations',''] + [f'- {f}' for f in qa.findings]
    md += ['','## Limits',''] + [f'- {f}' for f in qa.limitations]
    write_new(ROOT/'REVIEWED_TRANSCRIPT.md',('\n'.join(md)+'\n').encode())


if __name__ == '__main__':
    main()
