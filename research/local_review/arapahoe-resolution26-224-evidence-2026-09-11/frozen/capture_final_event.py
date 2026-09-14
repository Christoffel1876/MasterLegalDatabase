"""One bounded ordinary GET of the observed official Resolution attachment."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import os
import subprocess

from pydantic import BaseModel, ConfigDict


class Capture(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    event_id: str
    requested_url: str
    started_at: datetime
    completed_at: datetime
    curl_exit_code: int
    http_status: int | None
    effective_url: str | None
    redirect_url: str | None
    content_type: str | None
    response_files: dict[str, dict[str, str | int]]
    policy: str


P = Path(__file__).absolute().parent
url = 'https://arapahoe.legistar.com/View.ashx?GUID=E4F2D438-01EB-4B24-B6DD-6E13EEB14FDB&ID=15828215&M=F'
assert not (P / 'E008.json').exists()
start = datetime.now(timezone.utc)
assert start < datetime(2026, 9, 11, 20, 15, tzinfo=timezone.utc)
command = ['/usr/bin/curl', '--silent', '--show-error', '--connect-timeout', '10',
           '--max-time', '30', '--max-filesize', '20971520', '--max-redirs', '0',
           '--user-agent', 'Project Geode public-source research',
           '--dump-header', str(P / 'http/E008.headers'),
           '--output', str(P / 'http/E008.body'), '--write-out', '%{json}', url]
result = subprocess.run(command, capture_output=True)
end = datetime.now(timezone.utc)
(P / 'http/E008.curl-metrics.txt').write_bytes(result.stdout)
(P / 'http/E008.stderr').write_bytes(result.stderr)
metrics = json.loads(result.stdout)
files = {}
for name in ['E008.body', 'E008.headers', 'E008.curl-metrics.txt', 'E008.stderr']:
    path = P / 'http' / name
    if not path.exists():
        path.write_bytes(b'')
    data = path.read_bytes()
    files[name] = {'path': str(path.relative_to(P)), 'size_bytes': len(data),
                   'sha256': hashlib.sha256(data).hexdigest()}
record = Capture(event_id='E008', requested_url=url, started_at=start, completed_at=end,
                 curl_exit_code=result.returncode, http_status=metrics.get('http_code') or None,
                 effective_url=metrics.get('url_effective'),
                 redirect_url=metrics.get('redirect_url'),
                 content_type=metrics.get('content_type'), response_files=files,
                 policy='One ordinary GET; default TLS verification; no credentials, redirects, retries, or identity changes. Final public event of this bounded task.')
for name, data in [('E008.json', record.model_dump_json(indent=2) + '\n'),
                   ('E008.schema.json', json.dumps(Capture.model_json_schema(), indent=2) + '\n')]:
    target = P / name
    temporary = target.with_name(target.name + '.tmp')
    temporary.write_text(data)
    os.replace(temporary, target)
print(json.dumps({'event_id': 'E008', 'http_status': record.http_status,
                  'curl_exit_code': result.returncode, 'content_type': record.content_type,
                  'body': files['E008.body']}, indent=2))
