"""Read-only CCR source baseline accounting; no source/current-law promotion."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

class Strict(BaseModel):
    model_config=ConfigDict(extra='forbid')

class Asset(Strict):
    path: str
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    bytes: int = Field(ge=0,le=25_000_000)

    @field_validator('path')
    @classmethod
    def safe(cls,value: str) -> str:
        """Require an ordinary repository-relative path before any file access."""
        path=PurePosixPath(value)
        if path.is_absolute() or '..' in path.parts or str(path)!=value or '\\' in value:
            raise ValueError('Unsafe repository-relative path')
        return value

class Selector(Strict):
    agency_id: str = Field(pattern=r'^[0-9]+$')
    rule_id: str = Field(pattern=r'^[0-9]+$')

class Capsule(Strict):
    manifest: Asset
    format: Literal['v1','v2']
    department_id: Literal['16','21']
    selectors: list[Selector]

class EmptyListing(Strict):
    department_id: Literal['16'] = '16'
    agency_id: Literal['170'] = '170'
    url: str
    content_type: str
    body: Asset
    receipt: Asset

class Observation(Strict):
    body: Asset
    receipt: Asset
    receipt_schema: Asset

class PartialPair(Strict):
    department_id: Literal['21'] = '21'
    agency_id: Literal['124'] = '124'
    rule_id: Literal['3475'] = '3475'
    version_id: Literal['12137'] = '12137'
    pdf: Asset
    returned_word_body: Asset
    observations: list[Observation] = Field(min_length=5,max_length=5)
    pdf_pages: Literal[10] = 10
    status: Literal['valid_pdf_exact_word_handler_returned_html'] = 'valid_pdf_exact_word_handler_returned_html'
    legal_currentness: Literal['not_verified'] = 'not_verified'

class Scope(Strict):
    department_id: str
    catalog_agency_ids: list[str]
    observed_listing_agency_ids: list[str]
    listed: list[Selector]
    paired: list[Selector]
    missing_pairs: list[Selector]
    source_cutoff_claims: list[str]
    earliest_observed: str
    latest_observed: str
    publisher_department_complete: Literal[False] = False
    legal_currentness: Literal['not_verified'] = 'not_verified'

class Index(Strict):
    schema_version: Literal['ccr-source-baseline-1'] = 'ccr-source-baseline-1'
    prepared_at: str
    prior_department_index: Asset
    capsules: list[Capsule]
    explicit_empty_listing: EmptyListing
    partial_pairs: list[PartialPair]
    department_catalog_count: Literal[25] = 25
    unchanged_department_collection_count: Literal[23] = 23
    full_prior_source_replayed_departments: Literal[22] = 22
    prior_metadata_only_department_ids: list[Literal['12']] = ['12']
    scopes: list[Scope]
    exact_remaining_gap: str
    source_cutoff_claims: list[str]
    legal_currentness: Literal['not_verified'] = 'not_verified'
    answer_safe: Literal[False] = False
    limitations: list[str]

    @model_validator(mode='after')
    def identities(self) -> Index:
        """Keep source capture references unique and both partial departments explicit."""
        paths=[c.manifest.path for c in self.capsules]
        if len(paths)!=len(set(paths)):
            raise ValueError('Duplicate capture manifest')
        if len(self.scopes)!=2 or {s.department_id for s in self.scopes}!={'16','21'}:
            raise ValueError('Both exact partial-department scopes required')
        return self

def sha(raw: bytes) -> str:
    """Hash exact source or metadata bytes."""
    return hashlib.sha256(raw).hexdigest()

def read(root: Path,asset: Asset) -> bytes:
    """Read one pinned bounded ordinary file, refusing changed bytes and symlinks."""
    path=root
    for part in PurePosixPath(asset.path).parts:
        path=path/part
        if path.is_symlink():raise ValueError('Symlink refused')
    if not path.is_file() or path.stat().st_size!=asset.bytes:
        raise ValueError('Source reference size differs')
    raw=path.read_bytes()
    if sha(raw)!=asset.sha256:raise ValueError('Source reference hash differs')
    return raw

def key(item: Selector) -> tuple[str,str]:
    """Return the publisher agency/rule identity without inferring legal sections."""
    return item.agency_id,item.rule_id

def ordered(values: set[tuple[str,str]]) -> list[Selector]:
    """Produce a stable numerical identity ordering."""
    return [Selector(agency_id=a,rule_id=r) for a,r in sorted(values,key=lambda p:(int(p[0]),int(p[1])))]

def validate_partition(listed: list[Selector],paired: list[Selector],missing: list[Selector]) -> None:
    """Require paired and missing identities to form the exact observed listing."""
    sets=[]
    for rows in [listed,paired,missing]:
        values=[key(x) for x in rows]
        if len(values)!=len(set(values)):raise ValueError('Duplicate selector')
        sets.append(set(values))
    all_,done,gap=sets
    if done&gap or done|gap!=all_:raise ValueError('Foreign or missing selector in partition')

def validate_capture_selectors(declared: list[Selector],actual: set[tuple[str,str]]) -> None:
    """Refuse duplicate, missing or foreign selection claims."""
    selectors=[key(x) for x in declared]
    if len(selectors)!=len(set(selectors)) or set(selectors)!=actual:
        raise ValueError('Capture selectors duplicate, missing or foreign')

def derive(root: Path,index: Index,*,replay_prior: bool=True) -> list[Scope]:
    """Replay source packages and reconstruct complete retained listing partitions."""
    sys.path.insert(0,str(root))
    from geode.pipeline import ccr_agency_capture as v1
    from geode.pipeline import ccr_agency_capture_v2 as v2
    from geode.pipeline import ccr_current as ccr
    from scripts import verify_ccr_source_coverage as old
    prior=old.Index.model_validate_json(read(root,index.prior_department_index))
    if replay_prior:old.verify(root,prior)
    if (len(prior.new_department_ids)!=22 or prior.existing_department_ids_excluded_from_new_totals!=['12'] or len(prior.catalog_department_ids)!=25):
        raise ValueError('Previous departmental coverage changed')
    rows={d:dict(roster={},listings={},paired=set(),cutoffs=set(),starts=[],ends=[]) for d in ['16','21']}
    for ref in index.capsules:
        read(root,ref.manifest)
        folder=root/Path(ref.manifest.path).parent
        state=rows[ref.department_id]
        if ref.format=='v1':
            record=v1.verify(folder,ref.manifest.sha256)
            if record.plan.department_id!=ref.department_id:raise ValueError('Foreign department')
            roster={a.agency_id:a.observed_url for a in record.plan.department_catalog_agencies}
            actual={ (t.agency_id,t.rule_id) for t in record.plan.targets if t.role=='rule_history'}
            listing_data=[(t.agency_id,t.requested_url,t.historical.body.path,t.historical.content_type) for t in record.plan.targets if t.role=='agency_listing']
            welcome=next(t for t in record.plan.targets if t.role=='welcome')
            doc=ccr._parse_html((folder/welcome.historical.body.path).read_bytes(),welcome.historical.content_type)
            cutoff=ccr._cutoff(doc,welcome.historical.recorded_finished_at.date()).isoformat()
        else:
            record=v2.verify(folder,ref.manifest.sha256)
            if record.department_id!=ref.department_id:raise ValueError('Foreign department')
            plan=v2.Plan.model_validate_json((folder/'PLAN.json').read_bytes())
            roster={a.agency_id:a.listing_url for a in record.agencies}
            actual={(r.agency_id,r.rule_id) for r in record.selected_rules}
            by_id={r.association_id:r for r in plan.responses}
            listing_data=[]
            for agency in record.agencies:
                if agency.selected:
                    r=by_id[agency.listing_association_id]
                    listing_data.append((agency.agency_id,r.claim.requested_url,r.body.path,r.claim.content_type))
            cutoff=record.source_cutoff_claim.isoformat()
        validate_capture_selectors(ref.selectors,actual)
        if state['paired']&actual:raise ValueError('Selector appears in two captures')
        state['paired'].update(actual)
        if state['roster'] and state['roster']!=roster:raise ValueError('Catalog agency identities changed')
        state['roster']=roster
        for aid,url,path,ctype in listing_data:
            if roster[aid]!=url:raise ValueError('Listing not bound to catalog')
            parsed=ccr._rules(ccr._parse_html((folder/path).read_bytes(),ctype),url)
            identities={(aid,rid) for rid in parsed}
            if aid in state['listings'] and state['listings'][aid]!=identities:
                raise ValueError('Observed listing denominator changed')
            state['listings'][aid]=identities
        state['cutoffs'].add(cutoff)
        state['starts'].append(record.observed_start_claim.isoformat())
        state['ends'].append(record.observed_finish_claim.isoformat())
    empty=index.explicit_empty_listing
    receipt=json.loads(read(root,empty.receipt))
    raw=read(root,empty.body)
    if (receipt['requested_url']!=empty.url or receipt['final_url']!=empty.url or receipt['http_status']!=200 or not receipt['complete_transfer'] or receipt['body']['sha256']!=empty.body.sha256 or receipt['body']['size_bytes']!=empty.body.bytes or receipt['public_headers']['content-type']!=empty.content_type):
        raise ValueError('Empty listing receipt binding differs')
    state=rows['16']
    if state['roster'].get('170')!=empty.url:raise ValueError('Empty listing outside source catalog')
    doc=ccr._parse_html(raw,empty.content_type)
    if ccr._rules(doc,empty.url)!={}:raise ValueError('Listing is not explicitly empty')
    state['listings']['170']=set()
    scopes=[]
    for dept,state in rows.items():
        if set(state['roster'])!=set(state['listings']):raise ValueError('Missing agency listing')
        listed=set().union(*state['listings'].values())
        missing=listed-state['paired']
        scope=Scope(department_id=dept,catalog_agency_ids=sorted(state['roster'],key=int),observed_listing_agency_ids=sorted(state['listings'],key=int),listed=ordered(listed),paired=ordered(state['paired']),missing_pairs=ordered(missing),source_cutoff_claims=sorted(state['cutoffs']),earliest_observed=min(state['starts']),latest_observed=max(state['ends']))
        validate_partition(scope.listed,scope.paired,scope.missing_pairs)
        scopes.append(scope)
    for partial in index.partial_pairs:
        import pymupdf
        from jsonschema import Draft202012Validator
        receipts={}
        for observation in partial.observations:
            raw_receipt=read(root,observation.receipt)
            receipt=json.loads(raw_receipt)
            Draft202012Validator(json.loads(read(root,observation.receipt_schema))).validate(receipt)
            observed=read(root,observation.body)
            if (receipt['body']['sha256']!=observation.body.sha256 or receipt['body']['bytes']!=len(observed) or receipt['body']['path']!='response.body' or receipt['requested_url']!=receipt['observed_final_url'] or not receipt['complete_transfer'] or receipt['curl_exit']!=0 or receipt['http_status']!=200):
                raise ValueError('Partial source observation differs')
            v2.official_url(receipt['requested_url'])
            receipts[receipt['target_id']]=(receipt,observed)
        if len(receipts)!=5:raise ValueError('Duplicate gap observation')
        hist,hbody=receipts['transportation3475-history']
        versions=ccr._versions(ccr._parse_html(hbody,hist['safe_headers']['content-type']),hist['requested_url'])
        version=next(v for v in versions if v.version_id==partial.version_id)
        for target,asset in [('transportation3475-pdf',partial.pdf),('transportation3475-word',partial.returned_word_body)]:
            r,body=receipts[target]
            if r['requested_url'] not in version.document_urls or sha(body)!=asset.sha256:
                raise ValueError('Partial pair not joined to source history')
        raw=read(root,partial.pdf)
        word=read(root,partial.returned_word_body)
        with pymupdf.open(stream=raw,filetype='pdf') as pdf:
            if pdf.page_count!=partial.pdf_pages:raise ValueError('Partial PDF page count differs')
        if b'<html' not in word[:8192].lower() or word.startswith((b'PK\x03\x04',bytes.fromhex('d0cf11e0a1b11ae1'),b'{\\rtf')):
            raise ValueError('Expected failed Word HTML evidence differs')
        missing=next(s.missing_pairs for s in scopes if s.department_id=='21')
        if Selector(agency_id=partial.agency_id,rule_id=partial.rule_id) not in missing:
            raise ValueError('Partial PDF incorrectly credited as complete pair')
    return scopes

def verify(root: Path,index: Index) -> dict:
    """Compare declared source coverage with immutable maintained source replays."""
    derived=derive(root,index)
    if derived!=index.scopes:raise ValueError('Declared coverage differs from source replay')
    for scope in index.scopes:validate_partition(scope.listed,scope.paired,scope.missing_pairs)
    if sorted({date for s in index.scopes for date in s.source_cutoff_claims})!=index.source_cutoff_claims:
        raise ValueError('Cutoff claims differ')
    if len(index.partial_pairs)!=1 or next(s.missing_pairs for s in derived if s.department_id=='21')!=[Selector(agency_id='124',rule_id='3475')]:
        raise ValueError('Exact remaining gap differs')
    if next(s.missing_pairs for s in derived if s.department_id=='16'):
        raise ValueError('Public Health remaining paired-source gaps exist')
    return {'status':'pass','unchanged_department_collections':23,'catalog_departments':25,'departments':[{ 'department_id':s.department_id,'listed':len(s.listed),'paired':len(s.paired),'missing':len(s.missing_pairs)} for s in derived],'legal_currentness':'not_verified'}

def main() -> None:
    """Verify an externally pinned repository index without writes or HTTP."""
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--index',type=Path)
    parser.add_argument('--index-sha256',required=True)
    args=parser.parse_args()
    path=args.index or args.root/'_CONTROL_PLANE/CCR_SOURCE_BASELINE_2026-10-05.json'
    raw=path.read_bytes()
    if sha(raw)!=args.index_sha256:raise ValueError('Index pin differs')
    index=Index.model_validate_json(raw,strict=True)
    if json.loads(path.with_suffix('.schema.json').read_bytes())!=Index.model_json_schema():raise ValueError('Schema differs')
    print(json.dumps(verify(args.root,index),sort_keys=True))

if __name__=='__main__':main()
