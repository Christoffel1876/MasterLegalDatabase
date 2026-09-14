"""Bind ledger publisher exceptions to complete offline proof and exact official referrals."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import quote

import pytest

from geode.pipeline import local_coverage as coverage
from geode.pipeline import municipal_code_export as exports
from tests.test_municipal_code_export import _fixture

MANIFEST = "_CONTROL_PLANE/MUNICIPAL_EXPORTS_2026-09-10.json"
GOLDEN = "CO-MUNICIPAL-GOLDEN"
GEORGETOWN = "CO-MUNICIPAL-GEORGETOWN"


def ledger_from_sources(sources: list[dict]) -> coverage.CoverageLedger:
    """Build every authority/category row so tests pass through real referential validation."""
    authorities = []
    for identity, name in ((GOLDEN, "Golden"), (GEORGETOWN, "Georgetown")):
        rows = []
        for category in coverage.CATEGORIES:
            matching = [source for source in sources if source["authority_id"] == identity
                        and category in source["categories"]]
            legal = any(source["kind"] == "legal_text" for source in matching)
            rows.append(dict(
                category=category, source_ids=[source["source_id"] for source in matching],
                collection="legal_documents_preserved" if legal else
                "supporting_evidence_only" if matching else "missing",
                completeness="partial" if matching else "not_assessed",
                gap="Later law remains unresolved", next_action="Review later adoptions",
            ))
        authorities.append(dict(authority_id=identity, name=name, level="municipal",
                                identity_basis="Fixture identity", checklist=rows))
    return coverage.CoverageLedger.model_validate(dict(
        prepared_at="2026-09-10T12:00:00Z", baseline_commit="a" * 40,
        scope="Fixture official referrals and publisher exports only",
        sources=sources, authorities=authorities, directory_assessments=[],
        limitations=["Publisher edition does not establish legally current coverage"],
    ))


@pytest.fixture
def bundle(tmp_path: Path) -> SimpleNamespace:
    """Reuse the real Golden PDF and Georgetown node proof fixture, never a permissive mock."""
    manifest = _fixture(tmp_path)
    payload = manifest.model_dump(mode="json")
    raw_root = tmp_path / "_RAW_ARCHIVE/local/coverage"
    raw_root.mkdir(parents=True)
    for source in payload["sources"]:
        if source["source_id"] not in {
            "goldenofficial", "georgetownofficial", "goldencontent", "georgetowncontent"
        }:
            continue
        body = (tmp_path / source["archive_path"]).read_bytes()
        destination = raw_root / f"{source['sha256']}.{source['media_type']}"
        destination.write_bytes(body)
        source["archive_path"] = destination.relative_to(tmp_path).as_posix()
    manifest = exports.MunicipalExportManifest.model_validate(payload)
    path = tmp_path / MANIFEST
    path.parent.mkdir()
    path.write_text(manifest.model_dump_json())
    refs = {source.source_id: source for source in manifest.sources}
    sources = []
    for item in manifest.exports:
        for key, kind in ((item.official_referral, "catalog"), (item.content, "legal_text")):
            source = refs[key]
            sources.append(dict(
                source_id=key, authority_id=item.authority_id, title=key,
                url=source.url, final_url=source.url, retrieved_at=source.retrieved_at,
                archive_path=source.archive_path, sha256=source.sha256,
                size_bytes=source.size_bytes, media_type=source.media_type, kind=kind,
                categories=["codified_rules"], provenance_notes="Actual fixture publisher chain",
                currentness_notes="Unknown later amendments",
                linked_from_source_id=item.official_referral if kind == "legal_text" else None,
                publisher_export_manifest=MANIFEST if kind == "legal_text" else None,
                pdf_pages=1 if source.media_type == "pdf" else None,
            ))
    ledger = ledger_from_sources(sources)
    return SimpleNamespace(root=tmp_path, manifest=manifest, path=path, ledger=ledger)


def source_payload(bundle: SimpleNamespace, source_id: str) -> dict:
    """Copy one independently validated ledger source for deliberate negative mutations."""
    return next(source.model_dump() for source in bundle.ledger.sources
                if source.source_id == source_id)


def replace_source(bundle: SimpleNamespace, source: dict, old_id: str | None = None) -> None:
    """Regenerate checklist identities after replacing a source record."""
    rows = [item.model_dump() for item in bundle.ledger.sources]
    index = next(i for i, item in enumerate(rows)
                 if item["source_id"] == (old_id or source["source_id"]))
    rows[index] = source
    bundle.ledger = ledger_from_sources(rows)


def test_real_export_proof_is_required_and_cached_once(
    bundle: SimpleNamespace, monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = []
    actual = exports.validate_municipal_exports

    def counting(manifest: exports.MunicipalExportManifest, root: Path) -> object:
        calls.append(root)
        return actual(manifest, root)

    monkeypatch.setattr(exports, "validate_municipal_exports", counting)
    coverage.validate_ledger_evidence(bundle.ledger, bundle.root)
    assert calls == [bundle.root]
    assert all(source.legal_currentness == "not_verified" for source in bundle.ledger.sources)


@pytest.mark.parametrize("case", ["missing", "symlink", "ancestor_symlink", "oversized"])
def test_manifest_missing_or_unsafe_cannot_enable_export_endpoint(
    bundle: SimpleNamespace, monkeypatch: pytest.MonkeyPatch, case: str,
) -> None:
    if case == "missing":
        bundle.path.unlink()
    elif case == "symlink":
        target = bundle.root / "other-proof.json"
        bundle.path.rename(target)
        bundle.path.symlink_to(target)
    elif case == "ancestor_symlink":
        parent = bundle.path.parent
        destination = bundle.root / "other-control-plane"
        parent.rename(destination)
        parent.symlink_to(destination, target_is_directory=True)
    else:
        monkeypatch.setattr(coverage, "MAX_LEDGER_BYTES", 100)
    with pytest.raises((ValueError, OSError)):
        coverage.validate_ledger_evidence(bundle.ledger, bundle.root)


@pytest.mark.parametrize("source_id", ["goldencontent", "georgetowncontent"])
def test_export_endpoint_without_proof_has_no_general_allowlist(
    bundle: SimpleNamespace, source_id: str,
) -> None:
    value = source_payload(bundle, source_id)
    value["publisher_export_manifest"] = None
    with pytest.raises(ValueError, match="outside reviewed"):
        coverage.EvidenceSource.model_validate(value)


@pytest.mark.parametrize("source_id,field,value", [
    ("goldencontent", "kind", "guidance"),
    ("goldencontent", "linked_from_source_id", None),
    ("goldencontent", "url", "https://www.cityofgolden.gov/other"),
    ("goldencontent", "final_url", "https://www.cityofgolden.gov/other"),
    ("goldencontent", "authority_id", GEORGETOWN),
    ("georgetowncontent", "authority_id", GOLDEN),
    ("goldencontent", "publisher_export_manifest", "../proof.json"),
    ("georgetowncontent", "publisher_export_manifest", "_CONTROL_PLANE/arbitrary.json"),
])
def test_scoped_source_contract_rejects_role_or_authority_escape(
    bundle: SimpleNamespace, source_id: str, field: str, value: object,
) -> None:
    source = source_payload(bundle, source_id)
    source[field] = value
    with pytest.raises(ValueError):
        coverage.EvidenceSource.model_validate(source)


@pytest.mark.parametrize("source_id,url", [
    ("goldencontent", exports.STORAGE + "/publication-official-copy-pdfs/4206/Final.pdf"),
    ("goldencontent", exports.STORAGE + "/publication-official-copy-pdfs/768/Final.pdf?x=1"),
    ("goldencontent", exports.STORAGE + "/publication-official-copy-pdfs/768/Final.pdf#x"),
    ("georgetowncontent", exports.LIBRARY + "/api/Anything"),
    ("georgetowncontent", exports.LIBRARY + "/api/CodesContent/docIds/other"),
    ("georgetowncontent", "https://evil.test/api/CodesContent/docIds"),
])
def test_exact_publisher_paths_cannot_expand_into_api_permission(
    bundle: SimpleNamespace, source_id: str, url: str,
) -> None:
    source = source_payload(bundle, source_id)
    source.update(url=url, final_url=url)
    with pytest.raises(ValueError, match="scoped authority"):
        coverage.EvidenceSource.model_validate(source)


@pytest.mark.parametrize("change", ["query", "retrieval", "archive", "hash", "size", "source_id"])
def test_valid_proof_cannot_be_reused_for_different_content(
    bundle: SimpleNamespace, change: str,
) -> None:
    key = "georgetowncontent" if change == "query" else "goldencontent"
    source = source_payload(bundle, key)
    if change == "query":
        source.update(url=exports.LIBRARY + "/api/CodesContent/docIds?productId=15366",
                      final_url=exports.LIBRARY + "/api/CodesContent/docIds?productId=15366")
    elif change == "retrieval":
        source["retrieved_at"] = "2026-09-10T12:00:01Z"
    elif change == "archive":
        old = bundle.root / source["archive_path"]
        source["archive_path"] = source["archive_path"].replace("/coverage/", "/research/")
        dest = bundle.root / source["archive_path"]
        dest.parent.mkdir(parents=True)
        dest.write_bytes(old.read_bytes())
    elif change == "hash":
        body = (bundle.root / source["archive_path"]).read_bytes() + b" \n"
        digest = exports.hashlib.sha256(body).hexdigest()
        source.update(sha256=digest, size_bytes=len(body),
                      archive_path=f"_RAW_ARCHIVE/local/coverage/{digest}.pdf")
        (bundle.root / source["archive_path"]).write_bytes(body)
    elif change == "size":
        source["size_bytes"] += 1
    else:
        source["source_id"] = "othercontent"
    replace_source(bundle, source, old_id=key)
    with pytest.raises(ValueError):
        coverage.validate_ledger_evidence(bundle.ledger, bundle.root)


def test_official_parent_identity_must_match_validated_proof(bundle: SimpleNamespace) -> None:
    rows = [source.model_dump() for source in bundle.ledger.sources]
    parent = next(source for source in rows if source["source_id"] == "goldenofficial")
    parent["source_id"] = "other-official-referral"
    content = next(source for source in rows if source["source_id"] == "goldencontent")
    content["linked_from_source_id"] = parent["source_id"]
    bundle.ledger = ledger_from_sources(rows)
    with pytest.raises(ValueError, match="official referral"):
        coverage.validate_ledger_evidence(bundle.ledger, bundle.root)


def test_reversed_authority_export_proof_fails_before_hook_cache(bundle: SimpleNamespace) -> None:
    data = bundle.manifest.model_dump()
    data["exports"][0]["authority_id"] = GEORGETOWN
    data["exports"][1]["authority_id"] = GOLDEN
    manifest = exports.MunicipalExportManifest.model_validate(data)
    bundle.path.write_text(manifest.model_dump_json())
    with pytest.raises(ValueError):
        coverage.validate_ledger_evidence(bundle.ledger, bundle.root)


def test_corrupt_raw_publisher_proof_cannot_be_accepted_by_ledger(bundle: SimpleNamespace) -> None:
    source = next(source for source in bundle.manifest.sources if source.source_id == "clients")
    path = bundle.root / source.archive_path
    path.write_bytes(path.read_bytes().replace(b"Golden", b"Xolden"))
    with pytest.raises(ValueError, match="hash"):
        coverage.validate_ledger_evidence(bundle.ledger, bundle.root)


def test_valid_proof_hook_binds_both_records_even_with_cached_manifest(
    bundle: SimpleNamespace,
) -> None:
    source = coverage.EvidenceSource.model_validate(source_payload(bundle, "goldencontent"))
    parent = coverage.EvidenceSource.model_validate(source_payload(bundle, "goldenofficial"))
    cached = {MANIFEST: bundle.manifest}
    coverage._validate_publisher_export(source, parent, bundle.root, cached)
    other = parent.model_copy(update={"size_bytes": parent.size_bytes + 1})
    with pytest.raises(ValueError, match="official referral"):
        coverage._validate_publisher_export(source, other, bundle.root, cached)


@pytest.mark.parametrize("wrapper,allowed", [
    ("https://www.google.com/url?q={target}", True),
    ("https://www.google.com/url?q={target}&sa=D", True),
    ("https://google.com/url?q={target}", False),
    ("https://www.google.com/other?q={target}", False),
    ("http://www.google.com/url?q={target}", False),
    ("https://www.google.com:443/url?q={target}", False),
    ("https://www.google.com/url?q={target}&q={target}", False),
    ("https://www.google.com/url?url={target}", False),
])
def test_google_wrapper_requires_exact_wrapper_and_one_official_target(
    bundle: SimpleNamespace, wrapper: str, allowed: bool,
) -> None:
    parent = coverage.EvidenceSource.model_validate(source_payload(bundle, "goldenofficial"))
    target = "https://www.cityofgolden.gov/fees.pdf"
    url = wrapper.format(target=quote(target, safe=""))
    body = ('<html><a href="' + url + '">Official fees</a></html>').encode()
    assert (target in coverage._catalog_targets(parent, body)) is allowed


@pytest.mark.parametrize("target", [
    "https://www.townofgeorgetown.us/fees.pdf", "https://evil.test/fees.pdf",
    "http://www.cityofgolden.gov/fees.pdf",
])
def test_google_wrapper_never_adopts_other_authorities_or_insecure_target(
    bundle: SimpleNamespace, target: str,
) -> None:
    parent = coverage.EvidenceSource.model_validate(source_payload(bundle, "goldenofficial"))
    url = "https://www.google.com/url?q=" + quote(target, safe="")
    body = ('<html><a href="' + url + '">Fees</a></html>').encode()
    assert target not in coverage._catalog_targets(parent, body)


def test_official_wrapped_link_binds_preserved_delegated_fee_bytes(bundle: SimpleNamespace) -> None:
    target = "https://www.cityofgolden.gov/fees.pdf"
    parent = source_payload(bundle, "goldenofficial")
    wrapper = "https://www.google.com/url?q=" + quote(target, safe="")
    body = ('<html><a href="' + wrapper + '">Official fee PDF</a></html>').encode()
    digest = exports.hashlib.sha256(body).hexdigest()
    parent.update(sha256=digest, size_bytes=len(body),
                  archive_path=f"_RAW_ARCHIVE/local/coverage/{digest}.html")
    (bundle.root / parent["archive_path"]).write_bytes(body)
    content = source_payload(bundle, "goldencontent")
    content.update(publisher_export_manifest=None, url=target,
                   final_url="https://cms3.revize.com/revize/goldenco/fees.pdf")
    ledger = ledger_from_sources([parent, content])
    coverage.validate_ledger_evidence(ledger, bundle.root)
