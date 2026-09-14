"""Offline semantic/hash/association tamper regressions for the retained Pueblo source."""
from __future__ import annotations
import copy
import json
import shutil
from pathlib import Path
import pytest
from pydantic import ValidationError
from qa_model import QA, Inventory, Ref, checked, derive_tables, file_ref, native_lines, norm
from validate_qa import verify_data, validate, inventory

ROOT=Path(__file__).resolve().parent

@pytest.fixture
def qa():
    return QA.model_validate_json((ROOT/'SOURCE_QA.json').read_bytes())

@pytest.fixture
def package(tmp_path):
    root=tmp_path/'source-qa'
    shutil.copytree(ROOT,root,ignore=shutil.ignore_patterns('__pycache__','.pytest_cache'))
    seal(root)
    return root

def seal(root):
    files=[file_ref(root,p) for p in sorted(root.rglob('*')) if p.is_file() and p.name!='MANIFEST.json']
    record=Inventory(files=files)
    (root/'MANIFEST.json').write_text(record.model_dump_json())


def test_exact_source_whole_table_and_rendering(qa):
    verify_data(ROOT,qa,True)
    assert [len([r for r in qa.rows if r.physical_page==n]) for n in range(1,5)]==[13,14,14,3]
    assert sum(len(r.nested) for r in qa.rows)==43
    assert sum(len(p.lines) for p in qa.pages)==243
    assert sum(p.native.size_bytes for p in qa.pages)==4923
    assert qa.rows[10].fee.reviewed_display.count('nor site improvements')==2
    rezoning=next(r for r in qa.rows if r.row_id=='P3-04')
    assert len(rezoning.nested)==11
    assert rezoning.nested[6].fee_line_ids!=rezoning.nested[8].fee_line_ids
    assert 'CCN, RCN'==rezoning.nested[8].application_display
    assert '$150_+' in rezoning.nested[8].fee_display
    assert '_' not in rezoning.fee.native_text
    vacation=next(r for r in qa.rows if r.row_id=='P4-01')
    assert len(vacation.nested)==3
    assert all(entry.inherited_note_line_ids for entry in vacation.nested)


@pytest.mark.parametrize('case', [
    'fee_amount','condition_nor','unit','waiver','category_swap','same_fee_wrong_lines',
    'nested_missing','inherited_note','row_order','row_bbox','native_offset','native_geometry',
    'native_byte','context_omitted','header_erratum','date_erratum','glyph_certain','crop',
    'crop_page','repeat_pixels','graphic','custody_time','source_identity','frozen_identity',
    'custody_identity',
])
def test_semantic_tampering_is_rejected(qa,case):
    changed=qa.model_copy(deep=True)
    if case=='fee_amount':changed.rows[0].fee.reviewed_display='$500'
    elif case=='condition_nor':changed.rows[10].fee.reviewed_display=changed.rows[10].fee.reviewed_display.replace('nor','or')
    elif case=='unit':changed.rows[3].fee.reviewed_display=changed.rows[3].fee.reviewed_display.replace('acre','lot')
    elif case=='waiver':changed.rows[23].fee.reviewed_display=changed.rows[23].fee.reviewed_display.split('\n')[0]
    elif case=='category_swap':changed.rows[30].nested[0],changed.rows[30].nested[1]=changed.rows[30].nested[1],changed.rows[30].nested[0]
    elif case=='same_fee_wrong_lines':changed.rows[30].nested[8].fee_line_ids=changed.rows[30].nested[6].fee_line_ids
    elif case=='nested_missing':changed.rows[10].nested.pop()
    elif case=='inherited_note':changed.rows[41].nested[0].inherited_note_line_ids=[]
    elif case=='row_order':changed.rows[0],changed.rows[1]=changed.rows[1],changed.rows[0]
    elif case=='row_bbox':changed.rows[0].fee.bbox[0]=0.
    elif case=='native_offset':changed.pages[0].lines[0].start_byte=1
    elif case=='native_geometry':changed.pages[0].lines[1].bbox[0]+=1
    elif case=='native_byte':changed.pages[0].lines[1].text+='extra'
    elif case=='context_omitted':changed.pages[2].context_line_ids=[]
    elif case=='header_erratum':changed.annotations=[a for a in changed.annotations if a.id!='E03']
    elif case=='date_erratum':changed.annotations[1].pages=[1,4]
    elif case=='glyph_certain':changed.annotations[3].limitation='A certified encoded underscore.'
    elif case=='crop':changed.reproducible_crops[0].clip[2]-=10
    elif case=='crop_page':changed.reproducible_crops[-1].physical_page=1
    elif case=='repeat_pixels':changed.repeated_region_equality['printed_date'][1]='0'*64
    elif case=='graphic':changed.source_graphic_bbox[0]+=1
    elif case=='custody_time':changed.request_started_at=changed.response_finished_at
    elif case=='source_identity':changed.source.sha256='0'*64
    elif case=='frozen_identity':changed.pass1.sha256='0'*64
    elif case=='custody_identity':changed.custody_event.sha256='0'*64
    with pytest.raises(ValueError):verify_data(ROOT,changed)


@pytest.mark.parametrize('field,value',[('authority_id','CO-COUNTY-PUEBLO'),('answer_safe',True),
    ('legal_currentness','verified'),('adoption_verified',True),('monitoring_enrolled',True),
    ('physical_application_row_count',43),('native_byte_count',4922),('actual_page_count',3),
    ('source_date_claim','Effective 2026-02-13')])
def test_schema_does_not_allow_promotion_or_scope_changes(qa,field,value):
    data=json.loads(qa.model_dump_json());data[field]=value
    with pytest.raises(ValidationError):QA.model_validate_json(json.dumps(data))


