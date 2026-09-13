"""Preserve the currently installed inventory before preparing its last bounded extension."""
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import jsonschema
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

ROOT=Path('/Users/mcoors/Documents/Project Geode/MasterLegalDatabase')
BASE=ROOT.parent/'handoffs/run-2026-09-13/plato-inventory-70-35-integration'
PREFIX='research/local_review/manual-source-review-inventory-2026-09-11/'

class Item(BaseModel):
    """Exact before-copy identity tied to the maintained predecessor path."""
    model_config=ConfigDict(strict=True,extra='forbid')
    repository_path:str
    preserved_path:str
    sha256:str=Field(pattern=r'^[0-9a-f]{64}$')
    size_bytes:int=Field(ge=0)

class Receipt(BaseModel):
    """Preimage capture only; the new fee source review remains pending."""
    model_config=ConfigDict(strict=True,extra='forbid')
    captured_at:AwareDatetime
    status:Literal['preimages_preserved_final_fee_review_pending']
    inventory_sources:Literal[69]
    inventory_reviewed:Literal[33]
    inventory_unmapped:Literal[36]
    current_raw_manifest_records:Literal[70]
    inventory_expected_transient_staleness:Literal[True]
    production_writes:Literal[0]
    files:list[Item]

assert not BASE.exists()
(BASE/'preimages').mkdir(parents=True)
(BASE/'proposed').mkdir()
names=[PREFIX+n for n in ['join-plan.json','join-plan.schema.json','inventory.json',
                         'inventory.schema.json','README.md']]
names+=['geode/pipeline/manual_review_inventory.py','tests/test_manual_review_inventory.py']
files=[]
for name in names:
    p=ROOT/name;raw=p.read_bytes();dest=BASE/'preimages'/p.name
    with dest.open('xb') as h:h.write(raw)
    files.append(Item(repository_path=name,preserved_path='preimages/'+p.name,
                      sha256=hashlib.sha256(raw).hexdigest(),size_bytes=len(raw)))
inventory=json.loads((BASE/'preimages/inventory.json').read_bytes())
assert (len(inventory['sources']),inventory['rows_with_review'],inventory['rows_without_review'])==(69,33,36)
receipt=Receipt(captured_at=datetime.now(timezone.utc),
    status='preimages_preserved_final_fee_review_pending',inventory_sources=69,
    inventory_reviewed=33,inventory_unmapped=36,current_raw_manifest_records=70,
    inventory_expected_transient_staleness=True,production_writes=0,files=files)
data=receipt.model_dump_json(indent=2)+'\n';schema=Receipt.model_json_schema()
jsonschema.validate(json.loads(data),schema)
(BASE/'PREIMAGE_RECEIPT.schema.json').write_text(json.dumps(schema,indent=2)+'\n')
(BASE/'PREIMAGE_RECEIPT.json').write_text(data)
shutil.copyfile(__file__,BASE/'capture_preimages.py')
for name in ['manual_review_inventory.py','test_manual_review_inventory.py']:
    shutil.copyfile(BASE/'preimages'/name,BASE/'proposed'/name)
print(BASE)
