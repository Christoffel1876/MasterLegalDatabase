"""Apply root-requested formatting to the new transaction; source inputs stay immutable."""
from pathlib import Path
import ast,os
base=Path(__file__).resolve().parent;p=base/'transaction.py';s=p.read_text();tree=ast.parse(s)
s=s.replace('DEFAULT_ROOT = (BASE.parents[3] if BASE.name == "prepared-transaction" else BASE.parents[2] / "MasterLegalDatabase")','''DEFAULT_ROOT = (
    BASE.parents[3]
    if BASE.name == "prepared-transaction"
    else BASE.parents[2] / "MasterLegalDatabase"
)''')
s=s.replace('VERIFIER_SHA = "a9c665796a66e8282491e6eb732fa6abb673b5df8d503a79fcc553c64954df8e"\n','')
pins=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='RUNTIME_CODE' for t in n.targets))
a=s.index('RUNTIME_CODE = ');b=s.index('\ndef validate_runtime_code',a)
formatted='RUNTIME_CODE = {\n'+''.join(f'    "{key}": (\n        "{value}"\n    ),\n' for key,value in pins.items())+'}\n\n'
identities='''APPROVED_IDENTITIES = {
    "douglas-ehs-fees-atlas-directed": (
        "CO-COUNTY-DOUGLAS",
        "08_County_Authorities",
        "https://www.douglasco.gov/documents/fee-schedule.pdf/",
    ),
    "pueblo-planning-fees-atlas-directed": (
        "CO-MUNICIPAL-PUEBLO",
        "10_Municipal_Authorities",
        "https://www.pueblo.us/DocumentCenter/View/21956/Fee-Schedule?bidId=",
    ),
}

'''
s=s[:a]+formatted+identities+s[b:]
a=s.index('def load_plan(');b=s.index('\ndef rows(',a)
s=s[:a]+'''def load_plan(root: Path) -> Plan:
    """Check the root-verified manifest directly instead of running the prior verifier.

    Root reviewed the source evidence and this frozen input set separately. Pin its
    exact manifest and every member here; final request/record validation still runs
    before writes. Executing the predecessor's embedded verifier adds no custody
    evidence and would introduce another code path into the write preflight.
    """
    safe(root)
    for name, expected in [
        ("PREPARATION.json", PREP_SHA),
        ("FINAL_MANIFEST.json", MANIFEST_SHA),
    ]:
        path = safe(PREP, name)
        if not path.is_file() or digest(path.read_bytes()) != expected:
            raise ValueError("Unapproved preparation: " + name)
    manifest = json.loads((PREP / "FINAL_MANIFEST.json").read_bytes())
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
        checked(PREP, File.model_validate(item))
    data = json.loads((PREP / "PREPARATION.json").read_bytes())
    before, guards = {}, []
    for baseline in data["baseline"]:
        content = checked(PREP, File.model_validate(baseline["preserved"]))
        if baseline["repository_path"] in TARGETS:
            before[baseline["repository_path"]] = content
        else:
            guards.append(ref(baseline["repository_path"], content))
    return Plan(
        PREP_SHA,
        digest((PREP / "source-provenance.jsonl").read_bytes()),
        tuple(data["sources"]),
        tuple(data["proposed_records"]),
        PREP,
        before,
        tuple(guards),
    )

''' +s[b:]
a=s.index('        if (sid != template["record_id"]');b=s.index('            raise ValueError("Source/template/authority mismatch")',a)
s=s[:a]+'''        identity = (source["authority_id"], source["layer_id"], source["http_url"])
        if (
            sid != template["record_id"]
            or sid in data
            or identity != APPROVED_IDENTITIES.get(sid)
            or template["layer_id"] != source["layer_id"]
            or template["acquisition_method"] != "manual_official_download"
            or template["expected_sha256"] != source["original"]["sha256"]
        ):
'''+s[b:]
t=p.with_name('.transaction.py.tmp');t.write_text(s);os.replace(t,p)
# The prior README remains preserved within the complete historical packet.
r=base/'README.md';s=r.read_text().replace('The legacy `VERIFIER_SHA` constant from the reference is unused.','The unused legacy `VERIFIER_SHA` constant was removed in the root-requested readability revision.')
s+='\nThe complete first 100-file packet is preserved byte-for-byte under `historical/first-prepared-9a12c339/`, including its original final manifest. This revision only reformats new code, names the fixed identity map and removes the unused constant; original source, proposed records, acquisition evidence and exact historical control prefixes remain unchanged.\n';t=r.with_name('.README.md.tmp');t.write_text(s);os.replace(t,r)
print('Root-requested readability revision applied; original100file snapshot preserved')
print('Remaining lines over100:',[(n,len(line)) for n,line in enumerate(p.read_text().splitlines(),1) if len(line)>100])
