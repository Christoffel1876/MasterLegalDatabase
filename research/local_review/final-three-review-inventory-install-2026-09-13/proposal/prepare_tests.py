"""Prepare maintained test updates without editing the maintained suite."""
from pathlib import Path
HERE=Path(__file__).resolve().parent
p=HERE/'proposed/test_manual_review_inventory.py'
s=(HERE/'preimages/test_manual_review_inventory.py').read_text()
s=s.replace('len(new.sources) == 63','len(new.sources) == 64')
s=s.replace('(new.rows_with_review, new.rows_without_review) == (24, 39)', '(new.rows_with_review, new.rows_without_review) == (27, 37)')
s=s.replace('len(new_plan.reviews) == 24','len(new_plan.reviews) == 27')
s=s.replace('len(plan.reviews) == 24','len(plan.reviews) == 27')
s=s.replace('len(plan.authorities) == 63','len(plan.authorities) == 64')
s=s.replace('assert row == previous[row.record_id]', 'assert _before_final_reviews(row) == previous[row.record_id]')
s=s.replace('assert new.sources[:61] == old.sources', 'assert [_before_final_reviews(r) for r in new.sources[:61]] == old.sources')
s=s.replace('new.sources[61:]', 'new.sources[61:63]')
s=s.replace('    if row.record_id != "el-paso-boh-ehs-fees-sd011":', '    row = _before_final_reviews(row)\n    if row.record_id != "el-paso-boh-ehs-fees-sd011":')
s=s.replace('        else:\n            assert row.reviews is None and row.review_status == "metadata_only_review_unknown"', '        elif row.record_id == "el-paso-boh-bylaws-sd011":\n            assert len(row.reviews) == 1 and row.reviews[0].review_kind == "checked_passages"\n        else:\n            assert row.reviews is None and row.review_status == "metadata_only_review_unknown"',1)
s += '''

FINAL_REVIEW_IDENTITIES = {
    "larimer-equity-fee-memo-sd007-05": (
        "20f268b2f632d655d25d739002f43b67654c9ce351ca8b6a5bdebac107baa92d",
        "checked_tables"),
    "el-paso-boh-bylaws-sd011": (
        "8a3d6f2c37fbacacc104ce3fd0dba53806157858f4cb487caf44f1a511657ec6",
        "checked_passages"),
}


def _before_final_reviews(row: inventory.SourceRow) -> inventory.SourceRow:
    """Remove only two exact later reviews for historical metadata equality checks."""
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
    assert (len(new.sources), new.rows_with_review, new.rows_without_review) == (64, 27, 37)
    assert plan.authorities[:63] == old_plan.authorities and len(plan.authorities) == 64
    assert plan.reviews[:24] == old_plan.reviews and len(plan.reviews) == 27
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
'''
p.write_text(s)
