"""Offline semantic mutation checks, including rehashed malicious data changes."""
import copy,json,shutil,sys,tempfile
from pathlib import Path
from hashlib import sha256
import pytest
sys.path.insert(0,str(Path(__file__).absolute().parent))
from validate_review import validate,load,safe,ordinary
from review_models import Inventory,Asset
ROOT=Path(__file__).absolute().parent
@pytest.fixture
def pkg():
 with tempfile.TemporaryDirectory(prefix='csfd-test-',dir='/private/tmp') as td:
  p=Path(td)/'review';shutil.copytree(ROOT,p);yield p

def save(p,obj):p.write_text(json.dumps(obj,indent=2)+'\n')
def repin(p):
 # Intentionally rehash the outer inventory: semantic checks must still reject bad associations.
 m=load(p/'FINAL_MANIFEST.json')
 m['files']=[{'path':f.relative_to(p).as_posix(),'sha256':sha256(f.read_bytes()).hexdigest(),'size_bytes':f.stat().st_size} for f in sorted(p.rglob('*')) if f.is_file() and f.relative_to(p).as_posix() not in {'FINAL_MANIFEST.json','FINAL_MANIFEST.schema.json'}]
 save(p/'FINAL_MANIFEST.json',Inventory.model_validate(m).model_dump())
def change(p,fn):
 q=load(p/'SOURCE_QA.json');fn(q);save(p/'SOURCE_QA.json',q);repin(p)
def block(q,name):return next(b for b in q['blocks'] if b['block_id']==name)
def test_complete_read_only(pkg):
 before={p.relative_to(pkg).as_posix():sha256(p.read_bytes()).hexdigest() for p in pkg.rglob('*') if p.is_file()}
 out=validate(pkg);assert out.fee_rows==128 and out.native_lines==410 and out.native_bytes==14423
 after={p.relative_to(pkg).as_posix():sha256(p.read_bytes()).hexdigest() for p in pkg.rglob('*') if p.is_file()};assert before==after
@pytest.mark.parametrize('mutate,match',[
 (lambda q:q.update(authority_id='CO-DISTRICT-PPRBD'),'literal'),
 (lambda q:q.update(legal_currentness='verified'),'literal'),
 (lambda q:q.update(effective_date_verification='adopted'),'literal'),
 (lambda q:q['provenance'].update(request_started_at='2026-07-01T00:00:00Z'),'literal'),
 (lambda q:q['provenance'].update(official_url='https://example.com/fees.pdf'),'literal'),
 (lambda q:q['pages'].reverse(),'page order'),
 (lambda q:q['fee_rows'].pop(),'128'),
 (lambda q:q['fee_rows'][0]['label'].update(exact_native_text='Inspection first fire hydrant \n'),'wording'),
 (lambda q:q['fee_rows'][0]['fee_as_printed'].update(exact_native_text='$215.00 \n'),'wording'),
 (lambda q:q['fee_rows'][0]['label']['native_ranges'][0].__setitem__(0,0),'offset'),
 (lambda q:q['fee_rows'][0]['label']['pixel_bboxes'][0].__setitem__(0,0),'geometry'),
 (lambda q:q['fee_rows'][0]['label'].update(role='fee_as_printed'),'role swapped'),
 (lambda q:q['fee_rows'][0]['global_context_ids'].remove('IMPLEMENTATION'),'global'),
 (lambda q:q['fee_rows'][0]['global_context_ids'].remove('OTHER-SCHEDULE'),'global'),
 (lambda q:q['fee_rows'][0]['global_context_ids'].remove('P4-MISC-01'),'global'),
 (lambda q:next(r for r in q['fee_rows'] if r['table_id']=='sprinkler')['table_context_ids'].clear(),'linked'),
 (lambda q:next(r for r in q['fee_rows'] if r['table_id']=='construction')['definition_ids'].remove('DEF-CONSTRUCTION-PLAN-CHECK'),'linked'),
 (lambda q:block(q,'DEF-REINSPECTION')['parts'].pop(),'continuation'),
 (lambda q:block(q,'DEF-EXPEDITED')['parts'][0]['line_ids'].pop(),'associations'),
 (lambda q:block(q,'SPRINKLER-INSPECTIONS')['parts'][0].update(exact_native_text='Three inspections.\n'),'wording'),
 (lambda q:q['tables'][1]['page_order'].remove(3),'continuation'),
 (lambda q:q['tables'][0]['row_ids'].reverse(),'continuation'),
 (lambda q:q.update(native_byte_count=14422),'native scope'),
 (lambda q:q['fee_rows'][0].update(calculated_fee=258.0),'Extra inputs'),
])
def test_rehashed_semantic_mutations(pkg,mutate,match):
 change(pkg,mutate)
 with pytest.raises((ValueError,KeyError),match=match):validate(pkg)
