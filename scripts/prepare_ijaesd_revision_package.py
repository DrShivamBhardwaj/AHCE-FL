#!/usr/bin/env python3
"""IJAESD revised research manuscript, real reviewer response and annotated change sheet."""
from pathlib import Path
from copy import deepcopy
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_COLOR_INDEX, WD_BREAK, WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import hashlib, json, re

ROOT=Path(__file__).resolve().parents[1]
DIR=ROOT/'manuscripts/IJAESD-345169'
SRC=DIR/'AHCE_FL_Claim_Audited_Blind.docx'
DEST=DIR/'revision_package';DEST.mkdir(parents=True,exist_ok=True)
CLEAN=DEST/'AHCE_FL_IJAESD_Reviewer_Revised_Blind.docx'
MARKED=DEST/'AHCE_FL_IJAESD_Annotated_Blind.docx'
RESP=DEST/'IJAESD_345169_Point_by_Point_Response.docx'
SHEET=DEST/'IJAESD_345169_Annotated_Change_Sheet.docx'
COMBINED=DEST/'IJAESD_345169_Response_and_Annotated_Manuscript.docx'

doc=Document(SRC)
old=Document(SRC)
def par(fragment):
 xs=[p for p in doc.paragraphs if fragment in p.text]
 assert len(xs)==1,('ambiguous paragraph',fragment,len(xs))
 return xs[0]
changes=[]
def edit(fragment,new,issue,tag):
 p=par(fragment)
 before=p.text
 assert before!=new
 # Only modify plain prose paragraphs; retain all other equation-bearing XML.
 assert not p._p.xpath('.//m:oMath') and not p._p.xpath('.//m:oMathPara'),fragment
 p.text=new
 changes.append(dict(issue=issue,tag=tag,old=before,new=new))
 return p
def insert_after(anchor,text,issue,tag=None):
 p=doc.add_paragraph(text,style='Normal')
 par(anchor)._p.addnext(p._p)
 changes.append(dict(issue=issue,tag=tag or 'added paragraph',old='',new=text))
 return p

edit('In federated learning, clients retain their data',
'Federated learning trains a shared model using data retained at participating clients rather than transferring their raw examples to a central server (McMahan et al., 2017; Kairouz et al., 2021). Hierarchical implementations place an aggregation tier between clients and the cloud. That tier can reduce wide-area traffic, but the benefit depends on when the edge model is forwarded: exchanging a full aggregate after every round leaves the cloud-update frequency unchanged.',
'E1/R2-M1','Introduction')
edit('After a round with no cloud exchange',
'When the cloud does not receive an update, participating edges may retain locally updated models while the global model remains unchanged. Subsequent clients can therefore begin training from models that differ in age. Client-side encoding poses a separate decision: transmitting sparse values saves bytes only if the discarded coefficients compensate for the indices needed to describe those retained. We study these decisions jointly, measuring both modelled payload volume and final accuracy rather than treating a smaller message as evidence of a better learning policy.',
'R2-M1/R2-M2/R2-M7','Introduction')
edit('Before local training, the scheduler ranks eligible clients',
'AHCE-FL ranks eligible clients using five simulated descriptors—bandwidth, residual energy, accuracy, latency and computing capability—and selects ten participants. Each selected client transmits an encoded difference from its starting model. The assigned edge decodes the update, reconstructs the resulting client model and forms a sample-weighted aggregate. A separate, explicit rule determines whether the cloud replaces its global model with the aggregate of the active edges.',
'R2-M2/R2-M5/R2-M6','Introduction')
edit('We use the same partitioning procedure',
'The evaluation uses a common CIFAR-10 partitioning procedure and the same participation fraction for AHCE-FL and reconstructed FedAvg, FedProx, FedCS and HFL comparators. Every run comprises 100 rounds; paired comparisons use seeds 11, 23 and 42. The original 51-run study tests baseline methods, compression thresholds and synchronization gaps. A further 45 runs examine resource-score weights and the interaction between the divergence threshold and the maximum synchronization gap. These groups test distinct controls; they are not 96 repetitions of a single treatment.',
'R2-M1/R2-M4/R2-M7','Introduction')
edit('Within the threshold sweep',
'The experiments do not establish a general advantage for AHCE-FL. In the baseline comparison, FedAvg achieves higher final accuracy while using fewer modelled bytes. Within AHCE-FL, τ = 0.05 produces the smallest payload but also the lowest accuracy. The initial maximum-gap sweep synchronizes every round, because the divergence condition dominates; when that condition is deliberately suppressed, gaps of 1, 2, 3 and 5 produce 100, 50, 33 and 20 cloud exchanges, respectively. These observations motivate a mechanism-level interpretation rather than a claim of unconditional communication efficiency.',
'R2-M1/R2-M2/R2-M7','Introduction')
insert_after('The experiments do not establish a general advantage',
'For engineering assessment, we make the selection, compression, aggregation and synchronization operations individually traceable to their configurations, algorithms and per-round logs. This permits controlled testing of policy changes and makes failure cases visible. It does not constitute an experimental evaluation of agile development practices or a production cloud deployment.',
'E1/R2-M1','Introduction')

