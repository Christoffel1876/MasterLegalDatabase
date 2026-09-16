import importlib.util, json, tempfile
from pathlib import Path
from unittest.mock import patch
ROOT=Path('/Users/mcoors/Documents/Project Geode/MasterLegalDatabase')
import sys
sys.path.insert(0,str(ROOT))
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
h=module('http_fixture',ROOT/'tests/test_manual_watch_http.py')
w=module('watch_fixture',ROOT/'tests/test_manual_source_watch.py')
from geode.pipeline import manual_source_watch as adapter
with tempfile.TemporaryDirectory(prefix='watch-review-',dir='/private/tmp') as d:
    parent=Path(d)
    path, output=h.package(parent,{'bytes_per_source':4})
    wire=h.wire_response(b'HTTP/1.1 200 OK\r\nConnection: close\r\nTransfer-Encoding: chunked\r\nContent-Length: 4\r\n\r\n8\r\nabcdefgh\r\n0\r\n\r\n')
    guard,calls=h.execute(path,output,[wire,h.FakeResponse()]);guard.execute(h.NOW)
    result=guard.ledger()[0][1]
    print(json.dumps({'case':'TE+CL truncated at cap','outcome':result.outcome,'partial':result.partial_body,'retained':(output/result.body.path).read_text(),'http_chunked_body_length':8,'charged':result.charged_bytes}))
with tempfile.TemporaryDirectory(prefix='watch-review-',dir='/private/tmp') as d:
    root=w.packet.__wrapped__(Path(d))
    real_seal=adapter.seal
    with patch.object(adapter,'seal',side_effect=OSError('offline simulated report-seal interruption')):
        try:w.run(root,[w.Response(x) for x in w.bodies(root)])
        except OSError as e:print('seal first:',str(e))
    output=root/adapter.RUNTIME/'fixture'
    print('seal evidence: report', (output/'report.json').exists(),'manifest', (output/'RUN_MANIFEST.json').exists())
    try:w.run(root,[])
    except Exception as e:print('seal replay:',type(e).__name__,str(e))
with tempfile.TemporaryDirectory(prefix='watch-review-',dir='/private/tmp') as d:
    root=w.packet.__wrapped__(Path(d)); calls=[]
    times=iter([w.NOW,w.NOW.replace(minute=16),w.NOW.replace(minute=16)])
    clock=lambda:next(times)
    try:
        report=adapter.run_watch(root/adapter.SELECTION,root/adapter.RUNTIME/'deadline',w.NOW,adapter.g.sha(root/adapter.SELECTION),clock=clock,fetch=lambda *a:calls.append(a))
        print('expiry produced report:',report.status,'requests',len(calls))
        adapter.verify_run(root/adapter.SELECTION,root/adapter.RUNTIME/'deadline')
    except Exception as e:print('expiry verification:',type(e).__name__,str(e))
