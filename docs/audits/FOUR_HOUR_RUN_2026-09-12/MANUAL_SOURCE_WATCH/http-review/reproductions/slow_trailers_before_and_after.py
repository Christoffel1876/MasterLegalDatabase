import importlib.util,socket,http.client,threading,time,tempfile,sys
from pathlib import Path
from datetime import datetime,timezone
from types import SimpleNamespace
ROOT=Path('/Users/mcoors/Documents/Project Geode/MasterLegalDatabase');sys.path.insert(0,str(ROOT))
s=importlib.util.spec_from_file_location('fixture',ROOT/'tests/test_manual_source_watch.py');t=importlib.util.module_from_spec(s);s.loader.exec_module(t)
from geode.pipeline import manual_source_watch as w
from geode.pipeline import manual_watch_http as g
with tempfile.TemporaryDirectory(prefix='watch-slow-',dir='/private/tmp') as d:
    root=t.packet.__wrapped__(Path(d));t.change_plan(root,lambda p:p['limits'].update(request_seconds=1))
    body=t.bodies(root)[0];reader,writer=socket.socketpair()
    def send():
        try:
            writer.sendall(b'HTTP/1.1 200 OK\r\nConnection: close\r\nContent-Type: application/pdf\r\nTransfer-Encoding: chunked\r\n\r\n'+hex(len(body))[2:].encode()+b'\r\n'+body+b'\r\n0\r\n')
            for n in range(9):
                time.sleep(.2);writer.sendall(b'X-Trailer: ignored\r\n')
            writer.sendall(b'\r\n')
        finally:writer.close()
    thread=threading.Thread(target=send);thread.start()
    raw=http.client.HTTPResponse(reader);raw.begin()
    response=g.Response(SimpleNamespace(close=reader.close),raw,reader)
    replies=[response,t.Response(t.bodies(root)[1])]
    start=datetime.now(timezone.utc);output=root/w.RUNTIME/'slow-trailer'
    report=w.run_watch(root/w.SELECTION,output,start,g.sha(root/w.SELECTION),fetch=lambda *a:replies.pop(0))
    first=g.Result.model_validate_json((output/'events/0001/result.json').read_bytes());res=g.Reservation.model_validate_json((output/'events/0001/reservation.json').read_bytes())
    print('request_seconds=1; actual elapsed',(first.finished_at-res.reserved_at).total_seconds(),'outcome',first.outcome,'partial',first.partial_body)
    print('adapter',report.status,report.observations[0].status,'past deadline',(first.finished_at-res.deadline).total_seconds())
    print('verify',w.verify_run(root/w.SELECTION,output).status)
    thread.join()
