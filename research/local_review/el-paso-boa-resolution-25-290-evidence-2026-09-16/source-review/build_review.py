"""Write typed literal visual review; never infer an adoption chain or current law."""
from datetime import datetime,timezone
from hashlib import sha256
from html.parser import HTMLParser
import json
from pathlib import Path
import sys
import pymupdf
from models import Access,Render,Review
ROOT=Path(__file__).resolve().parent
P1='''Resolution No. 25-290

BOARD OF COUNTY COMMISSIONERS
OF EL PASO COUNTY, COLORADO

RESOLUTION TO DISSOLVE AND RECONSTITUTE THE EL PASO COUNTY BOARD OF ADJUSTMENT AND THEREAFTER APPOINT THE EL PASO COUNTY BOARD OF COUNTY COMMISSIONERS TO SERVE AS THE EL PASO COUNTY BOARD OF ADJUSTMENT

WHEREAS, pursuant to C.R.S. §§ 30-11-101, 30-11-103, and 30-11-107, the Board of County Commissioners of El Paso County, Colorado (hereinafter “Board” or “County”), has the legislative authority to manage the business and concerns of the County when deemed by the Board to be in the best interests of the County; and

WHEREAS, pursuant to C.R.S. § 30-28-117, the Board shall provide for a Board of Adjustment (“BOA”) of three to five members and for the appointment of such members; and

WHEREAS, historically, the Board has appointed volunteers to serve on the BOA, and in recent years, the BOA has met sparsely during each calendar year; and

WHEREAS, El Paso County staff has recommended the Board consider appointing itself as the BOA given the relatively low number of matters that go before the BOA and to better serve El Paso County residents through greater efficiencies; and

WHEREAS, final actions of the BOA are appealable directly to district court and do not go before the Board, and the Board finds that final actions on behalf of the County are best suited to be determined by the Board, as elected officials, who are ultimately accountable to the residents of El Paso County; and

WHEREAS, the Board of County Commissioners is authorized to appoint the Board of County Commissioners to serve as the Board of Adjustment; and

WHEREAS, the Board has determined that it is well suited to serve as the BOA and desires to appoint the Board to serve as the BOA; and

WHEREAS, the Board expresses its sincere gratitude to all of the volunteers who have offered their time and service to serve on previous Boards of Adjustment; and

WHEREAS, the Board hereby finds, determines, and declares that adoption of this Resolution is necessary for the preservation and protection of the public health, safety and welfare of the inhabitants of El Paso County.'''
P2='''NOW THEREFORE, BE IT RESOLVED that the Board of County Commissioners of El Paso County, Colorado, hereby dissolves the El Paso County Board of Adjustment and repeals and rescinds Resolution No. 22-401 recorded at Reception No. 222141805 in the records of the El Paso County Clerk and Recorder’s Office, and that to the extent any other prior resolutions are inconsistent with this Resolution, the terms of this Resolution shall control.

BE IT FURTHER RESOLVED that the Board hereby immediately appoints the El Paso County Board of County Commissioners to serve as to the El Paso County Board of Adjustment.

BE IT FURTHER RESOLVED that the Board intends to concurrently adopt and approve Amended Legislative and Parliamentary Rules and Procedures to incorporate revisions necessary to reflect the Board’s procedures when sitting as the Board of Adjustment and which shall serve as the Board of Adjustment’s rules of procedure.

BE IT FURTHER RESOLVED that the Chair and Vice Chair of the Board of Adjustment shall be the same as those of the Board.

BE IT FURTHER RESOLVED that El Paso County staff is directed to review the Land Development Code and propose any necessary amendments thereto to ensure conformity with this Resolution.

BE IT FURTHER RESOLVED that Carrie Geitner, duly elected qualified member and Chair of the Board of County Commissioners, or Holly Williams, duly elected, qualified member and Vice Chair of the Board of County Commissioners be and is hereby authorized and appointed on behalf of the Board to execute any and all documents necessary to carry out the intent of the Board as described herein, specifically any documents related to titling.

DONE THIS 28th day of October, 2025 at Colorado Springs, Colorado.'''

