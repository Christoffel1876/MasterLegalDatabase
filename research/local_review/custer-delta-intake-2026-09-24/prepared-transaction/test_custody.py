"""Additional source-specific refusal tests using temporary copied packages only."""
from pathlib import Path
from typing import Any
import json
import pytest
import transaction as tx
from models import Preparation
from test_transaction import fixture, snapshot


def reseal(base: Path, plan: Preparation, asset: Any, value: Any) -> Preparation:
    """Reseal a deliberately altered fixture so semantic checks must reject it."""
    path = base / asset.path
    path.write_text(json.dumps(value))
    raw = path.read_bytes()
    data = plan.model_dump(mode='json')
    def update(node: Any) -> None:
        if isinstance(node, dict):
            if node.get('path') == asset.path and 'sha256' in node:
                node.update(sha256=tx.digest(raw), size_bytes=len(raw))
            for child in node.values():
                update(child)
        elif isinstance(node, list):
            for child in node:
                update(child)
    update(data)
    return Preparation.model_validate_json(json.dumps(data))


@pytest.mark.parametrize('field,value', [
    ('http_status', 403), ('exit_code', 23), ('physical_pages', 236),
    ('observed_final_url', 'https://www.deltacountyco.gov/wrong'),
    ('action_id', 'SHSTATE03-A999'), ('body_role', 'original_html'),
    ('body_size_basis', 'partial'), ('automatic_redirect_urls', ['https://example.invalid']),
    ('finished_at', '2020-01-01T00:00:00Z'),
])
def test_resealed_result_refused(fixture: Any, field: str, value: Any) -> None:
    """Coherent file resealing does not bypass the selected transport claims."""
    _, base, plan = fixture
    asset = plan.provenance[1].result
    data = json.loads((base / asset.path).read_bytes())
    data[field] = value
    revised = reseal(base, plan, asset, data)
    with pytest.raises(ValueError, match='transport binding'):
        tx.check_custody(base, revised)


def test_authority_mismatch_refused(fixture: Any) -> None:
    """Two allowed county names are not interchangeable for a selected original."""
    _, base, plan = fixture
    data = plan.model_dump(mode='json')
    data['templates'][0]['authority_id'] = 'CO-COUNTY-DELTA'
    data['provenance'][0]['authority_id'] = 'CO-COUNTY-DELTA'
    revised = Preparation.model_validate_json(json.dumps(data))
    with pytest.raises(ValueError, match='authority'):
        tx.check_custody(base, revised)


def test_delta_count_correction_preserved() -> None:
    """Keep the original236 claim distinct from independently parsed234 pages."""
    plan = tx.load_plan()
    item = plan.provenance[2]
    assert (item.physical_pages, item.originally_reported_pages) == (234, 236)
    assert all(t.original_filename.endswith('.bin') for t in plan.templates)
    assert all(t.official_source_url is None for t in plan.templates)
    assert all(t.acquisition_method == 'received_review_package' for t in plan.templates)
    assert all('equivalence' in p.limitations[-1] or p.action_id != 'SHSTATE03-A014'
               for p in plan.provenance)


def test_captured_source_aba_preserves_checked_bytes(fixture: Any, monkeypatch: Any) -> None:
    """Late ABA changes cannot replace the exact byte buffer selected for a write."""
    root, base, plan = fixture
    source = base / plan.templates[0].source.path
    original = source.read_bytes()
    old = tx.atomic_once
    def change_during_write(path: Path, raw: bytes) -> None:
        if path.suffix == '.bin':
            source.write_bytes(b'late foreign bytes')
            try:
                old(path, raw)
            finally:
                source.write_bytes(original)
        else:
            old(path, raw)
    monkeypatch.setattr(tx, 'atomic_once', change_during_write)
    done = tx.run(root, base=base, apply=True)
    assert (root / done['canonical_archive_paths'][0]).read_bytes() == original
    assert tx.run(root, base=base, verify=True) == done
