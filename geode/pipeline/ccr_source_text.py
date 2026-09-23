"""Offline, unreviewed native-page search over captured CCR collection evidence."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Annotated, Literal
from urllib.parse import parse_qs, urlparse

import pymupdf as fitz
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, model_validator

from geode.pipeline.ccr_current import (
    MAX_SOURCES,
    CCRCurrentRecord,
    CCRSource,
    CCRState,
    CCRVersion,
    record_identity,
)

PREFIX = "02_Regulations_CCR/_verification/current/"
MAX_FILE_BYTES = 25_000_000
MAX_TOTAL_BYTES = 500_000_000
MAX_FILES = 4000
MAX_DOCUMENTS = 1000
MAX_PAGES = 20000
MAX_TEXT_BYTES = 100_000_000
WARNING = (
    "Machine extraction is unreviewed against page images. Native text can include struck or "
    "deleted text, concatenate replacements, omit visual markup, or be empty on scanned pages. "
    "A match is source discovery, not a legal answer or evidence of current applicability. "
    "No match does not establish absence from the source or Colorado law."
)


class StrictModel(BaseModel):
    """Closed immutable output records."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class Asset(StrictModel):
    """Exact portable package member."""

    path: str = Field(pattern=r"^[A-Za-z0-9_./-]+$")
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    size_bytes: int = Field(ge=0, le=MAX_TOTAL_BYTES)

    @model_validator(mode="after")
    def safe_path(self) -> Asset:
        """Reject absolute, noncanonical and parent-traversal paths."""
        path = Path(self.path)
        if path.is_absolute() or ".." in path.parts or path.as_posix() != self.path:
            raise ValueError("Unsafe package path")
        return self


class DepartmentInput(StrictModel):
    """Pinned collector outputs; root is local provenance, not a portable dependency."""

    root: str = Field(min_length=1)
    department_id: str = Field(pattern=r"^\d+$")
    state_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    inventory_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class InputPlan(StrictModel):
    """Finite, explicitly selected department snapshots."""

    version: Literal[1] = 1
    departments: list[DepartmentInput] = Field(min_length=1, max_length=30)

    @model_validator(mode="after")
    def unique_departments(self) -> InputPlan:
        """Do not merge competing snapshots under one department identity."""
        ids = [item.department_id for item in self.departments]
        if len(set(ids)) != len(ids):
            raise ValueError("Duplicate department")
        return self


class Document(StrictModel):
    """One recorded rule/version/document association, with its original claims intact."""

    document_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    record: CCRCurrentRecord
    version: CCRVersion
    source: CCRSource
    original: Asset
    extraction_status: Literal["native_text", "empty_native", "unsupported_format"]
    physical_pages: int = Field(ge=0, le=MAX_PAGES)
    empty_native_pages: list[int]
    extraction_method: Literal["PyMuPDF get_text(text), sort=False", "not_extracted"]
    review_status: Literal["machine_extraction_unreviewed"] = "machine_extraction_unreviewed"
    answer_safe: Literal[False] = False
    currentness: Literal["not_verified"] = "not_verified"


class Page(StrictModel):
    """Exact native UTF-8 text for one physical source page."""

    document_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    physical_page: int = Field(ge=1, le=MAX_PAGES)
    original_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    text: Asset
    native_empty: bool


class Manifest(StrictModel):
    """Closed package inventory; independent trust requires pinning this manifest hash."""

    version: Literal[1] = 1
    extractor: str
    departments: int = Field(ge=1, le=30)
    documents: int = Field(ge=0, le=MAX_DOCUMENTS)
    page_associations: int = Field(ge=0, le=MAX_PAGES)
    unique_pdf_originals: int = Field(ge=0, le=MAX_DOCUMENTS)
    unique_physical_pages: int = Field(ge=0, le=MAX_PAGES)
    empty_native_documents: int = Field(ge=0, le=MAX_DOCUMENTS)
    unsupported_documents: int = Field(ge=0, le=MAX_DOCUMENTS)
    files: list[Asset] = Field(min_length=1, max_length=MAX_FILES)
    warning: Literal[WARNING] = WARNING
    answer_safe: Literal[False] = False
    currentness: Literal["not_verified"] = "not_verified"