def test_swap_complete_fee_cells(pkg):
 def swap(q):q['fee_rows'][0]['fee_as_printed'],q['fee_rows'][1]['fee_as_printed']=q['fee_rows'][1]['fee_as_printed'],q['fee_rows'][0]['fee_as_printed']
 change(pkg,swap)
 with pytest.raises(ValueError,match='associations'):validate(pkg)
def test_rehashed_source_change(pkg):
 with (pkg/'source/original.pdf').open('ab') as f:f.write(b'\n')
 repin(pkg)
 with pytest.raises(ValueError,match='asset hash/size'):validate(pkg)
def test_native_changed_with_rebound_asset(pkg):
 p=pkg/'native/page-0002.txt';p.write_bytes(p.read_bytes().replace(b'$258.00',b'$259.00',1))
 change(pkg,lambda q:q['pages'][1]['native'].update(sha256=sha256(p.read_bytes()).hexdigest()))
 with pytest.raises(ValueError,match='native extraction'):validate(pkg)
def test_geometry_changed_with_rebound_asset(pkg):
 p=pkg/'native/page-0002.geometry.json';g=load(p);g['lines'][10]['bbox'][0]=0.0;save(p,g)
 change(pkg,lambda q:q['pages'][1]['geometry'].update(sha256=sha256(p.read_bytes()).hexdigest(),size_bytes=p.stat().st_size))
 with pytest.raises(ValueError,match='geometry or byte'):validate(pkg)
def test_crop_bounds_changed(pkg):
 p=pkg/'CROPS.json';c=load(p);c[0]['pixel_bbox'][0]=-5;save(p,c);repin(pkg)
 with pytest.raises(ValueError,match='crop bounds'):validate(pkg)
def test_closed_extra_file(pkg):
 (pkg/'unexpected.txt').write_text('not frozen')
 with pytest.raises(ValueError,match='closed file'):validate(pkg)
def test_missing_file(pkg):
 (pkg/'native/page-0007.txt').unlink()
 with pytest.raises(ValueError,match='closed file'):validate(pkg)
def test_symlink_file(pkg):
 p=pkg/'native/page-0007.txt';p.unlink();p.symlink_to(pkg/'native/page-0006.txt')
 with pytest.raises(ValueError,match='symlink'):validate(pkg)
@pytest.mark.parametrize('path',['../outside','/etc/passwd','native/../SOURCE_QA.json','./SOURCE_QA.json','native\\page-0001.txt','native//page-0001.txt'])
def test_path_escape_refused_before_open(pkg,path):
 with pytest.raises(ValueError,match='unsafe path'):safe(pkg,path)
def test_symlink_ancestor(pkg):
 link=pkg.parent/'alias';link.symlink_to(pkg, target_is_directory=True)
 with pytest.raises(ValueError,match='symlink'):validate(link)
def test_duplicate_json_key(pkg):
 p=pkg/'SOURCE_QA.json';p.write_text(p.read_text().replace('{','{"schema_version":"1.0",',1));repin(pkg)
 with pytest.raises(ValueError,match='duplicate JSON key'):validate(pkg)
def test_result_partial_not_complete(pkg):
 p=pkg/'custody/result.json';x=load(p);x['partial_body']=True;save(p,x)
 change(pkg,lambda q:next(a for a in q['provenance']['receipts'] if a['path']=='custody/result.json').update(sha256=sha256(p.read_bytes()).hexdigest(),size_bytes=p.stat().st_size))
 with pytest.raises(ValueError,match='literal'):validate(pkg)
def test_native_blank_line_not_dropped(pkg):
 change(pkg,lambda q:q['blocks'].__setitem__(slice(None),[b for b in q['blocks'] if b['block_id']!='UNASSIGNED-P1-L001']))
 with pytest.raises(ValueError,match='footer/whitespace'):validate(pkg)
def test_two_variable_rates_are_literal(pkg):
 q=load(pkg/'SOURCE_QA.json');rates=[r['fee_as_printed']['exact_native_text'].strip() for r in q['fee_rows']]
 assert rates.count('0.04/sq. ft.')==2
 assert '1.5x Review \nFee' in rates and '2x Permit \nFee' in rates and 'IRS Standard \nMileage Rate' in rates
