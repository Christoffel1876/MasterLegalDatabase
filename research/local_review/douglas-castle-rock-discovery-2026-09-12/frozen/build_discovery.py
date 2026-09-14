"""Build a strict finite-discovery report from already retained evidence only."""
from __future__ import annotations
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
from capture import Event, Parsed, HERE, Ref, ref, save, sha, write
from review_models import (
    ChecklistRow, Comparison, DiscoveredLink, Discovery, LegacyMatch, LinkObservation,
    Priority, RawSizeCandidate, Referral, Snippet, Statement, ViewedPage,
)

COUNTY='CO-COUNTY-DOUGLAS'
TOWN='CO-MUNICIPAL-CASTLE_ROCK'
CATS=['identity_service_area','codified_rules','adopted_changes','land_use_zoning',
      'building_fire','permits_licenses','fees','taxes','health_environment',
      'roads_utilities','enforcement_appeals','policies_guidance']


def exact_snippet(events: dict[str, Event], eid: str, page: int | None,
                  needle: str) -> Snippet:
    """Bind one exact text line containing the requested source phrase."""
    if page is not None:
        path=HERE/'pdf-evidence'/eid/f'page-{page:04d}.native.txt'
        method='unaltered native PDF extraction'
    else:
        path=HERE/'readable'/f'{eid}.txt'
        method='HTML text derivative'
    body=path.read_bytes()
    text=body.decode('utf-8')
    lines=[line for line in text.splitlines(keepends=True) if needle in line]
    if not lines:
        raise ValueError(f'Missing exact source phrase {eid}: {needle}')
    chosen=lines[0]
    raw=chosen.encode('utf-8');start=body.index(raw)
    return Snippet(original=events[eid].body,text_file=ref(path),physical_page=page,
                   start_byte=start,end_byte=start+len(raw),text=chosen,text_sha256=sha(raw),
                   method=method)


def statement(events: dict[str, Event], eid: str, page: int | None, needle: str,
              kind: str, value: str, qualification: str) -> Statement:
    """Preserve a source-stated date or visible anomaly without legal certification."""
    return Statement(kind=kind,value=value,evidence=exact_snippet(events,eid,page,needle),
                     qualification=qualification)


