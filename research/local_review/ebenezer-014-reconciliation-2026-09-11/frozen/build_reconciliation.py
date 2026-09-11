"""Build the bounded EB014 reconciliation; never changes its source inputs."""
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json
import pymupdf
import jsonschema
from reconciliation_models import Reconciliation, Decision, FileRef, SourceSupport, FontSpan
B = Path(__file__).parent
P = 'comparison/committed-package/'

def ref(path):
    p = B / path
    return FileRef(path=path, sha256=sha256(p.read_bytes()).hexdigest(), size_bytes=p.stat().st_size)

def save(name, model):
    data = json.loads(model.model_dump_json())
    schema = type(model).model_json_schema()
    jsonschema.Draft202012Validator(schema).validate(data)
    (B / (name + '.json')).write_text(model.model_dump_json(indent=2) + '\n')
    (B / (name + '.schema.json')).write_text(json.dumps(schema, indent=2) + '\n')

pdfref = ref(P + 'source/original.pdf')
font_rows = []
with pymupdf.open(B / pdfref.path) as pdf:
    for block in pdf[4].get_text('dict')['blocks']:
        for line in block.get('lines', []):
            for s in line['spans']:
                if any(t in s['text'] for t in ['Our Climate Future', 'cited and referred', 'referenced in the Land Use Code']):
                    font_rows.append(FontSpan(physical_page=5, text=s['text'], font=s['font'], flags=s['flags'], bbox=list(s['bbox'])))
    links = [dict(xref=l['xref'], uri=l['uri'], rect=list(l['from'])) for l in pdf[1].get_links()]
support = SourceSupport(source_pdf=pdfref, pymupdf_version='1.28.2', selected_font_spans=font_rows,
    page2_uri_annotations=links, purpose='Limited font and URI metadata corroboration. These are source PDF data, not visual Unicode certification, live link tests, or evidence of current law.', network_requests=0, legal_currentness='not_verified')
save('SOURCE_SUPPORT', support)
rows = (B / 'received/PASS2_REVIEW.md').read_text().splitlines()
obs = json.loads((B / (P + 'audit/SOURCE_QA.json')).read_text())['observations']
obs_ids = {x['id'] for x in obs}
D = []
def decision(id, kind, disposition, pages, numbers, observation, qualification, prefix=None):
    prefix = prefix or '| ' + id + ' |'
    matches = [(i + 1, s) for i, s in enumerate(rows) if s.startswith(prefix)]
    assert len(matches) == 1, (id, matches)
    line, claim = matches[0]
    ids = [x['id'] for x in obs if int(x['id'].split('-O')[1]) in numbers]
    assert len(ids) == len(numbers)
    D.append(Decision(id=id, kind=kind, disposition=disposition, external_report='PASS2_REVIEW.md',
        external_line=line, external_claim=claim, physical_pages=pages,
        page_images=[ref(P + f'images/page-{n:04}.png') for n in pages], atlas_observation_ids=ids,
        source_observation=observation, qualification=qualification, native_text_change_required=False,
        legal_currentness='not_verified'))

def finding(n, disposition, pages, numbers, observation, qualification):
    decision(f'EB014-P2-{n:03}', 'external_finding', disposition, pages, numbers, observation, qualification)

finding(1, 'qualified', [1], [1],
    'The full cover and bottom-region crop show no visible footer or printed 1-0. Fresh extraction nevertheless reproduces the entire footer from the original PDF.',
    'Accept the visible/native discrepancy. Spurious must not mean fabricated or absent from the PDF: preserve the exact bytes and label them not visible in the checked render. The cover article banner IS visible. No author-intent or rendering-mechanism conclusion follows.')
finding(2, 'accepted', [1], [2],
    'Visible order is the top banner, City logo, large ARTICLE 1, then General Purpose and Provisions. Native text reverses the two large title blocks.',
    'This is reading-order metadata. The candidate remains unchanged, with visible order stored separately.')
finding(3, 'accepted', [1], [3],
    'The image wordmark visibly reads City of above Fort Collins and includes a stylized mountain/wave graphic. No separate native logo words are extracted.',
    'Record image-only words separately; do not invent a native byte span or replace the candidate.')
finding(4, 'accepted', [2], [4],
    'The top image wordmark reads City of / Fort Collins. It is not separately extracted as native logo text.',
    'The graphical wordmark is source-image evidence, not a new publisher or ownership verification.')
