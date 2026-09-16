"""Bounded original regression rechecks; actual transport is always local/injected."""
import importlib.util,json,tempfile,sys,socket,http.client,threading,time,hashlib
from pathlib import Path
from unittest.mock import patch
from datetime import datetime,timezone
from types import SimpleNamespace
ROOT=Path('/Users/mcoors/Documents/Project Geode/MasterLegalDatabase');sys.path.insert(0,str(ROOT))
spec=importlib.util.spec_from_file_location('fixtures',ROOT/'tests/test_manual_source_watch.py');t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)
from geode.pipeline import manual_source_watch as w
from geode.pipeline import manual_watch_http as g
identities={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(w.__file__),Path(g.__file__)]}
results=[]
with tempfile.TemporaryDirectory(prefix='watch-final-seal-',dir='/private/tmp') as d:
    root=t.packet.__wrapped__(Path(d));output=root/w.RUNTIME/'fixture'
    with patch.object(w,'seal',side_effect=OSError('simulated interrupted sealing')):
        try:t.run(root,[t.Response(x) for x in t.bodies(root)])
        except OSError:pass
        else:raise AssertionError('seal interruption absent')
    assert (output/'report.json').exists() and not (output/'RUN_MANIFEST.json').exists()
    bodies_before={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in output.glob('events/*/body.bin')}
    report,calls=t.run(root,[])
    assert not calls and report.status=='completed' and w.verify_run(root/w.SELECTION,output)==report
    assert all(hashlib.sha256(p.read_bytes()).hexdigest()==sha for p,sha in bodies_before.items())
    results.append({'case':'interrupted_final_seal','result':'completed verified seal recovered; zero extra requests; body bytes unchanged'})
with tempfile.TemporaryDirectory(prefix='watch-final-expiry-',dir='/private/tmp') as d:
    root=t.packet.__wrapped__(Path(d));output=root/w.RUNTIME/'expiry';calls=[]
    sequence=iter([t.NOW,t.NOW.replace(minute=16),t.NOW.replace(minute=16)])
    report=w.run_watch(root/w.SELECTION,output,t.NOW,g.sha(root/w.SELECTION),clock=lambda:next(sequence),fetch=lambda *a:calls.append(a))
    assert not calls and report.status=='stopped' and (output/'run.json').is_file()
    assert w.verify_run(root/w.SELECTION,output)==report
    results.append({'case':'deadline_during_initialization','result':'zero-request stopped report has run.json and verifies'})
with tempfile.TemporaryDirectory(prefix='watch-final-trailer-',dir='/private/tmp') as d:
    root=t.packet.__wrapped__(Path(d));t.change_plan(root,lambda p:p['limits'].update(request_seconds=1))
    body=t.bodies(root)[0];reader,writer=socket.socketpair();stop=threading.Event()
    def send():
        try:
            writer.sendall(b'HTTP/1.1 200 OK\r\nConnection: close\r\nContent-Type: application/pdf\r\nTransfer-Encoding: chunked\r\n\r\n'+hex(len(body))[2:].encode()+b'\r\n'+body+b'\r\n0\r\n')
            for _ in range(12):
                if stop.wait(.2):break
                writer.sendall(b'X-Trailer: ignored\r\n')
            if not stop.is_set():writer.sendall(b'\r\n')
        except OSError:pass
        finally:writer.close()
    thread=threading.Thread(target=send);thread.start()
    raw=http.client.HTTPResponse(reader);raw.begin();wrapped=g.Response(SimpleNamespace(close=reader.close),raw,reader)
    replies=[wrapped,t.Response(t.bodies(root)[1])];output=root/w.RUNTIME/'slow'
    try:
        report=w.run_watch(root/w.SELECTION,output,g.utcnow(),g.sha(root/w.SELECTION),fetch=lambda *a:replies.pop(0))
        event=g.Result.model_validate_json((output/'events/0001/result.json').read_bytes());reservation=g.Reservation.model_validate_json((output/'events/0001/reservation.json').read_bytes())
        assert event.outcome=='timeout' and event.partial_body
        assert report.status=='stopped' and report.observations[0].status=='transport_error'
        assert w.verify_run(root/w.SELECTION,output)==report
        assert (output/event.body.path).read_bytes()==body
        results.append({'case':'slow_chunk_trailers','result':'timeout/partial; adapter stopped/transport_error; exact prior body retained; stopped report verifies','elapsed_seconds':(event.finished_at-reservation.reserved_at).total_seconds()})
    finally:
        stop.set();thread.join(timeout=2);assert not thread.is_alive();reader.close()
assert identities=={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(w.__file__),Path(g.__file__)]},'code changed during check'
print(json.dumps({'hashes':identities,'results':results,'public_requests':0},indent=2))
