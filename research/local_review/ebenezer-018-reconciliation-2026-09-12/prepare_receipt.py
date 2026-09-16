"""One-time creation of the additive EB018 receipt; refuses overwrites."""
from pathlib import Path
import importlib.util
import sys
import json
from datetime import datetime, timezone

HERE = Path(__file__).absolute().parent
spec = importlib.util.spec_from_file_location('independent_check', HERE/'validate_check.py')
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)
root = HERE.parent/'ebenezer018-atlas-reconciliation'
original_reports = HERE.parent/'ebenezer/reviews/EB-PDF-018_weld-building-fees-sd008-01_20260912T223629Z'

def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as f:
        f.write(data)

def asset(path):
    p=HERE/path
    b=p.read_bytes()
    return m.Asset(path=path,sha256=m.sha(b),size_bytes=len(b))

def save(path, obj):
    data=(obj.model_dump_json(indent=2)+'\n').encode()
    type(obj).model_validate_json(data)
    write(HERE/path,data)
    write(HERE/path.replace('.json','.schema.json'),
          (json.dumps(type(obj).model_json_schema(),indent=2)+'\n').encode())

if m.sha((root/'INVENTORY.json').read_bytes()) != m.ROOT_INVENTORY:
    raise ValueError('Unexpected root inventory')
pre={p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file()}
for relative,data in sorted(pre.items()):
    m.ordinary(root/relative)
    write(HERE/'frozen-root-reconciliation'/relative,data)
for path,data in pre.items():
    if (root/path).read_bytes()!=data:
        raise ValueError('Root changed during copy')
for p in (HERE/'frozen-root-reconciliation/reports').iterdir():
    m.ordinary(original_reports/p.name)
    if p.read_bytes()!=(original_reports/p.name).read_bytes():
        raise ValueError('Root report differs from delivered original')

native={n:json.loads((HERE/f'frozen-root-reconciliation/native-evidence/page-{n:04}.json').read_bytes())['text'].encode() for n in range(1,6)}

def span(id,page,start,end,purpose):
    data=native[page]
    a=data.index(start.encode())
    b=data.index(end.encode(),a) if end is not None else len(data)
    text=data[a:b]
    return m.Slice(id=id,physical_page=page,native_evidence=asset(f'frozen-root-reconciliation/native-evidence/page-{page:04}.json'),start_byte=a,end_byte=b,exact_native_text=text.decode(),sha256=m.sha(text),purpose=purpose)

