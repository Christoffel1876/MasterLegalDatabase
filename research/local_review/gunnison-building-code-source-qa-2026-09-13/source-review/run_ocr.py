"""Run the retained local OCR engine once per source image, preserving all results."""
from datetime import datetime, timezone
from pathlib import Path
import subprocess
from models import OCRResult, ProcessReceipt
from prepare import ROOT, asset, write


def main() -> None:
    """Preserve complete machine output without corrections or truncation."""
    for number in range(1, 17):
        command = [str(ROOT / 'tools/apple-vision-ocr'),
                   str(ROOT / f'pages/page-{number:02}.png')]
        started = datetime.now(timezone.utc).isoformat()
        result = subprocess.run(command, capture_output=True, timeout=90)
        completed = datetime.now(timezone.utc).isoformat()
        output = ROOT / f'ocr/page-{number:04}.json'
        error = ROOT / f'ocr/page-{number:04}.stderr'
        write(output, result.stdout)
        write(error, result.stderr)
        receipt = ProcessReceipt(started_at=started, completed_at=completed,
                                 command=command, returncode=result.returncode,
                                 stdout=asset(output), stderr=asset(error))
        write(ROOT / f'ocr/receipt-{number:04}.json',
              (receipt.model_dump_json(indent=2) + '\n').encode())
        if result.returncode:
            raise RuntimeError(f'OCR failed on page {number}; original attempt retained')
        parsed = OCRResult.model_validate_json(result.stdout)
        text = '\n'.join(line.text for line in parsed.lines) + '\n'
        write(ROOT / f'ocr/page-{number:04}.txt', text.encode())


if __name__ == '__main__':
    main()
