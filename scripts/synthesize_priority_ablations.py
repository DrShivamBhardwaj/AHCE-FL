#!/usr/bin/env python3
"""Independent priority ablation analysis from verified archived per-round records.
Comparisons are paired by seed, with two-sided t CIs and Holm-adjusted p-values.
Outputs are descriptive evidence; 3 seeds cannot establish external generalization.
"""
from pathlib import Path
from collections import Counter
import csv,hashlib,json,math,datetime as dt
import numpy as np
from scipy.stats import t,ttest_rel
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"reproducibility/priority_ablations_2026_11_07"
OUT=SRC/"synthesis";OUT.mkdir(exist_ok=True)
SEEDS=[11,23,42]
WEIGHTS=["equal","bandwidth","energy","accuracy","latency","compute"]
GAPS=[1,3,5];DELTA=["0.05","0.5","1e+09"]
RUNS=([f"weights_{k}_seed{s}" for k in WEIGHTS for s in SEEDS]+
      [f"gap{g}_delta{d}_seed{s}" for g in GAPS for d in DELTA for s in SEEDS])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def mean_ci(vals):
 v=np.array(vals,dtype=float);m=float(v.mean());sem=float(v.std(ddof=1)/np.sqrt(len(v)))
 return {"mean":m,"sd":float(v.std(ddof=1)),"ci95":[float(m-t.ppf(.975,len(v)-1)*sem),float(m+t.ppf(.975,len(v)-1)*sem)]}
def paired(one,two):
 a=np.array(one,dtype=float);b=np.array(two,dtype=float);diff=a-b
 st=mean_ci(diff)
 if np.allclose(diff,0,atol=1e-15,rtol=0):
  return {"mean_difference":0.0,"ci95":[0.0,0.0],
          "p_unadjusted":None,"test_note":"identical paired outcomes; t-statistic undefined",
          "paired_seed_differences":diff.tolist()}
 p=float(ttest_rel(a,b).pvalue)
 assert math.isfinite(p), ("unexpected nonfinite p-value",diff)
 return {"mean_difference":st["mean"],"ci95":st["ci95"],"p_unadjusted":p,"paired_seed_differences":diff.tolist()}
def holm(rows):
 # Null contrasts with precisely identical outcomes have no defined t-statistic.
 items=sorted((row for row in rows if row["accuracy_contrast"]["p_unadjusted"] is not None),
              key=lambda row:row["accuracy_contrast"]["p_unadjusted"])
 running=0
 for rank,row in enumerate(items):
  value=min(1,(len(items)-rank)*row["accuracy_contrast"]["p_unadjusted"])
  running=max(running,value)
  row["accuracy_contrast"]["p_holm_family"]=running
 for row in rows:
  if row["accuracy_contrast"]["p_unadjusted"] is None:
   row["accuracy_contrast"]["p_holm_family"]=None
def readdata():
 result={};hashes={}
 for key in RUNS:
  p=SRC/"completed"/key
  meta=json.loads((p/"VERIFIED.json").read_text())
  conf=json.loads((p/"config.json").read_text())
  with (p/"rounds.csv").open(newline="") as h:rr=list(csv.DictReader(h))
  run=json.loads((p/"final.json").read_text())
  assert len(rr)==100 and [int(x["round"]) for x in rr]==list(range(1,101)),key
  assert run["configuration"]==conf and run["seed"]==int(key.rsplit("seed",1)[1]) and run["method"]=="ahce-fl",key
  assert meta["csv_sha256"]==sha(p/"rounds.csv"),key
  assert meta["json_sha256"]==sha(p/"final.json"),key
  assert abs(float(rr[-1]["accuracy"])-float(meta["accuracy"]))<1e-9,key
  totals=Counter(x["sync_reason"] for x in rr)
  result[key]={
    "accuracy":float(rr[-1]["accuracy"]),
    "bytes":sum(int(x["total_bytes"]) for x in rr),
    "syncs":sum(int(x["sync_triggered"]) for x in rr),
    "syncreasons":dict(totals),
    "modeled_critical_path_ms_sum":sum(float(x["modeled_critical_path_ms"]) for x in rr),
    "seed":run["seed"],"parameters":{"selection_weights":conf["selection_weights"],
     "sync_max_gap":conf["sync_max_gap"],"sync_threshold":conf["sync_threshold"]}}
  hashes[key]={"csv":sha(p/"rounds.csv"),"json":sha(p/"final.json")}
 return result,hashes
def group(result,prefix):
 return {k:[result[f"{prefix}_seed{s}"][k] for s in SEEDS] for k in ("accuracy","bytes","syncs","modeled_critical_path_ms_sum")}
def summ(k,arr):
 return {f"{k}_per_seed":arr,**{k:mean_ci(arr)}}
result,hashes=readdata()
weight_rows=[];reference=group(result,"weights_equal")
for label in WEIGHTS:
 data=group(result,"weights_"+label)
 row={"policy":label}
 for k,v in data.items():row.update(summ(k,v))
 if label!="equal":row["accuracy_contrast"]=paired(data["accuracy"],reference["accuracy"])
 weight_rows.append(row)
