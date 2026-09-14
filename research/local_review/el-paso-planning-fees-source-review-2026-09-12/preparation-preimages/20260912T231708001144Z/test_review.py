"""Offline adversarial checks; all mutations occur in disposable package copies."""
from pathlib import Path
import copy,hashlib,json,shutil,sys
import pytest
HERE=Path(__file__).absolute().parent;sys.path.insert(0,str(HERE))
from validate_review import validate,body
from review_models import Asset

def sha(b):return hashlib.sha256(b).hexdigest()
def save(path,data):path.write_text(json.dumps(data,indent=2)+'\n')
def load(path):return json.loads(path.read_bytes())
@pytest.fixture
def package(tmp_path):
 target=tmp_path/'package';shutil.copytree(HERE,target);return target

def repin(root):
 # Rebind byte references to expose semantic gates, not merely inventory hashes.
 for unused in range(5):
  for p in root.rglob('*.json'):
   if p.name in ['FINAL_MANIFEST.json'] or 'preparation-preimages' in p.parts:continue
   try:data=load(p)
   except ValueError:continue
   changed=False
   def walk(v):
    nonlocal changed
    if isinstance(v,dict):
     if set(['path','sha256','size_bytes'])<=set(v) and isinstance(v['path'],str):
      target=root/v['path']
      if target.is_file() and not target.is_symlink():
       b=target.read_bytes();new=(sha(b),len(b))
       if (v['sha256'],v['size_bytes'])!=new:v['sha256'],v['size_bytes']=new;changed=True
     for x in v.values():walk(x)
    elif isinstance(v,list):
     for x in v:walk(x)
   walk(data)
   if changed:save(p,data)
 inv=load(root/'FINAL_MANIFEST.json');inv['files']=[]
 for p in sorted(root.rglob('*')):
  if p.is_file() and p not in [root/'FINAL_MANIFEST.json',root/'FINAL_MANIFEST.schema.json']:
   b=p.read_bytes();inv['files'].append({'path':p.relative_to(root).as_posix(),'sha256':sha(b),'size_bytes':len(b)})
 save(root/'FINAL_MANIFEST.json',inv)

def mutate_grid(root,fn):
 p=root/'REVIEWED_GRID.json';data=load(p);fn(data);save(p,data);repin(root)

def row(data,id):return next(x for x in data['rows'] if x['id']==id)

def test_actual_package_valid(package):
 result=validate(package)
 assert result['fee_rows']==104 and result['native_bytes']==0
 assert result['explicit_unresolved_rows']==['P3-ENG-14']
 assert result['legal_currentness']=='not_verified'

@pytest.mark.parametrize('mutation',[
 lambda d:row(d,'P3-ENG-04')['cells'][1].update(text='$10,478.00'),
 lambda d:row(d,'P1-PLAN-01')['cells'][2].update(text='D'),
 lambda d:row(d,'P1-PLAN-15')['cells'][0].update(superscript_footnotes=[3]),
 lambda d:row(d,'P3-PLAN-01').update(section_header_id='ENGINEERING-MAJOR'),
 lambda d:row(d,'P1-PLAN-01')['cells'][0].update(pixel_bbox=[200,408,1761,445]),
 lambda d:row(d,'P3-ENG-14')['cells'][0].update(state='visible_text'),
 lambda d:d['rows'].pop(5),
 lambda d:d['rows'].insert(5,copy.deepcopy(d['rows'][5])),
 lambda d:row(d,'P1-PLAN-01')['cells'][0].update(transcript_start_byte=0),
])
def test_rejects_semantic_grid_mutation_after_repin(package,mutation):
 mutate_grid(package,mutation)
 with pytest.raises(ValueError):validate(package)

def test_fee_swap_same_length_cannot_move_between_rows(package):
 def mutate(d):
  a=row(d,'P3-ENG-03')['cells'][1];b=row(d,'P3-ENG-04')['cells'][1]
  a['text'],b['text']=b['text'],a['text']
 mutate_grid(package,mutate)
 with pytest.raises(ValueError):validate(package)

def test_blank_project_cannot_inherit_neighbor_code(package):
 mutate_grid(package,lambda d:row(d,'P1-PLAN-17')['cells'][2].update(text='B',state='visible_text',transcript_end_byte=row(d,'P1-PLAN-17')['cells'][2]['transcript_start_byte']+1))
 with pytest.raises(ValueError):validate(package)

@pytest.mark.parametrize('name', ['source/original.pdf','images/page-2.png','native/page-0002.txt','VISUAL_TRANSCRIPTION.json'])
def test_input_corruption_rejected(package,name):
 p=package/name;p.write_bytes(p.read_bytes()+b'changed');repin(package)
 with pytest.raises((ValueError,RuntimeError)):validate(package)

def test_extra_file_refused(package):
 (package/'unexpected.txt').write_text('extra')
 with pytest.raises(ValueError,match='Closed inventory'):validate(package)

def test_symlink_source_refused(package,tmp_path):
 p=package/'source/original.pdf';real=tmp_path/'original.pdf';p.rename(real);p.symlink_to(real)
 with pytest.raises(ValueError,match='Nonordinary'):validate(package)

def test_path_escape_refused(package):
 with pytest.raises(ValueError,match='Path escape'):body(package,Asset(path='../outside',sha256='0'*64,size_bytes=0))

def test_missing_ocr_page_refused(package):
 (package/'ocr/retry-authorized/page-0003.stdout').unlink();repin(package)
 with pytest.raises((ValueError,FileNotFoundError)):validate(package)

def test_ocr_before_visual_freeze_refused(package):
 p=package/'OCR_COMPARISON_RECEIPT.json';d=load(p);d['events'][0]['started_at']='2026-09-12T22:00:00Z';save(p,d);repin(package)
 with pytest.raises(ValueError,match='OCR must follow'):validate(package)

def test_ocr_row_assignment_rebinding_cannot_rewrite_text(package):
 p=package/'OCR_CELL_COMPARISON.json';d=load(p);d['cells'][0]['ocr_text']='new unsupported text';save(p,d);repin(package)
 with pytest.raises(ValueError,match='OCR cell/visual'):validate(package)

def test_custody_is_not_relabelled_download(package):
 p=package/'custody/intake-RECEIPT.json';d=load(p);d['intent']['records'][0]['acquisition_method']='official_download';save(p,d);repin(package)
 with pytest.raises(ValueError,match='Intake/custody'):validate(package)

@pytest.mark.parametrize('key,value',[('fully_legible_complete_extraction',True),('currentness','verified'),('answer_safe',True),('verified_effective_date','2026-05-01')])
def test_source_status_not_promoted(package,key,value):
 p=package/'SOURCE_QA.json';d=load(p);d[key]=value;save(p,d);repin(package)
 with pytest.raises(ValueError):validate(package)
