"""Run staged tests with only staged-plan and checkpoint reads redirected; no installer."""
from pathlib import Path
import sys
import tempfile
import pytest
from prepare import HERE, ROOT, PROPOSED, BASELINE, load_proposed
module=load_proposed()
import geode.pipeline
sys.modules['geode.pipeline.manual_review_inventory']=module
geode.pipeline.manual_review_inventory=module
source=(PROPOSED/'test_manual_review_inventory.py').read_text()
source=source.replace('Path(__file__).resolve().parents[1]',repr(ROOT))
source=source.replace('(root / inventory.PLAN)', '(Path('+repr(str(PROPOSED))+') / "join-plan.json")')
source=source.replace('(root / inventory.PACKAGE / "inventory.json")',
                      '(Path('+repr(str(PROPOSED))+') / "inventory.json")')
source=source.replace('root / inventory.PACKAGE / "_SNAPSHOTS/BEFORE_FINAL_THREE_2026-09-13"',
                      'Path('+repr(str(BASELINE))+')')
with tempfile.TemporaryDirectory(prefix='geode-final-three-tests-') as temp:
    path=Path(temp)/'test_manual_review_inventory.py'
    path.write_text(source.replace('from pathlib import Path', 'from pathlib import Path, PosixPath'))
    raise SystemExit(pytest.main([str(path),'-q','-p','no:cacheprovider',
        '--cov=prepared_inventory','--cov-branch','--cov-report=term-missing',
        '--cov-report=json:'+str(HERE/'coverage.json')]))
