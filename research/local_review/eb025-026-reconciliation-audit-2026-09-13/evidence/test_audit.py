"""Bounded refusal probes for the independent join verifier; no original mutation."""
import copy
import json
from pathlib import Path
import shutil

import pytest
from models import Audit
from verify_audit import HERE, PACKAGE, read, sha, verify_joins


def inputs():
    """Load immutable audit and exact reconciliation fixtures."""
    audit = Audit.model_validate_json((HERE / 'AUDIT.json').read_bytes())
    rec = json.loads((HERE / 'repository' / PACKAGE / 'RECONCILIATION.json').read_bytes())
    return audit, rec


def test_all_sixteen_joins():
    """The original scoped findings all join."""
    audit, rec = inputs()
    assert verify_joins(HERE, rec, audit)['findings'] == 16


@pytest.mark.parametrize('change,match', [
    ('summary', 'report summary'), ('severity', 'severity join'),
    ('missing', 'finding scope'), ('duplicate', 'finding scope'),
    ('corrected', 'unapproved source correction'), ('empty', 'empty evidence'),
    ('current', 'currentness'), ('safe', 'scope promotion'),
    ('translation', 'scope promotion'), ('independent', 'scope promotion'),
])
def test_reject_changed_claim_or_scope(change, match):
    """Rejection does not depend on an outer manifest catching the change first."""
    audit, original = inputs()
    rec = copy.deepcopy(original)
    if change == 'summary':
        rec['findings'][0]['reported_summary'] += ' invented'
    elif change == 'severity':
        rec['findings'][0]['reported_classification'] = 'minor'
    elif change == 'missing':
        rec['findings'].pop()
    elif change == 'duplicate':
        rec['findings'][-1] = rec['findings'][0]
    elif change == 'corrected':
        rec['findings'][0]['correction_applied'] = True
    elif change == 'empty':
        rec['findings'][0]['evidence'] = []
    elif change == 'current':
        rec['legal_currentness'] = 'verified'
    else:
        key = {'safe': 'answer_safe', 'translation': 'translation_equivalence_verified',
               'independent': 'independent_grok_review_established'}[change]
        rec[key] = True
    with pytest.raises(ValueError, match=match):
        verify_joins(HERE, rec, audit)


@pytest.mark.parametrize('name', ['../outside', '/etc/hosts', './AUDIT.json'])
def test_unsafe_paths_refused(name):
    """No alias, traversal or absolute source reads."""
    with pytest.raises(ValueError):
        read(HERE, name)


def test_symlink_refused(tmp_path):
    """Read helper refuses a linked evidence leaf."""
    (tmp_path / 'alias').symlink_to(HERE / 'AUDIT.json')
    with pytest.raises(ValueError, match='linked evidence'):
        read(tmp_path, 'alias')


def test_rehashed_footer_year_promotion_refused(tmp_path):
    """Even a coherently rehashed source-QA join cannot certify the clipped year."""
    audit, rec = inputs()
    shutil.copytree(HERE / 'repository', tmp_path / 'repository')
    pin = rec['pre_report_qa'][0]
    path = tmp_path / 'repository' / pin['path']
    data = json.loads(path.read_bytes())
    data['footer_evidence'][0]['visually_certified_year'] = 2023
    body = json.dumps(data).encode()
    path.write_bytes(body)
    # Rebind every occurrence to bypass the ordinary stale-digest protection.
    refs = rec['pre_report_qa'] + [e for f in rec['findings'] for e in f['evidence']]
    for ref in refs:
        if ref['path'] == pin['path']:
            ref['sha256'] = sha(body)
            ref['size_bytes'] = len(body)
    with pytest.raises(ValueError, match='footer year certification'):
        verify_joins(tmp_path, rec, audit)
