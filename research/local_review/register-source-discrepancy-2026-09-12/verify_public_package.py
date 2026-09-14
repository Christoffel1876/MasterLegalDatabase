"""Verify this closed public subset without private headers, collection or writes."""

from __future__ import annotations

import hashlib
import html
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import jsonschema

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from models import Asset, CheckResult, Custody, Manifest

SENSITIVE = {
    b"set-cookie", b"cookie", b"authorization", b"proxy-authorization",
    b"www-authenticate", b"proxy-authenticate",
}
MISSING = [
    "RM-2026-daily-6ae185cdffa4fdedd5bb", "RM-2026-daily-fe6fe04b708089735009",
]


def sha(data: bytes) -> str:
    """Compute a byte-exact SHA256 digest."""
    return hashlib.sha256(data).hexdigest()


def read_record(relative: str) -> Any:
    """Read one inventory-bound JSON document after inventory preflight."""
    return json.loads((HERE / relative).read_bytes())


def checked_asset(asset: Asset) -> bytes:
    """Check path shape, size and digest without following links."""
    path = HERE / asset.path
    assert all(not parent.is_symlink() for parent in [path, *path.parents])
    assert path.is_file() and path.stat().st_size == asset.bytes
    data = path.read_bytes()
    assert len(data) == asset.bytes and sha(data) == asset.sha256
    return data


def check_inventory(manifest: Manifest) -> None:
    """Enforce a closed ordinary-file and directory inventory."""
    paths = [asset.path for asset in manifest.assets]
    assert len(paths) == len(set(paths)) and "FINAL_MANIFEST.json" not in paths
    entries = list(HERE.rglob("*"))
    assert not any(path.is_symlink() for path in [HERE, *HERE.parents, *entries])
    expected_files = set(paths) | {"FINAL_MANIFEST.json"}
    assert {p.relative_to(HERE).as_posix() for p in entries if p.is_file()} == expected_files
    expected_dirs = {
        parent.as_posix() for name in paths for parent in Path(name).parents
        if parent != Path(".")
    }
    assert {p.relative_to(HERE).as_posix() for p in entries if p.is_dir()} == expected_dirs
    for asset in manifest.assets:
        checked_asset(asset)


def passive_view(data: bytes) -> bytes:
    """Generate a passive display; original byte interpretation is ISO-8859-1."""
    prefix = (
        '<!doctype html><html><head><meta charset="utf-8">'
        '<meta http-equiv="Content-Security-Policy" '
        'content="default-src &#39;none&#39;; style-src &#39;none&#39;">'
        '<title>Passive source bytes</title></head><body><pre>'
    )
    return (prefix + html.escape(data.decode("iso-8859-1")) + "</pre></body></html>\n").encode()


