"""Bounded offline refusal checks using copies of the retained public evidence."""
import json
import shutil
from pathlib import Path
import pytest
import validate_package as vp
from models import Manifest,Preservation


@pytest.fixture
def copied(tmp_path:Path)->Path:
    """Leave every original and frozen source byte unchanged."""
    target=tmp_path/'package'
    shutil.copytree(vp.BASE,target)
    return target


def inputs(root:Path):
    """Load existing typed records for focused semantic refusal cases."""
    audit=Preservation.model_validate_json((root/'PRESERVATION.json').read_bytes())
    manifest=Manifest.model_validate_json((root/'FINAL_MANIFEST.json').read_bytes())
    return audit,{a.path:a for a in manifest.files}


def test_actual_package_is_offline_valid():
    result=vp.verify()
    assert result['recorded_gets']==4 and result['pdf_pages']==6
    assert result['canonical_writes']==result['new_public_requests']==0


@pytest.mark.parametrize('case',['pdf','nested_manifest','symlink'])
def test_closed_inventory_refuses_tampering(copied:Path,case:str):
    if case=='pdf':
        with (copied/'fresh/SD008-06/body.bin').open('ab') as stream:stream.write(b'changed')
    elif case=='nested_manifest':
        folder=copied/'unlisted';folder.mkdir();(folder/'FINAL_MANIFEST.json').write_text('{}')
    else:
        (copied/'unlisted').symlink_to(copied/'PRESERVATION.json')
    with pytest.raises(ValueError):vp.verify(copied)


@pytest.mark.parametrize('case',['status','private_header','time','length'])
def test_semantic_receipts_refuse_false_completion(copied:Path,case:str):
    audit,indexed=inputs(copied)
    path=copied/'fresh/SD008-06/receipt.json';receipt=json.loads(path.read_bytes())
    if case=='status':receipt['http_status']=403
    elif case=='private_header':receipt['headers']['set-cookie']='fixture-only'
    elif case=='time':receipt['started_at']='2026-09-12T23:00:00Z'
    else:receipt['headers']['content-length']='0'
    path.write_text(json.dumps(receipt))
    summary_path=copied/'fresh/summary.json';summary=json.loads(summary_path.read_bytes())
    summary['receipts'][1]=receipt;summary_path.write_text(json.dumps(summary))
    with pytest.raises(ValueError):vp.validate_content(copied,audit,indexed)


@pytest.mark.parametrize('case',['offset','qa_swap'])
def test_association_refusals(copied:Path,case:str):
    audit,indexed=inputs(copied)
    raw=audit.model_dump(mode='json')
    if case=='offset':raw['sources'][0]['anchor']['exact_source_start_byte']+=1
    else:
        raw['sources'][0]['prior_qa']=raw['sources'][1]['prior_qa']
        raw['sources'][0]['prior_qa_schema']=raw['sources'][1]['prior_qa_schema']
    changed=Preservation.model_validate_json(json.dumps(raw))
    with pytest.raises((ValueError,KeyError)):
        vp.validate_content(copied,changed,indexed)
