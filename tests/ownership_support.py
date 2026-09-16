"""Explicit ownership-policy setup for local-pipeline test projects."""

from pathlib import Path

import pytest

from geode.pipeline.local_source_ownership import POLICY_PATH, OwnershipPolicy


@pytest.fixture(autouse=True)
def ownership_policy(tmp_path: Path) -> OwnershipPolicy:
    """Install validated, real retirement evidence in each local test project."""

    source = Path(__file__).resolve().parents[1] / POLICY_PATH
    data = source.read_bytes()
    policy = OwnershipPolicy.model_validate_json(data)
    target = tmp_path / POLICY_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return policy
