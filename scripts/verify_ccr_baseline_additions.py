"""Verify the portable twelve-package CCR native addition index without HTTP."""
from __future__ import annotations
import argparse
from contextlib import nullcontext
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import sys
import tempfile
from typing import Literal
from pydantic import BaseModel,ConfigDict,Field

class Strict(BaseModel):
    """Refuse undeclared fields in publication records."""
    model_config=ConfigDict(extra='forbid',strict=True)

class Asset(Strict):
    """One repository-relative immutable artifact."""
    path:str
    sha256:str=Field(pattern=r'^[a-f0-9]{64}$')
    bytes:int=Field(ge=0)

class Page(Strict):
    """One native text page, identified independently of aliases."""
    physical_page:int=Field(ge=1)
    text_sha256:str=Field(pattern=r'^[a-f0-9]{64}$')
    text_bytes:int=Field(ge=0)

class Original(Strict):
    """Complete native page sequence for one original PDF."""
    sha256:str=Field(pattern=r'^[a-f0-9]{64}$')
    pages:list[Page]

class Package(Strict):
    """Portable source capsule and reproducible native output references."""
    package_id:str
    capture_root:str
    capture_manifest:Asset
    native_manifest:Asset
    native_input:Asset
    native_originals:Asset
    selected_rule_ids:list[str]
    source_cutoff_claim:str
    native_pdfs:int
    native_pages:int
    native_build_command:list[str]
    native_verify_command:list[str]

class Index(Strict):
    """Source acquisition and unreviewed native text, never current-law approval."""
    generated_at:str
    packages:list[Package]
    prior_index:Asset
    prior_page_sets:list[Asset]
    new_page_set:Asset
    original_schema:Asset
    previous_pdfs:int
    previous_pages:int
    added_whole_rule_identities:int
    new_distinct_pdfs:int
    new_distinct_pages:int
    overlap_pdfs:int
    overlap_pages:int
    union_pdfs:int
    union_pages:int
    legal_currentness:Literal['not_verified']='not_verified'
    answer_safe:Literal[False]=False
    existing_department_completion_flags_changed:Literal[False]=False
    native_status:Literal['machine_extraction_unreviewed']='machine_extraction_unreviewed'

MAX_REFERENCE_BYTES=25_000_000
MAX_TOTAL_REFERENCE_BYTES=100_000_000
NATIVE_PAGE=re.compile(r'^native/([a-f0-9]{64})/([0-9]{6})\.txt$')
SAFE_PACKAGE=re.compile(r'^[A-Za-z0-9_-]{1,80}$')

def sha(raw:bytes)->str:
    """Hash exact retained bytes."""
    return hashlib.sha256(raw).hexdigest()

def safe_path(name:str)->PurePosixPath:
    """Refuse absolute, noncanonical and parent-traversing member names."""
    path=PurePosixPath(name)
    if path.is_absolute() or '..' in path.parts or str(path)!=name or '\\' in name:
        raise ValueError('Unsafe relative artifact path')
    return path

class Reader:
    """Bound all referenced metadata reads and refuse symlink or hash substitution."""
    def __init__(self,root:Path)->None:
        self.root=root
        self.total=0

    def read(self,asset:Asset)->bytes:
        """Read a size/hash-pinned ordinary file under the fixed metadata allowance."""
        if asset.bytes>MAX_REFERENCE_BYTES:raise ValueError('Reference exceeds file cap')
        path=self.root
        for part in safe_path(asset.path).parts:
            path=path/part
            if path.is_symlink():raise ValueError('Symlink reference refused')
        if not path.is_file() or path.stat().st_size!=asset.bytes:
            raise ValueError('Reference size or ordinary-file status differs')
        self.total+=asset.bytes
        if self.total>MAX_TOTAL_REFERENCE_BYTES:raise ValueError('Metadata read budget exceeded')
        raw=path.read_bytes()
        if sha(raw)!=asset.sha256:raise ValueError('Reference hash differs')
        return raw

def validate_original(row:Original)->None:
    """Require complete, unique, ordered physical pages beginning at one."""
    if not row.pages or [p.physical_page for p in row.pages]!=list(range(1,len(row.pages)+1)):
        raise ValueError('Missing, duplicate or unordered physical page')

def ledger(raw:bytes)->dict[str,Original]:
    """Stream a JSONL ledger, rejecting duplicate originals and incomplete page sequences."""
    result={}
    for line in io.BytesIO(raw):
        if not line.strip():raise ValueError('Blank JSONL row')
        row=Original.model_validate_json(line,strict=True)
        validate_original(row)
        if row.sha256 in result:raise ValueError('Duplicate original in ledger')
        result[row.sha256]=row
    if not result:raise ValueError('Empty original ledger')
    return result

def merge(target:dict[str,Original],incoming:dict[str,Original])->None:
    """Deduplicate shared PDFs only when every physical-page identity agrees."""
    for digest,row in incoming.items():
        if digest in target and target[digest]!=row:
            raise ValueError('Conflicting native pages for one original PDF')
        target[digest]=row

