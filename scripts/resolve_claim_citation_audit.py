#!/usr/bin/env python3
"""Conservative claim-level citation review and literature update, November 2026.
Operates on latest blinded compliance version; never edits baseline numeric evidence.
"""
from pathlib import Path
from docx import Document
import json,hashlib,re,csv
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"manuscripts/IJAESD-345169/AHCE_FL_IJAESD_Final_Compliance_Blind.docx"
OUT=ROOT/"manuscripts/IJAESD-345169/AHCE_FL_Claim_Audited_Blind.docx"
REPORT=ROOT/"reproducibility/priority_ablations_2026_11_07/research_skill_audit"
REPORT.mkdir(exist_ok=True)
doc=Document(BASE);before=Document(BASE)
def find_fragment(fragment):
 xs=[p for p in doc.paragraphs if fragment in p.text]
 assert len(xs)==1,(fragment,len(xs))
 return xs[0]
def replace_par(fragment,old,new):
 p=find_fragment(fragment)
 assert old in p.text,(fragment,old,p.text)
 p.text=p.text.replace(old,new)
 return p
changes=[]
# Distinguish primary McMahan comparator from a generic unbounded claim.
p=replace_par("McMahan et al. (2017) reported",
 "McMahan et al. (2017) reported a reduction of 10× or more in the number of FedAvg communication rounds.",
 "In their evaluated tasks, McMahan et al. (2017) reported that FedAvg required 10–100 times fewer communication rounds than synchronised stochastic gradient descent.")
changes.append({"section":"2.1","type":"claim precision","source":"McMahan et al. 2017 primary PMLR abstract","before":"unqualified FedAvg reduction","after":"bounded to tested tasks and synchronous SGD comparator"})
# The two reviews describe device constraints and selection bias in FL generally. Distinguish scholarly discussion from own observed selection behavior.
p=replace_par("Selecting a client also selects its data.",
 "As Kairouz et al. (2021) and Lim et al. (2020) discuss, a preference for better-resourced devices can repeatedly favour the same partitions.",
 "Kairouz et al. (2021) describe participation and heterogeneity challenges in federated learning, while Lim et al. (2020) review mobile-edge resource constraints. Under a fixed resource ranking, repeatedly favouring the same clients can also underrepresent some non-IID partitions; this is a possible consequence of the selection rule examined here rather than a measured result from those two surveys.")
changes.append({"section":"2.2","type":"attribution","source":"Kairouz 2021 monograph, Lim 2020 IEEE survey","after":"general cited context separated from current framework implication"})
# Correct nomenclature of ShapeFL.
p=replace_par("ShapeFL changes the distribution seen at an edge",
 "ShapeFL changes the distribution seen at an edge",
 "ShapeFL jointly considers edge-node association and the diversity of data represented at edge aggregators")
changes.append({"section":"2.3","type":"specificity","source":"Deng et al. 2024 IEEE primary abstract"})
# Clarify Wen Bayesian technique and prevent generic edge-scheduling overstatement.
p=replace_par("Wen et al. (2025) examine how edges coordinate asynchronously.",
 "Wen et al. (2025) examine how edges coordinate asynchronously.",
 "Wen et al. (2025) study hierarchical asynchronous learning through a Bayesian formulation with variational inference and multilevel model aggregation.")
changes.append({"section":"2.4","type":"specificity","source":"Wen et al. 2025 Journal of Internet Technology official abstract"})
# Clarify semantic gating; not simple threshold cloud-sync.
p=replace_par("Tseng et al. (2026) use semantic-aware graph attention to decide when communication should occur.",
 "Tseng et al. (2026) use semantic-aware graph attention to decide when communication should occur.",
 "Tseng et al. (2026) use semantic proxies and communication-gated graph attention to represent link conditions when coordinating hierarchical learning.")
changes.append({"section":"2.4","type":"mechanism specificity","source":"Tseng et al. 2026 DOI-linked abstract; full text not inspected"})
# FedProx coefficient must be attributed to local experiment.
p=replace_par("FedProx uses the same selection rule and adds the proximal penalty",
 "FedProx uses the same selection rule and adds the proximal penalty µ = 0.01 from Li et al. (2020).",
 "FedProx follows the proximal-objective formulation of Li et al. (2020), with µ = 0.01 selected for the present implementation.")
changes.append({"section":"4.2","type":"experimental provenance","source":"Li et al. 2020 FedProx; AHCE-FL repo configuration","before":"μ misattributed to cited authors","after":"μ declared study-specific"})
# Related-work comparison, strictly from publisher abstract / DOI; no invented performance values.
anchor=find_fragment("The same hierarchy can behave differently")
new=doc.add_paragraph(
 "More recent work addresses transmission control directly. Fan et al. (2025) describe FedDAC, which varies compression ratios on device–edge and edge–cloud links in response to resource conditions. Qiu and Li (2026) describe network-aware parameter transmission with link sensing and a choice among full, incremental and cached updates. These systems differ from the present experiment, where resource descriptors are synthetic and fixed during a run, sparsification uses an explicit encoded-size test, and cloud synchronisation is triggered by a divergence threshold or maximum-gap ceiling. We do not reproduce FedDAC or AHPT-FL as numerical baselines; consequently, the present comparisons cannot establish superiority over either approach.")
