"""Offline authority coverage must retain missing work and exact source provenance."""

from __future__ import annotations

import copy
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pymupdf
import pytest
from pydantic import ValidationError

from geode.pipeline import local_coverage as coverage

GOLDEN = "CO-MUNICIPAL-GOLDEN"
GEORGETOWN = "CO-MUNICIPAL-GEORGETOWN"
NOW = datetime.now(timezone.utc).isoformat()


def preserve(
    root: Path, source_id: str, body: bytes, media: str, *,
    owner: str | None = GOLDEN, kind: str = "guidance", category: str = "building_fire",
    url: str = "https://www.cityofgolden.gov/source", **extra: object,
) -> dict:
    """Create a source whose metadata matches actual local bytes."""
    digest = hashlib.sha256(body).hexdigest()
    relative = f"_RAW_ARCHIVE/local/coverage/{digest}.{media}"
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)
    return dict(
        source_id=source_id, authority_id=owner, title=source_id, url=url, final_url=url,
        retrieved_at=NOW, archive_path=relative, sha256=digest, size_bytes=len(body),
        media_type=media, kind=kind, categories=[category],
        provenance_notes="Preserved fixture original", currentness_notes="Not reconciled",
        **extra,
    )


def pdf_bytes() -> bytes:
    """Create a real, structurally valid one-page source PDF."""
    with pymupdf.open() as document:
        document.new_page().insert_text((72, 72), "Adoption resolution fixture")
        return document.tobytes()


def payload(sources: list[dict]) -> dict:
    """Build explicit missing or partial checklist rows for two independent authorities."""
    authorities = []
    directory_ids = [s["source_id"] for s in sources if s["kind"] == "directory"]
    for identity, name in ((GOLDEN, "Golden"), (GEORGETOWN, "Georgetown")):
        rows = []
        for category in coverage.CATEGORIES:
            matching = [s for s in sources if s["authority_id"] == identity
                        and category in s["categories"]]
            legal = any(s["kind"] in {"legal_text", "fee_schedule"} for s in matching)
            rows.append(dict(
                category=category, source_ids=[s["source_id"] for s in matching],
                collection=("legal_documents_preserved" if legal else
                            "supporting_evidence_only" if matching else "missing"),
                completeness="partial" if matching else "not_assessed",
                gap="Later amendments | effective dates remain unknown",
                next_action="Reconcile official sources\nwith adoption instruments",
            ))
        authorities.append(dict(
            authority_id=identity, name=name, level="municipal", pilot=identity == GOLDEN,
            identity_basis="Directory candidate; active status not established",
            identity_source_ids=directory_ids, checklist=rows,
        ))
    assessments = [dict(level="municipal", reference_count=2, source_ids=directory_ids,
                        source_as_of="Dated source population", findings=["Unreconciled roster"])]
    return dict(
        prepared_at=NOW, baseline_commit="a" * 40, scope="Two fixture authorities only",
        directory_assessments=assessments if directory_ids else [], sources=sources,
        authorities=authorities, limitations=["Legal currency and completeness unverified"],
    )


@pytest.fixture
def sample(tmp_path: Path) -> tuple[Path, dict]:
    """Seed actual directory, catalog, and legal-document evidence without network."""
    sources = [
        preserve(tmp_path, "directory", b"name|state\nGolden|CO\n", "txt", owner=None,
                 kind="directory", category="identity_service_area",
                 url="https://www2.census.gov/directory.txt"),
        preserve(tmp_path, "catalog", b"<html><body>Official code links</body></html>", "html",
                 kind="catalog", category="codified_rules"),
        preserve(tmp_path, "adoption", pdf_bytes(), "pdf", kind="legal_text"),
    ]
    return tmp_path, payload(sources)


def validated(data: dict) -> coverage.CoverageLedger:
    """Validate a fixture through the same complete schema used by the CLI."""
    return coverage.CoverageLedger.model_validate(data)


def test_valid_evidence_report_and_assignment_guards(sample: tuple[Path, dict]) -> None:
    root, data = sample
    ledger = validated(data)
    coverage.validate_ledger_evidence(ledger, root)
    report = coverage.render_ledger_report(ledger)
    assert "Legally current categories: 0" in report
    assert "## Golden" in report and "## Georgetown" not in report
    assert "\\| effective dates" in report and "reference count 2" in report
    with pytest.raises(ValidationError):
        ledger.sources[0].legal_currentness = "verified_current"


