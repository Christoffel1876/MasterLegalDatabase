"""Adversarial offline publisher proof tests using small, structurally valid originals."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from urllib.parse import urlencode

import pymupdf
import pytest

from geode.pipeline import municipal_code_export as module


def _pdf(text: str = "Golden Municipal Code\nCHARTER\nSupplement 20\nOrd. 2292") -> bytes:
    with pymupdf.open() as document:
        page = document.new_page()
        page.insert_text((40, 40), text)
        return document.tobytes()


def _fixture(root: Path) -> module.MunicipalExportManifest:
    refs = []

    def save(source_id: str, url: str, body: bytes | dict | list, media: str = "json",
             **kwargs: object) -> str:
        if not isinstance(body, bytes):
            body = json.dumps(body).encode()
        digest = hashlib.sha256(body).hexdigest()
        path = root / "originals" / f"{digest}.{media}"
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(body)
        refs.append(module.SourceRef(
            source_id=source_id, url=url, archive_path=path.relative_to(root).as_posix(),
            sha256=digest, size_bytes=len(body), retrieved_at="2026-09-10T12:00:00Z",
            media_type=media, **kwargs,
        ))
        return source_id

    script_url = module.LIBRARY + "/dist/js/all/all.min.js?v=public"
    inspection = module.EndpointInspection(
        script_url=script_url, original_response_sha256="b" * 64,
        endpoint_bindings=module.PUBLIC_ENDPOINTS,
    )
    save("script", script_url, inspection.model_dump(),
         representation="public_client_endpoint_summary")
    save("shell", module.LIBRARY + "/co/golden/codes/municipal_code",
         f'<html><script src="{script_url}"></script></html>'.encode(), "html")
    save("clients", module.LIBRARY + "/api/Clients/stateAbbr?stateAbbr=co", [
        {"ClientID": 2384, "ClientName": "Golden", "State": {"StateAbbreviation": "CO"}},
        {"ClientID": 19056, "ClientName": "Georgetown", "State": {"StateAbbreviation": "CO"}},
    ])
    exports = []
    for authority, (name, client, product, publication, host) in module.PROFILES.items():
        slug = name.lower()
        save(slug + "official", "https://" + host + "/folder/",
             ('<html><base href="https://' + host + '/"><a href="' + module.LIBRARY
              + '/co/' + slug + '/codes/municipal_code#new_tab">Code</a></html>').encode(),
             "html")
        save(slug + "pub", f"{module.LIBRARY}/api/ClientContent/{client}", {"codes": [{
            "productId": product, "publicationId": publication, "productName": "Municipal Code",
            "hasPdf": slug == "golden", "hasPdfDownloadEnabled": slug == "golden",
        }]})
        save(slug + "job", f"{module.LIBRARY}/api/Jobs/latest/{product}", {
            "ProductId": product, "Id": 123, "IsLatest": True, "BannerText": "Supplement 20",
        })
        roots = [{"Id": "CODE", "Heading": "Golden Municipal Code" if slug == "golden"
                  else "Georgetown Municipal Code", "DocOrderId": 1, "ParentId": str(product),
                  "NodeDepth": 1},
                 {"Id": "CH", "Heading": "CHARTER", "DocOrderId": 3,
                  "ParentId": str(product), "NodeDepth": 1}]
        save(slug + "toc", f"{module.LIBRARY}/api/codesToc?productId={product}&jobId=123",
             {"Id": str(product), "Children": roots})
        download = None
        images = []
        if slug == "golden":
            url = f"{module.STORAGE}/publication-official-copy-pdfs/{publication}/Final.pdf"
            save(slug + "content", url, _pdf(), "pdf", request_query_redacted=True)
            endpoint = f"{module.LIBRARY}/api/PublicationPdfDownload/{publication}"
            download = save("download", endpoint,
                            {"stable_download_url": url, "signed_query_redacted": True,
                             "original_response_sha256": "a" * 64},
                            representation="signed_url_redacted")
        else:
            image_url = f"{module.STORAGE}/codecontent/{product}/123/plate.png"
            chunks = []
            for ordinal, node, title, depth in [(1, "CODE", roots[0]["Heading"], 1),
                                                 (2, "CODE_S1", "1.01 - Rule", 2),
                                                 (3, "CH", "CHARTER", 1)]:
                chunks.append(dict(Id=node, Title=title, NodeDepth=depth, DocOrderId=ordinal,
                                   Content='<p>Exact rule.</p><img src="' + image_url + '">',
                                   Footnotes="<p>Exception retained.</p>"))
            query = urlencode({"productId": product, "jobId": 123,
                               "docIds": [r["Id"] for r in roots], "showChanges": "false"},
                              doseq=True)
            save(slug + "content", module.LIBRARY + "/api/CodesContent/docIds?" + query, chunks)
            with pymupdf.open(stream=_pdf(), filetype="pdf") as document:
                image_bytes = document[0].get_pixmap(matrix=pymupdf.Matrix(.05, .05)).tobytes("png")
            images = [save("image", image_url, image_bytes, "png")]
        exports.append(module.MunicipalExport(
            authority_id=authority, official_referral=slug + "official", publications=slug + "pub",
            latest_job=slug + "job", toc=slug + "toc", content=slug + "content",
            download_response=download, images=images, job_id=123,
            expected_units=1 if slug == "golden" else 3, edition_statement="Supplement 20",
            pdf_edition_excerpts=[module.EditionExcerpt(page=1, excerpt="Ord. 2292")]
            if slug == "golden" else [], limitations=["Later ordinances remain unreconciled."],
        ))
    return module.MunicipalExportManifest(sources=refs, clients="clients", library_shell="shell",
                                         library_script="script", exports=exports)


@pytest.fixture
def bundle(tmp_path: Path) -> tuple[Path, module.MunicipalExportManifest]:
    return tmp_path, _fixture(tmp_path)


def _replace(root: Path, manifest: module.MunicipalExportManifest, source_id: str,
             body: object | None = None, **changes: object) -> module.MunicipalExportManifest:
    data = manifest.model_dump(mode="json")
    item = next(s for s in data["sources"] if s["source_id"] == source_id)
    if body is not None:
        raw = body if isinstance(body, bytes) else json.dumps(body).encode()
        digest = hashlib.sha256(raw).hexdigest()
        path = root / "originals" / f"{digest}.{item['media_type']}"
        path.write_bytes(raw)
        item.update(archive_path=path.relative_to(root).as_posix(), sha256=digest,
                    size_bytes=len(raw))
    item.update(changes)
    return module.MunicipalExportManifest.model_validate(data)


def _json(root: Path, manifest: module.MunicipalExportManifest, source_id: str) -> object:
    source = next(s for s in manifest.sources if s.source_id == source_id)
    return json.loads((root / source.archive_path).read_bytes())


def test_valid_proof_and_text_include_exception_and_image(bundle: tuple) -> None:
    root, manifest = bundle
    results = module.validate_municipal_exports(manifest, root)
    assert [r.units for r in results] == [1, 3]
    assert results[0].signed_response_original_hash_recomputed is False
    assert results[1].missing_images == []
    records = list(module.iter_export_text(manifest, root))
    assert len(records) == 4 and records[0].page == 1
    assert "Exact rule." in records[1].text and "Exception retained." in records[1].text
    assert len(records[1].image_urls) == 1
    assert all(r.legal_currentness == "not_reconciled" and r.review_required for r in records)


@pytest.mark.parametrize("field,value", [
    ("url", "http://library.municode.com/"), ("url", "https://user:pass@library.municode.com/"),
    ("url", "https://library.municode.com:444/"), ("url", "https://library.municode.com/a/../b"),
    ("url", "https://library.municode.com/a?sig=secret"), ("url", "https://x.test/a#fragment"),
    ("archive_path", "/outside/hash.pdf"), ("archive_path", "../outside/hash.pdf"),
    ("archive_path", "originals/" + "a" * 64 + ".pdf"), ("retrieved_at", "2026-09-10"),
])
def test_source_schema_rejects_unsafe_locations(bundle: tuple, field: str, value: str) -> None:
    _, manifest = bundle
    item = manifest.sources[0].model_dump()
    item[field] = value
    with pytest.raises(ValueError):
        module.SourceRef.model_validate(item)


@pytest.mark.parametrize("change", ["source_duplicate", "authority_duplicate", "source_missing",
                                   "false_current", "false_review", "unknown_authority"])
def test_manifest_identity_and_honesty(bundle: tuple, change: str) -> None:
    _, manifest = bundle
    data = manifest.model_dump()
    if change == "source_duplicate":
        data["sources"].append(data["sources"][0])
    elif change == "authority_duplicate":
        data["exports"][1] = data["exports"][0]
    elif change == "source_missing":
        data["sources"].pop()
    elif change == "false_current":
        data["exports"][0]["legal_currentness"] = "current"
    elif change == "false_review":
        data["exports"][0]["review_required"] = False
    else:
        data["exports"][0]["authority_id"] = "CO-MUNICIPAL-OTHER"
    with pytest.raises(ValueError):
        module.MunicipalExportManifest.model_validate(data)


@pytest.mark.parametrize("change", ["missing", "hash", "symlink", "ancestor_symlink", "budget"])
def test_missing_corrupt_or_unsafe_bytes(bundle: tuple, change: str) -> None:
    root, manifest = bundle
    source = manifest.sources[0]
    path = root / source.archive_path
    if change == "missing":
        path.unlink()
    elif change == "hash":
        path.write_bytes(b"version https://git-lfs.github.com/spec/v1\n")
    elif change == "symlink":
        target = root / "target"
        target.write_bytes(path.read_bytes())
        path.unlink()
        path.symlink_to(target)
    elif change == "ancestor_symlink":
        moved = root / "moved"
        path.parent.rename(moved)
        path.parent.symlink_to(moved, target_is_directory=True)
    else:
        data = manifest.model_dump()
        for item in data["sources"]:
            item["size_bytes"] = 50_000_000
        manifest = module.MunicipalExportManifest.model_validate(data)
    with pytest.raises(ValueError):
        module.validate_municipal_exports(manifest, root)


@pytest.mark.parametrize("source_id,body", [
    ("goldenofficial", b'<html><a href="https://library.municode.com/co/georgetown/codes/'
                       b'municipal_code">Wrong</a></html>'),
    ("goldenofficial", b"<html>Truncated"),
    ("goldenofficial", b'<html><base href="https://evil.test/"></html>'),
    ("goldenofficial", b'<html><base href="/"><base href="/"></html>'),
    ("shell", b"<html>No script referral</html>"),
    ("script", b"CodesContent/docIds only"),
    ("goldencontent", b"%PDF-1.7\n"),
    ("goldencontent", _pdf("Wrong municipality and no charter")),
    ("image", b"\x89PNG\r\n\x1a\ntruncated"),
])
def test_rehashed_wrong_originals_still_fail(bundle: tuple, source_id: str, body: bytes) -> None:
    root, manifest = bundle
    manifest = _replace(root, manifest, source_id, body)
    with pytest.raises(ValueError):
        module.validate_municipal_exports(manifest, root)


@pytest.mark.parametrize("source_id,change", [
    ("clients", "wrong_state"), ("clients", "duplicate"), ("clients", "wrong_name"),
    ("goldenpub", "publication"), ("goldenpub", "pdf_disabled"),
    ("goldenjob", "product"), ("goldenjob", "job"), ("goldenjob", "edition"),
    ("goldentoc", "parent"), ("goldentoc", "id"), ("goldentoc", "duplicate"),
    ("download", "url"), ("download", "digest"), ("download", "redaction"),
])
def test_rehashed_metadata_cannot_change_identity(
    bundle: tuple, source_id: str, change: str,
) -> None:
    root, manifest = bundle
    data = _json(root, manifest, source_id)
    if source_id == "clients":
        if change == "wrong_state":
            data[0]["State"]["StateAbbreviation"] = "WY"
        elif change == "duplicate":
            data.append(data[0])
        else:
            data[0]["ClientName"] = "Other"
    elif source_id == "goldenpub":
        data["codes"][0]["publicationId" if change == "publication" else
                         "hasPdfDownloadEnabled"] = 999 if change == "publication" else False
    elif source_id == "goldenjob":
        data[{"product": "ProductId", "job": "Id", "edition": "BannerText"}[change]] = 999
    elif source_id == "goldentoc":
        if change == "parent":
            data["Children"][0]["ParentId"] = "other"
        elif change == "id":
            data["Id"] = "other"
        else:
            data["Children"].append(data["Children"][0])
    else:
        data[{"url": "stable_download_url", "digest": "original_response_sha256",
              "redaction": "signed_query_redacted"}[change]] = "wrong"
    manifest = _replace(root, manifest, source_id, data)
    with pytest.raises((ValueError, AttributeError)):
        module.validate_municipal_exports(manifest, root)


@pytest.mark.parametrize("change", ["missing", "duplicate", "reordered", "bool_order", "malformed",
                                   "missing_key", "nonstring", "top_title", "root_tail"])
def test_partial_print_is_not_full_export(bundle: tuple, change: str) -> None:
    root, manifest = bundle
    chunks = _json(root, manifest, "georgetowncontent")
    if change == "missing":
        chunks.pop()
    elif change == "duplicate":
        chunks[1]["Id"] = chunks[0]["Id"]
    elif change == "reordered":
        chunks[0], chunks[1] = chunks[1], chunks[0]
    elif change == "bool_order":
        chunks[0]["DocOrderId"] = True
    elif change == "malformed":
        chunks[0] = "not a chunk"
    elif change == "missing_key":
        chunks[0].pop("Footnotes")
    elif change == "nonstring":
        chunks[0]["Content"] = None
    elif change == "top_title":
        chunks[0]["Title"] = "Another title"
    else:
        chunks[-1]["NodeDepth"] = 2
    manifest = _replace(root, manifest, "georgetowncontent", chunks)
    with pytest.raises(ValueError):
        module.validate_municipal_exports(manifest, root)


@pytest.mark.parametrize("source_id,field,value", [
    ("goldenpub", "url", module.LIBRARY + "/api/ClientContent/19056"),
    ("goldenofficial", "url", "https://evil.test/"),
    ("script", "url", "https://evil.test/script.js"),
    ("georgetowncontent", "url", module.LIBRARY + "/api/CodesContent/docIds?showChanges=true"),
    ("image", "url", module.STORAGE + "/codecontent/15366/123/plate.png"),
    ("goldencontent", "representation", "signed_url_redacted"),
    ("download", "representation", "original"),
])
def test_chain_endpoint_and_representation_cannot_be_swapped(
    bundle: tuple, source_id: str, field: str, value: str,
) -> None:
    root, manifest = bundle
    manifest = _replace(root, manifest, source_id, **{field: value})
    with pytest.raises(ValueError):
        module.validate_municipal_exports(manifest, root)


@pytest.mark.parametrize("change", ["pdf_count", "excerpt_page", "excerpt_text", "missing_excerpt",
                                   "georgetown_pdf", "duplicate_image"])
def test_export_structure_failures(bundle: tuple, change: str) -> None:
    root, manifest = bundle
    data = manifest.model_dump()
    if change == "pdf_count":
        data["exports"][0]["expected_units"] = 2
    elif change == "excerpt_page":
        data["exports"][0]["pdf_edition_excerpts"][0]["page"] = 2
    elif change == "excerpt_text":
        data["exports"][0]["pdf_edition_excerpts"][0]["excerpt"] = "Not on the page"
    elif change == "missing_excerpt":
        data["exports"][0]["pdf_edition_excerpts"] = []
    elif change == "georgetown_pdf":
        data["exports"][1]["pdf_edition_excerpts"] = [{"page": 1, "excerpt": "Wrong"}]
    else:
        data["exports"][1]["images"].append("image")
    manifest = module.MunicipalExportManifest.model_validate(data)
    with pytest.raises(ValueError):
        module.validate_municipal_exports(manifest, root)


def test_absent_images_are_explicit_gaps_not_complete(bundle: tuple) -> None:
    root, manifest = bundle
    data = manifest.model_dump()
    data["sources"] = [s for s in data["sources"] if s["source_id"] != "image"]
    data["exports"][1]["images"] = []
    result = module.validate_municipal_exports(module.MunicipalExportManifest(**data), root)[1]
    assert len(result.missing_images) == 1 and result.images_preserved == 0


def test_atomic_new_directory_and_cli(bundle: tuple) -> None:
    root, manifest = bundle
    path = root / "manifest.json"
    path.write_text(manifest.model_dump_json())
    output = root / "text"
    assert module.main(["--manifest", str(path), "--root", str(root), "--output", str(output)]) == 0
    records = [module.ExtractedText.model_validate_json(line)
               for line in (output / "text.jsonl").read_text().splitlines()]
    assert len(records) == 4
    with pytest.raises(ValueError, match="new directory"):
        module.write_export_text(manifest, root, output)
    assert module.main(["--manifest", str(path), "--root", str(root)]) == 0
    path.write_text("{}")
    assert module.main(["--manifest", str(path), "--root", str(root)]) == 1
    path.write_bytes(b" " * 2_000_001)
    assert module.main(["--manifest", str(path), "--root", str(root)]) == 1


def test_failed_extraction_never_promotes_directory(bundle: tuple) -> None:
    root, manifest = bundle
    manifest = _replace(root, manifest, "goldencontent", b"broken")
    with pytest.raises(ValueError):
        module.write_export_text(manifest, root, root / "output")
    assert not (root / "output").exists()
    assert not list(root.glob("tmp*"))


def test_output_symlink_and_extraction_record_guards(bundle: tuple) -> None:
    root, manifest = bundle
    (root / "link").symlink_to(root, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        module.write_export_text(manifest, root, root / "link" / "out")
    records = list(module.iter_export_text(manifest, root))
    for index, field, value in [(0, "page", 2), (1, "node_id", None),
                                (0, "research_only", False), (1, "review_required", False)]:
        data = records[index].model_dump()
        data[field] = value
        with pytest.raises(ValueError):
            module.ExtractedText.model_validate(data)


def test_html_text_does_not_include_script_or_style() -> None:
    html = module._HTML("<style>hidden</style><p>Law<br>next</p><script>not law</script>")
    assert "".join(html.parts).strip() == "Law\nnext"


@pytest.mark.parametrize("change", ["dropped", "extra", "modified", "reordered", "oversized"])
def test_saved_text_cannot_diverge(bundle: tuple, change: str) -> None:
    root, manifest = bundle
    output = root / "extracted"
    module.write_export_text(manifest, root, output)
    path = output / "text.jsonl"
    assert module.validate_saved_export_text(manifest, root, path) == 4
    rows = path.read_text().splitlines(keepends=True)
    if change == "dropped":
        rows.pop()
    elif change == "extra":
        rows.append(rows[0])
    elif change == "modified":
        record = json.loads(rows[0])
        record["text"] = "Invented mandatory duty."
        rows[0] = json.dumps(record) + "\n"
    elif change == "oversized":
        rows[0] = " " * 2_000_001
    else:
        rows[0], rows[1] = rows[1], rows[0]
    path.write_text("".join(rows))
    with pytest.raises(ValueError):
        module.validate_saved_export_text(manifest, root, path)


@pytest.mark.parametrize("location", ["outside", "traversal", "raw", "symlink_manifest"])
def test_output_and_manifest_confinement(bundle: tuple, location: str) -> None:
    root, manifest = bundle
    if location == "symlink_manifest":
        actual = root / "manifest.json"
        actual.write_text(manifest.model_dump_json())
        alias = root / "alias.json"
        alias.symlink_to(actual)
        assert module.main(["--manifest", str(alias), "--root", str(root)]) == 1
        return
    output = {"outside": root.parent / "escaped-output",
              "traversal": root / "unused" / ".." / "out",
              "raw": root / "_RAW_ARCHIVE" / "derived"}[location]
    with pytest.raises(ValueError):
        module.write_export_text(manifest, root, output)
    assert not output.exists()


def test_cli_validates_saved_native_text(bundle: tuple) -> None:
    root, manifest = bundle
    path = root / "manifest.json"
    path.write_text(manifest.model_dump_json())
    module.write_export_text(manifest, root, root / "extracted")
    text = root / "extracted" / "text.jsonl"
    assert module.main(["--manifest", str(path), "--root", str(root), "--text", str(text)]) == 0
