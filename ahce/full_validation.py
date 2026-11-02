"""Run full CIFAR-10 protocol. Existing verified 100-round CSV files are skipped."""
import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path

METHODS=("fedavg","fedprox","fedcs","hfl","ahce-fl")
SEEDS=(11,23,42)

def finished(path):
    if not path.exists():
        return False
    try:
        with path.open(newline="") as f:
            rows=list(csv.DictReader(f))
        return len(rows)==100 and int(rows[-1]["round"])==100
    except (ValueError,KeyError,IndexError,OSError):
        return False

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--config",default="configs/manuscript_cifar10.json")
    p.add_argument("--seeds",nargs="+",type=int,default=list(SEEDS))
    p.add_argument("--methods",nargs="+",choices=METHODS,default=list(METHODS))
    p.add_argument("--tau",type=float,default=0.01)
    args=p.parse_args()
    config=json.loads(Path(args.config).read_text())
    assert config["dataset"]=="cifar10" and config["rounds"]==100
    assert config["local_epochs"]==5 and config["clients"]==50
    assert not config.get("train_limit") and not config.get("test_limit")
    for seed in args.seeds:
        for method in args.methods:
            tau=args.tau if method=="ahce-fl" else 0.01
            prefix=f"{Path(args.config).stem}_cifar10_{method}_seed{seed}_tau{tau:g}"
            path=Path("results")/(prefix+".csv")
            if finished(path):
                print("SKIP verified",path,flush=True)
                continue
            print("START",method,"seed",seed,"tau",tau,flush=True)
            proc=subprocess.run([sys.executable,"-m","ahce.train","--config",args.config,
                                 "--seed",str(seed),"--method",method,"--tau",str(tau)])
            if proc.returncode:
                raise SystemExit(f"FAIL {method} seed={seed} exit={proc.returncode}")
            if not finished(path):
                raise SystemExit(f"FAIL incomplete output {path}")
    print("All requested full-data runs completed",flush=True)

if __name__=="__main__":
    main()