@pytest.mark.parametrize("target,field,value", [
    ("source", "legal_currentness", "current"), ("source", "legal_review", "approved"),
    ("row", "currentness", "current"), ("row", "completeness", "complete"),
    ("row", "legal_review", "approved"), ("row", "collection", "complete"),
    ("authority", "active_government", "verified"),
    ("directory", "current_universe_verified", True),
])
def test_fully_current_or_complete_states_do_not_exist(
    sample: tuple[Path, dict], target: str, field: str, value: object,
) -> None:
    _, data = sample
    objects = {"source": data["sources"][0], "authority": data["authorities"][0],
               "row": data["authorities"][0]["checklist"][0],
               "directory": data["directory_assessments"][0]}
    objects[target][field] = value
    with pytest.raises(ValidationError):
        validated(data)


@pytest.mark.parametrize("field,value", [
    ("url", "http://www.cityofgolden.gov/source"),
    ("url", "https://user:secret@www.cityofgolden.gov/source"),
    ("url", "https://www.cityofgolden.gov:444/source"),
    ("url", "https://www.cityofgolden.gov:bad/source"),
    ("url", "https://www.cityofgolden.gov/%2e%2e/source"),
    ("url", "https://www.cityofgolden.gov/\nsource"),
    ("url", "https://www.townofgeorgetown.us/source"),
    ("final_url", "https://library.municode.com/co/goldenevil/codes"),
    ("final_url", "https://library.municode.com/co/golden/codes/municipal_code"),
    ("archive_path", "_RAW_ARCHIVE/local/coverage/" + "0" * 64 + ".html"),
    ("sha256", "0" * 64), ("categories", ["building_fire", "building_fire"]),
    ("categories", ["invented_subject"]), ("title", " "),
    ("retrieved_at", "2026-09-10T12:00:00"), ("size_bytes", True),
    ("size_bytes", 0), ("size_bytes", coverage.MAX_SOURCE_BYTES + 1),
    ("invented_property", "unapproved"),
])
def test_source_contract_rejects_wrong_urls_metadata_and_claims(
    sample: tuple[Path, dict], field: str, value: object,
) -> None:
    _, data = sample
    data["sources"][1][field] = value
    with pytest.raises(ValidationError):
        validated(data)


@pytest.mark.parametrize("change", ["missing", "duplicate", "level", "id", "naive"])
def test_authority_checklist_identity_and_preparation_requirements(
    sample: tuple[Path, dict], change: str,
) -> None:
    _, data = sample
    authority = data["authorities"][0]
    if change == "missing":
        authority["checklist"].pop()
    elif change == "duplicate":
        authority["checklist"][-1] = authority["checklist"][0]
    elif change == "level":
        authority["level"] = "county"
    elif change == "id":
        authority["authority_id"] = "GOLDEN"
    else:
        data["prepared_at"] = "2026-09-10"
    with pytest.raises(ValidationError):
        validated(data)


@pytest.mark.parametrize("change", [
    "duplicate_source", "duplicate_authority", "unknown_owner", "unknown_parent", "self_parent",
    "foreign_parent", "cycle", "directory_kind", "identity_kind", "duplicate_reference",
    "foreign_category", "wrong_category", "unknown_reference", "inflated_catalog",
    "unacknowledged_partial", "orphan", "statewide_nondirectory",
])
def test_ledger_references_and_evidence_classifications_are_enforced(
    sample: tuple[Path, dict], change: str,
) -> None:
    root, data = sample
    sources = data["sources"]
    rows = {r["category"]: r for r in data["authorities"][0]["checklist"]}
    if change == "duplicate_source":
        sources.append(copy.deepcopy(sources[1]))
    elif change == "duplicate_authority":
        data["authorities"].append(copy.deepcopy(data["authorities"][0]))
    elif change == "unknown_owner":
        sources[1]["authority_id"] = "CO-MUNICIPAL-UNKNOWN"
        sources[1]["url"] = sources[1]["final_url"] = "https://unknown.example/source"
    elif change in {"unknown_parent", "self_parent", "foreign_parent"}:
        sources[1]["linked_from_source_id"] = {
            "unknown_parent": "absent", "self_parent": "catalog", "foreign_parent": "directory",
        }[change]
    elif change == "cycle":
        sources[1]["linked_from_source_id"] = "adoption"
        sources[2]["linked_from_source_id"] = "catalog"
    elif change == "directory_kind":
        data["directory_assessments"][0]["source_ids"] = ["catalog"]
    elif change == "identity_kind":
        data["authorities"][0]["identity_source_ids"] = ["catalog"]
    elif change == "duplicate_reference":
        rows["codified_rules"]["source_ids"] = ["catalog", "catalog"]
    elif change == "foreign_category":
        data["authorities"][1]["checklist"] = copy.deepcopy(data["authorities"][0]["checklist"])
    elif change == "wrong_category":
        rows["fees"]["source_ids"] = ["catalog"]
    elif change == "unknown_reference":
        rows["fees"]["source_ids"] = ["absent"]
    elif change == "inflated_catalog":
        rows["codified_rules"]["collection"] = "legal_documents_preserved"
    elif change == "unacknowledged_partial":
        rows["codified_rules"]["completeness"] = "not_assessed"
    elif change == "orphan":
        sources.append(preserve(root, "orphan", b"<html>Unreferenced</html>", "html"))
    else:
        sources[0]["kind"] = "guidance"
    with pytest.raises(ValidationError):
        validated(data)


