"""Read-only verification of staged joins and a closed, typed preservation inventory."""
from __future__ import annotations
import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Literal
import jsonschema
from pydantic import BaseModel, ConfigDict, Field
from prepare import HERE, ROOT, PROPOSED, BASELINE, ACCEPTANCES, load_proposed

class FileIdentity(BaseModel):
    """Exact package or repository identity."""
    model_config = ConfigDict(extra='forbid', strict=True)
    path: str
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    size_bytes: int = Field(ge=0)

class Manifest(BaseModel):
    """Closed preparation payload inventory; never an installation instruction."""
    model_config = ConfigDict(extra='forbid', strict=True)
    schema_version: Literal['final-three-inventory-preparation-1']
    status: Literal['prepared_not_installed']
    created_at: str
    files: list[FileIdentity]
    repository_inputs: list[FileIdentity]
    source_count: Literal[64]
    mapped_count: Literal[27]
    unmapped_count: Literal[37]
    changed_existing_review_ids: list[str]
    new_source_id: Literal['pueblo-county-planning-fees-sh-ext-002']
    original_metadata_unchanged_except_two_reviews: Literal[True]
    prior_authority_joins_unchanged: Literal[63]
    prior_review_joins_unchanged: Literal[24]
    legal_currentness: Literal['not_verified']
    answer_safe: Literal[False]
    limitations: list[str]


def ordinary(root: Path, relative: str) -> Path:
    """Reject traversal, symlinks and non-file evidence."""
    rel=Path(relative)
    if rel.is_absolute() or '..' in rel.parts:
        raise ValueError('unsafe path')
    result=root/rel
    for component in [result,*result.parents]:
        if component.is_symlink():
            raise ValueError('symlink evidence')
        if component==root:
            break
    if not result.is_file():
        raise ValueError('missing ordinary evidence: '+relative)
    return result


def check_file(root: Path, item: FileIdentity) -> None:
    """Stream an exact digest; no source interpretation or source extraction."""
    path=ordinary(root,item.path)
    digest=hashlib.sha256()
    size=0
    with path.open('rb') as handle:
        for chunk in iter(lambda:handle.read(1024*1024),b''):
            digest.update(chunk)
            size+=len(chunk)
    if digest.hexdigest()!=item.sha256 or size!=item.size_bytes:
        raise ValueError('hash/size mismatch: '+item.path)


def verify(repository: bool = False) -> None:
    """Verify immutable package and optionally replay its exact read-only repository joins."""
    manifest=Manifest.model_validate_json((HERE/'FINAL_MANIFEST.json').read_bytes())
    schema=json.loads((HERE/'FINAL_MANIFEST.schema.json').read_bytes())
    jsonschema.validate(json.loads(manifest.model_dump_json()),schema)
    expected={item.path for item in manifest.files}
    if len(expected)!=len(manifest.files):
        raise ValueError('duplicate payload')
    actual={p.relative_to(HERE).as_posix() for p in HERE.rglob('*') if p.is_file()}
    if actual != expected|{'FINAL_MANIFEST.json'}:
        raise ValueError('unlisted or absent package payload')
    for item in manifest.files:
        check_file(HERE,item)
    if repository:
        for item in manifest.repository_inputs:
            check_file(ROOT,item)
        for relative,expected_sha in ACCEPTANCES.items():
            data=ordinary(ROOT,relative).read_bytes()
            if hashlib.sha256(data).hexdigest()!=expected_sha:
                raise ValueError('acceptance mismatch')
        module=load_proposed()
        result=module.build_inventory(ROOT)
        module.check_inventory(ROOT,result)
        old=module.Inventory.model_validate_json((BASELINE/'inventory.json').read_bytes())
        for a,b in zip(result.sources[:63],old.sources,strict=True):
            if a.record_id in manifest.changed_existing_review_ids:
                a=a.model_copy(update={'reviews':None,'review_status':'metadata_only_review_unknown'})
            if a!=b:
                raise ValueError('previous metadata changed: '+a.record_id)
    sys.stdout.write('PASS: closed typed preparation; '+
        ('repository pins and deterministic 64/27/37 join replay' if repository else
         'repository evidence not re-opened')+'; no maintained writes.\n')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository',action='store_true')
    verify(parser.parse_args().repository)
