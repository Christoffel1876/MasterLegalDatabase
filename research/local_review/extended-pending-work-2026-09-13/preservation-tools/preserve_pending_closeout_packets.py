"""Preserve closed review evidence without accepting pending sources or transactions."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json

from pydantic import BaseModel, ConfigDict
from preserve_watch_test_repair import File, save

BASE = Path('/Users/mcoors/Documents/Project Geode')
RUN = BASE / 'handoffs/run-2026-09-12/extended-run'
DEST = BASE / 'MasterLegalDatabase/research/local_review/extended-pending-work-2026-09-13'
PACKETS = {
    'eb023024-closeout-status':
    '3a617b4f089f3b4e9e69ee9b055908175514898dd00ee3f62fc21de6fd5b1c36',
    'sherlock-sh-ext-003-independent-audit':
    'c9326e7833b67202a96ab64326b716f71dab3f2cd6dc9b12cdcff4dfd7eb1bb9',
    'pueblo-county-fees-intake-proposal':
    'bd5fdf638f2fef30830fb2ed65b2cfe96466726a3903a98d2ad615b958eafd8c',
}


class Receipt(BaseModel):
    """Actual file preservation with all source and transaction decisions still pending."""
    model_config = ConfigDict(extra='forbid')
    preserved_at: datetime
    files: list[File]
    status: str
    canonical_writes: int = 0
    legal_currentness: str = 'not_verified'


def main() -> None:
    """Pin each closed packet and copy it unchanged as pending evidence."""
    if DEST.exists():
        raise ValueError('Existing pending-work preservation folder')
    captured = {}
    for name, digest in PACKETS.items():
        folder = RUN / name
        if hashlib.sha256((folder / 'FINAL_MANIFEST.json').read_bytes()).hexdigest() != digest:
            raise ValueError('Closed packet identity differs: ' + name)
        for path in sorted(folder.rglob('*')):
            if path.is_symlink():
                raise ValueError('Symlink in packet')
            if path.is_file():
                relative = name + '/' + path.relative_to(folder).as_posix()
                captured[relative] = (path, path.read_bytes())
    files = [File(path=name, sha256=hashlib.sha256(raw).hexdigest(), size_bytes=len(raw))
             for name, (_, raw) in captured.items()]
    receipt = Receipt(preserved_at=datetime.now(timezone.utc), files=files,
                      status='preserved_pending_source_acceptance_or_transaction_review')
    for name, (source, raw) in captured.items():
        save(DEST / name, raw)
        if source.read_bytes() != raw:
            raise ValueError('Packet changed while copied')
    save(DEST / 'PRESERVATION.schema.json',
         (json.dumps(Receipt.model_json_schema(), indent=2) + '\n').encode())
    save(DEST / 'PRESERVATION.json', (receipt.model_dump_json(indent=2) + '\n').encode())
    for helper in [Path(__file__), Path(__file__).with_name('preserve_watch_test_repair.py')]:
        save(DEST / 'preservation-tools' / helper.name, helper.read_bytes())
    save(DEST / 'README.md', b'''---
status: preserved_pending_acceptance
legal_currentness: not_verified
---
# Pending work preserved at the extended-run checkpoint

These are frozen receipts and proposals, not new accepted corpus records.

- Ebenezer 023/024: delivered and hash-checked; source judgments await Atlas review.
  Caption-mediated reopening is reported, with missing per-page execution notes.
- Sherlock SH-EXT-003: custody and metadata audit passed. Three Gunnison PDFs have
  23 pages; only three first pages were visually reviewed for document role. Two
  PDFs recover historical digests. Four corrected Chaffee targets remain unopened.
  Four cookie-bearing logs are explicitly redacted derivatives; originals remain
  untouched outside this public-ready package. Their original hashes cannot be
  reconstructed from the redacted copies.
- Pueblo County fee schedule: source-fidelity review already accepted separately;
  the one-source intake transaction is prepared and tested but has NOT been applied.
  Do not run historical apply scripts without checking the current preimages.

The manual PDF inventory remains 63 originals / 24 mapped / 39 unmapped. Copying
these packages changes none of those counts, source bytes or legal-currentness flags.
''')
    print(json.dumps({'status': receipt.status, 'files': len(files),
                      'bytes': sum(item.size_bytes for item in files)}))


if __name__ == '__main__':
    main()
