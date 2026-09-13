"""Portable read-only verification, with no transaction or historical collector import."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys

import jsonschema
import pymupdf
from models import Asset, Manifest, Preparation, Validation

HERE = Path(__file__).absolute().parent
EXPECTED_PLAN = 'a8f768ff4c00bf55ba2db4712d67183f8c739e8e59777fa9bfed77f1bd12ef4b'
EXPECTED_RETRIEVAL = 'ecfdc65448dd2cc58d00eec7ec1ba3e9987457d5d9270d5e3362c165602ab8f3'


def ordinary(root: Path, name: str) -> Path:
    """Forbid linked, aliased, escaped or nonordinary evidence reads."""
    relative = Path(name)
    if (relative.is_absolute() or '..' in relative.parts or '\\' in name
            or relative.as_posix() != name):
        raise ValueError('unsafe reference')
    path = root / name
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('linked evidence')
    if not stat.S_ISREG(path.stat().st_mode):
        raise ValueError('not an ordinary evidence file')
    return path


def checked(root: Path, item: Asset) -> bytes:
    """Hash an exact buffer before decoding it."""
    raw = ordinary(root, item.path).read_bytes()
    if len(raw) != item.size_bytes or hashlib.sha256(raw).hexdigest() != item.sha256:
        raise ValueError('evidence pin differs: ' + item.path)
    return raw


def typed(root: Path, name: str, model: type):
    """Validate strict model/schema equality."""
    raw = ordinary(root, name + '.json').read_bytes()
    schema = json.loads(ordinary(root, name + '.schema.json').read_bytes())
    if schema != model.model_json_schema():
        raise ValueError('schema differs')
    jsonschema.validate(json.loads(raw), schema)
    return model.model_validate_json(raw), raw



def parse_historical_output(text: str) -> dict:
    """Accept only JSON plus the known PyMuPDF deprecated-import notice."""
    lines = text.splitlines()
    notice = (
        "warning: The `fitz` API is deprecated and will be removed in future. "
        "Use `import pymupdf` instead."
    )
    if not lines or len(lines) > 2 or (len(lines) == 2 and lines[0] != notice):
        raise ValueError("unexpected historical verifier output")
    value = json.loads(lines[-1])
    if not isinstance(value, dict):
        raise ValueError("historical verifier result is not an object")
    return value


def verify(root: Path = HERE) -> dict:
    """Check preparation and retained public custody only; never apply records."""
    manifest, _ = typed(root, 'FINAL_MANIFEST', Manifest)
    expected = {a.path for a in manifest.files} | {'FINAL_MANIFEST.json'}
    found, execution = set(), []
    for top, dirs, files in os.walk(root, followlinks=False):
        for name in dirs + files:
            if (Path(top) / name).is_symlink():
                raise ValueError('linked package member')
        for name in files:
            path = Path(top) / name
            if not stat.S_ISREG(path.stat().st_mode):
                raise ValueError('nonordinary package member')
            relative = path.relative_to(root).as_posix()
            if relative.startswith('execution/'):
                execution.append(relative)
            else:
                found.add(relative)
    if len(expected) != len(manifest.files) + 1 or found != expected:
        raise ValueError('closed preparation membership differs')
    for item in manifest.files:
        checked(root, item)
    plan, raw = typed(root, 'PREPARATION', Preparation)
    if hashlib.sha256(raw).hexdigest() != EXPECTED_PLAN:
        raise ValueError('preparation identity differs')
    if plan.retrieval_manifest.sha256 != EXPECTED_RETRIEVAL:
        raise ValueError('retrieval seal differs')
    buffers = {a.path: checked(root, a) for a in plan.custody_subset}
    prior = json.loads(buffers[plan.retrieval_manifest.path])
    pins = {a['path']: a for a in prior['files']}
    if len(pins) != len(prior['files']):
        raise ValueError('duplicate historical member')
    expected = {'inputs/retrieval/' + n for n in pins} | {
        'inputs/retrieval/FINAL_MANIFEST.json'}
    if set(buffers) != expected:
        raise ValueError('incomplete frozen public packet')
    for name, pin in pins.items():
        body = buffers['inputs/retrieval/' + name]
        if len(body) != pin['size_bytes'] or hashlib.sha256(body).hexdigest() != pin['sha256']:
            raise ValueError('retrieval member differs')
    historical = subprocess.run(
        [sys.executable, '-B', str(root / 'inputs/retrieval/verify_packet.py')],
        cwd=root, capture_output=True, text=True, check=True, timeout=30,
    )
    observed = parse_historical_output(historical.stdout)
    if observed['pdf_count'] != 1 or observed['structural_pdf_pages'] != 2:
        raise ValueError('retrieval body scope differs')
    pages = 0
    for index, (source, provenance) in enumerate(zip(plan.templates, plan.provenance)):
        body = checked(root, source.source)
        if body != buffers[provenance.response_body.path]:
            raise ValueError('incoming source copy differs from original HTTP response')
        result = json.loads(buffers[provenance.result.path])
        if (provenance.action_id != f'A{index + 1:03}'
                or source.official_source_url != result['final_url']
                or source.source.sha256 != result['body']['sha256']
                or provenance.http_completed_at.isoformat().replace('+00:00', 'Z')
                != result['completed_at']):
            raise ValueError('source/actual HTTP provenance join differs')
        with pymupdf.open(stream=body, filetype='pdf') as pdf:
            if (pdf.page_count != provenance.physical_pages or pdf.is_repaired
                    or pdf.is_encrypted):
                raise ValueError('PDF structure differs')
            pages += pdf.page_count
    validation, _ = typed(root, 'VALIDATION', Validation)
    tx_sha = hashlib.sha256(ordinary(root, 'transaction.py').read_bytes()).hexdigest()
    if (validation.preparation_sha256 != EXPECTED_PLAN
            or validation.transaction_sha256 != tx_sha):
        raise ValueError('recorded validation/code binding differs')
    for result in validation.results:
        checked(root, result.stdout)
        checked(root, result.stderr)
    coverage = json.loads(checked(root, validation.coverage))
    if coverage['totals']['percent_covered'] != (
            validation.combined_branch_inclusive_coverage_percent):
        raise ValueError('recorded coverage differs')
    for baseline in plan.baseline:
        checked(root, baseline.preserved)
    checked(root, plan.deduplication)
    allowed = {'execution/LOCK', 'execution/INTENT.json', 'execution/RECEIPT.json'}
    allowed.update('execution/preimages/' + Path(i.repository_path).name for i in plan.baseline)
    if not set(execution) <= allowed:
        raise ValueError('unknown execution payload')
    return {
        'status': 'passed', 'closed_payloads': len(manifest.files), 'sources': 1,
        'physical_pages': pages, 'source_bytes': sum(t.source.size_bytes for t in plan.templates),
        'raw_before': plan.raw_before, 'raw_after': plan.raw_after,
        'ledger_before': plan.ledger_before, 'ledger_after': plan.ledger_after,
        'new_pdf_actions': 1, 'earlier_redirect_chain_actions': 3, 'selected_pdf_actions': ['A001'],
        'fee_pdf_intaken': False, 'future_execution_present': bool(execution),
        'execution_validated': False, 'legal_currentness': 'not_verified',
        'public_requests': 0, 'canonical_mutations': 0,
    }


if __name__ == '__main__':
    sys.stdout.write(json.dumps(verify(), indent=2) + "\n")