class Hit(StrictModel):
    """Complete matched page and all recorded version/source citation metadata."""

    document: Document
    page: Page
    native_text: str


class QueryResult(StrictModel):
    """Source-only matches; result limits never conceal truncation."""

    package_manifest_sha256: str
    query: str
    mode: Literal["phrase", "citation"]
    total_matching_pages: int = Field(ge=0)
    returned_pages: int = Field(ge=0, le=50)
    truncated: bool
    empty_native_documents: int = Field(ge=0, le=MAX_DOCUMENTS)
    unsupported_documents: int = Field(ge=0, le=MAX_DOCUMENTS)
    hits: list[Hit] = Field(max_length=50)
    warning: Literal[WARNING] = WARNING
    answer_safe: Literal[False] = False
    currentness: Literal["not_verified"] = "not_verified"


class SelectedInputPlan(InputPlan):
    """Version two selects whole PDF hashes while retaining every pinned source input."""

    version: Literal[2] = 2
    selected_pdf_sha256: list[Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]] = Field(
        min_length=1, max_length=MAX_DOCUMENTS,
    )

    @model_validator(mode="after")
    def unique_selection(self) -> SelectedInputPlan:
        """Require an explicit canonical set; no duplicate, range or page selectors."""
        if self.selected_pdf_sha256 != sorted(set(self.selected_pdf_sha256)):
            raise ValueError("PDF selection must be sorted and unique")
        return self


class SelectedDocument(Document):
    """Every association remains visible, including intentionally unextracted PDFs."""

    selection_status: Literal["selected_pdf", "unselected_pdf", "unsupported_format"]
    extraction_status: Literal[
        "native_text", "empty_native", "unsupported_format", "intentionally_unselected",
    ]
    physical_pages: int | None = Field(ge=0, le=MAX_PAGES)


class SelectionScope(StrictModel):
    """Explicit extraction scope; retained originals do not imply searchable native text."""

    scope: Literal["selected_pdf_originals_only"] = "selected_pdf_originals_only"
    selected_pdf_sha256: list[Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]] = Field(
        min_length=1, max_length=MAX_DOCUMENTS,
    )
    selected_pdf_originals: int = Field(ge=1, le=MAX_DOCUMENTS)
    unselected_pdf_originals: int = Field(ge=0, le=MAX_DOCUMENTS)
    selected_document_associations: int = Field(ge=1, le=MAX_DOCUMENTS)
    unselected_document_associations: int = Field(ge=0, le=MAX_DOCUMENTS)
    complete_department_native_text: Literal[False] = False


class SelectedManifest(Manifest):
    """Version two preserves full source custody and declares bounded native selection."""

    version: Literal[2] = 2
    selection: SelectionScope


class SelectedHit(Hit):
    """A selected-source page with its explicit association selection status."""

    document: SelectedDocument


class SelectedQueryResult(QueryResult):
    """Even a no-match result exposes the intentionally unsearched document scope."""

    hits: list[SelectedHit] = Field(max_length=50)
    selection: SelectionScope
    selection_warning: Literal[
        "Only selected PDF originals were searched. Unselected PDF associations and unsupported "
        "formats remain unsearched; no match is not department-wide absence."
    ] = (
        "Only selected PDF originals were searched. Unselected PDF associations and unsupported "
        "formats remain unsearched; no match is not department-wide absence."
    )


PLAN_ADAPTER = TypeAdapter(InputPlan | SelectedInputPlan)
MANIFEST_ADAPTER = TypeAdapter(Manifest | SelectedManifest)