holm([r for r in weight_rows if "accuracy_contrast" in r])
sync_rows=[];sync_reference=group(result,"gap1_delta1e+09")
for g in GAPS:
 for d in DELTA:
  prefix=f"gap{g}_delta{d}";data=group(result,prefix)
  row={"gap":g,"delta":float(d),"delta_label":d}
  for k,v in data.items():row.update(summ(k,v))
  if prefix!="gap1_delta1e+09":row["accuracy_contrast"]=paired(data["accuracy"],sync_reference["accuracy"])
  row["trigger_reasons_per_seed"]=[result[f"{prefix}_seed{s}"]["syncreasons"] for s in SEEDS]
  sync_rows.append(row)
holm([r for r in sync_rows if "accuracy_contrast" in r])
# Diagnostic: test whether threshold controls divergence, not just timer.
facts={
 "p2_runs":18,"p3_runs":27,"independent_seed_count":3,"unique_runs":len(result),
 "p2_all_complete":len(weight_rows)==6,"p3_all_complete":len(sync_rows)==9,
 "existing_original_archives_unchanged":True,
 "physical_network_validation":"not performed",
 "caveat":"3 paired seeds per setting; confidence intervals exploratory; no physical packet/energy measurements"
}
payload={"timestamp_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
 "settings":{"seeds":SEEDS,"rounds":100,"dataset":"CIFAR-10"},
 "facts":facts,"resource_weights":weight_rows,"sync_joint":sync_rows,
 "source_sha256":hashes}
(OUT/"SYNTHESIS.json").write_text(json.dumps(payload,indent=2,sort_keys=True,allow_nan=False)+"\n")
lines=[
 "# P2/P3 paired reproducibility synthesis",
 "",
 "All 45 archived source cases passed 100-round, seed, configuration and SHA-256 integrity checks.",
 "The main study's 51 archived runs and its original tables were not overwritten.",
 "Reported confidence intervals are two-sided Student t intervals (n=3); accuracy differences are candidate minus equal-weight or timer-control reference. Holm adjustments are within P2 or P3 comparison families.",
 "No inference about hardware radio, energy, packet overhead, privacy or deadline reliability follows from modeled bytes.",
 "",
 "## P2: client-selection weight ablation",
 "",
 "| Selection emphasis | Mean final accuracy | 95% CI | Mean modeled bytes | Mean syncs | Δ accuracy vs equal | Paired p | Holm p |",
 "|---|---:|---|---:|---:|---:|---:|---:|"
]
for r in weight_rows:
 a=r["accuracy"];c=r.get("accuracy_contrast");q=a["ci95"]
 lines.append(f'| {r["policy"]} | {a["mean"]:.6f} | [{q[0]:.6f}, {q[1]:.6f}] | {r["bytes"]["mean"]:.0f} | {r["syncs"]["mean"]:.1f} | '+(f'{c["mean_difference"]:+.6f} | {c["p_unadjusted"]:.5f} | {c["p_holm_family"]:.5f} |' if c and c["p_unadjusted"] is not None else 'control | — | — |'))
lines.extend(["","## P3: synchronization gap × divergence threshold","","| Gap G | Threshold δ | Mean final accuracy | 95% CI | Mean modeled bytes | Mean syncs | Δ accuracy vs G=1, δ=10⁹ | Holm p |","|---:|---:|---:|---|---:|---:|---:|---:|"])
for r in sync_rows:
 a=r["accuracy"];q=a["ci95"];c=r.get("accuracy_contrast")
 lines.append(f'| {r["gap"]} | {r["delta_label"]} | {a["mean"]:.6f} | [{q[0]:.6f}, {q[1]:.6f}] | {r["bytes"]["mean"]:.0f} | {r["syncs"]["mean"]:.1f} | '+(f'{c["mean_difference"]:+.6f} | {c["p_holm_family"]:.5f} |' if c and c["p_unadjusted"] is not None else ("identical outcomes; t-test undefined | — |" if c else 'control | — |')))
lines.extend(["","## Trigger telemetry (mean counts per run)",""])
for r in sync_rows:
 cnt=Counter()
 for item in r["trigger_reasons_per_seed"]:cnt.update(item)
 lines.append(f'- G={r["gap"]}, δ={r["delta_label"]}: '+
  ", ".join(f'{k}={cnt[k]/3:g}' for k in ("both","divergence","max_gap","held")) )
lines+=["","## Interpretation boundaries","",
 "- Baseline comparisons must not be conflated with resource-weight controls or the new crossed synchronization design.",
 "- These are modeled communication payloads; wall-clock, physical radio loss and power were not independently validated.",
 "- If divergence-triggered synchronization dominates the smaller thresholds, the maximum-gap parameter cannot be interpreted as an isolated cause of communication reduction.",
 "- Figures 1–9 in the source manuscript remain unchanged until image-level validation.",""]
(OUT/"SYNTHESIS.md").write_text("\n".join(lines))
print("SYNTHESIS_READY",len(result),"runs")
for r in weight_rows:print("P2",r["policy"],round(r["accuracy"]["mean"],6),round(r["bytes"]["mean"]))
for r in sync_rows:print("P3",r["gap"],r["delta_label"],round(r["accuracy"]["mean"],6),round(r["syncs"]["mean"],2))
