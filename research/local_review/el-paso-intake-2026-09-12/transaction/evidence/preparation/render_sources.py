"""Render fixed source front pages without changing original PDF bytes."""
from pathlib import Path
import concurrent.futures, json, os, subprocess
import pymupdf
BASE=Path(__file__).resolve().parent
AUDIT=json.loads((BASE/'inputs/audit/AUDIT.json').read_bytes())
BIN='/Users/mcoors/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/override/pdftoppm'
def render(s):
    sid=s['proposed_source_id'];pdf=BASE/'sources'/sid/'original.pdf'
    with pymupdf.open(pdf) as d:
        text=d[0].get_text('text',flags=195,sort=False)
        (BASE/'native'/f'{sid}-p001.txt').write_bytes(text.encode())
    env={**os.environ,'FONTCONFIG_FILE':str(BASE/'fontconfig.xml')}
    r=subprocess.run([BIN,'-f','1','-l','1','-r','144','-png',str(pdf),str(BASE/'images'/sid)],env=env,capture_output=True,timeout=90)
    (BASE/'render-logs'/f'{sid}.stderr').write_bytes(r.stderr)
    if r.returncode: raise ValueError(sid)
    return sid
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
    for sid in ex.map(render,AUDIT['pdf_intake_proposals']): print(sid)
