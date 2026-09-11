"""Failures and bounded review semantics for the additive manual inventory."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from geode.pipeline import manual_review_inventory as inventory


def save(path: Path, value: Any) -> None:
    """Write fixture JSON without using production corpus outputs."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


@pytest.fixture
def corpus(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Two sources: one partial reviewed county source and one unmatched city source."""
    records = []
    provenance = []
    for number, (sid, authority, layer) in enumerate([
        ("county-one", "CO-COUNTY-ONE", "08_County_Authorities"),
        ("city-two", "CO-MUNICIPAL-TWO", "10_Municipal_Authorities"),
    ]):
        raw = f"_RAW_ARCHIVE/manual_intake/{layer}/{sid}/original.pdf"
        (tmp_path / raw).parent.mkdir(parents=True)
        (tmp_path / raw).write_bytes(b"%PDF-1.7\nfixture-original-bytes-" + str(number).encode())
        source = inventory.identity(tmp_path, raw)
        records.append({
            "intake_id": f"intake-{number}", "record_id": sid, "layer_id": layer,
            "official_source_name": "Fixture authority", "official_source_url": None,
            "acquisition_method": "received_review_package", "received_from": "Fixture",
            "reviewer_name": "Fixture", "reviewer_email": None,
            "custody_note": "Received bytes, not independently acquired publisher original.",
            "original_filename": "original.pdf", "archive_path": raw,
            "sha256": source.sha256, "size_bytes": source.size_bytes, "source_format": "pdf",
            "received_at": "2026-09-11T20:00:00Z", "status": "archived_pending_pipeline",
            "blocked_queue_match": False, "boundary": "No legal-currentness promotion",
        })
        provenance.append({
            "source_id": sid, "authority_id": authority, "sha256": source.sha256,
            "claimed_at": "2026-09-10T12:00:00Z", "verified_at": "2026-09-11T19:00:00Z",
            "http_status": 200, "role": "unsigned draft", "qualification": "claim only",
        })
    manifest = "manual.jsonl"
    (tmp_path / manifest).write_text("".join(json.dumps(row) + "\n" for row in records))
    (tmp_path / "legacy.json").write_text('{"current":false}')
    (tmp_path / "provenance.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in provenance))
    review = {
        "source_id": "historical-county-alias", "source_sha256": records[0]["sha256"],
        "authority_id": "CO-COUNTY-ONE", "scope": {"pages": [2], "whole_document": False},
        "limits": ["Only two selected passages; adoption and currentness unknown"],
        "legal_currentness": "not_verified",
    }
    schema = {
        "type": "object", "additionalProperties": False,
        "required": list(review),
        "properties": {
            "source_id": {"type": "string"}, "source_sha256": {"type": "string"},
            "authority_id": {"type": "string"}, "scope": {"type": "object"},
            "limits": {"type": "array", "items": {"type": "string"}},
            "legal_currentness": {"const": "not_verified"},
        },
    }
    save(tmp_path / "review.json", review)
    save(tmp_path / "review.schema.json", schema)
    asset = lambda name: inventory.identity(tmp_path, name).model_dump()
    schema_asset = asset("review.schema.json")
    monkeypatch.setattr(inventory, "ALLOWED_REVIEW_SCHEMAS", {
        schema_asset["sha256"]: "checked_passages",
    })
    document = {"artifact": asset("provenance.jsonl"), "jsonl_row": 0}
    plan = {
        "schema_version": 1, "prepared_at": "2026-09-11T21:00:00Z",
        "manual_manifest": asset(manifest), "legacy_ledger": asset("legacy.json"),
        "authorities": [], "reviews": [{
            "record_id": records[0]["record_id"], "review": asset("review.json"),
            "review_schema": schema_asset, "source_sha_pointer": "/source_sha256",
            "source_id_pointer": "/source_id",
            "expected_review_source_id": "historical-county-alias",
            "authority_pointer": "/authority_id", "scope_pointers": ["/scope"],
            "limitation_pointers": ["/limits"], "note": "Exact hash alias, partial scope only",
        }], "limitations": ["Recorded scopes are not summed; legal currentness unknown"],
    }
    for i, row in enumerate(provenance):
        doc = {**document, "jsonl_row": i}
        plan["authorities"].append({
            "record_id": row["source_id"], "authority_id": row["authority_id"],
            "provenance": doc, "sha_pointer": "/sha256", "source_id_pointer": "/source_id",
            "authority_pointer": "/authority_id", "reported_acquisition_pointers": ["/claimed_at"],
            "role_pointers": ["/role"], "qualification_pointers": ["/qualification"],
            "verified_http": {
                "document": doc, "sha_pointer": "/sha256", "status_pointer": "/http_status",
                "time_pointer": "/verified_at",
            } if i == 0 else None,
        })
    save(tmp_path / inventory.PLAN, plan)
    return {"root": tmp_path, "plan": plan, "records": records,
            "provenance": provenance, "review": review, "schema": schema}


def rebuild(case: dict[str, Any]) -> inventory.Inventory:
    """Persist changed fixture plan and run the public builder."""
    save(case["root"] / inventory.PLAN, case["plan"])
    return inventory.build_inventory(case["root"])


def rebind(case: dict[str, Any], filename: str, value: Any) -> None:
    """Bind a deliberate fixture mutation so semantic gates, not only hashes, are tested."""
    root, plan = case["root"], case["plan"]
    if filename.endswith(".jsonl"):
        (root / filename).write_text("".join(json.dumps(row) + "\n" for row in value))
    else:
        save(root / filename, value)
    asset = inventory.identity(root, filename).model_dump()
    if filename == "manual.jsonl":
        plan["manual_manifest"] = asset
    elif filename == "provenance.jsonl":
        for join in plan["authorities"]:
            join["provenance"]["artifact"] = asset
            if join["verified_http"]:
                join["verified_http"]["document"]["artifact"] = asset
    else:
        key = "review_schema" if filename.endswith("schema.json") else "review"
        plan["reviews"][0][key] = asset


def test_partial_scope_unknown_review_and_separate_times(corpus: dict[str, Any]) -> None:
    result = rebuild(corpus)
    county, city = result.sources
    assert (result.rows_with_review, result.rows_without_review) == (1, 1)
    assert county.reviews[0].scope_fields == {"/scope": {"pages": [2], "whole_document": False}}
    assert county.reviews[0].review_source_id == "historical-county-alias"
    assert county.reviews[0].limitations["/limits"] == corpus["review"]["limits"]
    assert city.reviews is None and city.review_status == "metadata_only_review_unknown"
    assert city.verified_http_acquired_at is None
    assert city.reported_acquisition["/claimed_at"] == "2026-09-10T12:00:00Z"
    assert county.verified_http_acquired_at < county.intake_received_at
    assert county.source_roles == {"/role": "unsigned draft"}
    assert not result.answer_safe and not result.coverage_promotion
    assert result.legal_currentness == "not_verified"


@pytest.mark.parametrize("file", ["raw", "manual.jsonl", "legacy.json", "provenance.jsonl",
                                  "review.json", "review.schema.json"])
def test_tampered_pinned_evidence_fails(corpus: dict[str, Any], file: str) -> None:
    target = corpus["records"][0]["archive_path"] if file == "raw" else file
    with (corpus["root"] / target).open("ab") as handle:
        handle.write(b" ")
    with pytest.raises(ValueError, match="hash/size"):
        inventory.build_inventory(corpus["root"])
    assert not (corpus["root"] / inventory.PACKAGE / "inventory.json").exists()


@pytest.mark.parametrize("change", ["extra", "string_bool", "non_pdf", "duplicate_id",
                                   "duplicate_intake", "duplicate_path", "missing_row"])
def test_bad_manual_rows(corpus: dict[str, Any], change: str) -> None:
    rows = corpus["records"]
    if change == "extra":
        rows[0]["invented"] = True
    elif change == "string_bool":
        rows[0]["blocked_queue_match"] = "false"
    elif change == "non_pdf":
        rows[0]["source_format"] = "html"
    elif change == "missing_row":
        rows.pop()
    else:
        key = {"duplicate_id": "record_id", "duplicate_intake": "intake_id",
               "duplicate_path": "archive_path"}[change]
        rows[1][key] = rows[0][key]
    rebind(corpus, "manual.jsonl", rows)
    with pytest.raises(ValueError):
        rebuild(corpus)


@pytest.mark.parametrize("change", ["join_duplicate", "join_missing", "wrong_source",
                                   "wrong_hash", "wrong_authority", "wrong_layer",
                                   "bad_http_hash", "failed_http", "naive_http", "row_missing"])
def test_provenance_and_authority_fail_closed(corpus: dict[str, Any], change: str) -> None:
    plan, rows = corpus["plan"], corpus["provenance"]
    if change == "join_duplicate":
        plan["authorities"].append(copy.deepcopy(plan["authorities"][0]))
    elif change == "join_missing":
        plan["authorities"].pop()
    elif change == "wrong_authority":
        plan["authorities"][0]["authority_id"] = "CO-COUNTY-OTHER"
    elif change == "wrong_layer":
        rows[0]["authority_id"] = "CO-MUNICIPAL-ONE"
        plan["authorities"][0]["authority_id"] = rows[0]["authority_id"]
    elif change == "bad_http_hash":
        plan["authorities"][0]["verified_http"]["sha_pointer"] = "/source_id"
    elif change == "row_missing":
        plan["authorities"][0]["provenance"]["jsonl_row"] = 9
    else:
        key, value = {
            "wrong_source": ("source_id", "other"), "wrong_hash": ("sha256", "0" * 64),
            "failed_http": ("http_status", 403), "naive_http": ("verified_at", "2026-09-11"),
        }[change]
        rows[0][key] = value
    rebind(corpus, "provenance.jsonl", rows)
    with pytest.raises(ValueError):
        rebuild(corpus)


@pytest.mark.parametrize("change", ["unknown_source", "duplicate", "unknown_schema", "hash",
                                   "alias", "authority", "currentness", "missing_scope"])
def test_review_join_failures(corpus: dict[str, Any], change: str) -> None:
    joins, review = corpus["plan"]["reviews"], corpus["review"]
    if change == "unknown_source":
        joins[0]["record_id"] = "unknown"
    elif change == "duplicate":
        joins.append(copy.deepcopy(joins[0]))
    elif change == "unknown_schema":
        joins[0]["review_schema"]["sha256"] = "0" * 64
    elif change == "missing_scope":
        joins[0]["scope_pointers"] = []
    else:
        key, value = {
            "hash": ("source_sha256", corpus["records"][1]["sha256"]),
            "alias": ("source_id", "other-source"),
            "authority": ("authority_id", "CO-COUNTY-OTHER"),
            "currentness": ("legal_currentness", "current"),
        }[change]
        review[key] = value
    rebind(corpus, "review.json", review)
    with pytest.raises((ValueError, inventory.jsonschema.ValidationError)):
        rebuild(corpus)


def test_external_schema_reference_is_never_resolved(
    corpus: dict[str, Any], monkeypatch: pytest.MonkeyPatch,
) -> None:
    schema = corpus["schema"]
    schema["allOf"] = [{"$ref": "https://example.invalid/remote.json"}]
    rebind(corpus, "review.schema.json", schema)
    digest = corpus["plan"]["reviews"][0]["review_schema"]["sha256"]
    monkeypatch.setattr(inventory, "ALLOWED_REVIEW_SCHEMAS", {digest: "checked_passages"})
    with pytest.raises(ValueError, match="External schema"):
        rebuild(corpus)


@pytest.mark.parametrize("path", ["../outside", "/absolute", "a/../b"])
def test_path_escape_rejected(tmp_path: Path, path: str) -> None:
    with pytest.raises(ValueError, match="Unsafe"):
        inventory.safe_path(tmp_path, path)


def test_symlink_and_wrong_raw_root_rejected(corpus: dict[str, Any]) -> None:
    root = corpus["root"]
    (root / "linked").symlink_to(root / "_RAW_ARCHIVE", target_is_directory=True)
    with pytest.raises(ValueError, match="Symlinked"):
        inventory.safe_path(root, "linked/anything")
    corpus["records"][0]["archive_path"] = "outside.pdf"
    rebind(corpus, "manual.jsonl", corpus["records"])
    with pytest.raises(ValueError, match="immutable archive"):
        rebuild(corpus)


def test_json_document_pointer_and_absent_alias(corpus: dict[str, Any]) -> None:
    root, plan = corpus["root"], corpus["plan"]
    save(root / "single.json", corpus["provenance"][0])
    plan["authorities"][0]["provenance"] = {
        "artifact": inventory.identity(root, "single.json").model_dump(), "jsonl_row": None,
    }
    plan["reviews"][0].update(source_id_pointer=None, expected_review_source_id=None,
                              authority_pointer=None)
    assert rebuild(corpus).sources[0].reviews[0].review_source_id is None
    data = {"a/b": {"~": ["value"]}}
    assert inventory.pointer(data, "/a~1b/~0/0") == "value"
    assert inventory.pointer(data, "") is data
    with pytest.raises(ValueError, match="pointer"):
        inventory.pointer(data, "bad")


def test_write_check_tamper_snapshot_and_no_change(corpus: dict[str, Any]) -> None:
    root = corpus["root"]
    legacy_before = (root / "legacy.json").read_bytes()
    args = ["--root", str(root)]
    assert inventory.main([*args, "--write"]) == 0
    output = root / inventory.PACKAGE / "inventory.json"
    first, modified = output.read_bytes(), output.stat().st_mtime_ns
    assert inventory.main([*args, "--write"]) == 0
    assert output.read_bytes() == first and output.stat().st_mtime_ns == modified
    assert inventory.main([*args, "--check"]) == 0
    data = json.loads(first)
    data["sources"][0]["reviews"][0]["scope_fields"] = {"claimed_complete": True}
    save(output, data)
    assert inventory.main([*args, "--check"]) == 1
    tampered = output.read_bytes()
    assert inventory.main([*args, "--write"]) == 0
    snapshots = list((root / inventory.PACKAGE / "_SNAPSHOTS").rglob("inventory.json"))
    assert any(path.read_bytes() == tampered for path in snapshots)
    assert output.read_bytes() == first
    assert (root / "legacy.json").read_bytes() == legacy_before
    assert not (root / "_SNAPSHOTS").exists()


@pytest.mark.parametrize("field,value", [("answer_safe", True), ("coverage_promotion", True),
                                         ("legal_currentness", "current")])
def test_output_schema_cannot_claim_legal_promotion(
    corpus: dict[str, Any], field: str, value: Any,
) -> None:
    data = rebuild(corpus).model_dump(mode="json")
    data[field] = value
    with pytest.raises(ValidationError):
        inventory.Inventory.model_validate_json(json.dumps(data))


def test_bad_plan_and_missing_output_cli(corpus: dict[str, Any]) -> None:
    root = corpus["root"]
    assert inventory.main(["--root", str(root), "--check"]) == 1
    corpus["plan"]["invented"] = True
    save(root / inventory.PLAN, corpus["plan"])
    assert inventory.main(["--root", str(root), "--write"]) == 1
    with pytest.raises(ValueError, match="parent traversal"):
        inventory.build_inventory(root / ".." / root.name)


@pytest.mark.parametrize("filename", ["README.md", "inventory.schema.json"])
@pytest.mark.parametrize("mutation", ["missing", "tampered"])
def test_every_companion_is_checked_and_repaired(
    corpus: dict[str, Any], filename: str, mutation: str,
) -> None:
    root = corpus["root"]
    result = rebuild(corpus)
    inventory.write_inventory(root, result)
    path = root / inventory.PACKAGE / filename
    original = path.read_bytes()
    inventory_bytes = (root / inventory.PACKAGE / "inventory.json").read_bytes()
    if mutation == "missing":
        path.unlink()
    else:
        path.write_bytes(b"tampered companion")
    assert inventory.main(["--root", str(root), "--check"]) == 1
    assert inventory.main(["--root", str(root), "--write"]) == 0
    assert path.read_bytes() == original
    assert (root / inventory.PACKAGE / "inventory.json").read_bytes() == inventory_bytes
    if mutation == "tampered":
        copies = list((root / inventory.PACKAGE / "_SNAPSHOTS").rglob(filename))
        assert any(copy.read_bytes() == b"tampered companion" for copy in copies)
    inventory.check_inventory(root, result)


@pytest.mark.parametrize("filename", ["inventory.json", "inventory.schema.json", "README.md",
                                      "_SNAPSHOTS"])
def test_all_symlinks_preflight_before_any_write(corpus: dict[str, Any], filename: str) -> None:
    root = corpus["root"]
    result = rebuild(corpus)
    outside = root / "outside"
    outside.write_bytes(b"must remain untouched")
    (root / inventory.PACKAGE / filename).symlink_to(outside)
    with pytest.raises(ValueError, match="Symlinked"):
        inventory.write_inventory(root, result)
    assert outside.read_bytes() == b"must remain untouched"
    for name in ["inventory.json", "inventory.schema.json", "README.md"]:
        path = root / inventory.PACKAGE / name
        assert path.is_symlink() or not path.exists()


def test_bad_output_types_fail_before_any_write(corpus: dict[str, Any]) -> None:
    root = corpus["root"]
    result = rebuild(corpus)
    output = root / inventory.PACKAGE / "README.md"
    output.mkdir()
    with pytest.raises(ValueError, match="ordinary file"):
        inventory.write_inventory(root, result)
    assert not (output.parent / "inventory.json").exists()
    output.rmdir()
    (output.parent / "_SNAPSHOTS").write_text("not a directory")
    with pytest.raises(ValueError, match="Snapshot destination"):
        inventory.write_inventory(root, result)
    assert not (output.parent / "inventory.json").exists()


@pytest.mark.parametrize("root_form", ["relative", "tilde"])
def test_cli_root_forms_target_one_tree(
    corpus: dict[str, Any], monkeypatch: pytest.MonkeyPatch, root_form: str,
) -> None:
    root = corpus["root"]
    monkeypatch.chdir(root.parent)
    monkeypatch.setenv("HOME", str(root.parent))
    spelling = root.name if root_form == "relative" else "~/" + root.name
    assert inventory.main(["--root", spelling, "--write"]) == 0
    assert inventory.main(["--root", spelling, "--check"]) == 0
    assert (root / inventory.PACKAGE / "inventory.json").is_file()


def test_symlinked_root_refused(corpus: dict[str, Any]) -> None:
    root = corpus["root"]
    (root / "root-alias").symlink_to(root, target_is_directory=True)
    with pytest.raises(ValueError, match="root must not contain symlinks"):
        inventory.build_inventory(root / "root-alias")


@pytest.mark.parametrize("mutation", ["count", "duplicate", "status", "empty_review"])
def test_standalone_inventory_model_rejects_false_review_accounting(
    corpus: dict[str, Any], mutation: str,
) -> None:
    data = rebuild(corpus).model_dump(mode="json")
    if mutation == "count":
        data["rows_with_review"] = 2
    elif mutation == "duplicate":
        data["sources"][1]["record_id"] = data["sources"][0]["record_id"]
    elif mutation == "empty_review":
        data["sources"][0]["reviews"] = []
    else:
        data["sources"][1]["review_status"] = "explicit_review_artifacts_linked"
    with pytest.raises(ValueError):
        inventory.Inventory.model_validate_json(json.dumps(data))
