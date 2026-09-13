"""Load normal staged modules without installing or modifying a repository package."""
from pathlib import Path
import importlib.util
import sys

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3] / 'MasterLegalDatabase'
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))

def load():
    """Load two separately versioned module files; never rewrite module source or host policy."""
    for name in ('manual_watch_http_v2', 'manual_source_watch_batches'):
        qualified = 'geode.pipeline.' + name
        path = BASE / 'proposed/geode/pipeline' / (name + '.py')
        spec = importlib.util.spec_from_file_location(qualified, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[qualified] = module
        spec.loader.exec_module(module)
    return module

if __name__ == '__main__':
    watch = load()
    raise SystemExit(watch.main())
