"""One-time offline preservation; never execute the copied acquisition script."""
from __future__ import annotations
import hashlib
import json
import os
import re
import sys
from datetime import datetime,timezone
from pathlib import Path
from bs4 import BeautifulSoup
import pymupdf

BASE=Path(__file__).absolute().parent
PROJECT=BASE.parents[2]
REPO=PROJECT/'MasterLegalDatabase'
sys.dont_write_bytecode=True
sys.path.insert(0,str(BASE))
sys.path.insert(0,str(REPO))
from models import (Asset,Copy,Line,Anchor,ArchivedMatch,Source,Scan,Preservation,
                    HttpCandidate,HttpBinding,Document,Manifest)
from geode.pipeline.manual_source_intake import ManualSourceIntakeRecord
from geode.pipeline.manual_review_inventory import HttpBinding as CurrentHttpBinding

LIVE=BASE.parent/'greeley-custody-recheck-live'
OLD=REPO/'research/local_review/weld-greeley-intake-sherlock008-2026-09-11'
QA=REPO/'research/local_review/greeley-fees-atlas-source-review-2026-09-11'
IDS={'SD008-06':('greeley-building-fees-sd008-06','EB-PDF-015','SOURCE_QA','/source_sha256'),
     'SD008-07':('greeley-development-impact-fee-memo-sd008-07','EB-PDF-016','SOURCE_QA','/source/sha256'),
     'SD008-08':('greeley-water-sewer-proposed-pif-notice-sd008-08','EB-PDF-017','SOURCE_REVIEW','/source_pdf/sha256')}
PATTERNS=[r'(?i)(?:authorization|proxy-authorization|set-cookie)\s*:',
          r'(?i)bearer\s+[A-Za-z0-9._-]{10,}',
          r'(?i)(?:access_token|client_secret|api_key|apikey|sessionid)\s*[=:]\s*["\x27]?[^\s,;"\x27]{8,}',
          r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
          r'\b(?:ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk_live_[A-Za-z0-9]{12,})\b']
PUBLIC={'content-type','content-length','last-modified','date','etag','cache-control','location'}