edit('Selecting a client also selects its data.',
'The composition of a participating client set matters because each client also contributes a particular data partition. Kairouz et al. (2021) identify participation and heterogeneity as central federated-learning challenges, and Lim et al. (2020) review the effect of mobile-edge resource constraints. Here, bandwidth, energy, accuracy, latency and computing capability are represented by fixed synthetic descriptors. Reusing a resource ranking can repeatedly select the same clients, potentially narrowing the range of non-IID partitions represented in training. The experiment does not quantify participation fairness or demonstrate that the descriptor weights are optimal.',
'R2-M1/R2-M5/R2-S4','Related work')
edit('ShapeFL jointly considers edge-node association',
'Existing hierarchical systems modify different parts of the learning process. ShapeFL addresses node–edge assignment together with the distribution of data represented at edge aggregators (Deng et al., 2024). HiFlash combines heterogeneity-aware association with staleness control (Wu et al., 2023), while Async-HFL accommodates asynchronous arrivals across gateway and cloud levels (Yu et al., 2023). AHCE-FL instead fixes client–edge membership in the tested simulator and evaluates a five-descriptor client ranking, update encoding and an end-of-round synchronization gate. The resulting mechanism is identifiable, but combining known components alone does not establish technical superiority.',
'R2-M1/R2-S1/R2-S3','Related work')
edit('More recent work addresses transmission control directly',
'Recent approaches show why the baseline comparison must be interpreted cautiously. FedDAC adjusts compression on both device–edge and edge–cloud links using resource conditions (Fan et al., 2025). AHPT-FL selects transmission behaviour in response to changing link observations (Qiu and Li, 2026). In contrast, the present AHCE-FL implementation uses fixed simulated resource descriptors, a deterministic sparse-versus-dense byte comparison and a divergence-or-gap synchronization gate. Neither FedDAC nor AHPT-FL was reproduced in these experiments, so no result here establishes better accuracy, traffic or latency relative to those methods.',
'R2-M1/R2-S3/R2-S4','Related work')
edit('Hierarchical training introduces a timing question',
'Between cloud exchanges, edge and global models may no longer represent the same training state. Async-HFL and delay-aware hierarchical FL study different aspects of this problem (Yu et al., 2023; Lin et al., 2024). Our coordinator makes a decision only after the current round has finished local training and edge aggregation. It measures the Euclidean distance between the candidate cloud model and the stored global model and compares the elapsed rounds with the configured maximum gap. This rule reacts to model-state divergence and elapsed rounds; the experiment does not demonstrate adaptation to measured wireless congestion or battery state.',
'R2-M2/R2-S2','Related work')
edit('In these runs, the CIFAR-10 training images stay',
'The simulator retains CIFAR-10 training images in its client partitions and transmits model representations rather than raw images. Data locality is a basic federated-learning property, not a formal privacy guarantee. Parameter updates can still reveal information or be manipulated by malicious participants (Bagdasaryan et al., 2020; Truex et al., 2020). The implementation provides neither differential privacy nor secure aggregation, encrypted transport, multiparty computation or trusted execution. Attack resistance and leakage were not measured, and no such protection is claimed.',
'R2-M8/R2-M9','Related work')
edit('Reconstructed FedAvg finished at higher accuracy',
'The baseline result is unfavorable to AHCE-FL on both final accuracy and modelled communication relative to FedAvg. HFL finishes with higher accuracy than AHCE-FL but consumes more modelled bytes. The sparsification sweep demonstrates a clear accuracy cost at the most aggressive threshold; the gap sweep demonstrates fewer cloud exchanges only when the divergence trigger does not intervene. These controls are therefore useful for explaining the communication–accuracy trade-off, not for claiming universal improvement.',
'R2-M1/R2-M7/R2-M11','Results discussion')
edit('We count the bytes used for parameter values',
'The communication ledger counts parameter values and any retained sparse indices, with each transfer counted once. It does not include packet headers, fragmentation, acknowledgements, retries or shared-channel contention. The critical-path quantity is an analytical estimate based on synthetic link parameters, not measured elapsed time. Likewise, the energy variable influences simulated selection but was not obtained from battery-discharge measurements. Hardware measurements would be necessary to evaluate radio traffic, end-to-end delay and energy use.',
'R2-M11','Limitations')
edit('The additional 45 runs were verified against',
'Each of the 45 supplementary experiments has a consecutive 100-round record, an explicit seed and configuration, a final-result summary and a file-integrity manifest. The original nine numerical figures and nine tables remain associated with the preceding 51-run campaign; Tables 10 and 11 are calculated from the additional runs. We retained the embedded figures and checked their displayed principal values against archived summaries, although an exhaustive extraction of each plotted pixel was not performed.',
'R1-CLARITY/R2-M11','Limitations')
edit('The 51 CIFAR-10 runs show how the two controls save bytes.',
'The controlled runs distinguish two mechanisms that can lower modelled transfer volume within AHCE-FL. At τ = 0.05, the modelled total is 288659957 bytes and mean final accuracy falls to 0.186133. When divergence triggering is suppressed, increasing G from 1 to 5 reduces cloud exchanges from 100 to 20 (Table 8, Figure 7). These changes quantify mechanism behaviour under the specified simulator, rather than improvements over every baseline.',
'R2-M1/R2-M7/R2-M11','Conclusion')
edit('In the baseline runs, AHCE-FL reached',
'Across the baseline seeds, AHCE-FL obtains mean final accuracy 0.473067 and transmits 366004619 modelled bytes. Reconstructed FedAvg instead obtains 0.643467 accuracy with 308560000 bytes under corrected direct-transfer accounting. This negative comparison is central to the interpretation: the present client-ranking and hierarchical communication policies do not outperform FedAvg on these two outcomes. Further experiments with different data partitions, model architectures and participating devices are required before assessing generality.',
'R2-M1/R2-M11','Conclusion')
edit('In an additional 45-run, three-seed evaluation',
'The supplementary 45-run study adds two diagnostic results. First, none of the five nonuniform resource-weight profiles provides Holm-adjusted evidence of higher accuracy than equal weighting across the three paired seeds. Second, cloud exchanges depend on the joint divergence and maximum-gap settings: a permissive divergence trigger can eliminate the apparent benefit of a longer timer. These are simulation-level findings. They neither establish non-inferiority in predictive performance nor validate physical packet, latency or energy benefits.',
'R2-M2/R2-M5/R2-M11','Conclusion')

