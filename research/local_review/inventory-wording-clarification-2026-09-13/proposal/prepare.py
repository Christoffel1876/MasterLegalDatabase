"""Prepare one count-neutral limitation and only the corresponding visualization digest."""
from __future__ import annotations
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]/'MasterLegalDatabase'
PACKAGE=Path('research/local_review/manual-source-review-inventory-2026-09-11')
VISUAL=Path('/Users/mcoors/.codex/visualizations/2026/09/09/01a08848-5f8e-7c51-9b66-fd82eff860fe/geode-source-review-inventory.html')
BEFORE=HERE/'preimages'
PROPOSED=HERE/'proposed'
OLD='All 61 rows are exact manual-source custody identities, not a percentage of geographic, documentary or legal coverage. The legacy local coverage ledger is pinned and unchanged.'
NEW='Every row is an exact manual-source custody identity, not a percentage of geographic, documentary or legal coverage. The legacy local coverage ledger is pinned and unchanged.'

class Asset(BaseModel):
    """Exact ordinary-file bytes."""
    model_config=ConfigDict(extra='forbid',strict=True)
    path:str
    sha256:str=Field(pattern=r'^[a-f0-9]{64}$')
    size_bytes:int=Field(ge=0)

class Receipt(BaseModel):
    """Metadata-only clarification with explicit equivalence scope."""
    model_config=ConfigDict(extra='forbid',strict=True)
    status:Literal['prepared_not_installed']
    prepared_at:str
    historical_inventory_prepared_at:str
    old_limitation:str
    new_limitation:str
    sources:Literal[64]
    mapped:Literal[27]
    unmapped:Literal[37]
    authorities:Literal[12]
    all_source_rows_typed_equal:Literal[True]
    all_source_rows_serialized_array_equal:Literal[True]
    all_authority_and_review_joins_equal:Literal[True]
    inventory_changed_fields:list[str]
    schema_unchanged:Literal[True]
    visual_only_digest_attribute_changed:Literal[True]
    visual_all_ids_authorities_review_kinds_equal:Literal[True]
    inputs:list[Asset]
    outputs:list[Asset]
    limitations:list[str]


def exact(path:Path, label:str)->Asset:
    """Capture a non-symlink file digest."""
    if path.is_symlink() or not path.is_file():raise ValueError(str(path))
    data=path.read_bytes()
    return Asset(path=label,sha256=hashlib.sha256(data).hexdigest(),size_bytes=len(data))


def write_new(path:Path,data:bytes)->None:
    """Write only new task files atomically."""
    if path.exists():raise ValueError('Refuse overwrite: '+str(path))
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_name(path.name+'.tmp')
    temporary.write_bytes(data)
    temporary.replace(path)


def array_bytes(data:bytes,key:str)->bytes:
    """Extract the exact serialized JSON array without reformatting."""
    text=data.decode()
    start=text.index('"'+key+'":')+len(key)+3
    while text[start].isspace():start+=1
    value,end=json.JSONDecoder().raw_decode(text[start:])
    if not isinstance(value,list):raise ValueError('not an array')
    return text[start:start+end].encode()


