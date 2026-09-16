"""Run staged tests with only staged-plan and checkpoint reads redirected; no installer."""
from pathlib import Path
import sys
import tempfile
import pytest
import coverage
from prepare import HERE, ROOT, PROPOSED, BASELINE, load_proposed
cov=coverage.Coverage(source=[str(PROPOSED)],branch=True,
    data_file='/private/tmp/geode-final-three-final.coverage')
cov.start()
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
    status=pytest.main([str(path),'-q','-p','no:cacheprovider'])
    cov.stop()
    cov.save()
    cov.report(include=[str(PROPOSED/'manual_review_inventory.py')],show_missing=True)
    cov.json_report(outfile=str(HERE/'coverage.json'),
                    include=[str(PROPOSED/'manual_review_inventory.py')])
    raise SystemExit(status)