@pytest.mark.parametrize("change", ["missing", "hash", "size", "file_link", "directory_link"])
def test_actual_missing_changed_or_symlinked_bytes_fail(
    sample: tuple[Path, dict], change: str,
) -> None:
    root, data = sample
    source = data["sources"][2]
    path = root / source["archive_path"]
    if change == "missing":
        path.unlink()
    elif change == "hash":
        body = path.read_bytes()
        path.write_bytes(body[:-1] + b"X")
    elif change == "size":
        source["size_bytes"] += 1
    elif change == "file_link":
        target = path.with_suffix(".saved")
        path.rename(target)
        path.symlink_to(target)
    else:
        directory = path.parent
        moved = directory.with_name("real-coverage")
        directory.rename(moved)
        directory.symlink_to(moved, target_is_directory=True)
    with pytest.raises(ValueError):
        coverage.validate_ledger_evidence(validated(data), root)


@pytest.mark.parametrize("ancestor", [False, True])
def test_root_or_root_ancestor_symlink_is_rejected(
    sample: tuple[Path, dict], tmp_path_factory: pytest.TempPathFactory, ancestor: bool,
) -> None:
    root, data = sample
    link = tmp_path_factory.mktemp("alias") / "linked"
    link.symlink_to(root.parent if ancestor else root, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        coverage.validate_ledger_evidence(validated(data), link / root.name if ancestor else link)


@pytest.mark.parametrize("media,body", [
    ("pdf", b"%PDF-1.7\n"), ("pdf", b"%PDF-1.7\ninvalid\n%%EOF"),
    ("html", b"<html>No closing tag"), ("html", b"Not HTML</html>"),
    ("html", b"<html><title>Access Denied</title></html>"),
    ("html", b"<html><script>_cf_chl_opt</script></html>"),
    ("txt", b"version https://git-lfs.github.com/spec/v1\noid sha256:abc\nsize 15\n"),
    ("txt", b"name|state"), ("json", b"not JSON"), ("txt", b"\xff"),
])
def test_matching_hash_cannot_make_invalid_formats_valid(
    tmp_path: Path, media: str, body: bytes,
) -> None:
    directory = media in {"txt", "json"}
    source = preserve(tmp_path, "bad-source", body, media,
                      owner=None if directory else GOLDEN,
                      kind="directory" if directory else "legal_text",
                      url="https://www2.census.gov/table" if directory else
                          "https://www.cityofgolden.gov/source")
    with pytest.raises(ValueError):
        coverage.validate_ledger_evidence(validated(payload([source])), tmp_path)


def test_valid_json_directory_fee_schedule_and_unresolved_count(tmp_path: Path) -> None:
    sources = [preserve(tmp_path, "directory", b'{"name":"Golden"}', "json", owner=None,
                        kind="directory", category="identity_service_area",
                        url="https://data.colorado.gov/directory"),
               preserve(tmp_path, "fees", pdf_bytes(), "pdf", kind="fee_schedule",
                        category="fees")]
    data = payload(sources)
    data["directory_assessments"][0]["reference_count"] = None
    ledger = validated(data)
    coverage.validate_ledger_evidence(ledger, tmp_path)
    assert "reference count unresolved" in coverage.render_ledger_report(ledger)


@pytest.mark.parametrize("has_text,status,pages,valid", [
    (True, "text_layer_present", 1, True), (False, "ocr_required", 1, True),
    (True, "ocr_required", 1, False), (False, "text_layer_present", 1, False),
    (True, "text_layer_present", 2, False),
])
def test_pdf_page_count_and_extraction_status_are_checked_against_bytes(
    tmp_path: Path, has_text: bool, status: str, pages: int, valid: bool,
) -> None:
    with pymupdf.open() as document:
        page = document.new_page()
        if has_text:
            page.insert_text((72, 72), "Source page text")
        body = document.tobytes()
    source = preserve(tmp_path, "adoption", body, "pdf", kind="legal_text",
                      extraction_status=status, pdf_pages=pages)
    ledger = validated(payload([source]))
    if valid:
        coverage.validate_ledger_evidence(ledger, tmp_path)
    else:
        with pytest.raises(ValueError, match="Invalid PDF"):
            coverage.validate_ledger_evidence(ledger, tmp_path)


@pytest.mark.parametrize("metadata", [{"pdf_pages": 1}, {"extraction_status": "ocr_required"}])
def test_non_pdf_evidence_cannot_claim_pdf_extraction_metadata(
    sample: tuple[Path, dict], metadata: dict,
) -> None:
    _, data = sample
    data["sources"][1].update(metadata)
    with pytest.raises(ValidationError, match="PDF"):
        validated(data)


def test_valid_authority_source_requires_owner_in_roster(sample: tuple[Path, dict]) -> None:
    _, data = sample
    data["authorities"].pop(0)
    with pytest.raises(ValidationError, match="roster"):
        validated(data)


def delegated_payload(root: Path, *, base: bool = True, kind: str = "catalog") -> dict:
    """Build delegated evidence whose exact link uses a preserved HTML base URL."""
    url = "https://library.municode.com/co/golden/codes/municipal_code"
    html = (b'<html><base href="https://library.municode.com/co/golden/">'
            b'<a href="codes/municipal_code">Code</a></html>') if base else (
                b'<html><a href="' + url.encode() + b'">Code</a></html>')
    parent = preserve(root, "parent", html, "html", kind="catalog", category="codified_rules")
    source = preserve(root, "delegated", b"<html>Application shell</html>", "html", kind=kind,
                      category="codified_rules", url=url, linked_from_source_id="parent")
    return payload([parent, source])


@pytest.mark.parametrize("base", [False, True])
def test_delegation_uses_exact_anchor_and_html_base(tmp_path: Path, base: bool) -> None:
    coverage.validate_ledger_evidence(validated(delegated_payload(tmp_path, base=base)), tmp_path)


@pytest.mark.parametrize("change", ["absent", "pdf_parent", "shell_legal", "foreign_prefix"])
def test_delegated_provenance_and_app_shell_cannot_be_promoted(
    tmp_path: Path, change: str,
) -> None:
    data = delegated_payload(tmp_path, kind="legal_text" if change == "shell_legal" else "catalog")
    if change == "absent":
        data["sources"][1]["url"] += "_missing"
    elif change == "pdf_parent":
        data["sources"][0] = preserve(tmp_path, "parent", pdf_bytes(), "pdf", kind="catalog",
                                      category="codified_rules")
    elif change == "foreign_prefix":
        data["sources"][1]["url"] = "https://library.municode.com/co/georgetown/codes"
    with pytest.raises(ValueError):
        coverage.validate_ledger_evidence(validated(data), tmp_path)


def test_district_provider_legacy_id_is_classified_explicitly(sample: tuple[Path, dict]) -> None:
    _, data = sample
    authority = copy.deepcopy(data["authorities"][1])
    authority.update(authority_id="CO-DISTRICT-DENVER_WATER", name="Denver Water",
                     level="public_provider")
    data["authorities"].append(authority)
    assert validated(data).authorities[-1].level == "public_provider"


def test_cli_validates_then_snapshots_reports_and_rejects_escape(
    sample: tuple[Path, dict], tmp_path_factory: pytest.TempPathFactory,
) -> None:
    root, data = sample
    path = root / "ledger.json"
    path.write_text(json.dumps(data))
    args = ["--ledger", str(path), "--root", str(root)]
    assert coverage.main(args) == 0
    assert coverage.main([*args, "--output-dir", "reports"]) == 0
    report = root / "reports/local-coverage.json"
    before = report.read_bytes()
    assert coverage.main([*args, "--output-dir", "reports"]) == 0
    snapshots = list((root / "_SNAPSHOTS").rglob("local-coverage.json"))
    assert len(snapshots) == 1 and snapshots[0].read_bytes() == before
    outside = tmp_path_factory.mktemp("outside")
    assert coverage.main([*args, "--output-dir", str(outside)]) == 1
    assert not list(outside.iterdir())
    assert coverage.main([*args, "--output-dir", "_RAW_ARCHIVE/reports"]) == 1
    path.write_text("not json")
    assert coverage.main(args) == 1


def test_cli_refuses_oversize_or_missing_input(tmp_path: Path) -> None:
    path = tmp_path / "large.json"
    path.write_bytes(b" " * (coverage.MAX_LEDGER_BYTES + 1))
    assert coverage.main(["--ledger", str(path), "--root", str(tmp_path)]) == 1
    path.unlink()
    assert coverage.main(["--ledger", str(path), "--root", str(tmp_path)]) == 1
