"""Offline corruption tests; no source changes, transport, or OCR reruns."""
import copy
import hashlib
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

import verify_source_review as v
from models import Manifest, Ref

ROOT = Path(__file__).resolve().parent


@pytest.fixture(scope='session')
def buffers() -> dict[str, bytes]:
    """Read the immutable source-review evidence for in-memory probes."""
    return {p.relative_to(ROOT).as_posix():p.read_bytes() for p in ROOT.rglob('*') if p.is_file()}


def replace_qa(buffers: dict[str,bytes], change: object) -> dict[str,bytes]:
    """Modify only an in-memory QA record, bypassing closure to test inner binding gates."""
    result=dict(buffers)
    qa=json.loads(result['SOURCE_QA.json'])
    change(qa)
    result['SOURCE_QA.json']=json.dumps(qa).encode()
    return result


def test_complete_evidence_and_rerender(buffers: dict[str,bytes]) -> None:
    """Replay the complete reviewed pages, uncorrected OCR and fresh full Poppler renders."""
    result=v.verify_review(buffers)
    assert (result['physical_pages'],result['segments'],result['ocr_lines'])==(14,174,432)
    assert result['native_bytes']==0 and result['answer_safe'] is False
    executable=Path('/Users/mcoors/.cache/codex-runtimes/codex-primary-runtime/'
                    'dependencies/bin/override/pdftoppm')
    v.rerender(buffers,executable)


@pytest.mark.parametrize('change',[
    lambda q:q.update(authority_id='CO-MUNICIPAL-SALIDA'),
    lambda q:q.update(source_id='another-source'),
    lambda q:q.update(answer_safe=True),
    lambda q:q.update(legal_currentness='verified'),
    lambda q:q.update(verified_adoption_date='2026-05-19'),
    lambda q:q['pages'].pop(),
    lambda q:q['pages'].reverse(),
    lambda q:q['pages'][0].update(image=q['pages'][1]['image']),
    lambda q:q['pages'][0].update(ocr_line_count=35),
    lambda q:q['pages'][0]['segment_ids'].reverse(),
    lambda q:q['segments'][0].update(image_path='pages/page-02.png'),
    lambda q:q['segments'][0].update(pixel_rect=[0,0,2551,20]),
    lambda q:q['segments'][0].update(crop_paths=['crops/page-02-top.png']),
    lambda q:q['segments'][0]['ocr_line_numbers'].pop(),
    lambda q:q['segments'][0].update(ocr_line_numbers=[0,1,2,3]),
    lambda q:q['segments'][0].update(ocr_span=None),
    lambda q:q['segments'][0].update(ocr_text='wrong recorder text\n'),
    lambda q:q['segments'][0]['ocr_span'].update(start=1),
    lambda q:q['segments'][0].update(checked_span=None),
    lambda q:q['segments'][0]['checked_span'].update(start=1),
    lambda q:q['segments'][0].update(checked_text=None),
    lambda q:q['segments'][0].update(continuation_of='absent-id'),
    lambda q:q['segments'][0].update(id=q['segments'][1]['id']),
    lambda q:q['observations'][0].update(segment_ids=['absent']),
    lambda q:q['date_claims'][0].update(segment_ids=[]),
    lambda q:q['acquisition'].update(actual_completed_at='2026-06-01T08:47:00Z'),
    lambda q:q['acquisition'].update(final_url='https://example.com/another.pdf'),
    lambda q:q['source'].update(path='../outside.pdf'),
    lambda q:q['source'].update(path='missing.pdf'),
    lambda q:q['source'].update(size_bytes=1),
    lambda q:q.update(source_sha='0'*64),
    lambda q:q['segments'][0].update(ocr_line_numbers=[1,3]),
])
def test_qa_binding_refusals(buffers: dict[str,bytes],change: object) -> None:
    """Reject changed ownership, time, scope, order, spans, and unbound source context."""
    with pytest.raises((ValueError,KeyError,IndexError,jsonschema_error())):
        v.verify_review(replace_qa(buffers,change))


def jsonschema_error() -> type[Exception]:
    """Return the independent JSON Schema validation error class."""
    return v.jsonschema.ValidationError


@pytest.mark.parametrize('field', ['start','end','text'])
def test_strike_binding_refuses_modification(buffers: dict[str,bytes],field: str) -> None:
    """Material struck conjunction remains bound to exact reviewed text offsets."""
    def change(q: dict) -> None:
        segment=next(s for s in q['segments'] if s['id']=='CWRC-P06-S08')
        mark=next(m for m in segment['markup'] if m['kind']=='strikethrough')
        mark[field]='and' if field=='text' else mark[field]+1
    with pytest.raises(ValueError):
        v.verify_review(replace_qa(buffers,change))


