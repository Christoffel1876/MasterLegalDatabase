"""Local derivation receipts, including exact retention of the failed first OCR attempt."""
from typing import Literal
from models import Asset, Strict


class Attempt(Strict):
    """An actual command receipt with explicit retention-path mapping."""
    label: str
    page: int
    receipt: Asset
    retained_stdout: Asset
    retained_stderr: Asset
    original_paths_relocated: bool
    note: str


class Derivation(Strict):
    """Known local engine settings and complete candidate outcomes."""
    source_sha256: str
    poppler_binary_sha256: str
    poppler_version_output: Asset
    render_dpi: Literal[150]
    pymupdf_version: str
    ocr_binary: Asset
    ocr_swift: Asset
    os_version_reported: str
    vision_revision: Literal[3]
    recognition_level: Literal['accurate']
    languages: list[str]
    language_correction: Literal[False]
    automatic_language_detection: Literal[False]
    minimum_text_height: Literal[0]
    cpu_only: Literal[True]
    initial_failed_attempt: Attempt
    successful_attempts: list[Attempt]
    method_limits: list[str]
