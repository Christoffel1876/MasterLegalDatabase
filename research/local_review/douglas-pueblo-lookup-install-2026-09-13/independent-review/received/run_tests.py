"""Measure proposed source lookup code without installing production changes."""
from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path

import coverage
import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3] / "MasterLegalDatabase"


def main() -> int:
    """Load only the prepared adapter while existing source bytes remain in the repository."""
    sys.path.insert(0, str(ROOT))
    import scripts

    measurement = coverage.Coverage(branch=True,
        include=[str(HERE / "proposed/research_source_lookup.py")],
        data_file="/private/tmp/geode-dp-native-lookup-revision-1.coverage")
    measurement.start()
    try:
        spec = importlib.util.spec_from_file_location("scripts.research_source_lookup",
                                                     HERE / "proposed/research_source_lookup.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        scripts.research_source_lookup = module
        module.__file__ = str(ROOT / "scripts/research_source_lookup.py")
        text = (HERE / "proposed/test_douglas_pueblo_native_lookup.py").read_text()
        text = text.replace("Path(__file__).resolve().parents[1]", "Path(" + repr(str(ROOT)) + ")")
        text = text.replace('ROOT / "tests/fixtures/douglas_pueblo_native_lookup/seven-native-sources"',
                            "Path(" + repr(str(HERE / "fixtures/seven-native-sources")) + ")")
        text = text.replace("Path(lookup.__file__).absolute()",
                            "Path(" + repr(str(HERE / "proposed/research_source_lookup.py")) + ")")
        with tempfile.TemporaryDirectory(prefix="geode-dp-lookup-tests-") as folder:
            test = Path(folder) / "test_douglas_pueblo_native_lookup.py"
            test.write_text(text)
            targets = [str(test)]
            if "--combined" in sys.argv:
                targets += [str(ROOT / "tests" / name) for name in [
                    "test_research_source_lookup.py", "test_colorado_springs_native_lookup.py",
                    "test_el_paso_ehs_native_lookup.py"]]
            return pytest.main([*targets, "-q", "-p", "no:cacheprovider"])
    finally:
        measurement.stop()
        measurement.json_report(outfile=str(HERE / "coverage.json"))


if __name__ == "__main__":
    raise SystemExit(main())
