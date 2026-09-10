"""Fee findings must preserve page provenance, authority ownership and unresolved scope."""

from __future__ import annotations

import copy
import hashlib
import runpy
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from geode.pipeline import local_fee_review as fees
from geode.pipeline.local_text_review import ExcerptReview
from tests.test_local_text_review import NOW, OWNER, TEXT, package, save_ledger

FeeFixture = tuple[Path, dict, dict, dict]


@pytest.fixture
def fee_package(package: tuple[Path, dict, dict, dict]) -> FeeFixture:
    """Build native and scan citations around real PDF, ledger and strict OCR fixtures."""
    root, review_data, ledger, _ = package
    relative = "research/fees/fixture-excerpts.json"
    path = root / relative
    path.parent.mkdir(parents=True)
    body = ExcerptReview.model_validate(review_data).model_dump_json().encode()
    path.write_bytes(body)
    citation = dict(
        source_id="golden-fee", source_sha256=ledger["sources"][0]["sha256"],
        physical_page=1, printed_page="1", section="Effective date", excerpt=TEXT,
        method="native_text",
    )
    checked = dict(
        **{**citation, "method": "checked_ocr_excerpt"}, checked_review_path=relative,
        checked_review_sha256=hashlib.sha256(body).hexdigest(), checked_excerpt_id="fee-effective",
    )
    observation = dict(
        observation_id="native-fee", authority_id=OWNER, classification="adopting_text",
        statement="The source states effectiveness upon adoption.",
        conditions=["Later amendments remain unreconciled"], evidence=[citation, checked],
    )
    data = dict(
        study_id="fixture-fees", prepared_at=NOW, scope="Sampled fixture only",
        observations=[observation], open_chain=[dict(
            item_id="missing-amendments", authority_id=OWNER, issue="Later changes are unknown",
            source_ids=["golden-fee"], next_action="Collect later adopted changes",
            observed_urls=["https://www.cityofgolden.gov/fees"],
        )], limitations=["Not a total-cost estimate or current-law certification"],
    )
    return root, data, ledger, review_data


def validate(data: dict, root: Path) -> fees.FeeReconciliation:
    """Validate both schema and actual local source evidence."""
    model = fees.FeeReconciliation.model_validate(data)
    fees.validate_fee_reconciliation(model, root)
    return model


def test_native_and_checked_citations_use_actual_ledger_and_ocr(fee_package: FeeFixture) -> None:
    root, data, _, _ = fee_package
    data["observations"][0]["evidence"] *= 2  # Exercise verified review/page reuse.
    model = validate(data, root)
    assert model.coverage == "sampled_findings_only"
    assert model.legal_currentness == "not_verified"
    assert model.legal_review == "pending"


@pytest.mark.parametrize("field", [
    "checked_review_path", "checked_review_sha256", "checked_excerpt_id",
])
def test_checked_passages_require_complete_review_binding(
    fee_package: FeeFixture, field: str,
) -> None:
    _, data, _, _ = fee_package
    data["observations"][0]["evidence"][1].pop(field)
    with pytest.raises(ValidationError, match="hashed checked-excerpt"):
        fees.FeeReconciliation.model_validate(data)


def test_native_passage_cannot_carry_unused_review_metadata(fee_package: FeeFixture) -> None:
    _, data, _, _ = fee_package
    data["observations"][0]["evidence"][0]["checked_excerpt_id"] = "unused"
    with pytest.raises(ValidationError, match="unused review metadata"):
        fees.FeeReconciliation.model_validate(data)


