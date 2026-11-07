#!/usr/bin/env python3
"""Priority-gated AHCE-FL research workflow.

P1: provenance sidecar (immutable raw experiment files).
P2: resource-selection weights, reproducible plan only.
P3: divergence threshold x maximum-gap plan only.
P4: single-transfer communication accounting and manuscript numerical audit.
P5: figure source-audit preparation.
P6: further hardware and external-dataset validation (not claimed complete).
"""
import argparse,csv,datetime as dt,hashlib,json,subprocess,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/"reports/priority_workflow"
SEEDS=(11,23,42)
SOURCE=ROOT/"reproducibility/cifar10_100round"
GROUPS=("fedavg","fedprox","fedcs","hfl","ahce-fl")
BASE_CONFIG=ROOT/"configs/manuscript_cifar10.json"

def save(name,data):
    OUTPUT.mkdir(parents=True,exist_ok=True)
    (OUTPUT/name).write_text(json.dumps(data,indent=2,sort_keys=True)+"\n")

def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1<<20),b""):h.update(chunk)
    return h.hexdigest()

def p1_provenance():
    record=[];discrepancies=[];problems=[]
    for method in GROUPS:
        for seed in SEEDS:
            stem=f"manuscript_cifar10_cifar10_{method}_seed{seed}_tau0.01"
            j=SOURCE/(stem+".json");c=SOURCE/(stem+".csv")
            if not (j.is_file() and c.is_file()):
                problems.append(f"Missing archived files for {stem}")
                continue
            meta=json.loads(j.read_text())
            with c.open(newline="") as fh:
                rows=list(csv.DictReader(fh))
            good=(meta.get('method')==method and meta.get('seed')==seed
                  and len(rows)==100 and str(rows[-1].get('round'))=='100')
            if not good:problems.append(f"Run label, seed or 100-round mismatch: {stem}")
            cfg_method=meta.get("configuration",{}).get("method")
            item={"method":method,"seed":seed,"json_path":str(j.relative_to(ROOT)),
                  "csv_path":str(c.relative_to(ROOT)),"json_sha256":sha(j),
                  "csv_sha256":sha(c),"embedded_configuration_method":cfg_method,
                  "verified_top_level_method":meta.get("method"),
                  "source_originals_unchanged":True}
            record.append(item)
            if cfg_method!=method:discrepancies.append(item)
    result={"status":"pass" if not problems else "fail",
            "source_records":len(record),"expected_records":15,
            "metadata_mismatch_count":len(discrepancies),
            "metadata_mismatches":discrepancies,
            "problems":problems,
            "policy":"Retain original raw JSON/CSV; use verified top-level method and filenames; preserve hashes"}
    save("P1_PROVENANCE_SIDECAR.json",result)
    print("P1",result["status"],"records",len(record),"metadata_discrepancies",len(discrepancies))
    return not problems and len(record)==15

def p4_accounting():
    per_method={}
    errors=[]
    for method in GROUPS:
        samples=[]
        for seed in SEEDS:
            p=SOURCE/f"manuscript_cifar10_cifar10_{method}_seed{seed}_tau0.01.csv"
            if not p.exists():
                errors.append(f"Missing {p}");continue
            with p.open(newline="") as f:rows=list(csv.DictReader(f))
            if method in ("fedavg","fedprox","fedcs"):
                counted=sum(int(r["client_upload_bytes"])+int(r["client_download_bytes"]) for r in rows)
                duplicate=sum(int(r["cloud_upload_bytes"])+int(r["cloud_download_bytes"]) for r in rows)
                if counted!=308560000 or duplicate!=308560000:errors.append(f"Unexpected flat count {method} seed {seed}: {counted}/{duplicate}")
            else: counted=sum(int(r["total_bytes"]) for r in rows)
            samples.append(counted)
        if samples:per_method[method]={"per_seed_bytes":samples,"mean_bytes":sum(samples)/len(samples)}
    # Explicitly distinguish old model ledger from corrected transfer accounting.
    legacy=ROOT/"reproducibility/revision_analysis/EVIDENCE_REPORT.md"
    txt=legacy.read_text()
    old_duplicated="617120000" in txt
    if not old_duplicated:errors.append("Old communication ledger changed unexpectedly; review provenance.")
    result={"status":"pass" if not errors else "fail","methods":per_method,
            "corrected_flat_baseline_bytes":308560000,
            "legacy_flat_baseline_bytes":617120000,
            "old_report_contains_duplicated_ledger":old_duplicated,
            "errors":errors,
            "interpretation":"modeled parameter payload only, not measured physical network traffic"}
    save("P4_COMMUNICATION_LEDGER.json",result)
    print("P4",result["status"],"corrected_baselines",result["corrected_flat_baseline_bytes"])
    return not errors

