from pathlib import Path
from hashlib import sha256
import shutil,ast,pprint
r=Path(__file__).resolve().parent
for n in ['transaction.py','test_transaction.py']:
 p=r/n;out=r/'_SNAPSHOTS'/sha256(p.read_bytes()).hexdigest()/n;out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,out)
p=r/'transaction.py';s=p.read_text();a=s.index('RUNTIME_CODE = ');b=s.index('\n',a);pins=ast.literal_eval(s[a+len('RUNTIME_CODE = '):b]);s=s[:a]+'RUNTIME_CODE = '+pprint.pformat(pins,width=95,sort_dicts=True)+s[b:]
s=s.replace('    # Refuse concurrent changes while the isolated read-only verifier was running.','''    post_members = set()
    for member in PREP.rglob("*"):
        safe(PREP, member.relative_to(PREP).as_posix())
        if not member.is_dir() and not member.is_file():
            raise ValueError("Nonordinary preparation member after verifier")
        if member.is_file(): post_members.add(member.relative_to(PREP).as_posix())
    if post_members != expected:
        raise ValueError("Preparation membership changed during verifier")
    # Refuse concurrent changes while the isolated read-only verifier was running.''')
s=s.replace('            if path.is_symlink():\n                raise ValueError("Symlink in raw archive")','''            if path.is_symlink():
                raise ValueError("Symlink in raw archive")
            if not path.is_dir() and not path.is_file():
                raise ValueError("Nonordinary member in raw archive")''')
a=s.index('\ndef execute(')
s=s[:a]+'''
def validate_state(state: Path) -> None:
    """Reject unrelated state members and impossible orphan completion artifacts."""
    safe(state)
    if not state.exists():
        return
    if not state.is_dir():
        raise ValueError("Execution state is not a directory")
    for member in state.iterdir():
        relative = member.relative_to(state).as_posix()
        safe(state, relative)
        if relative == ".staging":
            if not member.is_dir():
                raise ValueError("State staging is not a directory")
            for staged in member.iterdir():
                if not staged.name.startswith("staged-") or not staged.is_file():
                    raise ValueError("Unrelated staging member")
                safe(state, staged.relative_to(state).as_posix())
        elif relative not in {"INTENT.json", "records.jsonl", "RECEIPT.json",
                              "transaction.lock"} or not member.is_file():
            raise ValueError("Unrelated or nonordinary execution state member")
    if not (state / "INTENT.json").exists() and any(
        (state / p).exists() for p in ("records.jsonl", "RECEIPT.json")
    ):
        raise ValueError("Orphan suffix or receipt without intent")

'''+s[a:]
s=s.replace('    safe(root); safe(state)\n    checkpoint', '    safe(root); validate_state(state)\n    checkpoint')
s=s.replace('        # Reload state under the lock; pre-lock observations do not authorize writes.','''        validate_state(state)
        # Reload state under the lock; pre-lock observations do not authorize writes.''')
p.write_text(s)
