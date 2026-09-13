"""Adapt existing offline regressions for the ordinary versioned successor modules."""
from pathlib import Path
BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3] / 'MasterLegalDatabase'
OUT = BASE / 'proposed/tests'
OUT.mkdir(parents=True, exist_ok=True)
for name in ('test_manual_watch_http.py', 'test_manual_watch_http_deadlines.py'):
    text = (ROOT / 'tests' / name).read_text()
    text = text.replace('manual_watch_http as g', 'manual_watch_http_v2 as g')
    text = text.replace('www.coloradosprings.gov', 'www.weld.gov')
    text = text.replace('coloradosprings.gov', 'www.gjcity.org')
    (OUT / name.replace('manual_watch_http', 'manual_watch_http_v2')).write_text(text)
text = (ROOT / 'tests/test_manual_source_watch.py').read_text()
text = text.replace('manual_source_watch as w', 'manual_source_watch_batches as w')
text = text.replace("SOURCE = Path(__file__).resolve().parents[1]", """PROPOSED = Path(__file__).resolve().parents[1]
SOURCE = PROPOSED.parents[4] / 'MasterLegalDatabase'""")
start = text.index('@pytest.fixture\ndef packet(')
end = text.index('\ndef bodies(', start)
fixture = '''@pytest.fixture
def packet(tmp_path: Path) -> Path:
    """Copy fixed configurations and exact six-source evidence into an isolated repository."""
    root = tmp_path / 'packet'
    catalog = json.loads((PROPOSED / w.CATALOG).read_bytes())
    copied = set()

    def copy(relative: str, base: Path = SOURCE) -> None:
        """Preserve selected immutable evidence without executing research scripts."""
        if relative in copied:
            return
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(base / relative, target)
        copied.add(relative)

    copy(w.CATALOG.as_posix(), PROPOSED)
    for selection in w.SELECTIONS.values():
        copy(selection.as_posix(), PROPOSED)
    for source in catalog['sources']:
        copy(source['baseline']['path'])
        for field in ('authority_evidence', 'custody_evidence', 'review_evidence'):
            copy(source[field]['artifact']['path'])
        copy(source['review_schema']['path'])
        for evidence in source['referral_evidence']:
            copy(evidence['artifact']['path'])
            if evidence['artifact']['path'].endswith('/PRESERVATION.json'):
                path = Path(evidence['artifact']['path'])
                data = json.loads((SOURCE / path).read_bytes())
                for item in data['sources'][:2]:
                    copy((path.parent / item['anchor']['parent']['path']).as_posix())
    selected = {s['record_id'] for s in catalog['sources']}
    output = root / w.MANUAL_MANIFEST
    output.parent.mkdir(parents=True, exist_ok=True)
    with (SOURCE / w.MANUAL_MANIFEST).open('rb') as reader, output.open('wb') as writer:
        for raw in reader:
            if json.loads(raw)['record_id'] in selected:
                writer.write(raw)
    return root

'''
text = text[:start] + fixture + text[end:]
text = text.replace("assert all(o.valid_pdf_pages == 7 and o.bytes_equal_to_baseline for o in result.observations)",
    "assert [o.valid_pdf_pages for o in result.observations] == [2, 3]\n    assert all(o.bytes_equal_to_baseline for o in result.observations)")
text = text.replace("assert '2015' in ' '.join(result.observations[0].source_context)",
    "assert result.observations[0].baseline_request_started_at is None")
text = text.replace("assert 'PPRBD' in ' '.join(result.observations[1].source_context)",
    "assert result.observations[1].authority_id == 'CO-COUNTY-WELD'")
text = text.replace('www.coloradosprings.gov', 'www.weld.gov')
text = text.replace('coloradosprings.gov', 'files.arapahoeco.gov')
text = text.replace("data['custody_scope']['sha256'] = '0' * 64", "data['source_catalog_sha256'] = '0' * 64")
start = text.index("    if change != 'date':")
end = text.index('\n\n\n@pytest.mark.parametrize', start)
text = text[:start] + "    with pytest.raises(ValueError):\n        w.Plan.model_validate_json(json.dumps(data))" + text[end:]
text = text.replace('result.manual_pdf_records == 3 and result.locally_hash_verified_pdf_originals == 2',
    'result.manual_pdf_records == 7 and result.locally_hash_verified_pdf_originals == 6')
text = text.replace('result.unselected_manual_pdf_records == 1',
    'result.unselected_manual_pdf_records == 5')
text = text.replace('assert result.accepted_prior_finite_live_source_checks == 2',
    "assert result.prior_watch_execution == 'not_asserted'")
start = text.index("@pytest.mark.parametrize('key', ['custody_schema', 'prior_live'])")
text = text[:start]
(OUT / 'test_manual_source_watch_batches.py').write_text(text)
