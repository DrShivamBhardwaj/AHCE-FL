#!/usr/bin/env python3
"""Conservative Inderscience compliance pass, preserving all original evidence."""
from pathlib import Path
import json,re,hashlib
from docx import Document
ROOT=Path(__file__).resolve().parents[1]
DIR=ROOT/"manuscripts/IJAESD-345169"
SOURCE=DIR/"AHCE_FL_P2_P3_Evidence_Revised_Blind.docx"
TARGET=DIR/"AHCE_FL_IJAESD_Final_Compliance_Blind.docx"
OUT=ROOT/"reproducibility/priority_ablations_2026_11_07/submission_audit"
OUT.mkdir(parents=True,exist_ok=True)
doc=Document(SOURCE)
abstract=next(p for i,p in enumerate(doc.paragraphs) if i>0 and doc.paragraphs[i-1].text.strip()=="Abstract")
old=abstract.text
assert old.startswith("We evaluated Adaptive Hierarchical Communication-Efficient Federated Learning (AHCE-FL) in 51 CIFAR-10 simulation runs.")
new=("We evaluated Adaptive Hierarchical Communication-Efficient Federated Learning (AHCE-FL) "
     "in 96 CIFAR-10 simulation runs: 51 baseline and initial sensitivity runs plus 45 additional "
     "resource-weight and synchronisation experiments. Across three paired seeds and 100 training rounds, "
     "baseline AHCE-FL reached 0.473067 mean accuracy using 366004619 modelled bytes, whereas reconstructed "
     "FedAvg reached 0.643467 using 308560000 bytes. Altering resource-selection weights did not provide "
     "Holm-adjusted evidence of improved accuracy. Joint gap–threshold tests showed that a low divergence "
     "threshold caused cloud synchronisation every round; with divergence triggering disabled, maximum gaps "
     "of 1, 3 and 5 produced 100, 33 and 20 cloud exchanges. These results quantify simulated trade-offs, "
     "not hardware communication or energy savings.")
assert len(new.split())<150,len(new.split())
abstract.text=new
declarations=next(p for p in doc.paragraphs if p.text.strip()=="Declarations")
conflict=next(p for p in doc.paragraphs if p.text.startswith("Competing interests:"))
# Inderscience explicitly requires conflict-of-interest wording; preserve original meaning.
conflict.text="Conflicts of interest: All authors declare that they have no conflicts of interest."
disclosure=doc.add_paragraph(
 "AI-assisted editorial and research-support tools: OpenAI ChatGPT was used to assist with "
 "manuscript editing, reference-metadata checks, experimental-analysis scripting and consistency "
 "audits. The authors remain responsible for independently checking the calculations, source "
 "attribution, interpretation and final manuscript. No AI tool is listed as an author.")
conflict._p.addnext(disclosure._p)
# Remove identifying metadata from the blinded submission file.
meta=doc.core_properties
meta.author=""
meta.last_modified_by=""
meta.initials=""
meta.comments=""
meta.identifier=""
meta.keywords=""
meta.category=""
meta.subject=""
doc.save(TARGET)
check=Document(TARGET)
checks={
 "abstract_words":len(new.split()),
 "keyword_count":len(next(p.text for p in check.paragraphs if p.text.startswith("Keywords:")).split(",")),
 "author_metadata_blank":not check.core_properties.author and not check.core_properties.last_modified_by,
 "AI_declaration_present":any("AI-assisted editorial and research-support tools:" in p.text for p in check.paragraphs),
 "conflict_declaration_present":any("All authors declare that they have no conflicts of interest." in p.text for p in check.paragraphs),
 "tables_preserved":len(check.tables)==11 and all(
 [[c.text for c in row.cells] for row in a.rows]==[[c.text for c in row.cells] for row in b.rows]
 for a,b in zip(Document(SOURCE).tables,check.tables)),
 "figures_preserved":len(check.inline_shapes)==9,
 "source_docx_sha256":hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
 "final_docx_sha256":hashlib.sha256(TARGET.read_bytes()).hexdigest(),
}
assert checks["abstract_words"]<150 and checks["keyword_count"]>=10 and all(checks[k] for k in ("author_metadata_blank","AI_declaration_present","conflict_declaration_present","tables_preserved","figures_preserved"))
(OUT/"FORMAT_AUDIT.json").write_text(json.dumps(checks,indent=2)+"\n")
print(json.dumps(checks,indent=2))
