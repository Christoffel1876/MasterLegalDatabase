from pathlib import Path
from hashlib import sha256
import shutil,json,os
r=Path(__file__).resolve().parent;base=r.parents[2];repo=base/'MasterLegalDatabase'
old=base/'handoffs/run-2026-09-12/el-paso-intake-transaction'
prep=base/'handoffs/run-2026-09-12/colorado-springs-intake-preparation'
assert sha256((prep/'FINAL_MANIFEST.json').read_bytes()).hexdigest()=='5b0e8cf0cd835d793c99ae1c32f50d287e9760ae854fa8fa69e911c1b6b21142'
shutil.copytree(prep,r/'evidence/preparation')
for name in ['transaction.py','test_transaction.py','README.md']:
 (r/'evidence/el-paso-reference').mkdir(exist_ok=True);shutil.copyfile(old/name,r/'evidence/el-paso-reference'/name)
pins={}
for rel in ['geode/__init__.py','geode/pipeline/__init__.py','geode/connectors/__init__.py','geode/schemas/__init__.py','geode/utils/__init__.py','geode/pipeline/manual_source_intake.py','geode/connectors/archive_paths.py','geode/connectors/download_metadata.py','geode/constants.py','geode/schemas/models.py','geode/schemas/local.py','geode/schemas/ontology.py','geode/schemas/validators.py','geode/utils/file_io.py']:
 pins[rel]=sha256((repo/rel).read_bytes()).hexdigest();out=r/'evidence/runtime-code'/rel;out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(repo/rel,out)
s=(old/'transaction.py').read_text();s=s.replace('Guarded El Paso received-PDF','Guarded Colorado Springs official-PDF')
s=s.replace('08fc11d7de1f23128b2f1dae63c8ed0960517a9ecdbd1e1a0ef8f4852c05d0fa','ef11c721fa642cea4a3fa684bcaf3f472fb61559442dfad93974e626d104d032').replace('8291e4abed17a31eb11eb85c3482ae8386e8763dffaabbeb69bb07b87096caac','5b0e8cf0cd835d793c99ae1c32f50d287e9760ae854fa8fa69e911c1b6b21142').replace('3903be561058ffbefa6b711f8ea62fe9f0739e0fcab8e803b9fb80445884897f','a9c665796a66e8282491e6eb732fa6abb673b5df8d503a79fcc553c64954df8e')
a=s.index('_runtime_source =');b=s.index('sys.path.insert(0, str(DEFAULT_ROOT))',a)
s=s[:a]+'RUNTIME_CODE = '+repr(pins)+'''\n\ndef validate_runtime_code() -> None:
    """Pin all transitive local imports before execution and again before writes."""
    for relative, expected in RUNTIME_CODE.items():
        path = DEFAULT_ROOT / relative
        if not path.is_file() or any(p.is_symlink() for p in (path, *path.parents)):
            raise ValueError("Reviewed runtime is not an ordinary file")
        with path.open("rb") as handle:
            actual = hashlib.file_digest(handle, "sha256").hexdigest()
        if actual != expected:
            raise ValueError("Reviewed runtime changed: " + relative)

validate_runtime_code()
'''+s[b:]
s=s.replace('    _report_from_records,','    _report_from_records,\n    _validate_reconciliation_record,\n    ManualSourceIntakeRequest,')
s=s.replace('min_length=13, max_length=13','min_length=2, max_length=2').replace('Literal["08_County_Authorities"]','Literal["10_Municipal_Authorities"]').replace('Literal["received_review_package"]','Literal["manual_official_download"]')
s=s.replace('raw_before: Literal[46]','raw_before: Literal[59]').replace('raw_after: Literal[59]','raw_after: Literal[61]').replace('ledger_before: Literal[47]','ledger_before: Literal[60]').replace('ledger_after: Literal[60]','ledger_after: Literal[62]')
s=s.replace('expected = {x["path"] for x in manifest["files"]} | set(manifest["exclusions"])','expected = {x["path"] for x in manifest["files"]} | {"FINAL_MANIFEST.json", "FINAL_MANIFEST.schema.json"}')
s=s.replace('included = tuple(s for s in data["sources"] if s["decision"] == "propose_county_intake")','included = tuple(data["sources"])')
s=s.replace('if len(plan.sources) != 13 or len(plan.templates) != 13:', 'if len(plan.sources) != 2 or len(plan.templates) != 2:').replace('Exactly thirteen approved sources required','Exactly two approved sources required')
s=s.replace('sid = source["source_id"]','sid = source["proposed_record_id"]')
s=s.replace('"CO-COUNTY-EL_PASO"','"CO-MUNICIPAL-COLORADO_SPRINGS"').replace('"08_County_Authorities"','"10_Municipal_Authorities"').replace('"received_review_package"','"manual_official_download"')
s=s.replace('        data[sid] = checked(plan.originals_root, File.model_validate(source["original"]))','''        request_fields = {key: template[key] for key in (
            "record_id", "layer_id", "official_source_name", "official_source_url",
            "acquisition_method", "received_from", "reviewer_name", "reviewer_email",
            "custody_note", "expected_sha256", "allow_duplicate")}
        request_fields["source_file"] = str(plan.originals_root / source["original"]["path"])
        ManualSourceIntakeRequest.model_validate(request_fields)
        if (template["source_file"] != source["original"] or
                source["http_url"] != template["official_source_url"] or
                template["intake_id"] is not None or template["received_at"] is not None or
                template["archive_path"] is not None or template["status"] != "proposed_not_applied"):
            raise ValueError("Source/template custody mismatch")
        data[sid] = checked(plan.originals_root, File.model_validate(source["original"]))''')
