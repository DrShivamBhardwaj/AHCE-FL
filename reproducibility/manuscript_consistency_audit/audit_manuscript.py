#!/usr/bin/env python3
"""Read-only, independent audit of the archived blinded manuscript against CSV runs."""
import collections,csv,datetime as dt,hashlib,json,math,re,zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
import numpy as np
from scipy import stats
ROOT=Path(__file__).resolve().parents[2]
DOC=ROOT/"manuscripts/IJAESD-345169/AHCE_FL_Final_Audited_Blind.docx"
OUT=Path(__file__).resolve().parent
SOURCES={
"baseline": ROOT/"reproducibility/cifar10_100round",
"compression":ROOT/"reproducibility/cifar10_sensitivity",
"original_sync":ROOT/"reproducibility/cifar10_sensitivity",
"corrected_gap":ROOT/"reproducibility/sync_corrected",
}
N={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
with zipfile.ZipFile(DOC) as z:
 root=ET.fromstring(z.read('word/document.xml'))
 body=root.find('w:body',N)
 tables=[];paragraphs=[]
 for i,elem in enumerate(body):
  if elem.tag.endswith('}p'):
   s=''.join(t.text or '' for t in elem.findall('.//w:t',N))
   if s.strip():paragraphs.append({'idx':i,'text':s})
  if elem.tag.endswith('}tbl'):
   table=[]
   for tr in elem.findall('w:tr',N):
    table.append([' '.join(''.join(t.text or '' for t in p.findall('.//w:t',N)) for p in cell.findall('w:p',N)).strip() for cell in tr.findall('w:tc',N)])
   tables.append(table)
 media=[n for n in z.namelist() if n.startswith('word/media/') and not n.endswith('/')]
 assert len(tables)==9, len(tables)
 assert len(media)>=9, len(media)
 find_lines=['abstract','table 4.','table 5.','table 6.','table 7.','table 8.','table 9.','figure 1.']
 issues=[];checks=[]
 def check(name,ok,detail):
  checks.append({'check':name,'passed':bool(ok),'detail':detail})
  if not ok:issues.append({'check':name,'detail':detail})
 def eq(actual,expected,decimals=6):return abs(float(str(actual).replace('−','-'))-float(expected)) <= (0.5*10**(-decimals)+1e-12)
 def csvrows(path):
  with path.open(newline='') as f:return list(csv.DictReader(f))
 def get(kind,setting,seed):
  if kind=='baseline':p=SOURCES[kind]/f'manuscript_cifar10_cifar10_{setting}_seed{seed}_tau0.01.csv'
  elif kind=='compression':p=SOURCES[kind]/f'cifar10_compression_tau_{setting}_cifar10_ahce-fl_seed{seed}_tau{setting}.csv'
  elif kind=='original_sync':p=SOURCES[kind]/f'cifar10_synchronization_gap_{setting}_cifar10_ahce-fl_seed{seed}_tau0.01.csv'
  else:p=SOURCES[kind]/f'cifar10_sync_corrected_gap_{setting}_cifar10_ahce-fl_seed{seed}_tau0.01.csv'
  return p,csvrows(p)
 runs=[]
 groups=[('baseline',['fedavg','fedprox','fedcs','hfl','ahce-fl']),('compression',['0','0.001','0.01','0.05']),('original_sync',['1','2','3','5']),('corrected_gap',['1','2','3','5'])]
 seeds=[11,23,42]
 for kind,settings in groups:
  for setting in settings:
   for seed in seeds:
    path,rows=get(kind,setting,seed)
    rounds=[int(float(x['round'])) for x in rows]
    check(f'rounds:{kind}:{setting}:{seed}',len(rows)==100 and rounds==list(range(1,101)),f'{len(rows)} rows, start {rounds[:2]}, end {rounds[-2:]}')
    syncs=sum(int(x['sync_triggered']) for x in rows)
    final_acc=float(rows[-1]['accuracy'])
    if kind=='baseline' and setting in ['fedavg','fedprox','fedcs']:
     modeled_bytes=sum(int(x['client_upload_bytes'])+int(x['client_download_bytes']) for x in rows)
     duplicate=sum(int(x['cloud_upload_bytes'])+int(x['cloud_download_bytes']) for x in rows)
     check('direct_baseline_accounting:'+setting+':'+str(seed),modeled_bytes==308560000 and duplicate==308560000,
       f'client up+down {modeled_bytes}, redundant cloud columns {duplicate}')
    else:modeled_bytes=sum(int(x['total_bytes']) for x in rows)
    if kind=='corrected_gap':
     reasons=collections.Counter(x.get('sync_reason') for x in rows)
     check('gap_trigger:'+setting+':'+str(seed),reasons.get('divergence',0)==0 and reasons.get('both',0)==0 and reasons.get('max_gap',0)==syncs,
       f'syncs {syncs}, sync_reason {dict(reasons)}')
    runs.append({'group':kind,'setting':setting,'seed':seed,'accuracy':final_acc,
                 'bytes':modeled_bytes,'syncs':syncs,'csv':str(path.relative_to(ROOT)),
                 'csv_sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
 check('count:51',len(runs)==51,f'{len(runs)} distinct CSV run files')
 def vals(group,setting,key):return [next(r[key] for r in runs if r['group']==group and r['setting']==setting and r['seed']==seed) for seed in seeds]
 def mean(group,setting,key):return np.mean(vals(group,setting,key))
 # Manuscript Table 4
 for row in tables[3][1:]:
  method=row[0].lower()
  for i,seed in enumerate(seeds):
   actual=next(r['accuracy'] for r in runs if r['group']=='baseline' and r['setting']==method and r['seed']==seed)
   check(f'table4:{method}:seed{seed}',eq(float(row[i+1]),actual,4),f'manuscript={row[i+1]} archived={actual}')
  check(f'table4:{method}:mean',eq(float(row[4]),mean('baseline',method,'accuracy')),f'manuscript={row[4]} archived={mean("baseline",method,"accuracy"):.10f}')
 # Table 5
 for row in tables[4][1:]:
  method=row[0].lower()
  mb=mean('baseline',method,'bytes')
  n=mean('baseline',method,'syncs')
  check('table5:'+method,round(mb)==int(row[1]) and round(n)==int(row[2]),f'bytes manuscript={row[1]} archived={mb:.7f}; sync={row[2]}/{n}')
 # Table 6
 for row in tables[5][1:]:
  method=row[0].lower();diff=np.array(vals('baseline','ahce-fl','accuracy'))-np.array(vals('baseline',method,'accuracy'))
  n=len(diff);md=float(diff.mean());sem=stats.sem(diff)
  lo,hi=stats.t.interval(0.95,n-1,loc=md,scale=sem);pv=float(stats.ttest_rel(vals('baseline','ahce-fl','accuracy'),vals('baseline',method,'accuracy')).pvalue)
  nums=re.findall(r'-?\d+\.\d+(?:e[-+]?\d+)?',row[2].replace('−','-'))
  check('table6:'+method,eq(row[1],md,6) and len(nums)==2 and eq(float(nums[0]),lo,10) and eq(float(nums[1]),hi,10) and eq(row[3],pv,10),
        f'mean={md} CI=[{lo},{hi}] p={pv}')
 # Tables 7 / 8
 for ix,kind in ((6,'compression'),(7,'corrected_gap')):
  for row in tables[ix][1:]:
   setting=row[0]
   conditions=[eq(row[i+1],vals(kind,setting,'accuracy')[i],4) for i in range(3)]
   conditions.append(eq(row[4],mean(kind,setting,'accuracy'),6))
   if kind=='compression':
    conditions.append(round(mean(kind,setting,'bytes'))==int(row[5]))
   else:
    conditions.append(int(mean(kind,setting,'syncs'))==int(row[5]))
    conditions.append(round(mean(kind,setting,'bytes'))==int(row[6]))
   check('table'+str(ix+1)+':'+setting,all(conditions),f'per seed correct={conditions[:3]}, mean={mean(kind,setting,"accuracy")}, bytes={mean(kind,setting,"bytes")}, sync={mean(kind,setting,"syncs")}')
 # Table 9
 for row in tables[8][1:]:
  setting=re.search(r'\d+',row[0]).group()
  diff=np.array(vals('corrected_gap',setting,'accuracy'))-np.array(vals('corrected_gap','1','accuracy'))
  md=float(diff.mean());lo,hi=stats.t.interval(0.95,2,loc=md,scale=stats.sem(diff))
  pv=float(stats.ttest_rel(vals('corrected_gap',setting,'accuracy'),vals('corrected_gap','1','accuracy')).pvalue)
  nums=re.findall(r'-?\d+\.\d+(?:e[-+]?\d+)?',row[2].replace('−','-'))
  check('table9:G'+setting,eq(row[1],md,10) and len(nums)==2 and eq(float(nums[0]),lo,10) and eq(float(nums[1]),hi,10) and eq(row[3],pv,10),
        f'paired mean={md}; CI=[{lo},{hi}]; p={pv}')
 # Figure and documentary checks
 text='\n'.join(p['text'] for p in paragraphs)
 for n in range(1,10):
  count=len(re.findall(r'Figure '+str(n)+r'\.',text))
  check(f'figure_{n}_caption',count>=1,f'{count} caption or textual mentions; {len(media)} total embedded media files')
 check('figures_embedded',len(media)>=9,f'{len(media)} image objects')
 check('manuscript_51_run_statement','51 CIFAR-10 simulation runs' in text and len(runs)==51, f'CSV experiments {len(runs)}')
 check('manuscript_model_parameter_count',len(runs)==51 and all(int(float(row['parameters']))==38570 for r in runs for row in get(r['group'],r['setting'],r['seed'])[1]),'all per-round CSV rows show 38,570 model parameters')
 # Baseline provenance issue: JSON configurations copied from AHCE-FL despite correct actual method property
 mismatches=[]
 for r in runs:
  p=ROOT/r['csv'].replace('.csv','.json')
  if p.exists():
   j=json.loads(p.read_text())
   if j.get('configuration',{}).get('method')!=j.get('method'): mismatches.append(str(p.relative_to(ROOT)))
 report={'audited_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'source_docx':str(DOC.relative_to(ROOT)),
 'docx_sha256':hashlib.sha256(DOC.read_bytes()).hexdigest(),
 'total_checks':len(checks),'passed_checks':sum(c['passed'] for c in checks),
 'failed_checks':sum(not c['passed'] for c in checks),
 'findings':issues,'configuration_method_metadata_discrepancies':mismatches,
 'legacy_report_caveat':'EVIDENCE_REPORT.md flat baseline modeled bytes 617120000 include duplicate cloud columns; final manuscript correctly uses client upload/download once: 308560000',
 'claims_scope':'Single-process simulation, synthetic network parameters; not empirical network or battery measurements',
 'csv_runs':runs,'checks':checks}
 (OUT/'AUDIT_RESULTS.json').write_text(json.dumps(report,indent=2)+'\n')
 lines=['# AHCE-FL independent manuscript-to-results consistency audit','',
 f'Audited UTC: {report["audited_utc"]}',
 f'Manuscript: `{report["source_docx"]}`',
 f'DOCX SHA-256: `{report["docx_sha256"]}`','',
 f'**Checks: {report["passed_checks"]}/{report["total_checks"]} passed; {report["failed_checks"]} failed.**',
 '','## Primary evidence','- Independently checked all 51 source CSVs, each with 100 rounds.',
 '- Recalculated accuracy, modeled bytes, cloud-sync events, paired 95% t intervals and unadjusted p-values for manuscript Tables 4–9.',
 '- Verified flat direct-transfer baseline accounting explicitly excludes redundant cloud columns.',
 '- Checked nine figure captions and presence of embedded images (not pixel-level chart accuracy).',
 '','## Limitations and provenance caveats',
 '- Source experiment JSON configuration.method can report ahce-fl even when the top-level method is a different comparator. The separate actual method, filename and per-round logs define each group; this metadata discrepancy should be corrected in a future provenance-only update, without rewriting results.',
 '- Historic EVIDENCE_REPORT.md uses 617120000 modeled bytes for flat baselines. The final manuscript uses 308560000 after excluding duplicate direct-transfer cloud entries. Interpret the two ledgers separately.',
 '- All statistical contrasts rely on only three paired seeds; p-values are exploratory and require cautious interpretation.',
 '- This audit validates internal numerical consistency, not external scholarly references, journal formatting, plot pixels or hardware energy/latency.',
 '',f'Configuration-method metadata mismatches: {len(mismatches)} JSON files.','',
 '## Failed checks']
 if issues:
  lines.extend(f'- **{i["check"]}**: {i["detail"]}' for i in issues)
 else:lines.append('- None in the automated table/CSV checks.')
 lines+=['','## Git integrity','All analyzed CSVs include SHA-256 in `AUDIT_RESULTS.json`. The original manuscript and experiment files were not modified.']
 (OUT/'AUDIT_REPORT.md').write_text('\n'.join(lines)+'\n')
 print('AUDIT_SUMMARY',report['passed_checks'],report['total_checks'],'FAILED',len(issues),'JSON_METADATA_MISMATCHES',len(mismatches),'MEDIA',len(media))
 for issue in issues[:25]:print('ISSUE',issue)
