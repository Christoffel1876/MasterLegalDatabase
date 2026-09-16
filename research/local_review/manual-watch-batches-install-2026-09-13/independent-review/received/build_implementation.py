"""Prepare ordinary versioned modules and three fixed offline configurations."""
from pathlib import Path
import hashlib
import json
import shutil

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3] / 'MasterLegalDatabase'
OUT = BASE / 'proposed/geode/pipeline'
OUT.mkdir(parents=True, exist_ok=True)
old = (ROOT / 'geode/pipeline/manual_watch_http.py').read_text()
new = old.replace('Maintained bounded HTTP custody for explicit manual-source watch selections.',
    'Version 2 bounded HTTP custody for six explicitly approved additional sources.')
new = new.replace("HOSTS = {'coloradosprings.gov', 'www.coloradosprings.gov'}", """# Version 1 remains unchanged for existing Springs saved-run replay.
# This transport policy is necessary, not sufficient: the adapter pins each exact URL.
HOSTS = {
    'files.arapahoeco.gov', 'www.weld.gov', 'www.gjcity.org', 'www.mesacounty.us',
    'cogy-p-001.sitecorecontenthub.cloud',
}""")
(OUT / 'manual_watch_http_v2.py').write_text(new)
old = (ROOT / 'geode/pipeline/manual_source_watch.py').read_text()
old = old.replace('Two-source manual PDF byte watch with canonical custody and read-only readiness.',
    'Three fixed two-source watch batches with custody checks and no automatic enrollment.')
old = old.replace('from typing import Any, Callable, Literal',
    'from typing import Any, Callable, Literal\n\nfrom pydantic import JsonValue')
old = old.replace('manual_watch_http as g', 'manual_watch_http_v2 as g')
start = old.index("SELECTION =")
end = old.index('class Availability')
proposal_model = (BASE / 'inputs/proposal-proposal_models.py').read_text()
source_class = proposal_model[proposal_model.index('class Evidence'):proposal_model.index('class Remaining')]
source_class = source_class.replace('(Strict)', '(g.Strict)').replace(': Ref', ': g.Ref')
source_class = source_class.replace('class Candidate', 'class SourceBinding')
constants = '''MANUAL_MANIFEST = Path('_RAW_ARCHIVE/manual_intake/manual_source_intake_manifest.jsonl')
RUNTIME = Path('.geode_runtime/manual_source_watch_batches')
CATALOG = Path('config/manual_source_watch_sources_v1.json')
CATALOG_SHA = 'd70ab79926513fa01d502ca03b824223fd47cb62f4d5d3a750d2c2633d6e564a'
BATCHES = {
    'county-fees-v1': ('arapahoe-planning-fees-sd002-14',
                       'weld-ehs-fees-2026-atlas-directed'),
    'western-fees-v1': ('grand-junction-fire-fees-atlas-directed',
                        'mesa-building-fees-exhibit-a-atlas-directed'),
    'greeley-fees-v1': ('greeley-building-fees-sd008-06',
                       'greeley-development-impact-fee-memo-sd008-07'),
}
SELECTIONS = {key: Path('config/manual_source_watch_' + key.replace('-', '_') + '.json')
              for key in BATCHES}
SELECTION = SELECTIONS['county-fees-v1']

'''
classes = '''class Catalog(g.Strict):
    """Immutable explicit six-source admission data, separate from installed/live status."""
    schema_version: Literal[1]
    catalog_version: Literal['2026-09-13-v1']
    prepared_at: AwareDatetime
    status: Literal['PREPARED_NOT_INSTALLED']
    sources: list[SourceBinding] = Field(min_length=6, max_length=6)
    public_requests: Literal[0]
    legal_currentness: Literal['not_verified']


class Target(g.Target):
    """One exact source and complete custody/qualification fields for result consumers."""
    canonical_source_id: str
    authority_id: str
    baseline: g.Ref
    baseline_page_count: int = Field(ge=1, le=100)
    baseline_request_started_at: AwareDatetime | None
    baseline_response_finished_at: AwareDatetime
    repository_received_at: AwareDatetime
    intake_id: str
    raw_manifest_line_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    source_context: list[str] = Field(min_length=1)
    source: SourceBinding
    legal_currentness: Literal['not_verified'] = 'not_verified'

    @model_validator(mode='after')
    def consistent(self) -> Target:
        """Refuse inconsistent convenience fields or loss of qualification context."""
        expected = target_fields(self.source)
        if self.model_dump(exclude={'source'}) != expected:
            raise ValueError('Source/target custody or context differs')
        return self


def target_fields(source: SourceBinding) -> dict[str, Any]:
    """Expose dates according to their recorded roles; never fill an unknown start time."""
    return dict(source_id=source.record_id, canonical_source_id=source.record_id,
        authority_id=source.authority_id, url=source.proposed_url, baseline=source.baseline.model_dump(),
        baseline_page_count=source.baseline_pages,
        baseline_request_started_at=source.http_started_at,
        baseline_response_finished_at=source.http_finished_at,
        repository_received_at=source.repository_received_at, intake_id=source.intake_id,
        raw_manifest_line_sha256=source.raw_manifest_exact_line_sha256,
        source_context=[source.http_time_role, source.official_link_basis,
                        *source.review_limitations, *source.enrollment_conditions],
        legal_currentness='not_verified')


class Plan(g.Plan):
    """One selected named pair. Limits may narrow, but source membership never expands."""
    batch_id: Literal['county-fees-v1', 'western-fees-v1', 'greeley-fees-v1']
    status: Literal['configured_not_scheduled']
    targets: list[Target] = Field(min_length=2, max_length=2)
    source_catalog_sha256: Literal[
        'd70ab79926513fa01d502ca03b824223fd47cb62f4d5d3a750d2c2633d6e564a']
    automatic_baseline_updates: Literal[False] = False
    legal_currentness: Literal['not_verified'] = 'not_verified'
    qualifications: list[str]

    @model_validator(mode='after')
    def fixed_sources(self) -> Plan:
        """Refuse source/batch swaps before examining any transport destination."""
        if tuple(t.source_id for t in self.targets) != BATCHES[self.batch_id]:
            raise ValueError('Exactly the two ordered batch sources are required')
        return self


'''
old = old[:start] + constants + source_class + classes + old[end:]
old = old.replace("authority_id: Literal['CO-MUNICIPAL-COLORADO_SPRINGS']", 'authority_id: str')
old = old.replace('baseline_request_started_at: AwareDatetime\n',
                  'baseline_request_started_at: AwareDatetime | None\n')