s=s.replace('txid = "el-paso-sd011-" + stamp','txid = "colorado-springs-sd014-" + stamp')
s=s.replace('archive = f"_RAW_ARCHIVE/manual_intake/08_County_Authorities/{sid}/{stamp}_original.pdf"','''from geode.connectors.archive_paths import safe_archive_stem
        filename = template["original_filename"]
        archive = (f"_RAW_ARCHIVE/manual_intake/10_Municipal_Authorities/{sid}/"
                   f"{when.strftime('%Y%m%dT%H%M%SZ')}_{safe_archive_stem(Path(filename).stem)}.pdf")''')
s=s.replace('original_filename="original.pdf"','original_filename=filename')
s=s.replace('boundary="Received source evidence only; original HTTP acquisition not independently "\n            "witnessed, legal_currentness=not_verified, answer_safe=false. No rule or coverage promotion.",','boundary="Direct Atlas official HTTP source evidence only; acquisition interval remains in "\n            "custody_note. legal_currentness=not_verified, answer_safe=false. No rule or coverage promotion.",')
s=s.replace('    suffix = b"".join((r.model_dump_json() + "\\n").encode() for r in records)','''    for record in records:
        _validate_reconciliation_record(root, record)
        destination(root, record.archive_path)
    suffix = b"".join((r.model_dump_json() + "\\n").encode() for r in records)''')
s=s.replace('len(old_raw) != 46 or len(old_ledger) != 47','len(old_raw) != 59 or len(old_ledger) != 60').replace('Expected exactly 46 raw and 47 ledger rows','Expected exactly 59 raw and 60 ledger rows').replace('manifest_records=59','manifest_records=61')
s=s.replace('    safe(root)\n    snapshots = safe(root, "_SNAPSHOTS")','    validate_runtime_code()\n    safe(root)\n    snapshots = safe(root, "_SNAPSHOTS")')
s=s.replace('    states = []\n    for p in TARGETS:', '''    else:
        # Validate the actual final-record host/layer/path rules even for a dry run,
        # before execution state or any repository destination is created.
        _derive(plan, root, datetime.now(timezone.utc))
    states = []
    for p in TARGETS:''')
