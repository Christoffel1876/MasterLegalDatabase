"""Identify unavailable Git LFS content without downloading or changing files."""

from __future__ import annotations

import re
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

LFS_VERSION = b"version https://git-lfs.github.com/spec/v1"
POINTER_READ_LIMIT = 4096


class LfsPointer(BaseModel):
    """Declared object identity, not a verification of recovered source bytes."""

    model_config = ConfigDict(extra="forbid", strict=True)

    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(ge=0)


class UnhydratedLfsPointerError(ValueError):
    """Report an on-disk pointer where actual artifact content is required."""

    def __init__(self, path: Path, pointer: LfsPointer) -> None:
        self.path = path
        self.pointer = pointer
        super().__init__(
            f"Git LFS content unavailable at {path}: pointer declares "
            f"sha256:{pointer.sha256}, {pointer.size_bytes} bytes; "
            "the original content is not present in this file"
        )


def require_hydrated_file(path: Path) -> None:
    """Reject a literal LFS pointer while reading only a bounded file prefix.

    Non-pointer files are not otherwise validated. A malformed pointer header
    fails closed; it is never interpreted as a valid original or fetched here.
    """

    with path.open("rb") as handle:
        prefix = handle.read(POINTER_READ_LIMIT + 1)
    lines = prefix.splitlines()
    if not lines or lines[0] != LFS_VERSION:
        return
    if len(prefix) > POINTER_READ_LIMIT:
        raise ValueError(f"Malformed or oversized Git LFS pointer at {path}")
    oid_lines = [line for line in lines[1:] if line.startswith(b"oid ")]
    size_lines = [line for line in lines[1:] if line.startswith(b"size ")]
    if (
        len(oid_lines) != 1
        or len(size_lines) != 1
        or not re.fullmatch(rb"oid sha256:[0-9a-f]{64}", oid_lines[0])
        or not re.fullmatch(rb"size [0-9]+", size_lines[0])
    ):
        raise ValueError(f"Malformed Git LFS pointer at {path}")
    pointer = LfsPointer(
        sha256=oid_lines[0].removeprefix(b"oid sha256:").decode("ascii"),
        size_bytes=int(size_lines[0].removeprefix(b"size ")),
    )
    raise UnhydratedLfsPointerError(path, pointer)
