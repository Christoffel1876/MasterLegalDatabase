"""Install a captured-buffer source lookup only after exact independent review."""
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
import json
import os

from pydantic import BaseModel, ConfigDict
from install_reviewed_watch_batches import BASE, ROOT, HANDOFF, Ref, closed, identity, new_file, read

OUT = ROOT / 'research/local_review/douglas-pueblo-lookup-install-2026-09-13'
PIN = 'e7a292b0774d2c53585836267d97f36854c183f67c3cadd2fdc8bef6a35ebb18'
REVIEW_PIN = '2158d1be785cc3ba5f1ebdb6fa85202510b296be42193380f7626250e64306ae'


class Receipt(BaseModel):
    """Actual installation identities and explicit scope of this additive adapter."""
    model_config = ConfigDict(extra='forbid')
    status: Literal['installed_reviewed_captured_buffer_lookup']
    finished_at: datetime
    proposal_manifest_sha256: str
    independent_review_manifest_sha256: str
    installed_files: list[Ref]
    archived_preimages: list[Ref]
    preserved_files: list[Ref]
    source_ids_added: list[str]
    public_requests: Literal[0] = 0
    source_bytes_changed: Literal[0] = 0
    legal_currentness: Literal['not_verified'] = 'not_verified'
    old_seven_adapter_concurrency_audit: Literal['separate_pending_work']
    full_suite: Literal['pending_after_installation']


def main() -> None:
    """Snapshot old script/docs, then write exact reviewed buffers atomically."""
    if OUT.exists():
        raise ValueError('Installation already has a receipt directory')
    _, review = closed(HANDOFF / 'douglas-pueblo-lookups-revision-independent-review', REVIEW_PIN)
    proposal = {key[len('received/'):]: raw for key, raw in review.items()
                if key.startswith('received/')}
    manifest = proposal['FINAL_MANIFEST.json']
    if identity('manifest', manifest).sha256 != PIN:
        raise ValueError('Independently received proposal pin differs')
    names = {item['path'] for item in json.loads(manifest)['files']}
    if set(proposal) != names | {'FINAL_MANIFEST.json', 'FINAL_MANIFEST.schema.json'}:
        raise ValueError('Proposal closure differs from its declared schema convention')
    original = HANDOFF / 'douglas-pueblo-lookups-revision-1'
    actual = {p.relative_to(original).as_posix() for p in original.rglob('*') if p.is_file()}
    if actual != set(proposal):
        raise ValueError('Current proposal closure differs')
    for relative, raw in proposal.items():
        if read(original / relative) != raw:
            raise ValueError('Current proposal differs from independent reviewed capture')
    mapping = {
        'proposed/research_source_lookup.py': 'scripts/research_source_lookup.py',
        'proposed/RESEARCH_SOURCE_LOOKUP.md': 'docs/RESEARCH_SOURCE_LOOKUP.md',
        'proposed/test_douglas_pueblo_native_lookup.py': 'tests/test_douglas_pueblo_native_lookup.py',
    }
    for name in proposal:
        if name.startswith('fixtures/seven-native-sources/'):
            mapping[name] = 'tests/fixtures/douglas_pueblo_native_lookup/' + name[len('fixtures/'):]
    if len(mapping) != 17:
        raise ValueError('Unexpected installation set')
    before = {}
    for source, target in mapping.items():
        path = ROOT / target
        if source in {'proposed/research_source_lookup.py', 'proposed/RESEARCH_SOURCE_LOOKUP.md'}:
            raw = read(path)
            if raw != proposal['preimages/' + path.name]:
                raise ValueError('Installation preimage differs')
            before[target] = raw
        elif path.exists():
            raise ValueError('New destination already exists')
    frozen = {'prepared/' + k: v for k, v in proposal.items()}
    frozen.update({'independent-review/' + k: v for k, v in review.items()})
    frozen[Path(__file__).name] = read(Path(__file__))
    frozen['install_reviewed_watch_batches.py'] = read(
        BASE / 'handoffs/run-2026-09-12/install_reviewed_watch_batches.py')
    for name, raw in frozen.items():
        new_file(OUT / name, raw)
    for name, raw in before.items():
        new_file(OUT / '_SNAPSHOTS/before-install' / name, raw)
    for source, target in mapping.items():
        path, raw = ROOT / target, proposal[source]
        if target in before:
            if read(path) != before[target]:
                raise ValueError('Preimage changed during installation')
            temp = path.with_name(path.name + '.dp-install.tmp')
            with temp.open('xb') as handle:
                handle.write(raw)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp, path)
        else:
            new_file(path, raw)
        if read(path) != raw:
            raise ValueError('Installed bytes differ')
    receipt = Receipt(
        status='installed_reviewed_captured_buffer_lookup',
        finished_at=datetime.now(timezone.utc), proposal_manifest_sha256=PIN,
        independent_review_manifest_sha256=REVIEW_PIN,
        installed_files=[identity(target, proposal[source]) for source, target in mapping.items()],
        archived_preimages=[identity('_SNAPSHOTS/before-install/' + k, v)
                            for k, v in before.items()],
        preserved_files=[identity(k, v) for k, v in sorted(frozen.items())],
        source_ids_added=['douglas-ehs-fees-atlas-directed', 'pueblo-planning-fees-atlas-directed'],
        old_seven_adapter_concurrency_audit='separate_pending_work',
        full_suite='pending_after_installation',
    )
    new_file(OUT / 'RECEIPT.schema.json',
             (json.dumps(Receipt.model_json_schema(), indent=2) + '\n').encode())
    new_file(OUT / 'RECEIPT.json', (receipt.model_dump_json(indent=2) + '\n').encode())
    print(receipt.model_dump_json(include={'status', 'finished_at', 'source_ids_added'}))


if __name__ == '__main__':
    main()