s=s.replace('prefix=".el-paso-transaction-"','prefix=".colorado-springs-transaction-"')
s=s.replace('"sources": 13','"sources": 2').replace('"raw_records": 59, "ledger_records": 60','"raw_records": 61, "ledger_records": 62')
s=s.replace('raw_before=46, raw_after=59','raw_before=59, raw_after=61').replace('ledger_before=47, ledger_after=60','ledger_before=60, ledger_after=62')
s=s.replace('    actual = {p.relative_to(PREP).as_posix() for p in PREP.rglob("*") if p.is_file()}','''    actual = set()
    for p in PREP.rglob("*"):
        safe(PREP, p.relative_to(PREP).as_posix())
        if not p.is_dir() and not p.is_file():
            raise ValueError("Nonordinary preparation member")
        if p.is_file(): actual.add(p.relative_to(PREP).as_posix())''')
s=s.replace('    data = json.loads((PREP / "PREPARATION.json").read_bytes())','''    # Refuse concurrent changes while the isolated read-only verifier was running.
    for value in manifest["files"]:
        checked(PREP, File.model_validate(value))
    data = json.loads((PREP / "PREPARATION.json").read_bytes())''')
s=s.replace('    for name in dirs + files:\n            path = Path(folder) / name\n            if path.is_symlink():','    for name in dirs + files:\n            path = Path(folder) / name\n            if path.is_symlink():')
s=s.replace('                    raise ValueError("Duplicate source bytes outside this transaction")','''                    raise ValueError("Duplicate source bytes outside this transaction")
            elif path.is_file() and path.stat().st_size < 200:
                raw = path.read_bytes()
                if raw.startswith(b"version https://git-lfs.github.com/spec/v1") and any(
                    h.encode() in raw for h in candidate_digests
                ):
                    raise ValueError("Matching source LFS pointer already exists")''')
(r/'transaction.py').write_text(s)
# Adapt isolated fixture suite; preserve old tests as references, not imported dependencies.
s=(old/'test_transaction.py').read_text().replace('46 small synthetic originals, one missing historical row and 13 PDFs','59 small synthetic originals, one missing historical row and two PDFs').replace('range(46)','range(59)').replace('manifest_records=46','manifest_records=59').replace('range(13)','range(2)').replace('All 13 append','Both sources append').replace('== 59','== 61').replace('== 60','== 62').replace('original:fixture-new-04','original:fixture-new-01')
s=s.replace('sources.append(dict(source_id=sid, authority_id="CO-COUNTY-EL_PASO",\n                            layer_id="08_County_Authorities", original=original))','sources.append(dict(source_id=f"SD014-{i+1:02}", proposed_record_id=sid, authority_id="CO-MUNICIPAL-COLORADO_SPRINGS",\n                            layer_id="10_Municipal_Authorities", original=original, http_url="https://coloradosprings.gov/fixture.pdf"))')
s=s.replace('templates.append(dict(record_id=sid, acquisition_method="received_review_package",','templates.append(dict(record_id=sid, layer_id="10_Municipal_Authorities", acquisition_method="manual_official_download",')
s=s.replace('official_source_name="Fixture only", official_source_url=None,\n                              received_from=', 'official_source_name="Fixture only", official_source_url="https://coloradosprings.gov/fixture.pdf",\n                              reviewer_email=None,allow_duplicate=False,intake_id=None,archive_path=None,received_at=None,status="proposed_not_applied",original_filename=sid+".pdf",received_from=')
s=s.replace('r.acquisition_method == "received_review_package"','r.acquisition_method == "manual_official_download"')
s=s.replace('sources[0]["authority_id"] = "CO-MUNICIPAL-COLORADO_SPRINGS"','sources[0]["authority_id"] = "CO-COUNTY-EL_PASO"')
(r/'test_transaction.py').write_text(s)
print('prepared implementation',sha256((r/'transaction.py').read_bytes()).hexdigest())
