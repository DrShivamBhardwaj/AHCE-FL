#!/usr/bin/env python3
"""Sequential, resumable AHCE-FL P2 then P3 full-data experiments.

Do not overwrite archived experiments or claim a run complete without 100 valid CSV rows.
Git checkpoints include only this campaign's configs/results, not historical outputs.
"""
import argparse, csv, datetime as dt, hashlib, json, os, signal, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RUNROOT=ROOT/"reproducibility"/"priority_ablations_2026_11_07"
LOGS=RUNROOT/"run_logs"
CONFIGS=ROOT/"configs"/"priority_generated"
STATE=RUNROOT/"status.json"
SEEDS=(11,23,42)
ORDER=["equal","bandwidth","energy","accuracy","latency","compute"]
RUNS=[f"weights_{w}_seed{s}" for w in ORDER for s in SEEDS]
RUNS += [f"gap{g}_delta{d}_seed{s}" for g in (1,3,5) for d in ("0.05","0.5","1e+09") for s in SEEDS]
# The filename format from the plan script uses :g, so 1e+09 is intentional.
assert len(RUNS)==45 and len(set(RUNS))==45
RUNROOT.mkdir(parents=True,exist_ok=True)
LOGS.mkdir(exist_ok=True)
def now():return dt.datetime.now(dt.timezone.utc).isoformat()
def sha(path):
 h=hashlib.sha256()
 with path.open("rb") as f:
  for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
 return h.hexdigest()
def atomic_json(p,obj):
 temp=p.with_suffix(p.suffix+".tmp")
 temp.write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n")
 temp.replace(p)
def log(*parts):print(now(),*parts,flush=True)
def run_paths(name,seed):
 config=CONFIGS/(name+".json")
 effective=json.loads(config.read_text())
 checkpoint=RUNROOT/"checkpoints"/f"{name}.pt"
 effective["checkpoint_path"]=str(checkpoint.relative_to(ROOT))
 effective["checkpoint_every"]=5
 localconfig=RUNROOT/"configs"/f"{name}.json"
 localconfig.parent.mkdir(exist_ok=True)
 if localconfig.exists() and json.loads(localconfig.read_text()) !=effective:raise RuntimeError(f"Configuration differs, refusing overwrite {localconfig}")
 if not localconfig.exists():atomic_json(localconfig,effective)
 stem=f"{name}_cifar10_ahce-fl_seed{seed}_tau0.01"
 return localconfig,checkpoint,ROOT/"results"/(stem+".csv"),ROOT/"results"/(stem+".json"),stem,effective
def verify(csvpath,jsonpath,effective,seed):
 if not csvpath.exists() or not jsonpath.exists():return None
 try:
  with csvpath.open(newline="") as f:rows=list(csv.DictReader(f))
  j=json.loads(jsonpath.read_text())
  rounds=[int(float(r["round"])) for r in rows]
  expected=effective.copy()
  if not (len(rows)==100 and rounds==list(range(1,101)) and
          j.get("method")=="ahce-fl" and j.get("seed")==seed and
          j.get("configuration")==expected and
          int(j["result"]["round"])==100 and
          abs(float(j["result"]["accuracy"])-float(rows[-1]["accuracy"]))<1e-10):
   return None
  return {"accuracy":float(rows[-1]["accuracy"]),"syncs":sum(int(r["sync_triggered"]) for r in rows),
          "modeled_bytes":sum(int(r["total_bytes"]) for r in rows),"csv_sha256":sha(csvpath),
          "json_sha256":sha(jsonpath),"completed_utc":now()}
 except (ValueError,KeyError,TypeError,json.JSONDecodeError) as ex:
  log("VERIFY_ERROR",str(ex));return None
def archive(name,config,csvpath,jsonpath,record):
 out=RUNROOT/"completed"/name
 out.mkdir(parents=True,exist_ok=True)
 pairs=[(config,"config.json"),(csvpath,"rounds.csv"),(jsonpath,"final.json")]
 for src,dst in pairs:
  dest=out/dst
  data=src.read_bytes()
  if dest.exists() and dest.read_bytes()!=data:
   raise RuntimeError("ARCHIVE_MISMATCH refused to overwrite "+str(dest))
  if not dest.exists():dest.write_bytes(data)
 record["archive_files"]={dst:sha(out/dst) for _,dst in pairs}
 atomic_json(out/"VERIFIED.json",record)
