"""Local preflight and evidence safety checks; no public actions."""
from datetime import datetime,timezone
from pathlib import Path
import json,hashlib
import pytest
from budget import ROOT,CUTOFF,reserve,complete,load_log,save_new,counters
from models import Reservation,Result,ActionLog,Asset
NOW=datetime(2026,9,13,15,30,tzinfo=timezone.utc)
URLS=[x['encoded_requested_url'] for x in json.loads((ROOT/'TARGETS.json').read_bytes())]
def res(n):
 return Reservation(action_id=f'SHEXT004-A{n:03}',authority_id='CO-COUNTY-CHAFFEE',reserved_at=NOW,tool_name='test',action_kind='open',requested_url=URLS[(n-1)%4],basis='fixed target',budget_checked=True)
def result(n):
 return Result(action_id=f'SHEXT004-A{n:03}',finished_at=NOW,observed_final_url=URLS[(n-1)%4],visible_redirect_urls=[],outcome='response',body_role='no_body',retained_assets=[],pdf_magic_checked=False,pdf_parse_succeeded=False,notes='fixture',body_size_basis='no_body_observed',observed_body_bytes=0)
def test_serial_and_four_target_cap(tmp_path):
 reserve(tmp_path,res(1),NOW)
 with pytest.raises(ValueError):reserve(tmp_path,res(2),NOW)
 complete(tmp_path,result(1),NOW)
 for n in range(2,5):reserve(tmp_path,res(n),NOW);complete(tmp_path,result(n),NOW)
 assert not counters(load_log(tmp_path),NOW).can_reserve
 with pytest.raises(ValueError):reserve(tmp_path,res(5),NOW)
 assert len(load_log(tmp_path).reservations)==4
@pytest.mark.parametrize('kind',['foreign','search','retry','denied','cutoff'])
def test_preflight_blocks_before_write(tmp_path,kind):
 n=1;value=res(n);now=NOW
 if kind in {'retry','denied'}:
  reserve(tmp_path,value,NOW);complete(tmp_path,result(1).model_copy(update={'outcome':'access_denied' if kind=='denied' else 'response'}),NOW);n=2;value=res(n).model_copy(update={'requested_url':URLS[0]})
 if kind=='foreign':value=value.model_copy(update={'requested_url':'https://example.invalid/'})
 if kind=='search':value=value.model_copy(update={'requested_url':None,'action_kind':'search','search_query':'x'})
 if kind=='cutoff':now=CUTOFF;value=value.model_copy(update={'reserved_at':now})
 with pytest.raises(ValueError):reserve(tmp_path,value,now)
 assert len(load_log(tmp_path).reservations)==n-1
@pytest.mark.parametrize('update',[{'visible_redirect_urls':['https://example.invalid/hop']},{'observed_final_url':'https://example.invalid/hop'}])
def test_unexpected_hop_preserved_then_blocks(tmp_path,update):
 reserve(tmp_path,res(1),NOW)
 with pytest.raises(ValueError):complete(tmp_path,result(1).model_copy(update=update),NOW)
 assert (tmp_path/'results/SHEXT004-A001.json').exists()
 assert not counters(load_log(tmp_path),NOW).can_reserve
@pytest.mark.parametrize('basis',['unknown','retained_partial'])
def test_incomplete_accounting_stops(tmp_path,basis):
 reserve(tmp_path,res(1),NOW)
 update={'body_size_basis':basis,'observed_body_bytes':None}
 if basis=='retained_partial':
  data=b'partial';(tmp_path/'partial.bin').write_bytes(data);h=hashlib.sha256(data).hexdigest();update.update(body_sha256=h,observed_body_bytes=len(data),retained_assets=[Asset(path='partial.bin',sha256=h,size_bytes=len(data))])
 assert not complete(tmp_path,result(1).model_copy(update=update),NOW).can_reserve
 with pytest.raises(ValueError):reserve(tmp_path,res(2),NOW)
def test_identity_and_immutable_records(tmp_path):
 reserve(tmp_path,res(1),NOW);data=b'x';(tmp_path/'x').write_bytes(data)
 bad=result(1).model_copy(update={'retained_assets':[Asset(path='x',sha256='0'*64,size_bytes=1)]})
 with pytest.raises(ValueError):complete(tmp_path,bad,NOW)
 assert not (tmp_path/'results/SHEXT004-A001.json').exists()
 complete(tmp_path,result(1),NOW)
 before=(tmp_path/'results/SHEXT004-A001.json').read_bytes()
 with pytest.raises(FileExistsError):save_new(tmp_path/'results/SHEXT004-A001.json',result(2))
 assert (tmp_path/'results/SHEXT004-A001.json').read_bytes()==before
@pytest.mark.parametrize('size,count',[(20_000_001,1),(20_000_000,4)])
def test_per_body_and_aggregate_caps(size,count):
 results=[]
 for n in range(1,count+1):
  asset=Asset(path=f'{n}.bin',sha256='a'*64,size_bytes=size)
  results.append(result(n).model_copy(update={'retained_assets':[asset],'body_sha256':asset.sha256,'body_size_basis':'retained_complete','observed_body_bytes':size}))
 with pytest.raises(ValueError):ActionLog(reservations=[res(n) for n in range(1,count+1)],results=results)
def test_symlink_state_refused(tmp_path):
 (tmp_path/'link').symlink_to(tmp_path,target_is_directory=True)
 with pytest.raises(ValueError):load_log(tmp_path/'link')