finding(5, 'source_observation', [2], [4],
    'The lower page contains a color streetscape photograph. Native text does not encode that image as prose.',
    'Expected image omission is not a word-transcription error. No location, building identity, photograph date, or exact scene inventory is certified; Pass 1 calls it Old Town without a source caption establishing that identity.')
finding(6, 'qualified', [2], [5, 6],
    'The email address, reasonable-accommodation label, and displayed Non-Discrimination address are blue and underlined. The PDF also contains three URI annotations reproduced in SOURCE_SUPPORT.json.',
    'The external reviewer correctly limited a pixel-only reading. Atlas can resolve embedded destinations as PDF metadata, including the nonprinted OpenForms URL; no link was opened and no present availability or validity is established.')
finding(7, 'qualified', [3], [7],
    'The contents-page full image and top/bottom crops show neither the recurring article banner nor the 1-1 footer. Both are reproducible native text in the original PDF.',
    'Preserve rather than delete those native bytes. The visible City of Fort Collins - Land Use Code contents heading is distinct and must remain visible. Do not confuse extracted 1-1 here with physical page 4, which visibly prints 1-1.')
for n, page, number in [(8, 4, 9), (9, 5, 10), (10, 6, 11), (11, 7, 12)]:
    finding(n, 'accepted', [page], [number],
        f'Physical page {page} visibly has the banner at top and printed 1-{page-3} footer at bottom. Native text places the footer before header/body.',
        'The native ordering is preserved; record the footer location separately from its position in extraction.')
finding(12, 'qualified', [5], [17],
    'Our Climate Future alone is visibly italic in item C. The PDF span is GothamNarrow-BookItalic; surrounding prose is roman.',
    'Accept the style observation, not a missing-word finding. Plain text has no italic markup by design. An annotation can preserve emphasis without editing native text; no exhaustive font inventory is claimed.')
finding(13, 'qualified', [3, 4, 5, 6, 7], [8, 13, 16, 20, 24, 25, 28],
    'Fresh extraction reproduces narrow no-break spaces, including U+202F between some section numbers and headings. The candidate preserves them.',
    'The native character value can be checked in bytes, but pixels alone cannot certify Unicode. These are not shown to be inserted packaging errors: preserve them and do not count their presence as a lexical correction.')
finding(14, 'source_observation', [5], [16],
    'The title crop shows visibly different quote shapes around the long titles versus LUC and Code. Native text preserves straight double quotes for the long titles and curly double quotes for LUC/Code.',
    'The mixture is source/native evidence, not a demonstrated transcription error. Exact codepoints are certified only as extracted bytes, not inferred from pixels. Do not normalize the title punctuation.')
finding(15, 'source_observation', [4], [15],
    'The organization paragraph visibly uses curved paired quotation marks around LUC and Code; the native text has curly quote characters.',
    'Agreement is not a candidate error. Glyph appearance and native codepoints remain distinct evidence.')
finding(16, 'source_observation', [3, 7], [8, 26],
    'The contents entry repeats Conflict, and the body heading repeats CONFLICT. Both match the candidate.',
    'Preserve the repeated word; do not silently rewrite the heading or infer a legal hierarchy from the title alone.')
finding(17, 'source_observation', [7], [27],
    'The visible clause reads Articles 2, 3, or 4 a standard or requirement in Article 5, with no conjunction between 4 and a.',
    'The source grammatical gap is real. Do not select and, or, punctuation, or another editorial repair.')
finding(18, 'source_observation', [7], [29],
    'The severability paragraph visibly reads the City. it is the further intent, with lowercase it.',
    'Preserve the capitalization anomaly; it does not establish invalidity or present legal effect.')
finding(19, 'source_observation', [6], [21, 22],
    'The source crop visibly reads interpretation - 4 - and application inside the paragraph; native text matches.',
    'This is not merely a displaced footer or candidate-only artifact. Preserve the inline token without treating it as the physical or printed page number.')
finding(20, 'source_observation', [6], [20],
    'The Authority crop visibly reads Charter of The City of Fort Collins; The begins with a capital T. A semicolon appears after Colorado Constitution.',
    'This confirms the bounded printed wording, not the cited authorities or operative status.')
finding(21, 'source_observation', [4], [14, 15],
    'The full page and crop from Article 7 through the first organization paragraph contain no mid-page - 4 - token.',
    'The reported false caption is not authoritative evidence. The candidate and Pass 1 correctly omit such a token at this location.')
