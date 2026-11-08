#!/usr/bin/env python3
"""Map every AHCE-FL bibliography entry to actual cited prose locations.
Limited to exact in-text source attribution; does not claim all full text read.
"""
import csv,json,re,hashlib
from pathlib import Path
from docx import Document
ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/"manuscripts/IJAESD-345169/AHCE_FL_Claim_Audited_Blind.docx"
OLD=ROOT/"manuscripts/IJAESD-345169/AHCE_FL_IJAESD_Final_Compliance_Blind.docx"
OUT=ROOT/"reproducibility/priority_ablations_2026_11_07/research_skill_audit"
d=Document(DOC);ref_idx=next(i for i,p in enumerate(d.paragraphs) if p.text=="References")
figure_idx=next(i for i,p in enumerate(d.paragraphs) if p.text=="Figures")
bibliography=[p.text for p in d.paragraphs[ref_idx+1:figure_idx] if p.text.strip()]
assert len(bibliography)==18
authors=["Bagdasaryan","Chowdhury","Deng","Fan","Kairouz","Konečný","Li","Lim","Lin","Ma","McMahan","Qiu","Shabariram","Truex","Tseng","Wen","Wu","Yu"]
# Li references can be ambiguous with Qiu and Li, so require Li et al. pattern explicitly.
patterns={
"Li":r"\bLi et al\.\s*\(2020\)|\bLi et al\.,\s*2020",
"Qiu":r"\bQiu and Li\s*\(2026\)|\bQiu and Li,\s*2026",
}
rows=[]
for j,(name,ref) in enumerate(zip(authors,bibliography),1):
 assert ref.startswith(name+",") or name=="Konečný" and ref.startswith("Konečný"),(name,ref[:100])
 matches=[]
 for i,p in enumerate(d.paragraphs[:ref_idx]):
  text=p.text
  regex=patterns.get(name,rf"\b{re.escape(name)}(?: et al\.)?(?:\s*\(|,\s*)(?:20\d{{2}}|2016|2017)(?=[\s,;)])")
  if re.search(regex,text,re.I):
   matches.append({"paragraph_index":i,"context":text[:600]})
 # citations also appear in parenthetic author-year format; Regex matches.
 rows.append({"ref_no":j,"lead_author":name,"citation_count":len(matches),
   "cited_paragraphs":matches,"reference":ref,
   "claim_verification_level":"primary publisher abstract/SciSpace extract for targeted mechanism statements; exact full text not uniformly available"})
report={
 "source_document":str(DOC.relative_to(ROOT)),
 "source_sha256":hashlib.sha256(DOC.read_bytes()).hexdigest(),
 "cited":sum(bool(r["citation_count"]) for r in rows),
 "reference_count":len(rows),
 "uncited":[r["lead_author"] for r in rows if not r["citation_count"]],
 "claim_references":rows,
 "limitations":[
  "Search does not certify every clause in multi-claim paragraphs; manual semantic reading required.",
  "Metadata and accessible abstracts support mechanism descriptions, not any newly claimed performance.",
  "No full-text examination of every reference is claimed."
 ]}
(OUT/"CLAIM_TO_SOURCE_LEDGER.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
with (OUT/"CLAIM_TO_SOURCE_LEDGER.csv").open("w",newline="\n") as f:
 w=csv.writer(f,lineterminator="\n")
 w.writerow(["ref_no","lead_author","citation_count","paragraph_indices","verification_level"])
 for r in rows:
  w.writerow([r["ref_no"],r["lead_author"],r["citation_count"],
             ",".join(str(x["paragraph_index"]) for x in r["cited_paragraphs"]),
             r["claim_verification_level"]])
print("CLAIM_COVERAGE",report["cited"],"/",report["reference_count"],"UNCITED",report["uncited"])
if report["uncited"]:raise SystemExit(2)