def prepare()->None:
    """Use unchanged maintained rendering while redirecting only staged plan reads."""
    sys.path.insert(0,str(ROOT))
    from geode.pipeline import manual_review_inventory as module
    rels=[PACKAGE/n for n in ['join-plan.json','inventory.json','inventory.schema.json','README.md']]
    rels += [Path('geode/pipeline/manual_review_inventory.py'),
             Path('tests/test_manual_review_inventory.py')]
    inputs=[]
    for rel in rels:
        path=ROOT/rel
        inputs.append(exact(path,rel.as_posix()))
        write_new(BEFORE/rel.name,path.read_bytes())
    inputs.append(exact(VISUAL,str(VISUAL)))
    write_new(BEFORE/VISUAL.name,VISUAL.read_bytes())
    assert exact(ROOT/rels[-2],'').sha256=='47cf0fec86218b6909825196e055fbb8b8c5d4777df3e6f6f1b31b46f5a22c88'
    old_plan=module.JoinPlan.model_validate_json((BEFORE/'join-plan.json').read_bytes())
    old_inv=module.Inventory.model_validate_json((BEFORE/'inventory.json').read_bytes())
    assert old_plan.limitations[0]==old_inv.limitations[0]==OLD
    assert len(old_inv.sources)==64 and (old_inv.rows_with_review,old_inv.rows_without_review)==(27,37)
    new_plan=old_plan.model_copy(deep=True)
    new_plan.limitations[0]=NEW
    module.JoinPlan.model_validate_json(new_plan.model_dump_json())
    write_new(PROPOSED/'join-plan.json',(new_plan.model_dump_json(indent=2)+'\n').encode())
    old_safe=module.safe_path
    def staged(root:Path,relative:str)->Path:
        if root==ROOT and relative in {(PACKAGE/n).as_posix() for n in
            ['join-plan.json','inventory.json','inventory.schema.json','README.md']}:
            return old_safe(PROPOSED,Path(relative).name)
        return old_safe(root,relative)
    module.safe_path=staged
    try:
        new_inv=module.build_inventory(ROOT)
        for name,text in module._render_outputs(new_inv).items():
            write_new(PROPOSED/name,text.encode())
        module.check_inventory(ROOT,new_inv)
    finally:
        module.safe_path=old_safe
    assert new_inv.sources==old_inv.sources
    assert new_plan.authorities==old_plan.authorities and new_plan.reviews==old_plan.reviews
    assert new_plan.prepared_at==old_plan.prepared_at==new_inv.prepared_at==old_inv.prepared_at
    assert array_bytes((BEFORE/'inventory.json').read_bytes(),'sources')==array_bytes((PROPOSED/'inventory.json').read_bytes(),'sources')
    for key in ['authorities','reviews']:
        assert array_bytes((BEFORE/'join-plan.json').read_bytes(),key)==array_bytes((PROPOSED/'join-plan.json').read_bytes(),key)
    a,b=old_inv.model_dump(mode='json'),new_inv.model_dump(mode='json')
    changed=[key for key in a if a[key]!=b[key]]
    assert changed==['plan','limitations']
    assert (PROPOSED/'inventory.schema.json').read_bytes()==(BEFORE/'inventory.schema.json').read_bytes()
    assert (PROPOSED/'README.md').read_text()==(BEFORE/'README.md').read_text().replace(OLD,NEW,1)
    old_sha=hashlib.sha256((BEFORE/'inventory.json').read_bytes()).hexdigest()
    new_sha=hashlib.sha256((PROPOSED/'inventory.json').read_bytes()).hexdigest()
    old_fragment=(BEFORE/VISUAL.name).read_bytes()
    needle=('data-inventory-sha256="'+old_sha+'"').encode()
    replacement=('data-inventory-sha256="'+new_sha+'"').encode()
    assert old_fragment.count(needle)==1
    new_fragment=old_fragment.replace(needle,replacement,1)
    write_new(PROPOSED/VISUAL.name,new_fragment)
    assert new_fragment.replace(replacement,needle,1)==old_fragment
    rows=json.loads(re.search(r'<script type="application/json" id="inv-source-data">(.*?)</script>',new_fragment.decode(),re.S).group(1))
    assert len(rows)==64 and len({r['id'] for r in rows})==64
    assert len({r['a'] for r in rows})==12
    assert [r['id'] for r in rows]==[r.record_id for r in new_inv.sources]
    for visual,source in zip(rows,new_inv.sources,strict=True):
        assert visual['a']==source.authority_id
        assert visual['kind']==(source.reviews[0].review_kind if source.reviews else None)
    assert sum(r['kind'] is not None for r in rows)==27
    for item in inputs:
        path=Path(item.path) if Path(item.path).is_absolute() else ROOT/item.path
        assert exact(path,item.path)==item
    outputs=[exact(p,p.relative_to(HERE).as_posix()) for p in sorted(PROPOSED.iterdir())]
    record=Receipt(status='prepared_not_installed',
        prepared_at=datetime.now(timezone.utc).isoformat().replace('+00:00','Z'),
        historical_inventory_prepared_at=old_inv.prepared_at.isoformat(),
        old_limitation=OLD,new_limitation=NEW,sources=64,mapped=27,unmapped=37,authorities=12,
        all_source_rows_typed_equal=True,all_source_rows_serialized_array_equal=True,
        all_authority_and_review_joins_equal=True,inventory_changed_fields=changed,
        schema_unchanged=True,visual_only_digest_attribute_changed=True,
        visual_all_ids_authorities_review_kinds_equal=True,inputs=inputs,outputs=outputs,
        limitations=['No maintained writes or code/test changes. Install only after root finishes its running suite.',
                     'Same historical prepared_at; this receipt separately records clarification preparation.',
                     'No UI rerender claimed: only nonvisual digest attribute changed. Prior four-viewport UI QA remains historical evidence.',
                     'No source review repeated and no legal-currentness promotion.'])
    write_new(HERE/'CLARIFICATION.json',(record.model_dump_json(indent=2)+'\n').encode())
    write_new(HERE/'CLARIFICATION.schema.json',(json.dumps(Receipt.model_json_schema(),indent=2)+'\n').encode())
    sys.stdout.write('PASS: deterministic clarification; all64source rows/joins unchanged; visual digest-only update.\n')

if __name__=='__main__':prepare()