anchor._p.addprevious(new._p)
changes.append({"section":"2.3","type":"new verified comparison","sources":["Fan et al. 2025 IEEE WCSP","Qiu and Li 2026 IEEE Access"],"claim":"mechanism-level comparison only; unexecuted baseline"})
references=find_fragment("Bagdasaryan, E.")
newrefs=[
("Fan","Fan, L., Zhang, X., Duan, M. and Jiang, J. (2025) 'Adaptive communication control for efficient hierarchical federated learning in heterogeneous edge networks', Proceedings of the 17th International Conference on Wireless Communications and Signal Processing (WCSP 2025). doi:10.1109/WCSP68525.2025.1010225."),
("Qiu","Qiu, Y. and Li, D. (2026) 'Adaptive hierarchical parameter transmission for federated learning in MEC environments with dynamic network awareness', IEEE Access, Vol. 14, pp. 65150–65160. doi:10.1109/ACCESS.2026.3688275.")
]
# Insert each directly before the next alphabetically later surname.
for surname,content in newrefs:
 if surname=="Fan":before_p=find_fragment("Kairouz, P.")
 else:before_p=find_fragment("Shabariram, C.P.")
 para=doc.add_paragraph(content,style=references.style)
 before_p._p.addprevious(para._p)
# anonymisation must remain intact.
doc.core_properties.author="";doc.core_properties.last_modified_by=""
doc.save(OUT)
now=Document(OUT)
assert len(before.tables)==len(now.tables)==11
for i in range(11):
 aa=[[c.text for c in row.cells] for row in before.tables[i].rows]
 bb=[[c.text for c in row.cells] for row in now.tables[i].rows]
 assert aa==bb,("table changed",i)
assert len(now.inline_shapes)==len(before.inline_shapes)==9
# Check original results not changed.
for marker in ["0.643467","0.473067","366004619","308560000","96 CIFAR-10","100, 33 and 20"]:
 assert any(marker in p.text for p in now.paragraphs),marker
start=next(i for i,p in enumerate(now.paragraphs) if p.text=="References")
end=next(i for i,p in enumerate(now.paragraphs) if p.text=="Figures")
reference_list=[p.text for p in now.paragraphs[start+1:end] if p.text.strip()]
assert len(reference_list)==18,len(reference_list)
assert reference_list==sorted(reference_list,key=lambda s:s.casefold())
ledger=[{"ref_no":i+1,"reference":ref} for i,ref in enumerate(reference_list)]
p=REPORT/"CLAIM_CITATION_RESOLUTION.json"
p.write_text(json.dumps({"authoritative_input_sha256":hashlib.sha256(BASE.read_bytes()).hexdigest(),
 "claim_audit_changes":changes,"all_18_references_in_bibliography":True,
 "new_reference_count":2,"prior_source_reference_count":16,
 "figures_preserved":9,"tables_preserved":11,
 "source":str(BASE.relative_to(ROOT)),"output":str(OUT.relative_to(ROOT)),
 "output_sha256":hashlib.sha256(OUT.read_bytes()).hexdigest(),
 "remaining_limits":["Publisher abstract is insufficient to certify full-text claim context",
 "Full-text comparison to FedDAC and AHPT-FL not performed","Physical hardware experiment not performed",
 "IJAESD topical suitability requires editor assessment"],
 "references":ledger},indent=2,ensure_ascii=False)+"\n")
lines=["# AHCE-FL claim-to-citation audit and conservative revision","","**Audited source:** "+str(BASE.relative_to(ROOT)),"**Final revised copy:** "+str(OUT.relative_to(ROOT)),
"","18 bibliography entries, including 2 new publisher-verified relevant comparators. None of the original 16 bibliography entries was removed.",
"","## Claim-level corrections"]
for a in changes:lines.append(f'- **{a["section"]}:** {a["type"]}. '+a.get("after",a.get("claim","Primary publication wording refined.")))
lines.extend(["","## Limits","",
"- The claim review used named primary abstracts and available SciSpace article extracts; it does not certify unavailable full text for all 18 citations.",
"- Full-text evidence for novel comparative numerical superiority is absent, and no such claim was added.",
"- Hardware claims remain unsupported. Actual results, equations, charts and algorithmic definitions were unchanged.",
"- Source DOCX remains unmodified; this is a new revision file.",
""])
(REPORT/"CLAIM_CITATION_RESOLUTION.md").write_text("\n".join(lines))
print("CLAIM_AUDIT_READY",len(changes),"claim corrections/additions",len(reference_list),"references")
print("FINAL_DOCX",OUT)