# Insert explicit experimental traceability note before the experimental results, without modifying equations/algorithms.
insert_after('Each of the 45 supplementary experiments',
'For reproducibility, the release records the run configuration, selected seed, 100-round data, final metrics, trigger reason and checksum for each supplementary experiment. The 12 legacy comparator metadata inconsistencies are disclosed in a provenance sidecar rather than silently rewriting the original measurements. Exact communication-accounting conventions are stated alongside Tables 4–5.',
'R2-M3/R2-M11','Limitations')

# Reviewer's six-way mechanism matrix, appended as a short non-numerical table following Table 1.
# Distinguish study mechanisms from proofs of non-IID robustness.
base_t=doc.tables[0]
# Current comparison already includes method, selection, compression, hierarchy, sync, privacy.
# Extend with explicit non-IID evidence rather than replacing existing table cells.
base_t.add_column(Inches(0.91))
v=['Non-IID','Tested only','Not established','Heterogeneity studied','Heterogeneity studied','Non-IID tested']
assert len(v)==len(base_t.rows)
for row,word in zip(base_t.rows,v): row.cells[-1].text=word
base_t.rows[0].cells[-1].paragraphs[0].runs[0].bold=True
base_t.style='Table Grid'
changes.append(dict(issue='R2-S1/R2-S2',tag='Table 1 comparison expanded',old='six columns',new='seven columns, including non-IID evidence qualifiers'))

