"""Auditable final-accuracy and modeled-communication evidence analysis."""
import csv
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reproducibility/revision_analysis'
OUT.mkdir(parents=True, exist_ok=True)
seeds = (11,23,42)


def rows(path):
    with path.open(newline='') as handle:
        data=list(csv.DictReader(handle))
    if len(data)!=100 or int(data[-1]['round'])!=100:
        raise RuntimeError('Expected 100-round output: '+str(path))
    return data


def sample(path, seed, group, value):
    r=rows(path)
    return {'group':group, 'setting':str(value), 'seed':seed,
            'accuracy':float(r[-1]['accuracy']),
            'modeled_total_bytes':sum(int(x['total_bytes']) for x in r),
            'sync_count':sum(int(x['sync_triggered']) for x in r),
            'run_file':path.name}

all_data=[]
for method in ('fedavg','fedprox','fedcs','hfl','ahce-fl'):
    for seed in seeds:
        name=f'manuscript_cifar10_cifar10_{method}_seed{seed}_tau0.01.csv'
        all_data.append(sample(ROOT/'reproducibility/cifar10_100round'/name,seed,'baseline',method))
for tau in ('0','0.001','0.01','0.05'):
    for seed in seeds:
        name=f'cifar10_compression_tau_{tau}_cifar10_ahce-fl_seed{seed}_tau{tau}.csv'
        all_data.append(sample(ROOT/'reproducibility/cifar10_sensitivity'/name,seed,'compression',tau))
for gap in (1,2,3,5):
    for seed in seeds:
        name=f'cifar10_synchronization_gap_{gap}_cifar10_ahce-fl_seed{seed}_tau0.01.csv'
        all_data.append(sample(ROOT/'reproducibility/cifar10_sensitivity'/name,seed,'original_sync',gap))
corrected=ROOT/'reproducibility/sync_corrected'
for gap in (1,2,3,5):
    for seed in seeds:
        f=corrected/f'cifar10_sync_corrected_gap_{gap}_cifar10_ahce-fl_seed{seed}_tau0.01.csv'
        if f.exists():
            all_data.append(sample(f,seed,'corrected_gap',gap))

def group_summary(data):
    by=defaultdict(list)
    for x in data:
        by[(x['group'],x['setting'])].append(x)
    out=[]
    for (group,setting),items in sorted(by.items()):
        a=[x['accuracy'] for x in items]
        b=[x['modeled_total_bytes'] for x in items]
        s=[x['sync_count'] for x in items]
        mean=statistics.mean(a)
        sd=statistics.stdev(a) if len(a)>1 else None
        ci=stats.t.ppf(.975,len(a)-1)*sd/math.sqrt(len(a)) if sd is not None else None
        out.append({'group':group,'setting':setting,'n':len(a),
                    'accuracy_mean':mean,'accuracy_sd':sd,
                    'accuracy_ci95_lower':mean-ci if ci is not None else None,
                    'accuracy_ci95_upper':mean+ci if ci is not None else None,
                    'mean_modeled_total_bytes':statistics.mean(b),
                    'mean_cloud_sync_count':statistics.mean(s)})
    return out

summary=group_summary(all_data)

paired=[]
groups=defaultdict(dict)
for item in all_data:
    groups[(item['group'],item['setting'])][item['seed']]=item['accuracy']
for group,reference in [('baseline','ahce-fl'),('compression','0'),('original_sync','1'),('corrected_gap','1')]:
    candidates=sorted(v for g,v in groups if g==group and v!=reference)
    for candidate in candidates:
        A=groups[(group,candidate)]
        B=groups[(group,reference)]
        shared=sorted(set(A)&set(B))
        if len(shared)!=3:continue
        differences=[A[s]-B[s] for s in shared]
        mean=statistics.mean(differences)
        sd=statistics.stdev(differences)
        t=stats.ttest_rel([A[s] for s in shared],[B[s] for s in shared])
        margin=stats.t.ppf(.975,2)*sd/math.sqrt(3)
        paired.append({'group':group,'candidate':candidate,'reference':reference,
                       'seed_count':3,'mean_accuracy_difference':mean,
                       'ci95_lower':mean-margin,'ci95_upper':mean+margin,
                       'p_value':float(t.pvalue) if math.isfinite(t.statistic) else (1.0 if sd==0 else None)})

(OUT/'individual_runs.json').write_text(json.dumps(all_data,indent=2)+'\n')
(OUT/'descriptive_statistics.json').write_text(json.dumps(summary,indent=2)+'\n')
(OUT/'paired_tests.json').write_text(json.dumps(paired,indent=2)+'\n')

with (OUT/'statistics.csv').open('w',newline='') as h:
    writer=csv.DictWriter(h,fieldnames=list(summary[0]))
    writer.writeheader();writer.writerows(summary)

