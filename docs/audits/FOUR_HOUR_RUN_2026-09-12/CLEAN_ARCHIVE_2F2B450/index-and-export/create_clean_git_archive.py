"""Export an exact local commit and verify every stored blob without network or smudging."""
from __future__ import annotations
import argparse,hashlib,json,subprocess,tarfile
from pathlib import Path,PurePosixPath
from datetime import datetime,timezone
from pydantic import BaseModel,ConfigDict,Field
class Receipt(BaseModel):
 model_config=ConfigDict(extra='forbid',strict=True)
 status:str
 started_at:str
 finished_at:str
 commit:str
 archive_root:str
 stored_blob_algorithm:str
 verified_files:int
 total_bytes:int
 tree_listing_sha256:str
 network_requests:int=0
 lfs_smudge_performed:bool=False
 legal_currentness:str='not_verified'
def main()->None:
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--repo',type=Path,required=True)
 parser.add_argument('--commit',required=True)
 parser.add_argument('--destination',type=Path,required=True)
 parser.add_argument('--receipt-directory',type=Path,required=True)
 a=parser.parse_args();start=datetime.now(timezone.utc).isoformat()
 head=subprocess.check_output(['git','rev-parse',a.commit+'^{commit}'],cwd=a.repo).decode().strip()
 assert head==a.commit
 algo=subprocess.check_output(['git','rev-parse','--show-object-format'],cwd=a.repo).decode().strip()
 assert algo in ['sha1','sha256']
 tree=subprocess.check_output(['git','ls-tree','-rz',head],cwd=a.repo)
 entries={}
 for raw in tree.split(b'\0'):
  if not raw:continue
  info,name=raw.split(b'\t',1);mode,kind,oid=info.decode().split()
  assert kind=='blob' and mode in ['100644','100755'],'Symlink/submodule needs separate review'
  rel=PurePosixPath(name.decode());assert not rel.is_absolute() and '..' not in rel.parts
  entries[rel.as_posix()]=oid
 assert not a.destination.exists()
 a.destination.mkdir(parents=True)
 process=subprocess.Popen(['git','archive','--format=tar',head],cwd=a.repo,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 seen=set();total=0
 with tarfile.open(fileobj=process.stdout,mode='r|') as stream:
  for member in stream:
   rel=PurePosixPath(member.name)
   assert not rel.is_absolute() and '..' not in rel.parts
   target=a.destination.joinpath(*rel.parts)
   if member.isdir():target.mkdir(parents=True,exist_ok=True);continue
   assert member.isfile() and member.name in entries and member.name not in seen
   target.parent.mkdir(parents=True,exist_ok=True)
   hasher=hashlib.new(algo);hasher.update(f'blob {member.size}\0'.encode())
   size=0
   with stream.extractfile(member) as source,target.open('xb') as output:
    while chunk:=source.read(1024*1024):
     output.write(chunk);hasher.update(chunk);size+=len(chunk)
   assert size==member.size and hasher.hexdigest()==entries[member.name],member.name
   target.chmod(member.mode & 0o777)
   seen.add(member.name);total+=size
 error=process.stderr.read();assert process.wait()==0,error.decode()
 assert seen==set(entries)
 assert {p.relative_to(a.destination).as_posix() for p in a.destination.rglob('*') if p.is_file()}==seen
 record=Receipt(status='passed_exact_committed_blob_export',started_at=start,finished_at=datetime.now(timezone.utc).isoformat(),commit=head,archive_root=str(a.destination),stored_blob_algorithm=algo,verified_files=len(seen),total_bytes=total,tree_listing_sha256=hashlib.sha256(tree).hexdigest())
 a.receipt_directory.mkdir(parents=True,exist_ok=True)
 for name,value in [('ARCHIVE_RECEIPT.schema.json',Receipt.model_json_schema()),('ARCHIVE_RECEIPT.json',record.model_dump())]:
  path=a.receipt_directory/name;assert not path.exists();path.write_text(json.dumps(value,indent=2)+'\n')
 print(record.model_dump_json())
if __name__=='__main__':main()
