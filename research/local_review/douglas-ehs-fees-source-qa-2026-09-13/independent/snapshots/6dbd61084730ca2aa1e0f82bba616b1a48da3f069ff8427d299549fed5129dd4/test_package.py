"""Offline source-proof refusal checks; mutate isolated copies, never frozen originals."""
import json
import shutil
import hashlib
from pathlib import Path
from types import SimpleNamespace
import pytest
import pymupdf
import validate_package as vp
from independent_models import Asset,Review
from qa_models import QA
from pass_models import Transcript


@pytest.fixture
def copied(tmp_path:Path)->Path:
    """Copy the complete bounded package into isolated test storage."""
    root=tmp_path/'package';shutil.copytree(vp.BASE,root);return root


def inputs(root:Path):
    """Return fresh typed structures for semantic adversarial mutations."""
    return (json.loads((root/'SOURCE_QA.json').read_bytes()),
            json.loads((root/'PASS1_frozen.json').read_bytes()),
            json.loads((root/'INDEPENDENT_REVIEW.json').read_bytes()))


def check(root:Path,q:dict,f:dict,r:dict,rerender:bool=False):
    """Validate data semantics without relying on the outer immutable manifest gate."""
    return vp.validate_qa(root,QA.model_validate_json(json.dumps(q)),
        Transcript.model_validate_json(json.dumps(f)),Review.model_validate_json(json.dumps(r)),rerender)


def ref(root:Path,name:str)->dict:
    data=(root/name).read_bytes()
    return Asset(path=name,sha256=hashlib.sha256(data).hexdigest(),size_bytes=len(data)).model_dump()


@pytest.mark.parametrize('rerender',[False,True])
def test_actual_complete_package(rerender:bool):
    result=vp.verify(rerender=rerender)
    assert (result['rows'],result['cells'],result['native_cell_lines'],result['blank_fee_cells'])==(44,220,218,2)
    assert result['poppler_replayed']==rerender
    assert result['legal_currentness']=='not_verified' and not result['answer_safe']


@pytest.mark.parametrize('issue',['amount','blank_zero','caption','footnote','note_text','offset',
    'bbox','blank_region','duplicate_field','context_line','wordmark','erratum','row_selection',
    'independent_row','crop_clip','header','caption_scope','authority'])
def test_semantic_mutations_refused(copied:Path,issue:str):
    q,f,r=inputs(copied)
    if issue=='amount':
        q['rows'][0]['cells'][4]['displayed_text']='$1.00'
        r['reviewed_rows'][0]['displayed_fields']['fee']='$1.00'
    elif issue=='blank_zero':
        q['rows'][-1]['cells'][4]['displayed_text']='$0.00'
        r['reviewed_rows'][-1]['displayed_fields']['fee']='$0.00'
    elif issue=='caption':q['rows'][0]['table_caption_id']='STATE-CAPTION'
    elif issue=='footnote':q['rows'][17]['footnote_id']=None
    elif issue=='note_text':q['contexts'][0]['text']='omitted conditions'
    elif issue=='offset':q['rows'][0]['cells'][0]['utf8_start']+=1
    elif issue=='bbox':q['rows'][0]['cells'][0]['displayed_bbox'][1]+=1
    elif issue=='blank_region':q['rows'][-1]['cells'][4]['blank_region'][0]-=20
    elif issue=='duplicate_field':q['rows'][0]['cells'][1]['field']='authority'
    elif issue=='context_line':q['contexts'][0]['native_lines']=[1]
    elif issue=='wordmark':q['contexts'][-1]['native_lines']=[1]
    elif issue=='erratum':q['errata'][0]['image_supported_text']=q['errata'][0]['frozen_text']
    elif issue=='row_selection':q['rows'][0]['row_id']='COUNTY-02'
    elif issue=='independent_row':r['reviewed_rows'][0]['source_qa_row_index']=1
    elif issue=='crop_clip':r['crops'][0]['displayed_pdf_clip'][0]+=5
    elif issue=='header':q['contexts'][4]['text']=q['contexts'][4]['text'].replace('2026','2027')
    elif issue=='caption_scope':q['contexts'][2]['applies_to']=q['contexts'][3]['applies_to']
    else:
        q['rows'][0]['cells'][0]['displayed_text']='25-4-1607'
        r['reviewed_rows'][0]['displayed_fields']['authority']='25-4-1607'
    with pytest.raises(ValueError):check(copied,q,f,r)


def test_cropped_full_proof_is_not_complete(copied:Path):
    q,f,r=inputs(copied)
    with pymupdf.open(copied/'original.pdf') as doc:
        data=doc[0].get_pixmap(dpi=150,clip=pymupdf.Rect(0,0,792,300)).tobytes('png')
    (copied/'page-0001.png').write_bytes(data)
    new=ref(copied,'page-0001.png');q['full_image']=new;r['original_full_image']=new
    f['image_sha256']=new['sha256']
    with pytest.raises(ValueError,match='cropped or invalid'):check(copied,q,f,r)


def test_native_truncation_refused_even_with_updated_hash(copied:Path):
    q,f,r=inputs(copied);p=copied/'candidate-native.txt';p.write_bytes(p.read_bytes()[:-10])
    new=ref(copied,'candidate-native.txt');q['native']=new;r['native']=new
    with pytest.raises(ValueError,match='Native replay'):check(copied,q,f,r)


@pytest.mark.parametrize('issue',['body','extra_manifest','symlink','escape'])
def test_custody_and_paths_refused(copied:Path,issue:str):
    if issue=='body':
        p=copied/'original.pdf';p.write_bytes(p.read_bytes()+b'changed')
    elif issue=='extra_manifest':
        p=copied/'extra';p.mkdir();(p/'FINAL_MANIFEST.json').write_text('{}')
    elif issue=='symlink':(copied/'extra-link').symlink_to(copied/'original.pdf')
    else:
        with pytest.raises(ValueError,match='Unsafe evidence path'):vp.safe(copied,'../outside')
        return
    with pytest.raises(ValueError):vp.verify(copied)


@pytest.mark.parametrize('issue',['missing','failed','wrong_bytes'])
def test_optional_poppler_failures_do_not_certify(copied:Path,monkeypatch,issue:str):
    q,f,r=inputs(copied)
    if issue=='missing':monkeypatch.setattr(vp.shutil,'which',lambda _name:None)
    else:
        def result(argv,**kwargs):
            if issue=='wrong_bytes':Path(argv[-1]+'.png').write_bytes(b'not rendered source')
            return SimpleNamespace(returncode=1 if issue=='failed' else 0)
        monkeypatch.setattr(vp.subprocess,'run',result)
    with pytest.raises(ValueError):check(copied,q,f,r,True)


def test_acquisition_source_mismatch(copied:Path):
    q,f,r=inputs(copied);p=copied/'acquisition-event.json';data=json.loads(p.read_bytes())
    data['body']['sha256']='0'*64;p.write_text(json.dumps(data))
    with pytest.raises(ValueError,match='Acquisition body'):check(copied,q,f,r)
