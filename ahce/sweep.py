"""Batch runner for controlled baseline, sparsification and synchronization studies."""
import argparse
import json
import subprocess
import sys
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--config", default="configs/manuscript_mnist.json")
    p.add_argument("--seeds", type=int, nargs="+", default=[11, 23, 42])
    p.add_argument("--methods", nargs="+",
                   default=["fedavg", "fedprox", "fedcs", "hfl", "ahce-fl"])
    p.add_argument("--taus", type=float, nargs="+", default=[0.0, 0.001, 0.01, 0.05])
    p.add_argument("--fail-fast", action="store_true")
    args = p.parse_args()
    config = json.loads(Path(args.config).read_text())
    failures = []
    for method in args.methods:
        tau_values = args.taus if method == "ahce-fl" else [config["compression_threshold"]]
        for seed in args.seeds:
            for tau in tau_values:
                cmd = [sys.executable, "-m", "ahce.train", "--config", args.config,
                       "--method", method, "--seed", str(seed), "--tau", str(tau)]
                print("RUN", " ".join(cmd), flush=True)
                result = subprocess.run(cmd, check=False)
                if result.returncode:
                    failures.append({"method": method, "seed": seed,
                                     "tau": tau, "returncode": result.returncode})
                    if args.fail_fast:
                        raise SystemExit(result.returncode)
    Path("results").mkdir(exist_ok=True)
    Path("results/failures.json").write_text(json.dumps(failures, indent=2))
    if failures:
        raise SystemExit(f"{len(failures)} experiments failed")
    print("Completed all configured runs")


if __name__ == "__main__":
    main()
