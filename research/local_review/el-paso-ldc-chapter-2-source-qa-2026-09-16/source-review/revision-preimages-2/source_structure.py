"""Manually specified complete source structure after direct seven-page review."""
# Tuple: passage ID, first line, last line, type, logical unit, parent unit, printed label.
SPECS = {n: [(f'P{n}-HEADER',1,1,'page_header',f'P{n}-HEADER',None,None),
             (f'P{n}-FOOTER',2,2,'page_footer',f'P{n}-FOOTER',None,None),
             (f'P{n}-DATE',3,3,'footer_date',f'P{n}-DATE',None,None)] for n in range(1,8)}


def heading(page: int, unit: str, start: int, end: int, parent: str | None,
            label: str) -> None:
    """Record a visible heading with its exact parent and printed enumeration."""
    SPECS[page].append((unit,start,end,'section_heading',unit,parent,label))


def text(page: int, ident: str, start: int, end: int, unit: str) -> None:
    """Record a complete paragraph or a physically split paragraph fragment."""
    SPECS[page].append((ident,start,end,'paragraph',unit,unit,None))


SPECS[1] += [('P1-CHAPTER',4,4,'document_title','P1-CHAPTER',None,None),
             ('P1-TITLE',5,5,'document_title','P1-TITLE',None,None)]
heading(1,'2.1',6,7,None,'2.1.')
heading(1,'2.1.1',8,9,'2.1','2.1.1')
text(1,'2.1.1-text',10,12,'2.1.1')
heading(1,'2.1.2',13,14,'2.1','2.1.2')
for k,a,b in [(1,15,25),(2,26,35),(3,36,40),(4,41,42)]:
    text(1,f'2.1.2-p{k}',a,b,'2.1.2')
heading(2,'2.1.3',4,5,'2.1','2.1.3')
text(2,'2.1.3-text',6,12,'2.1.3')
heading(2,'2.1.4',13,14,'2.1','2.1.4')
text(2,'2.1.4-text',15,21,'2.1.4')
heading(2,'2.2',22,23,None,'2.2.')
heading(2,'2.2.1',24,25,'2.2','2.2.1')
text(2,'2.2.1-intro',26,30,'2.2.1')
for letter,h1,h2,t1,t2 in [('A',31,32,33,34),('B',35,36,37,40),('C',41,42,43,46)]:
    unit='2.2.1'+letter
    heading(2,unit,h1,h2,'2.2.1',f'({letter})')
    text(2,unit+('-part1' if letter=='C' else '-text'),t1,t2,unit)
text(3,'2.2.1C-part2',4,5,'2.2.1C')
for letter,h1,h2,t1,t2 in [('D',6,7,8,9),('E',10,11,12,13),('F',14,15,16,20),('G',21,22,23,23),('H',24,25,26,31),('I',32,33,34,36)]:
    unit='2.2.1'+letter
    heading(3,unit,h1,h2,'2.2.1',f'({letter})');text(3,unit+'-text',t1,t2,unit)
heading(3,'2.2.2',37,38,'2.2','2.2.2')
heading(3,'2.2.2A',39,40,'2.2.2','(A)')
text(3,'2.2.2A-part1',41,44,'2.2.2A')
text(4,'2.2.2A-part2',4,8,'2.2.2A')
heading(4,'2.2.2B',9,10,'2.2.2','(B)');text(4,'2.2.2B-intro',11,15,'2.2.2B')
for n,h1,h2,t1,t2 in [(1,16,17,18,20),(2,21,22,23,24),(3,25,26,27,32),(4,33,34,35,36),(5,37,39,40,42)]:
    unit=f'2.2.2B.{n}'
    heading(4,unit,h1,h2,'2.2.2B',f'({n})');text(4,unit+'-text',t1,t2,unit)
heading(4,'2.2.2B.6',43,44,'2.2.2B','(6)');text(5,'2.2.2B.6-text',4,6,'2.2.2B.6')
for n,h1,h2,t1,t2 in [(7,7,8,9,13),(8,14,15,16,19)]:
    unit=f'2.2.2B.{n}'
    heading(5,unit,h1,h2,'2.2.2B',f'({n})');text(5,unit+'-text',t1,t2,unit)
heading(5,'2.2.3',20,20,'2.2','2.2.3')
heading(5,'2.2.3A',21,22,'2.2.3','(A)');text(5,'2.2.3A-text',23,29,'2.2.3A')
heading(5,'2.2.3B',30,31,'2.2.3','(B)');text(5,'2.2.3B-intro',32,38,'2.2.3B')
for n,h1,h2,t1,t2 in [(1,39,40,41,43),(2,44,45,46,48)]:
    unit=f'2.2.3B.{n}'
    heading(5,unit,h1,h2,'2.2.3B',f'({n})');text(5,unit+'-text',t1,t2,unit)
heading(5,'2.2.3B.3',49,50,'2.2.3B','(3)');text(6,'2.2.3B.3-text',4,5,'2.2.3B.3')
heading(6,'2.2.4',6,6,'2.2','2.2.4')
heading(6,'2.2.4A',7,8,'2.2.4','(A)');text(6,'2.2.4A-text',9,10,'2.2.4A')
heading(6,'2.2.4B',11,12,'2.2.4','(B)');text(6,'2.2.4B-intro',13,15,'2.2.4B')
for n,h1,h2,t1,t2 in [(1,16,17,18,22),(2,23,24,25,26),(3,27,28,29,32),(4,33,34,35,37),(5,38,39,40,41),(6,42,43,44,45),(7,46,47,48,50)]:
    unit=f'2.2.4B.{n}'
    heading(6,unit,h1,h2,'2.2.4B',f'({n})');text(6,unit+'-text',t1,t2,unit)
heading(6,'2.2.4B.8',51,52,'2.2.4B','(8)');text(7,'2.2.4B.8-text',4,6,'2.2.4B.8')
for n,h1,h2,t1,t2 in [(9,7,8,9,10),(10,11,12,13,14),(11,15,16,17,19),(12,20,21,22,24)]:
    unit=f'2.2.4B.{n}'
    heading(7,unit,h1,h2,'2.2.4B',f'({n})');text(7,unit+'-text',t1,t2,unit)

LINKS = [
 ('paragraph_continues','2.2.1C-part1','2.2.1C-part2'),
 ('paragraph_continues','2.2.2A-part1','2.2.2A-part2'),
 ('heading_to_body','2.2.2B.6','2.2.2B.6-text'),
 ('heading_to_body','2.2.3B.3','2.2.3B.3-text'),
 ('heading_to_body','2.2.4B.8','2.2.4B.8-text'),
]


def visual_order(page: int) -> list[str]:
    """Place the two footer lines after the body without altering the native asset."""
    ids=[s[0] for s in SPECS[page]]
    return [ids[0]]+ids[3:]+ids[1:3]
