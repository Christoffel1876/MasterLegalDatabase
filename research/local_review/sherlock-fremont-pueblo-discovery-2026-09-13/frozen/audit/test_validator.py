"""Three temporary negative checks; never fetch sources or modify the frozen evidence."""
from pathlib import Path
import hashlib
import json
import shutil
import tempfile
import sys

sys.dont_write_bytecode = True
from validate_audit import validate


def reseal(root):
    manifest = json.loads((root / 'FINAL_MANIFEST.json').read_bytes())
    for item in manifest['files']:
        data = (root / item['path']).read_bytes()
        item.update(sha256=hashlib.sha256(data).hexdigest(), size_bytes=len(data))
    data = (json.dumps(manifest, indent=2) + '\n').encode()
    (root / 'FINAL_MANIFEST.json').write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def run(root):
    original = hashlib.sha256((root / 'FINAL_MANIFEST.json').read_bytes()).hexdigest()
    results = []
    for case in ['modified_original', 'extra_member', 'forged_proposal_anchor']:
        with tempfile.TemporaryDirectory(prefix='sh-ext-audit-', dir='/private/tmp') as directory:
            fixture = Path(directory) / 'packet'
            shutil.copytree(root, fixture)
            digest = original
            if case == 'modified_original':
                p = fixture / 'received/raw/SHEXT001-A001.pdf'
                p.write_bytes(p.read_bytes() + b'altered')
            elif case == 'extra_member':
                (fixture / 'unlisted.txt').write_text('fixture')
            else:
                p = fixture / 'DIRECTED_PROPOSAL.json'
                data = json.loads(p.read_bytes())
                data['targets'][0]['exact_href'] = 'https://www.pueblocounty.gov/invented.pdf'
                data['targets'][0]['url'] = data['targets'][0]['exact_href']
                p.write_text(json.dumps(data, indent=2) + '\n')
                digest = reseal(fixture)
            try:
                validate(fixture, digest)
            except ValueError as error:
                results.append({'case': case, 'status': 'PASS', 'rejection': str(error)})
            else:
                raise AssertionError('mutation accepted: ' + case)
    return results


if __name__ == '__main__':
    sys.stdout.write(json.dumps(run(Path(__file__).parent), indent=2) + '\n')