def prepare_ablations():
    base=json.loads(BASE_CONFIG.read_text())
    assert base["dataset"]=="cifar10" and base["rounds"]==100
    # Planned independent comparisons; control is equal weights.
    weight_specs={
     "equal":[.2,.2,.2,.2,.2],
     "bandwidth":[.4,.15,.15,.15,.15],
     "energy":[.15,.4,.15,.15,.15],
     "accuracy":[.15,.15,.4,.15,.15],
     "latency":[.15,.15,.15,.4,.15],
     "compute":[.15,.15,.15,.15,.4]
    }
    experiments=[]
    for name,weights in weight_specs.items():
        assert abs(sum(weights)-1)<1e-10
        for seed in SEEDS:
            cfg=dict(base,selection_weights=weights,seed=seed)
            experiments.append({"priority":"P2","id":f"weights_{name}_seed{seed}",
               "seed":seed,"parameters":{"selection_weights":weights},
               "config":cfg,"baseline_comparison":"weights_equal"})
    # Crossed design identifies whether divergence and max-gap interact.
    for gap in (1,3,5):
        for delta in (0.05,0.5,1e9):
            for seed in SEEDS:
                cfg=dict(base,sync_max_gap=gap,sync_threshold=delta,seed=seed)
                experiments.append({"priority":"P3","id":f"gap{gap}_delta{delta:g}_seed{seed}",
                  "seed":seed,"parameters":{"sync_max_gap":gap,"sync_threshold":delta},
                  "config":cfg,"baseline_comparison":"gap1_delta1e9"})
    # Structured plan, no training, no GPU billing and no replacement of archival files.
    manifest={"status":"planned_not_executed","dataset":"CIFAR-10",
       "seeds":list(SEEDS),"rounds_per_run":100,
       "P2_run_count":len(weight_specs)*len(SEEDS),
       "P3_run_count":3*3*len(SEEDS),
       "total_new_runs":len(experiments),
       "execution_policy":"Manual initiation only after resource budget and dataset availability checked. Never auto-label planned data as completed.",
       "experiment_identifiers":[{"priority":e["priority"],"id":e["id"],"seed":e["seed"],"parameters":e["parameters"]} for e in experiments]}
    save("P2_P3_EXPERIMENT_PLAN.json",manifest)
    # Full configs are local generated input and do not overwrite previous runs.
    dest=ROOT/"configs/priority_generated"
    dest.mkdir(exist_ok=True)
    for e in experiments:
        p=dest/(e["id"]+".json")
        if p.exists() and json.loads(p.read_text())!=e["config"]:
            raise RuntimeError(f"Refusing to overwrite changed configuration: {p}")
        p.write_text(json.dumps(e["config"],indent=2,sort_keys=True)+"\n")
    print("P2_PLANNED",manifest["P2_run_count"],"P3_PLANNED",manifest["P3_run_count"],"NEW_RUNS_EXECTUTED",0)
    return True

def figure_plan():
    manuscript=ROOT/"manuscripts/IJAESD-345169/AHCE_FL_Final_Audited_Blind.docx"
    sources=["reproducibility/revision_analysis/descriptive_statistics.json",
             "reproducibility/revision_analysis/paired_tests.json",
             "reproducibility/sync_corrected/metrics.json"]
    item={"status":"manual_pixel_and_provenance_review_pending",
      "manuscript_sha256":sha(manuscript),
      "figures_expected":9,
      "source_files":[{"path":n,"sha256":sha(ROOT/n)} for n in sources],
      "required_check":"Review chart axes, point values, error bars, caption-to-image identity, and source plot scripts; do not equate embedded figure presence to correctness."}
    save("P5_FIGURE_REVIEW_PLAN.json",item)
    return True

def audit():
    ok=p1_provenance() and p4_accounting()
    # Existing audit performs 125 CSV/table checks, does not alter source file.
    cmd=[sys.executable,str(ROOT/"reproducibility/manuscript_consistency_audit/audit_manuscript.py")]
    r=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True)
    print(r.stdout[-800:])
    if r.returncode:
        print(r.stderr[-1200:],file=sys.stderr)
        ok=False
    else:
        data=json.loads((ROOT/"reproducibility/manuscript_consistency_audit/AUDIT_RESULTS.json").read_text())
        ok=ok and data["failed_checks"]==0
    figure_plan()
    save("WORKFLOW_STATUS.json",{
        "P1_provenance":"pass_sidecar_created" if ok else "inspect_report",
        "P2_resource_weight_ablation":"pending_experimental_runs",
        "P3_divergence_gap_ablation":"pending_experimental_runs",
        "P4_communication_accounting":"pass_independent_recalculation" if ok else "inspect_report",
        "P5_figures":"visual_review_pending",
        "P6_robustness_hardware":"future_separately_scoped_validation",
        "research_claims":"baseline AHCE-FL does not outperform FedAvg; no hardware/network measurements",
        "passed_audit":bool(ok)})
    return ok

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--stage",choices=["audit","plan","all-preflight"],default="all-preflight")
    a=p.parse_args()
    ok=True
    if a.stage in ("plan","all-preflight"):ok=prepare_ablations() and ok
    if a.stage in ("audit","all-preflight"):ok=audit() and ok
    raise SystemExit(0 if ok else 1)
if __name__=="__main__":main()
