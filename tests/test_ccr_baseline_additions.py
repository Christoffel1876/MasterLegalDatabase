"""Native page identities and immutable-reference boundaries; no network access."""
from pathlib import Path
from types import SimpleNamespace
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from verify_ccr_baseline_additions import (
    Asset,Index,Original,Page,Reader,check_counts,ledger,merge,native_ledger,safe_path,sha,
)

def original(digest:str='a'*64,numbers:tuple[int,...]=(1,),text:str='b'*64)->Original:
    """Create a small exact physical-page sequence for boundary cases."""
    return Original(sha256=digest,pages=[Page(physical_page=n,text_sha256=text,text_bytes=2) for n in numbers])

def encoded(row:Original)->bytes:
    """Encode a typed original as one JSONL row."""
    return (row.model_dump_json()+'\n').encode()

def index_for(prior:dict[str,Original],new:dict[str,Original])->Index:
    """Prepare coherent counters without reading any corpus files."""
    ref=Asset(path='dummy',sha256='0'*64,bytes=0)
    union=prior|new
    overlap=set(prior)&set(new)
    count=lambda data:sum(len(x.pages) for x in data.values())
    return Index(generated_at='2026-10-05',packages=[],prior_index=ref,prior_page_sets=[],new_page_set=ref,original_schema=ref,previous_pdfs=len(prior),previous_pages=count(prior),added_whole_rule_identities=1,new_distinct_pdfs=len(new),new_distinct_pages=count(new),overlap_pdfs=len(overlap),overlap_pages=sum(len(new[d].pages) for d in overlap),union_pdfs=len(union),union_pages=count(union))

def test_complete_ledger()->None:
    row=original(numbers=(1,2))
    assert ledger(encoded(row))=={row.sha256:row}

@pytest.mark.parametrize('numbers',[(2,),(1,1),(1,3),(2,1),()])
def test_missing_duplicate_out_of_order_pages(numbers:tuple[int,...])->None:
    with pytest.raises(ValueError):ledger(encoded(original(numbers=numbers)))

def test_duplicate_original_row()->None:
    raw=encoded(original())
    with pytest.raises(ValueError,match='Duplicate original'):ledger(raw+raw)

@pytest.mark.parametrize('raw',[b'',b'\n',b'{}\n'])
def test_empty_or_invalid_ledger(raw:bytes)->None:
    with pytest.raises(ValueError):ledger(raw)

def test_manifest_page_binding()->None:
    refs=[SimpleNamespace(path='native/'+'a'*64+'/000001.txt',sha256='b'*64,size_bytes=2)]
    assert native_ledger(refs)=={'a'*64:original()}
    with pytest.raises(ValueError,match='Duplicate native'):native_ledger(refs+refs)

def test_bad_native_page_path()->None:
    refs=[SimpleNamespace(path='native/'+'a'*64+'/1.txt',sha256='b'*64,size_bytes=2)]
    with pytest.raises(ValueError,match='Malformed'):native_ledger(refs)

def test_merge_deduplicates_agreeing_physical_pages()->None:
    rows={'a'*64:original()}
    merge(rows,{'a'*64:original()})
    assert len(rows)==1

def test_merge_rejects_conflicting_native_text()->None:
    with pytest.raises(ValueError,match='Conflicting'):
        merge({'a'*64:original()},{'a'*64:original(text='c'*64)})

def test_exact_overlap_not_double_counted()->None:
    prior={'a'*64:original()}
    new={'a'*64:original(),'c'*64:original(digest='c'*64,numbers=(1,2))}
    result=check_counts(index_for(prior,new),prior,new,{'42'})
    assert result['union_pages']==3 and result['overlap_pages']==1

@pytest.mark.parametrize('field',['previous_pdfs','previous_pages','added_whole_rule_identities','new_distinct_pdfs','new_distinct_pages','overlap_pdfs','overlap_pages','union_pdfs','union_pages'])
def test_inflated_counter_rejected(field:str)->None:
    prior={'a'*64:original()};new={'c'*64:original(digest='c'*64)}
    index=index_for(prior,new)
    changed=index.model_copy(update={field:getattr(index,field)+1})
    with pytest.raises(ValueError,match='counts differ'):check_counts(changed,prior,new,{'42'})

def test_changed_source_reference(tmp_path:Path)->None:
    (tmp_path/'body').write_bytes(b'body')
    ref=Asset(path='body',sha256=sha(b'body'),bytes=4)
    assert Reader(tmp_path).read(ref)==b'body'
    (tmp_path/'body').write_bytes(b'edit')
    with pytest.raises(ValueError,match='hash'):Reader(tmp_path).read(ref)

def test_oversized_reference_rejected_before_read(tmp_path:Path)->None:
    with pytest.raises(ValueError,match='file cap'):
        Reader(tmp_path).read(Asset(path='absent',sha256='0'*64,bytes=25_000_001))

def test_symlink_reference(tmp_path:Path)->None:
    (tmp_path/'body').write_bytes(b'x');(tmp_path/'link').symlink_to(tmp_path/'body')
    with pytest.raises(ValueError,match='Symlink'):
        Reader(tmp_path).read(Asset(path='link',sha256=sha(b'x'),bytes=1))

@pytest.mark.parametrize('path',['../outside','/absolute','a/../b','a\\b'])
def test_unsafe_relative_path(path:str)->None:
    with pytest.raises(ValueError):safe_path(path)
