#!/usr/bin/env python3
"""Generate a versioned blinded DOCX adding provenance-audited P2/P3 experiments.

Retains existing 51-run tables, figures, equations, citation/reference content.
New Tables 10-11 are appended, not substituted into the baseline tables.
"""
from pathlib import Path
import json,hashlib
from docx import Document
from docx.shared import Inches,Pt
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
ROOT=Path(__file__).resolve().parents[1]
ORIGINAL=ROOT/"manuscripts/IJAESD-345169/AHCE_FL_Final_Audited_Blind.docx"
OUTPUT=ROOT/"manuscripts/IJAESD-345169/AHCE_FL_P2_P3_Evidence_Revised_Blind.docx"
REPORT=ROOT/"reproducibility/priority_ablations_2026_11_07/synthesis/SYNTHESIS.json"
s=json.loads(REPORT.read_text());doc=Document(ORIGINAL)
original_image_count=len(doc.inline_shapes)
original_table_count=len(doc.tables)
original_reference_text=[p.text for p in doc.paragraphs if p.style.name=="Normal" and p.text.startswith(("Bagdasaryan,","Chowdhury,","Deng,","Kairouz,","Konečný,","Li,","Lim,","Lin,","Ma,","McMahan,","Shabariram,","Truex,","Tseng,","Wen,","Wu,","Yu,"))]
reference_signature=hashlib.sha256("\n".join(original_reference_text).encode()).hexdigest()
assert original_table_count==9 and original_image_count==9,(original_table_count,original_image_count)
conclusion=next(p for p in doc.paragraphs if p.text.strip()=="6. Conclusion")
def create_paragraph(text,style=None):
 p=doc.add_paragraph(text,style=style);conclusion._p.addprevious(p._p)
 return p
def create_table(headers,rows,width=None):
 t=doc.add_table(rows=1,cols=len(headers))
 t.style="Table Grid"
 for i,h in enumerate(headers):
  t.cell(0,i).text=str(h)
  for r in t.cell(0,i).paragraphs[0].runs:r.bold=True
  t.cell(0,i).paragraphs[0].style="Normal"
 for row in rows:
  cells=t.add_row().cells
  for i,value in enumerate(row):cells[i].text=str(value)
 for row in t.rows:
  for c in row.cells:
   for p in c.paragraphs:
    p.paragraph_format.space_after=Pt(0)
    for run in p.runs:run.font.size=Pt(8)
 # Repeat header across pages.
 trPr=t.rows[0]._tr.get_or_add_trPr();v=OxmlElement('w:tblHeader');v.set(qn('w:val'),'true');trPr.append(v)
 conclusion._p.addprevious(t._tbl)
 return t
def pct(val):return f"{100*val:.3f}%"
def ci(pair):return "["+", ".join(f"{x:+.4f}" for x in pair["ci95"])+"]"
weights=s["resource_weights"]
joint=s["sync_joint"]
create_paragraph("5.7 Additional resource-weight sensitivity experiments (P2)",style="Heading 2")
create_paragraph("To test whether the initially equal client-selection weights unduly determine the reported behavior, we completed 18 additional 100-round CIFAR-10 runs. Six prespecified resource-weight profiles were evaluated at the same paired seeds (11, 23 and 42). Each nonuniform profile assigns 0.40 to one descriptor and 0.15 to each of the other four, in the simulator's bandwidth, energy, accuracy, latency and computing-capability order. The equal-weight control assigns 0.20 to all five descriptors. All other study settings, including the synthetic resource descriptors, remain unchanged.")
create_paragraph("Table 10 reports mean final accuracy, its exploratory two-sided Student-t interval, and modeled transfer volume over the three paired seeds. Accuracy contrasts subtract the equal-weight result; p-values use paired two-sided t tests and are Holm-adjusted across the five nonuniform-weight comparisons. These tests quantify sensitivity under fixed simulator assumptions and do not establish that the selection descriptors are calibrated to real device conditions.")
create_paragraph("Table 10. Selection-weight sensitivity for AHCE-FL across three paired seeds.",style="Caption")
rows=[]
for r in weights:
 c=r.get("accuracy_contrast");q=r["accuracy"]["ci95"]
 rows.append((r["policy"].capitalize(),f'{r["accuracy"]["mean"]:.6f}',f'[{q[0]:.4f}, {q[1]:.4f}]',f'{r["bytes"]["mean"]:.0f}',
             f'{c["mean_difference"]:+.6f}' if c else "Reference",
             f'{c["p_holm_family"]:.4f}' if c else "—"))
