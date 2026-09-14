"""Read-only portable verification of the completed Colorado Springs intake evidence."""
import hashlib
import json
from pathlib import Path

import jsonschema

BASE = Path(__file__).absolute().parent


def load(relative):
    return json.loads((BASE / relative).read_bytes())


def check(item, prefix=''):
    relative = Path(prefix) / item['path']
    assert not relative.is_absolute() and '..' not in relative.parts
    path = BASE / relative
    assert path.is_file() and not any(p.is_symlink() for p in (path, *path.parents))
    data = path.read_bytes()
    assert hashlib.sha256(data).hexdigest() == item['sha256']
    assert len(data) == item['size_bytes']
    return data


def main():
    inventory = load('INVENTORY.json')
    jsonschema.validate(inventory, load('INVENTORY.schema.json'))
    names = [item['path'] for item in inventory['files']]
    assert names == sorted(set(names))
    actual = set()
    for path in BASE.rglob('*'):
        assert not path.is_symlink() and (path.is_file() or path.is_dir())
        if path.is_file():
            actual.add(path.relative_to(BASE).as_posix())
    assert actual == set(names) | {'INVENTORY.json', 'INVENTORY.schema.json'}
    for item in inventory['files']:
        check(item)
    acceptance = load('ACCEPTANCE.json')
    jsonschema.validate(acceptance, load('ACCEPTANCE.schema.json'))
    receipt = json.loads(check(acceptance['receipt']))
    intent_raw = check(acceptance['intent'])
    intent = json.loads(intent_raw)
    jsonschema.validate(receipt, load('prepared-transaction/RECEIPT.schema.json'))
    jsonschema.validate(intent, load('prepared-transaction/INTENT.schema.json'))
    assert hashlib.sha256(intent_raw).hexdigest() == receipt['intent_sha256']
    assert receipt['intent'] == intent
    assert receipt['actual_repository_received_at'] == acceptance['actual_repository_received_at']
    assert receipt['raw_before'] == 59 and receipt['raw_after'] == 61
    assert receipt['ledger_before'] == 60 and receipt['ledger_after'] == 62
    suffix = check(intent['suffix'], 'prepared-transaction/execution')
    assert len(suffix.splitlines()) == 2
    assert [json.loads(line) for line in suffix.splitlines()] == intent['records']
    for item, record in zip(receipt['originals'], intent['records'], strict=True):
        check(item, 'completed-canonical')
        assert item['path'] == record['archive_path'] and item['sha256'] == record['sha256']
        assert record['received_at'] == receipt['actual_repository_received_at']
        assert record['layer_id'] == '10_Municipal_Authorities'
    for change in intent['changes']:
        before = check(change['snapshot'], 'completed-canonical')
        assert hashlib.sha256(before).hexdigest() == change['before']['sha256']
        after = check(change['after'], 'completed-canonical')
        if change['path'].endswith('.jsonl'):
            assert after == before + suffix
    report = load('completed-canonical/_CONTROL_PLANE/MANUAL_SOURCE_INTAKE_REPORT.json')
    assert report['archive_verification']['manifest_records'] == 61
    assert report['archive_verification']['missing_ledger_only_intake_ids'] == acceptance['missing_historical_intake_ids']
    assert len(acceptance['missing_historical_intake_ids']) == 1
    assert acceptance['answer_safe'] is False and acceptance['legal_currentness'] == 'not_verified'
    print(json.dumps({'status': 'verified_completed_custody', 'payloads': len(names),
                      'raw_records': 61, 'ledger_records': 62,
                      'legal_currentness': 'not_verified'}))


if __name__ == '__main__':
    main()
