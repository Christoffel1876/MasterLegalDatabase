"""Manually checked line associations, anchored to the unchanged seven-page source.

Ranges are inclusive native line numbers. These are source-review records, not a fee calculator.
"""
TABLES={
 'water':(2,9), 'construction':(2,21), 'alarm':(4,10), 'sprinkler':(4,31),
 'fixed':(4,58),'misc':(4,69),'inspections':(5,24),'administrative':(5,44),'extraterritorial':(5,56)}
# page, table, label native lines, fee native lines. Long cells retain every line.
ROWS=[]
def pairs(p,t,first,last):
 for a in range(first,last+1,2):ROWS.append((p,t,[a],[a+1]))
pairs(2,'water',10,18);pairs(2,'construction',22,80)
pairs(3,'construction',4,92)
ROWS.extend([(4,'construction',[4,5],[6]),(4,'construction',[7],[8])])
pairs(4,'alarm',11,27);pairs(4,'sprinkler',32,44)
ROWS.extend([(4,'sprinkler',[46,47],[48]),(4,'sprinkler',[49],[50]),(4,'sprinkler',[51,52],[53])])
pairs(4,'fixed',59,65);pairs(4,'misc',70,72)
pairs(5,'misc',4,14)
ROWS.extend([(5,'misc',[16,17],[18]),(5,'misc',[19],[20,21])])
pairs(5,'inspections',25,35)
ROWS.append((5,'inspections',[37,38],[39]))
pairs(5,'administrative',45,47)
ROWS.extend([(5,'administrative',[49],[50,51]),(5,'administrative',[52],[53]),(5,'extraterritorial',[58],[59]),(5,'extraterritorial',[60],[61,62])])
assert len(ROWS)==128
# Complete paragraphs and notes, including the re-inspection page break.
CONTEXT={
 'GENERAL-PLAN-REVIEW':('general_note',[(2,6,7)]),
 'SPRINKLER-INSPECTIONS':('table_note',[(4,54,55)]),
 'REINSPECTION-NOTE':('table_note',[(5,40,41)]),
 'EXTRATERRITORIAL-NOTE':('table_note',[(5,63,67)]),
 'DEF-ADMINISTRATIVE':('definition',[(6,5,7)]),
 'DEF-CONSTRUCTION-PLAN-CHECK':('definition',[(6,8,12)]),
 'DEF-CONVENIENCE':('definition',[(6,13,15)]),
 'DEF-EXPEDITED':('definition',[(6,16,21)]),
 'DEF-FIRE-PLAN-CHECK':('definition',[(6,22,25)]),
 'DEF-HIGH-RISE':('definition',[(6,26,27)]),
 'DEF-LIMITED-REVIEW':('definition',[(6,28,30)]),
 'DEF-PERFORMANCE':('definition',[(6,31,35)]),
 'DEF-PRELIMINARY':('definition',[(6,36,38)]),
 'DEF-PREPLAN':('definition',[(6,39,41)]),
 'DEF-REINSPECTION':('definition',[(6,42,45),(7,4,4)]),
 'DEF-TRIP':('definition',[(7,5,7)]),
 'DEF-WUI-COMMERCIAL':('definition',[(7,8,10)]),
 'IMPLEMENTATION':('implementation',[(7,12,12)]),
 'OTHER-SCHEDULE':('other_schedule_reference',[(7,14,16)]),
 'PRINTED-EFFECTIVE-DATE':('printed_date',[(1,12,12)]),
 'DEFINITIONS-HEADING':('heading',[(6,4,4)]),
 'CONSTRUCTION-TITLE':('heading',[(2,4,4)]),
 'COVER':('cover',[(1,8,10)]),
 'CONTENTS':('contents',[(1,14,34)])}
GLOBAL=['GENERAL-PLAN-REVIEW','IMPLEMENTATION','OTHER-SCHEDULE','P4-MISC-01']
# Entire declared context bundle is retained; links do not assert that every condition applies.
def linked_context(p,t,label):
 notes=[];defs=[]
 if t=='sprinkler':notes=['SPRINKLER-INSPECTIONS'];defs=['DEF-FIRE-PLAN-CHECK','DEF-TRIP']
 if t in {'water','alarm','fixed'}:defs=['DEF-FIRE-PLAN-CHECK']
 if t=='inspections':notes=['REINSPECTION-NOTE'];defs=['DEF-CONVENIENCE','DEF-PRELIMINARY','DEF-REINSPECTION','DEF-TRIP']
 if t=='extraterritorial':notes=['EXTRATERRITORIAL-NOTE']
 if t=='construction':defs=['DEF-CONSTRUCTION-PLAN-CHECK','DEF-LIMITED-REVIEW','DEF-HIGH-RISE','DEF-PERFORMANCE','DEF-WUI-COMMERCIAL']
 if t=='administrative':defs=['DEF-ADMINISTRATIVE']
 if t=='misc':defs=['DEF-EXPEDITED','DEF-FIRE-PLAN-CHECK','DEF-PREPLAN']
 return notes,defs