@pytest.mark.parametrize("target,field,value", [
    ("package", "coverage", "complete"), ("package", "legal_currentness", "current"),
    ("package", "legal_review", "approved"), ("package", "prepared_at", "2026-09-10"),
    ("package", "observations", []), ("package", "open_chain", []),
    ("package", "sources", []), ("observation", "conditions", []),
    ("observation", "legal_review", "approved"), ("citation", "physical_page", True),
    ("citation", "method", "manual_unchecked"), ("citation", "excerpt", " "),
    ("open", "status", "closed"), ("open", "source_ids", []),
])
def test_false_completion_currentness_unchecked_text_and_empty_context_rejected(
    fee_package: FeeFixture, target: str, field: str, value: object,
) -> None:
    _, data, _, _ = fee_package
    objects = {"package": data, "observation": data["observations"][0],
               "citation": data["observations"][0]["evidence"][0], "open": data["open_chain"][0]}
    objects[target][field] = value
    with pytest.raises(ValidationError):
        fees.FeeReconciliation.model_validate(data)


@pytest.mark.parametrize("target", ["observations", "open_chain"])
def test_duplicate_identifiers_rejected(fee_package: FeeFixture, target: str) -> None:
    _, data, _, _ = fee_package
    data[target] *= 2
    with pytest.raises(ValidationError, match="unique"):
        fees.FeeReconciliation.model_validate(data)


@pytest.mark.parametrize("url", [
    "http://www.cityofgolden.gov/fee", "https://user:secret@www.cityofgolden.gov/fee",
    "https:///empty", "https://www.cityofgolden.gov:444/fee",
    "https://www.cityofgolden.gov:bad/fee", "https://www.cityofgolden.gov/a\nb",
])
def test_continuation_links_are_ordinary_https_references(
    fee_package: FeeFixture, url: str,
) -> None:
    _, data, _, _ = fee_package
    data["open_chain"][0]["observed_urls"] = [url]
    with pytest.raises(ValidationError):
        fees.FeeReconciliation.model_validate(data)


@pytest.mark.parametrize("change", ["owner", "source", "hash", "page"])
def test_citation_source_owner_hash_and_page_binding(fee_package: FeeFixture, change: str) -> None:
    root, data, _, _ = fee_package
    observation = data["observations"][0]
    citation = observation["evidence"][0]
    if change == "owner":
        observation["authority_id"] = "CO-MUNICIPAL-MISSING"
    elif change == "source":
        citation["source_id"] = "absent"
    elif change == "hash":
        citation["source_sha256"] = "f" * 64
    else:
        citation["physical_page"] = 3
    with pytest.raises(ValueError, match="authority|preserved PDF"):
        validate(data, root)


def add_other_owner(root: Path, ledger: dict) -> None:
    """Add a real ledger authority with all categories explicitly uncollected."""
    other = copy.deepcopy(ledger["authorities"][0])
    other.update(authority_id="CO-MUNICIPAL-GEORGETOWN", name="Georgetown")
    for row in other["checklist"]:
        row.update(source_ids=[], collection="missing", completeness="not_assessed")
    ledger["authorities"].append(other)
    save_ledger(root, ledger)


def test_known_foreign_authority_cannot_claim_another_owners_pdf(fee_package: FeeFixture) -> None:
    root, data, ledger, _ = fee_package
    add_other_owner(root, ledger)
    data["observations"][0]["authority_id"] = "CO-MUNICIPAL-GEORGETOWN"
    with pytest.raises(ValueError, match="owner's preserved PDF"):
        validate(data, root)


def test_native_excerpt_must_appear_on_the_exact_page(fee_package: FeeFixture) -> None:
    root, data, _, _ = fee_package
    data["observations"][0]["evidence"][0]["physical_page"] = 2
    with pytest.raises(ValueError, match="absent"):
        validate(data, root)


@pytest.mark.parametrize("change", ["hash", "id", "transcription", "source", "page"])
def test_checked_citation_is_bound_to_exact_review_record(
    fee_package: FeeFixture, change: str,
) -> None:
    root, data, _, _ = fee_package
    citation = data["observations"][0]["evidence"][1]
    if change == "hash":
        citation["checked_review_sha256"] = "f" * 64
    elif change == "id":
        citation["checked_excerpt_id"] = "unreviewed"
    elif change == "transcription":
        citation["excerpt"] = "The fee is permanently waived."
    elif change == "page":
        citation["physical_page"] = 2
    else:
        citation["source_id"] = "missing"
    with pytest.raises(ValueError, match="hash mismatch|specified checked|preserved PDF"):
        validate(data, root)


