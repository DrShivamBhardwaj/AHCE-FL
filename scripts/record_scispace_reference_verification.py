#!/usr/bin/env python3
"""Create evidence-specific AHCE bibliography ledger from actual SciSpace searches.
SciSpace exact-title discovery was performed on 8 Nov 2026; DOI records
and publisher sources are separately identified, not silently conflated.
"""
import csv,json
from pathlib import Path
from docx import Document
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"reproducibility/priority_ablations_2026_11_07/research_skill_audit"
prev=json.loads((ROOT/"reproducibility/priority_ablations_2026_11_07/submission_audit/REFERENCES_AUDIT.json").read_text())
IDs=[
"how-to-backdoor-federated-learning-e2a87howw8",
"merit-an-on-demand-iot-service-delivery-and-resource-4z16ej54fx",
"a-communication-efficient-hierarchical-federated-learning-1z2e7cmc9t",
"advances-and-open-problems-in-federated-learning-3t0jgb90ia",
"federated-learning-strategies-for-improving-communication-4hoq9ri1wt",
"federated-optimization-in-heterogeneous-networks-3v7i26o2nb",
"federated-learning-in-mobile-edge-networks-a-comprehensive-5dgelc5m6h",
"delay-aware-hierarchical-federated-learning-2q0ahzw103",
"personalized-client-edge-cloud-hierarchical-federated-4t2cnhpecv13",
"communication-efficient-learning-of-deep-networks-from-2s16evj791",
"",
"ldp-fed-federated-learning-with-local-differential-privacy-4sfg5qyzte",
"",
"hierarchical-asynchronous-federated-learning-algorithm-for-nryaqn3lm5hn",
"hiflash-communication-efficient-hierarchical-federated-j5bsjbrk",
"async-hfl-efficient-and-robust-asynchronous-federated-2ef0mvh3"
]
assert len(prev["entries"])==len(IDs)==16
notes={
1:"SciSpace returned 2018 for a proceedings-style record; authoritative PMLR AISTATS 2020 vol.108 pp.2938-2948 prevails. https://proceedings.mlr.press/v108/bagdasaryan20a.html",
5:"SciSpace indexes 2016 preprint; Crossref 10.48550/arXiv.1610.05492 query returned 404; record is identifiable by arXiv identifier 1610.05492, not a Crossref DOI match.",
6:"SciSpace has titled 2020 version; verify MLSys proceedings full metadata separately before claiming DOI verification.",
10:"SciSpace publication result is 2017 AISTATS. Publisher PMLR v54/mcmahan17a.html is authoritative.",
11:"Exact-title SciSpace query did not surface this 2026 FL-KAN article. Previously matched DOI 10.1504/IJAHUC.2026.151264 through Crossref. Publisher DOI metadata required; no SciSpace exact match claimed.",
12:"SciSpace published workshop record uses shorter title LDP-Fed; arXiv 2006.03637 expands to Federated Learning with Local Differential Privacy. Same research identity with DOI 10.1145/3378679.3394533.",
13:"Exact-title SciSpace query did not surface SCGAT-HFL. Prior Crossref DOI match 10.1109/MNET.2026.3719448 does not imply SciSpace indexed it.",
14:"SciSpace indexed 2025 Journal of Internet Technology record; official journal confirms vol.26 no.5 pp.617-629 (2025). Its page does not display DOI; do not add DOI from SciSpace without final publisher confirmation.",
15:"One SciSpace indexed record omits first author Qiong Wu; institutional IEEE metadata and DBLP confirm manuscript's correct seven-author list. DOI 10.1109/TPDS.2023.3238049.",
}
with (OUT/"AHCE_SCISPACE_LEDGER.csv").open("w",newline="") as f:
 w=csv.DictWriter(f,fieldnames=["ref_no","citation_key","scispace_unique_id","reference","existing_crossref_status","scispace_exact_title_search","publisher_crosscheck","verification_level","claim_level_full_text_verified","source_note"])
 w.writeheader()
 for i,entry in enumerate(prev["entries"],1):
  w.writerow({"ref_no":i,"citation_key":f"AHCE-{i:02d}",
   "scispace_unique_id":IDs[i-1],"reference":entry["reference"],
   "existing_crossref_status":entry["status"],
   "scispace_exact_title_search":"no reliable exact paper result" if i in (11,13) else "matching title search result",
   "publisher_crosscheck":"yes" if i in (1,10,12,14,15) else ("previous Crossref metadata only" if i in (11,13) else "Crossref/PMLR prior record or SciSpace record"),
   "verification_level":"identity and publication metadata only",
   "claim_level_full_text_verified":"no",
   "source_note":notes.get(i,"Exact-title SciSpace paper found; full-text claim-level validation outstanding.")})
 report={"search_date":"2026-11-08","source_bibliography_count":16,
 "exact_title_scispace_matching_entries":14,"scispace_index_gaps":[11,13],
 "publication_identity_notes":notes,
 "crossref_previous_no_flag":10,
 "claim_level_full_text_verified":0,
 "source_report":"User-supplied FreshBack-IoT SciSpace report supplies procedure only; its 22 reference conclusions were not copied.",
 "no_bibliography_content_changed":True}
 (OUT/"AHCE_SCISPACE_LEDGER_SUMMARY.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
 (OUT/"AHCE_SCISPACE_VERIFICATION_REPORT.md").write_text(
  "# AHCE-FL: SciSpace exact-title and publisher reconciliation\n\n"
  "Search date: 8 November 2026. Following the user-supplied FreshBack-IoT verification procedure, all 16 AHCE-FL bibliography titles were searched individually in SciSpace.\n\n"
  "**14/16 titles returned matching paper identities.** Two recently published items (FL-KAN and SCGAT-HFL) did not surface reliably under their exact titles. Prior Crossref DOI matches exist for both, but no SciSpace exact-DOI match is claimed for them.\n\n"
  "**Important version/metadata notes:**\n\n"+
  "\n".join(f"- Ref. {i}: {note}" for i,note in notes.items())+"\n\n"
  "**Evidence grading:** Metadata identity verification is not full-text claim verification. This review does not assert that all 16 papers were read in full, or that citations justify each sentence where they appear. The next stage is a two-way citation-to-claim audit.\n\n"
  "**Preservation:** None of the AHCE-FL manuscript references or simulation results were edited in this verification run. No FreshBack-IoT reference was imported.\n"
 )
print("LEDGER",len(IDs),"SciSpace identity matches",14,"index gaps",2)
