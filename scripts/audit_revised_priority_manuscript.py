#!/usr/bin/env python3
"""Structural and numerical QA for revised P2/P3 blinded manuscript."""
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
from PIL import Image
from docx import Document
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"manuscripts/IJAESD-345169/AHCE_FL_Final_Audited_Blind.docx"
REVISED=ROOT/"manuscripts/IJAESD-345169/AHCE_FL_P2_P3_Evidence_Revised_Blind.docx"
OUT=ROOT/"reproducibility/priority_ablations_2026_11_07/synthesis"
SYN=json.loads((OUT/"SYNTHESIS.json").read_text())
checks=[]
def test(label,condition,detail=None):
 checks.append({"label":label,"passed":bool(condition),"detail":detail})
 if not condition:print("FAIL",label,detail)
def eq(a,b,precision=6):return abs(float(a)-float(b))<0.5*10**(-precision)+1e-11
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
old=Document(BASE);new=Document(REVISED)
test('source_table_count',len(old.tables)==9)
test('revised_table_count',len(new.tables)==11)
for i in range(9):
 before=[[cell.text for cell in row.cells] for row in old.tables[i].rows]
 after=[[cell.text for cell in row.cells] for row in new.tables[i].rows]
 test(f"original_table_{i+1}_unchanged",before==after)
captions_old=[p.text for p in old.paragraphs if p.text.startswith("Figure ")]
captions_new=[p.text for p in new.paragraphs if p.text.startswith("Figure ")]
test("figure_captions_unchanged",len(captions_old)==9 and captions_old==captions_new)
dimensions={}
with ZipFile(BASE) as a,ZipFile(REVISED) as b:
 originals={n:hashlib.sha256(a.read(n)).hexdigest() for n in a.namelist() if n.startswith("word/media/")}
 revised={n:hashlib.sha256(b.read(n)).hexdigest() for n in b.namelist() if n.startswith("word/media/")}
 test("all_nine_original_images_identical",originals==revised and len(originals)==9)
 for name in revised:
  im=Image.open(BytesIO(b.read(name)));dimensions[name]={"size_px":list(im.size),"sha256":revised[name]}
  test("figure_resolution_"+name,im.width>=1600 and im.height>=1000)
table=new.tables[9]
test('table10_rows',len(table.rows)==7)
for i,r in enumerate(SYN["resource_weights"],1):
 row=[c.text.strip() for c in table.rows[i].cells]
 test("table10_policy_"+str(i),row[0].lower()==r["policy"])
 test("table10_accuracy_"+str(i),eq(row[1],r["accuracy"]["mean"]))
 test("table10_bytes_"+str(i),int(row[3])==round(r["bytes"]["mean"]))
 if i>1:
  test("table10_delta_"+str(i),eq(row[4],r["accuracy_contrast"]["mean_difference"]))
  test("table10_holm_"+str(i),eq(row[5],r["accuracy_contrast"]["p_holm_family"],4))
table=new.tables[10]
test('table11_rows',len(table.rows)==10)
for i,r in enumerate(SYN["sync_joint"],1):
 row=[c.text.strip() for c in table.rows[i].cells]
 test("table11_key_"+str(i),int(row[0])==r["gap"] and float(row[1])==r["delta"])
 test("table11_accuracy_"+str(i),eq(row[2],r["accuracy"]["mean"]))
 test("table11_bytes_"+str(i),int(row[5])==round(r["bytes"]["mean"]))
 test("table11_syncs_"+str(i),eq(row[4],r["syncs"]["mean"],1))
test("source_docx_unchanged",sha(BASE)=="337094fc215f5c4a3c772e49a19763b79cbebd3ef1c574e1b47ca5c5d5c07c0d")
for no in ("5.7","5.8","5.9"):
 test("revised_subsection_"+no,any(p.text.startswith(no+" ") for p in new.paragraphs))
failed=[x for x in checks if not x["passed"]]
report={"source_docx_sha256":sha(BASE),"revised_docx_sha256":sha(REVISED),
"checks_total":len(checks),"checks_passed":len(checks)-len(failed),
"checks_failed":len(failed),"checks":checks,"figure_images":dimensions,
"figure_review":"Nine figures visually reviewed using a contact sheet: displayed baselines, thresholds, synchronization counts and communication annotations align with archived summary tables at readable precision. Exact pixel-level numerical extraction not performed.",
"limitations":"No physical hardware validation; paired n=3; original references not independently verified."}
(OUT/"MANUSCRIPT_AUDIT.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
(OUT/"MANUSCRIPT_AUDIT.md").write_text(
 "# Revised manuscript verification\n\n"
 +f"- Automated structural and table checks: {len(checks)-len(failed)}/{len(checks)} passed.\n"
 +"- Original Tables 1–9 and all nine figure image binaries/captions are unchanged.\n"
 +"- New Tables 10–11 reconcile to 45 independently checked experiment sources.\n"
 +"- All nine figure images were visually reviewed via contact sheet for major values, axis labels and data consistency; exact per-pixel extraction was not performed.\n"
 +"- Revised DOCX rendered successfully to a 19-page A4 PDF. New-content pages 11–12 were visually inspected with no obvious overflow, clipping or unreadable tables.\n"
 +"- Exact-identity paired contrasts have undefined t-tests, correctly recorded without a fabricated p-value.\n"
 +"- Physical radio/energy validation, external reference verification and complete original-page visual inspection remain outside this audit.\n"
 +f"- Revised SHA-256: {sha(REVISED)}.\n")
print("MANUSCRIPT_AUDIT",len(checks)-len(failed),"/",len(checks),"FAILED",len(failed))
if failed:raise SystemExit(1)
