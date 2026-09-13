"""Preserve and close the independently reproduced metadata reread gap."""
from pathlib import Path
import hashlib,os
p=Path(__file__).with_name('transaction.py');old=p.read_bytes();snap=p.parent/'preparation-history'/hashlib.sha256(old).hexdigest();snap.mkdir(parents=True,exist_ok=True);(snap/'transaction.py').write_bytes(old)
s=old.decode();a=s.index('def load_plan(');b=s.index('\ndef rows(',a)
s=s[:a]+'''def load_plan(root: Path) -> Plan:
    """Consume captured root-verified bytes instead of running the prior verifier.

    Root separately reviewed this frozen source evidence. Pin the manifest and all
    members here, then consume those exact buffers without rereading metadata. Final
    request/record validation and fresh source-byte checks still run before writes.
    The predecessor's embedded verifier adds no custody evidence to this preflight.
    """
    safe(root)
    captured = {}
    for name, expected in [
        ("PREPARATION.json", PREP_SHA),
        ("FINAL_MANIFEST.json", MANIFEST_SHA),
    ]:
        path = safe(PREP, name)
        if not path.is_file():
            raise ValueError("Unapproved preparation: " + name)
        content = path.read_bytes()
        if digest(content) != expected:
            raise ValueError("Unapproved preparation: " + name)
        captured[name] = content
    manifest = json.loads(captured["FINAL_MANIFEST.json"])
    expected_members = {item["path"] for item in manifest["files"]} | {
        "FINAL_MANIFEST.json",
        "FINAL_MANIFEST.schema.json",
    }
    actual_members = set()
    for path in PREP.rglob("*"):
        relative = path.relative_to(PREP).as_posix()
        safe(PREP, relative)
        if not path.is_file() and not path.is_dir():
            raise ValueError("Nonordinary preparation member")
        if path.is_file():
            actual_members.add(relative)
    if actual_members != expected_members:
        raise ValueError("Preparation membership changed")
    for item in manifest["files"]:
        file = File.model_validate(item)
        if file.path not in captured:
            captured[file.path] = checked(PREP, file)
        elif ref(file.path, captured[file.path]) != file:
            raise ValueError("Conflicting preparation file pins")
    data = json.loads(captured["PREPARATION.json"])
    before, guards = {}, []
    for baseline in data["baseline"]:
        file = File.model_validate(baseline["preserved"])
        content = captured[file.path]
        if ref(file.path, content) != file:
            raise ValueError("Baseline binding differs from captured input")
        if baseline["repository_path"] in TARGETS:
            before[baseline["repository_path"]] = content
        else:
            guards.append(ref(baseline["repository_path"], content))
    return Plan(
        PREP_SHA,
        digest(captured["source-provenance.jsonl"]),
        tuple(data["sources"]),
        tuple(data["proposed_records"]),
        PREP,
        before,
        tuple(guards),
    )

'''+s[b:]
# Only readability wrapping; no logic changes to these existing operations.
s=s.replace('"""Guarded Douglas County / Pueblo City official-PDF transaction. Defaults to a strictly read-only dry run."""','"""Guarded Douglas County / Pueblo City official-PDF intake; read-only by default."""')
s=s.replace('        request_fields["source_file"] = str(plan.originals_root / source["original"]["path"])','        request_fields["source_file"] = str(\n            plan.originals_root / source["original"]["path"]\n        )')
s=s.replace('            intake_id=f"MSI-{stamp}-{sid}", record_id=sid, layer_id=template["layer_id"],','            intake_id=f"MSI-{stamp}-{sid}",\n            record_id=sid,\n            layer_id=template["layer_id"],')
s=s.replace('            boundary="Direct Atlas official HTTP source evidence only; acquisition interval remains in "','            boundary="Direct Atlas official HTTP source evidence only; "\n            "acquisition interval remains in "')
s=s.replace('            "custody_note. legal_currentness=not_verified, answer_safe=false. No rule or coverage promotion.",','            "custody_note. legal_currentness=not_verified, answer_safe=false. "\n            "No rule or coverage promotion.",')
s=s.replace('        intent = Intent.model_validate_json(intent_path.read_bytes()) if intent_path.exists() else None','        intent = (\n            Intent.model_validate_json(intent_path.read_bytes())\n            if intent_path.exists()\n            else None\n        )')
s=s.replace('            checked(root, File(path=record.archive_path, sha256=record.sha256, size_bytes=record.size_bytes))','            checked(\n                root,\n                File(\n                    path=record.archive_path,\n                    sha256=record.sha256,\n                    size_bytes=record.size_bytes,\n                ),\n            )')
s=s.replace('                full_corpus_validation="not_run_by_this_transaction", legal_currentness="not_verified",','                full_corpus_validation="not_run_by_this_transaction",\n                legal_currentness="not_verified",')
t=p.with_name('.transaction.py.tmp');t.write_text(s);os.replace(t,p)
print('Remaining over100:',[(n,len(x),x) for n,x in enumerate(s.splitlines(),1) if len(x)>100])
