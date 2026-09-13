"""Strict closed-manifest contract for the completed final scanner run."""
from pydantic import AwareDatetime, BaseModel, ConfigDict

from prepare_final import Ref


class Manifest(BaseModel):
    """Exact local scan and preparation payloads, excluding this manifest itself."""

    model_config = ConfigDict(extra='forbid', strict=True)
    recorded_at: AwareDatetime
    status: str
    files: list[Ref]
