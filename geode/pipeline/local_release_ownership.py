"""Follow explicit active-record relationships before releasing local evidence."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from geode.pipeline.local_source_ownership import OwnershipPolicy

_IDENTITY_FIELDS = (
    "id", "rule_unit_id", "candidate_rule_unit_id", "permanent_rule_unit_id",
    "parent_rule_id", "parent_regulation_id", "review_id", "source_id",
)
_NESTED_FIELDS = ("candidate_rule_unit", "source", "source_metadata", "metadata")


def ownership_reason_with_parents(
    policy: OwnershipPolicy,
    row: Mapping[str, Any],
    indexed_rows: Mapping[str, Mapping[str, Any]],
) -> str | None:
    """Check this record and reachable active identities without transferring ownership.

    Only explicit identity fields and documented numeric unit suffixes are followed.
    Missing active records do not imply ownership approval or source validation.
    Cyclic metadata and parent references terminate without hiding other references.
    """

    pending = [row]
    seen_rows: set[int] = set()
    seen_ids: set[str] = set()
    while pending:
        current = pending.pop()
        if id(current) in seen_rows:
            continue
        seen_rows.add(id(current))
        reason = policy.entity_exclusion_reason(current)
        if reason:
            return reason
        for key in _NESTED_FIELDS:
            child = current.get(key)
            if isinstance(child, Mapping):
                pending.append(child)
        for key in _IDENTITY_FIELDS:
            identity = str(current.get(key) or "")
            if not identity:
                continue
            normalized = identity.removeprefix("CONDITIONAL-")
            parent = re.sub(
                r"(?:-UNIT-|_RU_)\d+$", "", normalized.removeprefix("COUNTY-SEM-")
            )
            references = [identity, normalized]
            if parent != normalized.removeprefix("COUNTY-SEM-"):
                references.append(parent)
            for reference in references:
                if reference in seen_ids:
                    continue
                seen_ids.add(reference)
                active = indexed_rows.get(reference)
                if active is not None:
                    pending.append(active)
    return None
