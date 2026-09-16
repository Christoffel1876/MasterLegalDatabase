from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, shutil, subprocess, sys
sys.path.insert(0, '/private/tmp')
from preserve_geode_closing_packets import REPO, RUN, AUDIT, PYTHON, Acceptance, Ref, ref, copy_closed, verify, write_acceptance
source=RUN/'manual-watch-next-selection'
target=REPO/'research/local_review/manual-watch-next-selection-2026-09-13'
out=AUDIT/'MANUAL_SOURCE_WATCH/next-selection'
out.mkdir()
copied=copy_closed(source,target,'FINAL_MANIFEST.json')
check=verify([PYTHON,'-B',str(target/'verify_proposal.py')],out/'portable-verification.json')
result=subprocess.run([PYTHON,'-B',str(target/'verify_proposal.py'),'--repository-metadata',str(REPO)],capture_output=True,text=True,cwd='/private/tmp')
(out/'repository-pin-check.json').write_text(json.dumps({'at':datetime.now(timezone.utc).isoformat(),'exit_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr},indent=2)+'\n')
assert result.returncode==1 and 'External metadata pin changed: docs/MANUAL_SOURCE_WATCH.md' in result.stderr
write_acceptance(out,Acceptance(checked_at=datetime.now(timezone.utc).isoformat(),status='accepted_prepared_only_no_enrollment',copied_originals=copied,verification_artifacts=[check,ref(out/'repository-pin-check.json',out)],findings=[
'Root read complete proposal and verifier; twelve exact files copied and closed portable check passed.',
'Six proposed additions totaling2191486bytes/16pages, in three bounded pairs; all59 currently unselected entries classified from the frozen61/21/40 snapshot.',
'No new source request or PDF byte check occurred during proposal or preservation; scoped metadata references are not a complete current-custody audit.',
'Root optional live repository pin check correctly refused because docs/MANUAL_SOURCE_WATCH.md gained the actual maintained pilot section after proposal freeze. Prior agent metadata check is historical; no claim that all current repository pins passed.',
'Existing production selection remains exactly two Colorado Springs PDFs. Integration and any subsequent authorization are separate from this preserved proposal.',
'Null mapped HTTP/review evidence does not establish absence elsewhere; original Greeley received-package provenance remains separate from later exact-byte reacquisition.'
]))
output=AUDIT/'MANUAL_SOURCE_WATCH/live-final'
output.mkdir()
live=REPO/'research/local_review/manual-source-watch-live-2026-09-13'
verified=verify([PYTHON,'-I','-B',str(live/'verify_copy.py')],output/'portable-verification.json')
files=[]
for src,name in [(RUN/'springs-watch-final-suite/pytest.log','pytest-2548.log'),(Path('/private/tmp/geode-springs-watch-final-coverage.json'),'coverage-2548.json')]:
 shutil.copyfile(src,output/name);files.append(ref(output/name,output))
files.extend([Ref(path=str((live/n).relative_to(REPO)),sha256=hashlib.sha256((live/n).read_bytes()).hexdigest(),size_bytes=(live/n).stat().st_size) for n in ['ACCEPTANCE.json','FINAL_MANIFEST.json']])
write_acceptance(output,Acceptance(checked_at=datetime.now(timezone.utc).isoformat(),status='accepted_final_watch_full_suite_and_actual_two_source_pilot',copied_originals=files,verification_artifacts=[verified],findings=[
'Final watch code full suite:2548passed49warnings471.53seconds; historical preparation and finalization receipts pending-full statuses are superseded for that code by this receipt.',
'Actual maintained pilot00:44:41.691307Z through00:44:43.469133Z made two ordinary public HTTP200requests,421075bytes, no redirects; both exact seven-page PDFs unchanged.',
'At00:50:18.958363Z, after original00:49:41.691307Zdeadline, actual replay returned saved report without any transport call or runtime byte change.',
'Closed42-file portable live package verified; it preserves actual code/config/authorization/run/response bytes and replay evidence. Portable checker does not import saved acquisition code or execute public requests.',
'No scheduler, baseline advance, currentness promotion or wider source enrollment. review_needed:false concerns this fetch discrepancy only; existing legal/text limitations remain.'
]))
print('Preserved next-watch proposal and final maintained pilot acceptance.')
