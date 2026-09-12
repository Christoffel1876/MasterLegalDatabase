from pathlib import Path
from datetime import datetime,timezone
from hashlib import sha256
import json
from pydantic import BaseModel,ConfigDict
class Note(BaseModel):
 model_config=ConfigDict(extra='forbid',strict=True)
 page:int
 observations:list[str]
class Freeze(BaseModel):
 model_config=ConfigDict(extra='forbid',strict=True)
 method:str
 frozen_at:str
 source_sha256:str
 images:dict[str,str]
 notes:list[Note]
root=Path(__file__).resolve().parent
notes=[
(1,['Directly viewed full Poppler 200 dpi page. Colorado Springs Fire Department, Division of the Fire Marshal; Construction Services Fee Schedule. Printed Effective 07/01/2026, not independent adoption/currentness proof. City logo and CSFD patch are graphical. Printed page 1. TOC sends Definitions/Explanations to Page 5 although heading appears on physical page 6.']),
(2,['Directly viewed full page. Global note: Unless otherwise noted, a plan review fee includes two plan reviews, an initial inspection, and a final inspection. Additional fees may be assessed for subsequent reviews, trips, and re-inspections.',
'Water table has five rows: plan review $258.00; inspection first fire hydrant $215.00; each additional hydrant $129.00; inspection per fire line $344.00; water tank for fire suppression $860.00.',
'Construction table continues through pages 3 and 4. A-1 three tiers: $1,032.00 / $1,892.00 / $1,892.00. A-2: $602.00 / $774.00 / $774.00. A-3: $645.00 / $817.00 / $817.00. A-4: $688.00 / $1,032.00 / $1,032.00. A-5: $688.00 / $1,720.00 / $1,720.00. B fourtiers $473.00/$688.00/$946.00/$946.00. E new/additions $2,322.00 and remodels per 10,000 sq ft $430.00. F-1 $645.00/$1,032.00/$1,032.00; F-2 $602.00/$860.00/$860.00. H all groups $602.00. I-1/I-2 first two rows $559.00/$817.00; second label visibly retains or less after its range.']),
(3,['Directly viewed full page. Construction continuation starts I-1/I-2 50,001–100,000 $2,365.00 and each additional50,000 $516.00. I-3 increments50,000 $1,376.00; I-4 $688.00. M five tiers516/602/645/1204/602. R-1 688/1376/602. R-2 430/731/1849/3096/774; last label begins R2 without hyphen. Townhomes per building258. R-3WUI home/accessorydwelling688. WUI deck387,siding473,Deck/Patio/sunroom430,detached473. CommercialWUI surcharge tiers430/516/645/989 are italicized. R-4 559. S-1&S-2 tiers602/645/1204/645, last sq.Ft capitalization source. U344; otheroccupancies1032. High-rise surcharge in addition to occupancyfee, literal0.04/sq.ft without dollar sign. Shell516;foundation/superstructure129;Limitedreview86; smoke exhaust1548/pressurization4300;radio516;otherpermits516;phasedTCO1720;firefighterair2580;sitesafety344. All monetary rows other than explicit per-square-foot print dollars and two decimals.']),
(4,['Directly viewed full page. Two construction continuation rows: Performance-based design surcharge,in addition to applicable fees above, minimum$2,000, literal0.04/sq.ft.; construction plan check$86.00.',
'Alarm nine rows:5-device129;<=50devices473;51–100731;101–1501204;eachadditional20greater150430;residentialsinglefamily430;monitoring258;firefightercommunicationsotherthanradio602;2wayelevator430.',
'Sprinkler ten fee rows:20-head129;100orlesswithonewetpipe riser731;101–2001118;201–3001333;eachadditional100greater300336 (not344);additionalwetrisers/backflow344;standpipe344;dry/pre-action/delugevalve344;firepump/foam774;13Ddwelling/manufacturedhome602. Three sprinkler inspections allowed perpermit before tripfee foradditionalinspections; full note governs sprinkler rows.',
'Fixed extinguishing four rows430/215/860/2580. Misc table begins technologyfee assessed onallpermits25; fire sprinkler/fire alarm/fixedfire/waterplancheck100, continuespage5.']),
(5,['Directly viewed full page. Misc continuation cancelledpriorpermit perhour172,WorkatRisk500,expeditedfirstcome/firstservedmax5/week420,annualfacilities1032,revisions/spliceperquarterhour43,demolition258,preplanconsult first30minutesfree then172eachsubsequenthourorportion,third/subsequentsubmittals literal1.5x Review Fee.',
'Misc inspections seven rows: conveniencefirsttwohours516/additionalhour258;preliminaryperhour172;tripthird/subsequentpartialperhour172;reinspection500;WUIsinglefamilyR-3reinspection250;cancellationafter3:00PMbusinessdaybefore344. Whole note conditional reinspection if inaccessible/insufficientpretest/orhazardsnotcompleted.',
'Administrative four rows permitrenewal/reissue40;supportperhour40;workwithoutpermitperincidentliteral2x Permit Fee;thirdpartyreview86. Extraterritorial twosurcharges43perquarterhourandIRS Standard Mileage Rate; fullnote outsideCityjurisdiction,additionaltoallapplicablefees,travel-timeandroundtripmileage,citycentersGoogleMaps,currentIRSstandard,roundednearestdollar. Definitions heading actually nextpage, despiteTOC.']),
(6,['Directly viewed full page. Eleven definition starts. Administrative Support completeparagraph. Construction Plan Check Fee collectedbyPPRBD onsubmissiontoitsportal,limitedreviewminimumCSFDcharge;deductedfromtotalatCSFDapprovaliffullreviewandinspectionrequired. PPRBD collector not issuingmunicipalauthority. ConvenienceInspectionoutsidebusinesshours. Expeditedavailableincludingextraterritorial,firstcomefirstserved,paidatrequest,firecodeofficialdiscretionstaff/resources,doesnotsupersederapidresponse. Fireplancheck100atAccelasubmissionbeforecheck-in,appliestosprinkler/alarm/suppressionincluding5device/20head. Highriseone-time. Limitedscope nolifesafetyimpact/notapplicable/noinspection;sourcegrammarplans is marked. Performanceonetimeengineering scope/requestorplanreviewerdiscretion,min2000. Preliminaryscopeevaluation. Preplanconsult<=30minutesnofee. Reinspectiondefinitioncontinuespage7; do not truncate after the.']),
(7,['Directly viewed full page. Reinspection continuation: inspection, or a system that has not been pre-tested shall also require a re-inspection. Trip Fee accountsfor twoinspections; sprinklersthreeperpermit;additionalphasing/scheduling. WUIcommercialsurchargewithinCSFDWUIarea,inadditiontooccupancyclassandsquarefootagefee. Full Implementation: Fees shall be assessed upon the plan approval date. Note Worthy: Fees associated with high pile storage and hazardous materials are listed in the Colorado Springs Fire Department Code Services Fee Schedule. This exclusion/other-schedule reference must accompany fee outputs. Printedpage7;restblank.'])]
m=Freeze(method='Atlas source-first direct image review; title/role known, not blind. All seven full images viewed before extracting or reading native text. Notes are observations, not a normalized substitute for source text.',frozen_at=datetime.now(timezone.utc).isoformat(),source_sha256=sha256((root/'source/original.pdf').read_bytes()).hexdigest(),images={f'images/page-{p}.png':sha256((root/f'images/page-{p}.png').read_bytes()).hexdigest() for p in range(1,8)},notes=[Note(page=p,observations=n) for p,n in notes])
out=root/'VISUAL_OBSERVATIONS.json'
assert not out.exists()
out.write_text(m.model_dump_json(indent=2)+'\n')
(root/'VISUAL_OBSERVATIONS.schema.json').write_text(json.dumps(Freeze.model_json_schema(),indent=2)+'\n')
print(out,sha256(out.read_bytes()).hexdigest())