decision('E1', 'external_erratum', 'qualified', [1, 2], [3, 4],
    'The graphic is part of the City wordmark: it begins to the left of Fort and extends beneath Fort Collins as a sweeping shape. Both full-page logos support this coarse spatial description.',
    'Accept caution about exact design geometry. A binary beside-versus-beneath uncertainty is too crude: the graphic spans both regions. Pass 1 under is incomplete, not grounds to remove the visible graphic or invent a new logo.', prefix='| E1 |')
decision('E2', 'external_erratum', 'accepted', [6], [20],
    'The enlarged Authority crop confirms capital The and the semicolon after Constitution.',
    'Confidence can be increased for this visual wording. This is not independent confirmation of charter identity or legal authority.', prefix='| E2 |')
decision('E3', 'external_erratum', 'source_observation', [4], [14, 15],
    'No - 4 - appears between the article list and first paragraph.',
    'This is an affirmation of an already-correct omission, not a third new correction to the frozen Pass 1 wording.', prefix='| E3 |')
themes = [
    ([1,3,4,5,6,7], [1,7,15,16], 'Native bytes establish the extracted dash/quote/space character values. Crops support visible shapes and the mixed title quotes.', 'Exact original character encoding, all font styles and pixels-to-Unicode equivalence remain outside certification. Do not normalize source bytes.'),
    ([2], [6], 'Three embedded destinations are reproduced: mailto:adacoordinator@fortcollins.gov; https://us.openforms.com/Form/0be76172-63ca-4592-b47b-efeb16d85d6b; http://fortcollins.gov/Non-Discrimination.', 'Resolved only as offline PDF annotation metadata. Destinations are not wholly printed, none was opened, and there is no present-service claim.'),
    ([2], [4], 'A streetscape photograph with brick building, vegetation and overhead circular/line features is visible. No photograph caption identifying place, date or building appears.', 'No exhaustive fine inventory or Old Town identification is accepted from the report alone. This is non-text context, not missing operative wording.'),
    ([1,2], [3,4], 'The mountain/wave graphic lies left of and below the wordmark and sweeps underneath it.', 'This resolves broad placement directly. Exact contour measurements, design intent and formal logo specifications remain unverified; conflicting captions do not control the pixels.'),
    ([1,3], [1,7], 'The original PDF itself yields the footer/banner strings during fresh extraction, while full renders and targeted crops do not display them.', 'Existence in PDF/native text is verified. The rendering cause, paint-order occlusion, hidden-layer organization and author intent were not reconstructed or certified. Call the bytes not visible in the checked render, not fabricated or legally operative.'),
]
for i, (pages, numbers, observation, qualification) in enumerate(themes, 1):
    prefix = f'{i}. ' + ['Exact Unicode codepoints', 'Exact hyperlink destinations', 'Fine inventory', 'Logo lockup geometry', 'Whether any invisible'][i-1]
    decision(f'U{i}', 'unresolved_theme', 'qualified', pages, numbers, observation, qualification, prefix)