# Add contextual sentence under Table 1 (caption anchor).
insert_after('We use Table 1 to compare where each method makes its decisions',
'The new non-IID column distinguishes evaluation under heterogeneous partitions from a proved robustness guarantee. An entry of “not established here” means that the cited mechanism or the evidence reviewed does not justify an affirmative claim, not that the source system necessarily lacks the feature.',
'R2-S1/R2-S2','Related work')

# Preserve images/equations (except intentional conceptual Table 1 column change).
doc.core_properties.author='';doc.core_properties.last_modified_by=''
doc.save(CLEAN)

# Reviewer identifiers mirror the October 10 editorial email, not invented questions.
COMMENTS=[
('E1','Editor: detailed response at the beginning, page references and highlighted changes.',
 'Prepared a separate point-by-point response, a front-matter response copy, and a manuscript with marked revisions. Locations are cross-referenced by section and page after rendering.','Response front matter; annotated manuscript','Complied'),
('E2','Editor: update relevant recent literature, including journal literature where appropriate.',
 'Added the publisher-verified FedDAC (2025) and AHPT-FL (2026) studies and retained reviewer-suggested pertinent sources. Unrelated references were not added merely to increase the count; journal-specific citation would require a directly relevant verified study.','§2.3–2.4; References','Addressed with bounded scope'),
('R1','Reviewer 1: no mandatory changes or suggestions; clarity of tables and illustrations rated marginal.',
 'Thanked reviewer. Refined the prose and comparison table while preserving and auditing nine original figure assets and eleven data tables.','§2; §5; Table 1; Figures 1–9','Addressed'),
('R2-M1','Novelty and technical differentiation insufficient; combination of known mechanisms.',
 'Separated established prior mechanisms from this implementation, explained the deterministic selection/encoding/synchronization interactions, provided 18 selection-weight and 27 joint synchronization runs, and explicitly acknowledged that FedAvg performs better on baseline accuracy and modelled bytes. Neither novel component invention nor superiority is asserted.','§1; §2.3; §5.1; §§5.7–5.9; §6','Resolved within reported evidence'),
('R2-M2','Adaptive synchronization lacks mathematical model, explicit rule and triggers.',
 'Equation (5) and Algorithm 2 specify the threshold-or-maximum-gap decision, cached states and cloud replacement. The 27-run crossed G–δ experiment identifies timer-versus-divergence dominance from round-level reasons. No measured network-condition adaptation is claimed.','§3.5; Algorithm 2; §§5.4, 5.8; Table 11','Resolved within simulator'),
('R2-M3','Citation-reference mismatches, including prior Reference [13].',
 'Rebuilt an alphabetic author–date bibliography; screened all original titles in SciSpace, reconciled publisher/DOI metadata and added citation-to-source ledger. All 18 references in this revision have in-text citations. The former numbered Reference [13] cannot be mapped directly to the revised author–date numbering.','§2; References; citation ledger','Metadata and citation coverage resolved; full-text audit qualified'),
('R2-M4','Some descriptions of previous work do not match their references.',
 'Corrected specificity for FedAvg, ShapeFL, HiFlash, asynchronous learning and privacy; separated external claims from hypotheses and study-specific parameter choices. The source ledger documents available evidence and remaining full-text limitations.','§2.1–2.5; §4.2','Addressed with source limits'),
('R2-M5','Client-score coefficients unspecified and unjustified.',
 'Equation (2), Algorithm 1 and Table 2 identify five normalized features with equal weights of 0.2, including latency inversion. Six weight profiles across three seeds test sensitivity. No selection of an optimal weight is claimed; no Holm-adjusted accuracy advantage appeared.','§3.3; Algorithm 1; Table 2; §5.7; Table 10','Resolved; optimality not established'),
('R2-M6','Computing capability absent from the participation score.',
 'The implemented formula and Algorithm 1 explicitly use the computing-capability descriptor as the fifth scored feature; equal weight 0.2 in the baseline.','§3.3; Eq. (2); Algorithm 1','Resolved'),
('R2-M7','Threshold τ = 0.01 lacks justification and sensitivity evidence.',
 'Section 5.3 compares τ ∈ {0, 0.001, 0.01, 0.05} with accuracy and byte totals. τ = 0.01 is a tested reference configuration rather than a theoretically optimal threshold. At τ = 0.05 the lower payload incurs substantial accuracy loss.','§3.4; §4.3; §5.3; Table 7; Figures 5–6','Resolved experimentally'),
('R2-M8','Privacy-preserving claim unsupported by a concrete mechanism.',
 'Restricted the claim to raw-data locality and stated explicitly that no differential privacy, secure aggregation, MPC, TEE or verified encrypted transport was implemented.','§2.5; §5.6; Table 1','Resolved'),
('R2-M9','Figure 2 incorrectly labels differential privacy and secure communication.',
 'Retained the corrected operational Figure 2, which contains ranking, training, sparse update encoding, edge aggregation and synchronization without unsupported security labels.','Figure 2; §3.1','Resolved'),
('R2-M10','CNN architecture incomplete.',
 'Table 3 records input shape, both convolutional layers (3→16 and 16→32; kernel 3), pooling, dense layers 512→64→10 and 38,570 trainable parameters.','§4.2; Table 3','Resolved'),
('R2-M11','Model size and communication numbers, including legacy Figure 3 values, unverifiable.',
 'Table 3 gives 38,570 float32 parameters (154,280-byte dense state). The ledger distinguishes each direct transfer once and reports original 51 runs plus 45 audited ablations. Legacy 935/820/760/690/520 MB figures are not reused because the archived runs do not verify them.','§3.6; §4.2; Tables 3–5, 10–11; Figure 4; reproducibility audit','Resolved for modelled totals; physical traffic not measured'),
('R2-S1','Restructure related work into five themes and six-way comparison matrix including non-IID evidence.',
 'Related work is organized into communication compression, selection, hierarchical FL, asynchronous FL and privacy. Table 1 now includes selection, compression, hierarchy, synchronization, explicit privacy and non-IID evidence.','§2.1–2.5; Table 1','Addressed'),
('R2-S2','Distinguish the five research streams and compare them technically.',
 'Clarified each mechanism at its actual decision point and distinguished reported evidence from assumed capabilities.','§2.1–2.5; Table 1','Addressed'),
('R2-S3','Novelty positioning against recent hierarchical/compression methods remains weak.',
 'Added comparisons to FedDAC and AHPT-FL and made explicit that neither was experimentally reproduced; no claim of superiority over these studies is made.','§2.3; References','Addressed without unsupported performance claims'),
('R2-S4','Recent heterogeneous-device, resource-aware and asynchronous work missing.',
 'Included relevant Chowdhury, Wen, Tseng, Fan and Qiu studies with mechanisms and stated the fixed-descriptor limitation.','§2.2–2.4; References','Addressed'),
('R2-S5','Literature survey overly descriptive and lacks technical comparison.',
 'Used a mechanism-based Table 1 and prose comparing selection, encoding, aggregation and synchronization rather than a list of claimed benefits.','§2.1–2.5; Table 1','Addressed'),
('R2-S6','Suggested eight specific citations.',
 'Retained verified and directly relevant Chowdhury, Shabariram, Wen and SCGAT-HFL; the other four suggested items (Li vehicle security; Zheng integrity auditing; Tseng MEC-based HFL; Tseng VFLDiff) are not inserted without claim-specific source verification and a direct technical fit. Two independently verified recent communication-control studies were added.','§2; References; reference ledger','Partially adopted; irrelevant or unverified citations not padded')
]

