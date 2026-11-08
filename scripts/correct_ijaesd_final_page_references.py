#!/usr/bin/env python3
"""Correct figure page locations after removing blank page, idempotently."""
from pathlib import Path
from docx import Document
import re
ROOT=Path('manuscripts/IJAESD-345169/revision_package')
PAGE={
'E1':'1–3, 4–23',
'R1':'5–7, 12–16, 19–23',
'R2-M7':'8, 13, 21',
'R2-M9':'19',
'R2-M11':'10–12, 15, 19–23'}
for name in ['IJAESD_345169_Response_and_Annotated_Manuscript.docx',
             'IJAESD_345169_Point_by_Point_Response.docx',
             'IJAESD_345169_Annotated_Change_Sheet.docx']:
 p=ROOT/name;d=Document(p);active=None;n=0
 for x in d.paragraphs:
  tx=x.text
  match=re.match(r'^(E[12]|R1|R2-[MS]\d+)\s+—\s+',tx)
  if match:active=match.group(1)
  if active in PAGE and (tx.startswith('Revised article: ') or tx.startswith('Location: ')):
   new=re.sub(r'\(pp?\. [^)]*\)$','(pp. '+PAGE[active]+')',tx)
   new=re.sub(r'\(combined manuscript pp\. [^)]*\)$','(combined manuscript pp. '+PAGE[active]+')',new)
   if new!=tx:x.text=new;n+=1
 for tbl in d.tables:
  for row in tbl.rows[1:]:
   code=row.cells[0].text.strip()
   if code in PAGE:
    tx=row.cells[2].text
    new=re.sub(r'combined manuscript pp\. [\d–, ]+$','combined manuscript pp. '+PAGE[code],tx)
    if new!=tx:row.cells[2].text=new;n+=1
 d.save(p)
 print(name,'page_loc_corrections',n)
