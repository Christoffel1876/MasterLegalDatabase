from pathlib import Path
from datetime import datetime,timezone
import ast,hashlib,importlib.util,json,shutil,subprocess,sys,tempfile
p=Path('/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-13/popper-manual-watch-ci-public-audit')
s=p.parent/'ptolemy-manual-watch-ci-publishable-revision/proposed';d=p/'final'
expected={'scripts/manual_source_watch_ci.py':'09fc26756c7432af64c65b48ad8b08080c0cf1d5353456b587062386c65135df','config/manual_source_watch_ci.json':'27cd597e811efad82c458928db3dfe7c6ce453c7c57a1b108191723a90d51cde','tests/test_manual_source_watch_ci.py':'c040a16b0a052c3d42179105ad4e566d71799b5c64c6072a919e77ee0fd7c516','docs/MANUAL_SOURCE_WATCH_CI.md':'bb9d6b19f0f9ca006f9c6c3e87eee2208d35119a8bf02aa74c2c521334ef41d1'}
for n,h in expected.items():assert hashlib.sha256((s/n).read_bytes()).hexdigest()==h,n
shutil.copytree(s,d)
base=p/'historical-audit/received-final';old=json.loads((base/'config/manual_source_watch_ci.json').read_bytes());new=json.loads((d/'config/manual_source_watch_ci.json').read_bytes())
old['immutable_inputs']=[a for a in old['immutable_inputs'] if a['path']!='geode/schemas/models 2.py'];assert old==new
class Normalize(ast.NodeTransformer):
 def visit_Assign(self,node):
  if any(isinstance(t,ast.Name) and t.id=='CONFIG_SHA' for t in node.targets):node.value=ast.Constant('PIN')
  return self.generic_visit(node)
def tree(path):return ast.dump(Normalize().visit(ast.parse(path.read_text())),include_attributes=False)
assert tree(base/'scripts/manual_source_watch_ci.py')==tree(d/'scripts/manual_source_watch_ci.py')
class Annotations(ast.NodeTransformer):
 def visit_FunctionDef(self,node):
  node.returns=None
  for a in node.args.posonlyargs+node.args.args+node.args.kwonlyargs:a.annotation=None
  if node.args.vararg:node.args.vararg.annotation=None
  if node.args.kwarg:node.args.kwarg.annotation=None
  return self.generic_visit(node)
 def visit_ImportFrom(self,node):
  if node.module=='typing':
   node.names=[n for n in node.names if n.name!='Any']
   if not node.names:return None
  return node
assert ast.dump(Annotations().visit(ast.parse((base/'tests/test_manual_source_watch_ci.py').read_text())),include_attributes=False)==ast.dump(Annotations().visit(ast.parse((d/'tests/test_manual_source_watch_ci.py').read_text())),include_attributes=False)
repo=Path('/Users/mcoors/Documents/Project Geode/MasterLegalDatabase');root=Path(tempfile.mkdtemp(prefix='popper-final87-',dir='/private/tmp'))/'repository';root.mkdir();tracking=[]
for a in new['immutable_inputs']:
 b=(repo/a['path']).read_bytes();assert len(b)==a['size_bytes'] and hashlib.sha256(b).hexdigest()==a['sha256']
 assert subprocess.run(['git','ls-files','--error-unmatch','--',a['path']],cwd=repo,capture_output=True).returncode==0,a['path']
 attr=subprocess.run(['git','check-attr','filter','--',a['path']],cwd=repo,capture_output=True,text=True).stdout.rsplit(':',1)[-1].strip();assert attr=='unspecified',(a['path'],attr)
 tracking.append({**a,'tracked':True,'lfs_filter':attr})
 dst=root/a['path'];dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(b)
assert len(tracking)==87 and not(root/'geode/schemas/models 2.py').exists()
raw=Path('_RAW_ARCHIVE/manual_intake/manual_source_intake_manifest.jsonl');dst=root/raw;dst.parent.mkdir(parents=True,exist_ok=True)
with (repo/raw).open('rb') as inp,dst.open('xb') as out:
 for line in inp:out.write(line)
for n in ['scripts/manual_source_watch_ci.py','config/manual_source_watch_ci.json']:
 dst=root/n;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes((d/n).read_bytes())
start=datetime.now(timezone.utc).isoformat()
r=subprocess.run([sys.executable,'-B',str(root/'scripts/manual_source_watch_ci.py'),'--root',str(root),'--run-name','public-audit-readiness'],cwd='/private/tmp',capture_output=True,timeout=300)
print('actual87',r.returncode,start,datetime.now(timezone.utc).isoformat(),root)
print(r.stderr.decode()[-1000:]);assert r.returncode==0
summary=json.loads(r.stdout);assert summary['status']=='ready' and not summary['execution_requested']
assert not(root/'geode/schemas/models 2.py').exists()
assert not(root/'.geode_runtime/manual_source_watch').exists() and not(root/'.geode_runtime/manual_source_watch_batches').exists()
for a in new['immutable_inputs']:assert hashlib.sha256((root/a['path']).read_bytes()).hexdigest()==a['sha256']
checks=p/'checks';checks.mkdir(exist_ok=True);(checks/'readiness.stdout').write_bytes(r.stdout);(checks/'readiness.stderr').write_bytes(r.stderr)
shutil.copytree(root/'.geode_runtime/manual_source_watch_ci/public-audit-readiness',p/'actual-readiness')
sys.path.insert(0,str(p));from models import PinCheck
for row in tracking:PinCheck.model_validate(row)
# Typed records are retained as JSONL with one independently validated pin per line.
with (p/'TRACKED_PINS.jsonl').open('x',encoding='utf-8') as handle:
 for row in tracking:handle.write(PinCheck.model_validate(row).model_dump_json()+'\n')
print('87tracked/nonLFS; source/caps unchanged; runner AST differs only CONFIG_SHA; tests AST annotation-only; no excluded input present')
