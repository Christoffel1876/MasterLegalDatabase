"""The frozen retrieval verifier may print one known dependency notice before JSON."""
import json

import pytest
from validate_preparation import parse_historical_output

NOTICE = ('warning: The `fitz` API is deprecated and will be removed in future. '
          'Use `import pymupdf` instead.')


@pytest.mark.parametrize('prefix', ['', NOTICE + '\n'])
def test_exact_known_output(prefix):
    expected = {'status': 'PASS', 'pdf_count': 2, 'structural_pdf_pages': 21}
    assert parse_historical_output(prefix + json.dumps(expected) + '\n') == expected


@pytest.mark.parametrize('text', ['', 'garbage', 'other warning\n{}',
                                 '{}\n{}', NOTICE + '\n' + NOTICE + '\n{}', '[]'])
def test_unexpected_output_refused(text):
    with pytest.raises(ValueError):
        parse_historical_output(text)