def now():return datetime.now(timezone.utc).isoformat()
def asset(path):
    raw=(ROOT/path).read_bytes()
    return {'path':path,'sha256':sha256(raw).hexdigest(),'size_bytes':len(raw)}
def save(name,model,obj):
    (ROOT/(name+'.schema.json')).write_text(json.dumps(model.model_json_schema(),indent=2)+'\n')
    value=model.model_validate_json(json.dumps(obj))
    (ROOT/(name+'.json')).write_text(value.model_dump_json(indent=2)+'\n')

class Links(HTMLParser):
    """Read exact retained public href and its displayed anchor label."""
    def __init__(self):super().__init__();self.href=None;self.words=[];self.found=[]
    def handle_starttag(self,tag,attrs):
        if tag=='a':self.href=dict(attrs).get('href');self.words=[]
    def handle_data(self,text):
        if self.href:self.words.append(text)
    def handle_endtag(self,tag):
        if tag=='a':
            if self.href and self.href.endswith('/25-290.pdf'):
                self.found.append((self.href,' '.join(''.join(self.words).split())))
            self.href=None

def main():
    if (ROOT/'SOURCE_REVIEW.json').exists():raise ValueError('Already written')
    parser=Links();parser.feed((ROOT/'referring-homepage.html').read_text())
    url='https://epc-assets.elpasoco.com/wp-content/uploads/sites/12/Misc/25-290.pdf'
    if parser.found!=[(url,'Resolution to Dissolve')]:raise ValueError('Referring anchor differs')
    events=[]
    for path,seq in [('event-01.json',1),('escalated/event-01.json',2),('curl-event-03.json',3),('curl-event-04.json',4)]:
        value=json.loads((ROOT/path).read_text());value['sequence']=seq;events.append(value)
    save('COMBINED_ACCESS',Access,{'recorded_at':now(),'request_cap':8,'distinct_target_cap':6,
        'per_response_byte_cap':10485760,'aggregate_byte_cap':20971520,
        'deliberate_attempts':4,'distinct_targets':2,'retained_body_bytes':316142,
        'tls_verification':True,'cookies_or_authentication_used':False,'events':events,
        'limitations':['Four deliberate attempts: default sandbox DNS failure, Python verified-TLS chain failure outside sandbox, one root-authorized ordinary system-curl homepage GET, and its exact linked PDF GET. Last two returned HTTP200 without redirects.',
            'Default trust settings were never changed and no insecure flags were used. Each client used its own default certificate validation; successful system curl is not a claim that the Python trust chain was repaired.',
            'Only a selected public header derivative is retained; omitted header names are preserved without their values. No complete raw-header record or upstream credential-cleansing certification is claimed.',
            'Body sizes count network response bodies once, not duplicate friendly local copies. Hidden wire/DNS/TLS packets are not counted as deliberate requests.']})
    observed=json.loads((ROOT/'render-observed.txt').read_text())
    crops=[]
    for n,name,box in [(1,'recording-stamp',[1350,2800,2480,3160]),(2,'execution',[300,2040,2400,2930])]:
        crops.append({'page':n,'input_path':f'page-{n}.png','input_sha256':asset(f'page-{n}.png')['sha256'],
            'pixel_box':box,'output_path':name+'.png','output_sha256':asset(name+'.png')['sha256']})
    save('RENDER',Render,{**observed,'pymupdf_version':pymupdf.VersionBind,
        'native_method':"get_text('text', flags=195, sort=False), UTF-8; both empty. No OCR was run; reviewed wording is an explicitly separate manual visual transcript.",
        'native_bytes_per_page':[0,0],'crops':crops})
    data={'source_id':'el-paso-boa-resolution-25-290-directed-lead','authority_id':'CO-COUNTY-EL_PASO',
        'reviewed_at':now(),'reviewer':'Plato',
        'method':'Direct view_image display of both complete source pages, then unchanged native extraction (empty), then two exact pixel crops. Manual visual wording, whitespace/line wrapping normalized; no OCR or independent-model-family claim.',
        'source':asset('original.pdf'),'referring_html':asset('referring-homepage.html'),
        'referring_href':url,'referring_anchor_text':'Resolution to Dissolve',
        'pages':[{'physical_page':1,'image':asset('page-1.png'),'native':asset('page-1.native.txt'),
            'directly_viewed':True,'reviewed_text':P1,'observations':[
                'Complete heading and nine WHEREAS recitals transcribed above. Reference to three to five BOA members is the resolution’s own statement of C.R.S. §30-28-117; statute not separately checked.',
                'Handwritten upper-left mark resembles BoCC; no author or legal significance inferred. Printed page number 1.',
                'Recording stamp separately reads Steve Schleiker; 10/29/2025 08:47:03 AM; Doc $0.00; Rec $0.00; 2 Pages; El Paso County, CO; 225094063, with barcode. The exact focused crop is retained; this is not independent recorder-database verification.'
            ]}, {'physical_page':2,'image':asset('page-2.png'),'native':asset('page-2.native.txt'),
            'directly_viewed':True,'reviewed_text':P2,'observations':[
                'Six resolution paragraphs (one NOW THEREFORE and five BE IT FURTHER RESOLVED) plus the DONE date line are transcribed. Printed page number 2.',
                'Preserve the anomalous words "to serve as to the El Paso County Board of Adjustment" and "duly elected qualified member"; do not silently repair grammar.',
                'The statement that the Board intends to concurrently adopt amended rules is not proof those separate rules were adopted. The direction to staff to review/propose LDC amendments is not evidence of a completed code amendment.',
                'Printed execution block: ATTEST: By: Steve Schleiker / El Paso County Clerk and Recorder; BOARD OF COUNTY COMMISSIONERS / EL PASO COUNTY, COLORADO; By: Carrie Geitner. Seal and handwritten marks overlap the attestation area; no handwritten identity, wet execution, signature authenticity or independent adoption certification is asserted.',
                'The source refers to Resolution No.22-401 and Reception No.222141805. That instrument and recorder entry were not retrieved or reviewed in this task.'
            ]}],
        'status':'literal_source_review_pending_atlas_acceptance','legal_currentness':'not_verified','answer_safe':False,
        'source_date_claims':['Printed DONE statement: 28th day of October, 2025 at Colorado Springs, Colorado.',
            'Recording-stamp statement: 10/29/2025 08:47:03 AM, separate from the DONE date and today’s actual acquisition times.'],
        'limitations':['This is a newly acquired literal source lead with an exact current official referral. No complete adoption chain, current law, supersession, continuing operative status or conclusion about the older Chapter Two is certified.',
            'Full images and focused crops were directly viewed; exact Unicode, typography, marginal handwriting and signature identities are not mechanically certified by a manual transcript.',
            'Both native extractions are zero bytes; they are preserved honestly, not labelled a valid source-text candidate. No OCR candidate exists in this packet.',
            'No original source, canonical record, raw/control ledger, inventory, Git state or external agent assignment was changed. No additional source documents were opened.']}
    save('SOURCE_REVIEW',Review,data)
    md='---\nsource_id: el-paso-boa-resolution-25-290-directed-lead\nstatus: literal_source_review_pending_atlas_acceptance\nlegal_currentness: not_verified\n---\n# Literal visual transcript\n\nManual transcription of printed body; whitespace normalized. Marginal, stamp and signature observations remain separate in SOURCE_REVIEW.json.\n\n## Page 1\n\n'+P1+'\n\n## Page 2\n\n'+P2+'\n'
    (ROOT/'TRANSCRIPT.md').write_text(md)
    sys.stdout.write('Typed source review, actual access receipt and render receipt written.\n')
if __name__=='__main__':main()