def svg_line(filename, group, ylabel, key, *, scale=1.0):
    ss=[x for x in summary if x['group']==group]
    if not ss:return
    points=[(x['setting'],x[key]*scale) for x in ss]
    if group=='compression':points.sort(key=lambda x:float(x[0]))
    else:points.sort(key=lambda x:int(x[0]))
    v=[x[1] for x in points]
    lo=min(0,min(v));hi=max(v)*1.13 if max(v)>0 else 1
    width,height=720,430
    xpoints=[100+i*500/max(1,len(points)-1) for i in range(len(points))]
    ypoints=[350-280*(q-lo)/(hi-lo) for _,q in points]
    parts=['<svg xmlns="http://www.w3.org/2000/svg" width="720" height="430" viewBox="0 0 720 430">',
           '<rect width="720" height="430" fill="white"/>',
           '<path d="M100 45 V350 H630" stroke="black" fill="none" stroke-width="2"/>']
    for (label,num),x,y in zip(points,xpoints,ypoints):
        parts.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="5" fill="black"/>')
        parts.append(f'<text x="{x:.2f}" y="379" text-anchor="middle" font-size="15" font-family="serif">{label}</text>')
        parts.append(f'<text x="{x:.2f}" y="{y-13:.2f}" text-anchor="middle" font-size="14" font-family="serif">{num:.3f}</text>')
    parts.append('<polyline fill="none" stroke="black" stroke-width="2" points="'+ ' '.join(f'{x:.2f},{y:.2f}' for x,y in zip(xpoints,ypoints))+'"/>')
    parts.append(f'<text x="365" y="414" text-anchor="middle" font-size="16" font-family="serif">{("Compression threshold" if group=="compression" else "Maximum cloud synchronization gap")}</text>')
    parts.append(f'<text x="23" y="200" transform="rotate(-90 23 200)" text-anchor="middle" font-size="16" font-family="serif">{ylabel}</text>')
    parts.append('</svg>')
    (OUT/filename).write_text('\n'.join(parts))

svg_line('compression_accuracy.svg','compression','Mean final accuracy','accuracy_mean')
svg_line('compression_bytes.svg','compression','Mean modeled bytes (millions)','mean_modeled_total_bytes',scale=1e-6)
svg_line('original_sync_events.svg','original_sync','Mean cloud synchronization events','mean_cloud_sync_count')
if len([x for x in summary if x['group']=='corrected_gap'])==4:
    svg_line('corrected_sync_events.svg','corrected_gap','Mean cloud synchronization events','mean_cloud_sync_count')
    svg_line('corrected_gap_accuracy.svg','corrected_gap','Mean final accuracy','accuracy_mean')

report=['# AHCE-FL reproducibility and revision evidence',
        'All values below come from the stored CIFAR-10 experiment CSV files.',
        'Modeled communication bytes do not represent observed network packets.',
        'Accuracy and communication are reported as separate outcomes.',
        '',
        '## Results by configuration',
        '| Study | Setting | Seeds | Final accuracy mean | 95% t CI | Mean cloud sync events | Mean modeled bytes |',
        '|---|---|---:|---:|---|---:|---:|']
for x in summary:
    ci='Not available' if x['accuracy_ci95_lower'] is None else f"[{x['accuracy_ci95_lower']:.6f}, {x['accuracy_ci95_upper']:.6f}]"
    report.append(f"| {x['group']} | {x['setting']} | {x['n']} | {x['accuracy_mean']:.6f} | {ci} | {x['mean_cloud_sync_count']:.2f} | {x['mean_modeled_total_bytes']:.0f} |")
report+=['','## Paired seed comparisons',
         'Comparisons are exploratory because each group contains only three independent seeds.',
         '| Study | Candidate minus reference | Mean difference | 95% t CI | Two-sided paired p-value |',
         '|---|---|---:|---|---:|']
for x in paired:
    report.append(f"| {x['group']} | {x['candidate']} minus {x['reference']} | {x['mean_accuracy_difference']:.6f} | [{x['ci95_lower']:.6f}, {x['ci95_upper']:.6f}] | {x['p_value']:.10f} |")
report+=['','## Required manuscript corrections',
         '- Remove unsupported AHCE-FL classification-accuracy superiority statements.',
         '- Clarify client-selection proxy factors and the chosen normalized weights.',
         '- Separate compressed-upload payload estimates from physical network measurements.',
         '- State explicitly that no differential privacy or secure aggregation mechanism was experimentally validated.',
         '- The original synchronization gap ablation triggered 100 cloud synchronizations per seed and setting, so it cannot isolate the maximum-gap effect.',
         '- Describe the corrected ablation as a maximum-gap isolation experiment with the divergence trigger disabled by threshold 1e9. It does not establish the effectiveness of adaptive divergence threshold selection.',
         '- Recheck the corrected ablation against its per-round trigger telemetry before making any latency or energy claims.',
         '- Obtain and verify the actual reviewer correspondence and target journal format before preparing the final response and manuscript.',
         '']
(OUT/'EVIDENCE_REPORT.md').write_text('\n'.join(report))
print('ANALYSIS_OK',len(all_data),'runs',len(summary),'groups',len(paired),'paired comparisons')
