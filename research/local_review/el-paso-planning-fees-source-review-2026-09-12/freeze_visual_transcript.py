"""Freeze manual image transcription before an optional OCR comparison."""
from pathlib import Path
import sys,hashlib,json
from datetime import datetime,timezone
HERE=Path(__file__).absolute().parent
sys.path.insert(0,str(HERE))
from review_models import Asset,Cell,Row,Page,VisualTranscript
import visual_data as d

def write(name,b):
 with (HERE/name).open('xb') as f:f.write(b)
def asset(name):
 b=(HERE/name).read_bytes();return Asset(path=name,sha256=hashlib.sha256(b).hexdigest(),size_bytes=len(b))
transcript=bytearray();rows=[]
def cell(col,text,box,refs=None,clipped=False):
 start=len(transcript);transcript.extend(text.encode());end=len(transcript);transcript.extend(b'\n')
 return Cell(column=col,text=text,state='visible_text_with_clipped_unresolved_tail' if clipped else 'visible_text' if text else 'visibly_blank',pixel_bbox=box,superscript_footnotes=refs or [],transcript_start_byte=start,transcript_end_byte=end)
def header(id,page,text,y0,y1,role='section_header'):
 rows.append(Row(id=id,physical_page=page,role=role,cells=[cell('heading',text,(140,y0,2053,y1))]))
def fee_group(page,prefix,data,bounds,section):
 for i,line in enumerate(data.splitlines(),1):
  parts=line.split('\t');assert len(parts) in [3,4],parts
  label,fee,project=parts[:3];refs=[int(parts[3])] if len(parts)==4 else []
  y0,y1=bounds[i-1],bounds[i]
  boxes=[(140,y0,1761,y1),(1760,y0,1941,y1),(1940,y0,2053,y1)]
  rows.append(Row(id=f'{prefix}-{i:02}',physical_page=page,role='fee_row',section_header_id=section,fee_header_id='P1-COLUMNS',cells=[cell('application_type',label,boxes[0],refs,clipped=prefix=='P3-ENG' and i==14),cell('application_fee',fee,boxes[1]),cell('project_type',project,boxes[2])]))
header('P1-TITLE',1,'2026 Planning and Community Development',175,236,'title')
header('P1-DATE',1,'Fee Schedule- Effective Date May 1, 2026',240,300,'title')
rows.append(Row(id='P1-COLUMNS',physical_page=1,role='column_headers',cells=[cell('application_type','APPLICATION TYPE',(140,303,1761,373)),cell('application_fee','Application Fees',(1760,303,1941,373),[1]),cell('project_type','Project Type',(1940,303,2053,373))]))
header('PLANNING-MINOR',1,'Planning- Minor Applications',372,409)
fee_group(1,'P1-PLAN',d.P1_PLANNING,d.BOUNDS['p1planning'],'PLANNING-MINOR')
header('ENGINEERING-MINOR',1,'Engineering- Minor Applications',1220,1258)
fee_group(1,'P1-ENG',d.P1_ENGINEERING,d.BOUNDS['p1engineering'],'ENGINEERING-MINOR')
header('PLANNING-MAJOR',2,'Planning- Major Applications',187,225)
fee_group(2,'P2-PLAN',d.P2_PLANNING,d.BOUNDS['p2planning'],'PLANNING-MAJOR')
fee_group(3,'P3-PLAN',d.P3_PLANNING,d.BOUNDS['p3planning'],'PLANNING-MAJOR')
header('ENGINEERING-MAJOR',3,'Engineering- Major Applications',748,792)
fee_group(3,'P3-ENG',d.P3_ENGINEERING,d.BOUNDS['p3engineering'],'ENGINEERING-MAJOR')
fee_group(4,'P4-ENG',d.P4_ENGINEERING,d.BOUNDS['p4engineering'],'ENGINEERING-MAJOR')
header('OTHER',4,'Other',260,305)
fee_group(4,'P4-OTHER',d.P4_OTHER,d.BOUNDS['p4other'],'OTHER')
header('FOOTNOTES',5,'Footnotes',187,231)
for i,text in enumerate(d.FOOTNOTES+d.GENERAL_NOTES):
 y0,y1=d.BOUNDS['p5notes'][i:i+2]
 rows.append(Row(id=f'FN-{i+1:02}' if i<15 else f'GENERAL-{i-14}',physical_page=5,role='footnote' if i<15 else 'general_note',section_header_id='FOOTNOTES',note_id=i+1 if i<15 else None,cells=[cell('application_type',text,(140,y0,1761,y1)),cell('application_fee','',(1760,y0,1941,y1)),cell('project_type','',(1940,y0,2053,y1))]))
for n in range(1,6):
 rows.append(Row(id=f'P{n}-FOOTER',physical_page=n,role='page_label',cells=[cell('page_label',f'Page {n} of 5',(1010,1598,1170,1645))]))
write('VISUAL_TRANSCRIPTION.txt',bytes(transcript))
pages=[Page(physical_page=n,source_image=asset(f'images/page-{n}.png'),native_file=asset(f'native/page-{n:04}.txt')) for n in range(1,6)]
r=VisualTranscript(frozen_at=datetime.now(timezone.utc).isoformat(),visual_observations=asset('VISUAL_OBSERVATIONS.json'),review_mode='source_images_first_then_empty_native_comparison_before_ocr',pages=pages,transcript=asset('VISUAL_TRANSCRIPTION.txt'),rows=rows,unresolved_row_ids=['P3-ENG-14'],limitations=[
'Visual transcription is a manually entered reading of pixels, not extracted native bytes. The source has no native text on all five pages; all native offsets remain null.',
'Source wording, fee strings, superscript-footnote associations, project codes and blank cells are retained. Source line wraps are joined with spaces; superscript markers are stored separately. Exact Unicode, font metrics and repeated whitespace cannot be certified from pixels.',
'The page-3 erosion-label terminal region reaches and is clipped at its cell boundary. Only the visible wording through submittal is transcribed; no closing parenthesis or invisible continuation is supplied.',
'The blue county logo/seal is retained in the full source image as graphical identity context; this text transcription does not reproduce the logo artwork or make a signature/official-adoption claim.',
'No OCR candidate had been generated or consulted when this transcript was frozen. Previous title/role knowledge and empty native extraction are disclosed; no fully blind independence claim.',
'Page 2 Planning-Major rows continue on page 3; page 3 Engineering-Major rows continue on page 4. The page-1 fee-header superscript 1 and all 15 numbered footnotes remain available. No project-code meanings, calculations or source-currentness inference are added.',
'The five visibly blank fee-row Project Type cells and the blank right-hand footnote/general-note cells are represented explicitly; blanks and TBD are never numeric zero.',
'Canonical intake completion is not asserted. The source was copied from the prepared received Sherlock package; earlier HTTP acquisition was not independently witnessed.'
],source_date_claim='Fee Schedule- Effective Date May 1, 2026')
b=(r.model_dump_json(indent=2)+'\n').encode();VisualTranscript.model_validate_json(b);write('VISUAL_TRANSCRIPTION.json',b);write('VISUAL_TRANSCRIPTION.schema.json',(json.dumps(VisualTranscript.model_json_schema(),indent=2)+'\n').encode())
print('frozen',r.frozen_at,'rows',len(rows),'fee rows',sum(x.role=='fee_row' for x in rows),'SHA',hashlib.sha256(b).hexdigest())