# Create stand-alone response, annotated item sheet, and response-front highlighted reviewer copy.
def setup(document,heading):
 sec=document.sections[0]
 sec.header_distance=Inches(.4);sec.footer_distance=Inches(.4)
 core=document.core_properties;core.author='';core.last_modified_by=''
 h=document.add_heading(heading,level=0)
 h.alignment=WD_ALIGN_PARAGRAPH.CENTER
 document.add_paragraph('Manuscript IJAESD-345169 — AHCE-FL (double-blind reviewer copy)')
def add_comment(doc,row,highlight=False,location_suffix=''):
 code,comment,response,location,status=row
 h=doc.add_heading(code+' — '+('Editorial request' if code.startswith('E') else 'Reviewer comment'),level=2)
 p=doc.add_paragraph(style='Normal')
 run=p.add_run('Comment: '+comment);run.bold=True
 p=doc.add_paragraph('Response: '+response)
 if highlight:
  for r in p.runs:r.font.highlight_color=WD_COLOR_INDEX.YELLOW
 doc.add_paragraph('Location: '+location+location_suffix)
 doc.add_paragraph('Disposition: '+status)
 return h
response=Document();setup(response,'Detailed Response to the Editor and Reviewers')
response.add_paragraph('This reply addresses the decision dated 10 October 2026. Reviewer 1 required no mandatory changes. Reviewer 2’s mandatory observations and recommendations are treated separately. The new manuscript contains 96 experimental configurations (51 original and 45 additional); the response does not claim that every suggested comparator or physical system was experimentally evaluated.')
for row in COMMENTS:add_comment(response,row)
response.add_heading('Scientific interpretation and remaining limits',level=2)
response.add_paragraph('The reconstructed FedAvg baseline exceeds AHCE-FL on both final accuracy and modelled communication. The additional weight ablations provide no Holm-adjusted evidence of an accuracy improvement. Network radio traffic, physical energy and end-to-end hardware latency remain unmeasured. Full-text verification of each cited sentence is not claimed. Editorial suitability for IJAESD remains the editor’s decision.')
response.save(RESP)

