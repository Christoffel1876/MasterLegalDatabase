"""Replay the portable selected-line and registry bindings, without source opens or Git."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path

from packet_models import Comparison, Plan

ROOT = Path(__file__).resolve().parent


def verified(path: str, digest: str, size: int) -> bytes:
    """Verify a local non-JSONL payload after checking every path component."""
    relative = Path(path)
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('Unsafe comparison path')
    target = ROOT / relative
    if any(p.is_symlink() for p in [target, *target.parents]):
        raise ValueError('Symlinked comparison path')
    raw = target.read_bytes()
    if hashlib.sha256(raw).hexdigest() != digest or len(raw) != size:
        raise ValueError('Comparison payload differs')
    return raw


def main() -> int:
    """Recompute portable summaries; full-stream history remains a separately reported claim."""
    comparison = Comparison.model_validate_json((ROOT / 'COMPARISON.json').read_bytes())
    plan = Plan.model_validate_json((ROOT / 'PLAN.json').read_bytes())
    for name, model in [('PLAN', Plan), ('COMPARISON', Comparison)]:
        if json.loads((ROOT / (name + '.schema.json')).read_bytes()) != model.model_json_schema():
            raise ValueError('Preparation schema differs')
    if (plan.max_actions, plan.max_actions_per_county, plan.max_distinct_urls,
        plan.max_body_bytes, plan.max_total_body_bytes, plan.max_pending_actions) != (
            40, 20, 30, 20_000_000, 80_000_000, 1):
        raise ValueError('Prepared limits differ')
    if (plan.research_cutoff, plan.report_cutoff) != (
            '2026-09-13T03:05:00Z', '2026-09-13T03:20:00Z'):
        raise ValueError('Prepared cutoffs differ')
    if len(plan.seeds) != 8 or len({s.url for s in plan.seeds}) != 8:
        raise ValueError('Initial source scope differs')
    registry_input = next(i for i in comparison.inputs
                          if i.repository_path == '_CONTROL_PLANE/LOCAL_SOURCE_REGISTRY.json')
    registry = json.loads(verified(registry_input.working.path, registry_input.working.sha256,
                                   registry_input.working.size_bytes))
    by_id = {}
    for entry in comparison.registry_entries:
        value = registry
        for key in entry.json_pointer.strip('/').split('/'):
            value = value[int(key)] if isinstance(value, list) else value[key]
        if value != entry.record:
            raise ValueError('Registry pointer/object binding differs')
        by_id[value['source_id']] = entry
    for seed in plan.seeds:
        entry = by_id[seed.source_id]
        if (seed.url, seed.authority_id, seed.registry_json_pointer) != (
                entry.record['url'], entry.record['authority_id'], entry.json_pointer):
            raise ValueError('Seed identity or exact URL differs')
    for legacy in comparison.legacy:
        rows = 0
        authority, status, urls, source_ids = Counter(), Counter(), Counter(), Counter()
        hashes = set()
        relative = Path(legacy.selected.path)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('Unsafe selected path')
        target = ROOT / relative
        if any(p.is_symlink() for p in [target, *target.parents]):
            raise ValueError('Symlinked selected path')
        digest, size = hashlib.sha256(), 0
        with target.open('rb') as handle:
            for line in handle:
                digest.update(line)
                size += len(line)
                record = json.loads(line)
                rows += 1
                authority[record.get('authority_id', 'unknown')] += 1
                status[record.get('status', 'unknown')] += 1
                source_ids[record.get('source_id', 'unknown')] += 1
                for url in {record.get(k) for k in
                            ['source_url', 'requested_url', 'final_url', 'url']}:
                    if isinstance(url, str):
                        urls[url] += 1
                sha = record.get('sha256')
                if isinstance(sha, str) and len(sha) == 64:
                    hashes.add(sha)
        if (size, digest.hexdigest()) != (legacy.selected.size_bytes, legacy.selected.sha256):
            raise ValueError('Selected original lines differ')
        if (rows, dict(authority), dict(status), dict(urls), dict(source_ids), sorted(hashes)) != (
                legacy.selected_rows, legacy.by_authority, legacy.status_counts,
                legacy.url_attempts, legacy.source_id_attempts, legacy.recorded_sha256s):
            raise ValueError('Selected-line summary differs')
        lines = legacy.original_line_numbers
        if len(lines) != rows or lines != sorted(set(lines)) or max(lines) > legacy.full_rows:
            raise ValueError('Original line-number bounds differ')
    print(json.dumps({'status': 'passed', 'initial_urls': 8,
                      'selected_historical_rows_per_edition': [x.selected_rows
                                                               for x in comparison.legacy],
                      'full_stream_hashes_recomputed_portably': False,
                      'public_source_opens': 0, 'dispatch': 'not_performed'}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