def import_verified(path: Path) -> ModuleType:
    """Load a hash-checked local model/pure parser without calling its writer main."""
    spec = importlib.util.spec_from_file_location("preserved_detail_review", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def check_schema(prefix: str, record: str, schema: str | None = None) -> None:
    """Validate a preserved record against its exact exported schema."""
    jsonschema.validate(
        read_record(f"{prefix}{record}.json"),
        read_record(f"{prefix}{schema or record}.schema.json"),
    )


def check_sources(custody: Custody) -> None:
    """Reconcile the incomplete export with its original inventories and receipts."""
    copies = {row.path: row for row in custody.copies}
    assert len(copies) == 115
    for copy in copies.values():
        checked_asset(copy)
    exclusions = {row.would_be_package_path: row for row in custody.exclusions}
    assert len(exclusions) == 3 and set(exclusions).isdisjoint(copies)
    for subset in custody.source_subsets:
        selected = [p for p in copies if p.startswith(subset.package_prefix + "/")]
        omitted = [p for p in exclusions if p.startswith(subset.package_prefix + "/")]
        assert len(selected) == subset.copied_file_count
        assert len(omitted) == subset.excluded_file_count
        assert len(selected) + len(omitted) == subset.original_file_count
    original = read_record("historical-diagnosis/FINAL_MANIFEST.json")
    old_manifest = (HERE / "historical-diagnosis/FINAL_MANIFEST.json").read_bytes()
    assert sha(old_manifest) == custody.source_subsets[0].original_complete_manifest_sha256
    original_paths = {"historical-diagnosis/" + row["path"] for row in original["assets"]}
    original_paths.add("historical-diagnosis/FINAL_MANIFEST.json")
    assert original_paths == {
        p for p in set(copies) | set(exclusions) if p.startswith("historical-diagnosis/")
    }
    for row in original["assets"]:
        path = "historical-diagnosis/" + row["path"]
        if path in exclusions:
            excluded = exclusions[path]
            assert row["sha256"] == excluded.original_sha256
            assert row["bytes"] == excluded.original_bytes
        else:
            assert row["sha256"] == copies[path].sha256 and row["bytes"] == copies[path].bytes
    for excluded in exclusions.values():
        assert not (HERE / excluded.would_be_package_path).exists()
        public = checked_asset(excluded.public_derivative)
        assert not any(
            line.split(b":", 1)[0].strip().lower() in SENSITIVE for line in public.splitlines()
        )
        assert excluded.removed_field_names == ["set-cookie"]
    for view in custody.passive_views:
        assert checked_asset(view.view) == passive_view(checked_asset(view.source))


def check_issue() -> None:
    """Replay frozen notice identities and exact source slices with pinned old code."""
    prefix = "historical-diagnosis/"
    for name, schema in [
        ("BASELINE_RECEIPT", "BASELINE_RECEIPT"),
        ("SUPPLEMENTAL_BASELINE_RECEIPT", "BASELINE_RECEIPT"),
        ("MISSING_NOTICE_ORIGINALS_RECEIPT", "BASELINE_RECEIPT"),
        ("FETCH_RECEIPT", "FETCH_RECEIPT"),
        ("authorized-route/FETCH_RECEIPT", "authorized-route/FETCH_RECEIPT"),
        ("ARCHIVED_REPLAY", "ARCHIVED_REPLAY"),
        ("FRESH_COMPARISON", "FRESH_COMPARISON"),
        ("REMOVED_ROW_FRAGMENTS", "REMOVED_ROW_FRAGMENTS"),
        ("PUBLIC_HEADER_DERIVATIVE", "PUBLIC_HEADER_DERIVATIVE"),
        ("DECISION_RECEIPT", "DECISION_RECEIPT"),
        ("FINAL_MANIFEST", "FINAL_MANIFEST"),
    ]:
        check_schema(prefix, name, schema)
    for name in ["BASELINE_RECEIPT", "SUPPLEMENTAL_BASELINE_RECEIPT",
                 "MISSING_NOTICE_ORIGINALS_RECEIPT"]:
        for row in read_record(prefix + name + ".json")["assets"]:
            checked_asset(Asset(path=prefix + row["path"], sha256=row["sha256"],
                                bytes=row["bytes"]))
    for row in read_record(prefix + "REMOVED_ROW_FRAGMENTS.json")["fragments"]:
        source = (HERE / prefix / row["source_path"]).read_bytes()
        body = (HERE / prefix / row["path"]).read_bytes()
        assert sha(source) == row["source_sha256"]
        assert body == source[row["byte_start"]:row["byte_end"]]
        assert len(body) == row["bytes"] and sha(body) == row["sha256"]
        assert source[:row["byte_start"]].count(b"\n") + 1 == row["first_line"]
        assert source[:row["byte_end"]].count(b"\n") + 1 == row["last_line"]
    for script, expected in [("replay_offline.py", "ARCHIVED_REPLAY.json"),
                             ("compare_fresh.py", "FRESH_COMPARISON.json")]:
        result = subprocess.run(
            [sys.executable, "-I", "-B", str(HERE / prefix / script)],
            cwd=HERE, capture_output=True, timeout=40,
            env={"PATH": os.defpath, "PYTHONDONTWRITEBYTECODE": "1"},
        )
        assert result.returncode == 0, result.stderr.decode(errors="replace")
        assert json.loads(result.stdout) == read_record(prefix + expected)
    comparison = read_record(prefix + "FRESH_COMPARISON.json")
    assert comparison["old_notice_count"] == 50 and comparison["fresh_notice_count"] == 48
    assert comparison["common_rows_identical_except_row_number"] == 48
    assert comparison["removal_gate_missing_ids"] == MISSING


def check_details(custody: Custody) -> None:
    """Replay all 16 labeled fields per docket and actual HTTP/body custody."""
    prefix = "hearing-details/"
    check_schema(prefix, "DETAIL_REVIEW")
    check_schema(prefix, "PLAN")
    module = import_verified(HERE / prefix / "review_details.py")
    review = module.Review.model_validate_json((HERE / prefix / "DETAIL_REVIEW.json").read_bytes())
    state = read_record("historical-diagnosis/baseline/_CONTROL_PLANE/REGISTER_REFRESH_STATE.json")
    assert [d.docket for d in review.details] == ["2026-00337", "2026-00328"]
    for number, detail in enumerate(review.details, 1):
        sub = f"target-{number:02d}/"
        check_schema(prefix + sub, "FETCH_RECEIPT")
        receipt = read_record(prefix + sub + "FETCH_RECEIPT.json")
        assert receipt["status"] == "http_200_received" and len(receipt["events"]) == 1
        event = receipt["events"][0]
        assert event["requested_url"] == detail.requested_url == receipt["initial_url"]
        assert event["http_status"] == 200 and event["curl_exit"] == 0
        assert event["location"] is None
        assert detail.acquired_start.isoformat().replace("+00:00", "Z") == event["started_at"]
        assert detail.acquired_end.isoformat().replace("+00:00", "Z") == event["finished_at"]
        old = checked_asset(Asset(path=prefix + detail.old_body.path,
                                 sha256=detail.old_body.sha256, bytes=detail.old_body.size_bytes))
        fresh = checked_asset(Asset(path=prefix + detail.fresh_body.path,
                                   sha256=detail.fresh_body.sha256,
                                   bytes=detail.fresh_body.size_bytes))
        assert detail.fresh_body.path == sub + event["body_path"]
        assert sha(fresh) == event["body_sha256"] and len(fresh) == event["body_bytes"]
        state_source = state["sources"][detail.requested_url]
        assert sha(old) == state_source["sha256"]
        assert old == (HERE / "historical-diagnosis/baseline" / state_source["path"]).read_bytes()
        assert module.fields(old) == detail.old_fields
        assert module.fields(fresh) == detail.fresh_fields
        assert len(detail.old_fields) == len(detail.fresh_fields) == 16
        assert [(x.label, x.value) for x in detail.old_fields] == [
            (x.label, x.value) for x in detail.fresh_fields
        ]
        assert old != fresh and not detail.original_bytes_equal
        assert [x.value for x in detail.fresh_fields if x.label == "Date"] == [
            detail.visible_hearing_date
        ]
        excluded = next(x for x in custody.exclusions if x.would_be_package_path ==
                        prefix + sub + event["header_path"])
        assert excluded.original_sha256 == event["header_sha256"]
        derivative = review.header_derivatives[number - 1]
        assert derivative.original_private.sha256 == excluded.original_sha256
        assert derivative.original_private.size_bytes == excluded.original_bytes
        assert prefix + derivative.public.path == excluded.public_derivative.path
        assert derivative.public.sha256 == excluded.public_derivative.sha256
        assert derivative.public.size_bytes == excluded.public_derivative.bytes
    old_derivative = read_record("historical-diagnosis/PUBLIC_HEADER_DERIVATIVE.json")
    excluded = custody.exclusions[0]
    assert excluded.original_sha256 == old_derivative["original_sha256"]
    assert excluded.original_bytes == old_derivative["original_bytes"]
    assert excluded.public_derivative.sha256 == old_derivative["public_sha256"]
    assert excluded.public_derivative.bytes == old_derivative["public_bytes"]
    plan = read_record(prefix + "PLAN.json")
    assert plan["parent_comparison_sha256"] == sha(
        (HERE / "historical-diagnosis/FRESH_COMPARISON.json").read_bytes()
    )


def main() -> None:
    """Validate immutable public evidence without invoking its historical collectors."""
    manifest = Manifest.model_validate_json((HERE / "FINAL_MANIFEST.json").read_bytes())
    check_inventory(manifest)
    check_schema("", "FINAL_MANIFEST")
    check_schema("", "CUSTODY_RECEIPT")
    custody = Custody.model_validate_json((HERE / "CUSTODY_RECEIPT.json").read_bytes())
    check_sources(custody)
    check_issue()
    check_details(custody)
    check_inventory(manifest)
    result = CheckResult(
        status="verified_offline_public_subset", payloads=len(manifest.assets),
        exact_copied_files=115, excluded_private_headers=3, archived_notice_rows=50,
        fresh_notice_rows=48, common_notice_rows_unchanged_except_number=48,
        missing_notice_ids=MISSING, unchanged_detail_fields_per_docket={
            "2026-00337": 16, "2026-00328": 16,
        }, original_detail_bodies_byte_equal=False,
        raw_header_derivation_replayed_in_portable_package=False,
        legal_currentness="not_verified", new_network_requests=0,
    )
    sys.stdout.write(result.model_dump_json() + "\n")


if __name__ == "__main__":
    main()