old = old.replace('    accepted_prior_finite_live_source_checks: int\n    prior_live_checked_at: AwareDatetime',
    "    batch_id: str\n    existing_other_batch_sources: Literal[4] = 4\n    prior_watch_execution: Literal['not_asserted'] = 'not_asserted'")
old = old.replace('    source_context: list[str]\n    status:',
    '    source_context: list[str]\n    source: SourceBinding\n    status:')
old = old.replace('intake_id=target.intake_id, source_context=target.source_context,',
    'intake_id=target.intake_id, source_context=target.source_context, source=target.source,')
start = old.index('def repository_root(')
end = old.index('def checked_bytes(', start)
old = old[:start] + '''def repository_root(path: Path) -> Path:
    """Infer only one of the three standard config paths; no arbitrary plan location."""
    path = path.absolute()
    g.ordinary(path)
    if (path.name not in {p.name for p in SELECTIONS.values()} or
            path.parent.name != 'config' or '..' in path.parts):
        raise ValueError('Selection must use a fixed <repository>/config batch filename')
    return path.parent.parent


''' + old[end:]
start = old.index('def prior_live_check(')
end = old.index('def readiness(', start)
old = old[:start] + (BASE / 'source_preflight.py.fragment').read_text() + old[end:]
old = old.replace('def readiness(root: Path, selection_path: Path | None = None) -> Readiness:',
    'def readiness(root: Path, selection_path: Path | None = None) -> Readiness:')
old = old.replace('    count, checked_at = prior_live_check(root, plan)\n', '')
old = old.replace('        accepted_prior_finite_live_source_checks=count, prior_live_checked_at=checked_at,',
    '        batch_id=plan.batch_id,')
old = old.replace('.geode_runtime/manual_source_watch/<run-name>',
    '.geode_runtime/manual_source_watch_batches/<run-name>')
old = old.replace("    parser.add_argument('--run-name')", "    parser.add_argument('--batch', choices=list(BATCHES), default='county-fees-v1')\n    parser.add_argument('--run-name')")
old = old.replace('        plan_path = root / SELECTION', '        plan_path = root / SELECTIONS[args.batch]')
old = old.replace('            result = readiness(root)', '            result = readiness(root, plan_path)')
(OUT / 'manual_source_watch_batches.py').write_text(old)
