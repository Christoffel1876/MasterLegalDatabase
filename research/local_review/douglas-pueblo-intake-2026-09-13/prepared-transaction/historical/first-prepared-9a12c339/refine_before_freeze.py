"""Preserve builder history and refine the new, unapplied preparation only."""
from pathlib import Path
import hashlib,os
p=Path(__file__).with_name('prepare.py');b=p.read_bytes();snap=p.parent/'preparation-history'/hashlib.sha256(b).hexdigest();snap.mkdir(parents=True,exist_ok=True);(snap/'prepare.py').write_bytes(b)
s=b.decode().replace('Evidence: handoffs/run-2026-09-12/final-two-source-intake/evidence/preparation/custody/', 'Evidence: research/local_review/douglas-pueblo-intake-2026-09-13/prepared-transaction/evidence/preparation/custody/')
s=s.replace("code=code.replace('layer_id: Literal", "code=code.replace('VERIFIER_SHA = \\\"a9c665796a66e8282491e6eb732fa6abb673b5df8d503a79fcc553c64954df8e\\\"\\n','')\ncode=code.replace('layer_id: Literal") if False else s
needle="code=code.replace('f\"_RAW_ARCHIVE/manual_intake/10_Municipal_Authorities/{sid}/\"'"
pos=s.index(needle)
s=s[:pos]+"code=code.replace('(source[\\\"authority_id\\\"], source[\\\"layer_id\\\"]) not in {(\\\"CO-COUNTY-DOUGLAS\\\", \\\"08_County_Authorities\\\"), (\\\"CO-MUNICIPAL-PUEBLO\\\", \\\"10_Municipal_Authorities\\\")}', '(source[\\\"authority_id\\\"], source[\\\"layer_id\\\"]) != {\\\"douglas-ehs-fees-atlas-directed\\\": (\\\"CO-COUNTY-DOUGLAS\\\", \\\"08_County_Authorities\\\"), \\\"pueblo-planning-fees-atlas-directed\\\": (\\\"CO-MUNICIPAL-PUEBLO\\\", \\\"10_Municipal_Authorities\\\")}.get(sid)')\n"+s[pos:]
s=s.replace("put('test_transaction.py',tests.encode())", "tests=tests.replace('sid = f\\\"fixture-new-{i:02}\\\"', 'sid = [\\\"douglas-ehs-fees-atlas-directed\\\", \\\"pueblo-planning-fees-atlas-directed\\\"][i]').replace('fixture-new-00',ids[0]).replace('fixture-new-01',ids[1])\nput('test_transaction.py',tests.encode())")
tmp=p.with_name('.prepare.py.tmp');tmp.write_text(s);os.replace(tmp,p)
print('Builder refinement preserved',snap)