def native_ledger(files:list)->dict[str,Original]:
    """Reconstruct PDF/page hashes from exact native-manifest member identities."""
    pages={}
    seen=set()
    for ref in files:
        name=ref.path
        if name in seen:raise ValueError('Duplicate native-manifest member')
        seen.add(name)
        if not name.startswith('native/'):continue
        match=NATIVE_PAGE.fullmatch(name)
        if not match:raise ValueError('Malformed native-page member path')
        digest,number=match.groups()
        pages.setdefault(digest,[]).append(Page(physical_page=int(number),text_sha256=ref.sha256,text_bytes=ref.size_bytes))
    result={}
    for digest,rows in pages.items():
        row=Original(sha256=digest,pages=sorted(rows,key=lambda p:p.physical_page))
        validate_original(row)
        result[digest]=row
    return result

def page_count(rows:dict[str,Original])->int:
    """Count unique physical pages rather than citation aliases."""
    return sum(len(row.pages) for row in rows.values())

def check_counts(index:Index,prior:dict[str,Original],new:dict[str,Original],rules:set[str])->dict:
    """Prove all declared before, addition, overlap and union counters."""
    overlap=set(prior)&set(new)
    union=dict(prior)
    merge(union,new)
    expected=dict(previous_pdfs=len(prior),previous_pages=page_count(prior),
        added_whole_rule_identities=len(rules),new_distinct_pdfs=len(new),
        new_distinct_pages=page_count(new),overlap_pdfs=len(overlap),
        overlap_pages=sum(len(new[d].pages) for d in overlap),union_pdfs=len(union),union_pages=page_count(union))
    if any(getattr(index,name)!=value for name,value in expected.items()):
        raise ValueError('Declared prior/addition/overlap/union counts differ')
    return expected

