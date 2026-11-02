"""Configuration-safe compression and synchronization sensitivity experiments."""
import argparse
import json
import subprocess
import sys
from pathlib import Path
from ahce.full_validation import finished

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--base-config",default="configs/manuscript_cifar10.json")
    p.add_argument("--seeds",type=int,nargs="+",default=[11,23,42])
    p.add_argument("--taus",type=float,nargs="+",default=[0.0,0.001,0.01,0.05])
    p.add_argument("--sync-gaps",type=int,nargs="+",default=[1,2,3,5])
    p.add_argument("--mode",choices=["compression","synchronization"],required=True)
    args=p.parse_args()
    base=json.loads(Path(args.base_config).read_text())
    assert base["dataset"]=="cifar10" and base["rounds"]==100 and base["local_epochs"]==5
    assert "train_limit" not in base and "test_limit" not in base
    items=[(f"tau_{x:g}",{"compression_threshold":x},x) for x in args.taus] if args.mode=="compression" else [
        (f"gap_{x}",{"sync_max_gap":x},base["compression_threshold"]) for x in args.sync_gaps]
    Path("configs/generated").mkdir(parents=True,exist_ok=True)
    for name,updates,tau in items:
        cfg=dict(base)
        cfg.update(updates)
        filename=Path("configs/generated")/f"cifar10_{args.mode}_{name}.json"
        filename.write_text(json.dumps(cfg,indent=2)+"\n")
        for seed in args.seeds:
            path=Path("results")/f"{filename.stem}_cifar10_ahce-fl_seed{seed}_tau{tau:g}.csv"
            if finished(path):
                print("SKIP",path,flush=True)
                continue
            print("START",name,"seed",seed,flush=True)
            result=subprocess.run([sys.executable,"-m","ahce.train","--config",str(filename),
                                   "--method","ahce-fl","--seed",str(seed),"--tau",str(tau)])
            if result.returncode!=0 or not finished(path):
                raise SystemExit(f"FAILED {name} seed {seed}")
    print("Sensitivity complete",flush=True)

if __name__=="__main__":
    main()