def main() -> None:
    """Assemble exact references, all attempted events and explicit unresolved categories."""
    events={p.parent.name:Event.model_validate_json(p.read_bytes())
            for p in sorted((HERE/'events').glob('E*/event.json'))}
    assert len(events)==31
    parsed={p.parent.name:Parsed.model_validate_json(p.read_bytes())
            for p in sorted((HERE/'events').glob('E*/parsed.json'))}
    for eid,p in parsed.items():
        write(HERE/'readable'/f'{eid}.txt',p.text.encode())
    chain={
        1:('registry_seed',None,'county_douglas_homepage'),
        2:('dns_route_retry',1,None),3:('redirect',2,None),
        4:('registry_seed',None,'municipal_castle_rock_code_central'),
        5:('anchor',3,None),6:('anchor',3,None),7:('anchor',4,None),
        8:('anchor',4,None),9:('redirect',8,None),10:('anchor',5,None),
        11:('anchor',5,None),12:('anchor',6,None),13:('anchor',7,None),
        14:('registry_seed',None,'county_douglas_zoning_resolution'),
        15:('redirect',11,None),16:('redirect',14,None),17:('anchor',12,None),
        18:('anchor',10,None),19:('anchor',10,None),
        20:('registry_seed',None,'municipal_castle_rock_fire'),
        21:('anchor',4,None),22:('anchor',4,None),23:('redirect',16,None),
        24:('redirect',22,None),25:('anchor',21,None),26:('anchor',10,None),
        27:('anchor',20,None),28:('redirect',25,None),29:('anchor',24,None),
        30:('anchor',3,None),31:('redirect',29,None),
    }
    referrals=[Referral(event_id=f'E{n:03d}',type=v[0],
                        parent_event=f'E{v[1]:03d}' if v[1] else None,
                        seed_source_id=v[2]) for n,v in chain.items()]
    pdf={p.parent.name:json.loads(p.read_bytes())
         for p in sorted((HERE/'pdf-evidence').glob('E*/STRUCTURE.json'))}
    definitions=[
        ('E018',COUNTY,'ATTACHEMENT A: Code amendments bundle','code_amendments_attachment',
         ['building_fire','adopted_changes'],
         ['108-page bundle is retained; this is not the full incorporated ICC model codes.',
          'Catalog July 2026 adoption/effect statements are separate from an executed instrument.',
          'Catalog refers to 2023 NEC; bundle contents names 2026 NEC. Resolve version chain.']),
        ('E015',COUNTY,'Building Division Fees','fee_schedule_historical_printed_date',
         ['fees','permits_licenses'],
         ['Official permit page currently links this four-page schedule bearing 6/29/2018.',
          'Current legal applicability and reconciliation with the newly posted code bundle remain open.']),
        ('E017',COUNTY,'Environmental Health Fee Schedule','fee_schedule_mixed_authorities',
         ['fees','health_environment'],
         ['County Board of Health and state-legislation fee tables have different stated effective dates.',
          'Do not turn the 2026 column label into one adoption/effective date.',
          'Keep units, OWTS/state-charge footnotes and blank penalty amount cells; no totals calculated.']),
        ('E019',COUNTY,'Ordinance No. O-026-004: 2024 International Fire Code','unsigned_instrument_version',
         ['adopted_changes','building_fire','enforcement_appeals'],
         ['Page 2 leaves final adoption date and execution lines blank, despite catalog adoption claim.',
          'Preserve exemptions and county/district enforcement distinctions; no executed status certified.']),
        ('E026',COUNTY,'Ordinance No. O-026-XXX: alternate 2024 Fire Code attachment','placeholder_draft_version',
         ['adopted_changes','building_fire'],
         ['Distinct bytes from E019; first page and appendix retain O-026-XXX placeholder.',
          'Final adoption and execution lines blank; do not merge this draft into E019 or call it enacted.']),
        ('E023',COUNTY,'County code provider reached from legacy Section 1 URL','access_denial_body',
         ['codified_rules','land_use_zoning'],
         ['Official county route redirects to this provider; HTTP 403 response retained.',
          'No county code text was obtained and no access-denial retry was made.']),
        ('E013',TOWN,'Town of Castle Rock Development Services Fee Schedules','fee_schedule',
         ['fees','permits_licenses','building_fire'],
         ['25 pages with building, impact/system development, ROW, site development and fire fees.',
          'Cover effective date is a source statement; full table transcription and adoption chain unreviewed.',
          'Docusign envelope text does not certify signer identity or completed execution.']),
        ('E028',TOWN,'Development Procedures Manual','procedural_guidance_manual',
         ['land_use_zoning','permits_licenses','enforcement_appeals','policies_guidance'],
         ['57 pages; sampled overview bears Updated: May 21, 2015.',
          'Manual works with municipal code; it is not complete Titles 15, 16, 17 or zoning history.']),
        ('E031',TOWN,'Transportation Design Criteria Manual','technical_manual',
         ['roads_utilities','policies_guidance'],
         ['186 pages; inner title states April 2023.',
          'Catalog says technical manuals are adopted by reference; adopting instrument not recovered.']),
        ('E009',TOWN,'Adopted Building Codes','official_adoption_summary',
         ['building_fire','adopted_changes'],
         ['Government summary lists model-code editions and two summer 2026 dates.',
          'Summary is not an adoption ordinance or the full incorporated code text.']),
        ('E020',TOWN,'Permits and Inspections: Castle Rock Fire and Rescue','official_permit_guidance',
         ['building_fire','permits_licenses'],
         ['Page says the Fire and Life Safety Division page is being updated.',
          'Town fire/rescue guidance is distinct from county fire and metropolitan district authorities.']),
        ('E027',TOWN,'Town IFC amendments: official Municode referral','application_shell',
         ['codified_rules','building_fire'],
         ['HTTP 200 delivered a 6 KB application shell titled Municode Library.',
          'No substantive municipal code chapter was present in retained response; no hidden API used.']),
    ]
    priorities=[]
    for n,(eid,owner,title,role,cats,limits) in enumerate(definitions,1):
        priorities.append(Priority(priority_id=f'DCR-{n:02d}',authority_id=owner,title=title,
            event_id=eid,url=events[eid].requested_url,body=events[eid].body,evidence_role=role,
            substantive_text_retained=eid not in {'E023','E027'},
            pdf_pages=pdf[eid]['page_count'] if eid in pdf else None,categories=cats,
            source_statements=[],limits=limits))
    statements={
        'E018':[('E018',1,'ATTACHEMENT A','source_title_spelling','ATTACHEMENT A',
                 'Source spelling preserved.'),
                ('E018',1,'2026 National Electrical Code','edition_label','2026 NEC',
                 'Contents label differs from the 2023 NEC wording on county catalog; no repair inferred.'),
                ('E010',None,'Building Codes - Adopted','catalog_adoption_and_effect_claim',
                 'July 1, 2026; NEC effective January 1, 2027',
                 'Copied county HTML claim only; not independent instrument verification.')],
        'E015':[('E015',1,'6/29/2018','unlabeled_printed_date','2018-06-29',
                 'Printed footer date; not assumed adoption, expiration or current effectiveness.')],
        'E017':[('E017',1,'November','effective_as_stated_county_fee_table','2025-11-01',
                 'County Board of Health fee table only; operative legal status unverified.'),
                ('E017',1,'September','effective_as_stated_state_fee_table','2025-09-01',
                 'State-legislation fee table only; not a separate county enactment.')],
        'E019':[('E019',2,'FIRST READING','first_reading_as_stated','2026-06-09',
                 'Final adoption line is blank.'),
                ('E019',2,'ADOPTED ON SECOND','blank_final_adoption','blank',
                 'Direct full-page image check confirms blank date and execution lines.'),
                ('E010',None,'Adopted July 14','catalog_adoption_claim','2026-07-14',
                 'Catalog says adopted; linked PDF lacks completed final adoption/execution fields.')],
        'E026':[('E026',1,'O-026-XXX','placeholder_number','O-026-XXX',
                 'Visible first-page placeholder; not a completed ordinance identifier.'),
                ('E026',2,'ADOPTED ON SECOND','blank_final_adoption','blank',
                 'Visible blank date and execution lines.')],
        'E013':[('E013',1,'Effective July 1','effective_as_stated','2026-07-01',
                 'Cover statement only; no current-law certification.')],
        'E028':[('E028',2,'Updated:','updated_as_stated','2015-05-21',
                 'Sampled overview footer; no claim all later amendments are incorporated.')],
        'E031':[('E031',3,'April 2023','publication_or_edition_label','2023-04',
                 'Inner title date; not an independently established effective date.')],
        'E009':[('E009',None,'Building Codes - Adopted','summary_effective_dates',
                 'Building amendments June 30, 2026; wildfire code July 1, 2026',
                 'Official summary only; adopting ordinance chain remains open.')],
    }
    for row in priorities:
        row.source_statements=[statement(events,*args) for args in statements.get(row.event_id,[])]
    county=[
        ('candidate_found',['E003','E005'],'government_identity_and_scope_summary',True,
         'County permit page expressly addresses unincorporated Douglas County; full service-area mapping absent.'),
        ('access_blocked',['E014','E016','E023'],'official_code_referral_to_403',False,
         'Legacy Section 1 route now redirects to blocked county code provider; no code text retained.'),
        ('candidate_found',['E010','E018','E019','E026'],'attachments_and_catalog_assertions',True,
         'Unexecuted/placeholder fire versions and catalog adoption assertions remain distinct.'),
        ('access_blocked',['E014','E016','E023'],'official_zoning_referral_to_403',False,
         'No actual zoning or subdivision code acquired in this bounded pass.'),
        ('candidate_found',['E010','E018','E019','E026'],'code_amendment_sources',True,
         'Retained local amendments and draft fire instruments; complete incorporated codes not obtained.'),
        ('candidate_found',['E005'],'official_permit_guidance',True,
         'Building guidance captured, not all county permit or licensing rules.'),
        ('candidate_found',['E015','E017'],'building_and_environmental_fee_schedules',True,
         'Separate old printed date and mixed-authority 2026 fee tables; no complete county fee claim.'),
        ('not_searched',[],'unopened_tax_navigation_leads',False,
         'County tax sources not opened; town use-tax description is not independent county tax verification.'),
        ('candidate_found',['E006','E012','E017'],'health_catalog_and_fee_schedule',True,
         'Fee evidence only, not full county health regulations or OWTS requirements.'),
        ('not_searched',[],'unopened_public_works_leads',False,
         'Road maintenance navigation exists; county engineering/road standards were not acquired.'),
        ('candidate_found',['E019','E026'],'draft_fire_enforcement_clauses',True,
         'Draft county text names district/department enforcement roles; adopted enforcement chain unresolved.'),
        ('candidate_found',['E005','E030'],'permit_guidance_and_sheriff_notice',True,
         'Stage 1 restrictions notice is a county summary; underlying signed order was not collected.'),
    ]
    town=[
        ('candidate_found',['E004','E007','E013'],'town_identity_and_scope_statements',True,
         'Town sources identify Castle Rock; do not infer county/district jurisdiction from shared address.'),
        ('access_blocked',['E004','E020','E027'],'official_provider_application_shell',False,
         'HTTP 200 shell contains no code text; this is not a publisher HTTP denial.'),
        ('candidate_found',['E009'],'official_adoption_summary',True,
         'Summary gives dates and editions; final adoption instruments not recovered.'),
        ('candidate_found',['E021','E028'],'development_procedure_manual',True,
         'Manual covers development/zoning procedures; complete municipal zoning code not captured.'),
        ('candidate_found',['E009','E020'],'official_code_and_fire_summaries',True,
         'Model-code lists and fire guidance captured; amendments chapter remains an empty shell.'),
        ('candidate_found',['E020','E028'],'permit_and_procedure_guidance',True,
         'Multiple processes described; this is not a complete licensing inventory.'),
        ('candidate_found',['E007','E013'],'development_services_fee_schedule',True,
         'One complete 25-page downloaded schedule; tables and adoption chain await full review.'),
        ('candidate_found',['E007'],'official_use_tax_guidance',True,
         'Town fee page distinguishes municipal and county portions; no tax ordinance acquired.'),
        ('candidate_found',['E024'],'technical_manual_catalog',False,
         'TESC/stormwater and related manual URLs discovered, but their substantive texts unopened.'),
        ('candidate_found',['E024','E031'],'transportation_manual_and_other_manual_referrals',True,
         'Transportation manual retained; water/wastewater/stormwater manuals remain unopened.'),
        ('candidate_found',['E028'],'procedure_manual',True,
         'Manual contains variance/process chapters; no current operative appeals-code determination.'),
        ('candidate_found',['E021','E028','E024','E031'],'procedural_and_technical_manuals',True,
         'Edition/update dates and referenced law remain separately qualified.'),
    ]
    checklist=[]
    for owner,rows in [(COUNTY,county),(TOWN,town)]:
        for cat,values in zip(CATS,rows):
            status,eids,role,retained,qual=values
            checklist.append(ChecklistRow(authority_id=owner,category=cat,status=status,
                event_ids=eids,evidence_role=role,substantive_text_retained=retained,
                qualification=qual))
    seen={}
    for eid,p in parsed.items():
        for i,link in enumerate(p.links):
            seen.setdefault(link.url,[]).append(LinkObservation(event_id=eid,
                anchor_index_zero_based=i,href=link.href,label=link.label))
    links=[]
    for url,observations in sorted(seen.items()):
        opened=[e.event_id for e in events.values() if e.requested_url==url]
        parsed_url=urlsplit(url)
        public=(parsed_url.scheme=='https' and not parsed_url.fragment and
                not any(x in parsed_url.path.lower() for x in ['/admin','/login','/email','/cdn-cgi']))
        disposition='opened' if opened else 'unopened' if public else 'not_public_https_source_target'
        links.append(DiscoveredLink(url=url,observations=observations,event_ids_opened=opened,
            disposition=disposition,reason='Exact captured anchor; no authority inference for external hosts. '
            'Unopened URLs are leads only; no requests are implied.'))
    viewed={'E013':[1,2],'E015':[1],'E017':[1],'E018':[1],'E019':[1,2],
            'E026':[1,2,11],'E028':[1,2],'E031':[1,3]}
    views=[]
    for eid,pages in viewed.items():
        for page in pages:
            path=HERE/'pdf-evidence'/eid/f'page-{page:04d}.png'
            if not path.exists():path=path.with_name(path.stem+'.additional.png')
            views.append(ViewedPage(event_id=eid,physical_page=page,source=events[eid].body,
                image=ref(path),render_dpi=150,
                scope='source identity/date/layout sampling; not complete transcription review'))
    ordered=list(events.values());counts=Counter(str(e.http_status) for e in ordered if e.http_status)
    report=Discovery(recorded_at=datetime.now(timezone.utc),
        status='completed_pending_root_verification',legal_currentness='not_verified',
        event_count=31,distinct_exact_requested_urls=30,http_response_count=sum(counts.values()),
        http_status_counts=dict(counts),transport_failures=1,automatic_redirects_followed=0,
        public_started_at=ordered[0].started_at,public_finished_at=ordered[-1].completed_at,
        stopped_below_cap=True,
        public_limits='At most 50 events/35 exact requested URLs; redirects and DNS retry counted. '
        'Helper additionally limited 30 seconds/request, 20 MB/body, 75 MB total; no public opens '
        'after the final E031. Exact URL strings preserve query and case; no web searches used.',
        retained_response_bytes=sum(e.body.bytes for e in ordered),genuine_pdf_count=8,
        total_pdf_physical_pages=403,pdf_native_status='machine_native_text_unreviewed',
        referrals=referrals,priorities=priorities,checklist=checklist,discovered_links=links,
        viewed_pages=views,remaining_gaps=[
            'County codified zoning/subdivision text remains unavailable after official route HTTP 403.',
            'Town municipal/IFC codified text was not delivered by the retained application shell.',
            'County fire instrument final adoption/execution and placeholder-versus-numbered chain unresolved.',
            'County building fee schedule dated 2018 needs reconciliation with 2026 code amendments.',
            'Mixed county/state health fee dates, footnotes, blank cells and fee units require table review.',
            'Manuals dated 2015 and April 2023 need subsequent amendment and incorporation-chain checks.',
            'County taxes and engineering/road standards not searched; other town utility manuals unopened.',
            'This is discovery and structural preservation, not full transcription, legal applicability '
            'or comprehensive category coverage. No pending source is automatically promoted.',
        ],no_canonical_edits=True,no_git_commands=True,no_external_messages_or_forms=True)
    save(HERE/'DISCOVERY.json',report)
    write(HERE/'DISCOVERY.schema.json',(json.dumps(Discovery.model_json_schema(),indent=2)+'\n').encode())
    manifest_path=HERE/'baseline/_CONTROL_PLANE/LOCAL_DOWNLOAD_MANIFEST.jsonl'
    matches=[];found_pdf=set();pdf_ids=set(pdf)
    with manifest_path.open('rb') as handle:
        for line_number,line in enumerate(handle,1):
            old=json.loads(line);matching=[];fields=set()
            for eid,event in events.items():
                for key in ['requested_url','final_url','source_url']:
                    if old.get(key) and old[key] in {event.requested_url,event.final_url}:
                        matching.append(eid);fields.add(key)
                if old.get('sha256')==event.body.sha256 and event.body.bytes:
                    matching.append(eid);fields.add('body_sha256')
                    if eid in pdf_ids:found_pdf.add(eid)
            if matching:
                matches.append(LegacyMatch(line_number=line_number,line_sha256=sha(line),
                    source_id=old.get('source_id'),authority_id=old.get('authority_id'),
                    source_url=old.get('source_url'),requested_url=old.get('requested_url'),
                    final_url=old.get('final_url'),historical_sha256=old.get('sha256'),
                    matching_event_ids=sorted(set(matching)),match_fields=sorted(fields),
                    historical_raw_path_claim=old.get('raw_path')))
    repo=HERE.parents[2]/'MasterLegalDatabase';raw=[]
    sizes={events[eid].body.bytes for eid in pdf_ids}
    for path in (repo/'_RAW_ARCHIVE').rglob('*'):
        if path.is_file() and not path.is_symlink() and path.stat().st_size in sizes:
            data=path.read_bytes();digest=sha(data)
            raw.append(RawSizeCandidate(repository_relative_path=path.relative_to(repo).as_posix(),
                sha256=digest,bytes=len(data),identical_event_ids=sorted(
                    eid for eid in pdf_ids if events[eid].body.sha256==digest)))
    comparison=Comparison(recorded_at=datetime.now(timezone.utc),legacy_manifest=ref(manifest_path),
        streamed_rows=line_number,authority_selected_rows=33,matches=matches,
        actual_raw_size_candidates=raw,absent_pdf_legacy_digest_matches=sorted(pdf_ids-found_pdf),
        limits=['Comparisons stream the entire pinned working-file manifest, across all authorities.',
                'source_url matches identify parent catalog associations, not an identical downloaded body.',
                'URL equality is not byte equality; historical SHA claims do not prove retained originals.',
                'Windows raw paths are not opened. Actual local raw checks select ordinary files by '
                'matching PDF sizes, then measure SHA; unhydrated pointers cannot establish byte identity.',
                'Git HEAD and working-file hashes are separately pinned; committed-blob equality unverified.'])
    save(HERE/'LEGACY_COMPARISON.json',comparison)
    write(HERE/'LEGACY_COMPARISON.schema.json',
          (json.dumps(Comparison.model_json_schema(),indent=2)+'\n').encode())
    print(json.dumps({'events':31,'distinct':30,'statuses':dict(counts),'pdfs':8,'pages':403,
                      'viewed_pages':len(views),'links':len(links),'legacy_matching_rows':len(matches),
                      'pdf_legacy_digest_matches':sorted(found_pdf),'raw_candidates':len(raw)}))

if __name__=='__main__':
    main()