@pytest.mark.parametrize('path', [
    'source/original.pdf','native/page-0001.txt','ocr/page-0001/candidate.txt',
    'pages/page-01.png','ocr/page-0001/stdout.json','ocr/page-0001/stderr.txt',
    'transcript/page-0001.txt','custody/retrieval/events/A001/RESULT.json',
])
def test_payload_hash_refusal(buffers: dict[str,bytes],path: str) -> None:
    """Reject altered exact source, OCR, images, transcript and acquisition records."""
    changed=dict(buffers);changed[path]+=b'x'
    with pytest.raises(ValueError):
        v.verify_review(changed)


@pytest.mark.parametrize('which', ['missing','duplicate','raw','checked'])
def test_corrections_and_crop_coverage(buffers: dict[str,bytes],which: str) -> None:
    """Reject lost crop coverage and false raw/corrected text relations."""
    changed=dict(buffers)
    if which=='missing':
        changed['CROPS.jsonl']=b'\n'.join(changed['CROPS.jsonl'].splitlines()[:-1])+b'\n'
    else:
        rows=[json.loads(x) for x in changed['CORRECTIONS.jsonl'].splitlines()]
        if which=='duplicate':rows.append(rows[0])
        elif which=='raw':rows[0]['raw_ocr']='not the candidate'
        else:rows[0]['checked']='not the reviewed source'
        changed['CORRECTIONS.jsonl']=b'\n'.join(json.dumps(x).encode() for x in rows)+b'\n'
    with pytest.raises(ValueError):
        v.verify_review(changed)


@pytest.mark.parametrize('name',['../x','/x','a//b','a/./b','a\\b',''])
def test_unsafe_paths(name: str) -> None:
    """Reject paths that may escape or ambiguously name evidence."""
    with pytest.raises(ValueError):v.safe_name(name)


def minimal_package(root: Path) -> None:
    """Create a tiny closed fixture to test custody independently from source semantics."""
    data={'MANIFEST.schema.json':json.dumps(Manifest.model_json_schema()).encode(),
          'nested/input.txt':b'fixed'}
    for name,value in data.items():
        target=root/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(value)
    records=[Ref(path=n,sha256=hashlib.sha256(b).hexdigest(),size_bytes=len(b))
             for n,b in sorted(data.items())]
    manifest=Manifest(schema_version='cwrc-closed-payloads-1',created_at='2026-09-13T16:30:00Z',
                      files=records,payload_count=len(records))
    (root/'FINAL_MANIFEST.json').write_text(manifest.model_dump_json())


@pytest.mark.parametrize('attack',['extra','missing','symlink','emptydir','duplicate','badcount'])
def test_closed_inventory(tmp_path: Path,attack: str) -> None:
    """Refuse additional/missing/aliased payloads and inconsistent manifests."""
    minimal_package(tmp_path)
    assert v.capture(tmp_path)['nested/input.txt']==b'fixed'
    if attack=='extra':(tmp_path/'extra').write_text('extra')
    elif attack=='missing':(tmp_path/'nested/input.txt').unlink()
    elif attack=='symlink':(tmp_path/'alias').symlink_to(tmp_path/'nested/input.txt')
    elif attack=='emptydir':(tmp_path/'empty').mkdir()
    else:
        p=tmp_path/'FINAL_MANIFEST.json';m=json.loads(p.read_text())
        if attack=='duplicate':m['files'].append(m['files'][0])
        else:m['payload_count']=99
        p.write_text(json.dumps(m))
    with pytest.raises(ValueError):v.capture(tmp_path)


def test_symlink_ancestor(tmp_path: Path) -> None:
    """Refuse even a correct file reached through a lexical symlink ancestor."""
    (tmp_path/'real').mkdir();(tmp_path/'real/x').write_text('x')
    (tmp_path/'alias').symlink_to(tmp_path/'real',target_is_directory=True)
    with pytest.raises(ValueError):v.ordinary(tmp_path/'alias/x')
    with pytest.raises(ValueError):v.ordinary(tmp_path/'missing')


def test_renderer_failures(buffers: dict[str,bytes],monkeypatch: pytest.MonkeyPatch) -> None:
    """Refuse an unpinned executable and a failed render without modifying evidence."""
    with pytest.raises(ValueError):v.rerender(buffers,ROOT/'models.py')
    monkeypatch.setattr(v,'ordinary',lambda path:b'fake')
    monkeypatch.setattr(v,'POPPLER_SHA',v.digest(b'fake'))
    monkeypatch.setattr(v.subprocess,'run',lambda *a,**kw:SimpleNamespace(returncode=1))
    with pytest.raises(ValueError):v.rerender(buffers,Path('/fixture/renderer'))


def test_cli_on_minimal_fixture_refuses(tmp_path: Path) -> None:
    """An actual separate-process CLI cannot emit a source result from custody alone."""
    minimal_package(tmp_path)
    result=subprocess.run([__import__('sys').executable,'-B',str(ROOT/'verify_source_review.py'),
                           '--root',str(tmp_path)],capture_output=True,timeout=30,check=False)
    assert result.returncode!=0 and b'"status": "PASS"' not in result.stdout