sheet=Document();setup(sheet,'Annotated Reviewer-Change Sheet')
sheet.add_paragraph('Change register for the IJAESD-345169 reviewer revision. This is a companion audit document, not a new set of experimental results.')
t=sheet.add_table(rows=1,cols=4);t.style='Table Grid'
for c,h in zip(t.rows[0].cells,['Ref.','Action / change','Manuscript location','Status']):c.text=h
for code,comment,response,location,status in COMMENTS:
 cells=t.add_row().cells
 for c,val in zip(cells,[code,response,location,status]):c.text=val
 for c in cells:
  c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
  for p in c.paragraphs:
   for r in p.runs:r.font.size=Pt(8)
sheet.add_heading('Evidence and provenance',level=2)
sheet.add_paragraph('Experiment records, paired statistics and table consistency are tracked in the repository: original audit 125/125; 45 additional 100-round configurations; Table 10/11 independent audit 92/92 on the previous version; seven implementation unit tests. This revision changes conceptual Table 1 and prose, not the archived measurements. Reviewer comments are drawn from the forwarded Inderscience revision email of 10 October 2026.')
sheet.add_heading('Not claimed as completed',level=2)
sheet.add_paragraph('Independent end-to-end hardware testing, secure aggregation/privacy guarantees, quantified production energy savings, broad cross-dataset performance, and full-text access to every cited paper.')
sheet.save(SHEET)

