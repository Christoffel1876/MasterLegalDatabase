"""Meaningful in-memory corruption checks; no source or canonical modifications."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from pydantic import ValidationError

from review_models import Review
from verify_review import verify_content

ROOT=Path(__file__).resolve().parent


class ReviewTests(unittest.TestCase):
    """Preserve exact content, exceptions, source anomalies and paragraph associations."""

    @classmethod
    def setUpClass(cls) -> None:
        """Capture fixture bytes once; execute no public requests."""
        cls.data={p.relative_to(ROOT).as_posix():p.read_bytes()
                  for p in ROOT.rglob('*') if p.is_file()}
        cls.review=Review.model_validate_json(cls.data['SOURCE_QA.json'])

    def modified(self) -> Review:
        """Create an isolated model copy for negative checks."""
        return deepcopy(self.review)

    def test_complete_baseline(self) -> None:
        """All native bytes and complete paragraphs reproduce."""
        result=verify_content(self.review,self.data)
        self.assertEqual(result,{'pages':7,'native_bytes':19118,'candidate_bytes':19272,
                                 'passages':78,'native_lines':894,'crops':4})

    def test_exception_omission(self) -> None:
        """Removing the effective-date exception is rejected."""
        r=self.modified()
        p=next(p for p in r.checked_passages if p.id=='2.11O')
        p.text=p.text.replace(', unless otherwise provided by the Board of Health','')
        with self.assertRaisesRegex(ValueError,'wording'):
            verify_content(r,self.data)

    def test_source_anomaly_repair(self) -> None:
        """An apparently helpful spelling correction must fail."""
        r=self.modified()
        p=next(p for p in r.checked_passages if p.id=='2.7F')
        p.text=p.text.replace('EXECITOVE','EXECUTIVE')
        with self.assertRaisesRegex(ValueError,'wording'):
            verify_content(r,self.data)

    def test_invented_emergency_letter(self) -> None:
        """The final unlettered paragraph cannot acquire a printed Q."""
        r=self.modified()
        next(p for p in r.checked_passages if p.id=='2.11-UNLETTERED').label_as_printed='Q.'
        with self.assertRaisesRegex(ValueError,'Invented'):
            verify_content(r,self.data)

    def test_cross_page_wrong_parent(self) -> None:
        """Definition F cannot migrate to the following section."""
        r=self.modified()
        next(p for p in r.checked_passages if p.id=='2.7F').parent_id='2.8'
        with self.assertRaisesRegex(ValueError,'association'):
            verify_content(r,self.data)

    def test_nested_wrong_parent(self) -> None:
        """Certificate item 1 remains nested under F."""
        r=self.modified()
        next(p for p in r.checked_passages if p.id=='2.10F.1').parent_id='2.11'
        with self.assertRaisesRegex(ValueError,'association'):
            verify_content(r,self.data)

    def test_dropped_footer(self) -> None:
        """Every repeated footer date is required, including page seven."""
        r=self.modified();r.checked_passages=[p for p in r.checked_passages if p.id!='P7-DATE']
        with self.assertRaisesRegex(ValueError,'complete'):
            verify_content(r,self.data)

    def test_changed_native_or_image(self) -> None:
        """Captured source bytes must remain exactly frozen, even at equal size."""
        for name in ['native/page-0004.native.txt','pages/page-0005.png']:
            with self.subTest(name=name):
                data=dict(self.data);raw=data[name];data[name]=bytes([raw[0]^1])+raw[1:]
                with self.assertRaisesRegex(ValueError,'identity'):
                    verify_content(self.review,data)

    def test_omitted_native_whitespace(self) -> None:
        """Unchanged raw evidence cannot silently drop its leading blank line."""
        r=self.modified();r.pages[0].native_lines.pop(0)
        with self.assertRaisesRegex(ValueError,'coverage'):
            verify_content(r,self.data)

    def test_operativity_and_http_promotion(self) -> None:
        """Strict schema refuses date, currentness and HTTP verification promotions."""
        for transform in [lambda d:d.update(legal_currentness='verified'),
                          lambda d:d['dates'][0].update(operative_date_certified=True),
                          lambda d:d['provenance'].update(original_http_independently_verified=True)]:
            d=self.review.model_dump(mode='json');transform(d)
            with self.assertRaises(ValidationError):
                Review.model_validate_json(json.dumps(d))

    def test_changed_transcript(self) -> None:
        """The readable derivative cannot contradict the checked records."""
        data=dict(self.data)
        data['REVIEWED_TRANSCRIPT.md']=data['REVIEWED_TRANSCRIPT.md'].replace(b'in compliance',b'in noncompliance')
        with self.assertRaisesRegex(ValueError,'Readable transcript'):
            verify_content(self.review,data)

    def test_dropped_heading_markup(self) -> None:
        """Source heading underlining is retained without inferred amendment meaning."""
        r=self.modified();next(p for p in r.checked_passages if p.id=='2.8').visible_markup=[]
        with self.assertRaisesRegex(ValueError,'markup'):
            verify_content(r,self.data)


if __name__=='__main__':
    unittest.main()
