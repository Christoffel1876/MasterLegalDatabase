"""Verify this immutable local preparation; performs no public actions."""
from pathlib import Path
import json,hashlib
P=Path(__file__).absolute().parent
m=json.loads((P/'FINAL_MANIFEST.json').read_bytes())
expected={x['path'] for x in m['files']}
actual={str(x.relative_to(P)) for x in P.rglob('*') if x.is_file() and '__pycache__' not in x.parts and x!=P/'FINAL_MANIFEST.json'}
if actual!=expected:raise ValueError('Closed file set differs')
for row in m['files']:
 f=P/row['path']
 if f.is_symlink() or f.stat().st_size!=row['size_bytes'] or hashlib.sha256(f.read_bytes()).hexdigest()!=row['sha256']:raise ValueError(row['path'])
from models import Reservation,Result,ActionLog
for c in [Reservation,Result,ActionLog]:
 if json.loads((P/(c.__name__+'.schema.json')).read_bytes())!=c.model_json_schema():raise ValueError('Schema differs')
print('PASS: exact closed packet and schemas; zero public requests by verifier.')
