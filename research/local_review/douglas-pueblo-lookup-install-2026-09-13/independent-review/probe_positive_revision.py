"""Offline source associations and seven legacy output checks, using immutable input bytes."""
from pathlib import Path
import hashlib,json
from probe_late_qa_revision import m,ROOT,BASE
FIXTURE_BASE=BASE.parent/"douglas-pueblo-lookups"
HERE=Path(__file__).parent

def digest(b):return hashlib.sha256(b).hexdigest()

def run():
 checks=[]
 for source in [m.SOURCE_ID,m.GREELEY_SOURCE_ID,m.WELD_SOURCE_ID,*m.GRID_SOURCES,m.SPRINGS_SOURCE_ID,m.EHS_SOURCE_ID]:
  r=m.lookup(ROOT,source,list_rows=True)
  for ext,text in [('json',r.model_dump_json(indent=2)+'\n'),('md',m.render_markdown(r))]:
   normalized=text.replace(str(ROOT),'__REPOSITORY__')
   baseline=(FIXTURE_BASE/'fixtures/seven-native-sources'/f'{source}.{ext}').read_text()
   if normalized!=baseline:raise ValueError('Legacy output changed: '+source+'.'+ext)
   checks.append({'source':source,'format':ext,'status':'byte_equal','sha256':digest(normalized.encode())})
 details=[]
 for source,config in m.DP_SOURCES.items():
  r=m.lookup(ROOT,source,list_rows=True)
  qa=json.loads((ROOT/'research/local_review'/config['folder']/'SOURCE_QA.json').read_bytes())
  if len(r.rows)!=len(qa['rows']) or len(r.rows)!=44:raise ValueError('Row count')
  for actual,expected in zip(r.rows,qa['rows'],strict=True):
   if actual.row_id!=expected['row_id']:raise ValueError('Row identity')
   expected_cells=expected['cells'] if source==m.DOUGLAS_SOURCE_ID else [expected['application'],expected['fee']]
   for cell,want in zip(actual.cells,expected_cells,strict=True):
    field=want.get('field',want.get('role'));display=want.get('displayed_text',want.get('reviewed_display'))
    if (cell.field,cell.displayed_text,cell.native_text)!=(field,display,want['native_text']):raise ValueError('Cell association')
    for span in cell.native_spans:
     original=Path(span.native.path).read_bytes()
     if original[span.start:span.end]!=span.text.encode():raise ValueError('Native span')
     if digest(span.text.encode())!=span.sha256:raise ValueError('Span digest')
   if source==m.PUEBLO_SOURCE_ID and [x.model_dump() for x in actual.nested]!=expected['nested']:raise ValueError('Nested association')
  if r.source.source.sha256!=r.source.canonical_original.sha256:raise ValueError('Canonical equality')
  if r.source.authority_id!=config['authority']:raise ValueError('Authority identity')
  blanks=[row.row_id for row in r.rows if row.cells[-1].native_text is None]
  if source==m.DOUGLAS_SOURCE_ID and blanks!=['STATE-16','STATE-17']:raise ValueError('Blank fee identity')
  no=m.lookup(ROOT,source,'__no_such_service_independent__')
  if no.status!='no_matching_row' or no.rows or no.context!=r.context or no.annotations!=r.annotations:raise ValueError('No-match context lost')
  if m.lookup(Path('/not-a-repo'),source,'today').status!='refused_current_law':raise ValueError('Current-law refusal')
  query='transmitted' if source==m.DOUGLAS_SOURCE_ID else 'fees per plat'
  selected=m.lookup(ROOT,source,query)
  if source==m.DOUGLAS_SOURCE_ID and (selected.rows or selected.status!='matched_context_only'):raise ValueError('Context-only')
  if source==m.PUEBLO_SOURCE_ID and ([x.row_id for x in selected.rows]!=['P4-01'] or len(selected.rows[0].nested)!=3):raise ValueError('Nested enclosing row')
  details.append({'source':source,'rows':len(r.rows),'contexts':len(r.context),'annotations':len(r.annotations),'nested':sum(len(x.nested) for x in r.rows),'blank_fee_rows':blanks,'canonical_pdf_sha256':r.source.source.sha256,'http_completed_at':r.source.http_response_completed_at.isoformat(),'intake_received_at':r.source.intake_received_at.isoformat(),'no_match_preserves_context':True,'native_cell_associations':'exact','legal_currentness':r.legal_currentness})
 return {'status':'PASS','legacy_output_comparisons':checks,'new_source_checks':details,'public_requests':0,'scope':'No new source-page QA; compares output with accepted QA metadata and unchanged native bytes.'}
if __name__=='__main__':print(json.dumps(run(),indent=2))
