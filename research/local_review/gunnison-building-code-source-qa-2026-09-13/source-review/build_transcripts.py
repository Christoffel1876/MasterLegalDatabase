"""Preserve candidate-aware visual corrections in new files; never alter OCR."""
from pathlib import Path
from prepare import ROOT, write

# Crop-backed visual corrections below are editorial records, not source amendments.
BODY_END = {
    1: 'code update and has recommended adoption to the Board; and',
    2: 'effective January 1, 2024, by this action.',
    4: 'the required permit fees.',
    5: 'Resolution Section 8-103: Appeals.',
    6: 'months of the application submittal date.',
    7: 'Heating temperature difference: 92',
    8: 'Developed per ANSI/RESNET/ICC 301.',
    9: 'Appendix AS Strawbale Construction: Include the entire section.',
    10: 'Resolution Section 8-103: Appeals.',
    11: 'all occupancies.',
    12: 'Exception #2: New one-family dwellings greater than 5,000 square feet Gross Floor',
    13: 'ANSI/RESNET/ICC 301 standard.',
    14: 'Section 112 Board of Appeals, Section 112.1 General: Replace with the following:',
    15: 'of the building area.',
    16: 'Section 602 Automatic Sprinkler Systems, Section 602.1 General: Delete section.',
}

CORRECTIONS = {
    2: [("7' day", '7th day'),
        ('1. The "International Building Code",\n, 2021 edition',
         '1. The "International Building Code", 2021 edition'),
        ('The "International Residential Code"\n, 2021 edition',
         'The "International Residential Code", 2021 edition'),
        ('The "International Mechanical Code", 2021 edition',
         '3. The "International Mechanical Code", 2021 edition'),
        ('The "International Energy Conservation Code", 2021 edition',
         '5. The "International Energy Conservation Code", 2021 edition'),
        ('The "International Existing Building Code"\n", 2021 edition',
         'The "International Existing Building Code", 2021 edition')],
    4: [('Intornational', 'International'),
        ('ubject to 100 percent (100%) of the building permit and plan review '
         'fees in addition t',
         'subject to 100 percent (100%) of the building permit and plan review '
         'fees in addition to')],
    7: [('\nNot more than 80 percent', '\n2 Not more than 80 percent')],
    8: [('compartments,and', 'compartments, and')],
    10: [('shallhear', 'shall hear')],
    11: [('thnvenled room heaters utilizing fuel combustion are prohibited '
          'in al locations throughout',
          'the following:\nUnvented room heaters utilizing fuel combustion are prohibited '
          'in all locations throughout')],
    12: [('snow-and ice-melt systems', 'snow- and ice- melt systems')],
    13: [('The Energy Rating\n, Index (ERI)', 'The Energy Rating Index (ERI)')],
    15: [('Add the tollowing:', 'Add the following:')],
    16: [('or des conieations made by the code offcial relative to the application '
          'and interpretation',
          'or determinations made by the code official relative to the application '
          'and interpretation\n'
          'of this code.')],
}


def main() -> None:
    """Create complete printed text; handwriting/signatures remain separately qualified."""
    for number in range(1, 17):
        candidate = (ROOT / f'ocr/page-{number:04}.txt').read_text()
        if number == 3:
            text = ('Elizabeth Smith, Commissioner\n'
                    'Laura Puckett-Daniels, Commissioner\n'
                    'ATTEST:\nGunnison County Clerk\nGUNNISON COUNTY\nSEAL\nCOLORADO')
        else:
            end = BODY_END[number]
            pos = candidate.rfind(end)
            assert pos >= 0, number
            text = candidate[:pos + len(end)]
            for old, new in CORRECTIONS.get(number, []):
                assert old in text, (number, old)
                text = text.replace(old, new)
            if number == 2:
                text += ('\nINTRODUCED by Commissioner\n'
                         ', seconded by Commissioner\n'
                         ', and adopted on this\n'
                         'day of\n, 2023.\n'
                         'BOARD OF COUNTY COMMISSIONERS\n'
                         'OF GUNNISON COUNTY, COLORADO\n'
                         'Jonathan Houck, Chairperson')
            if number == 14:
                text += ('\nThe Gunnison County Board of Appeals pursuant to C.R.S. § 30-28-118 '
                         'shall be the\nGunnison County Board of Adjustment as described in the '
                         'Gunnison County Land Use\nResolution Section 8-103: Appeals and shall '
                         'hear and decide appeals of orders, decisions\nor determinations made '
                         'by the code official relative to the application and interpretation\n'
                         'of this code.')
        # Stamp is separately read from every full page, never decoded from its barcode.
        stamp = (f'Gunnison County, CO\n11/14/2023 8:13:55 AM\n447\n694082\n'
                 f'Page {number} of 16\nR 0.00 D 0.00')
        # Underlying printed pagination is visible on these physical pages.
        footer = f'\n{number}' if number in [3, 5, 9, 10, 11, 12, 13, 14, 15, 16] else ''
        text += '\n' + stamp + footer + '\n'
        write(ROOT / f'transcripts/page-{number:04}.txt', text.encode())


if __name__ == '__main__':
    main()