# Annotated paper: highlight textual edits by matching new paragraph text; descriptive Table 1 is highlighted too.
highlighted=Document(CLEAN)
added_texts=[x['new'] for x in changes if x['new']]
n=0
for p in highlighted.paragraphs:
 if p.text in added_texts:
  for run in p.runs:run.font.highlight_color=WD_COLOR_INDEX.YELLOW
  n+=1
for row in highlighted.tables[0].rows:
 for run in row.cells[-1].paragraphs[0].runs: run.font.highlight_color=WD_COLOR_INDEX.YELLOW
highlighted.save(MARKED)

# The journal requests a detailed response before the revised manuscript.
combined=Document(MARKED)
first=combined.paragraphs[0]._p
def move_to_top(p):
 first.addprevious(p._p)
header=combined.add_paragraph()
header.style='Title';header.add_run('Point-by-Point Response to Reviewers')
move_to_top(header)
sub=combined.add_paragraph('IJAESD-345169 | anonymised revised manuscript | editorial decision 10 October 2026')
move_to_top(sub)
intro=combined.add_paragraph('The following responses address the editor, Reviewer 1 and Reviewer 2. Updated prose is highlighted yellow in the article after this response. Page references are supplied in the response-sheet companion after final rendering.')
move_to_top(intro)
for code,comment,answer,location,status in COMMENTS:
 h=combined.add_paragraph(code+' — '+comment);h.style='Heading 2';move_to_top(h)
 a=combined.add_paragraph('Response: '+answer);move_to_top(a)
 loc=combined.add_paragraph('Revised article: '+location+' [PAGE_LOC]');move_to_top(loc)
last=combined.add_paragraph()
last.add_run().add_break(WD_BREAK.PAGE)
move_to_top(last)
combined.save(COMBINED)

# Check preservation of mathematical objects, image binaries, and tables 2-11.
with_source=Document(SRC);with_clean=Document(CLEAN)
assert len(with_source.inline_shapes)==len(with_clean.inline_shapes)==9
assert len(with_source.tables)==len(with_clean.tables)==11
for index in range(1,11):
 aa=[[c.text for c in row.cells] for row in with_source.tables[index].rows]
 bb=[[c.text for c in row.cells] for row in with_clean.tables[index].rows]
 assert aa==bb,('changed numeric table',index+1)
from zipfile import ZipFile
with ZipFile(SRC) as x,ZipFile(CLEAN) as y:
 ax={name:hashlib.sha256(x.read(name)).hexdigest() for name in x.namelist() if name.startswith('word/media/')}
 ay={name:hashlib.sha256(y.read(name)).hexdigest() for name in y.namelist() if name.startswith('word/media/')}
 assert ax==ay and len(ax)==9
report={'source':str(SRC),'source_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),
'clean_sha256':hashlib.sha256(CLEAN.read_bytes()).hexdigest(),
'change_count':len(changes),'review_items':len(COMMENTS),'highlighted_paragraphs':n,
'preserved_images':9,'preserved_numeric_tables':10,'conceptual_table_1_expanded':True,
'limitations':['Review comments are authentic; one reviewer suggested references not all independently confirmed as relevant','Hardware measurements not performed','No measured superiority over FedAvg'],
'changes':changes}
(DEST/'REVISION_CHANGE_LOG.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
print('PACKAGE_CREATED',[(p.name,p.stat().st_size) for p in [CLEAN,MARKED,RESP,SHEET,COMBINED]])
print('PARAGRAPHS_HIGHLIGHTED',n,'REVIEWER_ITEMS',len(COMMENTS),'CHANGES',len(changes))