slices=[
 span('minor-review',1,'Minor Plan Review',None,'Minor plan-review amount and all following indented scope lines; source whitespace retained.'),
 span('demolition',2,'Demolition Permit Fees:','Electrical Permit Fees:','Separate demolition amount with two printed decimal periods.'),
 span('complete-electrical',2,'Electrical Permit Fees:',None,'Complete residential and other-electrical sections including exception, labor/material valuation, all tiers and temporary meter.'),
 span('matrix-header',4,'Building Valuation Per Square Foot','A-1 Assembly','Construction-classification headings and native ordering; no 252-cell certification.'),
 span('matrix-bottom',4,'S-1 Storage, moderate hazard','Notes:','Selected S-1/S-2 VA cells were examined in context of the bottom grid and header; other bytes remain unchanged, not newly certified individually.'),
 span('road-agricultural',5,'Agricultural Commercial 1,000 sq. ft','County Facilities Categories','Road agricultural-commercial label and separate per-1,000-square-foot value, retaining native whitespace.'),
]
crop_defs=[('p4-bottom-rows',4,(140,2380,2415,2650),'Selected S-1 and S-2 VA values; other surrounding cells provide grid context.'),('p4-headers',4,(130,180,2420,410),'Nine classification headers and first-row alignment.'),('p2-electrical',2,(140,1500,2460,2880),'Complete visible electrical section and fee bases, exception and meter row.'),('p1-plan-review',1,(140,2400,2450,2880),'Minor amount and complete indented application scope.'),('p5-road',5,(130,300,2300,1120),'Road categories, agricultural embedded unit and separate amount/unit text.')]
crops=[m.Crop(path=f'crops/{name}.png',physical_page=page,source_image=asset(f'frozen-root-reconciliation/source/page-{page:04}.png'),pixel_box=box,method='PyMuPDF Pixmap.copy: exact source PNG pixels, no resampling',scope=scope) for name,page,box,scope in crop_defs]
obs=[
 m.Observation(id='IC-01',disposition_ids=['EB018-P2-009','EB018-P2-010'],physical_pages=[4],conclusion='The displayed grid has nine classification columns IA through VB. Native rows retain their values but do not themselves express a grid association contract. Root appropriately rejects the external blanket word harmless and limits its own matrix review. The targeted S-1 and S-2 VA values both read 92.33 in the source-pixel crop and agree with native and external Pass 1. A possible difference in the resized full-page preview was resolved by the crop; it is not a source discrepancy.',native_slice_ids=['matrix-header','matrix-bottom'],crop_paths=['crops/p4-headers.png','crops/p4-bottom-rows.png']),
 m.Observation(id='IC-02',disposition_ids=['EB018-P2-003','EB018-P2-018'],physical_pages=[1,2],conclusion='Minor Plan Review visibly has $80.00 with one decimal point; the separate demolition row visibly has $80..00. The minor-review scope remains the three indented lines in the source; this finding does not make $80.00 an unconditional project fee.',native_slice_ids=['minor-review','demolition'],crop_paths=['crops/p1-plan-review.png']),
 m.Observation(id='IC-03',disposition_ids=['EB018-P2-019'],physical_pages=[5],conclusion='The Road Impact Fee Categories label includes Agricultural Commercial 1,000 sq. ft, and the right-hand fee independently reads $1,186 per 1,000 sq. ft. Root preserves both occurrences without inferring a multiplier. The agricultural row in County Facilities is a separate row and is not substituted for the Road label.',native_slice_ids=['road-agricultural'],crop_paths=['crops/p5-road.png']),
 m.Observation(id='IC-04',disposition_ids=['EB018-P2-020'],physical_pages=[2],conclusion='The full electrical parent clause says except for inspections in mobile home and travel trailer parks, not an exemption for all park work or a waiver of every fee. It uses the dollar value of electrical installations including labor and materials (total cost to the customer), followed by valuation tiers. Residential scope includes additions to same and enclosed living area. The $3,001 to $50,000 row states $17.00 per $1,000 or fraction thereof of total valuation. More than $50,000 directs the reader to contact Weld County Building Department. Root correctly preserves these qualifications and treats the external Pass 1 prose as condensed, not exhaustive.',native_slice_ids=['complete-electrical'],crop_paths=['crops/p2-electrical.png']),
 m.Observation(id='IC-05',disposition_ids=[f'EB018-P2-{n:03}' for n in [1,2,4,5,6,7,8,11,12,13,14,15,16,17]],physical_pages=[1,2,3,4,5],conclusion='The remaining root dispositions were read alongside the reports and five full source images. The stated footer placement, preserved source-number forms, packaging-marker distinction, layout limits and separate unparsed date labels do not require a source or candidate correction in this scoped check. Punctuation/Unicode qualifications remain; this is not an exhaustive glyph transcription.',native_slice_ids=[],crop_paths=[]),
]
rec=m.Check(source_id='weld-building-fees-sd008-01',authority_id='CO-COUNTY-WELD',review_mode='candidate_report_and_prior_review_aware_direct_image_check',completed_at=datetime.now(timezone.utc).isoformat(),status='no_actionable_issue_in_scoped_reconciliation_check',original_root_inventory_sha256=m.ROOT_INVENTORY,frozen_inputs=[asset('frozen-root-reconciliation/'+p) for p in sorted(pre)],original_delivery_reports=[asset('frozen-root-reconciliation/reports/'+p.name) for p in sorted((HERE/'frozen-root-reconciliation/reports').iterdir())],full_page_images_directly_inspected=[1,2,3,4,5],report_disposition_ids_read=[f'EB018-P2-{n:03}' for n in range(1,21)],selected_slices=slices,crops=crops,observations=obs,limits=[
 'This is direct image review after reading candidate, external reports and prior review, not a fresh blind transcription.',
 'All five full images and five selected crops were directly viewed; this does not independently certify every one of the 252 valuation matrix cells or every glyph.',
 'External Ebenezer reports disclose pre-supplied image descriptions and caption-mediated Read results. Their declared procedure covered five pages, but their tool internals and all glyph-level accuracy were not independently proved.',
 'External PDF absence remains as reported. This check hashes the actual retained PDF and reproduces all five native pages; it does not retrospectively prove the external reviewer had the PDF.',
 'All five delivered external reports/receipts exactly match their copies in the root reconciliation. The execution/freeze times and non-consultation statements remain executor claims, not facts proved by hashes or filesystem times.',
 'JANUARY 2026 and Revised 012/25 are source labels with different roles. No adoption, effective date, operative applicability or legal currentness is determined.',
 'The successful original requested URL, final URL and HTTP acquisition timestamp remain unconfirmed. Received-review-package custody is not a fresh official download.',
 'Prior-review inventories and the complete three-document packet manifest are preserved as exact context, but unretained materials for other sources are not verified by this check.',
 'No source, native candidate, external report, prior audit, repository/control data or SD013 runtime was changed. Direct crop PNGs are additive derivatives of retained page pixels.'
])
save('INDEPENDENT_CHECK.json',rec)
write(HERE/'README.md',('''---
title: "EB018 independent check of Atlas reconciliation"
source_id: "weld-building-fees-sd008-01"
authority_id: "CO-COUNTY-WELD"
review_mode: "candidate_report_and_prior_review_aware_direct_image_check"
status: "no_actionable_issue_in_scoped_reconciliation_check"
legal_currentness: "not_verified"
---

No actionable correction was found in the frozen root reconciliation. All five full source PNGs and five targeted source-pixel crops were directly viewed after the candidate, reports and prior review were available. This is not a blind review or an independent certification of all 252 matrix cells.

The priority checks support root dispositions 10, 18, 19 and 20: grid joins must be retained; minor plan review is $80.00 while demolition is $80..00; the agricultural Road label embeds the unit separately from its fee; and the electrical exception applies specifically to inspections in mobile home and travel trailer parks. The complete electrical section is preserved as an unchanged native byte slice, including residential scope, customer labor/material basis, total-valuation wording, the contact referral above $50,000 and the temporary meter row.

All five external reports/receipts were compared byte-for-byte with the original delivery. Every file in the root reconciliation is copied unchanged under `frozen-root-reconciliation/`. The original PDF, candidate and all page-native/image bindings verify; all 14,311 native UTF-8 bytes reproduce from the PDF, and the 14,876-byte candidate regenerates exactly with its packaging markers. The five crop PNGs reproduce the recorded source pixels without resampling.

Ebenezer's review remains caption-mediated and assisted, including pre-supplied descriptions. Its declared coverage, timing and blind-order statements are not upgraded by this check. JANUARY 2026 and Revised 012/25 remain separate source labels; successful original URL/acquisition time and legal currentness remain unverified. No native word or amount correction is accepted.

Run, from any working directory, with Python, Pydantic 2 and PyMuPDF:

```sh
PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-status-venv/bin/python -I -B "/Users/mcoors/Documents/Project Geode/handoffs/run-2026-09-12/ebenezer018-independent-check/validate_check.py"
```

The read-only verifier checks the closed inventory, strict receipt/schema, pinned root verifier and inventory, exact native reproduction, candidate packaging, selected UTF-8 byte ranges and crop pixels. It checks integrity, not independent truth of every narrative judgment. Keep the final inventory hash outside this package when relying on it. `prepare_receipt.py` is the one-time preparation record; it must not be rerun in the frozen package.
''').encode())
files=[asset(p.relative_to(HERE).as_posix()) for p in sorted(HERE.rglob('*')) if p.is_file()]
save('INVENTORY.json',m.Inventory(files=files,exclusions='INVENTORY.json and INVENTORY.schema.json only'))
m.verify()
print('INDEPENDENT_CHECK.json',m.sha((HERE/'INDEPENDENT_CHECK.json').read_bytes()))
print('INVENTORY.json',m.sha((HERE/'INVENTORY.json').read_bytes()))
print('files',len(files)+2,'bytes',sum(x.size_bytes for x in files)+(HERE/'INVENTORY.json').stat().st_size+(HERE/'INVENTORY.schema.json').stat().st_size)