limits = [
    'Candidate-aware Atlas reconciliation, not blind review. All seven complete source images and eleven named crops were directly inspected after exposure to the candidate, earlier Atlas QA, and external reports. External self-reported blindness, crop operations and times are not independently certified.',
    'The four external files are frozen byte-identically. All 14 distinct advertised full asset digests match local packet/queue/committed bytes. External completion explicitly says original.pdf was absent from its work directory and was bound rather than locally rehashed; Atlas independently hashes the actual 340287-byte PDF. These are different custody claims.',
    'Comparison is fixed at commit 95155c235bc64756c6ed1cdf9014cd920fe30fcc. Fifty-six committed package files plus two packet/queue copies are retained. The existing external-review-pending state is preserved as historical package data; this additive audit does not rewrite it.',
    'The reported 2 critical, 12 minor and 7 info rows sum to 21; three errata and five unresolved themes are separate. This is not certification of 21 errors, 14 text corrections, or three changed Pass 1 passages. Several rows are expected plain-text limitations, agreements or source anomalies.',
    'All 13579 native bytes remain unchanged, as do the 14370-byte candidate and original PDF. No substantive word or number correction was identified. Visible-order and image-only evidence must remain separate from the native transcription.',
    'Purpose items A-L continue as M-N and retain the following qualification, including the explicit-reference exception, Sections 1.2.4, 6.8.2 and 6.14.4 and contextual limits. The ongoing-use paragraph on physical page 7 continues section 1.2.4 before minimum standards. Existing five associations remain intact.',
    'This source contains Article 1 only. References to seven articles, city authority, adoption by reference, applicability or hierarchy are source wording; other articles, the adopting instrument and amendment chain were not verified. No visible edition, adoption or effective date is established by these seven pages; PDF metadata timestamps are not legal dates.',
    'No network requests, links opened, external messages, candidate edits, source edits, repository writes, semantic promotion, coverage promotion or currentness promotion were performed.',
]
m = Reconciliation(schema_version=1, assignment='EB-PDF-014', source_id='fort-collins-land-use-article-1-sd005-07', authority_id='CO-MUNICIPAL-FORT_COLLINS', reviewed_at=datetime.now(timezone.utc), comparison_commit='95155c235bc64756c6ed1cdf9014cd920fe30fcc', status='reconciled_with_qualifications_no_source_changes', review_mode='candidate_aware_direct_image_review_with_native_support', physical_pages_directly_inspected=list(range(1,8)), directly_inspected_crops=[ref('crops/'+x+'.png') for x in ['p1-logo','p4-list-transition-quotes','p5-title-quotes','p5-italics','p6-authority']]+[ref(P+'audit/'+x+'.png') for x in ['p1-native-footer-region','p3-native-header-region','p3-native-footer-region','p6-inline-page-token','p7-conflict-wording','p7-severability']], source_pdf=pdfref, native_candidate=ref(P+'candidate.txt'), committed_review=ref(P+'reviewed-text.json'), receipts=[ref(x+'.json') for x in ['CUSTODY_RECEIPT','COMPARISON_RECEIPT']], supplemental_evidence=[ref('SOURCE_SUPPORT.json')], external_counts=dict(finding_rows=21,critical=2,minor=12,info=7,errata_rows=3,unresolved_themes=5,arithmetic_matches=True,unique_error_count_certified=False), decisions=D, disposition_counts=dict(Counter(x.disposition for x in D)), method_and_limits=limits, original_source_and_candidate_changed=False, external_reports_changed=False, production_changes=False, network_requests=0, legal_currentness='not_verified')
save('RECONCILIATION', m)
lines = ['---', 'title: "EB014 external-report reconciliation"', 'assignment: "EB-PDF-014"', 'reviewed_at: "'+m.reviewed_at.isoformat()+'"', 'status: "reconciled_with_qualifications_no_source_changes"', 'review_mode: "candidate_aware_direct_image_review_with_native_support"', 'legal_currentness: "not_verified"', '---', '', '# EB014 external-report reconciliation', '', 'All seven complete source pages and eleven focused crops were checked. No substantive native word or number correction was found. The four received reports remain unchanged. This audit disposes all 21 findings, three errata and five unresolved themes; the reported severity totals describe the external report, not a certified count of errors.', '', 'The cover footer and contents-page banner/footer are not visible in the checked images, but are real text extracted from the source PDF. Their original bytes remain preserved. Mixed title quotes, the inline - 4 -, the missing conjunction and lowercase it are source features, not cleanup instructions.', '', '## Dispositions', '', '| External item | Atlas disposition | Direct-source conclusion and limit |', '|---|---|---|']
for d in D:
    lines.append('| '+d.id+' | '+d.disposition.replace('_',' ')+' | '+(d.source_observation+' '+d.qualification).replace('|','\\|').replace('\n',' ')+' |')
lines += ['', '## Scope and custody', ''] + ['- '+x for x in limits]
lines += ['', '## Verification', '', 'The accompanying read-only validator checks strict models and JSON Schemas, frozen hashes, every exact external row, all 29 decisions, seven page identities, original native extraction, all existing observation spans and PDF links, the five new crop reproductions and the copied committed package. The saved validation result records the actual run; the validator does not certify unseen historical reviewer actions or legal currentness.', '', '```sh', "PYTHONDONTWRITEBYTECODE=1 /private/tmp/geode-status-venv/bin/python validate_reconciliation.py --check-originals", '```', '']
(B/'ATLAS_RECONCILIATION.md').write_text('\n'.join(lines))
print('Built', len(D), 'decisions:', m.disposition_counts)
