from pathlib import Path
from docx import Document
from docx.oxml.ns import qn
ROOT=Path('manuscripts/IJAESD-345169/revision_package')
for name in ['AHCE_FL_IJAESD_Reviewer_Revised_Blind.docx','AHCE_FL_IJAESD_Annotated_Blind.docx','IJAESD_345169_Response_and_Annotated_Manuscript.docx']:
 p=ROOT/name;d=Document(p)
 i=next(i for i,x in enumerate(d.paragraphs) if x.text.strip()=='Figures')
 preceding=d.paragraphs[i-1]
 assert not preceding.text.strip() and len(preceding._p.xpath('.//w:br[@w:type="page"]'))==1
 preceding._element.getparent().remove(preceding._element)
 heading=next(x for x in d.paragraphs if x.text.strip()=='Figures')
 heading.paragraph_format.page_break_before=True
 d.save(p)
 print('REMOVED_REDUNDANT_BREAK',name)
