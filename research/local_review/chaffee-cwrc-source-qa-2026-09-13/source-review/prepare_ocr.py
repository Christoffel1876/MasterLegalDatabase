"""Fixed fourteen-image, on-device OCR capture; never changes source bytes."""

import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

ROOT = Path(__file__).resolve().parent


class Strict(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")


class Ref(Strict):
    path: str
    sha256: str
    size_bytes: int


class OcrLine(Strict):
    text: str
    confidence: float
    bbox: list[float] = Field(min_length=4, max_length=4)


class OcrOutput(Strict):
    revision: int
    os_version: str
    lines: list[OcrLine]


class OcrEvent(Strict):
    page: int
    image: Ref
    executable: Ref
    swift_source: Ref
    argv: list[str]
    started_at: str
    completed_at: str
    exit_code: int
    stdout: Ref
    stderr: Ref
    candidate: Ref
    method: str
    correction_performed: bool


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def ref(path: Path) -> Ref:
    data = path.read_bytes()
    return Ref(path=path.relative_to(ROOT).as_posix(), sha256=hashlib.sha256(data).hexdigest(),
               size_bytes=len(data))


def put(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() or path.is_symlink():
        raise ValueError("refuse existing output")
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("xb") as stream:
        stream.write(data)
    os.replace(temporary, path)


def main() -> None:
    executable = ROOT / "tools/apple-vision-ocr"
    source = ROOT / "tools/apple_vision_ocr.swift"
    for page in range(1, 15):
        image = ROOT / "pages" / f"page-{page:02d}.png"
        before = ref(image)
        argv = [str(executable), str(image)]
        start = now()
        result = subprocess.run(argv, capture_output=True, timeout=60, check=False)
        finish = now()
        directory = ROOT / "ocr" / f"page-{page:04d}"
        put(directory / "stdout.json", result.stdout)
        put(directory / "stderr.txt", result.stderr)
        if result.returncode != 0:
            raise ValueError(f"OCR failed page {page}; outputs preserved")
        parsed = OcrOutput.model_validate_json(result.stdout)
        candidate = "\n".join(line.text for line in parsed.lines) + "\n"
        put(directory / "candidate.txt", candidate.encode())
        if ref(image) != before:
            raise ValueError("image changed during OCR")
        event = OcrEvent(
            page=page, image=before, executable=ref(executable), swift_source=ref(source),
            argv=argv, started_at=start, completed_at=finish, exit_code=result.returncode,
            stdout=ref(directory / "stdout.json"), stderr=ref(directory / "stderr.txt"),
            candidate=ref(directory / "candidate.txt"),
            method="On-device Apple Vision accurate en-US revision3 CPU-only; language correction "
            "and automatic language detection disabled; raw observation order preserved.",
            correction_performed=False)
        put(directory / "EVENT.json", (event.model_dump_json(indent=2) + "\n").encode())
    for name, model in [("OCR_OUTPUT", OcrOutput), ("OCR_EVENT", OcrEvent)]:
        put(ROOT / f"{name}.schema.json", (json.dumps(model.model_json_schema(), indent=2) + "\n").encode())


if __name__ == "__main__":
    main()
