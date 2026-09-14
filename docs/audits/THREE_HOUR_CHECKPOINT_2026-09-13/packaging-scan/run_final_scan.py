"""Capture the single authorized read-only final scanner invocation."""
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json
import subprocess
import sys

import jsonschema
from pydantic import BaseModel, ConfigDict

ROOT = Path(__file__).resolve().parent


class Run(BaseModel):
    """Actual bounded local scanner invocation; no staging claim."""

    model_config = ConfigDict(extra='forbid', strict=True)
    started_at: str
    finished_at: str
    argv: list[str]
    exit_code: int
    scanner_sha256: str
    approvals_sha256: str
    stdout_sha256: str
    stderr_sha256: str
    git_mutations: int
    public_requests: int


command = [sys.executable, '-B', str(ROOT/'FINAL_SCANNER.py'), 'final-ci-installed']
start = datetime.now(timezone.utc).isoformat()
result = subprocess.run(command, capture_output=True, check=False, timeout=240)
end = datetime.now(timezone.utc).isoformat()
(ROOT/'scan.stdout.log').write_bytes(result.stdout)
(ROOT/'scan.stderr.log').write_bytes(result.stderr)
receipt = Run(started_at=start, finished_at=end, argv=command, exit_code=result.returncode,
              scanner_sha256=sha256((ROOT/'FINAL_SCANNER.py').read_bytes()).hexdigest(),
              approvals_sha256=sha256((ROOT/'APPROVALS.json').read_bytes()).hexdigest(),
              stdout_sha256=sha256(result.stdout).hexdigest(),
              stderr_sha256=sha256(result.stderr).hexdigest(), git_mutations=0, public_requests=0)
schema = Run.model_json_schema()
raw = receipt.model_dump_json(indent=2)+'\n'
jsonschema.validate(json.loads(raw), schema)
(ROOT/'RUN.schema.json').write_text(json.dumps(schema, indent=2)+'\n')
with (ROOT/'RUN.json').open('x') as handle:
    handle.write(raw)
sys.stdout.write(result.stdout.decode())
sys.stderr.write(result.stderr.decode())
raise SystemExit(result.returncode)
