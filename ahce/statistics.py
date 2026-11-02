"""Summarize paired independent-seed comparisons without fabricating missing runs."""
import argparse
import csv
import json
import math
import statistics
from pathlib import Path

import numpy as np


def summarize(config, seeds, methods, tau=0.01, root="results"):
    rows=[]
    for seed in seeds:
        for method in methods:
            t = tau if method=="ahce-fl" else 0.01
            path=Path(root)/f"{config}_cifar10_{method}_seed{seed}_tau{t:g}.csv"
            if not path.exists():
                rows.append({"seed":seed,"method":method,"status":"MISSING","path":str(path)})
                continue
            with path.open(newline="") as file:
                history=list(csv.DictReader(file))
            if len(history)!=100:
                rows.append({"seed":seed,"method":method,"status":"INCOMPLETE","rounds":len(history),"path":str(path)})
                continue
            final=history[-1]
            rows.append({"seed":seed,"method":method,"status":"COMPLETE",
                         "accuracy":float(final["accuracy"]),
                         "total_bytes":sum(int(x["total_bytes"]) for x in history),
                         "sync_count":sum(int(x["sync_triggered"]) for x in history),
                         "rounds":len(history), "path":str(path)})
    complete={(r["method"],r["seed"]):r for r in rows if r["status"]=="COMPLETE"}
    comparisons=[]
    for baseline in methods:
        if baseline=="ahce-fl":
            continue
        pairs=[(complete[("ahce-fl",s)],complete[(baseline,s)]) for s in seeds
               if ("ahce-fl",s) in complete and (baseline,s) in complete]
        comp={"baseline":baseline,"paired_seeds":[s for s in seeds if ("ahce-fl",s) in complete and (baseline,s) in complete]}
        if len(pairs)>=2:
            diff=[a["accuracy"]-b["accuracy"] for a,b in pairs]
            sd=statistics.stdev(diff)
            mean=statistics.mean(diff)
            comp.update(mean_accuracy_difference=mean,sd_difference=sd,
                        standard_error=sd/math.sqrt(len(diff)))
            try:
                from scipy.stats import t, ttest_1samp
                comp["ci95"]=[mean-t.ppf(.975,len(diff)-1)*comp["standard_error"],
                              mean+t.ppf(.975,len(diff)-1)*comp["standard_error"]]
                comp["paired_t_pvalue"]=float(ttest_1samp(diff,0).pvalue)
            except ImportError:
                comp["ci95"]=None
                comp["paired_t_pvalue"]=None
        else:
            comp["status"]="INSUFFICIENT_PAIRED_SEEDS"
        comparisons.append(comp)
    return {"runs":rows,"comparisons":comparisons}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--config",default="manuscript_cifar10")
    p.add_argument("--seeds",type=int,nargs="+",default=[11,23,42])
    p.add_argument("--methods",nargs="+",default=["fedavg","fedprox","fedcs","hfl","ahce-fl"])
    p.add_argument("--tau",type=float,default=0.01)
    p.add_argument("--output",default="results/analysis_summary.json")
    a=p.parse_args()
    report=summarize(a.config,a.seeds,a.methods,a.tau)
    Path(a.output).parent.mkdir(parents=True,exist_ok=True)
    Path(a.output).write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))


if __name__=="__main__":
    main()