def _sha(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def _json(value: BaseModel | dict) -> bytes:
    data = value.model_dump(mode="json") if isinstance(value, BaseModel) else value
    return (json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()


def _asset(path: str, body: bytes) -> Asset:
    return Asset(path=path, sha256=_sha(body), size_bytes=len(body))


def _absolute(path: Path) -> Path:
    expanded = path.expanduser().absolute()
    if ".." in expanded.parts:
        raise ValueError("Parent traversal is forbidden")
    if any(part.is_symlink() for part in [expanded, *expanded.parents]):
        raise ValueError("Symlink paths are forbidden")
    return expanded


def _read(path: Path, limit: int = MAX_FILE_BYTES) -> bytes:
    path = _absolute(path)
    if not path.is_file() or path.stat().st_size > limit:
        raise ValueError(f"Missing, nonregular or oversized input: {path}")
    with path.open("rb") as handle:
        body = handle.read(limit + 1)
    if len(body) > limit or body.startswith(b"version https://git-lfs.github.com/spec/"):
        raise ValueError(f"Oversized or unavailable LFS input: {path}")
    return body


def _rows(body: bytes, model: type[BaseModel]) -> list:
    rows = []
    for line in io.BytesIO(body):
        if not line.strip():
            raise ValueError("Blank JSONL record")
        rows.append(model.model_validate_json(line))
        if len(rows) > MAX_PAGES:
            raise ValueError("JSONL record limit exceeded")
    return rows


def _jsonl(rows: list[BaseModel]) -> bytes:
    return b"".join((row.model_dump_json() + "\n").encode() for row in rows)


def _schemas(version: int = 1) -> dict[str, bytes]:
    models = (InputPlan, Document, Page, Manifest, QueryResult) if version == 1 else (
        SelectedInputPlan, SelectedDocument, Page, SelectedManifest, SelectedQueryResult,
        SelectionScope,
    )
    return {
        f"schemas/{model.__name__}.json": _json(model.model_json_schema())
        for model in models
    }


def _original(source: CCRSource) -> str:
    return f"originals/{source.sha256}{Path(source.path).suffix}"


def _bound(body: bytes, sha256: str, size: int | None = None) -> None:
    if _sha(body) != sha256 or (size is not None and len(body) != size):
        raise ValueError("Captured input hash/size mismatch")


def _url_identity(url: str, identities: dict[str, str], required: set[str]) -> None:
    parameters = parse_qs(urlparse(url).query, keep_blank_values=True)
    for key, expected in identities.items():
        if (key in parameters or key in required) and parameters.get(key) != [expected]:
            raise ValueError(f"Source URL {key} identity mismatch")


def _capture(plan: InputPlan | SelectedInputPlan) -> dict[str, bytes]:
    files = {"input-plan.json": _json(plan)}
    total = len(files["input-plan.json"])
    for item in plan.departments:
        root = _absolute(Path(item.root))
        stem = f"{PREFIX}department-{item.department_id}"
        state_bytes = _read(root / f"{stem}-state.json")
        inventory = _read(root / f"{stem}.jsonl")
        _bound(state_bytes, item.state_sha256)
        _bound(inventory, item.inventory_sha256)
        state = CCRState.model_validate_json(state_bytes)
        if len(state.sources) > MAX_SOURCES:
            raise ValueError("Collector source-count limit exceeded")
        files[f"inputs/{item.department_id}/state.json"] = state_bytes
        files[f"inputs/{item.department_id}/inventory.jsonl"] = inventory
        total += len(state_bytes) + len(inventory)
        for source in state.sources.values():
            body = _read(root / source.path)
            _bound(body, source.sha256, source.bytes)
            name = _original(source)
            total += len(body)
            if name not in files:
                files[name] = body
            if total > MAX_TOTAL_BYTES or len(files) > MAX_FILES:
                raise ValueError("Input byte/file budget exceeded")
    return files


def extract_pdf_pages(body: bytes) -> list[bytes]:
    """Extract exact native page text from the already captured original bytes, without OCR."""
    if not body.startswith(b"%PDF-"):
        raise ValueError("PDF magic missing")
    try:
        with fitz.open(stream=body, filetype="pdf") as pdf:
            if pdf.needs_pass or pdf.is_repaired or not 1 <= len(pdf) <= MAX_PAGES:
                raise ValueError("Encrypted, repaired, empty or oversized PDF")
            result = []
            total = 0
            for page in pdf:
                text = page.get_text("text", sort=False).encode("utf-8")
                total += len(text)
                if total > MAX_TEXT_BYTES:
                    raise ValueError("Native text budget exceeded")
                result.append(text)
            return result
    except (RuntimeError, fitz.FileDataError) as exc:
        raise ValueError("PDF extraction failed") from exc


def _check_unselected_pdf(body: bytes) -> None:
    if not body.startswith(b"%PDF-"):
        raise ValueError("PDF magic missing")
    try:
        with fitz.open(stream=body, filetype="pdf") as pdf:
            if pdf.needs_pass or pdf.is_repaired or not 1 <= len(pdf) <= MAX_PAGES:
                raise ValueError("Encrypted, repaired, empty or oversized PDF")
    except (RuntimeError, fitz.FileDataError) as exc:
        raise ValueError("PDF validation failed") from exc


def _derive(
    files: dict[str, bytes],
) -> tuple[list[Document | SelectedDocument], list[Page], dict[str, bytes]]:
    plan = PLAN_ADAPTER.validate_json(files["input-plan.json"])
    selected = set(plan.selected_pdf_sha256) if isinstance(plan, SelectedInputPlan) else None
    documents, pages = [], []
    texts: dict[str, bytes] = {}
    cache: dict[str, list[bytes]] = {}
    expected = {"input-plan.json"}
    identities: set[str] = set()
    eligible_pdfs: set[str] = set()
    checked_unselected: set[str] = set()
    for item in plan.departments:
        state_name = f"inputs/{item.department_id}/state.json"
        inventory_name = f"inputs/{item.department_id}/inventory.jsonl"
        expected.update((state_name, inventory_name))
        _bound(files[state_name], item.state_sha256)
        _bound(files[inventory_name], item.inventory_sha256)
        state = CCRState.model_validate_json(files[state_name])
        if len(state.sources) > MAX_SOURCES:
            raise ValueError("Collector source-count limit exceeded")
        _bound(files[inventory_name], state.inventory_sha256)
        records = _rows(files[inventory_name], CCRCurrentRecord)
        rule_ids = [record.rule_id for record in records]
        if (
            state.department_id != item.department_id
            or len(rule_ids) != len(set(rule_ids))
            or sorted(rule_ids) != sorted(state.rule_ids)
            or len(state.rule_ids) != len(set(state.rule_ids))
            or len(state.agency_ids) != len(set(state.agency_ids))
        ):
            raise ValueError("Department/inventory identity mismatch")
        for url, source in state.sources.items():
            if url != source.url:
                raise ValueError("Source map URL mismatch")
            name = _original(source)
            expected.add(name)
            _bound(files[name], source.sha256, source.bytes)
        for record in records:
            if (
                record.id in identities or record.department_id != item.department_id
                or record.id != record_identity(record.ccr_citation, record.rule_id)
                or parse_qs(urlparse(record.source_page_url).query).get("ruleId")
                != [record.rule_id]
                or record.department_name != state.department_name
                or record.agency_id not in state.agency_ids
                or record.source_publication_cutoff != state.source_publication_cutoff
                or any(state.sources.get(src.url) != src for src in record.sources)
            ):
                raise ValueError("Rule identity or source provenance mismatch")
            identities.add(record.id)
            sources = {source.url: source for source in record.sources}
            version_ids = [version.version_id for version in record.versions]
            if (
                len(version_ids) != len(set(version_ids))
                or (record.selected_version_id and record.selected_version_id not in version_ids)
                or record.source_page_url not in sources
            ):
                raise ValueError("Version/primary source identity mismatch")
            primary = sources[record.source_page_url]
            identities_by_parameter = {
                "ruleId": record.rule_id, "deptID": record.department_id,
                "agencyID": record.agency_id,
            }
            requested_parameters = parse_qs(urlparse(primary.url).query, keep_blank_values=True)
            required_parameters = {"ruleId"} | (
                set(requested_parameters) & set(identities_by_parameter)
            )
            _url_identity(primary.url, identities_by_parameter, required_parameters)
            _url_identity(primary.final_url, identities_by_parameter, required_parameters)
            for version in record.versions:
                if version.designation == "history":
                    continue
                if len(version.document_urls) != len(set(version.document_urls)):
                    raise ValueError("Duplicate document URL")
                for url in version.document_urls:
                    parameters = parse_qs(urlparse(url).query)
                    if (
                        parameters.get("ruleVersionId") != [version.version_id]
                        or parameters.get("fileName") != [record.ccr_citation]
                    ):
                        raise ValueError("Document URL version/citation identity mismatch")
                    source = sources.get(url)
                    if source is None or source.path.endswith(".html"):
                        raise ValueError("Version document missing or HTML")
                    if parse_qs(urlparse(source.final_url).query).get("ruleVersionId") != [
                        version.version_id
                    ]:
                        raise ValueError("Final document URL changed version identity")
                    name = _original(source)
                    body = files[name]
                    pdf = source.path.endswith(".pdf")
                    admitted = pdf and (selected is None or source.sha256 in selected)
                    if pdf:
                        eligible_pdfs.add(source.sha256)
                    if pdf and not admitted and source.sha256 not in checked_unselected:
                        _check_unselected_pdf(body)
                        checked_unselected.add(source.sha256)
                    if admitted and source.sha256 not in cache:
                        cache[source.sha256] = extract_pdf_pages(body)
                    native = cache[source.sha256] if admitted else []
                    identity = _sha(_json({"rule": record.id, "version": version.version_id,
                                          "url": url}))
                    empty = [index for index, text in enumerate(native, 1) if not text.strip()]
                    model = Document if selected is None else SelectedDocument
                    scope = {} if selected is None else {"selection_status": (
                        "selected_pdf" if admitted else "unselected_pdf" if pdf
                        else "unsupported_format"
                    )}
                    status = (("native_text" if len(empty) < len(native) else "empty_native")
                              if admitted else "intentionally_unselected" if pdf
                              else "unsupported_format")
                    documents.append(model(
                        document_id=identity, record=record, version=version, source=source,
                        original=_asset(name, body),
                        physical_pages=None if pdf and not admitted else len(native),
                        empty_native_pages=empty,
                        extraction_status=status,
                        extraction_method=("PyMuPDF get_text(text), sort=False"
                                           if admitted else "not_extracted"), **scope,
                    ))
                    for index, text in enumerate(native, 1):
                        text_name = f"native/{source.sha256}/{index:05d}.txt"
                        texts[text_name] = text
                        pages.append(Page(
                            document_id=identity, physical_page=index,
                            original_sha256=source.sha256, text=_asset(text_name, text),
                            native_empty=not text.strip(),
                        ))
                    if len(documents) > MAX_DOCUMENTS or len(pages) > MAX_PAGES:
                        raise ValueError("Document/page association budget exceeded")
    input_names = {name for name in files if name.startswith(("inputs/", "originals/"))}
    if expected != input_names | {"input-plan.json"}:
        raise ValueError("Unexpected captured input member")
    if sum(map(len, texts.values())) > MAX_TEXT_BYTES:
        raise ValueError("Total native text budget exceeded")
    if selected is not None and not selected <= eligible_pdfs:
        raise ValueError("Selection contains unknown or noneligible PDF hashes")
    return documents, pages, texts


def _outputs(files: dict[str, bytes]) -> tuple[dict[str, bytes], Manifest | SelectedManifest]:
    plan = PLAN_ADAPTER.validate_json(files["input-plan.json"])
    documents, pages, texts = _derive(files)
    outputs = {**_schemas(plan.version), **files, **texts, "documents.jsonl": _jsonl(documents),
               "pages.jsonl": _jsonl(pages)}
    if len(outputs) > MAX_FILES or sum(map(len, outputs.values())) > MAX_TOTAL_BYTES:
        raise ValueError("Package file/byte budget exceeded")
    model, extra = Manifest, {}
    if isinstance(plan, SelectedInputPlan):
        unselected = [
            doc for doc in documents if doc.extraction_status == "intentionally_unselected"
        ]
        extra = {"selection": SelectionScope(
            selected_pdf_sha256=plan.selected_pdf_sha256,
            selected_pdf_originals=len(plan.selected_pdf_sha256),
            unselected_pdf_originals=len({doc.source.sha256 for doc in unselected}),
            selected_document_associations=sum(
                doc.selection_status == "selected_pdf" for doc in documents
            ), unselected_document_associations=len(unselected),
        )}
        model = SelectedManifest
    manifest = model(
        extractor=f"PyMuPDF {fitz.VersionBind}", departments=len(plan.departments),
        documents=len(documents), page_associations=len(pages),
        unique_pdf_originals=len({page.original_sha256 for page in pages}),
        unique_physical_pages=len({page.text.path for page in pages}),
        empty_native_documents=sum(doc.extraction_status == "empty_native" for doc in documents),
        unsupported_documents=sum(doc.extraction_status == "unsupported_format"
                                  for doc in documents),
        files=[_asset(name, outputs[name]) for name in sorted(outputs)],
        **extra,
    )
    if sum(map(len, outputs.values())) + len(_json(manifest)) > MAX_TOTAL_BYTES:
        raise ValueError("Manifest-inclusive package byte budget exceeded")
    return outputs, manifest


def build(plan: InputPlan | SelectedInputPlan, output: Path) -> Manifest | SelectedManifest:
    """Publish a fresh isolated package, with its final manifest as the completion marker."""
    output = _absolute(output)
    if any(part.startswith(("_RAW_ARCHIVE", "_CONTROL_PLANE", "_SNAPSHOTS"))
           or (len(part) >= 3 and part[:2].isdigit() and part[2] == "_")
           for part in output.parts):
        raise ValueError("Output must be outside canonical archive/control/layer paths")
    if output.exists():
        raise ValueError("Output already exists; overwrite is forbidden")
    files, manifest = _outputs(_capture(plan))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.mkdir()  # Exclusive reservation; no replacement of even an empty existing package.
    try:
        for name, body in {**files, "MANIFEST.json": _json(manifest)}.items():
            target = output / name
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_name(target.name + ".tmp")
            with temporary.open("xb") as handle:
                handle.write(body)
            os.replace(temporary, target)
    except Exception:
        shutil.rmtree(output)
        raise
    return manifest


def _verified(package: Path, expected_sha256: str | None) -> tuple[dict[str, bytes], bytes]:
    package = _absolute(package)
    raw_manifest = _read(package / "MANIFEST.json")
    if expected_sha256 is not None:
        _bound(raw_manifest, expected_sha256)
    manifest = MANIFEST_ADAPTER.validate_json(raw_manifest)
    names = [asset.path for asset in manifest.files]
    if len(names) != len(set(names)) or "MANIFEST.json" in names:
        raise ValueError("Duplicate or self-referencing manifest member")
    if sum(asset.size_bytes for asset in manifest.files) + len(raw_manifest) > MAX_TOTAL_BYTES:
        raise ValueError("Declared package byte budget exceeded")
    actual = set()
    directories = set()
    for path in package.rglob("*"):
        if path.is_symlink():
            raise ValueError("Package contains symlink")
        relative = path.relative_to(package).as_posix()
        (directories if path.is_dir() else actual).add(relative)
    expected_dirs = {str(parent) for name in names for parent in Path(name).parents
                     if str(parent) != "."}
    if actual != set(names) | {"MANIFEST.json"} or directories != expected_dirs:
        raise ValueError("Package is not a closed inventory")
    files: dict[str, bytes] = {}
    total = 0
    for asset in manifest.files:
        body = _read(package / asset.path, MAX_TOTAL_BYTES)
        _bound(body, asset.sha256, asset.size_bytes)
        total += len(body)
        if total > MAX_TOTAL_BYTES:
            raise ValueError("Package byte budget exceeded")
        files[asset.path] = body
    inputs = {name: body for name, body in files.items()
              if name == "input-plan.json" or name.startswith(("inputs/", "originals/"))}
    expected, derived = _outputs(inputs)
    if files != expected or manifest != derived:
        raise ValueError("Package extraction/schema/metadata replay mismatch")
    return files, raw_manifest


def verify(package: Path, expected_sha256: str | None = None) -> Manifest | SelectedManifest:
    """Replay captured joins and native extraction without reopening original input paths."""
    _, raw = _verified(package, expected_sha256)
    return MANIFEST_ADAPTER.validate_json(raw)


def query(
    package: Path, text: str, *, mode: Literal["phrase", "citation"] = "phrase",
    limit: int = 10, expected_sha256: str | None = None,
) -> QueryResult | SelectedQueryResult:
    """Return literal case-insensitive source matches, preserving each entire physical page."""
    if not text.strip() or len(text) > 500 or not 1 <= limit <= 50:
        raise ValueError("Nonempty query up to 500 characters and limit 1..50 required")
    if mode not in {"phrase", "citation"}:
        raise ValueError("Only source phrase/citation search is supported")
    files, raw = _verified(package, expected_sha256)
    manifest = MANIFEST_ADAPTER.validate_json(raw)
    selected = isinstance(manifest, SelectedManifest)
    document_model = SelectedDocument if selected else Document
    hit_model = SelectedHit if selected else Hit
    result_model = SelectedQueryResult if selected else QueryResult
    documents = {
        doc.document_id: doc for doc in _rows(files["documents.jsonl"], document_model)
    }
    hits, count, returned_bytes = [], 0, 0
    for page in _rows(files["pages.jsonl"], Page):
        doc = documents[page.document_id]
        native = files[page.text.path].decode("utf-8")
        haystack = native if mode == "phrase" else doc.record.ccr_citation
        matched = (text.casefold() in haystack.casefold() if mode == "phrase"
                   else text.casefold() == haystack.casefold())
        if matched:
            count += 1
            if len(hits) < limit and returned_bytes + page.text.size_bytes <= 2_000_000:
                hits.append(hit_model(document=doc, page=page, native_text=native))
                returned_bytes += page.text.size_bytes
    extra = {"selection": manifest.selection} if selected else {}
    return result_model(
        package_manifest_sha256=_sha(raw), query=text, mode=mode,
        total_matching_pages=count, returned_pages=len(hits),
        truncated=count > len(hits), hits=hits,
        empty_native_documents=manifest.empty_native_documents,
        unsupported_documents=manifest.unsupported_documents,
        **extra,
    )


def main(argv: list[str] | None = None) -> int:
    """Build, verify or query an offline package, without collection or legal answers."""
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    creator = commands.add_parser("build")
    creator.add_argument("--plan", type=Path, required=True)
    creator.add_argument("--output", type=Path, required=True)
    for name in ("verify", "query"):
        command = commands.add_parser(name)
        command.add_argument("--package", type=Path, required=True)
        command.add_argument("--manifest-sha256")
        if name == "query":
            command.add_argument("--text", required=True)
            command.add_argument("--mode", choices=("phrase", "citation"), default="phrase")
            command.add_argument("--limit", type=int, default=10)
    args = parser.parse_args(argv)
    try:
        if args.command == "build":
            result = build(PLAN_ADAPTER.validate_json(_read(args.plan)), args.output)
        elif args.command == "verify":
            result = verify(args.package, args.manifest_sha256)
        else:
            result = query(args.package, args.text, mode=args.mode, limit=args.limit,
                           expected_sha256=args.manifest_sha256)
        sys.stdout.write(_json(result).decode())
        return 0
    except (ValueError, OSError, KeyError) as exc:
        sys.stderr.write(f"CCR source-text refusal: {exc}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
