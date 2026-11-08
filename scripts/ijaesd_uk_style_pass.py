#!/usr/bin/env python3
"""Conservative British-English prose pass; exclude bibliographic titles and tables."""
from pathlib import Path
from docx import Document
ROOT=Path(__file__).resolve().parents[1]/'manuscripts/IJAESD-345169/revision_package'
FILES=[
 'AHCE_FL_IJAESD_Reviewer_Revised_Blind.docx',
 'AHCE_FL_IJAESD_Annotated_Blind.docx',
 'IJAESD_345169_Response_and_Annotated_Manuscript.docx']
words=[('modeled','modelled'),('Modeled','Modelled'),('synchronization','synchronisation'),
       ('Synchronization','Synchronisation'),('normalized','normalised'),('Normalized','Normalised'),
       ('behavior','behaviour'),('Behavior','Behaviour'),('favor','favour'),('Favor','Favour')]
for name in FILES:
 p=ROOT/name;d=Document(p)
 inside_references=False;inside_figures=False;changed=0
 for paragraph in d.paragraphs:
  if paragraph.text.strip()=='References':inside_references=True
  if paragraph.text.strip()=='Figures':inside_figures=True
  if inside_references or inside_figures:continue
  for r in paragraph.runs:
   val=r.text
   for a,b in words:val=val.replace(a,b)
   if val!=r.text:r.text=val;changed+=1
 d.core_properties.author='';d.core_properties.last_modified_by=''
 d.save(p)
 print(name,'modified_runs',changed)
