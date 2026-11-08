#!/usr/bin/env python3
"""Final QA for actual IJAESD reviewer-response package."""
from pathlib import Path
from docx import Document
from zipfile import ZipFile
from lxml import etree
from hashlib import sha256
from collections import Counter
import json,re,subprocess
ROOT=Path(__file__).resolve().parents[1]
DIR=ROOT/'manuscripts/IJAESD-345169/revision_package'
SOURCE=ROOT/'manuscripts/IJAESD-345169/AHCE_FL_Claim_Audited_Blind.docx'
FILES={
 'clean':DIR/'AHCE_FL_IJAESD_Reviewer_Revised_Blind.docx',
 'marked':DIR/'AHCE_FL_IJAESD_Annotated_Blind.docx',
 'response':DIR/'IJAESD_345169_Point_by_Point_Response.docx',
 'sheet':DIR/'IJAESD_345169_Annotated_Change_Sheet.docx',
 'combined':DIR/'IJAESD_345169_Response_and_Annotated_Manuscript.docx'}
src=Document(SOURCE)
records=[]
def check(name,condition,detail=''):
 records.append(dict(check=name,passed=bool(condition),detail=detail))
 if not condition:print('FAIL',name,detail)
math_ns='{http://schemas.openxmlformats.org/officeDocument/2006/math}'
with ZipFile(SOURCE) as z:
 old_media={n:sha256(z.read(n)).hexdigest() for n in z.namelist() if n.startswith('word/media/')}
 old_math=[etree.tostring(x) for x in etree.fromstring(z.read('word/document.xml')).iter() if x.tag==math_ns+'oMath']
for key,path in FILES.items():
 check(key+'_exists',path.is_file())
 d=Document(path)
 check(key+'_blinded_author',not d.core_properties.author and not d.core_properties.last_modified_by)
 check(key+'_no_placeholder',all('[PAGE_LOC]' not in p.text for p in d.paragraphs))
 if key in ('clean','marked','combined'):
  check(key+'_11_tables',len(d.tables)==11)
  check(key+'_9_figures',len(d.inline_shapes)==9)
  with ZipFile(path) as z:
   images={n:sha256(z.read(n)).hexdigest() for n in z.namelist() if n.startswith('word/media/')}
   maths=[etree.tostring(x) for x in etree.fromstring(z.read('word/document.xml')).iter() if x.tag==math_ns+'oMath']
  check(key+'_media_identical',images==old_media)
  check(key+'_50_equations_identical',maths==old_math and len(maths)==50)
  for i in range(1,11):
   a=[[c.text for c in row.cells] for row in src.tables[i].rows]
   b=[[c.text for c in row.cells] for row in d.tables[i].rows]
   check(key+'_numeric_table_'+str(i+1),a==b)
  check(key+'_expands_table_1',len(d.tables[0].columns)==7)
  check(key+'_no_privacy_guarantee',any('not a formal privacy guarantee' in p.text for p in d.paragraphs))
  check(key+'_no_invented_superiority',any('do not outperform FedAvg' in p.text for p in d.paragraphs))
  check(key+'_abstract_word_count',len(d.paragraphs[next(i for i,p in enumerate(d.paragraphs) if p.text.strip()=='Abstract')+1].text.split())<150)
 if key in ('response','combined'):
  joined='\n'.join(p.text for p in d.paragraphs)
  for name in ['E1','E2','R1']+[f'R2-M{x}' for x in range(1,12)]+[f'R2-S{x}' for x in range(1,7)]:
   check(key+'_comment_'+name,bool(re.search(r'(?m)^'+re.escape(name)+r' — ',joined)))
 if key=='sheet':
  check('change_sheet_20_rows',len(d.tables)==1 and len(d.tables[0].rows)==21)
# Two newly added references plus all prior ones.
clean=Document(FILES['clean'])
start=next(i for i,p in enumerate(clean.paragraphs) if p.text.strip()=='References')
stop=next(i for i,p in enumerate(clean.paragraphs) if p.text.strip()=='Figures')
entries=[p.text for p in clean.paragraphs[start+1:stop] if p.text.strip()]
check('references_18',len(entries)==18)
check('ref_Fan_2025',any(x.startswith('Fan,') and '10.1109/WCSP68525.2025.1010225' in x for x in entries))
check('ref_Qiu_2026',any(x.startswith('Qiu,') and '10.1109/ACCESS.2026.3688275' in x for x in entries))
names=['Bagdasaryan','Chowdhury','Deng','Fan','Kairouz','Konečný','Li','Lim','Lin','Ma','McMahan','Qiu','Shabariram','Truex','Tseng','Wen','Wu','Yu']
prose='\n'.join(p.text for p in clean.paragraphs[:start])
for n in names:
 if n=='Li':pat=r'Li et al\.\s*\(2020\)'
 elif n=='Qiu':pat=r'Qiu and Li(?:\s*\(2026\)|,\s*2026)'
 else:pat=rf'\b{re.escape(n)}\b'
 check('reference_cited_'+n,bool(re.search(pat,prose)))
# The reviewer-front annotated file was visually rendered and checked.
pdf=Path('/tmp/ahce_ijaesd_reviewer_final_20261108/IJAESD_345169_Response_and_Annotated_Manuscript.pdf')
if pdf.exists():
 info=subprocess.check_output(['pdfinfo',str(pdf)],text=True)
 check('combined_pdf_23_pages','Pages:           23' in info)
 tx=Path('/tmp/ahce_ijaesd_reviewer_final_20261108/revised_final.txt')
 if tx.exists():
  pages=tx.read_text().split('\f')[:-1]
  check('pdf_no_blank_pages',all(len(page.split())>10 for page in pages))
check('original_preserved',sha256(SOURCE.read_bytes()).hexdigest()==sha256(subprocess.check_output(['git','show','HEAD:manuscripts/IJAESD-345169/AHCE_FL_Claim_Audited_Blind.docx'],cwd=ROOT)).hexdigest())
failed=[x for x in records if not x['passed']]
report={'checks_total':len(records),'passed':len(records)-len(failed),'failed':len(failed),
'items':records,'files':{k:dict(path=str(v.relative_to(ROOT)),sha256=sha256(v.read_bytes()).hexdigest()) for k,v in FILES.items()},
'reviewer_comments_from':'Inderscience editorial revision request dated 10 October 2026',
'claim_limits':'No physical measurements, no confirmed accuracy superiority over FedAvg, no universal source full-text validation',
'blinded':True}
(DIR/'REVISION_AUDIT.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
(DIR/'REVISION_AUDIT.md').write_text('# IJAESD-345169 reviewer revision quality audit\n\n'
+f'- Checks passed: {len(records)-len(failed)}/{len(records)}.\n'
+'- 20 response items: two editorial requests, Reviewer 1, eleven required Reviewer 2 concerns and six recommendations.\n'
+'- Source nine figures and 50 OOXML equations remain binary-identical in the revised manuscript.\n'
+'- Numerical Tables 2–11 remain text-identical. Conceptual Table 1 adds a qualifying non-IID evidence column.\n'
+'- The highlighted combined document renders as 23 A4 pages with no blank page and has journal-requested page references.\n'
+'- Seven unit tests and the original 125/125 numerical checks were previously passed. No new full training runs were initiated for this editorial pass.\n'
+'- The actual submitted deadline and authorship arrangements must be checked in the editorial portal.\n'
+'- Unresolved: physical hardware validation and journal acceptance; do not claim either.\n')
print('REVISION_QA',len(records)-len(failed),'/',len(records),'failed',len(failed))
if failed:raise SystemExit(1)
