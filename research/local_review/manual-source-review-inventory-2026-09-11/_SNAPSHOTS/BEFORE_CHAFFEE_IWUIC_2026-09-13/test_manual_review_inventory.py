"""Failures and bounded review semantics for the additive manual inventory."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import jsonschema
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


GREELEY_REACQUIRED = {
    "greeley-building-fees-sd008-06",
    "greeley-development-impact-fee-memo-sd008-07",
    "greeley-water-sewer-proposed-pif-notice-sd008-08",
}


def _without_later_http(row: inventory.SourceRow) -> dict[str, Any]:
    value = row.model_dump()
    value.pop("verified_http_acquired_at")
    value.pop("verified_http_evidence")
    return value


def test_accepted_equity_review_is_one_bounded_additive_join() -> None:
    """The later two-page source review changes only its former null-review row."""
    root = Path(__file__).resolve().parents[1]
    checkpoint = root / (
        "docs/audits/ONE_HOUR_CONTINUATION_2026-09-11/inventory-at-first-checkpoint"
    )
    old_plan = json.loads((checkpoint / "join-plan.json").read_bytes())
    old = inventory.Inventory.model_validate_json((checkpoint / "inventory.json").read_bytes())
    new_plan = inventory.JoinPlan.model_validate_json((root / inventory.PLAN).read_bytes())
    new = inventory.build_inventory(root)
    assert len(old.sources) == 46
    assert len(new.sources) == 67
    assert (old.rows_with_review, old.rows_without_review) == (18, 28)
    assert (new.rows_with_review, new.rows_without_review) == (30, 37)
    assert [r.model_dump(mode="json") for r in new_plan.reviews[:18]] == old_plan["reviews"]
    assert len(new_plan.reviews) == 30
    previous = {s.record_id: s for s in old.sources}
    added = [row for row in new.sources if row.record_id not in previous
             and row.authority_id == "CO-COUNTY-EL_PASO"]
    assert len(added) == 13
    for row in added:
        assert row.authority_id == "CO-COUNTY-EL_PASO"
        if row.record_id in {
            "el-paso-planning-fees-sd011", "el-paso-boh-ehs-fees-sd011",
            "el-paso-boh-ehs-fees-spanish-sd011",
        }:
            assert len(row.reviews) == 1 and row.reviews[0].review_kind == "checked_tables"
        elif row.record_id in {
            "el-paso-boh-bylaws-sd011", "el-paso-boh-bylaws-spanish-sd011",
        }:
            assert len(row.reviews) == 1 and row.reviews[0].review_kind == "checked_passages"
        else:
            assert row.reviews is None and row.review_status == "metadata_only_review_unknown"
        assert row.verified_http_acquired_at is None and row.verified_http_evidence is None
        assert row.acquisition_method == "received_review_package"
        assert row.legal_currentness == "not_verified" and row.answer_safe is False
    for row in new.sources:
        if row.record_id not in previous:
            continue
        if row.record_id != "larimer-equity-fee-resolution-sd007-04":
            if row.record_id in GREELEY_REACQUIRED:
                assert _without_later_http(row) == _without_later_http(previous[row.record_id])
            else:
                assert _before_final_reviews(row) == previous[row.record_id]
            continue
        assert previous[row.record_id].reviews is None
        assert len(row.reviews) == 1 and row.reviews[0].review_kind == "checked_passages"
        review = row.reviews[0]
        assert review.scope_fields["/expected_physical_pages"] == 2
        assert review.scope_fields["/review_mode"] == "atlas_candidate_aware_source_qa_not_blind"
        assert review.limitations["/adopted_status_verified"] is False
        assert review.limitations["/effective_date_verified"] is None
        assert review.limitations["/adoption_date_verified"] is None
        assert review.limitations["/attachment_a_reference_observed"] is False
        assert len(review.limitations["/execution"]) == 5
        assert "20243" in json.dumps(review.limitations["/observations"])
        assert row.verified_http_acquired_at is None
        assert row.acquisition_method == "received_review_package"
        assert row.recorded_intake_status == "archived_pending_pipeline"
        assert row.legal_currentness == "not_verified" and row.answer_safe is False
        prior_fields = previous[row.record_id].model_dump()
        current_fields = row.model_dump()
        for key in ("reviews", "review_status"):
            prior_fields.pop(key)
            current_fields.pop(key)
        assert current_fields == prior_fields
    assert new.manual_manifest.path == old.manual_manifest.path
    assert new.manual_manifest.sha256 != old.manual_manifest.sha256
    assert new.unchanged_legacy_ledger == old.unchanged_legacy_ledger


def test_planning_scan_join_preserves_prior_59_sources_and_19_reviews() -> None:
    """The accepted scan review changes only one previously unknown review status."""
    root = Path(__file__).resolve().parents[1]
    checkpoint = root / "docs/audits/FOUR_HOUR_RUN_2026-09-12/EL_PASO_INTAKE/inventory-after"
    old_plan = inventory.JoinPlan.model_validate_json((checkpoint / "join-plan.json").read_bytes())
    old = inventory.Inventory.model_validate_json((checkpoint / "inventory.json").read_bytes())
    new_plan = inventory.JoinPlan.model_validate_json((root / inventory.PLAN).read_bytes())
    new = inventory.build_inventory(root)
    assert len(old.sources) == 59 and len(new.sources) == 67
    assert (old.rows_with_review, old.rows_without_review) == (19, 40)
    assert (new.rows_with_review, new.rows_without_review) == (30, 37)
    assert len(new_plan.reviews) == 30 and new_plan.reviews[:19] == old_plan.reviews
    for current, previous in zip(new_plan.authorities[:59], old_plan.authorities, strict=True):
        a, b = current.model_dump(), previous.model_dump()
        if current.record_id in GREELEY_REACQUIRED:
            a.pop("verified_http")
            b.pop("verified_http")
        assert a == b
    assert new.manual_manifest.path == old.manual_manifest.path
    assert new.manual_manifest.sha256 != old.manual_manifest.sha256
    assert new.unchanged_legacy_ledger == old.unchanged_legacy_ledger
    for previous, current in zip(old.sources, new.sources[:59], strict=True):
        assert previous.record_id == current.record_id
        if current.record_id != "el-paso-planning-fees-sd011":
            if current.record_id in GREELEY_REACQUIRED:
                assert _without_later_http(current) == _without_later_http(previous)
            else:
                assert _before_ehs_review(current) == previous
            continue
        assert previous.reviews is None
        assert len(current.reviews) == 1
        review = current.reviews[0]
        assert review.review_kind == "checked_tables"
        assert review.review_source_id == "el-paso-planning-fees-sd011"
        assert review.artifact.sha256 == (
            "77416babde5e963f47a76aee0ee7dd16e54d70fcb7019f0ffc2267971df665e6"
        )
        assert review.scope_fields["/page_coverage"] == [1, 2, 3, 4, 5]
        assert review.scope_fields["/source_fee_rows"] == 104
        assert review.scope_fields["/source_footnotes"] == 15
        assert review.scope_fields["/source_general_notes"] == 3
        assert review.limitations["/native_extraction"]["total_utf8_bytes"] == 0
        assert review.limitations["/fully_legible_complete_extraction"] is False
        assert "P3-ENG-14" in json.dumps(review.limitations["/unresolved_regions"])
        assert "manually transcribed from pixels" in review.note
        assert review.limitations["/currentness"] == "not_verified"
        assert review.limitations["/verified_adoption_date"] is None
        assert review.limitations["/verified_effective_date"] is None
        assert review.limitations["/custody/verified_http_acquisition_at"] is None
        assert review.limitations["/custody/actual_repository_received_at"] == (
            "2026-09-12T22:59:48.795762Z"
        )
        assert not review.answer_safe and not review.limitations["/answer_safe"]
        a, b = previous.model_dump(), current.model_dump()
        for key in ("reviews", "review_status"):
            a.pop(key)
            b.pop(key)
        assert a == b


@pytest.mark.parametrize("field,value", [
    ("authority_id", "CO-MUNICIPAL-COLORADO_SPRINGS"),
    ("source_id", "el-paso-boh-ehs-fees-sd011"),
    ("source_pdf", {"path": "source/original.pdf", "sha256": "0" * 64, "size_bytes": 1198750}),
    ("source_fee_rows", 105),
    ("currentness", "verified"),
])
def test_actual_planning_review_identity_scope_and_currency_tamper(
    tmp_path: Path, field: str, value: object,
) -> None:
    """Rehashed mutant review bytes cannot substitute ownership, source, scope or currency."""
    root = Path(__file__).resolve().parents[1]
    plan = inventory.JoinPlan.model_validate_json((root / inventory.PLAN).read_bytes())
    join = next(r for r in plan.reviews if r.record_id == "el-paso-planning-fees-sd011")
    saved = inventory.Inventory.model_validate_json(
        (root / inventory.PACKAGE / "inventory.json").read_bytes()
    )
    row = next(r for r in saved.sources if r.record_id == join.record_id)
    data = json.loads((root / join.review.path).read_bytes())
    data[field] = value
    for asset in [join.review, join.review_schema]:
        path = tmp_path / asset.path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((root / asset.path).read_bytes())
    (tmp_path / join.review.path).write_text(json.dumps(data), encoding="utf-8")
    mutant = join.model_copy(update={"review": inventory.identity(tmp_path, join.review.path)})
    with pytest.raises((ValueError, jsonschema.ValidationError)):
        inventory._review(tmp_path, mutant, row)


def test_springs_and_later_greeley_preserve_all_prior_review_and_custody_fields() -> None:
    """Only two new originals, one review and three later HTTP bindings extend the snapshot."""
    root = Path(__file__).resolve().parents[1]
    before = root / inventory.PACKAGE / "_SNAPSHOTS/BEFORE_SPRINGS_2026-09-13"
    old = inventory.Inventory.model_validate_json((before / "inventory.json").read_bytes())
    old_plan = inventory.JoinPlan.model_validate_json((before / "join-plan.json").read_bytes())
    new = inventory.build_inventory(root)
    plan = inventory.JoinPlan.model_validate_json((root / inventory.PLAN).read_bytes())
    assert len(old.sources) == 59 and len(new.sources) == 67
    assert (old.rows_with_review, old.rows_without_review) == (20, 39)
    assert (new.rows_with_review, new.rows_without_review) == (30, 37)
    assert plan.reviews[:20] == old_plan.reviews and len(plan.reviews) == 30
    assert new.unchanged_legacy_ledger == old.unchanged_legacy_ledger
    changed = set()
    for a, b in zip(plan.authorities[:59], old_plan.authorities, strict=True):
        if a != b:
            changed.add(a.record_id)
            first, second = a.model_dump(), b.model_dump()
            first.pop("verified_http")
            second.pop("verified_http")
            assert first == second
    assert changed == GREELEY_REACQUIRED
    for current, previous in zip(new.sources[:59], old.sources, strict=True):
        if current.record_id in GREELEY_REACQUIRED:
            assert previous.verified_http_acquired_at is None
            assert current.verified_http_acquired_at.date().isoformat() == "2026-09-12"
            assert current.verified_http_acquired_at > current.intake_received_at
            assert current.official_source_url is None
            assert current.acquisition_method == "received_review_package"
            assert _without_later_http(current) == _without_later_http(previous)
        else:
            assert _before_ehs_review(current) == previous
    old_schedule, modern = new.sources[59:61]
    assert old_schedule.record_id == "colorado-springs-code-services-fees-2015-atlas-directed"
    assert old_schedule.reviews is None
    assert old_schedule.review_status == "metadata_only_review_unknown"
    assert modern.record_id == "colorado-springs-construction-fees-atlas-directed"
    assert modern.authority_id == old_schedule.authority_id == "CO-MUNICIPAL-COLORADO_SPRINGS"
    assert modern.intake_received_at.isoformat() == "2026-09-12T23:56:16.492216+00:00"
    assert modern.verified_http_acquired_at.isoformat() == "2026-09-12T23:10:47.380038+00:00"
    assert len(modern.reviews) == 1 and modern.reviews[0].review_kind == "checked_tables"
    review = modern.reviews[0]
    assert review.review_source_id == "SD014-02"
    assert review.scope_fields["/page_count"] == 7
    assert review.scope_fields["/native_byte_count"] == 14423
    assert sum(len(t["row_ids"]) for t in review.scope_fields["/tables"]) == 128
    assert review.limitations["/adoption_verification"] == "not_verified"
    assert review.limitations["/effective_date_verification"] == "printed_claim_only"
    assert "0.04" in json.dumps(review.limitations["/source_anomalies"])
    assert all(not r.answer_safe and r.legal_currentness == "not_verified" for r in new.sources)
    assert any("later reacquisition" in s.lower() for s in new.limitations)


@pytest.mark.parametrize("field,value", [
    ("authority_id", "CO-COUNTY-EL_PASO"),
    ("source_id", "SD014-01"),
    ("source", {"path": "source/original.pdf", "sha256": "0" * 64, "size_bytes": 258393}),
    ("legal_currentness", "verified"),
])
def test_actual_springs_join_rejects_wrong_owner_source_and_currency(
    tmp_path: Path, field: str, value: object,
) -> None:
    """An amended review cannot be attached by title, wrong alias or a false currency flag."""
    root = Path(__file__).resolve().parents[1]
    plan = inventory.JoinPlan.model_validate_json((root / inventory.PLAN).read_bytes())
    source_id = "colorado-springs-construction-fees-atlas-directed"
    join = next(r for r in plan.reviews if r.record_id == source_id)
    row = next(r for r in inventory.build_inventory(root).sources if r.record_id == source_id)
    for asset in [join.review, join.review_schema]:
        target = tmp_path / asset.path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((root / asset.path).read_bytes())
    data = json.loads((tmp_path / join.review.path).read_bytes())
    data[field] = value
    (tmp_path / join.review.path).write_text(json.dumps(data), encoding="utf-8")
    mutant = join.model_copy(update={"review": inventory.identity(tmp_path, join.review.path)})
    with pytest.raises((ValueError, jsonschema.ValidationError)):
        inventory._review(tmp_path, mutant, row)


def _before_ehs_review(row: inventory.SourceRow) -> inventory.SourceRow:
    """Remove only the exact accepted EHS join for an earlier snapshot comparison."""
    row = _before_final_reviews(row)
    if row.record_id != "el-paso-boh-ehs-fees-sd011":
        return row
    assert row.reviews is not None and len(row.reviews) == 1
    review = row.reviews[0]
    assert review.review_kind == "checked_tables"
    assert review.artifact.sha256 == (
        "55a5e8b088c3b407c20691c71cb62a73491b99e39c0e6d9c0d0e69c2b3746ebf"
    )
    assert review.scope_fields["/source_fee_rows"] == 65
    assert review.limitations["/legal_currentness"] == "not_verified"
    return row.model_copy(update={"reviews": None,
                                  "review_status": "metadata_only_review_unknown"})


def test_english_ehs_join_preserves_all_61_sources_and_21_prior_reviews() -> None:
    """The exact English QA is one added review, without custody or authority changes."""
    root = Path(__file__).resolve().parents[1]
    before = root / inventory.PACKAGE / "_SNAPSHOTS/BEFORE_EL_PASO_EHS_2026-09-13"
    old = inventory.Inventory.model_validate_json((before / "inventory.json").read_bytes())
    old_plan = inventory.JoinPlan.model_validate_json((before / "join-plan.json").read_bytes())
    new = inventory.build_inventory(root)
    plan = inventory.JoinPlan.model_validate_json((root / inventory.PLAN).read_bytes())
    assert len(old.sources) == 61 and len(new.sources) == 67
    assert (old.rows_with_review, old.rows_without_review) == (21, 40)
    assert (new.rows_with_review, new.rows_without_review) == (30, 37)
    assert plan.reviews[:21] == old_plan.reviews and len(plan.reviews) == 30
    assert plan.authorities[:61] == old_plan.authorities
    assert new.manual_manifest.path == old.manual_manifest.path
    assert new.manual_manifest.sha256 != old.manual_manifest.sha256
    assert new.unchanged_legacy_ledger == old.unchanged_legacy_ledger
    for current, previous in zip(new.sources[:61], old.sources, strict=True):
        assert _before_ehs_review(current) == previous
    row = next(r for r in new.sources if r.record_id == "el-paso-boh-ehs-fees-sd011")
    review = row.reviews[0]
    assert row.authority_id == "CO-COUNTY-EL_PASO"
    assert row.verified_http_acquired_at is None
    assert review.scope_fields["/source_groups"] == 7
    assert review.scope_fields["/native_bytes_preserved"] == 8060
    assert len(review.scope_fields["/contexts"]) == 37
    assert len(review.scope_fields["/rows"]) == 65
    assert review.limitations["/translation_equivalence"] == "not_reviewed"
    assert row.answer_safe is False and row.legal_currentness == "not_verified"


def test_final_two_sources_preserve_prior_61_sources_and_22_reviews() -> None:
    """Two distinct governments add only exact custody and checked-source review mappings."""
    root = Path(__file__).resolve().parents[1]
    before = root / inventory.PACKAGE / "_SNAPSHOTS/BEFORE_FINAL_TWO_2026-09-13"
    old = inventory.Inventory.model_validate_json((before / "inventory.json").read_bytes())
    old_plan = inventory.JoinPlan.model_validate_json((before / "join-plan.json").read_bytes())
    new = inventory.build_inventory(root)
    plan = inventory.JoinPlan.model_validate_json((root / inventory.PLAN).read_bytes())
    assert len(old.sources) == 61 and len(new.sources) == 67
    assert (old.rows_with_review, old.rows_without_review) == (22, 39)
    assert (new.rows_with_review, new.rows_without_review) == (30, 37)
    assert plan.reviews[:22] == old_plan.reviews and len(plan.reviews) == 30
    assert plan.authorities[:61] == old_plan.authorities and len(plan.authorities) == 67
    assert [_before_final_reviews(r) for r in new.sources[:61]] == old.sources
    assert new.unchanged_legacy_ledger == old.unchanged_legacy_ledger
    expected = {
        "douglas-ehs-fees-atlas-directed": (
            "CO-COUNTY-DOUGLAS", "08_County_Authorities", "douglas-county-ehs-fees-dcr03",
            "35e90b9c3b73b414155ed965898c8c270757f1c367cbe50d7645956039dbb687"),
        "pueblo-planning-fees-atlas-directed": (
            "CO-MUNICIPAL-PUEBLO", "10_Municipal_Authorities", "city-pueblo-planning-fees",
            "0ba13c07bede5bf07c24dd8bbbe604c61745e8a73be773a7987e26dfa601414b"),
    }
    assert {r.record_id for r in new.sources[61:63]} == set(expected)
    for row in new.sources[61:63]:
        authority, layer, alias, sha = expected[row.record_id]
        assert row.authority_id == authority and row.layer_id == layer
        assert row.source.sha256 == sha
        assert row.reviews is not None and len(row.reviews) == 1
        review = row.reviews[0]
        assert review.review_kind == "checked_tables" and review.review_source_id == alias
        assert len(review.scope_fields["/rows"]) == 44
        assert row.verified_http_acquired_at is not None
        assert row.intake_received_at > row.verified_http_acquired_at
        assert row.answer_safe is False and row.legal_currentness == "not_verified"
        assert review.legal_currentness == "not_verified" and review.answer_safe is False
    county, city = [next(r for r in new.sources if r.record_id == key) for key in expected]
    assert county.reviews[0].scope_fields["/physical_pages"] == 1
    assert len(county.reviews[0].scope_fields["/contexts"]) == 7
    county_rows = county.reviews[0].scope_fields["/rows"]
    blank_fees = [r["row_id"] for r in county_rows
                  if any(c["field"] == "fee" and c["displayed_text"] is None for c in r["cells"])]
    assert blank_fees == ["STATE-16", "STATE-17"]
    assert sum(len(r["nested"]) for r in city.reviews[0].scope_fields["/rows"]) == 43
    assert city.reviews[0].scope_fields["/actual_page_count"] == 4
    assert city.reviews[0].scope_fields["/native_byte_count"] == 4923
    assert city.reviews[0].limitations["/repository_received_at"] is None
    assert city.reviews[0].limitations["/adoption_verified"] is False
    assert city.reviews[0].limitations["/monitoring_enrolled"] is False


@pytest.mark.parametrize("source_id,change", [
    ("douglas-ehs-fees-atlas-directed", "source_sha"),
    ("douglas-ehs-fees-atlas-directed", "alias"),
    ("douglas-ehs-fees-atlas-directed", "unlisted_schema"),
    ("pueblo-planning-fees-atlas-directed", "source_sha"),
    ("pueblo-planning-fees-atlas-directed", "alias"),
    ("pueblo-planning-fees-atlas-directed", "county_ownership"),
])
def test_final_two_review_identity_refusals(source_id: str, change: str) -> None:
    """Exact byte, alias and explicit city-owner bindings cannot be silently reassigned."""
    root = Path(__file__).resolve().parents[1]
    plan = inventory.JoinPlan.model_validate_json((root / inventory.PLAN).read_bytes())
    data = inventory.build_inventory(root)
    row = next(r for r in data.sources if r.record_id == source_id)
    join = next(r for r in plan.reviews if r.record_id == source_id)
    if change == "source_sha":
        row = row.model_copy(update={"source": row.source.model_copy(update={"sha256": "0" * 64})})
    elif change == "alias":
        join = join.model_copy(update={"expected_review_source_id": "different-review"})
    elif change == "unlisted_schema":
        join = join.model_copy(update={"review_schema": join.review_schema.model_copy(
            update={"sha256": "0" * 64})})
    else:
        row = row.model_copy(update={"authority_id": "CO-COUNTY-PUEBLO"})
    with pytest.raises(ValueError):
        inventory._review(root, join, row)


FINAL_REVIEW_IDENTITIES = {
    "larimer-equity-fee-memo-sd007-05": (
        "20f268b2f632d655d25d739002f43b67654c9ce351ca8b6a5bdebac107baa92d",
        "checked_tables"),
    "el-paso-boh-bylaws-sd011": (
        "8a3d6f2c37fbacacc104ce3fd0dba53806157858f4cb487caf44f1a511657ec6",
        "checked_passages"),
}


def _before_final_reviews(row: inventory.SourceRow) -> inventory.SourceRow:
    """Remove only identified later reviews for historical metadata equality checks."""
    row = _before_september13_reviews(row)
    if row.record_id not in FINAL_REVIEW_IDENTITIES:
        return row
    sha, kind = FINAL_REVIEW_IDENTITIES[row.record_id]
    assert row.reviews is not None and len(row.reviews) == 1
    assert row.reviews[0].artifact.sha256 == sha
    assert row.reviews[0].review_kind == kind
    assert not row.answer_safe and row.legal_currentness == "not_verified"
    return row.model_copy(update={"reviews": None,
                                  "review_status": "metadata_only_review_unknown"})


def test_final_three_preserve_63_custody_rows_and_24_old_review_joins() -> None:
    """Two old rows gain reviews; County Pueblo gains custody without becoming City Pueblo."""
    root = Path(__file__).resolve().parents[1]
    before = root / inventory.PACKAGE / "_SNAPSHOTS/BEFORE_FINAL_THREE_2026-09-13"
    old = inventory.Inventory.model_validate_json((before / "inventory.json").read_bytes())
    old_plan = inventory.JoinPlan.model_validate_json((before / "join-plan.json").read_bytes())
    new = inventory.build_inventory(root)
    plan = inventory.JoinPlan.model_validate_json((root / inventory.PLAN).read_bytes())
    assert (len(old.sources), old.rows_with_review, old.rows_without_review) == (63, 24, 39)
    assert (len(new.sources), new.rows_with_review, new.rows_without_review) == (67, 30, 37)
    assert plan.authorities[:63] == old_plan.authorities and len(plan.authorities) == 67
    assert plan.reviews[:24] == old_plan.reviews and len(plan.reviews) == 30
    assert [_before_final_reviews(r) for r in new.sources[:63]] == old.sources
    assert new.unchanged_legacy_ledger == old.unchanged_legacy_ledger
    by_id = {r.record_id: r for r in new.sources}
    county = by_id["pueblo-county-planning-fees-sh-ext-002"]
    city = by_id["pueblo-planning-fees-atlas-directed"]
    assert county.authority_id == "CO-COUNTY-PUEBLO"
    assert county.layer_id == "08_County_Authorities"
    assert city.authority_id == "CO-MUNICIPAL-PUEBLO"
    assert county.source.sha256 != city.source.sha256
    assert county.official_source_url is None
    assert county.verified_http_acquired_at is None and county.verified_http_evidence is None
    assert county.acquisition_method == "received_review_package"
    assert county.intake_received_at.isoformat() == "2026-09-13T04:55:23.097658+00:00"
    assert county.reported_acquisition["/provenance/reported_finished_at"].startswith(
        "2026-09-13T01:57:20.393")
    review = county.reviews[0]
    assert review.scope_fields["/counts"]["physical_rows"] == 88
    assert review.limitations["/adoption_date"] is None
    assert review.limitations["/effective_date"] is None
    memo = by_id["larimer-equity-fee-memo-sd007-05"].reviews[0]
    assert memo.scope_fields["/complete_physical_pages"] == 4
    assert len(memo.scope_fields["/table_rows"]) == 4
    assert len(memo.scope_fields["/table_fragments"]) == 5
    assert memo.limitations["/source_type"] == "staff_recommendation_memo"
    assert memo.limitations["/adopted_effect"] == "not_verified"
    bylaws = by_id["el-paso-boh-bylaws-sd011"].reviews[0]
    assert bylaws.scope_fields["/full_pages_directly_viewed"] == [1, 2, 3, 4, 5]
    assert bylaws.scope_fields["/native_bytes"] == 12640
    assert bylaws.scope_fields["/nonblank_lines"] == 170
    assert bylaws.limitations["/printed_date"] == "5/23/2012"
    assert bylaws.limitations["/printed_date_role"] == "unlabeled_footer_on_all_five_pages"
    assert bylaws.limitations["/adoption_date"] is None
    assert bylaws.limitations["/effective_date"] is None
    assert all(not r.answer_safe and r.legal_currentness == "not_verified" for r in new.sources)


@pytest.mark.parametrize("source_id", [
    "pueblo-county-planning-fees-sh-ext-002",
    "larimer-equity-fee-memo-sd007-05", "el-paso-boh-bylaws-sd011",
])
@pytest.mark.parametrize("mutation", ["source_sha", "authority", "alias", "schema"])
def test_final_three_reject_wrong_hash_owner_alias_and_schema(
    source_id: str, mutation: str,
) -> None:
    """No new review joins by filename, other owner, substituted source, or unknown schema."""
    root = Path(__file__).resolve().parents[1]
    plan = inventory.JoinPlan.model_validate_json((root / inventory.PLAN).read_bytes())
    row = next(r for r in inventory.build_inventory(root).sources if r.record_id == source_id)
    join = next(r for r in plan.reviews if r.record_id == source_id)
    if mutation == "source_sha":
        row = row.model_copy(update={"source": row.source.model_copy(update={"sha256": "0"*64})})
    elif mutation == "authority":
        row = row.model_copy(update={"authority_id": "CO-MUNICIPAL-PUEBLO"})
    elif mutation == "alias":
        join = join.model_copy(update={"expected_review_source_id": "unrelated-source"})
    else:
        join = join.model_copy(update={"review_schema": join.review_schema.model_copy(
            update={"sha256": "0"*64})})
    with pytest.raises(ValueError):
        inventory._review(root, join, row)


SEPTEMBER13_REVIEW_IDENTITIES = {
    "el-paso-boh-ehs-fees-spanish-sd011": (
        "2372e6bde1fa544c56dbaed1a808a7389bf943006f8d2d4c65dd5fa10a8ad46f",
        "checked_tables"),
    "el-paso-boh-bylaws-spanish-sd011": (
        "fff90226a2dd0c213b551f7f1345bfd87f1eabfd55107243a6c60c30e708a556",
        "checked_passages"),
}
GUNNISON_SEPTEMBER13 = (
    "gunnison-building-fees-resolution-2025-24-sh-ext-003",
    "gunnison-building-code-resolution-2023-22-sh-ext-003",
    "gunnison-iwuic-resolution-2022-33-sh-ext-003",
)


def _before_september13_reviews(row: inventory.SourceRow) -> inventory.SourceRow:
    """Remove only the two exact newly accepted Spanish joins for historical comparisons."""
    if row.record_id not in SEPTEMBER13_REVIEW_IDENTITIES:
        return row
    digest, kind = SEPTEMBER13_REVIEW_IDENTITIES[row.record_id]
    assert row.reviews is not None and len(row.reviews) == 1
    assert row.reviews[0].artifact.sha256 == digest and row.reviews[0].review_kind == kind
    assert row.legal_currentness == "not_verified" and not row.answer_safe
    return row.model_copy(update={"reviews": None,
                                  "review_status": "metadata_only_review_unknown"})


def test_gunnison_and_spanish_joins_preserve_exact_64_source_baseline() -> None:
    """Three new originals and two old-source reviews preserve every older custody field."""
    root = Path(__file__).resolve().parents[1]
    before = root / inventory.PACKAGE / "_SNAPSHOTS/BEFORE_GUNNISON_SPANISH_2026-09-13"
    old = inventory.Inventory.model_validate_json((before / "inventory.json").read_bytes())
    old_plan = inventory.JoinPlan.model_validate_json((before / "join-plan.json").read_bytes())
    current = inventory.build_inventory(root)
    plan = inventory.JoinPlan.model_validate_json((root / inventory.PLAN).read_bytes())
    assert (len(old.sources), old.rows_with_review, old.rows_without_review) == (64, 27, 37)
    assert (len(current.sources), current.rows_with_review, current.rows_without_review) == (
        67, 30, 37,
    )
    assert plan.authorities[:64] == old_plan.authorities and len(plan.authorities) == 67
    assert plan.reviews[:27] == old_plan.reviews and len(plan.reviews) == 30
    assert [_before_september13_reviews(r) for r in current.sources[:64]] == old.sources
    assert current.unchanged_legacy_ledger == old.unchanged_legacy_ledger
    assert tuple(r.record_id for r in current.sources[64:]) == GUNNISON_SEPTEMBER13
    for row in current.sources[64:]:
        assert row.authority_id == "CO-COUNTY-GUNNISON"
        assert row.layer_id == "08_County_Authorities"
        assert row.acquisition_method == "received_review_package"
        assert row.official_source_url is None
        assert row.verified_http_acquired_at is None and row.verified_http_evidence is None
        assert row.intake_received_at.isoformat() == "2026-09-13T15:57:35.577123+00:00"
        assert row.recorded_intake_status == "archived_pending_pipeline"
        assert row.provenance_qualifications[next(
            k for k in row.provenance_qualifications if k.endswith("verified_original_acquired_at")
        )] is None
        reported = next(v for k, v in row.reported_acquisition.items()
                        if k.endswith("reported_finished_at"))
        assert reported.startswith("2026-09-13T02:18:")
        assert row.authority_evidence.artifact.path.endswith(
            "gunnison-county-intake-2026-09-13/prepared-transaction/PREPARATION.json")
        assert not row.answer_safe and row.legal_currentness == "not_verified"
    assert current.sources[65].reviews is None and current.sources[66].reviews is None
    fee = current.sources[64].reviews[0]
    assert fee.review_kind == "checked_passages"
    assert len(fee.scope_fields["/pages"]) == 3
    assert len(fee.scope_fields["/blocks"]) == 34 and len(fee.scope_fields["/fees"]) == 12
    for page in fee.scope_fields["/pages"]:
        assert page["native"]["size_bytes"] == 0 and page["native_spans"] == []
        assert page["native_status"] == "empty_image_only"
        assert page["ocr_observation_spans"]
    assert "not twelve physical table rows" in " ".join(fee.limitations["/limitations"])
    assert fee.limitations["/official_acquisition_at_verified"] is None
    assert fee.limitations["/source_bytes_intake_status_at_review"] == (
        "received_package_canonical_intake_not_asserted")


def test_spanish_review_scope_keeps_footer_and_translation_limits() -> None:
    """Language-specific accepted source QA never substitutes English or a certified date."""
    root = Path(__file__).resolve().parents[1]
    data = inventory.build_inventory(root)
    by_id = {row.record_id: row for row in data.sources}
    fees = by_id["el-paso-boh-ehs-fees-spanish-sd011"].reviews[0]
    assert fees.review_kind == "checked_tables"
    assert fees.scope_fields["/full_pages_directly_viewed"] == [1, 2, 3, 4, 5, 6]
    assert fees.scope_fields["/physical_table_rows"] == 75
    assert fees.scope_fields["/fee_rows"] == 65 and fees.scope_fields["/native_bytes"] == 10216
    assert len(fees.scope_fields["/links"]) == 11 and len(fees.scope_fields["/passages"]) == 27
    assert len(fees.limitations["/footer_evidence"]) == 6
    assert all(f["visually_certified_year"] is None for f in fees.limitations["/footer_evidence"])
    assert fees.limitations["/translation_equivalence_verified"] is False
    assert fees.limitations["/external_reports_consulted"] is False
    bylaws = by_id["el-paso-boh-bylaws-spanish-sd011"].reviews[0]
    assert bylaws.review_kind == "checked_passages"
    scope = bylaws.scope_fields["/fullscope"]
    assert scope["native_utf8_bytes"] == 13558 and scope["native_lines"] == 180
    assert scope["full_physical_pages"] == [1, 2, 3, 4, 5, 6]
    assert scope["translation_equivalence_assessed"] is False
    assert scope["english_versions_consulted"] is False
    assert scope["external_reports_consulted"] is False
    assert all(bylaws.limitations[k] is None for k in [
        "/issue_date", "/adoption_date", "/effective_date", "/independently_verified_http_at",
    ])
    assert len(bylaws.scope_fields["/pages"]) == 6
    assert sum(len(p["segments"]) for p in bylaws.scope_fields["/pages"]) == 51
    assert all(not r.answer_safe and r.legal_currentness == "not_verified" for r in data.sources)


@pytest.mark.parametrize("source_id", [
    *SEPTEMBER13_REVIEW_IDENTITIES, GUNNISON_SEPTEMBER13[0],
])
@pytest.mark.parametrize("mutation", ["source_sha", "authority", "alias", "schema"])
def test_september13_reviews_reject_reassigned_identity(
    source_id: str, mutation: str,
) -> None:
    """Each newly accepted review remains bound to exact source, government and schema."""
    root = Path(__file__).resolve().parents[1]
    plan = inventory.JoinPlan.model_validate_json((root / inventory.PLAN).read_bytes())
    data = inventory.Inventory.model_validate_json(
        (root / inventory.PACKAGE / "inventory.json").read_bytes())
    row = next(r for r in data.sources if r.record_id == source_id)
    join = next(r for r in plan.reviews if r.record_id == source_id)
    if mutation == "source_sha":
        row = row.model_copy(update={"source": row.source.model_copy(update={"sha256": "0" * 64})})
    elif mutation == "authority":
        row = row.model_copy(update={"authority_id": "CO-MUNICIPAL-GUNNISON"})
    elif mutation == "alias":
        join = join.model_copy(update={"expected_review_source_id": "el-paso-boh-bylaws-sd011"})
    else:
        join = join.model_copy(update={"review_schema": join.review_schema.model_copy(
            update={"sha256": "0" * 64})})
    with pytest.raises(ValueError):
        inventory._review(root, join, row)


@pytest.mark.parametrize("source_id,mutation", [
    ("el-paso-boh-ehs-fees-spanish-sd011", "footer_year"),
    ("el-paso-boh-ehs-fees-spanish-sd011", "translation"),
    ("el-paso-boh-ehs-fees-spanish-sd011", "currentness"),
    ("el-paso-boh-bylaws-spanish-sd011", "adoption"),
    ("el-paso-boh-bylaws-spanish-sd011", "translation"),
    (GUNNISON_SEPTEMBER13[0], "currentness"),
])
def test_september13_reviews_reject_rehashed_status_promotions(
    tmp_path: Path, source_id: str, mutation: str,
) -> None:
    """Rehashed records cannot promote uncertain years, equivalence, adoption or currency."""
    root = Path(__file__).resolve().parents[1]
    plan = inventory.JoinPlan.model_validate_json((root / inventory.PLAN).read_bytes())
    data = inventory.Inventory.model_validate_json(
        (root / inventory.PACKAGE / "inventory.json").read_bytes())
    row = next(r for r in data.sources if r.record_id == source_id)
    join = next(r for r in plan.reviews if r.record_id == source_id)
    for item in [join.review, join.review_schema]:
        path = tmp_path / item.path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((root / item.path).read_bytes())
    mutated = json.loads((tmp_path / join.review.path).read_bytes())
    if mutation == "footer_year":
        mutated["footer_evidence"][0]["visually_certified_year"] = 2023
    elif mutation == "translation":
        if "fullscope" in mutated:
            mutated["fullscope"]["translation_equivalence_assessed"] = True
        else:
            mutated["translation_equivalence_verified"] = True
    elif mutation == "adoption":
        mutated["adoption_date"] = "2026-09-13"
    else:
        mutated["legal_currentness"] = "verified"
    save(tmp_path / join.review.path, mutated)
    altered = join.model_copy(update={"review": inventory.identity(tmp_path, join.review.path)})
    with pytest.raises((ValueError, jsonschema.ValidationError)):
        inventory._review(tmp_path, altered, row)