def push(name):
 # A separate research-progress branch, not main. All output data is staged selectively.
 args=["git","add","--","scripts/execute_priority_ablations.py","docs/PRIORITY_ABLATION_RUNBOOK.md",
       "configs/priority_generated",str(RUNROOT.relative_to(ROOT))]
 a=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,timeout=60)
 if a.returncode:log("STAGING_ERROR",a.stderr[-500:]);return False
 staged=subprocess.run(["git","diff","--cached","--quiet"],cwd=ROOT)
 if staged.returncode==0:return True
 commit=subprocess.run(["git","commit","-m",f"Checkpoint priority ablations through {name}"],cwd=ROOT,capture_output=True,text=True,timeout=90)
 if commit.returncode:log("COMMIT_ERROR",commit.stderr[-500:]);return False
 p=subprocess.run(["git","push","origin","HEAD:refs/heads/research/priority-ablations-2026-11"],cwd=ROOT,capture_output=True,text=True,timeout=180)
 log("GIT_PUSH",name,p.returncode,p.stderr[-350:])
 return p.returncode==0
def main():
 a=argparse.ArgumentParser();a.add_argument("--max-runs",type=int,default=45)
 a.add_argument("--no-push",action="store_true");args=a.parse_args()
 # Exclusive instance lock; avoid concurrent invocation without destructive lock removal.
 import fcntl
 lockfile=(RUNROOT/"execution.lock").open("w")
 try:fcntl.flock(lockfile,fcntl.LOCK_EX|fcntl.LOCK_NB)
 except BlockingIOError:raise SystemExit("Another campaign controller active; refusing duplicate")
 state=json.loads(STATE.read_text()) if STATE.exists() else {"created_utc":now(),"runs":{}}
 state["planned"]=45
 def saved():
  state["updated_utc"]=now()
  state["verified_runs"]=sum(v.get("status")=="verified" for v in state["runs"].values())
  state["failed_runs"]=sum(v.get("status")=="error" for v in state["runs"].values())
  atomic_json(STATE,state)
 for idx,name in enumerate(RUNS[:args.max_runs],1):
  seed=int(name.rsplit("seed",1)[1])
  cfg,ckpt,csvp,jsonp,stem,effective=run_paths(name,seed)
  existing=verify(csvp,jsonp,effective,seed)
  if existing:
   log("SKIP_VERIFIED",idx,name)
   state["runs"][name]={"status":"verified",**existing}
   archive(name,cfg,csvp,jsonp,state["runs"][name]);saved()
   continue
  if csvp.exists() or jsonp.exists():
   raise RuntimeError("Partial or mismatched existing final output, manual review required: "+name)
  state["runs"][name]={"status":"running","started_utc":now(),"config_sha256":sha(cfg)}
  saved()
  log("START",idx,"OF",len(RUNS),name,"checkpoint",str(ckpt))
  with (LOGS/(name+".log")).open("ab") as f:
   p=subprocess.run([sys.executable,"-u","-m","ahce.train",
     "--config",str(cfg.relative_to(ROOT)),"--method","ahce-fl",
     "--seed",str(seed),"--tau","0.01"],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT)
  if p.returncode:
   state["runs"][name]={"status":"error","exit_code":p.returncode,"at_utc":now()}
   saved();log("RUN_FAILED",name,p.returncode);raise SystemExit(p.returncode)
  record=verify(csvp,jsonp,effective,seed)
  if not record:
   state["runs"][name]={"status":"error","reason":"100-round output failed validation","at_utc":now()}
   saved();raise RuntimeError("OUTPUT_VERIFICATION_FAILED: "+name)
  state["runs"][name]={"status":"verified",**record}
  archive(name,cfg,csvp,jsonp,state["runs"][name])
  log("VERIFIED",name,"accuracy",record["accuracy"],"syncs",record["syncs"])
  saved()
  if not args.no_push:push(name)
 state["status"]="completed" if all(state["runs"].get(n,{}).get("status")=="verified" for n in RUNS) else "in_progress"
 saved();log("FINISH",state["verified_runs"],"/45",state["status"])
 if not args.no_push:push("final")
if __name__=="__main__":main()
