"""Read-only streaming comparison against the exact locally tracked main commit."""
from datetime import datetime,timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from models import Comparison
ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[2]/'MasterLegalDatabase'
URLS=['https://planningdevelopment.elpasoco.com/','https://epc-assets.elpasoco.com/wp-content/uploads/sites/12/Misc/25-290.pdf']
PDF_SHA='754e98fb7908b66e54a192cefca9817f7bb4cf2a428cf7c469d59f7cfdcdf427'
def leaves(v):
    if isinstance(v,dict):
        for x in v.values():yield from leaves(x)
    elif isinstance(v,list):
        for x in v:yield from leaves(x)
    elif isinstance(v,str):yield v

def main():
    if (ROOT/'COMPARISON.json').exists():raise ValueError('Frozen comparison exists')
    commit=subprocess.check_output(['git','-C',str(REPO),'rev-parse','refs/heads/main'],text=True).strip()
    records=[]
    for path in ['_RAW_ARCHIVE/manual_intake/manual_source_intake_manifest.jsonl','_CONTROL_PLANE/LOCAL_DOWNLOAD_MANIFEST.jsonl']:
        oid=subprocess.check_output(['git','-C',str(REPO),'rev-parse',commit+':'+path],text=True).strip()
        proc=subprocess.Popen(['git','-C',str(REPO),'cat-file','blob',oid],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        h=sha256();size=count=valid=bad=0;matches=[];prefix=b''
        for line in proc.stdout:
            h.update(line);size+=len(line);count+=1
            if len(prefix)<200:prefix+=line[:200-len(prefix)]
            try:row=json.loads(line)
            except (ValueError,UnicodeError):bad+=1;continue
            valid+=1;found=sorted(set(leaves(row)) & set(URLS+[PDF_SHA]))
            if found:matches.append({'line_number':count,'matched_values':found,'row_sha256':sha256(line).hexdigest(),'raw_line':line.decode()})
        error=proc.stderr.read();code=proc.wait()
        if code:raise ValueError('Git blob read failed: '+error.decode(errors='replace'))
        records.append({'repository_path':path,'git_blob_oid':oid,'sha256':h.hexdigest(),
            'size_bytes':size,'line_count':count,'parsed_json_rows':valid,'parse_errors':bad,
            'is_lfs_pointer':prefix.startswith(b'version https://git-lfs.github.com/spec/v1'),
            'matches':matches})
    data={'recorded_at':datetime.now(timezone.utc).isoformat(),'repository_main_commit':commit,
          'urls':URLS,'acquired_pdf_sha256':PDF_SHA,'manifests':records,
          'limitations':['Only these two tracked main blobs were compared; working-tree changes and other archives are outside scope.',
            'Exact URL strings and exact acquired PDF SHA256 only. A URL match alone is not byte equality; a recorded digest match alone would not prove old bytes were retained.',
            'Zero matches establishes no match in these two captured tracked inputs, not that the source was never collected elsewhere.']}
    (ROOT/'COMPARISON.schema.json').write_text(json.dumps(Comparison.model_json_schema(),indent=2)+'\n')
    typed=Comparison.model_validate_json(json.dumps(data));(ROOT/'COMPARISON.json').write_text(typed.model_dump_json(indent=2)+'\n')
    sys.stdout.write(json.dumps({'commit':commit,'manifests':[{'path':r['repository_path'],'rows':r['parsed_json_rows'],'matches':len(r['matches'])} for r in records]},indent=2)+'\n')
if __name__=='__main__':main()