create_table(["Emphasis","Accuracy","95% CI","Modeled bytes","Δ accuracy","Holm p"],rows)
top=max(weights,key=lambda r:r["accuracy"]["mean"])
create_paragraph(f'The largest observed mean final accuracy was {top["accuracy"]["mean"]:.6f} under the {top["policy"]}-weighted profile, compared with 0.473067 under equal weights. None of the five paired contrasts met a Holm-adjusted 0.05 significance threshold. Consequently, these observations support parameter sensitivity, not a general accuracy advantage for a particular resource weight; the outcome remains limited by three seeds and simulated descriptors.')
create_paragraph("5.8 Joint synchronization-threshold and maximum-gap experiment (P3)",style="Heading 2")
create_paragraph("An additional 27 runs crossed the maximum synchronization gap G ∈ {1, 3, 5} with the divergence threshold δ ∈ {0.05, 0.5, 10⁹}, using the same paired seeds and 100-round configuration. The large threshold is a practical divergence-disabled control used to isolate the timer; it is not a recommended operational threshold. Round-level telemetry records whether synchronization resulted from divergence, the maximum gap, both mechanisms, or neither. As throughout the study, modeled bytes are parameter payload estimates, not measured packet traffic.")
create_paragraph("Table 11. Joint effects of maximum gap and divergence threshold on modeled communication and final accuracy (three paired seeds per setting).",style="Caption")
rows=[]
for r in joint:
 q=r["accuracy"]["ci95"];rows.append((str(r["gap"]),r["delta_label"],f'{r["accuracy"]["mean"]:.6f}',
                                     f'[{q[0]:.4f}, {q[1]:.4f}]',f'{r["syncs"]["mean"]:.1f}',f'{r["bytes"]["mean"]:.0f}'))
create_table(["G","δ","Accuracy","95% CI","Cloud syncs","Modeled bytes"],rows)
create_paragraph("At δ = 0.05, all G = 1, 3 and 5 settings synchronized on every round, so changing the maximum gap could not reduce cloud exchanges. At δ = 0.5 and G = 3 or 5, divergence-triggered synchronization averaged 76.67 exchanges per run and the modeled payload was 332,182,613 bytes; the two gaps produced identical aggregate outcomes in this particular simulator configuration. With δ = 10⁹, synchronization was driven solely by the maximum gap: 100 events for G = 1, 33 for G = 3 and 20 for G = 5. Mean modeled payload consequently fell from 366,004,619 to 273,122,664 and 253,395,056 bytes, respectively. These effects are a consequence of the stated triggering conditions, rather than evidence of reliable network-level adaptation.")
create_paragraph("In paired final-accuracy contrasts relative to the G = 1, δ = 10⁹ control, none of the eight other settings reached a Holm-adjusted p-value below 0.05. Since only three seeds were observed, a nonsignificant difference must not be interpreted as an equivalence or non-inferiority result. The joint study isolates how the divergence gate and gap ceiling interact in the simulator; it does not independently validate wireless delivery, energy use, device heterogeneity or privacy protection.")
create_paragraph("5.9 Figure, numerical provenance, and external validation boundaries",style="Heading 2")
create_paragraph("The additional 45 runs were verified against their 100 consecutively numbered rounds, seed-specific configurations, final-result summaries and SHA-256 manifests. The numerical figures and nine original manuscript tables remain linked to the preceding 51-run baseline and sensitivity archive. Figures 1–9 are retained without alteration; their presence and raster dimensions are checked separately, but image-level agreement between every plotted mark and its underlying data has not yet been independently certified. The two new tables are generated solely from the additional archived runs.")
create_paragraph("No real-radio experiment, packet capture, measured battery energy or physical end-to-end timing result is included in this revision. Such measurements require a separately specified hardware protocol and cannot be inferred from the single-process PyTorch simulation. The 96-run combined archive constitutes two study stages (51 original and 45 new) rather than 96 independent replications of the same experimental condition.")
# update conclusion while keeping its original numerical claims intact
after_conclusion=next(p for p in doc.paragraphs if p.text.strip()=="Data availability and reproducibility")
p=doc.add_paragraph("In an additional 45-run, three-seed evaluation, the five nonuniform selection-weight policies did not yield Holm-adjusted evidence of higher final accuracy than the equal-weight control. A joint gap–threshold experiment exposed the dependence of cloud synchronization on divergence-trigger settings: short thresholds forced synchronization every round even when the maximum gap was lengthened, whereas suppressing the divergence trigger isolated reductions associated with G. These results extend mechanism-level sensitivity evidence but do not reverse the baseline FedAvg comparison or establish network-, hardware- or energy-level superiority.")
after_conclusion._p.addprevious(p._p)
# Add line to data availability, without disclosing identity in blinded manuscript.
availability=next(p for p in doc.paragraphs if p.text.startswith("The AHCE-FL GitHub repository [Repository identity"))
availability.add_run(" The supplementary P2/P3 campaign contains 45 individually verified seed–configuration pairs with per-round CSVs, final JSON summaries, checksum manifests and a reproducible paired statistical synthesis; blinded access details may be provided to the editor.")
doc.save(OUTPUT)
new=Document(OUTPUT)
assert len(new.tables)==11 and len(new.inline_shapes)==original_image_count
refs2=[p.text for p in new.paragraphs if p.style.name=="Normal" and p.text.startswith(("Bagdasaryan,","Chowdhury,","Deng,","Kairouz,","Konečný,","Li,","Lim,","Lin,","Ma,","McMahan,","Shabariram,","Truex,","Tseng,","Wen,","Wu,","Yu,"))]
assert hashlib.sha256("\n".join(refs2).encode()).hexdigest()==reference_signature
print("REVISED",OUTPUT,"TABLES",len(new.tables),"IMAGES",len(new.inline_shapes),"PARAGRAPHS",len(new.paragraphs))
print("SHA256",hashlib.sha256(OUTPUT.read_bytes()).hexdigest())
