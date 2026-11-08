#!/usr/bin/env python3
"""Insert actual rendered combined-response page references in all reviewer documents."""
from pathlib import Path
from docx import Document
ROOT=Path(__file__).resolve().parents[1]/'manuscripts/IJAESD-345169/revision_package'
PAGE={
'E1':'1–3, 4–19',
'E2':'5–7, 17–19',
'R1':'5–7, 12–16, 20–24',
'R2-M1':'4–7, 12, 15–16',
'R2-M2':'9, 13–15',
'R2-M3':'5–7, 17–19',
'R2-M4':'5–7, 11',
'R2-M5':'8, 15',
'R2-M6':'8',
'R2-M7':'8, 13',
'R2-M8':'7, 14',
'R2-M9':'20',
'R2-M10':'11',
'R2-M11':'10–12, 15, 20–24',
'R2-S1':'5–7',
'R2-S2':'5–7',
'R2-S3':'5–6, 17–19',
'R2-S4':'5–6, 17–19',
'R2-S5':'5–7',
'R2-S6':'5–7, 17–19'}
names=[
'IJAESD_345169_Response_and_Annotated_Manuscript.docx',
'IJAESD_345169_Point_by_Point_Response.docx',
'IJAESD_345169_Annotated_Change_Sheet.docx']
for name in names:
 path=ROOT/name;doc=Document(path);current=None;n=0
 for p in doc.paragraphs:
  h=p.text.strip()
  for code in PAGE:
   if h.startswith(code+' — '):current=code
  if current and ('[PAGE_LOC]' in h):
   p.text=h.replace('[PAGE_LOC]','(pp. '+PAGE[current]+')');n+=1
  elif current and h.startswith('Location: '):
   p.text=h+' (combined manuscript pp. '+PAGE[current]+')';n+=1
 for tbl in doc.tables:
  for row in tbl.rows[1:]:
   code=row.cells[0].text.strip()
   if code in PAGE:
    row.cells[2].text+='; combined manuscript pp. '+PAGE[code];n+=1
 assert n==20,(name,n)
 doc.core_properties.author='';doc.core_properties.last_modified_by=''
 doc.save(path)
 print(name,'page_references',n)
