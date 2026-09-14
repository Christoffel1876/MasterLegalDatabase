"""Install only the independently reviewed captured-buffer repair and exact fixtures."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import os
import sys

from pydantic import BaseModel, ConfigDict
from preserve_watch_test_repair import File, save

BASE = Path('/Users/mcoors/Documents/Project Geode')
ROOT = BASE / 'MasterLegalDatabase'
PROPOSAL = BASE / 'handoffs/run-2026-09-12/extended-run/native-lookup-captured-buffers'
DEST = ROOT / 'research/local_review/native-lookup-capture-install-2026-09-13'
PINS = {
    'scripts/research_source_lookup.py':
    '4b3f084eb9bf9a20f3e5c7b7c0c25a3b1bbbfe0de05caff9b626100808dbad6f',
    'docs/RESEARCH_SOURCE_LOOKUP.md':
    '1bd0e66df47c82a9e80f01241f40664ea4e754723e798476348fffec0fb9e55f',
    '_RAW_ARCHIVE/manual_intake/manual_source_intake_manifest.jsonl':
    '9fb073ac96e611311c1cdb633fde846aef9cbd6f64521a1ab59f96916af04c13',
    '_CONTROL_PLANE/MANUAL_SOURCE_INTAKE_LEDGER.jsonl':
    '1d930dd8dbf78130c70f89d56ca87c5c6675589be757ba84c02dc47451dbe3b8',
    'research/local_review/manual-source-review-inventory-2026-09-11/inventory.json':
    'd1930cfeb1ca385bd680a596d338602c0201167e326107107b7e2bcb60c9769c',
}


class Change(BaseModel):
    """One exact reviewed maintained file with an optional archived predecessor."""
    model_config = ConfigDict(extra='forbid')
    path: str
    before_sha256: str | None
    after_sha256: str
    size_bytes: int


class Receipt(BaseModel):
    """Installation is separate from the final full-suite execution."""
    model_config = ConfigDict(extra='forbid')
    installed_at: datetime
    status: str
    proposal_manifest_sha256: str
    review_manifest_sha256: str
    changes: list[Change]
    frozen_files: list[File]
    source_data_changed: bool = False
    full_suite_status: str = 'pending_separate_installed_run'


def digest(raw: bytes) -> str:
    """Hash the actual buffer that will be copied."""
    return hashlib.sha256(raw).hexdigest()


def capture(folder: Path, expected: str) -> dict[str, bytes]:
    """Capture a closed packet under its independently supplied final manifest hash."""
    manifest_name = 'FINAL_MANIFEST.json' if folder == PROPOSAL else 'MANIFEST.json'
    raw = (folder / manifest_name).read_bytes()
    if digest(raw) != expected:
        raise ValueError('Packet manifest identity differs')
    captured = {}
    for path in sorted(folder.rglob('*')):
        if path.is_symlink():
            raise ValueError('Symlinked packet')
        if path.is_file():
            captured[path.relative_to(folder).as_posix()] = path.read_bytes()
    return captured


def main() -> None:
    """Check every input before snapshots and atomic installation."""
    proposal_sha, review_name, review_sha = sys.argv[1:]
    review = Path(review_name).resolve()
    if not review.is_relative_to(BASE / 'handoffs/run-2026-09-12/extended-run'):
        raise ValueError('Unexpected independent review folder')
    if DEST.exists():
        raise ValueError('Installation receipt already exists')
    before = {name: (ROOT / name).read_bytes() for name in PINS}
    if any(digest(before[name]) != expected for name, expected in PINS.items()):
        raise ValueError('Installed preimage changed')
    proposal = capture(PROPOSAL, proposal_sha)
    reviewed = capture(review, review_sha)
    mapping = {
        'scripts/research_source_lookup.py': 'proposed/research_source_lookup.py',
        'docs/RESEARCH_SOURCE_LOOKUP.md': 'proposed/RESEARCH_SOURCE_LOOKUP.md',
        'tests/test_native_lookup_capture.py': 'proposed/test_native_lookup_capture.py',
    }
    for name in proposal:
        if name.startswith('fixtures/nine-native-sources/'):
            mapping['tests/fixtures/native_lookup_capture/' + name[len('fixtures/'):]] = name
    if len(mapping) != 21:
        raise ValueError('Expected three maintained files and eighteen fixtures')
    if digest(proposal[mapping['scripts/research_source_lookup.py']]) != (
            '1f4da2ec117996c21a2676bdd82226018ecf4ad0e583297c1f52ece43d1ffe55'):
        raise ValueError('Unreviewed implementation')
    if digest(proposal[mapping['tests/test_native_lookup_capture.py']]) != (
            '4c5fb91a23eca9bb0faa1d7c2f3f768058d6bd3cde5886b7a9250967d2c80399'):
        raise ValueError('Unexpected test implementation')
    changes = []
    for name, source in mapping.items():
        if name not in before and (ROOT / name).exists():
            raise ValueError('New file already exists: ' + name)
        changes.append(Change(path=name, before_sha256=digest(before[name])
                              if name in before else None,
                              after_sha256=digest(proposal[source]),
                              size_bytes=len(proposal[source])))
    frozen = {}
    for prefix, entries in [('proposal', proposal), ('independent-review', reviewed)]:
        frozen.update({prefix + '/' + name: raw for name, raw in entries.items()})
    receipt = Receipt(installed_at=datetime.now(timezone.utc),
                      status='installed_after_root_and_independent_review',
                      proposal_manifest_sha256=proposal_sha, review_manifest_sha256=review_sha,
                      changes=changes,
                      frozen_files=[File(path=name, sha256=digest(raw), size_bytes=len(raw))
                                    for name, raw in frozen.items()])
    for name, raw in frozen.items():
        save(DEST / name, raw)
    for name in mapping:
        if name in before:
            save(DEST / '_SNAPSHOTS' / name, before[name])
    for name, source in mapping.items():
        target, raw = ROOT / name, proposal[source]
        if name in before:
            if target.read_bytes() != before[name]:
                raise ValueError('Preimage changed immediately before installation')
            temp = target.with_name(target.name + '.capture-install.tmp')
            with temp.open('xb') as handle:
                handle.write(raw)
            os.replace(temp, target)
        else:
            save(target, raw)
    for name in PINS.keys() - mapping.keys():
        if (ROOT / name).read_bytes() != before[name]:
            raise ValueError('Source data changed during implementation installation')
    save(DEST / 'RECEIPT.schema.json',
         (json.dumps(Receipt.model_json_schema(), indent=2) + '\n').encode())
    save(DEST / 'RECEIPT.json', (receipt.model_dump_json(indent=2) + '\n').encode())
    for helper in [Path(__file__), Path(__file__).with_name('preserve_watch_test_repair.py')]:
        save(DEST / 'installation-tools' / helper.name, helper.read_bytes())
    print(json.dumps({'status': receipt.status, 'files_installed': len(changes),
                      'source_data_changed': False, 'installed_at': str(receipt.installed_at)}))


if __name__ == '__main__':
    main()
