"""Read-only verification of a wording-only, closed metadata proposal."""
from __future__ import annotations
import hashlib
import json
import sys
from pathlib import Path
from typing import Literal
import jsonschema
from pydantic import BaseModel, ConfigDict
from prepare import HERE, Asset, Receipt, OLD, NEW, array_bytes

class Manifest(BaseModel):
    """Closed preparation file inventory."""
    model_config=ConfigDict(extra='forbid',strict=True)
    status:Literal['prepared_not_installed']
    files:list[Asset]


def verify()->None:
    """Verify exact custody, metadata-only diff and unchanged visual dataset."""
    manifest=Manifest.model_validate_json((HERE/'FINAL_MANIFEST.json').read_bytes())
    names={a.path for a in manifest.files}
    assert len(names)==len(manifest.files)
    actual={p.relative_to(HERE).as_posix() for p in HERE.rglob('*') if p.is_file()}
    assert actual==names|{'FINAL_MANIFEST.json'}
    for item in manifest.files:
        rel=Path(item.path)
        assert not rel.is_absolute() and '..' not in rel.parts
        path=HERE/rel
        assert not any(p.is_symlink() for p in [path,*path.parents])
        data=path.read_bytes()
        assert len(data)==item.size_bytes and hashlib.sha256(data).hexdigest()==item.sha256
    record=Receipt.model_validate_json((HERE/'CLARIFICATION.json').read_bytes())
    jsonschema.validate(json.loads(record.model_dump_json()),
                        json.loads((HERE/'CLARIFICATION.schema.json').read_bytes()))
    old=json.loads((HERE/'preimages/inventory.json').read_bytes())
    new=json.loads((HERE/'proposed/inventory.json').read_bytes())
    schema=json.loads((HERE/'proposed/inventory.schema.json').read_bytes())
    jsonschema.validate(new,schema)
    assert old['sources']==new['sources'] and len(new['sources'])==64
    assert old['prepared_at']==new['prepared_at']
    assert old['limitations'][0]==OLD and new['limitations'][0]==NEW
    assert old['limitations'][1:]==new['limitations'][1:]
    assert [k for k in old if old[k]!=new[k]]==['plan','limitations']
    for name,keys in [('inventory.json',['sources']),('join-plan.json',['authorities','reviews'])]:
        for key in keys:
            assert array_bytes((HERE/'preimages'/name).read_bytes(),key)==array_bytes((HERE/'proposed'/name).read_bytes(),key)
    old_sha=hashlib.sha256((HERE/'preimages/inventory.json').read_bytes()).hexdigest()
    new_sha=hashlib.sha256((HERE/'proposed/inventory.json').read_bytes()).hexdigest()
    before=(HERE/'preimages/geode-source-review-inventory.html').read_bytes()
    after=(HERE/'proposed/geode-source-review-inventory.html').read_bytes()
    assert before.replace(old_sha.encode(),new_sha.encode(),1)==after
    sys.stdout.write('PASS: closed metadata clarification; all64rows and joins exact; only limitation/plan identity/digest change.\n')

if __name__=='__main__':verify()