def digest(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()


def ordinary(path:Path)->None:
    if not path.is_file() or any(p.is_symlink() for p in (path,*path.parents)):
        raise ValueError('Nonordinary input')


def asset(path:Path)->Asset:
    ordinary(path)
    with path.open('rb') as stream: sha=hashlib.file_digest(stream,'sha256').hexdigest()
    return Asset(path=path.relative_to(BASE).as_posix(),sha256=sha,size_bytes=path.stat().st_size)


def write(path:Path,raw:bytes)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():raise ValueError('Refusing overwrite '+str(path))
    temporary=path.with_suffix(path.suffix+'.tmp')
    with temporary.open('xb') as out:out.write(raw);out.flush();os.fsync(out.fileno())
    os.replace(temporary,path)


def save(name:str,value:object)->None:
    write(BASE/name,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())


def copy(path:Path,destination:str,copies:list)->Asset:
    ordinary(path)
    raw=path.read_bytes();write(BASE/destination,raw)
    assert path.read_bytes()==raw
    ref=asset(BASE/destination)
    copies.append(Copy(original_path=str(path),copied=ref))
    return ref


def selected_lines(path:Path,key:str,ids:set[str],destination:str,model=None)->dict:
    ordinary(path)
    found={};hasher=hashlib.sha256();size=0
    with path.open('rb') as stream:
        for index,line in enumerate(stream):
            hasher.update(line);size+=len(line)
            row=json.loads(line)
            if row[key] in ids:
                if row[key] in found:raise ValueError('Duplicate selected ID')
                if model:model.model_validate_json(line)
                found[row[key]]=(index,line,row)
    assert set(found)==ids
    whole=hasher.hexdigest()
    with path.open('rb') as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==whole
    ordered=sorted(found.items(),key=lambda x:x[1][0])
    write(BASE/destination,b''.join(value[1] for _,value in ordered))
    ref=asset(BASE/destination)
    return {sid:(value[2],Line(original_repository_path=path.relative_to(REPO).as_posix(),
        original_whole_file_sha256=whole,original_whole_file_size_bytes=size,
        original_zero_based_row=value[0],selected_document=ref,selected_zero_based_row=selected,
        exact_line_sha256=digest(value[1]),exact_line_size_bytes=len(value[1])))
        for selected,(sid,value) in enumerate(ordered)}


def main()->None:
    copies=[]
    for path in sorted(LIVE.rglob('*')):
        if path.is_dir() and not path.is_symlink():continue
        copy(path,'fresh/'+path.relative_to(LIVE).as_posix(),copies)
    script=copy(BASE.parent/'greeley-custody-recheck.py','fresh/acquisition.py',copies)
    summary=json.loads((BASE/'fresh/summary.json').read_bytes())
    plan=json.loads((BASE/'fresh/plan.json').read_bytes())
    assert len(summary['receipts'])==len(plan['targets'])==4
    parent=asset(BASE/'fresh/GREELEY-PARENT/body.bin')
    old_parent=copy(OLD/'evidence/referrals/building_permits_and_inspections.html',
                    'prior/official-parent.html',copies)
    assert parent.sha256==old_parent.sha256
    html=(BASE/parent.path).read_bytes()
    wanted={value[0] for value in IDS.values()}
    raw=selected_lines(REPO/'_RAW_ARCHIVE/manual_intake/manual_source_intake_manifest.jsonl',
                       'record_id',wanted,'prior/canonical-records.selected.jsonl',ManualSourceIntakeRecord)
    provenance=selected_lines(OLD/'source-provenance.jsonl','source_id',wanted,
                              'prior/source-provenance.selected.jsonl')
    copy(OLD/'source-provenance.schema.json','prior/source-provenance.schema.json',copies)
    save('prior/canonical-record.schema.json',ManualSourceIntakeRecord.model_json_schema())
    copy(QA/'PACKAGE.json','prior/qa-package-manifest.json',copies)
    copy(QA/'PACKAGE.schema.json','prior/qa-package-manifest.schema.json',copies)
    sources=[];bindings=[]
    for receipt in summary['receipts'][1:]:
        event=receipt['source_id'];sid,assignment,stem,pointer=IDS[event]
        row,line=raw[sid];prov,provline=provenance[sid]
        body=asset(BASE/'fresh'/event/'body.bin')
        assert receipt['sha256']==body.sha256==row['sha256']==prov['canonical_original']['sha256']
        assert receipt['size_bytes']==body.size_bytes==row['size_bytes']
        assert row['official_source_url'] is None
        assert row['acquisition_method']=='received_review_package'
        canonical=REPO/row['archive_path'];prior_pdf=QA/'packet/01-source-only'/sid/'original.pdf'
        for existing in [canonical,prior_pdf]:
            ordinary(existing);assert existing.read_bytes()==(BASE/body.path).read_bytes()
        with pymupdf.open(BASE/body.path) as doc:
            assert not doc.is_repaired and not doc.is_encrypted
            assert len(doc)==receipt['pdf_pages']
            assert all(not page.rect.is_empty for page in doc)
        url=receipt['requested_url']
        matches=[]
        for match in re.finditer(rb'<a(?:\s[^>]*)?>.*?</a>',html,re.I|re.S):
            anchor=BeautifulSoup(match.group(),'html.parser').find('a')
            if anchor.get('href')==url:matches.append((match,anchor))
        assert len(matches)==1
        match,anchor=matches[0]
        anchor_binding=Anchor(parent=parent,parent_url=summary['receipts'][0]['requested_url'],
            href=url,exact_source_start_byte=match.start(),exact_source_end_byte=match.end(),
            exact_anchor_html=match.group().decode(),anchor_html_sha256=digest(match.group()),
            normalized_dom_text=' '.join(anchor.get_text(' ',strip=True).split()),occurrence_count=1,
            label_scope='DOM text including icon-label strings; not a new visual webpage review')
        qa=copy(QA/'source-audits'/assignment/(stem+'.json'),
                'prior/qa/'+assignment+'/'+stem+'.json',copies)
        schema=copy(QA/'source-audits'/assignment/(stem+'.schema.json'),
                    'prior/qa/'+assignment+'/'+stem+'.schema.json',copies)
        copy(QA/'source-audits'/assignment/(stem+'.md'),
             'prior/qa/'+assignment+'/'+stem+'.md',copies)
        source=Source(event_id=event,record_id=sid,authority_id='CO-MUNICIPAL-GREELEY',
            layer_id='10_Municipal_Authorities',body=body,
            reservation=asset(BASE/'fresh'/event/'reservation.json'),
            receipt=asset(BASE/'fresh'/event/'receipt.json'),pages=receipt['pdf_pages'],
            anchor=anchor_binding,
            archived_source=ArchivedMatch(repository_path=row['archive_path'],sha256=body.sha256,
                size_bytes=body.size_bytes,byte_comparison='same_exact_bytes',represented_by=body),
            prior_qa_original=ArchivedMatch(repository_path=prior_pdf.relative_to(REPO).as_posix(),
                sha256=body.sha256,size_bytes=body.size_bytes,byte_comparison='same_exact_bytes',represented_by=body),
            canonical_record=line,prior_provenance=provline,prior_qa=qa,prior_qa_schema=schema,
            prior_qa_source_sha_pointer=pointer,source_role=prov['source_role'],
            prior_repository_received_at=datetime.fromisoformat(row['received_at'].replace('Z','+00:00')),
            prior_acquisition_method='received_review_package',prior_official_source_url=None,
            qualifications=[
                'This later recorded GET does not prove the earlier Sherlock transport or acquisition times.',
                'Canonical received_at, null official_source_url and received_review_package remain unchanged.',
                'The CDN URL is linked from the City parent; this does not broaden the manual-intake host allowlist.',
                'This package rechecks byte identity and source bindings, not full prior visual or semantic QA.',
                *prov['qualifications']],legal_currentness='not_verified',answer_safe=False)
        sources.append(source)
        binding=HttpBinding(document=Document(artifact=source.receipt),sha_pointer='/sha256',
                            status_pointer='/http_status',time_pointer='/finished_at')
        CurrentHttpBinding.model_validate_json(binding.model_dump_json())
        bindings.append(HttpCandidate(record_id=sid,verified_http=binding,
            path_basis='package-relative; prefix with actual destination if later integrated',
            time_role='recorded response completion, not original acquisition or repository intake',
            integration_status='not_applied'))
    rejected=[]
    for receipt in summary['receipts']:
        assert receipt['error_text']==''
        rejected.extend(sorted(set(receipt['headers'])-PUBLIC))
        assert receipt==json.loads((BASE/'fresh'/receipt['source_id']/'receipt.json').read_bytes())
    assert not rejected
    scans=[]
    for path in sorted((BASE/'fresh').rglob('*')):
        if not path.is_file():continue
        if path.suffix in {'.json','.py'} or path==BASE/parent.path:
            text=path.read_bytes().decode('utf-8')
            assert not any(re.search(pattern,text) for pattern in PATTERNS),path
            scans.append(path.relative_to(BASE).as_posix())
    privacy=Scan(public_header_names=sorted(PUBLIC),header_dictionary_count=8,
        rejected_header_keys_found=[],credential_patterns=PATTERNS,scanned_text_assets=scans,
        credential_pattern_match_count=0,receipt_error_texts_empty=True,
        raw_response_headers_available=False,
        original_header_exclusions=['Set-Cookie','Authorization','Proxy-Authorization',
                                    'all response fields outside the source script public allowlist'],
        limitations=['Raw complete response headers were held only in memory and are unavailable for independent comparison.',
            'The scan checks explicit header keys and listed lexical patterns; it does not certify absence of all possible secrets.',
            'Compressed PDF streams are preserved unchanged; this scan is not a new full PDF content review.',
            'Public HTML includes ordinary site markup and links; no cookies/authentication values were identified by the defined scan.'],
        redactions_performed_in_this_package=0)
    result=Preservation(schema_version=1,status='public_custody_preserved_no_canonical_change',
        preserved_at=datetime.now(timezone.utc),original_copies=copies,acquisition_script=script,
        sources=sources,fresh_parent=parent,historical_parent=old_parent,
        parent_byte_identity='same_exact_bytes',privacy_scan=privacy,recorded_public_gets=4,
        recorded_redirects=0,requests_by_this_preservation=0,canonical_writes=0,
        total_pdf_pages=6,total_pdf_bytes=877639,full_source_qa_replayed=False,
        old_acquisition_claims_changed=False,legal_currentness='not_verified',limitations=[
            'Recorded local request/completion times are distinct from HTTP Date/Last-Modified and are not legal dates.',
            'The parent HTTP Date is September 8 while the recorded request is September 12; cached metadata is retained without replacing the acquisition interval.',
            'Four receipts and the script record complete HTTP 200 GETs without redirects; no new network request was made by this preservation.',
            'A later equal digest supports exact byte identity at the recorded acquisition event, not continuous availability or legal currentness.',
            'Full historical JSONL manifests and complete QA packages are not duplicated: selected exact rows and original whole-file digests are retained; only copied subset bytes can be recomputed portably.',
            'Prior QA metadata retains its original scoped/pending language. Complete old visual validators, images and candidates are not replayed here.',
            'The copied acquisition script is inert historical evidence and is never executed by the portable validator.'])
    save('PRESERVATION.json',result.model_dump(mode='json'))
    save('PRESERVATION.schema.json',Preservation.model_json_schema())
    write(BASE/'http-bindings.jsonl',b''.join((b.model_dump_json()+'\n').encode() for b in bindings))
    save('http-binding.schema.json',HttpCandidate.model_json_schema())
    save('FINAL_MANIFEST.schema.json',Manifest.model_json_schema())


if __name__=='__main__':main()
