"""Source coverage boundary checks with no HTTP or corpus mutation."""
import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from verify_ccr_baseline import Asset,Selector,read,sha,validate_partition,validate_capture_selectors

def row(a='7',r='2333'):
    return Selector(agency_id=a,rule_id=r)

def test_valid_partition():
    validate_partition([row(),row(r='2334')],[row()],[row(r='2334')])

@pytest.mark.parametrize('declared',[[row(),row()],[],[row(a='15')],[row(),row(r='9999')]])
def test_duplicate_missing_foreign_capture_selector(declared):
    with pytest.raises(ValueError):validate_capture_selectors(declared,{('7','2333')})

@pytest.mark.parametrize('listed,paired,missing',[
    ([row(),row()],[row()],[]),
    ([row()],[row(a='15')],[]),
    ([row()],[],[]),
    ([row()],[row()],[row()]),
])
def test_invalid_partition(listed,paired,missing):
    with pytest.raises(ValueError):validate_partition(listed,paired,missing)

def test_changed_source_reference(tmp_path):
    p=tmp_path/'source';p.write_bytes(b'original')
    ref=Asset(path='source',sha256=sha(b'original'),bytes=8)
    assert read(tmp_path,ref)==b'original'
    p.write_bytes(b'changed!')
    with pytest.raises(ValueError,match='hash'):read(tmp_path,ref)

def test_missing_source(tmp_path):
    with pytest.raises(ValueError):read(tmp_path,Asset(path='absent',sha256='0'*64,bytes=0))

def test_symlink_source(tmp_path):
    p=tmp_path/'source';p.write_bytes(b'x');(tmp_path/'link').symlink_to(p)
    with pytest.raises(ValueError):read(tmp_path,Asset(path='link',sha256=sha(b'x'),bytes=1))

@pytest.mark.parametrize('path',['../source','/absolute','a/../b','a\\b'])
def test_unsafe_path(path):
    with pytest.raises(ValueError):Asset(path=path,sha256='0'*64,bytes=0)