@pytest.mark.parametrize('path',['../escape','/absolute','./alias','a\\b'])
def test_confined_evidence_paths(path):
    with pytest.raises(ValueError):Ref(path=path,sha256='0'*64,size_bytes=0)


def test_closed_portable_package(package):
    assert validate(package,True)['physical_rows']==44


@pytest.mark.parametrize('case',['extra','missing','body','native','original','symlink','fifo','inventory_duplicate'])
def test_closed_inventory_tampering(package,case):
    if case=='extra':(package/'extra.txt').write_text('not evidence')
    elif case=='missing':(package/'page-0004.png').unlink()
    elif case=='body':(package/'custody/events/E005/body.bin').write_bytes(b'%PDF-bad')
    elif case=='native':(package/'native/page-0001.txt').write_bytes(b'changed')
    elif case=='original':(package/'original.pdf').write_bytes(b'changed')
    elif case=='symlink':(package/'linked').symlink_to(package/'original.pdf')
    elif case=='fifo':
        import os;os.mkfifo(package/'named-pipe')
    else:
        data=json.loads((package/'MANIFEST.json').read_bytes());data['files'].append(data['files'][0]);(package/'MANIFEST.json').write_text(json.dumps(data))
    with pytest.raises(ValueError):validate(package)


def test_source_reextraction_rejects_resealed_native_edit(package,qa):
    p=package/'native/page-0001.txt';p.write_bytes(p.read_bytes().replace(b'$50',b'$60',1))
    with pytest.raises(ValueError,match='native extraction'):derive_tables(package,json.loads((package/'PASS1_frozen.json').read_bytes())['rows'])


def test_wrong_frozen_row_order_rejected(qa):
    data=json.loads((ROOT/'PASS1_frozen.json').read_bytes())['rows'];data[0],data[1]=data[1],data[0]
    with pytest.raises(ValueError,match='row ordering'):derive_tables(ROOT,data)


def test_wrong_frozen_fee_rejected():
    data=json.loads((ROOT/'PASS1_frozen.json').read_bytes())['rows'];data[0]['fee']='$60'
    with pytest.raises(ValueError,match='visual/native'):derive_tables(ROOT,data)


def test_no_overbroad_normalization():
    assert norm('- A-1\n• $100 + $1.00 per acre')=='A-1$100+$1.00peracre'
    assert norm('nor')!=norm('or')
    assert norm('$150_+')!=norm('$150 +')


@pytest.mark.parametrize('case',['redirect','anchor','private_header','body','crop_image'])
def test_custody_and_visual_proofs_are_replayed(package,qa,case):
    if case=='redirect':
        p=package/'custody/events/E004/event.json';data=json.loads(p.read_bytes());data['redirect_to']='https://example.invalid/wrong';p.write_text(json.dumps(data))
    elif case=='anchor':
        import hashlib
        p=package/'custody/events/E002/body.bin';body=p.read_bytes().replace(b'planning and zoning department fee schedule',b'nonexistent source label');p.write_bytes(body)
        digest=hashlib.sha256(body).hexdigest()
        for name,key in [('custody/events/E002/event.json','body'),('custody/OFFICIAL_LINKS.json','parent_body')]:
            p=package/name;data=json.loads(p.read_bytes());data[key]['sha256']=digest;data[key]['size_bytes']=len(body);p.write_text(json.dumps(data))
    elif case=='private_header':
        p=package/'custody/events/E002/event.json';data=json.loads(p.read_bytes());data['public_headers']['set-cookie']='not permitted';p.write_text(json.dumps(data))
    elif case=='body':(package/'custody/events/E004/body.bin').write_bytes(b'changed')
    else:(package/qa.reproducible_crops[0].artifact.path).write_bytes(b'not the crop')
    with pytest.raises(ValueError):verify_data(package,qa)


def test_cropped_full_page_cannot_pass_pixel_replay(package,qa):
    import pymupdf
    with pymupdf.open(package/'original.pdf') as doc:
        cropped=doc[0].get_pixmap(dpi=160,clip=pymupdf.Rect(0,0,612,400),alpha=False).tobytes('png')
    path=package/'page-0001.png';path.write_bytes(cropped)
    qa.pages[0].image=file_ref(package,path)
    with pytest.raises(ValueError,match='full source rendering'):verify_data(package,qa,True)


def test_source_byte_mismatch_fails_checked_read(tmp_path):
    root=tmp_path;p=root/'a';p.write_bytes(b'original');proof=file_ref(root,p);p.write_bytes(b'changed')
    with pytest.raises(ValueError,match='hash or size'):checked(root,proof)


def test_pair_list_shape_and_unknown_nested_text_fail():
    from qa_model import Cell,nested_entries
    cell=Cell(role='application',bbox=[0.,0.,1.,1.],pixel_bbox=[0,0,1,1],line_ids=[],native_text='',reviewed_display='Parent\n- child')
    fee=cell.model_copy(update={'role':'fee','reviewed_display':'$1\n$2'})
    with pytest.raises(ValueError,match='list lengths'):nested_entries('P1-08',cell,fee,[])
    fee.reviewed_display='$1'
    with pytest.raises(ValueError,match='not located'):nested_entries('P1-08',cell,fee,[])


def test_standalone_main_is_read_only(package,monkeypatch,capsys):
    import runpy,sys
    before={p.relative_to(package).as_posix():p.read_bytes() for p in package.rglob('*') if p.is_file()}
    monkeypatch.setattr(sys,'argv',[str(ROOT/'validate_qa.py'),'--root',str(package),'--rerender'])
    runpy.run_path(str(ROOT/'validate_qa.py'),run_name='__main__')
    assert json.loads(capsys.readouterr().out)['public_requests']==0
    assert before=={p.relative_to(package).as_posix():p.read_bytes() for p in package.rglob('*') if p.is_file()}