def verify(root:Path,index:Index,*,rebuild_native:bool=False)->dict:
    """Replay source capsules and pinned page ledgers; optionally re-extract all new PDFs."""
    sys.path.insert(0,str(root))
    from geode.pipeline import ccr_agency_capture_v2 as capture
    from geode.pipeline import ccr_agency_text as native
    reader=Reader(root)
    if len(index.packages)!=12 or len({p.package_id for p in index.packages})!=12:
        raise ValueError('Exactly twelve distinct packages required')
    roots=[p.capture_root for p in index.packages]
    if len(roots)!=len(set(roots)):raise ValueError('Duplicate source capture root')
    if json.loads(reader.read(index.original_schema))!=Original.model_json_schema():
        raise ValueError('Original ledger schema differs')
    old=json.loads(reader.read(index.prior_index))
    expected_prior=old['baseline_page_sets']+[old['new_page_set']]
    if [r.model_dump() for r in index.prior_page_sets]!=expected_prior:
        raise ValueError('Prior page-set references differ from pinned predecessor')
    prior={}
    for ref in index.prior_page_sets:merge(prior,ledger(reader.read(ref)))
    aggregate={}
    rules=set()
    # Temporary rebuilds remain outside the repository and are automatically removed.
    scratch_context=(tempfile.TemporaryDirectory(prefix='geode-ccr-baseline-verify-',
                                               dir=Path(tempfile.gettempdir()).resolve())
                     if rebuild_native else nullcontext(None))
    with scratch_context as scratch:
        for package in index.packages:
            if not SAFE_PACKAGE.fullmatch(package.package_id):raise ValueError('Unsafe package identity')
            safe_path(package.capture_root)
            if package.capture_manifest.path!=package.capture_root+'/MANIFEST.json':
                raise ValueError('Capture root/manifest association differs')
            cbytes=reader.read(package.capture_manifest)
            record=capture.verify(root/package.capture_root,package.capture_manifest.sha256)
            selected={r.rule_id for r in record.selected_rules}
            if (record.department_id!='16' or package.selected_rule_ids!=sorted(selected)
                    or rules&selected or str(record.source_cutoff_claim)!=package.source_cutoff_claim):
                raise ValueError('Package source selection or cutoff differs')
            rules.update(selected)
            nbytes=reader.read(package.native_manifest)
            nmanifest=native.Manifest.model_validate_json(nbytes,strict=True)
            ibytes=reader.read(package.native_input)
            input_plan=native.InputPlan.model_validate_json(ibytes,strict=True)
            if (input_plan.capture_manifest_sha256!=package.capture_manifest.sha256
                    or nmanifest.input!=input_plan):
                raise ValueError('Native input/capture binding differs')
            scope=nmanifest.scope
            if (scope.department_id!=record.department_id or scope.catalog_agencies!=record.catalog_agency_count
                    or scope.capture_selected_rules!=record.selected_rule_count
                    or scope.capture_selected_agencies!=record.selected_agency_count
                    or scope.source_cutoff_claim!=record.source_cutoff_claim
                    or scope.observed_start_claim!=record.observed_start_claim
                    or scope.observed_finish_claim!=record.observed_finish_claim):
                raise ValueError('Native scope differs from source capture')
            members={r.path:r for r in nmanifest.files}
            if len(members)!=len(nmanifest.files):raise ValueError('Duplicate native member')
            cm=capture.Manifest.model_validate_json(cbytes,strict=True)
            embedded={r.path.removeprefix('capture/'):r for r in nmanifest.files if r.path.startswith('capture/')}
            expected_embedded={r.path:(r.sha256,r.bytes) for r in cm.files}
            expected_embedded['MANIFEST.json']=(package.capture_manifest.sha256,len(cbytes))
            if {name:(r.sha256,r.size_bytes) for name,r in embedded.items()}!=expected_embedded:
                raise ValueError('Embedded capture member identities differ')
            if 'INPUT.json' not in members or (members['INPUT.json'].sha256,members['INPUT.json'].size_bytes)!=(sha(ibytes),len(ibytes)):
                raise ValueError('Native input member differs')
            originals=ledger(reader.read(package.native_originals))
            if native_ledger(nmanifest.files)!=originals:
                raise ValueError('Page ledger differs from native manifest')
            pdf_pages={d.sha256:d.pages for d in record.documents if d.role=='pdf'}
            chosen=set(input_plan.selected_pdf_sha256) if input_plan.selected_pdf_sha256 is not None else set(pdf_pages)
            if (set(originals)!=chosen or scope.selected_pdf_sha256!=sorted(chosen)
                    or scope.unselected_pdf_sha256!=sorted(set(pdf_pages)-chosen)
                    or any(len(originals[d].pages)!=pdf_pages[d] for d in originals)):
                raise ValueError('Native original/page scope differs from captured PDFs')
            count=page_count(originals)
            if (package.native_pdfs!=len(originals) or package.native_pages!=count
                    or nmanifest.unique_physical_pages!=count
                    or nmanifest.unique_native_bytes!=sum(p.text_bytes for r in originals.values() for p in r.pages)):
                raise ValueError('Native counters differ from page identities')
            expected_names=set('capture/'+name for name in expected_embedded)|set(native.schemas())|{'INPUT.json','documents.jsonl','pages.jsonl'}|{f'native/{d}/{p.physical_page:06}.txt' for d,r in originals.items() for p in r.pages}
            if set(members)!=expected_names:raise ValueError('Unexpected or missing native output member')
            for name,raw in native.schemas().items():
                if (members[name].sha256,members[name].size_bytes)!=(sha(raw),len(raw)):
                    raise ValueError('Native schema member differs')
            runtime='.geode_runtime/ccr-baseline-2026-10-05/'+package.package_id
            if package.native_build_command!=['python','-B','-m','geode.pipeline.ccr_agency_text','build','--source',package.capture_root,'--capture-sha256',package.capture_manifest.sha256,'--output',runtime]:
                raise ValueError('Native rebuild command differs')
            if package.native_verify_command!=['python','-B','-m','geode.pipeline.ccr_agency_text','verify','--root',runtime,'--manifest-sha256',package.native_manifest.sha256]:
                raise ValueError('Native verify command differs')
            if rebuild_native:
                output=Path(scratch)/package.package_id
                native.build(root/package.capture_root,output,input_plan)
                if (output/'MANIFEST.json').read_bytes()!=nbytes:
                    raise ValueError('Rebuilt native manifest differs byte-for-byte')
                native.verify(output,package.native_manifest.sha256)
            merge(aggregate,originals)
    if ledger(reader.read(index.new_page_set))!=aggregate:
        raise ValueError('Combined new-page ledger differs from package union')
    counts=check_counts(index,prior,aggregate,rules)
    return {'status':'pass','packages':len(index.packages),**counts,
        'native_verification':'rebuilt_and_replayed' if rebuild_native else 'pinned_manifest_and_page_ledger_replay',
        'prior_native_reextracted':False,'legal_currentness':'not_verified'}

def main()->None:
    """Verify an externally pinned index, with optional temporary native reconstruction."""
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--index',type=Path)
    parser.add_argument('--index-sha256',required=True)
    parser.add_argument('--rebuild-native',action='store_true')
    args=parser.parse_args()
    path=args.index or args.root/'docs/audits/CCR_BASELINE_ADDITIONS_2026-10-05/INDEX.json'
    raw=path.read_bytes()
    if len(raw)>MAX_REFERENCE_BYTES or sha(raw)!=args.index_sha256:
        raise ValueError('Index size or external pin differs')
    index=Index.model_validate_json(raw,strict=True)
    if json.loads(path.with_suffix('.schema.json').read_bytes())!=Index.model_json_schema():
        raise ValueError('Index schema differs')
    print(json.dumps(verify(args.root,index,rebuild_native=args.rebuild_native),sort_keys=True))

if __name__=='__main__':main()