def test_changed_raw_ocr_invalidates_the_whole_checked_review(fee_package: FeeFixture) -> None:
    root, data, _, review_data = fee_package
    path = root / review_data["excerpts"][0]["ocr_page_path"]
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError, match="OCR page evidence hash mismatch"):
        validate(data, root)


@pytest.mark.parametrize("change", ["missing", "duplicate", "owner", "foreign"])
def test_open_chain_sources_remain_bound_to_the_authority(
    fee_package: FeeFixture, change: str,
) -> None:
    root, data, ledger, _ = fee_package
    item = data["open_chain"][0]
    if change == "missing":
        item["source_ids"] = ["missing"]
    elif change == "duplicate":
        item["source_ids"] *= 2
    elif change == "owner":
        item["authority_id"] = "CO-MUNICIPAL-MISSING"
    else:
        add_other_owner(root, ledger)
        item["authority_id"] = "CO-MUNICIPAL-GEORGETOWN"
    with pytest.raises(ValueError, match="authority"):
        validate(data, root)


def test_checked_review_path_symlink_is_not_followed(fee_package: FeeFixture) -> None:
    root, data, _, _ = fee_package
    path = root / data["observations"][0]["evidence"][1]["checked_review_path"]
    real = path.with_name("real.json")
    path.rename(real)
    path.symlink_to(real)
    with pytest.raises(ValueError, match="symlink"):
        validate(data, root)


def test_post_validation_forged_currentness_is_revalidated(fee_package: FeeFixture) -> None:
    root, data, _, _ = fee_package
    model = fees.FeeReconciliation.model_validate(data)
    object.__setattr__(model, "legal_currentness", "current")
    with pytest.raises(ValidationError):
        fees.validate_fee_reconciliation(model, root)


def write_study(root: Path, data: dict) -> Path:
    """Preserve a validated study file for CLI tests."""
    path = root / "research/fees/fixture-study.json"
    path.write_text(fees.FeeReconciliation.model_validate(data).model_dump_json())
    return path


def test_cli_valid_relative_and_absolute_paths(fee_package: FeeFixture) -> None:
    root, data, _, _ = fee_package
    path = write_study(root, data)
    assert fees.main(["--root", str(root), "--study", str(path.relative_to(root))]) == 0
    assert fees.main(["--root", str(root), "--study", str(path)]) == 0


@pytest.mark.parametrize("change", ["missing", "invalid", "outside", "symlink"])
def test_cli_rejects_bad_and_unconfined_inputs(fee_package: FeeFixture, change: str) -> None:
    root, data, _, _ = fee_package
    path = write_study(root, data)
    if change == "missing":
        path.unlink()
    elif change == "invalid":
        path.write_text("{invalid")
    elif change == "outside":
        path = root.parent / "outside.json"
    else:
        real = path.with_name("actual.json")
        path.rename(real)
        path.symlink_to(real)
    assert fees.main(["--root", str(root), "--study", str(path)]) == 1


def test_cli_and_checked_review_reads_are_bounded(
    fee_package: FeeFixture, monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, data, _, _ = fee_package
    path = write_study(root, data)
    monkeypatch.setattr(fees, "MAX_PACKAGE_BYTES", 10)
    assert fees.main(["--root", str(root), "--study", str(path)]) == 1
    monkeypatch.setattr(fees, "MAX_REVIEW_BYTES", 10)
    with pytest.raises(ValueError, match="read limit"):
        validate(data, root)


def test_actual_module_entrypoint_is_offline_and_successful(
    fee_package: FeeFixture, monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, data, _, _ = fee_package
    path = write_study(root, data)
    monkeypatch.setattr(
        sys, "argv", ["local_fee_review", "--root", str(root), "--study", str(path)],
    )
    with pytest.raises(SystemExit) as result:
        runpy.run_module("geode.pipeline.local_fee_review", run_name="__main__", alter_sys=True)
    assert result.value.code == 0
